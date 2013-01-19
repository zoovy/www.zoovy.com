#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require LUSER;
require DOMAIN::QUERY;
require DOMAIN;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my $ts = time();
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $VERB = $ZOOVY::cgiv->{'ACTION'};
if ($VERB eq '') { $VERB = $ZOOVY::cgiv->{'VERB'}; }
if ($VERB eq '') { $VERB = 'MARKETPLACES'; }

my $template_file = '';

my @MSGS = ();
my @BC = ();
push @BC, { name=>'Syndication',link=>'/biz/syndication/index.cgi','target'=>'_top', };



my @domains = ();
if ($VERB eq 'DOMAINS-SAVE') {
	$VERB = 'DOMAINS';
	(@domains) = &DOMAIN::QUERY::domains($USERNAME,'PRT'=>$PRT);
	foreach my $domain (@domains) {
		my ($D) = DOMAIN->new($USERNAME,$domain);
		my $is_checked = &ZOOVY::is_true($ZOOVY::cgiv->{"domain:$domain"});
	
		if ($is_checked == $D->syndication_enable()) {
			## nothing to see here, move along.
			}
		else {
			push @MSGS, sprintf("SUCCESS|Updated domain $domain to %s",($is_checked)?'enabled':'disabled');
			$D->syndication_enable($is_checked);
			$D->save();
			}

		my ($checked) = $D->syndication_enable()?'checked':'';
		}
	}

if ($VERB eq 'DOMAINS') {
	push @BC, { name=>'Domain Management',link=>'/biz/syndication/index.cgi?VERB=DOMAINS','target'=>'_top', };
	if (scalar(@domains)==0) { @domains = &DOMAIN::QUERY::domains($USERNAME,'PRT'=>$PRT); }
	my $c = '';
	my $r = '';
	foreach my $domain (sort @domains) {
		($r) = ($r eq 'r0')?'r1':'r0';
		my ($D) = DOMAIN->new($USERNAME,$domain);
		my ($checked) = $D->syndication_enable()?'checked':'';
		$c .= sprintf("<tr class='$r'><td><input name=\"domain:%s\" $checked type=\"checkbox\"><td>%s</td><td>%s</td><td>%s</td></tr>\n",$domain,$domain,$D->profile(),$D->prt());
		}
	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $c;
	$template_file = 'domains.shtml';	
	}


