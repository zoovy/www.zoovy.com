#!/usr/bin/perl

use strict;
use CGI;
use lib "/httpd/modules";
require GTOOLS;
require ZPAY;
require ZOOVY;
require ZWEBSITE;
require ZTOOLKIT;
require LUSER;
require CART2;

&ZOOVY::init();

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
my $template_file = '';

my $help = "#50542";

## get link for WEBDOC in templates
my ($helplink, $helphtml) = GTOOLS::help_link('Payment Gateways', 50611);
$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helplink;
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;


my $GATEWAY_OKAY = 0;
if ($FLAGS =~ /,[LD]2,/) { $GATEWAY_OKAY = 1; $FLAGS .= ',EBAY,'; }
elsif ($FLAGS =~ /,LITE,/) { $GATEWAY_OKAY = 1; }
elsif ($FLAGS =~ /,BASIC,/) { $GATEWAY_OKAY = 1; }

if ($FLAGS =~ /,DEV,/) { $FLAGS .= ',API2,'; }

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

my $ACTION = uc($ZOOVY::cgiv->{'ACTION'});
my $webdbref  = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
if ($webdbref->{'cc_processor'} eq '') { $webdbref->{'cc_processor'} = 'NONE'; }

if ($webdbref->{'pay_custom_desc'} ne '') {
	## make sure we can edit/remove custom payment methods
	$FLAGS .= ',API2,';
	}

##Breadcrumbing
my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Payment',link=>'/biz/setup/payment','target'=>'_top', };

##TABS
## ALL, OFFLINE, CREDIT, PAYPAL, SPECIAL


##SET DEFAULT PAGE
my $TAB = $ZOOVY::cgiv->{'TAB'};
if ($TAB eq '') { $TAB = 'HELP'; }



my @MSGS = ();



##
## General Code!
##

