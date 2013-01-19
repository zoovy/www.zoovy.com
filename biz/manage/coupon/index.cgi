#!/usr/bin/perl


use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;

my ($USERNAME,$FLAGS,$MID,$LUSER) = &ZOOVY::authenticate("/biz",6);

my @TABS = ();
push @TABS, { name=>'View All', link=>'/biz/manage/coupon/index.cgi?VERB=' };
push @TABS, { name=>'Create Coupon', link=>'/biz/manage/coupon/index.cgi?VERB=CREATE' };
push @TABS, { name=>'Products', link=>'/biz/manage/coupon/index.cgi?VERB=PRODUCTS' };

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $template_file = 'index.shtml';

if ($VERB eq 'CREATE') {
	$template_file = 'edit.shtml';
	}


&GTOOLS::output(file=>$template_file,header=>1,tabs=>\@TABS);
