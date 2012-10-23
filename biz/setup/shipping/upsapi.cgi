#!/usr/bin/perl -w

use strict;
no warnings 'once';

use CGI;

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require ZSHIP::UPSAPI;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$GTOOLS::TAG{'<!-- UPS_BRAND_MESSAGE -->'} = qq~
UPS, THE UPS SHIELD TRADEMARK, THE UPS READY MARK, THE UPS ONLINE TOOLS MARK AND THE COLOR BROWN ARE TRADEMARKS OF UNITED PARCEL SERVICE OF AMERICA, INC. ALL RIGHTS RESERVED.
~;

my @BC = ();
push @BC, { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'http://www.zoovy.com/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'UPS Shipping' };

my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my $template_file = ''; # Assume we don't know where we're going.
my $message = ''; # Assume we don't know what to say

my $VERB   = defined($ZOOVY::cgiv->{'VERB'}) ? $ZOOVY::cgiv->{'VERB'} : 'config' ;
my $proceed = (((defined $ZOOVY::cgiv->{'proceed'}) && $ZOOVY::cgiv->{'proceed'}) || ((defined $ZOOVY::cgiv->{'proceed.x'}) && $ZOOVY::cgiv->{'proceed.x'})) ? 1 : 0 ;

# variable only used from SUPPLY CHAIN MANAGEMENT
my $SUPPLIER_ID = $ZOOVY::cgiv->{'SUPPLIER_ID'};
$GTOOLS::TAG{'<!-- SUPPLIER_ID -->'} = $SUPPLIER_ID;

## setup variable for cancels, exits 
## SUPPLY CHAIN needs to exit back there
my $redirect = '';
my $license = '';
my $shipper_number = '';
my $S = '';
my %UPS_CONFIG = ();

## SUPPLIER UPS configuration
if ($SUPPLIER_ID && $SUPPLIER_ID ne ''){ 
	$redirect = "/biz/manage/suppliers/index.cgi?ACTION=SHIPPING&CODE=$SUPPLIER_ID"; 
	
	require ZTOOLKIT;
	require SUPPLIER;

	$S = SUPPLIER->new($USERNAME, $SUPPLIER_ID);
	my $params = ZTOOLKIT::parseparams($S->fetch_property(".ship.meter"));
	$license 	= defined($params->{'license'})			? $params->{'license'}			: '';
	$shipper_number = defined($params->{'shipper_number'})		? $params->{'shipper_number'}		: '';
	}
## non-SUPPLIER UPS configuration
else { 
	$redirect = "/biz/setup/shipping/upsapi.cgi"; 
	$license        = defined($webdb->{'upsapi_license'})        	? $webdb->{'upsapi_license'}       	: '';
	$shipper_number = defined($webdb->{'upsapi_shipper_number'}) 	? $webdb->{'upsapi_shipper_number'}	: '';
	}
$GTOOLS::TAG{'<!-- EXIT_URL -->'} = $redirect; 

my $template_file           = 'upsapi-register.shtml';

## never let them access 'config' without a license.
if (($license eq '') && ($VERB eq 'config')) { $VERB = 'apply'; } ## No license?  Always send them to get one!


if ($VERB eq 'abort') {
	require CGI;
	print CGI->redirect('/biz/setup/shipping');
	exit;
	}

if ($VERB eq 'apply') {
	$template_file = 'upsapi-apply.shtml';
	}


##
##
##
if ($VERB =~ m/^license/) {
	my $license = &ZSHIP::UPSAPI::get_ups_license($USERNAME);
	$license =~ s/^\s+//s;
	$license =~ s/\n +/\n/gs;
	$license =~ s/\&apos\;/'/gis;
	$GTOOLS::TAG{'<!-- LICENSE_AGREEMENT -->'} = $license;

	my $html = $license; 
	$html =~ s/\n/<br>/g;
	$GTOOLS::TAG{'<!-- LICENSE_AGREEMENT_HTML -->'} = $html;

	if ($VERB eq 'licenseframe') {
		## not sure if licenseframe is used anymore.
		$template_file = "upsapi-licenseframe.shtml";
		$GTOOLS::TAG{'<!-- PRINT_JAVASCRIPT -->'} = '';
		}
	elsif ($VERB eq 'licenseframeprint') {
		$template_file = "upsapi-licenseframe.shtml";
		$GTOOLS::TAG{'<!-- PRINT_JAVASCRIPT -->'} = qq~ onLoad="window.print()"~;
		}
	else {
		$template_file = "upsapi-license.shtml";
		
		if ($SUPPLIER_ID && $SUPPLIER_ID ne ''){
			$S = SUPPLIER->new($USERNAME, $SUPPLIER_ID);
			my $meter = $S->fetch_property(".ship.meter");
			$meter =~ s/license=(.*)\&/license=\&/;
			
			$S->save_property(".ship.meter", $meter);
			$S->save_property(".ship.meter_createdgmt", time());
			$S->save();
			print STDERR "saving supplier: type=UPS&supplier_id=$SUPPLIER_ID meter: $meter\n";

			$LU->log("SETUP.SHIPPING.UPSAPI","Reapplying Supplier $SUPPLIER_ID UPS License","SAVE");
			}
		else {
			$webdb->{'upsapi_license'} = '';
			$webdb->{'ups_int'} = '';
			$webdb->{'ups_dom'} = '';
			$LU->log("SETUP.SHIPPING.UPSAPI","Reset UPS License","SAVE");
			&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
			}
		}
	}

##
if ($VERB eq 'register') {
	$VERB = 'register';
	$template_file = 'upsapi-register.shtml';
	my $company_name = &ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:company_name');
	if ((not defined $company_name) || ($company_name eq '')) {
		$company_name = &ZTOOLKIT::pretty($webdb->{'company_name'});
		if ((not defined $company_name) || ($company_name eq '')) {
			$company_name = &ZTOOLKIT::pretty($USERNAME);
			}
		}
	my $merchantref = &ZOOVY::fetchmerchant_ref($USERNAME);
	my $paramdefaults = {
        'company_name'   => $company_name,
        'address1'       => defined($merchantref->{'zoovy:address1'}) ? $merchantref->{'zoovy:address1'} : '',
        'address2'       => defined($merchantref->{'zoovy:address2'}) ? $merchantref->{'zoovy:address2'} : '',
        'city'           => defined($merchantref->{'zoovy:city'}) ? $merchantref->{'zoovy:city'} : '' ,
        'state'          => defined($merchantref->{'zoovy:state'}) ? $merchantref->{'zoovy:state'} : '',
        'zip'            => defined($merchantref->{'zoovy:zip'}) ? $merchantref->{'zoovy:zip'} : '',
        'country'        => 'US',
        'name'           => "$merchantref->{'zoovy:firstname'} $merchantref->{'zoovy:lastname'}",
        'title'          => 'Mr.',
        'email'          => defined($merchantref->{'zoovy:email'}) ? $merchantref->{'zoovy:email'} : '',
        'phone'          => defined($merchantref->{'zoovy:phone'}) ? $merchantref->{'zoovy:phone'} : '',
        'url'            => "http://$USERNAME.zoovy.com/",
        'contact'        => "",
        'shipper_number' => defined($webdb->{'upsapi_shipper_number'}) ? $webdb->{'upsapi_shipper_number'} : '',
		};
	my $params = {%{$paramdefaults}}; ## Copy defaults into the params hashref
	my $sender = (defined $ZOOVY::cgiv->{'sender'}) ? $ZOOVY::cgiv->{'sender'} : '' ;
	if ($proceed && ($sender ne 'license')) {
		## Get all the CGI params and load up the hash we pass to the resistration function
		foreach my $key (keys %{$params}) {
			my $cgikey = 'UPS_'.uc($key);
			$params->{$key} = defined($ZOOVY::cgiv->{$cgikey}) ? $ZOOVY::cgiv->{$cgikey} : '';
			}
		if ($params->{'contact'} eq '') {
			## This is the one thing that does not get trapped by the UPS API
			$GTOOLS::TAG{"<!-- MESSAGE -->"} = 'You must select whether or not you want a UPS representative to contact you at the bottom of the page.';
			}
		else {
			## Normalize the data a bit...
			$params->{'country'} = 'US';
			$params->{'phone'} =~ s/\D//gs;
			$params->{'state'} = uc($params->{'state'});
			my $error; my $user; my $pass;
			($error,$license,$user,$pass) = &ZSHIP::UPSAPI::get_ups_registration($USERNAME,$params);
			$shipper_number = $params->{'shipper_number'};
			if ($error ne '') {
				$GTOOLS::TAG{"<!-- MESSAGE -->"} = $error;
				}
			elsif (($SUPPLIER_ID) && ($SUPPLIER_ID ne '')) {
				# &ZWEBSITE::save_website_attrib($USERNAME,'upsapi_SUPPLIER_ID',$SUPPLIER_ID);

				#use SUPPLIER;
				$S = SUPPLIER->new($USERNAME, $SUPPLIER_ID);
				$S->save_property(".ship.meter", "type=UPS&user=$user&pass=$pass&license=$license&shipper_number=$shipper_number");
				$S->save_property(".ship.meter_createdgmt", time());
				$S->save();
				print STDERR "saving supplier: type=UPS&supplier_id=$SUPPLIER_ID&user=$user&pass=$pass&license=$license&shipper_number=$shipper_number\n";

				$LU->log("SETUP.SHIPPING.UPSAPI","Intialized Supplier $SUPPLIER_ID UPS License","SAVE");

				$VERB = 'success'; ## Switch to give them an interface for editing UPS info
				$template_file = 'upsapi-success.shtml';
				}
			else {

				$webdb->{'upsapi_userid'} = $user;
				$webdb->{'upsapi_password'} = $pass;
				$webdb->{'upsapi_license'} = $license;
				$webdb->{'upsapi_shipper_number'} = $shipper_number;
				$LU->log("SETUP.SHIPPING.UPSAPI","Intialized UPS License","SAVE");
				&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);

				$VERB = 'success'; ## Switch to give them an interface for editing UPS info
				$template_file = 'upsapi-success.shtml';
				}
			}
		}
	foreach my $key (keys %{$params}) {
		$GTOOLS::TAG{'<!-- UPS_'.uc($key).' -->'} = $params->{$key};
		}
	$GTOOLS::TAG{'<!-- UPS_CONTACT_YES_CHECKED -->'} = ($params->{'contact'} eq 'Yes') ? ' checked' : '' ;
	$GTOOLS::TAG{'<!-- UPS_CONTACT_NO_CHECKED -->'} = ($params->{'contact'} eq 'No') ? ' checked' : '' ;
	}


