#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use ZSHIP::FREIGHTCENTER;
use GTOOLS;
use ZOOVY;

##
## important configuration settings:
##		$webdbref->{'freightcenter_enable'}  -- bit 1 = domestic, bit 2 = international 
##

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $VERB = $ZOOVY::cgiv->{'VERB'};


my $template_file = 'freightcenter.shtml';

##
##
##
if ($VERB eq 'SAVE') {
	$VERB = '';
	}


##
##
##
if ($VERB eq '') {
	
	}

my @BC = ();
push @BC, { name=>'Setup',link=>'//www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'//www.zoovy.com/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'FreightCenter',link=>'//www.zoovy.com/biz/setup/shipping/freightcenter.cgi','target'=>'_top', };
&GTOOLS::output(file=>$template_file,header=>1);