if ($VERB eq 'MARKETPLACES') {
	push @BC, { name=>'Marketplaces',link=>'/biz/syndication/index.cgi?VERB=MARKETPLACES','target'=>'_top', };
	my %DSTCODES = ();
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $PROFILE = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
	my $qtPROFILE = $udbh->quote($PROFILE);
	my $pstmt = "select DSTCODE,IS_ACTIVE,LASTRUN_GMT from SYNDICATION where MID=$MID /* $USERNAME */ and PROFILE=$qtPROFILE";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($DSTCODE,$IS_ACTIVE,$LASTRUN_GMT) = $sth->fetchrow() ) {
		$DSTCODES{ $DSTCODE } = ($IS_ACTIVE)?'Updated: '.&ZTOOLKIT::pretty_date($LASTRUN_GMT,1):'Not Active';
		}
	$sth->finish();
	&DBINFO::db_user_close();

	my @ITEMS = ();

	@ITEMS = ();
	# push @ITEMS, {	dst=>'GOO', link=>"/biz/syndication/googlebase/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/googleproducts.jpg", logoh=>31, logow=>100, webdoc=>50396 };
	push @ITEMS, { dst=>'GOO', link=>"/biz/syndication/googlebase/index.cgi", logo=>"//static.zoovy.com/img/proshop/Bffffff/zoovy/logos/googletrustedstores.png", logoh=>41, logow=>116, webdoc=>51724	};
	if ($FLAGS =~ /,EBAY,/) {
		push @ITEMS, { dst=>'EBF', link=>"/biz/syndication/ebay/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/ebay.gif", logoh=>31, logow=>100, webdoc=>50380 };
		}
	push @ITEMS, { dst=>'AMZ', link=>"/biz/syndication/amazon/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/amazon_serve_large.JPG", logoh=>31, logow=>100, webdoc=>50391 };

	if ($FLAGS =~ /,WS,/) {
		push @ITEMS, { link=>"/biz/syndication/doba/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/doba", logoh=>31, logow=>88, webdoc=>51368 };
		}

	push @ITEMS, { dst=>'BUY', link=>"/biz/syndication/buycom/index.cgi?ts=$ts", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/buycom", logoh=>31, logow=>88, webdoc=>50917 };
	push @ITEMS, { dst=>'BST', link=>"/biz/syndication/bestbuy/index.cgi?ts=$ts", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/bestbuy", logoh=>31, logow=>88, webdoc=>50917 };

	push @ITEMS, { dst=>'WSH', link=>"/biz/syndication/wishpot/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/wishpot.gif", logoh=>31, logow=>88, webdoc=>51424 };
	push @ITEMS, { dst=>'SRS', link=>"/biz/syndication/sears/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/sears.jpg", logoh=>31, logow=>88, webdoc=>51583 };
	push @ITEMS, { dst=>'EGG', link=>"/biz/syndication/newegg/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/newegg.png", logoh=>31, logow=>88, webdoc=>51624 };

	if ($LUSERNAME eq 'SUPPORT') {
		push @ITEMS, { dst=>'GCP', link=>"/biz/syndication/googlecpc/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/googleadwords.gif", logoh=>31, logow=>88, webdoc=>51528 };
		}

	$GTOOLS::TAG{'<!-- RECOMMENDED -->'} = &make_menu(\@ITEMS);

	@ITEMS = ();
	#push @ITEMS, { dst=>'YST', link=>"/biz/syndication/yahooshop/index.cgi", logo=>"/biz/syndication/images/yahooshopping.gif", logoh=>31, logow=>88, webdoc=>50375 };
	push @ITEMS, { dst=>'SHO', link=>"/biz/syndication/shoppingcom/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/shopping.gif", logoh=>31, logow=>88, webdoc=>50538 };
	push @ITEMS, { dst=>'BZR', link=>"/biz/syndication/bizrate/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/shopzilla.gif", logoh=>31, logow=>100, webdoc=>50374 };
	push @ITEMS, { dst=>'PRT', link=>"/biz/syndication/pricegrabber/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/pricegrabber.gif", logoh=>31, logow=>88, webdoc=>50379 };
	push @ITEMS, { dst=>'AMZ', link=>"/biz/syndication/amazonpa/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/amazonpa.jpg", logoh=>31, logow=>100, webdoc=>51478 };
	push @ITEMS, { dst=>'NXT', link=>"/biz/syndication/nextag/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/nextag.gif", logoh=>31, logow=>88, webdoc=>50594 };
	push @ITEMS, { dst=>'BNG', link=>"/biz/syndication/bing/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/bing", logoh=>31, logow=>88, webdoc=>50918 };
	push @ITEMS, { dst=>'IMS', link=>"/biz/syndication/imshopping/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/imshopping.gif", logoh=>31, logow=>88, webdoc=>51488 };
	$GTOOLS::TAG{'<!-- CPC -->'} = &make_menu(\@ITEMS,\%DSTCODES);

	@ITEMS = ();
	# push @ITEMS, { link=>"/biz/syndication/overstock/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/overstock.gif", logoh=>31, logow=>88, webdoc=>50592 };
	#push @ITEMS, { link=>"/biz/syndication/mysimon/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/mysimon", logoh=>31, logow=>88, webdoc=>50593 };
	push @ITEMS, { link=>"/biz/syndication/CJ/index.cgi", logo=>"//static.zoovy.com/img/proshop/W128-H31-Bffffff/zoovy/logos/commissionjunction.gif", logoh=>31, logow=>128, webdoc=>51002 };
	push @ITEMS, { dst=>'FND', link=>"/biz/syndication/thefind/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/thefind.gif", logoh=>31, logow=>88, webdoc=>51538 };
	push @ITEMS, { dst=>'PTO', link=>"/biz/syndication/pronto/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/pronto.gif", logoh=>31, logow=>88, webdoc=>51461 };
	# push @ITEMS, { link=>"/biz/syndication/buythecase/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/buythecase", logoh=>31, logow=>88, webdoc=>0 };
	push @ITEMS, { link=>"/biz/syndication/buysafeshopping/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/buysafe", logoh=>31, logow=>88, webdoc=>50732 };
	push @ITEMS, { dst=>'SAS', link=>"/biz/syndication/shareasale/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/shareasale.png", logoh=>31, logow=>88, webdoc=>51488 };

	push @ITEMS, { dst=>'BCM', link=>"/biz/syndication/become/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/become.png", logoh=>31, logow=>88, webdoc=>51554 };
	push @ITEMS, { dst=>'SMT', link=>"/biz/syndication/smarter/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/smarter.png", logoh=>31, logow=>88, webdoc=>51555 };
	push @ITEMS, { dst=>'DIJ', link=>"/biz/syndication/dijipop/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/dijipop.png", logoh=>31, logow=>88, webdoc=>51556 };
	push @ITEMS, { dst=>'LNK', link=>"/biz/syndication/linkshare/index.cgi", logo=>"//static.zoovy.com/img/proshop/W100-H31-Bffffff/zoovy/logos/linksha/biz/syndication/re.png/index.cgi", logoh=>31, logow=>88, webdoc=>51557 };
	push @ITEMS, { link=>"/biz/syndication/custom/index.cgi", logo=>"//static.zoovy.com/img/proshop/W88-H31-Bffffff/zoovy/logos/custom", logoh=>31, logow=>88, webdoc=>51245 };


	$GTOOLS::TAG{'<!-- OTHER -->'} = &make_menu(\@ITEMS,\%DSTCODES);

	$template_file = 'index.shtml';
	}


my @TABS = ();
push @TABS, { name=>'Domains', link=>'/biz/syndication/index.cgi?VERB=DOMAINS', selected=>($VERB eq 'DOMAINS')?1:0 };
push @TABS, { name=>'Marketplaces', link=>'/biz/syndication/index.cgi?VERB=MARKETPLACES', selected=>($VERB eq 'MARKETPLACES')?1:0 };

## run this by default.
&GTOOLS::output('*LU'=>$LU,
	'title'=>'Syndication',
	'file'=>$template_file,
	'header'=>'1',
	'help'=>'',
	'msgs'=>\@MSGS,
	'bc'=>\@BC,
	'tabs'=>\@TABS,
  	);


sub make_menu {
	my ($itemref,$dstcode) = @_;

	my $c = '';
	my $i = 0;
	foreach my $item (@{$itemref}) {
		$c .= qq~

	<div style='font-size: 8pt; width: 150px; height: 75px; align: center; float:left; margin-left:8px; margin-bottom:8px; text-align:center;'>	
	<a href="$item->{'link'}">
	<img border=0 width=$item->{'logow'} height=$item->{'logoh'} src="$item->{'logo'}"></a><br>
	<a href="http://webdoc.zoovy.com/doc-$item->{'webdoc'}" target="webdoc">[More Info]</a>		
	</div>
		~;
		}
	if ($c eq '') {
		$c .= "<center><font color='blue'>None Available for this account.</font></center>";
		}
	return($c);
	}


