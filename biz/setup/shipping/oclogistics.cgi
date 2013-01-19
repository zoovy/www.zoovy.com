#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require CGI;
require ZOOVY;
require ZWEBSITE;
require ZSHIP;
require ZSHIP::WEIGHT;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $VERB = $ZOOVY::cgiv->{'VERB'};
my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

if ($VERB eq "SAVE") {

	$LU->log("SETUP.SHIPPING.OCLOGISTICS","Saved OC Logistics Shipping Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = '';
	}


if ($VERB eq '') {
	# set the enabled checkbox status
	$template_file = 'oclogistics.shtml';
	}

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'OC Logistics' };

&GTOOLS::output(title=>"Shipping: Weight Based Shipping",help=>'#50998',file=>$template_file,header=>1,bc=>\@BC);
