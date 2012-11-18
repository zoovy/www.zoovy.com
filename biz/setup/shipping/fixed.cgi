#!/usr/bin/perl


##
##
##
##	NOTE: THIS USED TO BE REFERRED TO AS "MULTI-ITEM SIMPLE SHIPPING"
##
##
##

use lib "/httpd/modules";
require GTOOLS;
use CGI;
require ZWEBSITE;
require ZSHIP;
require ZSHIP::GLOBAL;
use Data::Dumper;



require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$q = new CGI;
$ACTION = $q->param('ACTION');
%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Fixed Shipping' };


if ($FLAGS =~ /LITE/) {
	## this is the stuff we hide from the LITE users
	$GTOOLS::TAG{'<!-- LITE_HIDE_ON -->'} = '<!--';
	$GTOOLS::TAG{'<!-- LITE_HIDE_OFF -->'} = '-->';
	$GTOOLS::TAG{'<!-- EXIT_URL -->'} = '/biz/setup';
	}
else {
	$GTOOLS::TAG{'<!-- EXIT_URL -->'} = 'index.cgi';
	}

if ($ACTION eq 'SAVE') {

	$webdb{'ship_simplemulti'} = 0;
	if (defined $q->param('simplemulti_dom')) { $webdb{'ship_simplemulti'} += 1; }
	if (defined $q->param('simplemulti_can')) { $webdb{'ship_simplemulti'} += 2; }
	if (defined $q->param('simplemulti_int')) { $webdb{'ship_simplemulti'} += 4; }
	
	$webdb{'ship_simplemulti_description'} = $q->param('ship_simplemulti_description');

	$webdb{'ship_simplemulti_description'}	=~ s/^[\s]*(.*)[\s]*$/$1/g;
	$webdb{'ship_simplemulti_description_can'} = $q->param('ship_simplemulti_description_can');
	$webdb{'ship_simplemulti_description_can'}	=~ s/^[\s]*(.*)[\s]*$/$1/g;
	$webdb{'ship_simplemulti_description_int'} = $q->param('ship_simplemulti_description_int');
	$webdb{'ship_simplemulti_description_int'}	=~ s/^[\s]*(.*)[\s]*$/$1/g;

#	use Data::Dumper;
#	print STDERR Dumper($webdb{'ship_simplemulti'},$webdb{'ship_simplemulti_description'});
	$LU->log("SETUP.SHIPPING.FIXED","Saved Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<font color="red">Saved Simple Fixed Shipping Settings</font>';
	$ACTION = '';
	}

if ($ACTION eq '') {

	if ($webdb{'ship_simplemulti_description'} eq '') { 
  		 $webdb{'ship_simplemulti_description'} = 'Shipping & Handling'; 
		}


	if ( (int($webdb{'ship_simplemulti'}) & 1) == 1) {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_DOM_CHECKED -->'} = ' CHECKED '; 
		} else {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_DOM_CHECKED -->'} = ''; 
		}
	if ( (int($webdb{'ship_simplemulti'}) & 2) == 2) {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_CAN_CHECKED -->'} = ' CHECKED '; 
		} else {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_CAN_CHECKED -->'} = ''; 
		}
	if ( (int($webdb{'ship_simplemulti'}) & 4) == 4) {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_INT_CHECKED -->'} = ' CHECKED '; 
		} else {
		$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_INT_CHECKED -->'} = ''; 
		}

	$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_DESCRIPTION -->'} = &ZOOVY::incode($webdb{'ship_simplemulti_description'});
	$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_DESCRIPTION_INT -->'} = &ZOOVY::incode($webdb{'ship_simplemulti_description_int'});
	$GTOOLS::TAG{'<!-- SHIP_SIMPLEMULTI_DESCRIPTION_CAN -->'} = &ZOOVY::incode($webdb{'ship_simplemulti_description_can'});
	

	$template_file = 'fixed.shtml';
	}

&GTOOLS::output(title=>'Shipping: Fixed Shipping',help=>'#50293',file=>$template_file,header=>1,bc=>\@BC);
