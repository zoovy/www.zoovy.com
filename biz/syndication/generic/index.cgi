#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use DOMAIN::TOOLS;
use SYNDICATION;

use strict;



require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
my $PATH = $ENV{'SCRIPT_NAME'};
$GTOOLS::TAG{'<!-- PATH -->'} = $PATH;

print STDERR "PATH:$PATH\n";

if ($ENV{'SCRIPT_NAME'} =~ /(buycom|ebay)/) {
	## make sure we never show profiles for ebay, buycom
	if ($VERB eq '') { $VERB = 'EDIT'; }
	$PROFILE = "#$PRT";
	}

my @MSGS = ();

my $FEEDTYPE = $ZOOVY::cgiv->{'FEEDTYPE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}


my @TABS = ();
my @FIELDS = ();
if ($PROFILE eq '') {
	}
elsif (substr($PROFILE,0,1) eq '#') { 	
	## buy.com, ebay, etc. which are PARTITION specific don't have a select profile option
	push @TABS, { name=>'Edit Partition',selected=>($VERB eq 'EDIT')?1:0, link=> "$PATH?VERB=EDIT&PROFILE=$PROFILE", };
	}
else {
	push @TABS, { name=>'Profiles',selected=>($VERB eq '')?1:0, link=>'index.cgi' };
	push @TABS, { name=>"Edit: $PROFILE",selected=>($VERB eq 'EDIT')?1:0, link=> "$PATH?VERB=EDIT&PROFILE=$PROFILE", };
	}

my @BC = (
      { name=>'Syndication',link=>'/biz/syndication/index.cgi','target'=>'_top', },
		);

my @CONFIG_FIELDS = ();

my ($WEBDOC) = 0;		## this is REQUIRED
my ($DST,$MARKETPLACE) = (undef,undef);
my @CSV_PRODUCT_EXPORT = ();

if ($ENV{'SCRIPT_NAME'} =~ /nextag/) {
	$WEBDOC = 50594;
	($DST,$MARKETPLACE) = ('NXT','Nextag.com');
	push @BC, { name=>'Nextag.com',link=>"$PATH",'target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP Username', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1, hint=>'example: upload.nextag.com' };
#	push @FIELDS, { type=>'textbox', name=>'FTP Folder', id=>'.ftp_path', hint=>'example: /private/yourname' };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /sitemap/) {
	$WEBDOC = 50396;
	($DST,$MARKETPLACE) = ('GSM','Google Sitemap');
	push @BC, { name=>'SiteMap',link=>"$PATH",'target'=>'_top', };
	push @FIELDS, { type=>'checkbox', name=>'Enable', id=>'.enable', required=>1 };
# .stragegy??
#	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
#	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
#	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1, hint=>'example: upload.nextag.com' };
#	push @FIELDS, { type=>'textbox', name=>'FTP Folder', id=>'.ftp_path', hint=>'example: /private/yourname' };
	}
#elsif ($ENV{'SCRIPT_NAME'} =~ /mysimon/) {
#	$WEBDOC = 50593;
#	($DST,$MARKETPLACE,$FEED_TYPE) = ('MYS','MySimon.com','API');
#	push @BC, { name=>'Nextag.com',link=>'/biz/syndication/nextag','target'=>'_top', };
#	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"?VERB=CATEGORIES&PROFILE=$PROFILE", };
#	}
#elsif (($ENV{'SCRIPT_NAME'} =~ /(buycom|bestbuy)/) && ($FLAGS !~ /,BUY,/)) {
#	print "Location: /biz/configurator?VERB=VIEW&PACKAGE=BUY&YOURFLAGS=$FLAGS\n\n";
#	}
elsif ($ENV{'SCRIPT_NAME'} =~ /buycom/) {
	require SYNDICATION::BUYCOM;
	$WEBDOC = 50917;
	($DST,$MARKETPLACE) = ('BUY','Buy.com');
	push @BC, { name=>'Buy.com',link=>'/biz/syndication/buycom/index.cgi','target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'FILES')?1:0, 'name'=>'Files', 'link'=>"$PATH?VERB=FILES&PROFILE=$PROFILE" };
	push @TABS, { selected=>($VERB eq 'DBMAP')?1:0, 'name'=>'DB Maps', 'link'=>"$PATH?VERB=DBMAP&PROFILE=$PROFILE" };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP Username', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Seller ID', id=>'.sellerid', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Seller Password', id=>'.sellerpass', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /bestbuy/) {
	require SYNDICATION::BUYCOM;
	$WEBDOC = 50917;
	($DST,$MARKETPLACE) = ('BST','BestBuy Marketplace');
	push @BC, { name=>'Best Buy Marketplace',link=>'/biz/syndication/bestbuy/index.cgi','target'=>'_top', };
	push @TABS, { selected=>($VERB eq 'FILES')?1:0, 'name'=>'Files', 'link'=>"$PATH?VERB=FILES&PROFILE=$PROFILE" };
	push @TABS, { selected=>($VERB eq 'DBMAP')?1:0, 'name'=>'DB Maps', 'link'=>"$PATH?VERB=DBMAP&PROFILE=$PROFILE" };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP Username', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Seller ID', id=>'.sellerid', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Seller Password', id=>'.sellerpass', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /pricegrabber/) {
	$WEBDOC = 50397;
	($DST,$MARKETPLACE) = ('PGR','PriceGrabber.com');
	push @BC, { name=>'PriceGrabber.com',link=>'/biz/syndication/pricegrabber/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	## NOTE: even though this is type FTP, it uses the .user and .pass fields
	##			because pricegrabber doesn't separate the fields.
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP/Web Username', id=>'.user', required=>1, hint=>'hint: uploaded filename is always username.csv',};
	push @FIELDS, { type=>'textbox', name=>'FTP/Web Password', id=>'.pass', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /amazonpa/) {
	$WEBDOC = 51478;
	($DST,$MARKETPLACE) = ('APA','Amazon Product Ads');
	push @BC, { name=>'Amazon Product Ads',link=>'/biz/syndication/amazonpa/index.cgi','target'=>'_top', };
	## NOTE: even though this is type FTP, it uses the .user and .pass fields
	##			because pricegrabber doesn't separate the fields.
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP/Web Username', id=>'.ftp_user', required=>1, hint=>'hint: uploaded filename is always username.csv',};
	push @FIELDS, { type=>'textbox', name=>'FTP/Web Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
#elsif (($ENV{'SCRIPT_NAME'} =~ /ebay/) && ($FLAGS !~ /,EBAY,/)) {
#	print "Location: /biz/configurator?VERB=VIEW&PACKAGE=EBAY\n\n";
#	}
elsif ($ENV{'SCRIPT_NAME'} =~ /ebay/) {
	$WEBDOC = 50380;
	($DST,$MARKETPLACE) = ('EBF','eBay Syndication');
	push @BC, { name=>'eBay.com',link=>"$PATH",'target'=>'_top', };
	# push @FIELDS, { type=>'warning', msg=>qq~Currently under development - check this space on 5/8/2011~, };
	push @TABS, { name=>"eBay Categories", selected=>($VERB eq 'EBAY-CATEGORIES')?1:0, link=>"$PATH?VERB=EBAY-CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Submit New Products', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };

	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Use AutoPilot on New Items', id=>'.autopilot',
		hint=>q~[RECOMMENDED] 
		Auto-Pilot allows Zoovy's eBay Syndication Engine to make 'reasonable guesses' about getting 
		your products up on eBay.  
		This includes using fields such as the price on the website as the eBay Fixed price.
		Without Auto-Pilot, it will be necessary for you to choose eBay settings per product.
		If settings are not configured the product will generate listing event errors which you will need to correct.
		If the syndication engine encounters too many errors - then your token could be deactivated and all eBay processing will be suspended.
		~ };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Detailed Logging', id=>'.logging', 
		hint=>q~[NOT RECOMMENDED] 
		What this does:
		The syndication engine generates detailed log files (which can be obtained by asking support), 
		that include the decision logic that was used to perform a listing. These log files consume significantly 
		more disk space. You should probably only enable this if instructed to by Zoovy support, but it can be invaluable
	   in diagnosing issues with auto-pilot.
		~ };
#	push @FIELDS, { type=>'checkbox', name=>'Use Inventory Reserves', 
#		id=>'.use_reserves', 
#		hint=>q~
#		If this is selected then the quantity specified in the product, or if auto-pilot is enabled then qty 1 will be sent, and a reserve record will be created to mitigate
#		potential overselling scenarios. 
#		If the box is not selected - then the entire quantity available will be sent and inventory will NOT be reserved.
#		If the product has a fixed price quantity specified then this setting controls if that quantity will be reserved,
#		and in no circumstances will the inventory configured in the product be sent if it exceeds the actual inventory
#		available (unless the product itself has unlimited inventory enabled)
#		~ };
#
	}
#elsif ($ENV{'SCRIPT_NAME'} =~ /amzrp/) {
#	$WEBDOC = 51607;
#	($DST,$MARKETPLACE) = ('ARP','Amazon Repricing');
#	push @BC, { name=>'Amazon Repricing',link=>'/biz/syndication/amzrp','target'=>'_top', };
#	}
elsif ($ENV{'SCRIPT_NAME'} =~ /wishpot/) {
	$WEBDOC = 51424;
	($DST,$MARKETPLACE) = ('WSH','Wishpot');
	push @BC, { name=>'Wishpot.com',link=>'/biz/syndication/wishpot/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /shareasale/) {
	$WEBDOC = 51514;
	($DST,$MARKETPLACE) = ('SAS','ShareASale.com');
	push @BC, { name=>'ShareASale.com',link=>'/biz/syndication/shareasale/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'Merchant ID', id=>'.merchantid', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /shoppingcom/) {
	$WEBDOC = 50538;
	($DST,$MARKETPLACE) = ('SHO','Shopping.com');
	push @BC, { name=>'Shopping.com',link=>'/biz/syndication/shoppingcom/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /thefind/) {
	$WEBDOC = 51538;
	($DST,$MARKETPLACE) = ('FND','TheFind.com');
	push @BC, { name=>'TheFind.com',link=>'/biz/syndication/thefind/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /bing/) { 
	$WEBDOC = 50918;
	($DST,$MARKETPLACE) = ('BIN','Bing.com');
	push @BC, { name=>'Bing.com',link=>'/biz/syndication/bing/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /googlebase/) { 
	$WEBDOC = 50396;
	($DST,$MARKETPLACE) = ('GOO','Google Shopping');
	push @BC, { name=>'GoogleBase.com',link=>'/biz/syndication/googlebase/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { type=>'checkbox', name=>'Google Shopping Account has Unique Identifer Exemption', id=>'.upc_exempt' };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Filename', id=>'.ftp_filename', required=>1, hint=>qq~(ex: products.xml)~};
	push @FIELDS, { type=>'checkbox', id=>'.trusted_feed', name=>'Enable Trusted Stores Shipping/Cancel Feed', required=>1 };
#	push @FIELDS, { type=>'select', name=>'Adwords Grouping', id=>'.grouping', '@options'=>[
#		[ '', 'None' ],
#		[ '0cat', 'Top
#		]};
#	push @FIELDS, { type=>'select', name=>'Adwords Labels', id=>'.labels' };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /bizrate/) { 
	$WEBDOC = 50374;
	($DST,$MARKETPLACE) = ('BZR','Shopzilla');
	push @BC, { name=>'Shopzilla',link=>'/biz/syndication/bizrate/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'Web Login Username', id=>'.user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Web Login Password', id=>'.pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /pronto/) { 
	$WEBDOC = 50538;
	($DST,$MARKETPLACE) = ('PTO','Pronto.com');
	push @BC, { name=>'Pronto.com',link=>'/biz/syndication/pronto/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /become/) { 
	$WEBDOC = 51554;
	($DST,$MARKETPLACE) = ('BCM','Become.com');
	push @BC, { name=>'Become.com',link=>'/biz/syndication/become/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /smarter/) { 
	$WEBDOC = 51555;
	($DST,$MARKETPLACE) = ('SMT','Smarter.com');
	push @BC, { name=>'Smarter.com',link=>'/biz/syndication/smarter/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /dijipop/) { 
	$WEBDOC = 51556;
	($DST,$MARKETPLACE) = ('DIJ','Dijipop.com');
	push @BC, { name=>$MARKETPLACE,link=>'/biz/syndication/dijipop/index.cgi','target'=>'_top', };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /linkshare/) { 
	$WEBDOC = 51557;
	($DST,$MARKETPLACE) = ('LNK','Linkshare.com');
	push @BC, { name=>$MARKETPLACE,link=>'/biz/syndication/linkshare/index.cgi','target'=>'_top', };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Linkshare MID', id=>'.linkshare_mid', required=>1, hint=>qq~Linkshare Merchant ID is assigned by LinkShare.~, };
	push @FIELDS, { type=>'textbox', name=>'Linkshare Company', id=>'.linkshare_company', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Linkshare Default ClassID', id=>'.linkshare_default_classid', size=>3, required=>1, hint=>qq~(ex: 140 is electronics)~, };
	}
elsif ($ENV{'SCRIPT_NAME'} =~ /hsn/) { 
	$WEBDOC = 51570;
	($DST,$MARKETPLACE) = ('HSN','HSN.com');
	push @BC, { name=>$MARKETPLACE,link=>'/biz/syndication/hsn/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Vendor ID', id=>'.vendorid', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Order FTP Server', id=>'.order_ftp_server', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Order FTP Username', id=>'.order_ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Order FTP Password', id=>'.order_ftp_pass', required=>1 };
   }
elsif ($ENV{'SCRIPT_NAME'} =~ /sears/) { 
	$WEBDOC = 51583;
	($DST,$MARKETPLACE) = ('SRS','Sears');
	push @BC, { name=>$MARKETPLACE,link=>'/biz/syndication/sears/index.cgi','target'=>'_top', };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'API User', id=>'.user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'API Password', id=>'.pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'Location ID', id=>'.location_id', required=>1, hint=>"This ID is created when a location is configured in the Sears UI." };
	push @FIELDS, { type=>'checkbox', name=>'Use Safe SKU Algorithm', id=>'.safe_sku', default=>1, hint=>"When necessary, an alternate SKU that is compatible with the marketplace will be generated. (Recommended)" };

	push @CSV_PRODUCT_EXPORT, 'Item Id|%SAFESKU';						# required
	push @CSV_PRODUCT_EXPORT, 'Action Flag|';								# optional, indicate D for DELETE
	push @CSV_PRODUCT_EXPORT, 'FBS Item|No';								# required, Yes=>Sell on Sears item (Fulfillment By Sears)
	push @CSV_PRODUCT_EXPORT, 'Variation Group ID|';					# optional, group id to associate variations together in your inventory
	push @CSV_PRODUCT_EXPORT, 'Title|zoovy:prod_name';					# required
 	push @CSV_PRODUCT_EXPORT, 'Short Description|zoovy:prod_desc';	# required, NEED to STRIP HTML/WIKI
 	push @CSV_PRODUCT_EXPORT, 'Long Description|';						# optional, NEED to STRIP HTML/WIKI
  	push @CSV_PRODUCT_EXPORT, 'Packing Slip Description|';			# NA (only used for FBS)
  	push @CSV_PRODUCT_EXPORT, 'Category|sears:category';				# required
  	push @CSV_PRODUCT_EXPORT, 'UPC|zoovy:prod_upc';						# optional
  	push @CSV_PRODUCT_EXPORT, 'Manufacturer Model #|zoovy:mfgid';	# required (40 characters max, letters, number, dash, underscores only)
  	push @CSV_PRODUCT_EXPORT, 'Cost|';										# NA (only used for FBS)
  	push @CSV_PRODUCT_EXPORT, 'Standard Price|zoovy:base_price';	# required (US dollars, without a $ sign, commas, text, or quotation marks)
  	push @CSV_PRODUCT_EXPORT, 'Sale Price|';								# optional (US dollars, without a $ sign, commas, text, or quotation marks)
	## andrew to add more fields on saturday or sunday
   }
elsif ($ENV{'SCRIPT_NAME'} =~ /newegg/) { 
	$WEBDOC = 00000;
	($DST,$MARKETPLACE) = ('EGG','Newegg');
	push @BC, { name=>$MARKETPLACE,link=>'/biz/syndication/newegg/index.cgi','target'=>'_top', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"$PATH?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @FIELDS, { align=>'left', type=>'checkbox', name=>'Is Active', id=>'.enable', default=>1, hint=>"Checkbox must be selected or syndication will not be attempted." };
	push @FIELDS, { type=>'textbox', name=>'FTP User', id=>'.ftp_user', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Password', id=>'.ftp_pass', required=>1 };
	push @FIELDS, { type=>'textbox', name=>'FTP Server', id=>'.ftp_server', required=>1 };
#	push @FIELDS, { type=>'checkbox', name=>'Enable Newegg Syndication', id=>'IS_ACTIVE', hint=>"Checkbox must be selected or syndication will not be attempted." };
   }
## TODO:
## thefind
## imshopping
## wishpot
## veruta
## shopping.com
## cj
## bin
## buysafe
## amazon product ads
else {
	$VERB = 'UNKNOWN-DST';
	push @MSGS, "ERROR|+UNKNOWN DST";
	print STDERR "UNKNOWN: $ENV{'SCRIPT_NAME'}\n";
	}



#push @TABS, { name=>"Files", selected=>($VERB eq 'FILEs')?1:0, link=>"?VERB=FILES&PROFILE=$PROFILE", };
if ($WEBDOC > 0) {
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $WEBDOC;
	push @TABS, { name=>"Webdoc", selected=>($VERB eq 'WEBDOC')?1:0, link=>"$PATH?VERB=WEBDOC&DOC=$WEBDOC&PROFILE=$PROFILE", };
	}

## some of the syndications can create a generic product csv export.
if (scalar(@CSV_PRODUCT_EXPORT)>0) {
	## commenting out until this is ready to go to production.
	#push @TABS, { name=>"Product Export", selected=>($VERB eq 'PRODUCT-CSV')?1:0, link=>"$PATH?VERB=PRODUCT-CSV&PROFILE=$PROFILE", };
	}


my ($so) = undef;
my ($DOMAIN,$ROOTPATH) = ();
if (($PROFILE ne '') && (defined $DST)) {
	($so) = SYNDICATION->new($USERNAME,$PROFILE,$DST);
	($DOMAIN,$ROOTPATH) = $so->syn_info();
	push @TABS, { name=>"History", selected=>($VERB eq 'HISTORY')?1:0, link=>"$PATH?VERB=HISTORY&PROFILE=$PROFILE", };
	if (($DST eq 'AMZ') || ($DST eq 'EBF')) {
		push @TABS, { name=>"Feed Errors", selected=>($VERB eq 'FEED-ERRORS')?1:0, link=>"$PATH?VERB=FEED-ERRORS&PROFILE=$PROFILE", };
		}
	push @TABS, { name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"$PATH?VERB=DEBUG&PROFILE=$PROFILE", };	
	}
$GTOOLS::TAG{'<!-- DOMAIN -->'} = $DOMAIN;
$GTOOLS::TAG{'<!-- ROOTPATH -->'} = $ROOTPATH;
$GTOOLS::TAG{'<!-- MARKETPLACE -->'} = $MARKETPLACE;
$GTOOLS::TAG{'<!-- DST -->'} = $DST;


if ($VERB eq 'DELETE') {
   $so->nuke();
   $VERB = '';
   }


##
##
##
if ($VERB eq 'DBMAP-NUKE') {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "delete from BUYCOM_DBMAPS where MID=$MID /* $USERNAME */ and ID=".int($ZOOVY::cgiv->{'ID'});
	print STDERR $pstmt."\n";
	$udbh->do($pstmt);
	&DBINFO::db_user_close();
	$VERB = 'DBMAP';
	}


##
##
##
if ($VERB eq 'DBMAP-SAVE') {
	my $ERROR = '';

	if (($ERROR eq '') && ($ZOOVY::cgiv->{'CATID'} eq '')) {
		$ERROR = "CatID not defined.";
		}

	if (($ERROR eq '') && ($ZOOVY::cgiv->{'STOREID'} == 0)) {
		$ERROR = "StoreID not defined.";
		}

	if (($ERROR eq '') && ($ZOOVY::cgiv->{'MAPID'} eq '')) {
		$ERROR = "MapID cannot be blank.";
		}

	if (($ERROR eq '') && ($ZOOVY::cgiv->{'MAPTXT'} eq '')) {
		$ERROR = "You must specify some JSON in the DBMAP";
		}

	if ($ERROR eq '') {
		require JSON;
		my $json = JSON->new();
		my $txt = $ZOOVY::cgiv->{'MAPTXT'};
#		$txt =~ s/,[\s]+$//;		# strip trailing comma.
		$txt =~ s/[\r]+//g;
#		$txt = "[$txt]";
#		$ZOOVY::cgiv->{'MAPTXT'} = $txt;
		my $p = eval { $json->decode($txt) } or $ERROR = "JSON Validation Error: $@";
#		use YAML::Syck;
#		$ZOOVY::cgiv->{'MAPTXT'} = YAML::Syck::Dump($p);
		$ERROR =~ s/ at \/.*?$//;	 ## get rid of at /httpd/htdocs/.... line 120
		if ($ERROR =~ /offset ([\d]+) /) {
			my ($offset) = int($1);
			my $bytes = 0;
			my $linecount = 0;
			foreach my $line (split(/[\n]/,$txt)) {
				$linecount++;
				if ( (($bytes+length($line)+5) >= $offset) && ($offset>=$bytes) ) {
					$ERROR .= "<br>LINE[$linecount] $line";
					}
				$bytes += length($line)+1;
				}
	
#			$offset -= 20;
#			if ($offset<=0) { $offset = 0; }			
#			$ERROR .= "\n<br>approximate location: ".substr($txt,$offset,40);
			}

		if (($ERROR eq '') && (int($ZOOVY::cgiv->{'CATID'})==0)) {
			## DBMAPS with CategoryID==0 means we need to be setting buycom:categoryid in the dbmap as an attribute.
			## this is a *required* field.
			my $found = 0;
			foreach my $dbmapset (@{$p}) {
				if ($dbmapset->{'id'} eq 'buycom:categoryid') { $found++; }
 				# $GTOOLS::TAG{'<!-- DEBUG -->'} .= "<hr>".Dumper($dbmapset);
				}
			if (not $found) {
				$ERROR = "Please specify the buycom:categoryid product attribute in the dbmap to use CategoryID 0";
				}
			}
		}


	if ($ERROR eq '') {
		my ($udbh) = &DBINFO::db_user_connect($USERNAME);
		&DBINFO::insert($udbh,'BUYCOM_DBMAPS',{
			USERNAME=>$USERNAME, MID=>$MID,
			MAPID=>uc($ZOOVY::cgiv->{'MAPID'}),
			STOREID=>int($ZOOVY::cgiv->{'STOREID'}),
			CATID=>int($ZOOVY::cgiv->{'CATID'}),
			MAPTXT=>$ZOOVY::cgiv->{'MAPTXT'},
			},key=>['MID','MAPID']);
		&DBINFO::db_user_close();
		push @MSGS, "SUCCESS|Added DBMAP $ZOOVY::cgiv->{'MAPID'}";
		}
	else {
		push @MSGS, "ERROR|ERROR: $ERROR";
		}

	$VERB = 'DBMAP';
	}


##
##
##
if (($VERB eq 'DBMAP') || ($VERB eq 'DBMAP-EDIT')) {

#	my $cattxt = '';
#	if ($prodref->{'buycom:category'}>0) {
#		## This works  - try to save '7000.50845' into category for example.
#		my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad('BUY');
#		my ($inforef) = SYNDICATION::CATEGORIES::CDSInfo($CDS,$prodref->{'buycom:category'});
#		$cattxt = $inforef->{'Path'};
#		}

	my $udbh = &DBINFO::db_user_connect($USERNAME);
	my $ref = $ZOOVY::cgiv;	## we'll copy from CGI params incase we're reloading

	if ($VERB eq 'DBMAP-EDIT') {
		my $pstmt = "select * from BUYCOM_DBMAPS where MID=$MID /* $USERNAME */ and MAPID=".$udbh->quote($ZOOVY::cgiv->{'ID'});
		$ref = $udbh->selectrow_hashref($pstmt);
		}

	$GTOOLS::TAG{'<!-- MAPID -->'} = $ref->{'MAPID'};
	$GTOOLS::TAG{'<!-- CATID -->'} = $ref->{'CATID'};
	$GTOOLS::TAG{'<!-- MAPTXT -->'} = $ref->{'MAPTXT'};

	my $c = '';
	foreach my $x (@{$SYNDICATION::BUYCOM::STORECODES}) {
		my $selected = ($ref->{'STOREID'}==$x->{'id'})?'selected':'';
		$c .= "<option $selected value=\"$x->{'id'}\">$x->{'title'}</option>\n";
		}
	$GTOOLS::TAG{'<!-- STORECODES -->'} = $c;

	$c = '';
	my @maps = &SYNDICATION::BUYCOM::fetch_dbmaps($USERNAME);
	my $class = '';
	foreach my $map (@maps) {
		$class = ($class eq 'r0')?'r1':'r0';
		$c .= "<tr class=\"$class\">";
		$c .= "<td valign=top>";
			$c .= "<a href=\"$PATH?VERB=DBMAP-EDIT&ID=$map->{'MAPID'}\">[Edit]</a>";
			$c .= "<a href=\"$PATH?VERB=DBMAP-NUKE&ID=$map->{'MAPID'}\">[Nuke]</a>";
		$c .= "</td>";
		$c .= "<td valign=top>$map->{'MAPID'}</td>";
		$c .= "<td valign=top>$map->{'STOREID'}</td>";
		$c .= "<td valign=top>$map->{'CATID'}</td>";
		my $mapjrefs = JSON::XS::decode_json($map->{'MAPTXT'});
		$c .= "<td valign=top>";
			foreach my $jref (@{$mapjrefs}) {
				$c .= "<b>$jref->{'id'}: $jref->{'header'}</b><br>";
				if ((defined $jref->{'options'}) && (ref($jref->{'options'}) eq 'ARRAY')) {
					$c .= "<i>Values: ";
					foreach my $opt (@{$jref->{'options'}}) { $c .= "$opt->{'p'} "; }
					$c .= "</i><br>";
					}
				# $c .= Dumper($jref)."<hr>";
				}
		$c .= "</td>";
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=4><i>No Buy.com DBMaps currently defined</i></td></tr>";
		}

	&DBINFO::db_user_close();
	$GTOOLS::TAG{'<!-- EXISTING_MAPS -->'} = $c;

	$template_file = 'dbmap.shtml';
	}


##
##
##
if ($VERB eq 'FILES') {
	require LUSER::FILES;
	my ($LF) = LUSER::FILES->new($USERNAME,LU=>$LU);

	my $type = '';
	if ($DST eq 'BUY') { $type = 'BUYCOM'; }

	my $results = $LF->list(type=>$type);
	my $c = '';
	foreach my $file (@{$results}) {
		$c .= "<tr>";
		$c .= "<td>$file->{'%META'}->{'type'}</td>";
		$c .= "<td><a href=\"/biz/setup/private/index.cgi/$file->{'TITLE'}?VERB=DOWNLOAD&GUID=$file->{'GUID'}&FILE=$file->{'FILE'}\">$file->{'TITLE'}</a></td>";
		$c .= "<td>$file->{'CREATED'}</td>";
		$c .= "<td>$file->{'SIZE'}</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- FILES -->'} = $c;
	# $GTOOLS::TAG{'<!-- FILES -->'} = '<table><tr><td><pre>'.Dumper($results).'</pre></td></tr></table>';
	$template_file = '_/syndication-files.shtml';
	}


#if ($VERB eq 'FILES') {
#	my ($lf) = LUSER::FILES->new($USERNAME);
#	$template_file = 'files.shtml';
#	}


if (($VERB eq 'SAVE') || ($VERB eq 'SAVE-AND-PUBLISH')) {
	tie my %s, 'SYNDICATION', THIS=>$so;

	my $ERROR = '';

	$so->{'IS_SUSPENDED'} = 0;
	$so->{'IS_ACTIVE'} = 1;

	## (almost!!) all syndication use FTP settings to push feeds
	foreach my $fref (@FIELDS) {
		my $user_data = $ZOOVY::cgiv->{ $fref->{'id'} };

		if ($fref->{'type'} eq 'checkbox') {
			## checkboxes are special! converts to 1/0
			$user_data = ($user_data eq 'on')?1:0;
			}

		$user_data =~ s/^[\s]+//gs;	 # strip leading space
		$user_data =~ s/[\s]+$//gs;	# strip trailing space
		if ($fref->{'id'} eq '.ftp_server') {
			$user_data =~ s/^ftp\:\/\///igs;
			if ($user_data =~ /[^A-Za-z0-9\.\-]+/) { $ERROR = "$MARKETPLACE FTP Server contains invalid characters (perhaps you're sending a URI?)"; }
			elsif (($DST eq 'BCM') && ($user_data !~ /\.become\.com$/)) { $ERROR = "FTP server [$user_data] does not end with .become.com - it's probably not valid!"; }
			elsif (($DST eq 'GOO') && ($user_data !~ /google\.com$/)) { $ERROR = "FTP server does not end with .google.com - it's probably not valid!"; }
			}
		elsif ($fref->{'id'} eq '.linkshare_mid') {
			if ($user_data==0) { $ERROR = "Linkshare Merchant ID is required"; }
			}
		
		if ($fref->{'id'} eq '.enable') {
			$so->{'IS_ACTIVE'} = $user_data;
			}

		$s{ $fref->{'id'} } = $user_data;
		if (($fref->{'required'}) && ($user_data eq '')) {
			$ERROR = "$MARKETPLACE $fref->{'name'} is required";
			}
		}

	## it doesnt appear that username or password is required for FTP but we will store for tech troubleshooting
	if ($DST eq 'GOO') {
		$s{'.feed_options'} = 0;
		$s{'.feed_options'} |= ($ZOOVY::cgiv->{'navcat_skiphidden'})?1:0;
		$s{'.feed_options'} |= ($ZOOVY::cgiv->{'navcat_skiplists'})?4:0;
		$s{'.include_shipping'} = ($ZOOVY::cgiv->{'include_shipping'})?1:0;
		$s{'.ignore_validation'} = ($ZOOVY::cgiv->{'ignore_validation'})?1:0;
		}
	## done with validation

	if ($LU->is_zoovy()) {
		$s{'INFORM_ZOOVY_MARKETING'} = (defined $ZOOVY::cgiv->{'INFORM_ZOOVY_MARKETING'})?1:0;
		}

	$s{'.schedule'} = undef;
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'SCHEDULE'};
      }

	if ($ERROR ne '') {
		push @MSGS, "ERROR|+$ERROR";
		}
	else {
		if ($s{'IS_SUSPENDED'}>0) {
			$s{'IS_SUSPENDED'} = 0;
			$so->appendtxlog("SETUP","Set IS_SUSPENDED=0 by $LUSERNAME");
			}
		$so->save();
		}



	if ($ERROR ne '') {
		$VERB = 'EDIT';
		}
	elsif ($VERB eq 'SAVE-AND-PUBLISH') {
		$VERB = 'PUBLISH';
		}
	else {
		$VERB  = 'EDIT';
		}
	untie %s;
	}


if ($VERB eq 'PUBLISH') {

	my $c = '';
	if ($SYNDICATION::PROVIDERS{$DST}->{'send_products'}>0) {
		$c .= qq~<div><input type="radio" name="FEEDTYPE" value="PRODUCT"> Product Feed</div>\n~;
		}
	if ($SYNDICATION::PROVIDERS{$DST}->{'send_inventory'}>0) {
		$c .= qq~<div><input type="radio" name="FEEDTYPE" value="INVENTORY"> Inventory Feed</div>\n~;
		}
	if ($SYNDICATION::PROVIDERS{$DST}->{'send_pricing'}>0) {
		$c .= qq~<div><input type="radio" name="FEEDTYPE" value="PRICING"> Pricing Feed</div>\n~;
		}
	if ($c eq '') {
		$c .= "<div class=\"error\">Regrettably, no feeds are manually publishable for this destination</div>\n";
		}
	$GTOOLS::TAG{'<!-- SUPPORTED_FEED_TYPES -->'} = $c;

	$template_file = 'publish.shtml';
	}


if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}



if ($VERB eq 'BATCH-UPDATE') {
	my $changed = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	my $batchregex = '^'.quotemeta($ZOOVY::cgiv->{'batch-path'});
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next unless ($safe =~ /$batchregex/);
		print STDERR "SAVED: $safe\n";
		$changed++;
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		$metaref->{$DST} = $ZOOVY::cgiv->{'batch-category'};
      $NC->set($safe,metaref=>$metaref);
		}
	$NC->save(); 
	undef $NC;
	$GTOOLS::TAG{'<!-- MSG -->'} = "<div class='success'>Successfully updated $changed categories.</div>";
	$VERB = 'CATEGORIES';
	}



if ($VERB eq 'PRODUCT-CSV') {
	
	$template_file = 'productcsv.shtml';
	}


if ($VERB eq 'SAVE-EBAY-CATEGORIES') {
	my $changed = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe ($NC->paths()) {
		next if (not defined $ZOOVY::cgiv->{'navcat-'.$safe});
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (($metaref->{'EBAYSTORE_CAT'} eq $ZOOVY::cgiv->{'navcat-'.$safe}) && ($metaref->{'EBAY_CAT'} eq $ZOOVY::cgiv->{'ebay-'.$safe}));
		$metaref->{'EBAYSTORE_CAT'} = $ZOOVY::cgiv->{'navcat-'.$safe};
		$metaref->{'EBAY_CAT'} = $ZOOVY::cgiv->{'ebay-'.$safe};

		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save(); undef $NC;

	push @MSGS, "SUCCESS|Updated eBay.com/eBay Store relationships with Website Categories";

	$VERB = 'EBAY-CATEGORIES';
	}


if ($VERB eq 'EBAY-CATEGORIES') {
	require EBAY2;
	require TOXML;

	$template_file = 'ebay-categories.shtml';
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my ($toxml) = TOXML->new('DEFINITION','ebay.auction',USERNAME=>$USERNAME,MID=>$MID);
	my $catref = $toxml->getList('EBAYCAT');

	my %categories = ();
	$categories{''} = 'Not Set';
	## reverse the categories
	foreach my $opt (@{$catref}) {
		$categories{$opt->{'V'}} = $opt->{'T'};
		}

	## SETUP EBAY CATEGORIES
	# &EBAYINFO::grab_storecats($USERNAME);
	my @EBAYCATS = @{&EBAY2::fetch_storecats($USERNAME,$PROFILE)};
	

	##
	## SANITY:  at this point the @EBAYCATS array is populated!
	##
	my $c = '';
	use Data::Dumper;
	
	my $bgcolor = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');

		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		# print STDERR "META: $meta\n";
		# next if (substr($pretty,0,1) eq '!'); 		# why not let them use hidden categories

		if ($bgcolor eq 'FFFFFF') { $bgcolor='DEDEDE'; } else { $bgcolor = 'FFFFFF'; }

		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,$safe)) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}
		my $val = $metaref->{'EBAYSTORE_CAT'};
		$c .= "<tr bgcolor='$bgcolor'>";
		$c .= "<td nowrap>$name</td><td>";
		$c .= "<select name=\"navcat-$safe\">";
		$c .= "<option value=\"\">Not Configured</option>";
		my $selected = '';
		my $found = 0;
		foreach my $cat (@EBAYCATS) {
			my ($catnum,$catname) = split(/,/,$cat,2);
			if ($val eq $catnum) { $found++; $selected = ' selected '; } else { $selected = ''; }
			$c .= "<option $selected value=\"$catnum\">$catname ($catnum)</a>";
			}
		if (($found == 0) && ($val ne '')) {
			$c .= "<option selected value=\"$val\">INVALID: $val</option>\n";
			}
		$c .= "</td>";

		$val = $metaref->{'EBAY_CAT'};
		$c .= "<td valign='top'><input name=\"ebay-$safe\" type=\"textbox\" size=\"6\" value=\"$val\"></td>";
		$c .= "<td valign='top'><a href=\"javascript:openWindow('/biz/syndication/ebay/catchooser2008.cgi?V=ebay-$safe');\">[Choose]</a></td>";
		my $fullname = &EBAY2::get_cat_fullname($USERNAME,$val);
                $fullname ||= '[not set]';
                $c .= "<td valign='top'>".$fullname."</td>";
		$c .= "</tr>\n";
		}
	if ($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	push @BC, { name=>"Map Categories" };
	}

	

##
##
##
##
##


if ($VERB eq 'SAVE-CATEGORIES') {
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		my $SUBMIT = ($ZOOVY::cgiv->{'navcat-'.$safe} ne '')?$ZOOVY::cgiv->{'navcat-'.$safe}:'';
		if ($SUBMIT eq '- Ignore -') { $SUBMIT = ''; }

		## googlebase has GOO as DSTCODE and GOOGLEBASE as navcatMETA
		## - product syndication and index.cgi?VERB=CATEGORIES currently use the navcatMETA vs DSTCODE
		#$metaref->{$DST} = $SUBMIT;
		$metaref->{$DST} = $SUBMIT;
		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save();
	undef $NC;
	$GTOOLS::TAG{'<!-- MSG -->'} = "<div class='success'>Successfully saved $MARKETPLACE categories.</font>";
	$VERB = 'CATEGORIES';
	}



if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = time();

	## probably better ways to deal with this... maybe change /httpd/servers/syndication/batch.pl instead
	## some syndications [SRS currently, but more to come] only syndicate inv, so PUBLISH NOW link should 
	##		default to the INVENTORY FEEDTYPE
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</b><br>";
		$c .= "<a href=\"$PATH?VERB=EDIT&DST=$DST&PROFILE=$ns\">EDIT</a>";
		$c .= " | ";
		$c .= "<a href=\"$PATH?VERB=PUBLISH&DST=$DST&PROFILE=$ns&GUID=$ts\">PUBLISH</a>";
		$c .= " | ";
		$c .= "<a href=\"$PATH?VERB=HISTORY&DST=$DST&PROFILE=$ns\">HISTORY</a>";
		$c .= "</td>";
		$c .= "</tr>";
		my ($s) = SYNDICATION->new($USERNAME,$ns,$DST);
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';

	## NOTE: if we only have one profile, then lets just head straight to edit
	if (scalar( keys %{$profref} )==1) {
		($PROFILE) = keys %{$profref};
		$VERB = 'EDIT';
		}

	}


if ($PROFILE ne '') {
	push @BC, { name=>'Profile: '.$PROFILE };
	if ($VERB eq 'EDIT') { push @BC, { name=>'Config' };  }
	if ($VERB eq 'CATEGORIES') { push @BC, { name=>'Categories' }; }
	if ($VERB eq 'PUBLISH') { push @BC, { name=>'Publish Feed' }; }
	if ($VERB eq 'FILES') { push @BC, { name=>'Files' }; }
	if ($VERB eq 'PRODUCT-CSV') { push @BC, { name=>'Product CSV Export' }; }
	}


##
##
##
if ($VERB eq 'PUBLISH-NOW') {
	## .FEEDTYPE
	if ($FEEDTYPE eq '') { $FEEDTYPE = 'FEED-TYPE-PASSED-WAS-BLANK-AND-THAT-WILL-NOT-WORK'; }

	require URI::Escape;
	#$PROFILE = URI::Escape::uri_escape($PROFILE);
	#$FEEDTYPE = URI::Escape::uri_escape($FEEDTYPE);

	require BATCHJOB;
	my $GUID = &BATCHJOB::make_guid();
	my %VARS = (
		'VERB'=>'ADD',
		'DST'=>$DST,
		'PROFILE'=>$PROFILE,
		'FEEDTYPE'=>$FEEDTYPE,		
		);
	my ($bj) = BATCHJOB->new($USERNAME,0,
		PRT=>$PRT,
		GUID=>$ZOOVY::cgiv->{'GUID'},
		EXEC=>'SYNDICATION',
		VARS=>&ZTOOLKIT::buildparams(\%VARS,1),
		'*LU'=>$LU,
		);
	if (not defined $bj) {
		push @MSGS, "ERROR|+Could not add job"; 
		}
	else {
		$bj->start();
		push @MSGS, "SUCCESS|BATCH:".$bj->id()."|+Job ".$bj->id()." has been started.";
		}
	$GTOOLS::TAG{'<!-- JOBID -->'} = $bj->id();
	$VERB = 'EDIT';
	}






if (not defined $so) {
	}
elsif ($VERB eq 'EDIT') {
	tie my %s, 'SYNDICATION', THIS=>$so;

	my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
	if ($nsref->{'zoovy:site_rootcat'} eq '') { $nsref->{'zoovy:site_rootcat'} = '.'; }
	$GTOOLS::TAG{'<!-- ROOTCAT -->'} = $nsref->{'zoovy:site_rootcat'};
	$GTOOLS::TAG{'<!-- PRT -->'} = $nsref->{'prt:id'};

	if ($LU->is_zoovy()) {
		##
		my $is_checked = $s{'INFORM_ZOOVY_MARKETING'}?'checked':'';
		$GTOOLS::TAG{'<!-- ZOOVY_MARKETING -->'} = qq~
<tr>
	<td colspan=2 class="zoovytableheader">*** ZOOVY EMPLOYEE ACCESS ***</td>
</tr>
<tr>
	<td colspan=2>
	<input type="checkbox" $is_checked name="INFORM_ZOOVY_MARKETING"> FEED IS MANAGED BY MARKETING.
	</td>
</tr>
~;
		}
	elsif ($s{'INFORM_ZOOVY_MARKETING'}) {
		##
		$GTOOLS::TAG{'<!-- ZOOVY_MARKETING -->'} = qq~
<tr>
	<td colspan=2>
	<div class="warning">
	NOTE: This feed is managed by Zoovy Marketing Services.
	<div class="hint">
	Please contact your marketing liason for questions, or prior to making any changes.	
	</div>
	</div></td>
</tr>
~;
		}

	foreach my $fref (@FIELDS) {
		my $html = '';

		if ($fref->{'type'} eq 'checkbox') {
			my ($checked) = '';
			if (defined $s{$fref->{'id'}}) { 
				$checked = ($s{$fref->{'id'}})?'checked':''; 
				}
			else {
				$checked = ($fref->{'default'})?'checked':'';
				}
			$html .= qq~<tr>~;
			if ($fref->{'align'} eq 'left') {
				## left aligned checkbox.
				$html .= qq~<td colspan=2 align=left>~;
				$html .= sprintf(qq~<input type="checkbox" name="%s" $checked>~,$fref->{'id'},&ZOOVY::incode($s{$fref->{'id'}}));
				$html .= qq~ <b>$fref->{'name'}</b>~;
				$html .= qq~</td>~;
				}
			else {
				## right (two column) aligned checkbox
				$html .= qq~<td align=right>~;
				$html .= sprintf(qq~<input type="checkbox" name="%s" $checked>~,$fref->{'id'},&ZOOVY::incode($s{$fref->{'id'}}));
				$html .= qq~</td><td><b>$fref->{'name'}</b>~;
				$html .= qq~</td>~;
				}
			$html .= qq~</tr>~;
			}
		elsif ($fref->{'type'} eq 'textbox') {
			## textbox, select list
			$html .= qq~
	<tr>
		<td valign=top><b>$MARKETPLACE $fref->{'name'}</b></td>
		<td valign=top>~;
			$html .= sprintf(
			qq~<input type="textbox" name="%s" value="%s">~,
			$fref->{'id'},&ZOOVY::incode($s{$fref->{'id'}}));
			$html .= qq~</td>
		</tr>
			~;
			}
		elsif ($fref->{'type'} eq 'select') {
			
			}
		elsif ($fref->{'type'} eq 'hint') {
			## type=>hint, msg=>''
			$html .= qq~
	<tr>
		<td colspan=2><div class='hint'>$fref->{'msg'}</div></td>
	</tr>
			~;
			}
		elsif ($fref->{'type'} eq 'warning') {
			## type=>hint, msg=>''
			$html .= qq~
	<tr>
		<td colspan=2><div class='warning'>$fref->{'msg'}</div></td>
	</tr>
			~;
			}
		else {
			$html .= "**ERROR UNKNOWN INPUT TYPE:$fref->{'type'}**";
			}

		if ($fref->{'hint'}) {
			$html .= qq~<tr><td colspan=2><div class="hint">$fref->{'hint'}</div></td></tr>~;
			}

		$GTOOLS::TAG{'<!-- FEED_TYPE_FIELDS -->'} .= $html;
		}


	if ($DST eq 'NXT') {
		$s{'.format'} = $ZOOVY::cgiv->{'format'};
		}
	elsif ($DST eq 'GOO') {
		my $CHK_NAVCAT_SKIPHIDDEN = (($s{'.feed_options'}&1)>0)?'checked':'';
		my $CHK_NAVCAT_SKIPLISTS = (($s{'.feed_options'}&4)>0)?'checked':'';
		my $CHK_INCLUDE_SHIPPING = (($s{'.include_shipping'}&1)>0)?'checked':'';
		my $CHK_IGNORE_VALIDATION = (($s{'.ignore_validation'}&1)>0)?'checked':'';
		my $STUPID_WARNING = '';
		if (! $s{'.ignore_validation'}) {
			## good user! 
			}
		elsif (($s{'.ignore_validation'}) && ($FLAGS =~ /,BPP,/)) {
			$s{'.ignore_validation'} = 0;
			$so->save();		
			$STUPID_WARNING = qq~
<div class="warning">
SORRY - but as a BPP user you may not use the "ignore validation logic" because 
it would create an unsupported profile.  (Read webdoc - you probably didn't want this anyway)
</div>
~;
			}
		elsif ($s{'.ignore_validation'}) {
			$STUPID_WARNING = qq~
<div class="warning">
WARNING: Ignoring validation logic is *NOT* a recommended setting. Your items probably won't appear correctly
on GoogleBase. 
</div>
~;
			}

		$GTOOLS::TAG{'<!-- MID_FIELDS -->'} = qq~
		<tr>
			<td colspan=2>
			<b>Options:</b><br>
			<input type="checkbox" $CHK_NAVCAT_SKIPHIDDEN name="navcat_skiphidden" value="on"> Skip hidden navigation categories.<br>
			<input type="checkbox" $CHK_NAVCAT_SKIPLISTS  name="navcat_skiplists" value="on"> Skip lists.<br>
			<input type="checkbox" $CHK_INCLUDE_SHIPPING name="include_shipping" value="on"> Include Fixed Cost Shipping Prices.<br>
			<input type="checkbox" $CHK_IGNORE_VALIDATION name="ignore_validation" value="on"> Skip recommended validation logic<br>
			$STUPID_WARNING
			</td>
		</tr>
		~;
		}

	if ($DST eq 'SAS') {
	my ($url) = $so->get('.url');
	$url =~ s/site\:\/\//http\:\/\/static\.zoovy\.com\/merchant\/$USERNAME\//;
$GTOOLS::TAG{'<!-- TOP_FIELDS -->'} = qq~
	<tr>
		<td>
		NOTE: Share-A-Sale does NOT have an automated way to send a feed.
You will need to generate the feed by hand, and then manually download +
upload it as frequently as you wish to have it updated.<br>
<br>
Once the file has been generated you can download it from the URL below:<br>
<a href="$url">$url</a>
		</td>
	</tr>
~;

$GTOOLS::TAG{'<!-- BOTTOM_FIELDS -->'} = qq~
<div class="hint">NOTE: Share-A-Sale does not accept automated feeds, for this reason the
feed will never be "ACTIVE" since it cannot be automatically
transmitted.</div><br>
~;
		}


	if ($DST eq 'NXT') {
		$GTOOLS::TAG{'<!-- TOP_FIELDS -->'} = qq~
   <tr>
      <td><b>Product Upload Location<br>(used in NexTag UI):</b></td>
      <td nowrap>
			<a href="http://webapi.zoovy.com/webapi/nextag/index.cgi/$USERNAME.$PROFILE.txt">
			http://webapi.zoovy.com/webapi/nextag/index.cgi/$USERNAME.$PROFILE.txt
			</a>
		</td>
   </tr>
   <tr>
      <td colspan='2'>
      <b>Output File Format:</b><br>
         <input type="radio" name="format" ~.(($s{'.format'}==0)?'checked':'').qq~ value="0"> Soft Goods (RECOMMENDED)<br>
         <input type="radio" name="format" ~.(($s{'.format'}==1)?'checked':'').qq~ value="1"> Tech Feed (Electronics Only)<br>
      </td>
   </tr>
~;
		}

   $GTOOLS::TAG{'<!-- GUID -->'} = $so->guid();
   $GTOOLS::TAG{'<!-- VIEW_URL -->'} = $so->url_to_privatefile();
	$GTOOLS::TAG{'<!-- PRODUCT_VALIDATION -->'} = $so->pleaseSirMayIHaveSomeValidations();

	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

	if ($FLAGS =~ /,WS,/) {
		my $c = '';
		require WHOLESALE;
		$c = "<option value=\"\">None</option>";
		foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
			$c .= "<option ".(($s{'.schedule'} eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
			}
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;
		}
	else { 
		$s{'.schedule'} = '';
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = '<option value="">Not Available</option>'; 
		}

	$template_file = 'edit.shtml';
	#if ($DST eq 'EBF') {
	#	$template_file = 'edit-ebay.shtml';
	#	}
	}

if ($VERB eq 'CLEAR-FEED-ERRORS') {
	my ($udbh) = &DBINFO::db_user_connect($so->username());
	my $pstmt = "update SYNDICATION_PID_ERRORS set ARCHIVE_GMT=$^T where MID=$MID /* $USERNAME */ and DSTCODE=".$udbh->quote($so->dstcode());
	$udbh->do($pstmt);
	&DBINFO::db_user_close();
	$VERB = 'FEED-ERRORS';
	}

if ($VERB eq 'FEED-ERRORS') {
	my $udbh = &DBINFO::db_user_connect($so->username());
	my ($MID) = $so->mid();
	my ($USERNAME) = $so->username();
	my @RESULTS = ();

	my $pstmt = "select CREATED_GMT,SKU,FEED,ERRCODE,ERRMSG,BATCHID from SYNDICATION_PID_ERRORS where MID=$MID /* $USERNAME */  and DSTCODE=".$udbh->quote($so->dstcode())." ";
	$pstmt .= " and ARCHIVE_GMT=0 ";
	$pstmt .= " order by CREATED_GMT desc limit 0,500";
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my @row = $sth->fetchrow() ) {
		push @RESULTS, \@row;
		}
	$sth->finish();
	&DBINFO::db_user_close();

	if (scalar(@RESULTS)==0) {
		push @RESULTS, [ '', 'NOTE', 0,0,0, 'No errors available.' ];
		}

	my $c = '';
	if ($DST eq 'EBF') {
		$GTOOLS::TAG{'<!-- CLEAR_FEED_ERRORS_LINK -->'} = "<tr><td colspan=5><a href=\"$PATH?VERB=CLEAR-FEED-ERRORS&PROFILE=$PROFILE\">Clear Feed Errors</a></td></tr>";
		}

	foreach my $logset (@RESULTS) {
		$c .= "<tr>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($logset->[0],1)."</td>";
		$c .= "<td>$logset->[1]</td>";
		$c .= "<td>$logset->[2]</td>";
		$c .= "<td>$logset->[3]</td>";
		$c .= "<td>$logset->[4]</td>";
		$c .= "<td>$logset->[5]</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- LOGS -->'} = $c;

   $template_file = '_/syndication-feederrors.shtml';
	}


if ($VERB eq 'HISTORY') {
	my ($MID) = $so->mid();
	my ($USERNAME) = $so->username();
	my @RESULTS = ();


	#my $pstmt = "select CREATED,FEEDTYPE,SKU_TOTAL,SKU_VALIDATED,SKU_TRANSMITTED,NOTE from SYNDICATION_SUMMARY where MID=$MID /* $USERNAME */ ";
	#$pstmt .= " and DSTCODE=".$udbh->quote($so->dstcode())." ";
	#$pstmt .= " and PROFILE=".$udbh->quote($so->profile())." "; 
	#$pstmt .= " order by CREATED desc limit 0,100";
	#print STDERR $pstmt."\n";
	#my $sth = $udbh->prepare($pstmt);
	#$sth->execute();
	#while ( my @row = $sth->fetchrow() ) {
	#	if ($row[1] eq '') { $row[1] = 'NOTE'; }
	#	push @RESULTS, \@row;
	#	}
	#$sth->finish();
	#if (scalar(@RESULTS)==0) {
	#	push @RESULTS, [ '', 'NOTE', 0,0,0, 'No logs available.' ];
	#	}


	#my $c = '';
	#foreach my $logset (@RESULTS) {
	#	$c .= "<tr>";
	#	$c .= "<td>$logset->[0]</td>";
	#	$c .= "<td>$logset->[1]</td>";
	#	if ($logset->[1] eq 'NOTE') {
	#		$c .= "<td colspan=3>$logset->[5]</td>";
	#		}
	#	else {
	#		$c .= "<td>$logset->[2]</td>";
	#		$c .= "<td>$logset->[3]</td>";
	#		$c .= "<td>$logset->[4]</td>";
	#	$c .= "</tr>";
	#	}

	my $c = '';
	
	require TXLOG;
	# my ($tx) = TXLOG->new($so->{'TXLOG'});
	#foreach my $line (@{$tx->lines()}) {
	#	}
	# my $c = "<pre>".Dumper($tx)."</pre>";

	my $r = '';	
	foreach my $line (reverse split(/\n/,$so->{'TXLOG'})) {
		$r = ($r eq 'r0')?'r1':'r0';
		my ($UNI,$TS,$PARAMSREF) = TXLOG::parseline($line);
		$c .= sprintf("<tr class='$r'><td>%s</td><td>%s</td><td>%s</td></tr>\n",&ZTOOLKIT::pretty_date($TS,2),$UNI,$PARAMSREF->{'+'});
		}

	$GTOOLS::TAG{'<!-- HISTORY -->'} = $c;

   $template_file = 'syndication-history.shtml';
   }

## BEGIN DEBUGGER
if ($VERB eq 'GOGO-DEBUG') {
	my ($feed_type) = $ZOOVY::cgiv->{'feed_type'};
	if ($feed_type eq '') { $feed_type = 'product'; }
	print STDERR "FEED_TYPE: $feed_type\n";
	$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = $so->runDebug(type=>$feed_type,TRACEPID=>$ZOOVY::cgiv->{'PID'});
	$VERB = 'DEBUG';
	}

if ($VERB eq 'DEBUG') {
	if ($GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} eq '') { 
		$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = '<i>Please specify a product</i>'; 
		}
	if ($DST eq 'BUY') {
		$GTOOLS::TAG{'<!-- SPECIAL_OPTIONS -->'} = qq~
<b>Feed Type:</b><br>
<div><input type="radio" name="feed_type" value="product"> Product Feed</div>
<div><input type="radio" name="feed_type" value="inventory"> Inventory Feed</div>
~;
		}
	if ($DST eq 'SRS') {
		$GTOOLS::TAG{'<!-- SPECIAL_OPTIONS -->'} = qq~
<b>Feed Type:</b><br>
<div><input type="radio" name="feed_type" value="pricing"> Pricing Feed</div>
<div><input type="radio" name="feed_type" value="inventory"> Inventory Feed</div>
~;
		}
	$GTOOLS::TAG{'<!-- PID -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'PID'});
	$template_file = '_/syndication-debug.shtml';
	}
## END DEBUGGER


if ($VERB eq 'CATEGORIES') {
	require SYNDICATION::CATEGORIES;
	my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad($DST);
	my $pathref = SYNDICATION::CATEGORIES::CDSByPath($CDS);

	my $c = '';
	if ($DST eq 'WSH') {
		## wishpot has 0 and -1 specified as valid options to choose in their category file
		}
	elsif (($DST eq 'GOO') || ($DST eq 'ESS')) {
		$c .= qq~me.options.add(new Option("Block all products in category","-2"));\n~;
		$c .= qq~me.options.add(new Option("Do not submit category","-1"));\n~;
		$c .= qq~me.options.add(new Option("Send Uncategorized","0"));\n~;
		}
	else {
		$c .= qq~me.options.add(new Option("Block all products in category","-2"));\n~;
		$c .= qq~me.options.add(new Option("Do not submit category","-1"));\n~;
		$c .= qq~me.options.add(new Option("Ignore Category","0"));\n~;
		}

   foreach my $pretty (sort keys %{$pathref}) {
		my $val = $pathref->{$pretty};
		$pretty = ZOOVY::incode($pretty);
      $c .= qq~me.options.add(new Option("$pretty","$val"));\n~;
      }
   $GTOOLS::TAG{'<!-- OPTIONS -->'} = $c;

	my $c = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	#if (defined $SYNDICATION::PROVIDERS{$DST}->{'navcatMETA'}) {
	#	## eventually we should consolidate down so everybody uses the DST as the navcatMETA
	#	$navcatMETA = $SYNDICATION::PROVIDERS{$DST}->{'navcatMETA'};
	#	}

	my ($r) = undef;
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (substr($pretty,0,1) eq '!');
		$r = ($r eq 'r0')?'r1':'r0';
	
		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,substr($safe,1))) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}
		my $val = $metaref->{$DST};

		## take out legacy commas (mostly in BZR-Shopzilla)
		$val =~ s/,//g;		

		## check if val is in the legacy text format
		if ($val eq '') {
			$val = 0;
			}
		elsif ($val !~ /^\d+$/) {
			$val =~ s/ > />/g;
			if (defined $pathref->{$val}) {
				$val = $pathref->{$val};
				}
			}	

		$c .= "<tr class=\"$r\">";
		$c .= "<td nowrap>
		<div>$name</div>
		<div class=\"hint\">$safe</div>
		</td>";
		
		my ($iref) = SYNDICATION::CATEGORIES::CDSInfo($CDS,$val);
		$pretty = $iref->{'Path'};

		$c .= qq~<td nowrap>~;
		$c .= qq~<button class="minibutton" type="button" 
			onClick="selectCategory('$DST','navcat-$safe',document.catFrm['navcat-$safe'].value);" 
			>Choose</button>~;
		$c .= qq~<input type="textbox" onChange="ajaxUpdate($DST,this);" value="$val" name="navcat-$safe" size="5"></td>~;
		$c .= qq~<td nowrap><span id="txt!navcat-$safe">$pretty</span></td>~;
		$c .= "</tr>\n";

		}
	if	($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;

	$template_file = 'categories.shtml';
	}




&GTOOLS::output('*LU'=>$LU,
	'title'=>"$MARKETPLACE Syndication",
	'file'=>$template_file,
	'header'=>'1',
	'help'=>"#$WEBDOC",
	'tabs'=>\@TABS,
	'jquery'=>1,
	'msgs'=>\@MSGS,
	'bc'=>\@BC,
	);