##
if ($VERB eq 'config') {
	$template_file = 'upsapi.shtml';

	my $save = (((defined $ZOOVY::cgiv->{'save'}) && $ZOOVY::cgiv->{'save'}) || ((defined $ZOOVY::cgiv->{'save.x'}) && $ZOOVY::cgiv->{'save.x'})) ? 1 : 0 ;
	if ($save) {
		$webdb->{'upsapi_dom'} = 0;
		if (defined($ZOOVY::cgiv->{'dom'})) {
			foreach my $bit (keys %ZSHIP::UPSAPI::DOM_METHODS) {
				my $name = lc($ZSHIP::UPSAPI::DOM_METHODS{$bit});
				if (defined $ZOOVY::cgiv->{"dom_$name"}) { $webdb->{'upsapi_dom'} += $bit; }
				}
			}
		$webdb->{'upsapi_int'} = 0;
		if (defined($ZOOVY::cgiv->{'int'})) {
			foreach my $bit (keys %ZSHIP::UPSAPI::INT_METHODS) {
				my $name = lc($ZSHIP::UPSAPI::INT_METHODS{$bit});
				if (defined $ZOOVY::cgiv->{"int_$name"}) { $webdb->{'upsapi_int'} += $bit; }
				}
			}
		$webdb->{'upsapi_options'} = 0;
		# multibox, residential, validation, use_rules
		foreach my $bit (keys %ZSHIP::UPSAPI::OPTIONS) {
			my $name = $ZSHIP::UPSAPI::OPTIONS{$bit};
			if (defined $ZOOVY::cgiv->{"option_$name"}) { $webdb->{'upsapi_options'} += $bit; }
			}
		$webdb->{'upsapi_dom_packaging'} = $ZOOVY::cgiv->{'dom_packaging'};
		$webdb->{'upsapi_int_packaging'} = $ZOOVY::cgiv->{'int_packaging'};
		$webdb->{'upsapi_rate_chart'}    = $ZOOVY::cgiv->{'rate_chart'};

		# Save stuff here!
		if (defined $ZOOVY::cgiv->{'PRIMARY_SHIPPER'}) {
			$webdb->{'primary_shipper'} = 'UPS';
			}

		$LU->log("SETUP.SHIPPING.UPS","Saved UPS Settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);		
		$message = "<br><table border='2' width='80%' align='center'><tr><td><center><font color='red' size='4' face='helvetica'><b>Successfully Saved!</b></font></center></td></tr></table><br>";
		}

	# Set the RATE_CHART drop-down selections
	foreach my $option (qw(01 03 06 07 19 20 11)) {
		my $option_code = uc($option);
		$option_code =~ s/\s+/\_/g;
		$GTOOLS::TAG{'<!-- RATE_CHART_'.$option_code.' -->'} = ($webdb->{'upsapi_rate_chart'} eq $option) ? 'selected' : '';
		}

	# Set the DOM_PACKAGING drop-down selections
	# Set the INT_PACKAGING drop-down selections
	foreach my $option (qw(00 01 03 04 21 24 25 30 2a 2b 2c SMART)) {
		$GTOOLS::TAG{'<!-- INT_PACKAGING_'.$option.' -->'} = ($webdb->{'upsapi_int_packaging'} eq $option) ? 'selected' : '';
		$GTOOLS::TAG{'<!-- DOM_PACKAGING_'.$option.' -->'} = ($webdb->{'upsapi_dom_packaging'} eq $option) ? 'selected' : '';
		}

	# check against the bitwise mnemonics and set the appropriate flags in GTOOLS
	# See %ZSHIP::UPSAPI::DOM_METHODS, %ZSHIP::UPSAPI::INT_METHODS, %ZSHIP::UPSAPI::OPTIONS
	$GTOOLS::TAG{'<!-- DOM -->'} = ($webdb->{'upsapi_dom'} > 0) ? 'checked' : '';
	foreach my $bit (keys %ZSHIP::UPSAPI::DOM_METHODS) {
		my $name = $ZSHIP::UPSAPI::DOM_METHODS{$bit};
		$GTOOLS::TAG{'<!-- DOM_'.uc($name).' -->'} = (int($webdb->{'upsapi_dom'}) & $bit) ? 'checked' : '';
		}

	$GTOOLS::TAG{'<!-- INT -->'} = ($webdb->{'upsapi_int'} > 0) ? 'checked' : '';
	foreach my $bit (keys %ZSHIP::UPSAPI::INT_METHODS) {
		my $name = $ZSHIP::UPSAPI::INT_METHODS{$bit};
		$GTOOLS::TAG{'<!-- INT_'.uc($name).' -->'} = (int($webdb->{'upsapi_int'}) & $bit) ? 'checked' : '';
		}

	foreach my $bit (keys %ZSHIP::UPSAPI::OPTIONS) {
		## MULTIBOX RESIDENTIAL VALIDATION USE_RULES
		my $name = $ZSHIP::UPSAPI::OPTIONS{$bit};
		$GTOOLS::TAG{'<!-- OPTION_'.uc($name).' -->'} = (int($webdb->{'upsapi_options'}) & $bit) ? 'checked' : '';

		if (($name eq 'use_rules') && !(int($webdb->{'upsapi_options'}) & $bit)) {
			$GTOOLS::TAG{'<!-- RULE_WARNING -->'} = '<br><font color="red">Rule processing is currently disabled. This will cause any UPS shipping rules to be ignored.</font>';
			}
		}
	
	
	
	$GTOOLS::TAG{'<!-- PRIMARY_SHIPPER -->'} = ((defined $webdb->{'primary_shipper'}) && ($webdb->{'primary_shipper'} eq 'UPS'))?'CHECKED':'';

	$GTOOLS::TAG{"<!-- MESSAGE -->"} = $message;
	}
$GTOOLS::TAG{'<!-- UPS_DISCLAIMER -->'} = qq~<p align="center"><small><i>$ZSHIP::UPSAPI::DISCLAIMER</i></small></p>~;
$GTOOLS::TAG{'<!-- UPS_SHIPPER_NUMBER -->'} = $shipper_number;
$GTOOLS::TAG{'<!-- UPS_LICENSE -->'}        = $license;

&GTOOLS::output(
	title=>'Shipping: UPS Shipping',
	help=>'#50300',file=>$template_file,
	header=>1,
	js=>2,	## needed for ups license.
	bc=>\@BC
	);

