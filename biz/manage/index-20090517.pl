#!/usr/bin/perl

use lib "/httpd/modules"; 
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
use strict;

&ZOOVY::init();
&GTOOLS::init();
&ZWEBSITE::init();

require LUSER;
my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $template_file = 'index.shtml';
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

my @EL = ();
push @EL, { link=>"/biz/manage/customer", img=>"/biz/images/utilities/customer.gif", title=>"Customer Manager", hint=>"Find or create a customer record for your website.", };
#if ($FLAGS =~ /,SC,/) {
	push @EL, { available=>($FLAGS=~/,SC,/)?1:0,  link=>"/biz/manage/suppliers", img=>"/biz/images/utilities/supplychain.gif", title=>"Supply Chain Management", hint=>"Track inventory, pricing and orders with your suppliers.", };
#	}
#if ($FLAGS =~ /,CRM,/) {
	push @EL, {	available=>($FLAGS=~/,CRM,/)?1:0, link=>"/biz/manage/giftcard", img=>"/biz/images/utilities/giftcard-54x54.gif", title=>"GiftCard Manager", hint=>"Create / Manage GiftCards", };
#	}
#if ($FLAGS =~ /,XSELL,/) {
#	push @EL, {	link=>"/biz/manage/coupon", img=>"/biz/images/utilities/coupons-54x54.gif", title=>"Coupon Manager", hint=>"Create / Manage Coupon/Offers", };
#	}

#if ($FLAGS =~ /,WS,/) {
	push @EL, {	available=>($FLAGS=~/,WS,/)?1:0, link=>"/biz/manage/schedules", img=>"/biz/images/utilities/wholesale.gif", title=>"Wholesale Pricing Schedules", hint=>"Create separate price lists for your wholesale customers.", };
#	}
#if ($FLAGS =~ /,CRM,/) {
	push @EL, {	available=>($FLAGS=~/,CRM,/)?1:0, link=>"/biz/manage/newsletter", img=>"/biz/images/utilities/newsletter.gif", title=>"Newsletter Manager", hint=>"Create subscription lists and then setup Campaigns to send newsletters to your subscribers.", };
	push @EL, {	available=>($FLAGS=~/,CRM,/)?1:0, link=>"/biz/manage/reviews", img=>"/biz/images/utilities/reviews.gif", title=>"Reviews", hint=>"Approve customer reviews of your products.", };
	push @EL, {	available=>($FLAGS=~/,CRM,/)?1:0, link=>"/biz/manage/faqs", img=>"/biz/images/utilities/faqs.gif", title=>"Frequently Asked Questions", hint=>"The ability to easily create and manage faqs on your store.", };
#	}
	push @EL, { available=>($FLAGS=~/,EBAY,/)?1:0, link=>"/biz/manage/powerlister", img=>"/biz/images/utilities/ebay_manager.gif", title=>"Powerlister Manager", hint=>"Track, and update your eBay PowerLister Channels.", };

#	if ($USERNAME eq 'brian') {
		push @EL, { link=>'/biz/manage/snapshots', img=>'/biz/images/utilities/snapshot.png', title=>'Snapshots', hint=>'create snapshots of your product database for backups, and faster performance', };
#		}

#		<td valign="top" width="1%" align="center"><img src="/biz/images/utilities/ebay_manager.gif" width="49" height="49" border="0"></td>
#		<td align="left"><b>eBay Integration</b><br>
#		<table>
#		<tr>
#			<td valign='top' height="15" width="15"><a href="/biz/manage/powerlister"><img border='0' name="img12" src="/biz/images/tabs/graphics/b.gif" height="15" width="15"></a></td>
#			<td align="left"><a href="/biz/manage/powerlister">PowerLister Manager</a><br>Track, and update your eBay PowerLister Channels.</td>

my $c = '';
foreach my $item (@EL) {

	my $class = 'available';
	if ((defined $item->{'available'}) && ($item->{'available'}==0)) {
		$item->{'img'} =~ s/\.gif/_off\.gif/;
		$class = 'unavailable';
		}

	$c .= qq~<div style='font-size: 8pt; width: 250px; height: 75px; align: center; float:left; margin-left:8px; margin-bottom:8px; text-align:center;'>~;
	$c .= qq~
<table border=0 cellspacing=0 cellpadding=0 width=225>
<tr>
<td valign='top' width="60" align="left">
	<a href="$item->{'link'}"><img src="$item->{'img'}" width="54" height="53" border="0"></a>
</td>
<td valign=top align="left">
	<div class="$class">
	<div class="title"><a href="$item->{'link'}">$item->{'title'}</a></div>
	<div class="hint">$item->{'hint'}</div>
	</div>
</td>
</tr>
</table>~;
	$c .= qq~</div>~;
	}
