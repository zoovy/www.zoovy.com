#!/usr/bin/perl

use lib '/httpd/modules';
require CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require LUSER;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if ($FLAGS =~ /L2/) { $FLAGS .= ',BASIC,'; }

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'US Postal Service' };


$q = new CGI;

if (defined($q->param('MESSAGE'))) {
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>" . $q->param('MESSAGE') . "</b></font></center></td></tr></table><br>";
	}

#if ($FLAGS !~ /L1/)
#{
#	$GTOOLS::TAG{'<!-- HIDE_L1_ONLY -->'}     = ' <!-- ';
#	$GTOOLS::TAG{'<!-- END_HIDE_L1_ONLY -->'} = ' --> ';
#}

$GTOOLS::HEADER_IMAGE = 'shipping_options';

$ACTION = $q->param('ACTION');

if ($FLAGS =~ /,BASIC,/) {
	$GTOOLS::HEADER_IMAGE = 'usps_configuration';
	$template_file    = 'usps.shtml';
	}
else {
	$template_file = 'noaccess.shtml';
	}

%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);

if ($ACTION eq 'SAVE') {
	$webdb{'usps_dom'}          = $q->param('usps_dom') ? 1 : 0 ;
	$webdb{'usps_dom_handling'} = $q->param('usps_dom_handling');
	$webdb{'usps_dom_ins'}      = $q->param('usps_dom_ins');
	$webdb{'usps_dom_insprice'} = $q->param('usps_dom_insprice');
	
	$webdb{'usps_int_priority'} = 0;
	$webdb{'usps_int_express'} = 0;
	$webdb{'usps_int_expressg'} = 0;
	foreach my $k (1,2,4) {
		$webdb{'usps_int_priority'} += ($q->param('usps_int_priority_'.$k))?int($k):0;
		$webdb{'usps_int_express'} += ($q->param('usps_int_express_'.$k))?int($k):0;
		$webdb{'usps_int_expressg'} += ($q->param('usps_int_expressg_'.$k))?int($k):0;
		}
	
	$webdb{'usps_dom_express'}  = $q->param('usps_dom_express');
	$webdb{'usps_dom_priority'} = $q->param('usps_dom_priority');
	$webdb{'usps_dom_bulkrate'} = $q->param('usps_dom_bulkrate');

	$webdb{'usps_int'}                 = $q->param('usps_int') ? 1 : 0 ;
	$webdb{'usps_int_handling'}        = $q->param('usps_int_handling');
	$webdb{'usps_int_ins'}             = $q->param('usps_int_ins');
	$webdb{'usps_int_insprice'}        = $q->param('usps_int_insprice');
	
#	$webdb{'usps_int_global_small'}    = $q->param('usps_int_global_small');
#	$webdb{'usps_int_global_large'}    = $q->param('usps_int_global_large');
#	$webdb{'usps_int_global_variable'} = $q->param('usps_int_global_variable');
#	$webdb{'usps_int_small_airmail'}   = $q->param('usps_int_small_airmail');
#	$webdb{'usps_int_small_surface'}   = $q->param('usps_int_small_surface');
#	$webdb{'usps_int_parcel_surface'}  = $q->param('usps_int_parcel_surface');
#	$webdb{'usps_int_parcel_airmail'}  = $q->param('usps_int_parcel_airmail');
#	$webdb{'usps_int_letter_airmail'}  = $q->param('usps_int_letter_airmail');
	$webdb{'usps_int_parcelpost'}         = $q->param('usps_int_parcelpost');
#	$webdb{'usps_int_priority'}         = $q->param('usps_int_priority');
#	$webdb{'usps_int_express'}         = $q->param('usps_int_express');

	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>Successfully saved US Postal Service settings!</b></font></center></td></tr></table><br>";
	$LU->log("SETUP.SHIPPING.USPS","Saved USPS Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME, \%webdb,$PRT);
	}

## Domestic settings
$GTOOLS::TAG{'<!-- USPS_DOM -->'}   = $webdb{'usps_dom'} ? 'CHECKED' : '' ;
## International settings
$GTOOLS::TAG{'<!-- USPS_INT -->'}   = $webdb{'usps_int'} ? 'CHECKED' : '' ;

## Domestic Methods
$GTOOLS::TAG{'<!-- USPS_DOM_EXPRESS -->'}   = $webdb{'usps_dom_express'}  ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_DOM_PRIORITY -->'}  = $webdb{'usps_dom_priority'} ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_DOM_BULKRATE -->'}  = $webdb{'usps_dom_bulkrate'} ? 'CHECKED' : '' ;

## International Methods
#$GTOOLS::TAG{'<!-- USPS_INT_GLOBALPRIORITY_SMALL -->'}    = $webdb{'usps_int_global_small'}    ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_GLOBALPRIORITY_LARGE -->'}    = $webdb{'usps_int_global_large'}    ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_GLOBALPRIORITY_VARIABLE -->'} = $webdb{'usps_int_global_variable'} ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_SMALLPACKET_AIRMAIL -->'}     = $webdb{'usps_int_small_airmail'}   ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_SMALLPACKET_SURFACE -->'}     = $webdb{'usps_int_small_surface'}   ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_PARCELPOST_SURFACE -->'}      = $webdb{'usps_int_parcel_surface'}  ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_PARCELPOST_AIRMAIL -->'}      = $webdb{'usps_int_parcel_airmail'}  ? 'CHECKED' : '' ;
#$GTOOLS::TAG{'<!-- USPS_INT_LETTER_AIRMAIL -->'}          = $webdb{'usps_int_letter_airmail'}  ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_PARCELPOST -->'}                 = $webdb{'usps_int_parcelpost'}         ? 'CHECKED' : '' ;

$GTOOLS::TAG{'<!-- USPS_INT_PRIORITY_1 -->'}                 = ($webdb{'usps_int_priority'}&1)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_PRIORITY_2 -->'}                 = ($webdb{'usps_int_priority'}&2)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_PRIORITY_4 -->'}                 = ($webdb{'usps_int_priority'}&4)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESS_1 -->'}                 = ($webdb{'usps_int_express'}&1)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESS_2 -->'}                 = ($webdb{'usps_int_express'}&2)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESS_4 -->'}                 = ($webdb{'usps_int_express'}&4)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESSG_1 -->'}                 = ($webdb{'usps_int_expressg'}&1)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESSG_2 -->'}                 = ($webdb{'usps_int_expressg'}&2)         ? 'CHECKED' : '' ;
$GTOOLS::TAG{'<!-- USPS_INT_EXPRESSG_4 -->'}                 = ($webdb{'usps_int_expressg'}&4)         ? 'CHECKED' : '' ;

if ($webdb{'ship_int_risk'} eq 'none') {
	# these tags make the usps int options hidden in a comment
	$GTOOLS::TAG{'<!-- USPS_HIDE_INT_BEGIN -->'} = '<!--';
	$GTOOLS::TAG{'<!-- USPS_HIDE_INT_END -->'}   = '--->';
	}
else {
	$GTOOLS::TAG{'<!-- USPS_HIDE_INT_BEGIN -->'} = '';
	$GTOOLS::TAG{'<!-- USPS_HIDE_INT_END -->'}   = '';
	}

&GTOOLS::output('*LU'=>$LU,title=>'USPS Configuration', help=>'#50815',file=>$template_file,header=>1,bc=>\@BC);

exit;