if ($TAB eq 'OFFLINE') {
	if ($ACTION eq '') { $ACTION = 'OFFLINE'; }
	if ($ACTION eq "OFFLINE-SAVE") {
		$ACTION = "OFFLINE";

		$webdbref->{'payable_to'} = $ZOOVY::cgiv->{'payable_to'};
		$webdbref->{"pay_cash"} = $ZOOVY::cgiv->{'pay_cash'}; 
		$webdbref->{"pay_mo"} = $ZOOVY::cgiv->{'pay_mo'}; 
		$webdbref->{"pay_giftcard"} = $ZOOVY::cgiv->{'pay_giftcard'}; 
		$webdbref->{"pay_pickup"} = $ZOOVY::cgiv->{'pay_pickup'}; 
		$webdbref->{"pay_check"} = $ZOOVY::cgiv->{'pay_check'}; 
		$webdbref->{"pay_check_fee"} = $ZOOVY::cgiv->{'pay_check_fee'}; 
		$webdbref->{"pay_cod"} = $ZOOVY::cgiv->{'pay_cod'}; 	
		$webdbref->{"pay_cod_fee"} = $ZOOVY::cgiv->{'pay_cod_fee'}; 
		$webdbref->{"pay_chkod"} = $ZOOVY::cgiv->{'pay_chkod'}; 
		$webdbref->{"pay_chkod_fee"} = $ZOOVY::cgiv->{'pay_chkod_fee'}; 
		$webdbref->{"pay_po"} = $ZOOVY::cgiv->{'pay_po'}; 
		$webdbref->{"pay_wire"} = $ZOOVY::cgiv->{'pay_wire'}; 
		$webdbref->{"pay_wire_fee"} = $ZOOVY::cgiv->{'pay_wire_fee'}; 
		$webdbref->{"pay_wire_instructions"} = $ZOOVY::cgiv->{'pay_wire_instructions'}; 

		$LU->log('SETUP.PAYMENT.OFFLINE',"Updated payment offline settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		$webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	
		push @MSGS, "SUCCESS|Saved General Settings Successfully";
		$ACTION = 'OFFLINE';
		}
		
	if ($ACTION eq 'OFFLINE') {
		$GTOOLS::TAG{'<!-- PAYABLE_TO -->'} = $webdbref->{'payable_to'};
		$GTOOLS::TAG{"<!-- PAY_PO_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PO_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PO_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PO_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PO_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PO_".$webdbref->{"pay_po"}."_SELECTED -->"} = "SELECTED";
	
		$GTOOLS::TAG{"<!-- PAY_CASH_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CASH_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CASH_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CASH_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CASH_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CASH_".$webdbref->{"pay_cash"}."_SELECTED -->"} = "SELECTED";

		$GTOOLS::TAG{"<!-- PAY_MO_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_MO_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_MO_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_MO_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_MO_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_MO_".$webdbref->{"pay_mo"}."_SELECTED -->"} = "SELECTED";

		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_GIFTCARD_".$webdbref->{"pay_giftcard"}."_SELECTED -->"} = "SELECTED";
	
		$GTOOLS::TAG{"<!-- PAY_PICKUP_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PICKUP_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PICKUP_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PICKUP_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PICKUP_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_PICKUP_".$webdbref->{"pay_pickup"}."_SELECTED -->"} = "SELECTED";
	
		$GTOOLS::TAG{"<!-- PAY_WIRE_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_WIRE_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_WIRE_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_WIRE_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_WIRE_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_WIRE_".$webdbref->{"pay_wire"}."_SELECTED -->"} = "SELECTED";
		$GTOOLS::TAG{'<!-- PAY_WIRE_FEE -->'} = $webdbref->{'pay_wire_fee'};
		$GTOOLS::TAG{'<!-- PAY_WIRE_INSTRUCTIONS -->'} = $webdbref->{'pay_wire_instructions'};
	
		$GTOOLS::TAG{"<!-- PAY_CHECK_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHECK_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHECK_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHECK_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHECK_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHECK_".$webdbref->{"pay_check"}."_SELECTED -->"} = "SELECTED";
		$GTOOLS::TAG{'<!-- PAY_CHECK_FEE -->'} = $webdbref->{'pay_check_fee'};
	
		$GTOOLS::TAG{"<!-- PAY_COD_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_COD_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_COD_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_COD_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_COD_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_COD_".$webdbref->{"pay_cod"}."_SELECTED -->"} = "SELECTED";
		$GTOOLS::TAG{'<!-- PAY_COD_FEE -->'} = $webdbref->{'pay_cod_fee'};
	
		$GTOOLS::TAG{"<!-- PAY_CHKOD_0_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHKOD_1_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHKOD_3_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHKOD_7_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHKOD_15_SELECTED -->"} = "";
		$GTOOLS::TAG{"<!-- PAY_CHKOD_".$webdbref->{"pay_chkod"}."_SELECTED -->"} = "SELECTED";
		$GTOOLS::TAG{'<!-- PAY_CHKOD_FEE -->'} = $webdbref->{'pay_chkod_fee'};


#		use Data::Dumper;
#		print STDERR Dumper(\%GTOOLS::TAG);
	
		$template_file = 'offline.shtml';
		push @BC, { name=>'Offline',link=>'/biz/setup/payment','target'=>'_top', },
		}
	}
	

##
## CREDIT CARDS
##

if ($TAB eq 'PROCESSOR') {

	if ($ACTION eq 'NONE') {
		if ($ACTION eq "NONE") { $webdbref->{'cc_processor'} = 'NONE'; }
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		$ACTION = '';
		}

	if ($ACTION eq "") {
		my $c = $webdbref->{'cc_processor'};
		$GTOOLS::TAG{"<!-- C -->"} = $c;
		# Default the $cc_processor value
		## There seems to be some missing from the above list, but I'm afraid to put anything in there...  -AK

		my $found = 0;
		foreach my $processor (qw(NONE QBMS MANUAL TESTING VERISIGN ECHO PAYPALWP AUTHORIZENET LINKPOINT TC SKIPJACK IONGATE SUREPAY)) {
			### having trouble?? check the whitelist above!
			$GTOOLS::TAG{"<!-- $processor -->"} = '';
			if ($c eq $processor) { 
				$found=1;
				$GTOOLS::TAG{"<!-- $processor -->"} = 'CHECKED';
				}
			}
		
		if (not $found) {
			$GTOOLS::TAG{'<!-- NONE -->'} = 'CHECKED';
			}
 	
		push @BC, { name=>'Choose Processor',link=>'', };
		$template_file = 'processor.shtml';
		}
	else {
		## we're' on processor, but we want to move to CREDIT/ACTION
		$TAB = 'CREDIT';
		$webdbref->{'cc_processor'} = $ACTION;
		}

	if ($ACTION eq 'HELP') {
		$TAB = 'HELP';
		$ACTION = '';
		}

	}




##
## PROCESSOR CONFIG
##
if ($TAB eq 'CREDIT') {

	push @BC, { name=>'Credit Cards',link=>'/biz/setup/payment/index.cgi?TAB=CREDIT','target'=>'_top', };
	$help = "#50304";

	
	if ($ACTION =~ /.*-SAVE$/) {
		## common save - saves the following:
		##		webdb/pay_credit - a list of payment methods accepted
		##		
		&nuke_requests($webdbref);
		my $cc_types = "";
		if ($ZOOVY::cgiv->{'cc_type_visa'})  { $cc_types .= "VISA,"; }
		if ($ZOOVY::cgiv->{'cc_type_mc'})    { $cc_types .= "MC,"; }
		if ($ZOOVY::cgiv->{'cc_type_amex'})  { $cc_types .= "AMEX,"; }
		if ($ZOOVY::cgiv->{'cc_type_novus'}) { $cc_types .= "NOVUS,"; }
		chop($cc_types);
		$webdbref->{"cc_types"}             = $cc_types;
		$webdbref->{"pay_credit"}           = $ZOOVY::cgiv->{"pay_credit"};
		$webdbref->{'cc_avs_review'}	= $ZOOVY::cgiv->{'cc_avs_review'};
		$webdbref->{'cc_cvv_review'}	= $ZOOVY::cgiv->{'cc_cvv_review'};
	
		my %fees = ();
		$fees{'CC_TRANSFEE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'CC_TRANSFEE'}))?$ZOOVY::cgiv->{'CC_TRANSFEE'}:'0';
		$fees{'CC_DISCRATE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'CC_DISCRATE'}))?$ZOOVY::cgiv->{'CC_DISCRATE'}:'0';
		$fees{'VISA_TRANSFEE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'VISA_TRANSFEE'}))?$ZOOVY::cgiv->{'VISA_TRANSFEE'}:'0';
		$fees{'VISA_DISCRATE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'VISA_DISCRATE'}))?$ZOOVY::cgiv->{'VISA_DISCRATE'}:'0';
		$fees{'MC_TRANSFEE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'MC_TRANSFEE'}))?$ZOOVY::cgiv->{'MC_TRANSFEE'}:'0';
		$fees{'MC_DISCRATE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'MC_DISCRATE'}))?$ZOOVY::cgiv->{'MC_DISCRATE'}:'0';
		$fees{'AMEX_TRANSFEE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'AMEX_TRANSFEE'}))?$ZOOVY::cgiv->{'AMEX_TRANSFEE'}:'0';
		$fees{'AMEX_DISCRATE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'AMEX_DISCRATE'}))?$ZOOVY::cgiv->{'AMEX_DISCRATE'}:'0';
		$fees{'NOVUS_TRANSFEE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'NOVUS_TRANSFEE'}))?$ZOOVY::cgiv->{'NOVUS_TRANSFEE'}:'0';
		$fees{'NOVUS_DISCRATE'} = (&ZTOOLKIT::isdecnum($ZOOVY::cgiv->{'NOVUS_DISCRATE'}))?$ZOOVY::cgiv->{'NOVUS_DISCRATE'}:'0';
		$webdbref->{'cc_fees'} = &ZTOOLKIT::buildparams(\%fees);
		# &ZTOOLKIT::parseparams(
		}

	if ($ACTION eq 'TESTING-SAVE') {
		$ACTION = 'TESTING';

		if ($ZOOVY::cgiv->{"pay_echeck"}>0) {
			$webdbref->{'echeck_processor'} = 'TESTING';
			$webdbref->{"pay_echeck"}           = $ZOOVY::cgiv->{"pay_echeck"};
			}
		else {
			$webdbref->{'echeck_processor'} = '';
			}

		$webdbref->{'cc_processor'}     = 'TESTING';

		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'cc_cvvcid'} = $ZOOVY::cgiv->{'cc_cvvcid'};
		$LU->log('SETUP.PAYMENT.TESTING',"Updated TESTING settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		push @MSGS, "SUCCESS|Saved Testing Gateway Settings Successfully";
		}

	if ($ACTION eq 'QBMS-SAVE') {
		$ACTION = 'QBMS';
		$webdbref->{'cc_processor'}     = 'QBMS';
		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'zid_qbms_sync'}	= (defined $ZOOVY::cgiv->{'zid_qbms_sync'})?1:0;

		## set to null, QBMS doesn't have API for echeck
		$webdbref->{'echeck_processor'} = '';
		$webdbref->{'pay_echeck'} = '';

		$webdbref->{'cc_cvvcid'} = 2; 	# 2=require CVV/CID card code | 1=optional | 0=do not ask

		$LU->log('SETUP.PAYMENT.QBMS',"Updated QBMS settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		push @MSGS, "SUCCESS|Saved QBMS Gateway Settings Successfully";
		}

	if ($ACTION eq 'ECHO-SAVE') {
		$ACTION = "ECHO";
	
		$webdbref->{'cc_processor'}     = 'ECHO';
		$webdbref->{'echeck_processor'} = 'ECHO';
		$webdbref->{'echeck_request_check_number'} = 1; ## Used by checkout to determine which fields to ask for
		$webdbref->{'echeck_request_drivers_license_number'} = 1;
		$webdbref->{'echeck_request_drivers_license_state'}  = 1;
		$webdbref->{'echeck_request_drivers_license_exp'}    = 1;
		$webdbref->{'echeck_request_business_account'}       = 1;
		if ($ZOOVY::cgiv->{"echo_username"}) { $webdbref->{"echo_username"} = $ZOOVY::cgiv->{"echo_username"}; }
		if ($ZOOVY::cgiv->{"echo_password"} && $ZOOVY::cgiv->{"echo_password"} ne '') { $webdbref->{"echo_password"} = $ZOOVY::cgiv->{"echo_password"}; }
	
		$webdbref->{'cc_cvvcid'} = $ZOOVY::cgiv->{'cc_cvvcid'};
	
		$webdbref->{'pay_echeck'}           = $ZOOVY::cgiv->{'pay_echeck'};
		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'echeck_success_code'}  = $ZOOVY::cgiv->{'echeck_success_code'};
		$webdbref->{'echeck_payable_to'}    = $ZOOVY::cgiv->{'echeck_payable_to'};

		$webdbref->{'echo_cybersource'} = $ZOOVY::cgiv->{'echo_cybersource'};
	
		$LU->log('SETUP.PAYMENT.ECHO',"Updated ECHO settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		push @MSGS, "SUCCESS|Saved ECHO Gateway Settings Successfully";
		} ## end if ($ACTION eq 'ECHO-SAVE'...


	if ($ACTION eq 'SKIPJACK-SAVE') {
		$ACTION = 'SKIPJACK';
		$webdbref->{'cc_processor'}     = 'SKIPJACK';
		$webdbref->{'echeck_processor'} = 'NONE';
	
		$webdbref->{'skipjack_htmlserial'} = $ZOOVY::cgiv->{'skipjack_htmlserial'};
		$webdbref->{'cc_cvvcid'}           = $ZOOVY::cgiv->{'cc_cvvcid'};
	
		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$LU->log('SETUP.PAYMENT.SKIPJACK',"Updated SKIPJACK settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		push @MSGS, "SUCCESS|Saved Skipjack Gateway Settings Successfully";
		} ## end if ($ACTION eq 'SKIPJACK-SAVE'...

	if ($ACTION eq "VERISIGN-SAVE") {
		$ACTION = "VERISIGN";

		$webdbref->{'cc_processor'}     = 'VERISIGN';
		$webdbref->{'echeck_processor'} = 'NONE';
		$webdbref->{"verisign_username"} = $ZOOVY::cgiv->{"verisign_username"}; 
		if ($ZOOVY::cgiv->{"verisign_password"} ne '') {
			$webdbref->{"verisign_password"} = $ZOOVY::cgiv->{"verisign_password"}; 
			}
		$webdbref->{"verisign_partner"}  = $ZOOVY::cgiv->{"verisign_partner"}; 
		$webdbref->{"verisign_vendor"}   = $ZOOVY::cgiv->{"verisign_vendor"};
		$webdbref->{'cc_cvvcid'} = $ZOOVY::cgiv->{'cc_cvvcid'};

		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$LU->log('SETUP.PAYMENT.VERISIGN',"Updated VERISIGN settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		push @MSGS, "SUCCESS|Saved Paypal Payflow Pro Gateway Settings Successfully";
		} ## end if ($ACTION eq "VERISIGN-SAVE"...


	if ($ACTION eq 'AUTHORIZENET-SETUPSAVE') {
		$ACTION = "AUTHORIZENET";
		$webdbref->{"authorizenet_username"}   = $ZOOVY::cgiv->{"authorizenet_username"};
		if ($ZOOVY::cgiv->{"authorizenet_password"} ne '') { $webdbref->{"authorizenet_password"} = $ZOOVY::cgiv->{"authorizenet_password"}; }
		$webdbref->{"authorizenet_key"}        = $ZOOVY::cgiv->{"authorizenet_key"};
		$LU->log('SETUP.PAYMENT.AUTHORIZENET',"Updated User/Password credentials","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
      push @MSGS, "SUCCESS|Saved Authorize.net Gateway Credentials Successfully";
 		}
	

	if ($ACTION eq "AUTHORIZENET-SAVE") {
		$ACTION = "AUTHORIZENET";
	
		$webdbref->{'cc_processor'}     = 'AUTHORIZENET';
		$webdbref->{'echeck_processor'} = 'AUTHORIZENET';
	
		($webdbref->{"authorizenet_wellsfargo"}) = $ZOOVY::cgiv->{"authorizenet_wellsfargo"};
	
		$webdbref->{'echeck_request_acct_name'} = 1; 
		$webdbref->{'cc_request_business_account'}       = 0;
		$webdbref->{'cc_request_tax_id'}                 = 0;
		$webdbref->{'cc_request_drivers_license_number'} = 0;
		$webdbref->{'cc_request_drivers_license_state'}  = 0;
		$webdbref->{'cc_request_drivers_license_dob'}    = 0;
		if ($webdbref->{"authorizenet_wellsfargo"}>0) {
			$webdbref->{'echeck_request_business_account'}       = 1;
			$webdbref->{'echeck_request_tax_id'}                 = 1;
			$webdbref->{'echeck_request_drivers_license_number'} = 1;
			$webdbref->{'echeck_request_drivers_license_state'}  = 1;
			$webdbref->{'echeck_request_drivers_license_dob'}    = 1;
			$webdbref->{'echeck_notice'} = "To process this transaction you need to either provide Driver's License or SSN / Tax ID information.";
			# $webdbref->{'cc_notice'} = "To process this transaction you need to either provide Driver's License or SSN / Tax ID information.";
			}
	
		if ($webdbref->{"authorizenet_wellsfargo"}==2) {
			$webdbref->{'cc_request_business_account'}       = 1;
			$webdbref->{'cc_request_tax_id'}                 = 1;
			$webdbref->{'cc_request_drivers_license_number'} = 1;
			$webdbref->{'cc_request_drivers_license_state'}  = 1;
			$webdbref->{'cc_request_drivers_license_dob'}    = 1;
			}
	
		$webdbref->{'cc_cvvcid'} = $ZOOVY::cgiv->{'cc_cvvcid'};
		
		my $cc_types = "";
		if ($ZOOVY::cgiv->{'cc_type_visa'})  { $cc_types .= "VISA,"; }
		if ($ZOOVY::cgiv->{'cc_type_mc'})    { $cc_types .= "MC,"; }
		if ($ZOOVY::cgiv->{'cc_type_amex'})  { $cc_types .= "AMEX,"; }
		if ($ZOOVY::cgiv->{'cc_type_novus'}) { $cc_types .= "NOVUS,"; }
		chop($cc_types);
	
		$webdbref->{"cc_types"}             = $cc_types;
		$webdbref->{'pay_echeck'}           = $ZOOVY::cgiv->{'pay_echeck'};
		$webdbref->{"pay_credit"}           = $ZOOVY::cgiv->{"pay_credit"};
		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'echeck_success_code'}  = $ZOOVY::cgiv->{'echeck_success_code'};
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
      push @MSGS, "SUCCESS|Saved Authorize.Net Gateway Settings Successfully";
 		} ## end if ($ACTION eq "AUTHORIZENET-SAVE"...
	

	if ($ACTION eq 'PAYPALWP-SAVE') {
		$ACTION = 'PAYPALWP';
		$webdbref->{'cc_processor'} = 'NONE';
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'cc_cvvcid'} = 2; 	# 2=require CVV/CID card code | 1=optional | 0=do not ask
		if ($ZOOVY::cgiv->{'paypal_use_wp'}) {
			$webdbref->{'cc_processor'} = 'PAYPALWP';
			}
		$LU->log('SETUP.PAYMENT.PAYPALWP',"Updated Paypal Website Payments settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
      push @MSGS, "SUCCESS|Saved Paypal Payflow Website Payments Pro Settings Successfully";
 		}

	if ($ACTION eq "LINKPOINT-SAVE") {
		$ACTION = "LINKPOINT";
	
		$webdbref->{'cc_processor'}       = 'LINKPOINT';
		$webdbref->{'echeck_processor'}   = 'LINKPOINT';
	
		$webdbref->{'echeck_request_check_number'}           = 1; ## Used by checkout to determine which fields to ask for
		$webdbref->{'echeck_request_acct_name'}              = 1; 
		$webdbref->{'echeck_request_drivers_license_number'} = 1; 
		$webdbref->{'echeck_request_drivers_license_state'}  = 1; 
		$webdbref->{'echeck_request_bank_state'}             = 1; 
	
		if ($ZOOVY::cgiv->{"storename"}) { $webdbref->{"storename"} = $ZOOVY::cgiv->{"storename"}; }

		my $x = $webdbref->{"storename"};
		$x =~ s/[^\d]+//gs;
		if ($x ne $webdbref->{'storename'} || $x eq '') {
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<font color="red"><br><h2>Critical Error: Linkpoint Store Name must be given, it must contain only numbers.</h2></font>';
			}
		$webdbref->{'linkpoint_storename'} = $x;
		$webdbref->{'storename'}           = $x;
		$webdbref->{'cc_cvvcid'} = $ZOOVY::cgiv->{'cc_cvvcid'};
	
		$webdbref->{'pay_echeck'}           = $ZOOVY::cgiv->{'pay_echeck'};
		$webdbref->{"cc_avs_require"}       = $ZOOVY::cgiv->{"cc_avs_require"};
		$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};
		$webdbref->{'echeck_success_code'}  = $ZOOVY::cgiv->{'echeck_success_code'};
		$LU->log('SETUP.PAYMENT.LINKPOINT',"Updated Linkpoint settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
      push @MSGS, "SUCCESS|Saved Linkpoint Gateway Settings Successfully";
 		} ## end if ($ACTION eq "LINKPOINT-SAVE"...


	if ($ACTION eq 'OTHER-SAVE') {
		## a generic gateway .. 
		$ACTION = 'OTHER';
		}
	
	if ($ACTION eq "MANUAL-SAVE") {
		$ACTION = "MANUAL";
		$webdbref->{'cc_processor'}     = 'MANUAL';
		$webdbref->{'echeck_processor'} = 'NONE';

		$webdbref->{'cc_emulate_gateway'} = (defined $ZOOVY::cgiv->{'cc_emulate_gateway'})?1:0;

		$LU->log('SETUP.PAYMENT.MANUAL',"Updated Manual CC settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
      push @MSGS, "SUCCESS|Saved Manual Gateway Settings Successfully";
 		} ## end if ($ACTION eq "MANUAL-SAVE"...

	# this is the save for both NONE and the SELECT page

	if ($ACTION eq 'NONE') {
		$webdbref->{'cc_processor'} = '';
		$LU->log('SETUP.PAYMENT.CREDIT',"Updated Credit Card Processor to 'NONE'","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
		}


	if ($ACTION eq "SAVE") {
		
		$webdbref->{'cc_processor'} = $ZOOVY::cgiv->{'process'};
		if (($webdbref->{'cc_processor'} eq 'ECHO') || ($webdbref->{'cc_processor'} eq 'AUTHORIZENET')) {
			$webdbref->{'echeck_processor'} = $webdbref->{'cc_processor'};
			}
		else {
			$webdbref->{'echeck_processor'} = 'NONE';
			}

		## only save when they won't be going to the next step (eg: tell them we've saved nothing)
		if ($webdbref->{'cc_processor'} eq 'NONE') {
			$webdbref->{'cc_types'}   = '';
			$webdbref->{'pay_credit'} = 0;
			$LU->log('SETUP.PAYMENT.CREDIT',"Updated Credit Card settings","SAVE");
			&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);	
			push @MSGS, "SUCCESS|Saved disabled credit card processing.";
 			}

		$ACTION = "JUMP";
		} ## end if ($ACTION eq "SAVE")

	## AT THIS POINT WE'RE DONE PROCESSING ANYTHING THAT SAVED
	$GTOOLS::TAG{'<!-- CC_CVVCID_0 -->'} = '';
	$GTOOLS::TAG{'<!-- CC_CVVCID_1 -->'} = '';
	$GTOOLS::TAG{'<!-- CC_CVVCID_2 -->'} = '';
	$GTOOLS::TAG{"<!-- CC_CVVCID_" . $webdbref->{'cc_cvvcid'} . " -->"} = ' SELECTED ';

	# whitelist the $webdbref->{'cc_processor'} default to NONE
	if ($webdbref->{'cc_processor'} ne 'MANUAL' && 
		$webdbref->{'cc_processor'} ne 'IONGATE' && 
		$webdbref->{'cc_processor'} ne 'QBMS' && 
		$webdbref->{'cc_processor'} ne 'TC' && 
		$webdbref->{'cc_processor'} ne 'ECHO' && 
		$webdbref->{'cc_processor'} ne 'VERISIGN' && 
		$webdbref->{'cc_processor'} ne 'PAYPALWP' && 
		$webdbref->{'cc_processor'} ne 'AUTHORIZENET' && 
		$webdbref->{'cc_processor'} ne 'SKIPJACK' && 
		$webdbref->{'cc_processor'} ne 'LINKPOINT' && 
		$webdbref->{'cc_processor'} ne 'SUREPAY') { 
		$webdbref->{'cc_processor'} = 'NONE'; 
		}
	
	# this should always run first, if jump then we'll go straight to the correct processor
	if ($ACTION eq 'JUMP') { $ACTION = $webdbref->{'cc_processor'}; }

	if ($webdbref->{'cc_processor'} ne 'NONE') {
		if ($webdbref->{'cc_instant_capture'} eq '') {
			push @MSGS, "WARNING|+Gateway capture setting is invalid.";
			}
		}

	if ($ACTION eq 'MANUAL') {
		&build_general($webdbref);
	
		if ($webdbref->{"cc_emulate_gateway"} == 1) {
			$GTOOLS::TAG{"<!-- CC_EMULATE_GATEWAY -->"} = 'checked';
			}
		else {
			$GTOOLS::TAG{"<!-- CC_EMULATE_GATEWAY -->"} = '';
			}
	
		push @BC, { name=>'Manual',link=>'', };
		$template_file = 'credit-manual.shtml';
		}
	
	if ($ACTION eq 'SKIPJACK') {
		&build_general($webdbref);
		$GTOOLS::TAG{'<!-- SKIPJACK_HTMLSERIAL -->'} = $webdbref->{'skipjack_htmlserial'};
		push @BC, { name=>'Skipjack',link=>'', };
		$template_file = 'credit-skipjack.shtml';
		}
	
	if ($ACTION eq 'VERISIGN') {
		$GTOOLS::TAG{"<!-- VERISIGN_USERNAME -->"} = $webdbref->{"verisign_username"};
		#$GTOOLS::TAG{"<!-- VERISIGN_PASSWORD -->"} = $webdbref->{"verisign_password"};
		$GTOOLS::TAG{"<!-- VERISIGN_PARTNER -->"}  = $webdbref->{"verisign_partner"};
		$GTOOLS::TAG{"<!-- VERISIGN_VENDOR -->"}   = $webdbref->{"verisign_vendor"};
		&build_general($webdbref);
		push @BC, { name=>'Verisign Payflow Pro',link=>'', };
		$template_file = 'credit-verisign.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}

	if ($ACTION eq 'SUREPAY') {
		$GTOOLS::TAG{"<!-- SUREPAY_USERNAME -->"} = $webdbref->{"surepay_username"};
		#$GTOOLS::TAG{"<!-- SUREPAY_PASSWORD -->"} = $webdbref->{"surepay_password"};
		&build_general($webdbref);
		push @BC, { name=>'Surepay',link=>'', };
		$template_file = 'credit-surepay.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; } 
		}

	if ($ACTION eq 'ECHO') {
		$GTOOLS::TAG{'<!-- ECHO_CYBERSOURCE_NONE -->'} = ($webdbref->{'echo_cybersource'} eq '')?'selected':'';
		$GTOOLS::TAG{'<!-- ECHO_CYBERSOURCE_NOFRAUD -->'} = ($webdbref->{'echo_cybersource'} eq 'NOFRAUD')?'selected':'';

		$GTOOLS::TAG{"<!-- ECHO_USERNAME -->"}     = &ZOOVY::incode($webdbref->{"echo_username"});
		$GTOOLS::TAG{"<!-- ECHO_PASSWORD -->"}     = &ZOOVY::incode($webdbref->{"echo_password"});
		&build_general($webdbref);
		push @BC, { name=>'ECHO',link=>'', };
		$template_file = 'credit-echo.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}

	if ($ACTION eq 'AUTHORIZENET') {
		$GTOOLS::TAG{"<!-- AUTHORIZENET_WELLSFARGO_0_SELECTED -->"} = '' ;
		$GTOOLS::TAG{"<!-- AUTHORIZENET_WELLSFARGO_1_SELECTED -->"} = '' ;
		$GTOOLS::TAG{"<!-- AUTHORIZENET_WELLSFARGO_2_SELECTED -->"} = '' ;
		$GTOOLS::TAG{"<!-- AUTHORIZENET_WELLSFARGO_".$webdbref->{"authorizenet_wellsfargo"}."_SELECTED -->"} = 'selected' ;
	
		if ($webdbref->{'authorizenet_username'} eq '') {
			$GTOOLS::TAG{'<!-- USERNAME -->'} = "<font color='red'>NOT SET</font>";
			$GTOOLS::TAG{'<!-- PASSWORD -->'} = "<font color='red'>NOT SET</font>";
			$GTOOLS::TAG{'<!-- KEY -->'} = "<font color='red'>NOT SET</font>";
			}
		else {
			$GTOOLS::TAG{'<!-- USERNAME -->'} = $webdbref->{'authorizenet_username'};
			$GTOOLS::TAG{'<!-- PASSWORD -->'} = "<i>hidden</i>";
			$GTOOLS::TAG{'<!-- KEY -->'} = "<i>hidden</i>";
			}
		
	
		&build_general($webdbref);
		push @BC, { name=>'Authorize.Net',link=>'', };

		## get link for WEBDOC
		my ($helplink, $helphtml) = GTOOLS::help_link('Authorize.net', 50276);
		$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helplink;
		
		$template_file = 'credit-authorize.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}
	
	if	($ACTION eq 'AUTHORIZENET-SETUP') {
		$GTOOLS::TAG{"<!-- AUTHORIZENET_USERNAME -->"} = $webdbref->{"authorizenet_username"};
		$template_file = 'credit-authorizesetup.shtml';		
		}
	
	
	if ($ACTION eq 'OTHER') {
		$GTOOLS::TAG{'<!-- CC_PROCESSOR -->'} = $webdbref->{'cc_processor'};
		$GTOOLS::TAG{'<!-- PARAMETERS -->'} = $webdbref->{'cc_parameters'};
		$template_file = 'credit-other.shtml';
		}


	if ($ACTION eq 'TC') {
		$GTOOLS::TAG{"<!-- TC_LOGIN -->"}    = $webdbref->{"tc_login"};
		#$GTOOLS::TAG{"<!-- TC_PASSWORD -->"} = $webdbref->{"tc_password"};
		&build_general($webdbref);
		push @BC, { name=>'PRI/Transaction Central',link=>'', };
		$template_file = 'credit-tc.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}

	if ($ACTION eq 'PAYPALWP') {
		$template_file = 'credit-paypalwp.shtml';
		&build_general($webdbref);

		$GTOOLS::TAG{'<!-- CHECKED_PAYPAL_USE_WP -->'} = ($webdbref->{'cc_processor'} eq 'PAYPALWP')?'checked':'';
		$GTOOLS::TAG{'<!-- PAYPAL_EMAIL -->'} = $webdbref->{'paypal_email'};

		push @BC, { name=>'Paypal Website Payments Pro',link=>'' };
		}

	if ($ACTION eq 'TESTING') {
		&build_general($webdbref);
		require ZPAY::TESTING;

		my $c = '';
		foreach my $ref (@ZPAY::TESTING::CARDS) {
			$c .= "<tr><td>$ref->[0]</td><td>$ref->[1]</td><td>$ref->[2]</td><td>".sprintf("\$%.2f",$ref->[3])."</td>";
			}		
		$c = "<tr class='zoovysub1header'><td>Card Type</td><td>Card Number</td><td>CVV</td><td>Limit\$</td></tr>$c";
		$c = "<table>$c</table>";
		$GTOOLS::TAG{'<!-- CARDS -->'} = $c;
		push @BC, { name=>'Testing Gateway',link=>'' };

		$template_file = 'credit-testing.shtml';
		}	


	if ($ACTION eq 'LINKPOINT') {
		my $pemfile = &ZOOVY::resolve_userpath($USERNAME) . "/linkpoint.pem";
		if (!-f $pemfile) {
			$GTOOLS::TAG{'<!-- LINKPOINT_PEM_MISSING -->'} = "<font color='red'><h2><b>CONFIGURATION ERROR:</b> Missing PEM file - please request a PEM file for Linkpoint API from Cardservice and contact Zoovy technical support to have it installed.</h2></font>";
			}
	
		$GTOOLS::TAG{"<!-- LINKPOINT_STORENAME -->"} = $webdbref->{"storename"};
		&build_general($webdbref);

		## get link for WEBDOC in templates
		my ($helplink, $helphtml) = GTOOLS::help_link('Payment Gateways', 50280);
		$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helplink;

		push @BC, { name=>'Cardservice Linkpoint',link=>'', };
		$template_file = 'credit-linkpoint.shtml';
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}
	
	if ($ACTION eq 'QBMS') {
		$GTOOLS::TAG{'<!-- MID -->'} = $MID;
		$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
		$template_file = 'credit-qbms.shtml';

		if (not defined $webdbref->{'zid_qbms_sync'}) { $webdbref->{'zid_qbms_sync'}++; }
		$GTOOLS::TAG{'<!-- ZID_QBMS_SYNC_CB -->'} = ($webdbref->{'zid_qbms_sync'})?'checked':'';

		if ($webdbref->{'qbms_appid'} eq '') {
			$GTOOLS::TAG{'<!-- TOKEN_STATUS -->'} = "<font color='red'>NOT AUTHORIZED: Before continuing use the links above to authorize Zoovy to access your Quickbooks Merchant Services Account</font>";
			}
		elsif ($webdbref->{'qbms_appid'} eq '58002316') {
			$GTOOLS::TAG{'<!-- TOKEN_STATUS -->'} = "<font color='orange'>Authorized on Test Server</font>"; 
			}
		elsif ($webdbref->{'qbms_appid'} eq '83162751') {
			$GTOOLS::TAG{'<!-- TOKEN_STATUS -->'} = "<font color='blue'>Successfully Authorized on Production</font>";
			}
		else {
			$GTOOLS::TAG{'<!-- TOKEN_STATUS -->'} = "<font color='red'>Token Authorized with Unknown Application Id [$webdbref->{'qbms_appid'}].</font>";
			}


		&build_general($webdbref);
		push @BC, { name=>'Quickbooks Merchant Services',link=>'', };
		if (not $GATEWAY_OKAY) { $template_file = "processor-deny.shtml"; }
		}



	
	}	
############################################################
## END: Merchant account code
############################################################


if ($TAB eq 'AMZPAY-SAVE') {
	$webdbref->{'amzpay_button'} = &ZTOOLKIT::buildparams({
		color=>$ZOOVY::cgiv->{'color'},
		size=>$ZOOVY::cgiv->{'size'},
		background=>$ZOOVY::cgiv->{'background'},
		});
	print STDERR "AMZBUTTON: $webdbref->{'amzpay_button'}\n";

	$webdbref->{'amzpay_env'} = int($ZOOVY::cgiv->{'amzpay_env'});
	#$webdbref->{'amzpay_tax'} = (defined $ZOOVY::cgiv->{'amzpay_tax'})?1:0;
	#$webdbref->{'amzpay_shipping'} = (defined $ZOOVY::cgiv->{'amzpay_shipping'})?1:0;
	#$webdbref->{'amzpay_simplepay'} = (defined $ZOOVY::cgiv->{'amzpay_simplepay'})?1:0;

	## no longer configurable
	## we currently only support these settings
	## - tax is always pulled from Amazon
	## - shipping is always pulled from Zoovy
	## - simple pay is not yet supported??
	$webdbref->{'amzpay_tax'} = 1; 
	$webdbref->{'amzpay_shipping'} = 1;
	$webdbref->{'amzpay_simplepay'} = 0;

	$LU->log('SETUP.PAYMENT.AMAZON',"Updated Checkout by Amazon settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
	$TAB = 'AMZPAY';
	}

if ($TAB eq 'AMZPAY') {
	require ZPAY::AMZPAY;
	
	$GTOOLS::TAG{'<!-- AMZPAY_ENV_0 -->'} = ($webdbref->{'amzpay_env'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- AMZPAY_ENV_1 -->'} = ($webdbref->{'amzpay_env'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- AMZPAY_ENV_2 -->'} = ($webdbref->{'amzpay_env'}==2)?'selected':'';

	## no longer configurable
	## we currently only support these settings
	## - tax is always pulled from Amazon
	## - shipping is always pulled from Zoovy
	## - simple pay is not yet supported??
	#$GTOOLS::TAG{'<!-- CHK_AMZPAY_TAX -->'} = ($webdbref->{'amzpay_tax'})?'checked':'';
	#$GTOOLS::TAG{'<!-- CHK_AMZPAY_SHIPPING -->'} = ($webdbref->{'amzpay_shipping'})?'checked':'';
	#$GTOOLS::TAG{'<!-- CHK_AMZPAY_SIMPLEPAY -->'} = ($webdbref->{'amzpay_simplepay'})?'checked':'';

	$GTOOLS::TAG{'<!-- AMZ_MERCHANTID -->'} = &ZOOVY::incode($webdbref->{'amz_merchantid'});
	if ($GTOOLS::TAG{'<!-- AMZ_MERCHANTID -->'} eq '') { $GTOOLS::TAG{'<!-- AMZ_MERCHANTID -->'} = "<i>Not set</i>"; }
	$GTOOLS::TAG{'<!-- AMZ_ACCESSKEY -->'} = &ZOOVY::incode($webdbref->{'amz_accesskey'});
	if ($GTOOLS::TAG{'<!-- AMZ_ACCESSKEY -->'} eq '') { $GTOOLS::TAG{'<!-- AMZ_ACCESSKEY -->'} = "<i>Not set</i>"; }
	$GTOOLS::TAG{'<!-- AMZ_SECRETKEY -->'} = &ZOOVY::incode($webdbref->{'amz_secretkey'});
	if ($GTOOLS::TAG{'<!-- AMZ_SECRETKEY -->'} eq '') { $GTOOLS::TAG{'<!-- AMZ_SECRETKEY -->'} = "<i>Not set</i>"; }

	my ($CART2) = CART2->new_memory($USERNAME,$PRT);
	my ($SITE) = SITE->new($USERNAME,PRT=>$PRT);
	$GTOOLS::TAG{'<!-- BUTTON_HTML -->'} = &ZPAY::AMZPAY::button_html($CART2,$SITE);

	my $btnref = &ZTOOLKIT::parseparams($webdbref->{'amzpay_button'});
	$GTOOLS::TAG{'<!-- color_orange -->'} = ($btnref->{'color'} eq 'orange')?'selected':'';
	$GTOOLS::TAG{'<!-- color_tan -->'} = ($btnref->{'color'} eq 'tan')?'selected':'';
	$GTOOLS::TAG{'<!-- size_small -->'} = ($btnref->{'size'} eq 'small')?'selected':'';
	$GTOOLS::TAG{'<!-- size_large -->'} = ($btnref->{'size'} eq 'large')?'selected':'';
	$GTOOLS::TAG{'<!-- background_white -->'} = ($btnref->{'background'} eq 'white')?'selected':'';
	$GTOOLS::TAG{'<!-- background_other -->'} = ($btnref->{'background'} eq 'other')?'selected':'';

	$template_file = 'amzpay.shtml';
	}


##############################################################
##
##
##############################################################

if ($TAB eq 'GOOGLE-SAVE') {

	$ZOOVY::cgiv->{'google_key'} =~ s/[^A-Za-z0-9\-\_\+]+//gs;	# clean out unallowed chars.
	$webdbref->{'google_key'} = $ZOOVY::cgiv->{'google_key'};
	$ZOOVY::cgiv->{'google_merchantid'} =~ s/[^\d]+//gs;	# clean out unallowed chars.
	$webdbref->{'google_merchantid'} = $ZOOVY::cgiv->{'google_merchantid'};
	$webdbref->{'google_api_env'} = $ZOOVY::cgiv->{'google_api_env'};
	$webdbref->{'google_api_analytics'} = $ZOOVY::cgiv->{'google_api_analytics'};
	$webdbref->{'google_api_merchantcalc'} = $ZOOVY::cgiv->{'google_api_merchantcalc'};
	$webdbref->{'google_dest_zip'} = $ZOOVY::cgiv->{'google_dest_zip'};
	$webdbref->{'google_int_shippolicy'} = int($ZOOVY::cgiv->{'google_int_shippolicy'});
	$webdbref->{'google_pixelurls'} = $ZOOVY::cgiv->{'google_pixelurls'};
	$LU->log('SETUP.PAYMENT.GOOGLE',"Updated Google Checkout settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);

	$TAB = 'GOOGLE';
	}

if ($TAB eq 'GOOGLE') {
	$GTOOLS::TAG{'<!-- GOOGLE_MERCHANTID -->'} = &ZOOVY::incode($webdbref->{'google_merchantid'});
	$GTOOLS::TAG{'<!-- GOOGLE_KEY -->'} = &ZOOVY::incode($webdbref->{'google_key'});
	$GTOOLS::TAG{'<!-- GOOGLE_DEST_ZIP -->'} = &ZOOVY::incode($webdbref->{'google_dest_zip'});
	$GTOOLS::TAG{'<!-- GOOGLE_API_ANALYTICS_0 -->'} = ($webdbref->{'google_api_analytics'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_ANALYTICS_1 -->'} = ($webdbref->{'google_api_analytics'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_ANALYTICS_2 -->'} = ($webdbref->{'google_api_analytics'}==2)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_ENV_0 -->'} = ($webdbref->{'google_api_env'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_ENV_1 -->'} = ($webdbref->{'google_api_env'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_ENV_2 -->'} = ($webdbref->{'google_api_env'}==2)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_MERCHANTCALC_0 -->'} = ($webdbref->{'google_api_merchantcalc'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_MERCHANTCALC_1 -->'} = ($webdbref->{'google_api_merchantcalc'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_API_MERCHANTCALC_2 -->'} = ($webdbref->{'google_api_merchantcalc'}==2)?'selected':'';

	$GTOOLS::TAG{'<!-- GOOGLE_INT_SHIPPOLICY_0 -->'} = ($webdbref->{'google_int_shippolicy'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- GOOGLE_INT_SHIPPOLICY_1 -->'} = ($webdbref->{'google_int_shippolicy'}==1)?'selected':'';

	$GTOOLS::TAG{'<!-- GOOGLE_API_URL -->'} = "https://webapi.zoovy.com/webapi/google/callback.pl/u=$USERNAME/v=1";
	$GTOOLS::TAG{'<!-- GOOGLE_PIXELURLS -->'} = &ZOOVY::incode($webdbref->{'google_pixelurls'});

	my $has_bad_pixel = 0;
	if ($webdbref->{'google_pixelurls'} =~ /\<parameterized\-url/s) {
		push @MSGS, "WARNING|The tag 'parameterized-url' appears the Pixel URL field, this is almost certainly not correct and will not work.";
		$has_bad_pixel++;
		}
	if ($webdbref->{'google_pixelurls'} =~ /\<input/s) {
		push @MSGS, "WARNING|The xml/html tag 'input' appears the Pixel URL field, this absolutely not correct and will not work. ";
		$has_bad_pixel++;
		}
	if ($webdbref->{'google_pixelurls'} =~ /<.*?>/s) {
		push @MSGS, "WARNING|It appears there is HTML or XML in the Pixel URL field. This is most likely incorrect and probably won't work, and it will probably break google checkout.";
		$has_bad_pixel++;
		}
	if ($has_bad_pixel) {
		push @MSGS, "WARNING|You definitely have one or more issues with your Pixel URL (because you didn't create a URL at all and gave us XML/HTML instead), the documentation you are using is wrong/outdated and probably not written for Zoovy anyway.  The standard way Google provides examples make their integration only compatible with ONE PIXEL -- since many of our clients need MORE THAN ONE PIXEL -- we had to build something different - please refer to webdoc #50737";
		}

	my $i = 0;
	foreach my $line (split(/[\n\r]+/,$webdbref->{'tax_rules'})) {
		next if (($line eq '') || (substr($line,0,1) eq '#'));
		$i++;
		}
	if ($i>100) {
		push @MSGS, "WARNING|You have more than 100 tax rules, GoogleCheckout will only utilize the first 100";
		}
	
	push @BC, { name=>'Google Payments',link=>'' };
	$template_file = 'google.shtml';
	}


#############################################################
##
#############################################################



if ($TAB eq 'PAYPALEC-SAVE') {	
	## this was commented? no idea why. 6/1/08 bh
	$webdbref->{"cc_instant_capture"}   = $ZOOVY::cgiv->{"cc_instant_capture"};

	$webdbref->{'paypal_api_reqconfirmship'} = $ZOOVY::cgiv->{'paypal_api_reqconfirmship'};
	$webdbref->{'paypal_api_callbacks'} = $ZOOVY::cgiv->{'paypal_api_callbacks'};
	$webdbref->{'paypal_email'} = $ZOOVY::cgiv->{'paypal_email'};
	$webdbref->{'paypal_email'} =~ s/[\s]+//g;

	$ZOOVY::cgiv->{'paypal_api_user'} =~ s/^[\s]+//gs;
	$ZOOVY::cgiv->{'paypal_api_user'} =~ s/[\s]+$//gs;
	$webdbref->{'paypal_api_user'} = $ZOOVY::cgiv->{'paypal_api_user'};

	$ZOOVY::cgiv->{'paypal_api_pass'} =~ s/^[\s]+//gs;
	$ZOOVY::cgiv->{'paypal_api_pass'} =~ s/[\s]+$//gs;
	$webdbref->{'paypal_api_pass'} = $ZOOVY::cgiv->{'paypal_api_pass'};

	$ZOOVY::cgiv->{'paypal_api_sig'} =~ s/^[\s]+//gs;
	$ZOOVY::cgiv->{'paypal_api_sig'} =~ s/[\s]+$//gs;
	$webdbref->{'paypal_api_sig'} = $ZOOVY::cgiv->{'paypal_api_sig'};

	$webdbref->{'paypal_paylater'} = (defined $ZOOVY::cgiv->{'paypal_paylater'})?1:0;

	$webdbref->{'paypal_api_env'} = $ZOOVY::cgiv->{'paypal_api_env'};
	$webdbref->{'pay_paypalec'} = ($webdbref->{'paypal_api_env'}>0)?0xFF:00;

	$LU->log('SETUP.PAYMENT.PAYPALEC',"Updated Paypal Express Checkout settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);

	push @MSGS, "SUCCESS|Saved Paypal Express Checkout Settings Successfully";
 	$TAB = 'PAYPALEC';
	}

if ($TAB eq 'PAYPALEC') {
	$template_file = 'paypalec.shtml';
	&build_general($webdbref);

	$GTOOLS::TAG{'<!-- PAYPAL_EMAIL -->'} = $webdbref->{'paypal_email'};
	$GTOOLS::TAG{'<!-- PAYPAL_API_USER -->'} = $webdbref->{'paypal_api_user'};
	$GTOOLS::TAG{'<!-- PAYPAL_API_PASS -->'} = $webdbref->{'paypal_api_pass'};
	$GTOOLS::TAG{'<!-- PAYPAL_API_SIG -->'} = $webdbref->{'paypal_api_sig'};
	$GTOOLS::TAG{'<!-- PAYPAL_API_REQCONFIRMSHIP_0 -->'} = ($webdbref->{'paypal_api_reqconfirmship'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_REQCONFIRMSHIP_1 -->'} = ($webdbref->{'paypal_api_reqconfirmship'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_CALLBACKS_0 -->'} = ($webdbref->{'paypal_api_callbacks'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_CALLBACKS_1 -->'} = ($webdbref->{'paypal_api_callbacks'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_ENV_0 -->'} = ($webdbref->{'paypal_api_env'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_ENV_1 -->'} = ($webdbref->{'paypal_api_env'}==1)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_ENV_2 -->'} = ($webdbref->{'paypal_api_env'}==2)?'selected':'';
	$GTOOLS::TAG{'<!-- PAYPAL_API_ENV_3 -->'} = ($webdbref->{'paypal_api_env'}==3)?'selected':'';
	$GTOOLS::TAG{'<!-- CB_PAYPAL_PAYLATER -->'} = ($webdbref->{'paypal_paylater'}>0)?'checked':'';

	push @BC, { name=>'Paypal Express Checkout',link=>'' };
	}



##	
## Paypal
##

if ($TAB eq 'PAYPALIPN') {

	$help = "#50284";
	if ($ACTION eq "SAVE") {
		$webdbref->{"pay_paypal"}    = $ZOOVY::cgiv->{"pay_paypal"};
		if (defined $ZOOVY::cgiv->{'pay_bidpay'}) {
			$webdbref->{'pay_bidpay'} = '15';
			}
		else {
			$webdbref->{'pay_bidpay'} = 'NO';
			}

		if (defined $ZOOVY::cgiv->{"paypal_email"})       { $webdbref->{"paypal_email"}       = $ZOOVY::cgiv->{"paypal_email"}; }
		if (defined $ZOOVY::cgiv->{"PAYPAL_CONFIRM"})     { $webdbref->{"paypal_confirm"}     = $ZOOVY::cgiv->{"PAYPAL_CONFIRM"}; }
		if (defined $ZOOVY::cgiv->{"paypal_correlate"})   { $webdbref->{"paypal_correlate"}   = $ZOOVY::cgiv->{"PAYPAL_CORRELATE"}; }
		$webdbref->{"paypal_manual"}   = (uc($ZOOVY::cgiv->{"paypal_manual"}) eq "ON") ? 1 : 0 ;
		$webdbref->{"paypal_feedback"} = $ZOOVY::cgiv->{"paypal_manual"} ? 1 : 0 ;
		$webdbref->{"paypal_disable_ipn"} = $ZOOVY::cgiv->{"paypal_disable_ipn"} ? 1 : 0 ;
	# 	$webdbref->{"paypal_checkout"} = $ZOOVY::cgiv->{"paypal_checkout"} ? 1 : 0 ;
		$webdbref->{"paypal_disable_address"} = $ZOOVY::cgiv->{"paypal_disable_address"} ? 1 : 0 ;

		my $v = 0;
		for (my $x = 0; $x<16; $x++) {
			my $bit = 1 << $x;
			if ($ZOOVY::cgiv->{'IPN_'.$bit}) {
				$v += (1 << $x);
				}
			}
		print STDERR "RESULT: $v\n";
		$webdbref->{'pay_paypal_ipn'} = $v;

		$LU->log('SETUP.PAYMENT.PAYPALIPN',"Updated Paypal IPN settings (cfg=$v)","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);

		$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table width='80%' border='0' cellpadding='5'><tr><td><font size='4' color='red'><i>Saved PayPal Payment Settings</i></font></td></tr></table><br>";

	} ## end if ($ACTION eq "SAVE")

	## PAYPAL
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_0_SELECTED -->"}       = "";
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_1_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_3_SELECTED -->"}    = "";
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_7_SELECTED -->"}  = "";	
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_15_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_PAYPAL_".$webdbref->{"pay_paypal"}."_SELECTED -->"} = "SELECTED";

	## bits:
	##
	## 1 : enable processing
	## 2 : attempt to correlate unknown payments
	## 4 : create phantom orders for unknown items
	## 128 : notify of unknown payments
	## 256 : audit shipping
	## 512 : process promotions
	##
	if (not defined $webdbref->{'pay_paypal_ipn'}) { $webdbref->{'pay_paypal_ipn'} = 1+128; }
	for (my $x = 0; $x<16; $x++) {
		my $bit = 1 << $x;
		if (($webdbref->{'pay_paypal_ipn'} & $bit) == $bit) {	
			$GTOOLS::TAG{'<!-- IPN_'.$bit.' -->'} = 'checked'; 
			}
		else {
			$GTOOLS::TAG{'<!-- IPN_'.$bit.' -->'} = ''; 
			}
		}


	$GTOOLS::TAG{"<!-- VALUE_CREDIT_HANDLER_PAYPAL -->"} = " CHECKED ";
	$GTOOLS::TAG{"<!-- VALUE_PAYPAL_EMAIL -->"}          = " VALUE=\"" . $webdbref->{"paypal_email"} . "\" ";
	$GTOOLS::TAG{"<!-- VALUE_PAYPAL_LASTNAME -->"}       = " VALUE=\"" . $webdbref->{"paypal_lastname"} . "\" ";
	#$GTOOLS::TAG{"<!-- VALUE_PAYPAL_PASSWORD -->"}       = " VALUE=\"" . $webdbref->{"paypal_password"} . "\" ";
	$GTOOLS::TAG{"<!-- CHECKED_PAYPAL_MANUAL -->"}       = $webdbref->{"paypal_manual"}   ? ' CHECKED' : '' ;
	$GTOOLS::TAG{'<!-- PAYPAL_FEEDBACK -->'}             = $webdbref->{'paypal_feedback'} ? ' CHECKED' : '' ;
	$GTOOLS::TAG{'<!-- PAYPAL_DISABLE_IPN -->'}          = $webdbref->{'paypal_disable_ipn'} ? ' CHECKED' : '' ;
	$GTOOLS::TAG{'<!-- PAYPAL_MINIMAL -->'}              = $webdbref->{'paypal_minimal'} ? ' CHECKED' : '' ;
#	$GTOOLS::TAG{'<!-- PAYPAL_CHECKOUT -->'}              = $webdbref->{'paypal_checkout'} ? ' CHECKED' : '' ;

	$GTOOLS::TAG{'<!-- PAYPAL_CORRELATE_0 -->'}  = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CORRELATE_1 -->'}  = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CORRELATE_10 -->'} = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CORRELATE_'.$webdbref->{'paypal_correlate'}.' -->'} = 'checked';
	
	$GTOOLS::TAG{'<!-- PAYPAL_CONFIRM_ -->'}     = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CONFIRM_ANY -->'}  = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CONFIRM_CITY -->'} = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CONFIRM_ZIP -->'}  = '';
	$GTOOLS::TAG{'<!-- PAYPAL_CONFIRM_'.$webdbref->{'paypal_confirm'}.' -->'} = 'selected';

	## get link for WEBDOC in templates
	my ($helplink, $helphtml) = GTOOLS::help_link('Paypal', 50284);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helplink;

	push @BC, { name=>'Paypal',link=>'', };
	$template_file = 'paypalipn.shtml';
	}


##
## Advanced
##
if ($TAB eq 'ADVANCED') {
	## no specific help available
	## $help = '';

	if ($ACTION eq "SAVE") {
		&ZOOVY::savemerchant_attrib($USERNAME,"zoovy:payment_explanation",$ZOOVY::cgiv->{'payment_explanation'});
		$webdbref->{'pay_custom'} = defined($ZOOVY::cgiv->{'pay_custom'})?$ZOOVY::cgiv->{'pay_custom'}:'';
		$webdbref->{'pay_custom_desc'} = defined($ZOOVY::cgiv->{'pay_custom_desc'})?$ZOOVY::cgiv->{'pay_custom_desc'}:'';
		$LU->log('SETUP.PAYMENT.ADVANCED',"Updated Advanced Payment settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table width='80%' border='3' cellpadding='5'><tr><td><font size='5' color='red'><center>Saved Settings</font></td></tr></table><br>";
		}

	$GTOOLS::TAG{'<!-- PAY_CUSTOM_DESC -->'} = $webdbref->{'pay_custom_desc'};
	
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_0_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_1_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_3_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_7_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_15_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CUSTOM_".$webdbref->{"pay_custom"}."_SELECTED -->"} = "SELECTED";
	push @BC, { name=>'Advanced Payment Types',link=>'', };
	$template_file = 'advanced.shtml';
	}

##
## Special
##

if ($TAB eq 'SPECIAL') {
	if ($ACTION eq "SAVE") {
		if (defined $ZOOVY::cgiv->{'pay_bidpay'}) {
			$webdbref->{'pay_bidpay'} = '15';
			}
		else {
			$webdbref->{'pay_bidpay'} = 'NO';
			}

		$LU->log('SETUP.PAYMENT.SPECIAL',"Updated Special Payment Method settings","SAVE");
		&ZWEBSITE::save_website_dbref($USERNAME, $webdbref, $PRT);
	
		$GTOOLS::TAG{"<!-- MESSAGE -->"} = "<br><table width='80%' border='3' cellpadding='5'><tr><td><font size='5' color='red'><center>Saved Special Payment Settings</font></td></tr></table><br>";
		} ## end if ($ACTION eq "SAVE")

	## BIDPAY
	if ((!defined($webdbref->{'pay_bidpay'})) || ($webdbref->{'pay_bidpay'} eq '')) { $webdbref->{'pay_bidpay'} = 'NO'; }
	if ($webdbref->{'pay_bidpay'} ne 'NO') {
		$GTOOLS::TAG{'<!-- PAY_BIDPAY_CHECKED -->'} = 'checked';
		}
	else {
		$GTOOLS::TAG{'<!-- PAY_BIDPAY_CHECKED -->'} = '';
		}

	push @BC, { name=>'Speciality Payment Types',link=>'?TAB=SPECIAL', };
	$template_file = 'special.shtml';
	}

my @TABS = ();
##push @TABS, { name=>'All Payments',link=>'/biz/setup/payment/index.cgi?TAB=ALL','target'=>'_top', };
push @TABS, { name=>'Help',selected=>($TAB eq 'HELP')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=HELP','target'=>'_top', };
push @TABS, { name=>'Offline',selected=>($TAB eq 'OFFLINE')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=OFFLINE','target'=>'_top', };
push @TABS, { name=>'Credit Cards',selected=>($TAB eq 'PROCESSOR')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=PROCESSOR','target'=>'_top', };

#http://www.zoovy.com/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=PAYPALVT&x=54&y=18
if ($webdbref->{'cc_processor'} eq 'QBMS') {
	push @TABS, { name=>'QBMS Gateway', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=QBMS' };
	}
elsif ($webdbref->{'cc_processor'} eq 'PAYPALWP') {
	push @TABS, { name=>'Paypal Website Payments Pro', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=PAYPALWP' };
	}
elsif ($webdbref->{'cc_processor'} eq 'AUTHORIZENET') {
	push @TABS, { name=>'Authorize.Net', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=AUTHORIZENET' };
	}
elsif ($webdbref->{'cc_processor'} eq 'VERISIGN') {
	push @TABS, { name=>'Paypal Payflow Pro', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=VERISIGN' };
	}
elsif ($webdbref->{'cc_processor'} eq 'LINKPOINT') {
	push @TABS, { name=>'Cardservice Linkpoint', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=LINKPOINT' };
	}
elsif ($webdbref->{'cc_processor'} eq 'ECHO') {
	push @TABS, { name=>'ECHO', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=ECHO' };
	}
elsif ($webdbref->{'cc_processor'} eq 'SKIPJACK') {
	push @TABS, { name=>'SkipJack', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=SKIPJACK' };
	}
elsif ($webdbref->{'cc_processor'} eq 'MANUAL') {
	push @TABS, { name=>'Manual CC', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=MANUAL' };
	}
elsif ($webdbref->{'cc_processor'} eq 'NONE') {
	}
elsif ($webdbref->{'cc_processor'} eq 'TESTING') {
	push @TABS, { name=>'Testing Logs', selected=>($TAB eq 'CREDIT')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=CREDIT&ACTION=TESTING' };
	}
else {
	push @TABS, { name=>'Unknown: '.$webdbref->{'cc_processor'} };
	}


push @TABS, { name=>'GoogleCheckout',link=>'/biz/setup/payment/index.cgi?TAB=GOOGLE','target'=>'_top', };
push @TABS, { name=>'Paypal EC',selected=>($TAB eq 'PAYPALEC')?1:0, link=>'/biz/setup/payment/index.cgi?TAB=PAYPALEC','target'=>'_top', };
push @TABS, { name=>'Amazon',selected=>($TAB eq 'AMZPAY')?1:0, link=>'/biz/setup/payment/index.cgi?TAB=AMZPAY','target'=>'_top', };

if ($FLAGS =~ /,EBAY,/) {
#	push @TABS, { name=>'Paypal Legacy',selected=>($TAB eq 'PAYPALIPN')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=PAYPALIPN','target'=>'_top', };
#	push @TABS, { name=>'Special',selected=>($TAB eq 'SPECIAL')?1:0,link=>'/biz/setup/payment/index.cgi?TAB=SPECIAL','target'=>'_top', };
	}


if (index($FLAGS,',API2,')>=0) {
	push @TABS, { name=>'Advanced',link=>'/biz/setup/payment/index.cgi?TAB=ADVANCED','target'=>'_top', };
	}

##End of script: outputting
##Header: 1 = yes  Boolean (bitwise)

if ($TAB eq 'HELP') {
	my $c = '';
	foreach my $tab (@TABS) {
		next if ($tab->{'selected'});
		if ($c ne '') { $c .= " &nbsp; | &nbsp; "; }
		$c .= qq~<a href="$tab->{'link'}">$tab->{'name'}</a>~;
		}	
	$GTOOLS::TAG{'<!-- HELP_LINKS -->'} = $c;
	$template_file = 'help.shtml';
	}

#if ($LU->get('todo.setup')) {
#	require TODO;
#	my $t = TODO->new($USERNAME);	
#	my ($need,$tasks) = $t->setup_tasks('payment',LU=>$LU,webdb=>$webdbref);
#	$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('payment',$tasks);
#   }



&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,
	'title'=>'Payment Processing Configuration',
	'file'=>$template_file,
	'header'=>'1',
	'msgs'=>\@MSGS,
	'help'=>$help,
	'tabs'=>\@TABS,
	'bc'=>\@BC,
	'jquery'=>'1',
	'todo'=>1,
	'js'=>2+4,
	);

exit;

sub build_general {
	my ($webdbref) = @_;

	$GTOOLS::TAG{"<!-- CC_TYPE_VISA_CHECKED -->"}  = "";
	$GTOOLS::TAG{"<!-- CC_TYPE_MC_CHECKED -->"}    = "";
	$GTOOLS::TAG{"<!-- CC_TYPE_AMEX_CHECKED -->"}  = "";
	$GTOOLS::TAG{"<!-- CC_TYPE_NOVUS_CHECKED -->"} = "";
	my @cc_types = split (',', $webdbref->{"cc_types"});
	foreach my $cc (@cc_types) { $GTOOLS::TAG{"<!-- CC_TYPE_" . $cc . "_CHECKED -->"} = "CHECKED"; }

	$GTOOLS::TAG{"<!-- PAY_CREDIT_0_SELECTED -->"}       = "";
	$GTOOLS::TAG{"<!-- PAY_CREDIT_1_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CREDIT_3_SELECTED -->"}    = "";
	$GTOOLS::TAG{"<!-- PAY_CREDIT_7_SELECTED -->"}  = "";
	$GTOOLS::TAG{"<!-- PAY_CREDIT_15_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_CREDIT_" . uc($webdbref->{"pay_credit"}) . "_SELECTED -->"} = "SELECTED";

	$GTOOLS::TAG{"<!-- PAY_ECHECK_0_SELECTED -->"}       = "";
	$GTOOLS::TAG{"<!-- PAY_ECHECK_1_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_ECHECK_3_SELECTED -->"}    = "";
	$GTOOLS::TAG{"<!-- PAY_ECHECK_7_SELECTED -->"}  = "";
	$GTOOLS::TAG{"<!-- PAY_ECHECK_15_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- PAY_ECHECK_" . uc($webdbref->{"pay_echeck"}) . "_SELECTED -->"} = "SELECTED";

	foreach my $row (@ZPAY::AVS_REVIEW_STATUS) {
		my ($selected) = ($webdbref->{'cc_avs_review'} eq $row->[0])?'selected':'';
		$GTOOLS::TAG{'<!-- CC_AVS_REVIEW -->'} .= "<option $selected value=\"$row->[0]\">$row->[1]</option>\n";
		}

	foreach my $row (@ZPAY::CVV_REVIEW_STATUS) {
		my ($selected) = ($webdbref->{'cc_cvv_review'} eq $row->[0])?'selected':'';
		$GTOOLS::TAG{'<!-- CC_CVV_REVIEW -->'} .= "<option $selected value=\"$row->[0]\">$row->[1]</option>\n";
		}

#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_NONE_SELECTED -->"}    = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_NONE_SELECTED -->"}    = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_PARTIAL_SELECTED -->"} = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_FULL_SELECTED -->"}    = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_NOFRAUD_SELECTED -->"} = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_REQUIRE_" . $webdbref->{"cc_avs_require"} . "_SELECTED -->"} = "SELECTED";

#	$GTOOLS::TAG{"<!-- CC_AVS_FAIL_CODE_105_SELECTED -->"} = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_FAIL_CODE_205_SELECTED -->"}  = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_FAIL_CODE_402_SELECTED -->"}  = "";
#	$GTOOLS::TAG{"<!-- CC_AVS_FAIL_CODE_" . $webdbref->{"cc_avs_fail_code"} . "_SELECTED -->"} = "SELECTED";
#
#	$GTOOLS::TAG{"<!-- CC_REPORT_VOICE_FAIL_ALWAYS_SELECTED -->"} = "";
#	$GTOOLS::TAG{"<!-- CC_REPORT_VOICE_FAIL_NEVER_SELECTED -->"}  = "";
#	$GTOOLS::TAG{"<!-- CC_REPORT_VOICE_FAIL_" . $webdbref->{"cc_report_voice_fail"} . "_SELECTED -->"} = "SELECTED";

#	$GTOOLS::TAG{"<!-- CC_VOICE_FAIL_CODE_103_SELECTED -->"} = "";
#	$GTOOLS::TAG{"<!-- CC_VOICE_FAIL_CODE_202_SELECTED -->"}  = "";
#	$GTOOLS::TAG{"<!-- CC_VOICE_FAIL_CODE_" . $webdbref->{"cc_voice_fail_code"} . "_SELECTED -->"} = "SELECTED";


	$GTOOLS::TAG{"<!-- CC_INSTANT_CAPTURE__SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- CC_INSTANT_CAPTURE_ALWAYS_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- CC_INSTANT_CAPTURE_NEVER_SELECTED -->"}  = "";
	$GTOOLS::TAG{"<!-- CC_INSTANT_CAPTURE_NOAUTH_DELAY_SELECTED -->"}  = "";
	$GTOOLS::TAG{"<!-- CC_INSTANT_CAPTURE_" . $webdbref->{"cc_instant_capture"} . "_SELECTED -->"} = "SELECTED";
	

	$GTOOLS::TAG{"<!-- ECHECK_SUCCESS_CODE_120_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- ECHECK_SUCCESS_CODE_006_SELECTED -->"} = "";
	$GTOOLS::TAG{"<!-- ECHECK_SUCCESS_CODE_" . $webdbref->{"echeck_success_code"} . "_SELECTED -->"} = "SELECTED";

	$GTOOLS::TAG{"<!-- ECHECK_PAYABLE_TO -->"} = &ZOOVY::incode($webdbref->{"echeck_payable_to"});

	my $feesref = &ZTOOLKIT::parseparams($webdbref->{'cc_fees'});
	$GTOOLS::TAG{'<!-- CC_TRANSFEE -->'} = $feesref->{'CC_TRANSFEE'};
	$GTOOLS::TAG{'<!-- CC_DISCRATE -->'} = $feesref->{'CC_DISCRATE'};
	$GTOOLS::TAG{'<!-- VISA_TRANSFEE -->'} = $feesref->{'VISA_TRANSFEE'};
	$GTOOLS::TAG{'<!-- VISA_DISCRATE -->'} = $feesref->{'VISA_DISCRATE'};
	$GTOOLS::TAG{'<!-- MC_TRANSFEE -->'} = $feesref->{'MC_TRANSFEE'};
	$GTOOLS::TAG{'<!-- MC_DISCRATE -->'} = $feesref->{'MC_DISCRATE'};
	$GTOOLS::TAG{'<!-- AMEX_TRANSFEE -->'} = $feesref->{'AMEX_TRANSFEE'};
	$GTOOLS::TAG{'<!-- AMEX_DISCRATE -->'} = $feesref->{'AMEX_DISCRATE'};
	$GTOOLS::TAG{'<!-- NOVUS_TRANSFEE -->'} = $feesref->{'NOVUS_TRANSFEE'};
	$GTOOLS::TAG{'<!-- NOVUS_DISCRATE -->'} = $feesref->{'NOVUS_DISCRATE'};
	

} ## end sub build_general

## Strips off the request variables out of a webdb hash.
## Most methods don't use much of them, so this keeps the webdb a lot cleaner
sub nuke_requests
{
	my ($webdbref) = @_;
	delete $webdbref->{'echeck_request_bank_state'};
	delete $webdbref->{'echeck_request_acct_name'};
	delete $webdbref->{'echeck_request_check_number'};
	delete $webdbref->{'echeck_request_business_account'};
	delete $webdbref->{'echeck_request_tax_id'};
	delete $webdbref->{'echeck_request_drivers_license_number'};
	delete $webdbref->{'echeck_request_drivers_license_state'};
	delete $webdbref->{'echeck_request_drivers_license_dob'};
	delete $webdbref->{'echeck_notice'};
	delete $webdbref->{'cc_request_business_account'};
	delete $webdbref->{'cc_request_tax_id'};
	delete $webdbref->{'cc_request_drivers_license_number'};
	delete $webdbref->{'cc_request_drivers_license_state'};
	delete $webdbref->{'cc_request_drivers_license_dob'};
	delete $webdbref->{'cc_notice'};
	delete $webdbref->{'cc_fees'};
}

	
