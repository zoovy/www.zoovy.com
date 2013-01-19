#!/usr/bin/perl

use lib '/httpd/modules';
require ZOOVY;
require ZWEBSITE;
require ZSHIP::DHLAPI;
require GTOOLS;




require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'DHL' };


my $ACTION = $ZOOVY::cgiv->{'ACTION'};
my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

##
## webdb values:
##	dhl_dom (bitwise)
##		1 = enable/disable service
##		2 = perform rule processing
##		
##	dhl_services (bitwise)
##		1 = express
##		2 = next day afternoon
##		4 = second day
##		8 = ground
##
## dhl_origin = origin zip code
## dhl_account = account #
##	dhl_shipkey = shipper key (obtained during registration)
##

$template_file = 'dhl.shtml';
if ($FLAGS !~ /,BASIC,/) {
	$template_file = 'dhl-deny.shtml';
	}

if ($ACTION eq 'REGISTER-SAVE') {
	$webdb->{'dhl_account'} = $ZOOVY::cgiv->{'ACCOUNT_NUM'};
	$webdb->{'dhl_origin'} = $ZOOVY::cgiv->{'ORIGIN_ZIP'};
	my ($shipkey,$msg) = &ZSHIP::DHLAPI::register($webdb);
	if ($shipkey eq '') {
		## ERROR 
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<font color="red">REGISTRATION ERROR: '.$msg.'</font>';	
		$ACTION = 'REGISTER';
		}
	else {
		$webdb->{'dhl_shipkey'} = $shipkey;
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<font color="blue">REGISTRATION SUCCESSFUL! ['.$msg.']</font>';	
		$LU->log("SETUP.SHIPPING.DHL","Registration Successful","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
		$ACTION = '';
		}
	}

if ($ACTION eq 'SAVE') {
	$webdb->{'dhl_dom'} = 0;
	$webdb->{'dhl_services'} = 0;
	if ($ZOOVY::cgiv->{'dhl_dom'}) {
		$webdb->{'dhl_dom'} = 1;
		$webdb->{'dhl_dom'} += ($ZOOVY::cgiv->{'option_use_rules'})?2:0;
		$webdb->{'dhl_dom'} += ($ZOOVY::cgiv->{'option_servicetimes'})?4:0;

		$webdb->{'dhl_services'} += ($ZOOVY::cgiv->{'SERVICE_E'})?1:0;
		$webdb->{'dhl_services'} += ($ZOOVY::cgiv->{'SERVICE_N'})?2:0;
		$webdb->{'dhl_services'} += ($ZOOVY::cgiv->{'SERVICE_S'})?4:0;
		$webdb->{'dhl_services'} += ($ZOOVY::cgiv->{'SERVICE_G'})?8:0;
		}
	$LU->log("SETUP.SHIPPING.DHL","Saved Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
	$ACTION = '';	
	}

if (not defined $webdb->{'dhl_dom'}) { $webdb->{'dhl_dom'} = 0; }
if (not defined $webdb->{'dhl_services'}) { $webdb->{'dhl_services'} = 0; }
if ($webdb->{'dhl_account'} eq '') { $ACTION = 'REGISTER'; }

if ($ACTION eq 'REGISTER') {
	$template_file = 'dhl-register.shtml';
	$GTOOLS::TAG{'<!-- ACCOUNT_NUM -->'} = ($webdb->{'dhl_account'})?$webdb->{'dhl_account'}:'';
	$GTOOLS::TAG{'<!-- ORIGIN_ZIP -->'} = ($webdb->{'dhl_origin'})?$webdb->{'dhl_origin'}:'';
	}

if ($ACTION eq '') {
	$GTOOLS::TAG{'<!-- DHL_DOM_ENABLED -->'} = ($webdb->{'dhl_dom'}&1)?'checked':'';
	$GTOOLS::TAG{'<!-- OPTION_USE_RULES -->'} = ($webdb->{'dhl_dom'}&2)?'checked':'';
	$GTOOLS::TAG{'<!-- OPTION_SERVICETIMES -->'} = ($webdb->{'dhl_dom'}&4)?'checked':'';
	$GTOOLS::TAG{'<!-- ACCOUNT_NUM -->'} = ($webdb->{'dhl_account'})?$webdb->{'dhl_account'}:'<font color="red"><i>NOT SET</i></font>';
	$GTOOLS::TAG{'<!-- ORIGIN_ZIP -->'} = ($webdb->{'dhl_origin'})?$webdb->{'dhl_origin'}:'<font color="red"><i>NOT SET</i></font>';
	$GTOOLS::TAG{'<!-- SHIPPER_KEY -->'} = ($webdb->{'dhl_shipkey'})?$webdb->{'dhl_shipkey'}:'<font color="red"><i>NOT SET</i></font>';

	$GTOOLS::TAG{'<!-- SERVICE_E -->'} = ($webdb->{'dhl_services'}&1)?'checked':'';
	$GTOOLS::TAG{'<!-- SERVICE_N -->'} = ($webdb->{'dhl_services'}&2)?'checked':'';
	$GTOOLS::TAG{'<!-- SERVICE_S -->'} = ($webdb->{'dhl_services'}&4)?'checked':'';
	$GTOOLS::TAG{'<!-- SERVICE_G -->'} = ($webdb->{'dhl_services'}&8)?'checked':'';
	}

&GTOOLS::output('*LU'=>$LU,
	header=>1,
	title=>'Shipping: DHL Shipping',
	file=>$template_file,
	help=>'#50301',
	bc=>\@BC,
	);