$GTOOLS::TAG{'<!-- ITEMS -->'} = $c;	


##
## MINI-MENU
##
my @ITEMS = ();
#push @ITEMS, { grp=>'mkt', link=>"/biz/manage/launchgroups", title=>"Launch Groups Manager", hint=>"Prepare groups of products to be submitted to marketplaces.", };
push @ITEMS, { available=>($FLAGS=~/,EBAY,/)?1:0, grp=>'mkt', link=>"/biz/manage/channels", title=>"Channel Manager", hint=>"Track, and update your marketing channels" };
push @ITEMS, { available=>($FLAGS=~/,EBAY,/)?1:0, grp=>'mkt', link=>"/biz/manage/channellist", title=>"Full Channel List", hint=>"Track, and update your marketing channels." };
push @ITEMS, { available=>($FLAGS=~/,EBAY,/)?1:0, grp=>'mkt', link=>"/biz/manage/batch", title=>"Batch Channel Editor", hint=>"Perform operations on multiple channels at once." };
push @ITEMS, { available=>($FLAGS=~/,CSV,/)?1:0, grp=>'store', link=>"/biz/manage/csvexport", title=>"Product Export", hint=>"Exports products into a CSV file.</td>" };
push @ITEMS, { available=>($FLAGS=~/,CSV,/)?1:0, grp=>'store', link=>"/biz/manage/powerprod", title=>"Product Power Tool", hint=>"Modify multiple product attributes in mass." };
push @ITEMS, { available=>($FLAGS=~/,CSV,/)?1:0, grp=>'store', link=>"/biz/manage/powersog", title=>"Option Power Tool", hint=>"Modify multiple product Store Option values in mass." };

push @ITEMS, { grp=>'store', link=>"/biz/manage/archive", title=>"Archive Orders", hint=>"Hide completed orders." };
push @ITEMS, { grp=>'store', link=>"/biz/manage/diskspace", title=>"Disk Space Manager", hint=>"Manage the amount of disk space in use by your account." };
push @ITEMS, { grp=>'store', link=>"/biz/batch/index.cgi?VERB=NEW&EXEC=REPORT&REPORT=IMAGE_ASSOC&GUID=".time(), title=>"Image Associations", hint=>"View a list of images, and the products they are associated with" };
push @ITEMS, { grp=>'store', link=>"/biz/manage/paypal", title=>"Paypal IPN Processor", hint=>"Check the status of Paypal transactions." };
push @ITEMS, { grp=>'store', link=>"/biz/syndication/sitemap", title=>"Static Google SiteMap", hint=>"Configure nightly generation of a static sitemap file." };
push @ITEMS, { grp=>'store', link=>'/biz/manage/debugger', title=>"Website Debugger", hint=>"Website Debugger" };

foreach my $item (@ITEMS) {
	my $class = 'available';
	my $image = "/biz/images/tabs/graphics/b.gif";
	if ((defined $item->{'available'}) && ($item->{'available'}==0)) {
		$image = "/biz/images/tabs/graphics/b_off.gif";
		$class = 'unavailable';
		}

	my $c = qq~
<tr>
	<td valign='top' height="15" width="15"><a href="$item->{'link'}"><img border='0' name="img43" src="$image" height="15" width="15"></a></td>
	<td align="left">
	<div class="$class">
	<a href="$item->{'link'}">$item->{'title'}</a><br>
	<div class="hint">$item->{'hint'}</div>
	</div>
</td>
</tr>
~;
	if ($item->{'grp'} eq 'mkt') {
		$GTOOLS::TAG{'<!-- MKT_HTML -->'} .= $c;
		}
	else {
		$GTOOLS::TAG{'<!-- STORE_HTML -->'} .= $c;		
		}
	}

if ($GTOOLS::TAG{'<!-- MKT_HTML -->'} eq '') {
	$GTOOLS::TAG{'<!-- MKT_HTML -->'} = "<tr><td colspan=2><i>eBay not enabled.</i></td></tr>"; 
	}

# &GTOOLS::print_form("Website Management Area",$template_file,1,'topic/manage.php');
&GTOOLS::output(
	'title'=>'Website Utilities',
	'file'=>$template_file,
	'header'=>'1',
	'help'=>'topic/manage.php',
	'tabs'=>[
		],
	'bc'=>[
		{ name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
		],
	);


