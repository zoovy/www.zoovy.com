#!/usr/bin/perl -w

use strict;
use lib "/httpd/modules"; 
require GTOOLS;
require ZWEBSITE;
require ZOOVY;
require PAGE;
require LUSER;
require TODO;

&ZOOVY::init();
&GTOOLS::init();
&ZWEBSITE::init();

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

#use Data::Dumper;
#print STDERR Dumper($LU);

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }
my @MSGS = ();

$GTOOLS::TAG{"<!-- MERCHANT -->"} = $USERNAME;

my $LEVEL = $LU->level();
my ($ref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

if ( (my $sizeof = &ZOOVY::sizeof($ref)) > 250000) {
	push @MSGS, 
	qq~WARN|Website Config Database is very large ($sizeof bytes)\n\n
For optimal performance try and reduce the size.
Having a large database increases your site rendering speed, and also 
increases the likihood for corruption when making an update. 
Common causes of bloat in are a combination of excessive coupons, shipping rules, or having lengthy 
custom site messages. A typical size is around 50,000 bytes, 
and anything over 200,000 bytes is considered large.~;
		}


my $NEEDREF = {};
if ($LU->get('todo.setup')) {
	my $t = TODO->new($USERNAME);	
	($NEEDREF) = $t->setup_tasks('');
	}

my @TABS = ();
my @BC = ();
push @BC, { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', };

if (not defined $ZOOVY::cgiv->{'MODE'}) { $ZOOVY::cgiv->{'MODE'} = ''; }

$GTOOLS::TAG{'<!-- SETUP.MANAGE -->'} = $LU->get('setup.manage',1);
$GTOOLS::TAG{'<!-- SETUP.PROPERTIES -->'} = $LU->get('setup.properties',1);
$GTOOLS::TAG{'<!-- SETUP.ACCOUNT -->'} = $LU->get('setup.account',1);
$GTOOLS::TAG{'<!-- SETUP.UTILITY -->'} = $LU->get('setup.utility',0);
$GTOOLS::TAG{'<!-- SETUP.MARKET -->'} = $LU->get('setup.market',0);
$GTOOLS::TAG{'<!-- SETUP.DEVELOPER -->'} = $LU->get('setup.developer',0);
$GTOOLS::TAG{'<!-- SETUP.CUSTOM -->'} = $LU->get('setup.custom',0);
undef $LU;


my $SCONLY = ($FLAGS =~ /,PKG=SHOPCART,/)?1:0;
my $ANYCOM = ($FLAGS =~ /,PKG=ANYONE,/)?1:0;
if ($SCONLY) { 
	## okay so we're SCONLY -- but do we have the SITEHOST bundle?
	if ($FLAGS =~ /SITEHOST/) { $SCONLY = 0; }
	}


my @LINKS = ();

#+-------------------+
#| LINK              |
#+-------------------+
#| SETUP:HASPRODUCT  |
#| SETUP:HASSHIPPING |
#| SETUP:HASPAYMENT  |
#| SETUP:HASTAX      |
#| SETUP:SYNDICATION |
#| SETUP:COMPANYLOGO |
#| SETUP:ZID         |
#+-------------------+


## MANAGE TAB
@LINKS = ();
if ($FLAGS =~ /,PKG=SHOPCART,/) {
	push @LINKS, { min=>0, link=>"/biz/setup/apphost", title=>"App Hosting", about=>"Domain/app hosting", };
	}

push @LINKS, { min=>1, link=>'/biz/setup/domain', title=>'Domain Hosting', about=>'Register and Link Domains.', };
push @LINKS, { min=>0, link=>"/biz/setup/projects", title=>"App Hosting", about=>"Manage Hosted Application Projects", };
if (not $ANYCOM) {
	push @LINKS, { min=>0, link=>"/biz/setup/builder", title=>"Site Builder", about=>"Build the content for your storefront.  Select page layouts and add product to categories and lists.", };
	}
push @LINKS, { todo=>($NEEDREF->{'company'})?1:0, min=>2, link=>'/biz/setup/builder/index.cgi?ACTION=COMPANYEDIT&NS=DEFAULT', title=>'Company Information', about=>'Put in Logo, Address, Policies, etc.' };
if (not $ANYCOM) {
	push @LINKS, { min=>2, link=>'/biz/setup/builder/themes/index.cgi?NS=DEFAULT', title=>'Pick Site Theme', about=>'Select the graphics, buttons and navigation which will be used for this site.' };
	push @LINKS, { min=>2, link=>"/biz/setup/builder/index.cgi?ACTION=EDIT-WRAPPER", title=>'Customize Site Theme', about=>'Tune customizable features in the selected theme.' };
	push @LINKS, { min=>2, link=>'/biz/setup/builder/index.cgi?ACTION=DECALS&amp;NS=DEFAULT', title=>'Customize Site Decals', about=>'Enhance your site with 3rd party logos.' };
	push @LINKS, { min=>2, link=>'/biz/setup/builder/themes/index.cgi?NS=DEFAULT&SUBTYPE=E', title=>'Select Email Theme', about=>'Pick a style for a header and footer for an email.' };
	}
push @LINKS, { min=>2, link=>'/biz/setup/builder/emails/index.cgi?VERB=EDIT&NS=DEFAULT', title=>'Edit Email Messages', about=>'Customize the emails that are sent to customers.' };
push @LINKS, { min=>0, link=>"/biz/setup/media/index.cgi", title=>"Media Library", about=>'Upload and manage your images, sounds, movies, documents and flash.' };
push @LINKS, { min=>2, link=>'/biz/setup/media/', title=>'Upload New Image', about=>'' };
push @LINKS, { min=>2, link=>'/biz/setup/customfiles', title=>'Public Files Library', about=>'' };
push @LINKS, { min=>3 }; ## a brea;
push @LINKS, { min=>0, link=>"/biz/setup/navcats", title=>"Categories &amp; Lists", about=>'Build your store category tree or add product lists.' },;

push @LINKS, { min=>1, link=>'/biz/setup/analytics/index.cgi', title=>'Analytics &amp; Plugins', about=>'Integrate approved 3rd party applications with your site.' };
push @LINKS, { min=>1, link=>'/biz/setup/rss/index.cgi', title=>'RSS Feeds', about=>'Create RSS Feeds to easily share your product lists with affiliate sites.' };
my $MANAGE_DIV = build_panel('MANAGE',"Manage Apps/Website", "images/icons/website_32x32.gif",'navcat_0',1,\@LINKS);


## MARKET TAB
@LINKS = ();
push @LINKS, { 
	requires=>(($FLAGS !~ /,EBAY,/)?'EBAY':''), 
	min=>0, link=>'/biz/setup/ebay/index.cgi', title=>'eBay Configuration', about=>'Manage eBay tokens, feedback, shipping &amp; launch profiles.' 
	};
push @LINKS, { 
	requires=>(($FLAGS !~ /,AMZ,/)?'AMZ':''), 
	min=>0, link=>'/biz/syndication/amazon/index.cgi', title=>'Amazon Configuration', about=>q~Manage Amazon Tokens and learn more about Zoovy's integration.~, 
	};
#push @LINKS, { 
#	requires=>(($FLAGS !~ /,BUY,/)?'BUY':''), 
#	min=>0, link=>'/biz/setup/buy/index.cgi', title=>'Buy.com Configuration', about=>q~Manage Buy.Com and learn more about Zoovy's integration.~, 
#	};
#push @LINKS, { 
#	requires=>(($FLAGS !~ /,SRS,/)?'SRS':''), 
#	min=>0, link=>'/biz/setup/buy/index.cgi', title=>'Sears.com Configuration', about=>q~Manage Sears.com and learn more about Zoovy's integration.~, 
#	};
#if (scalar(@LINKS)==0) {
#	push @LINKS, { min=>3, title=>'No integrated marketplaces enabled. (<a href="/biz/configurator/index.cgi?VERB=VIEW&BUNDLE=EBAY">eBay</a> or <a href="/biz/configurator/index.cgi?VERB=ADD&BUNDLE=AMZ">Amazon</a> bundles required)', };
#	}
my $MARKET_DIV = build_panel('MARKET','Integrated Marketplaces','images/icons/account_32x32.gif','navcat_3',1, \@LINKS);

## MPO TAB
@LINKS = ();
push @LINKS, { 
	min=>1, link=>'/biz/setup/repricing/index.cgi', title=>'Amazon Repricing', about=>q~
Let Zoovy automatically raise/lower pricing on Marketplaces to beat competitors.~, 
	};
my $MPO_DIV = build_panel('MPO','Marketplace Optimization','images/icons/account_32x32.gif','navcat_3',1, \@LINKS);


## PROPERTIES
@LINKS = ();
push @LINKS, { todo=>($NEEDREF->{'shipping'})?1:0, min=>1, link=>'/biz/setup/shipping', title=>'Shipping', about=>'Determine how shipping will be calculated for your products.' };
push @LINKS, { todo=>($NEEDREF->{'payment'})?1:0, min=>1, link=>'/biz/setup/payment', title=>'Payment Methods', about=>'Configure which payment methods you will accept from customers.' };
push @LINKS, { todo=>($NEEDREF->{'tax'})?1:0, min=>1, link=>'/biz/setup/tax', title=>'Sales Tax', about=>'Configure state and local tax collection amounts.' };
push @LINKS, { min=>0, link=>'/biz/setup/promotions', title=>'Coupons/Promotions', about=>'Create discounts for special purchases' };
push @LINKS, { min=>0, link=>'/biz/setup/checkout?MODE=GENERAL', title=>'Checkout Setup', about=>'Specify what info is optional/required during checkout.' };
push @LINKS, { min=>0, link=>'/biz/setup/checkout?MODE=CUSTOMERADMIN', title=>'Customer Admin Config', about=>'Configure what options customers have when they login to their accounts on your store.'};
push @LINKS, { min=>1, link=>'/biz/setup/checkout?MODE=SYS-MESSAGES', title=>'System Messages', about=>'Customize System Messages used throughout the site' };
push @LINKS, { min=>1, link=>'/biz/setup/checkout?MODE=CHK-MESSAGES', title=>'Checkout Messages', about=>'Customize Checkout Messaging used during checkout.' };
use Data::Dumper; print STDERR Dumper($LU);
if ($LEVEL>=7) {
	push @LINKS, { min=>1, link=>'/biz/setup/checkout?MODE=INTERNATIONAL', title=>'Languages &amp; Currencies', about=>'Configure which languages and currencies are available.' };
	}
if ($FLAGS =~ /,CRM,/) {
	push @LINKS, { min=>1, link=>'/biz/crm/index.cgi?VERB=CONFIG', title=>'CRM Behaviors', about=>'Configure preferences in the CRM area.' };
	}
# push @LINKS, { min=>1, link=>'/biz/setup/callcenter/index.cgi', title=>'Call Center', about=>'Manage call center scripts associated with your sites.' };
my $PROPERTIES_DIV = build_panel('PROPERTIES','Store Properties','images/icons/properties_32x32.gif', 'navcat_2',1,\@LINKS);

## UTILITIES
@LINKS = ();
push @LINKS, { todo=>($NEEDREF->{'import'})?1:0, min=>0, link=>'/biz/setup/import', title=>'CSV Import Utility', about=>'Import data from a variety of formats.', };
## No longer configurable:
#if ($FLAGS =~ /,EBAY,/) {
#	push @LINKS, { min=>1, link=>'/biz/setup/reminder', title=>'Payment Reminders', about=>'Configure feedback/payment reminders.', };
#	}
#if (($FLAGS =~ /,STAFF,/) || ($FLAGS =~ /,TIER=A/)) {
#	push @LINKS, { min=>1, link=>'/biz/setup/automation', title=>'Automation', about=>'Configure Automation/Events', };
#	}
if ($FLAGS =~ /,WEB,/) {
	push @LINKS, { min=>0, link=>'/biz/setup/search', title=>'Manage Search Catalogs', about=>'Create custom searchable indexes of your product database.', };
	}
my $UTILITY_DIV = build_panel('UTILITY','Utility Features','images/icons/advanced_32x32.gif','navcat_1',1, \@LINKS);

## ACCOUNT
@LINKS = ();
push @LINKS, { min=>1, link=>'/biz/setup/account', title=>'Contact Information', about=>'Change Administrative/Billing Information' };
if ($FLAGS =~ /,SITEHOST,/) {
	push @LINKS, { todo=>($NEEDREF->{'hosting'})?1:0, min=>0, link=>"/biz/setup/hosting", title=>"Hosting Setup", about=>"Enter URLS for your storefront.  Select page layouts and add product to categories and lists.", };
	}
#if (($LEVEL>3) || ($FLAGS =~ /,EBAY,/)) {
#	## PROFILES are only available to LEVEL3 or EBAY
#	push @LINKS, { min=>0, link=>'/biz/setup/profiles', title=>'Company Profiles', about=>'Profiles can be used to create separate policies for different domains/products.' };
#	}
push @LINKS, { min=>1, link=>'/biz/setup/global', title=>'Global Settings', about=>'Inventory &amp; Order settings in this area affect all sites managed from this account.' };
if ($LEVEL>=7) {
	push @LINKS, { min=>0, link=>'/biz/setup/global/index.cgi?VERB=PARTITIONS', title=>'Partitions', about=>'The ability to segment your settings, and databases for each site associated with this account.' };
	}

push @LINKS, { min=>1, link=>'/biz/setup/usermgr', title=>'Manage Users/Devices', about=>'Manage which users and devices can access your account.' };
push @LINKS, { min=>0, link=>'/biz/setup/password', title=>'Change Password', about=>'You should change your password every 60 days.' };
push @LINKS, { min=>1, link=>'/biz/configurator', title=>'Add/Remove Features', about=>'Manage feature bundles installed on this account.' };
push @LINKS, { min=>0, link=>'/biz/setup/billing', title=>'Billing History', about=>'View your billing history, update payment information.' };
if (not $ANYCOM) {
	push @LINKS, { min=>1, link=>'/biz/setup/proshop.cgi', title=>'Zoovy proShop Access', about=>'A showcase of design functionality &amp; services for your store.' };
	}

if (($FLAGS =~ /,PKG=SHOPCART,/) && ($FLAGS !~ /,SITEHOST,/)) {
	## this is strictly for upsetlling.
	push @LINKS, { 
		requires=>'SITEHOST',
		min=>0, link=>"#", title=>"Add Site Hosting", 
		about=>'Site Hosting lets you create categories and lists of products, specify homepage and about us all hosted on Zoovy\'s highly reliable architecture. ',
		};
	}

if (($FLAGS =~ /,PKG=SHOPCART,/) && ($FLAGS !~ /,ZID,/)) {
	## this is strictly for upsetlling.
	push @LINKS, { 
		requires=>'ZID',
		min=>0, link=>"#", title=>"Add Zoovy Integrated Desktop", 
		about=>'Windows software for processing orders, printing airbills/shipping labels, integrates with Quickbooks and more!',
		};
	}
my $ACCOUNT_DIV = build_panel('ACCOUNT','Account Settings','images/icons/account_32x32.gif','navcat_4',1, \@LINKS);

## DEVELOPER
@LINKS = ();
push @LINKS, {
	min=>1, link=>'/biz/setup/private', title=>'Private Files', about=>'Private files include diagnostic logs, reports, and ticket attachments.'
	};
push @LINKS, {
	min=>1, title=>'Developer SDK', about=>'Use this to easily custom integrations or apps',
	link=>'https://github.com/zoovy/Zoovy-MVC-Framework-JQuery-Plugin',
	};
push @LINKS, {
	min=>1, title=>'Dev Wiki', about=>'Learn more about what is possible, and what is included in the SDK.',
	link=>'https://github.com/zoovy/Zoovy-MVC-Framework-JQuery-Plugin/wiki',
	};
if (not $ANYCOM) {
	push @LINKS, { 
		requires=>(($FLAGS !~ /,WEB,/)?'WEB':''),
		min=>0, link=>'/biz/setup/toxml/index.cgi?ACTION=HELP', title=>'TOXML Editor', about=>'Create Custom Templates for your site, emails, auctions,etc.', 
		};
	push @LINKS, { 
		requires=>(($FLAGS !~ /,WEB,/)?'WEB':''),
		min=>2, link=>'toxml/index.cgi?MODE=WRAPPER', title=>'Site Themes', about=>'Templates which control the navigation and maintain consistency throughout your store.', 
		};
	push @LINKS, { 
		requires=>(($FLAGS !~ /,WEB,/)?'WEB':''),
		min=>2, link=>'toxml/index.cgi?MODE=LAYOUT', title=>'Page Layouts &amp; Newsletters', about=>'Templates which control the editing/formatting of each page on your store.', 
		};
	push @LINKS, { 
		requires=>(($FLAGS !~ /,WEB,/)?'WEB':''),
		min=>2, link=>'toxml/index.cgi?MODE=WIZARD', title=>'Auction Templates (Wizards)', about=>'Templates which are used to create all-in-one pages suitable for auctions.', 
		};
	push @LINKS, { 
		requires=>(($FLAGS !~ /,WEB,/)?'WEB':''),
		min=>2, link=>'toxml/index.cgi?MODE=ZEMAIL', title=>'Email Templates', about=>'Templates which are used when sending automated emails.', 
		};
	push @LINKS, { 
		requires=>(($FLAGS !~ /,API,/)?'API':''),
		min=>1, link=>'/biz/setup/dispatch', title=>'API Integration', about=>'Automatically transmit orders to a remote server.', 
		};
	push @LINKS, {
		min=>1, link=>'/biz/setup/interface', title=>'User Interface', about=>'Configure your user interface to increase employee productivity',
		};
	if ($LEVEL>=8) {
		push @LINKS, { min=>1, link=>'/biz/setup/developer', title=>'Site Integrator (API2)', about=>'Configure integration with non-zoovy websites.', };
		}
	}

my $DEVELOPER_DIV = build_panel('DEVELOPER','Developer Tools','images/icons/advanced_32x32.gif','navcat_4',1,\@LINKS);

##
## 
##############################################################################
my $html = qq~
<!-- SETUP_TAB -->

<script type="text/javascript" src="/biz/ajax/zoovy-jquery.js"></script>


<script type="text/javascript">
<!--


function moreOrLess(section,show) {
	// val of 1 is more, 0 is less.

	var val = show;
	// if val isn't passed, then it is read from the input variable.
	if (show == undefined) { 
		val = jQuery('#'+section+'\\\\!state').val(); 
		if (val=='0') { val = '1'; } else { val = '0'; }
		}
	
	if (val=='1') {
		jQuery('#'+section+'\\\\!min').hide();
		jQuery('#'+section+'\\\\!max').show();
		jQuery('#'+section+'\\\\!prompt').html(' &#187; <a onClick="moreOrLess(\\''+section+'\\');"  href="#"><strong>Less Choices..</strong></a>');		
		}
	else {
		jQuery('#'+section+'\\\\!min').show();
		jQuery('#'+section+'\\\\!max').hide();
		jQuery('#'+section+'\\\\!prompt').html(' &#187; <a onClick="moreOrLess(\\''+section+'\\');"  href="#"><strong>More Choices..</strong></a>');	
		}

	jQuery('#'+section+'\\\\!state').val(val);

	if (show == undefined) {		
		var postBody = 'm=PREFERENCE/Set&SET:setup.'+section+'='+val;
		jQuery.ajax('/biz/ajax/prototype.pl/PREFERENCE/SET', 
			{ dataType:"text",data: postBody,async: 1,success: function(data, textStatus, jqXHR){ jHandleResponse(data);} } ) ;
		}
	}


//-->
</script>

<input type="hidden" id="manage!state" value="<!-- SETUP.MANAGE -->">
<input type="hidden" id="utility!state" value="<!-- SETUP.UTILITY -->">
<input type="hidden" id="market!state" value="<!-- SETUP.MARKET -->">
<input type="hidden" id="properties!state" value="<!-- SETUP.PROPERTIES -->">
<input type="hidden" id="account!state" value="<!-- SETUP.ACCOUNT -->">
<input type="hidden" id="developer!state" value="<!-- SETUP.DEVELOPER -->">
<input type="hidden" id="mpo!state" value="<!-- SETUP.MPO -->">

<br />
<div align="center">
<table cellpadding="0" cellspacing="10"><tr>


	<td width="250" valign="top" rowspan="2">
	$MANAGE_DIV
	$MARKET_DIV
	$MPO_DIV
	</td>


	<td width="250" valign="top">
	$PROPERTIES_DIV	
	$UTILITY_DIV
	</td>

	<td width="250" valign="top">

	$ACCOUNT_DIV
	$DEVELOPER_DIV 
	</td>
</tr></table>

<script type="text/javascript">
<!--

moreOrLess('manage','<!-- SETUP.MANAGE -->');
moreOrLess('properties','<!-- SETUP.PROPERTIES -->');
moreOrLess('utility','<!-- SETUP.UTILITY -->');
moreOrLess('account','<!-- SETUP.ACCOUNT -->');
moreOrLess('market','<!-- SETUP.MARKET -->');
moreOrLess('developer','<!-- SETUP.DEVELOPER -->');
moreOrLess('mpo','<!-- SETUP.MPO -->');

//-->
</script>

</div>
<!-- FOOTER -->
~;


if ($PRT>0) {

	my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$PRT);

	push @BC, { name=>"Partition: $prtinfo->{'name'}" };

	my @LINKS = ();
	push @LINKS, { min=>0, link=>'/biz/setup/domain', title=>'Domain Hosting', about=>'Associate Domains to this Partition.', };
	push @LINKS, { min=>0, link=>'/biz/setup/promotions', title=>'Coupons/Promotions', about=>'Create discounts for special purchases', };
	push @LINKS, { min=>0, link=>'/biz/setup/tax', title=>'Sales Tax', about=>'Configure state and local tax collection amounts.', };
	push @LINKS, { min=>0, link=>'/biz/setup/shipping', title=>'Shipping', about=>'Determine how shipping will be calculated for your products.', };
	push @LINKS, { min=>0, link=>'/biz/setup/payment', title=>'Payment Methods', about=>'Configure which payment methods you will accept from customers.', };
	push @LINKS, { min=>0, link=>'/biz/setup/checkout?MODE=GENERAL', title=>'Checkout Setup', about=>'Specify what info is optional/required during checkout.', };
	push @LINKS, { min=>0, link=>'/biz/setup/checkout?MODE=CUSTOMERADMIN', title=>'Customer Admin Setup', about=>'Settings that affect what your customers can do in their admin area.', };
	push @LINKS, { min=>0, link=>'/biz/setup/checkout?MODE=SYS-MESSAGES', title=>'System Messages', about=>'Customize System Messages that are displayed to your customers', };
	push @LINKS, { min=>0, link=>'/biz/setup/builder', title=>'Site Builder', about=>'Build the content for your storefront.  Select page layouts and add product to categories and lists.', };
	push @LINKS, { min=>0, link=>'analytics/index.cgi', title=>'Analytics &amp; Plugins', about=>'Integrate approved 3rd party applications with your site.', };
	push @LINKS, { min=>0, link=>'/biz/syndication/amazon/index.cgi', title=>'Amazon', about=>'Amazon', };
	push @LINKS, { min=>0, link=>'/biz/setup/ebay', title=>'eBay.com', about=>'eBay Setup', };
	if ($prtinfo->{'p_navcats'}>0) {
		push @LINKS, { min=>0, link=>'/biz/setup/navcats', title=>'Categories &amp; Lists', about=>'Build your store category tree or add product lists.</di', };
		push @LINKS, { min=>0, link=>'/biz/setup/import', title=>'CSV Import Utility', about=>'Import Customer or Category data.', };
		push @LINKS, { min=>0, link=>'/biz/setup/rss/index.cgi', title=>'RSS Feeds', about=>'Create RSS Feeds to easily share your product lists with affiliate sites.' };
		push @LINKS, { min=>0, link=>"/biz/setup/media/index.cgi", title=>"Media Library", about=>'Upload and manage your images, sounds, movies, documents and flash.' };
		}	

	my $PROPERTIES_DIV = build_panel('PROPERTIES','Store Properties','images/icons/properties_32x32.gif', 'navcat_2', 0, \@LINKS);

	$html = qq~<!-- SETUP_TAB -->
<body>
<br>
<br>
<center>
<table width=300><tr><td>

$PROPERTIES_DIV

</td></tr>
</table>
</center>

<!-- FOOTER -->
</body>

~;
	}




&GTOOLS::output(
   'title'=>'Setup',
	'html'=>$html,
   'header'=>'1',
   'help'=>'#50727',
   'tabs'=>\@TABS,
	'bc'=>\@BC,
	'todo'=>1,
	'jquery'=>1,
	'msgs'=>\@MSGS,
   );

##
## 
##
sub build_panel {
	my ($panel,$name,$icon,$css,$allow_collapse,$sets) = @_;

	$panel = lc($panel);
	my $mintxt = '';

#	use Data::Dumper;
#	print STDERR Dumper($sets);

	foreach my $set (@{$sets}) {
		next unless ($set->{'min'}==0);
		my $class = '';
		if ((defined $set->{'todo'}) && ($set->{'todo'}>0)) { $class = "todo"; }

		next if ($set->{'requires'});		## we never minimize requires
		
		$mintxt .= qq~<img src="/biz/images/tabs/graphics/b.gif" width="15" height="15" > <a class="$class" href="$set->{'link'}">$set->{'title'}</a><br />\n~;
		}


	my $maxtxt = '';
	foreach my $set (@{$sets}) {
		my $class = '';
		my $style = '';
		my $stylesub = '';

		if ($set->{'requires'}) {
			$style = qq~ style="color: #707070;" ~;
			$stylesub = qq~ style="color: #A0A0A0;" ~;
			$set->{'link'} = "https://www.zoovy.com/biz/configurator?VERB=VIEW&BUNDLE=$set->{'requires'}";
			}

		if ((defined $set->{'todo'}) && ($set->{'todo'}>0)) { $class = "todo"; }
		if ($set->{'min'}==3) {
			## a link break.
			my $title = $set->{'title'};
			if (not defined $title) { $title = ''; }
			$maxtxt .= qq~<div class="subtitle1_margin"><div class="subtitle1">$title</div></div>~;
			}
		elsif ($set->{'min'}==2) {
			## a subheader which goes under a main header.
			$maxtxt .= qq~ - <a class="$class" $style href="$set->{'link'}">$set->{'title'}</a><br>\n~;
			if ($set->{'about'} ne '') { $maxtxt .= qq~<div $stylesub class="subtitle1">$set->{'about'}</div>\n~; }
			}
		else {
			## a main header (with bullet), which may or may not be collapsed
			my $gif = '/biz/images/tabs/graphics/b.gif';
			if ($set->{'requires'}) { $gif = '/biz/images/tabs/graphics/b_off.gif'; }

			$maxtxt .= qq~<img src="$gif" width="15" height="15" > <a class="$class" $style href="$set->{'link'}">$set->{'title'}</a><br />\n~;;
			if ($set->{'about'} ne '') { $maxtxt .= qq~<div $stylesub class="subtitle0">$set->{'about'}</div>\n~; }
			}
		}


		if ($allow_collapse) {
			## COLLAPSABLE 
			return qq~
<div id="$panel"><!-- $panel -->
<table cellspacing=0 cellpadding=4 border=0 width="100%" class="$css" style="margin-bottom:10px;"><tr>
	<td valign="top" width="4%"><img src="$icon" width="32" height="32"></td>
	<td valign="middle" width="45%" align="left"><span class="big_link">$name</span></td>
</tr><tr>
	<td colspan="2" style="padding-left:15px; background-color:#FFFFFF;">

<div id="$panel!min" style="display:none;">
$mintxt
</div>

<div id="$panel!max">
$maxtxt
<div class="subtitle1_margin"></div>
</div>


<!-- This should change to 'fewer choices' if more has been selected -->
<div id="$panel!prompt" style="text-align:right; margin-top:4px;">
 &#187; <a onClick="moreOrLess('$panel');" href="#"><strong>Fewer Choices..</strong></a></div>

</td></tr></table>
<!-- /$panel --></div>~;
			}
		else {
			## NON COLLAPSABLE (e.g. partitions)
         return qq~
<div id="$panel"><!-- $panel -->
<table cellspacing=0 cellpadding=4 border=0 width="100%" class="$css" style="margin-bottom:10px;"><tr>
   <td valign="top" width="4%"><img src="$icon" width="32" height="32"></td>
   <td valign="middle" width="45%" align="left"><span class="big_link">$name</span></td>
</tr><tr>
   <td colspan="2" style="padding-left:15px; background-color:#FFFFFF;">


<div>
$maxtxt
<div class="subtitle1_margin"></div>
</div>

</td></tr></table>
<!-- /$panel --></div>~;
 			}

	}
