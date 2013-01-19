#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use JSON::XS;
use Data::Dumper;
use GTOOLS;
require SITE;
require ZOOVY;
require DBINFO;
require ORDER;
require CUSTOMER;
require INVENTORY;
require ZTOOLKIT;
#require CART::VIEW;
#require ORDER::VIEW;
require CART2;
require CART2::VIEW;
require SITE;
require ZWEBSITE;
require TOXML;
use strict;

&ZOOVY::init();

my @MSGS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $CMD = uc($ZOOVY::cgiv->{"CMD"});
if (index($CMD,'?')>=0) {
	($CMD,my $PARAMS) = split(/\?/,$CMD,2);
	my $ref = &ZTOOLKIT::parseparams($PARAMS);
	foreach my $k (keys %{$ref}) { $ZOOVY::cgiv->{$k} = $ref->{$k}; }
	print STDERR Dumper($ref);
	}

my $ID = $ZOOVY::cgiv->{'ID'};
if ($ID eq '') { $ID = $ZOOVY::cgiv->{'order'}; }
if ($ID eq '') { $ID = $ZOOVY::cgiv->{'orderid'}; }
if ($ID eq '') { $ID = $ZOOVY::cgiv->{'OID'}; }

$GTOOLS::TAG{"<!-- ID -->"} = $ID;
$GTOOLS::TAG{"<!-- OID -->"} = $ID;

my ($O2) = CART2->new_from_oid($USERNAME,$ID);
my ($SITE) = SITE->new($O2->username(),'PRT'=>$O2->prt(),'PROFILE'=>$O2->profile(),'DOMAIN'=>$O2->if_our_sdomain());

my ($utf8_encoded_json_text) = JSON::XS->new->utf8->allow_blessed(1)->convert_blessed(1)->pretty(1)->encode( $O2->jsonify() );
$GTOOLS::TAG{'<!-- JSON -->'} = $utf8_encoded_json_text;

my @BC = ();
push @BC, { 'link'=>'/biz/orders/index.cgi', name=>'Orders' };
push @BC, { 'link'=>'/biz/orders/index.cgi?VERB=SHOW:'.$O2->pool(), name=>sprintf("[%s]",uc($O2->pool())) };
push @BC, { 'link'=>'/biz/orders/view.cgi?ID='.$O2->oid(), name=>sprintf("Order %s",$O2->oid()) };

my $webdb = $SITE->webdb();
my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$O2->prt());
my $NS = $O2->in_get('our/profile');
if (not defined $NS) { $NS = $prtinfo->{'profile'}; }
if ($NS eq '') { $NS = 'DEFAULT'; }
my $merchantref = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);
$GTOOLS::TAG{'<!-- NS -->'} = $NS;
$GTOOLS::TAG{'<!-- PRT -->'} = $O2->prt();

#my ($t) = TOXML->new('WRAPPER','default');
#$t->initConfig($SITE);
#$SITE->URLENGINE()->set('secure'=>1);

##
## passed: cgi parameter ID=200x-0x-xxxxxx
##

my $a = "";   # this is used throughout the program as scratch
my $ts = time();
my $template_file = '';

my $cname = &ZTOOLKIT::htmlstrip($merchantref->{"zoovy:company_name"});
if (length($cname)<1) { $cname = $USERNAME; }
$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = $cname;

if ($ID eq '') { 
	print "Content-type: text/plain\n\n";
	print "<html><b>This form requires an ORDER ID be passed to it!</b></html>";
	exit;
	}

my $CUSTOMER = undef;

if ($FLAGS =~ /,CRM,/) {
	require CUSTOMER;
	($CUSTOMER) = CUSTOMER->new($USERNAME,PRT=>$O2->prt(),EMAIL=>$O2->in_get('bill/email'),INIT=>33);
	if ($CUSTOMER->{'_CID'} == -1) { $CUSTOMER = undef; }
	if ($CUSTOMER->{'_CID'} == 0) { $CUSTOMER = undef; }
	}


my $status = $O2->pool();
my $created = $O2->in_get('our/order_ts');
$GTOOLS::TAG{'<!-- CREATED -->'} = &ZTOOLKIT::pretty_date($created);




#########################################################################################################
##
## TRACKING
##

if ($CMD eq 'VERB-EMAIL-SEND') {
	my $OID = $O2->oid();
	my $PROFILE = $O2->in_get('our/profile');
	if ($PROFILE eq '') { $PROFILE = 'DEFAULT'; }

	my $email = $O2->in_get('bill/email');
	push @MSGS, "SUCCESS|+Emailing $email for $OID";

	require SITE::EMAILS;
	my $messageid = 'BLANK';
	my $error = '';
	my $MSGSUBJECT = $ZOOVY::cgiv->{'emailSubject'};
	my $MSGBODY = $ZOOVY::cgiv->{'emailBody'};

	print STDERR "BODY:$MSGBODY\n";

	my ($SREF) = SITE->new($USERNAME,'PRT'=>$O2->prt(),'NS'=>$PROFILE);
	my ($se) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SREF); # NS=>$PROFILE,PRT=>$PRT,GLOBALS=>1);
	
	my ($ERR) = $se->send('ORDER.NOTE','*SITE'=>$SREF,'*CART2'=>$O2,MSGBODY=>$MSGBODY,MSGSUBJECT=>$MSGSUBJECT);		

	if ($ERR==0) { 
		}
	elsif (defined $SITE::EMAILS::ERRORS{$ERR}) {
		$error = $SITE::EMAILS::ERRORS{$ERR}; 
		push @MSGS, "ERROR|+$error";
		}
	else {
		$error = "UNDEFINED EMAIL ERROR CODE #$ERR";
		push @MSGS, "ERROR|+$error";
		}
	$se = undef;
	$CMD = '';	
	}


if ($CMD eq 'VERB-TRACKING-VOID') {
	$CMD = '';
	my $void_track = $ZOOVY::cgiv->{'track'};	
	my $changed = 0;
	foreach my $trkref (@{$O2->tracking()}) {
		next if (not defined $trkref);
		if ($trkref->{'track'} eq $void_track) {
			$trkref->{'void'} = time();
			$changed++;
			}
		}
	if ($changed) { $O2->order_save(); }
	}

if ($CMD eq 'VERB-TRACKING-ADD') {
	my $method = $ZOOVY::cgiv->{'method'};
	my $value = $ZOOVY::cgiv->{'value'};	## tracking number
	my $actualwt = $ZOOVY::cgiv->{'actualwt'};
	my $notes = $ZOOVY::cgiv->{'notes'};
	my $cost = $ZOOVY::cgiv->{'cost'};
	$cost =~ s/\$//g;		## take out any dollar signs
	$cost = sprintf("%.2f",$cost); ## adjust to 2 decimal places
	$value =~ s/[^\w-]+//g;
	my $changed = 0;
	if ($value ne '') {
		$O2->set_tracking($method,$value,$notes,$cost,$actualwt);
		$changed++;
		}

	if ($changed) {
		$O2->order_save();
		}
	push @MSGS, "SUCCESS|Order Tracking ID's have been added/updated!";
	
	$CMD = '';
	}

my $c = '';
foreach my $trkref (@{$O2->tracking()}) {
	my ($method, $value) = ($trkref->{'carrier'},$trkref->{'track'});
	my $notes = $trkref->{'notes'};
	my $cost = $trkref->{'cost'};
	my $actualwt = $trkref->{'actualwt'};

	## attribs: created, cost, carrier, actualwt, track, notes
	# print STDERR Dumper($trkref);

	next if ($value eq '');
	## skip deleted/hidden/voided tracking numbers
	## 	we're keeping all numbers per uPick terms/conditions

	if ($trkref->{'void'} > 0) {
		$c .= "<tr style='text-decoration: line-through'>";
		$c .= "<td>&nbsp;</td>";
		$c .= "<td><b>VOIDED</b></td>";
		}
	else {
		$c .= "<tr>";
		$c .= "<td>&nbsp;</td>";
		$c .= qq~<td>
<button onClick="
	jQuery('#CMD').val('VERB-TRACKING-VOID?track=$trkref->{'track'}'); 
	jQuery('#dialogTracking').dialog('close');
	myModal.dialog('close');
	jQuery('#viewFrm').submit();
	return false;
" class=\"minibutton\">VOID</button>
</td>~;
		}

	my $shipref = &ZSHIP::shipinfo($trkref->{'carrier'});

	$c .= "<td>$shipref->{'method'}</td>";
	$c .= "<td>$trkref->{'track'}</td>";
	if ($trkref->{'track'} eq '') {
		$c .= "<td bgcolor='FFFFFF'>Not Provided</td>";
		}
	else {
		my ($link,$text) = &ZSHIP::trackinglink($shipref,$trkref->{'track'});
		$c .= "<td bgcolor='FFFFFF'><a target=\"_blank\" href=\"$link\">$text</a></td>";
		}		
	$c .= "</tr>";

	if ($actualwt || $cost || $notes) {
		$c .= "<tr><td>&nbsp;</td><td>&nbsp;</td><td colspan='4'>";
		if ($cost) { $c .= "Shipping Cost: $cost<br>"; }
		if ($actualwt) { $c .= "Actual Weight: ".$actualwt."<br>"; }
		if ($notes) { $c .= "Shipping Notes: ".$notes."<br>"; }
		$c .= "</td></tr>";
		}

	}
if ($c eq '') {
	$c = "<tr bgcolor='white'><td></td><td colspan='3'><i>Sorry, no tracking information is available.</td></tr>";
	}
$GTOOLS::TAG{"<!-- TRACKING -->"} = $c;




#######################################################################################
##
## NOTES
##

if ($CMD eq 'VERB-NOTES-SET') {
	$O2->in_set('want/order_notes',$ZOOVY::cgiv->{'want/order_notes'});
	$O2->in_set('flow/private_notes',$ZOOVY::cgiv->{'flow/private_notes'});
	$O2->order_save();
	$CMD = '';
	}
$GTOOLS::TAG{'<!-- ORDER_NOTES -->'} = &ZOOVY::incode($O2->in_get('want/order_notes'));
$GTOOLS::TAG{'<!-- PRIVATE_NOTES -->'} = &ZOOVY::incode($O2->in_get('flow/private_notes'));

#
#	$CMD = '';
#	if ($ZOOVY::cgiv->{'NOTE'} ne '') {
#		$CUSTOMER->save_note($LUSERNAME,$ZOOVY::cgiv->{'NOTE'});
#		}
#	}


##########################################################################################
##
## NUKE ORDER
##
#if ($CMD eq 'DELETE-CONFIRMED') {
#	$ID = $ZOOVY::cgiv->{'ID'};
#	print STDERR "Deleting ID: $USERNAME $ID\n";
#	$LU->log("ORDER.DELETE","Removed order $ID","WARN");
#
# 	my ($FAILED) = &CART2::nuke_order($USERNAME,$ID);
#	if ($FAILED) {
#		push @MSGS, "ERROR|Sorry, cannot remove order.";
#		$CMD = '';
#		}
#	else {
#		print "Location: /biz/orders/recent.shtml?_NUKE_FAILED=$FAILED\n\n";
#		exit;
#		}	
#	}
#if ($CMD eq "DELETE") {
#	$template_file = "delete-confirm.shtml";
#	my $TAXRATE = $O2->in_get("our/tax_rate");
#	my $SHIPMETHOD = $O2->in_get("sum/shp_method");
#	my $SHIPPING = $O2->in_get("sum/shp_total");
#	#if ($O2->lock()) {
#	#	push @MSGS, "WARN|This order cannot be removed because it has been synced to one or more external systems and/or is locked.";
#	#	}
#	($a) = &CART2::VIEW::as_html($O2,'INVOICE',{},$SITE);
#	if (length($a)<1) { $a .= "No contents found!"; }
#	$GTOOLS::TAG{"<!-- DISPLAY_CONTENTS -->"} = "$a";
#	}



	if ($O2->in_get('flow/cancelled_ts')>0) {
		$GTOOLS::TAG{'<!-- PAID -->'} = '<font color="red">** CANCELLED **</font>';		
		}
	elsif ($O2->payment_status() =~ /^0/) {
		$GTOOLS::TAG{'<!-- PAID -->'} = "PAID ".&ZTOOLKIT::pretty_date($O2->in_get('flow/paid_ts'));	
		$GTOOLS::TAG{'<!-- PAYMENT_METHOD -->'} = $O2->payment_method();
		}
	elsif (($O2->payment_status() =~ /^4/) && ($O2->payment_status() ne '499')) {
		$GTOOLS::TAG{'<!-- PAID -->'} = "REVIEW ".&ZTOOLKIT::pretty_date($O2->in_get('flow/paid_ts'));	
		$GTOOLS::TAG{'<!-- PAYMENT_METHOD -->'} = $O2->payment_method();
		}
	else {
		$GTOOLS::TAG{'<!-- PAID -->'} = '<font color="red">** UNPAID **</font>';
		}

	$GTOOLS::TAG{"<!-- SHIP_NAME -->"} = 
		$O2->in_get("ship/firstname")." ".
		($O2->in_get("ship/middlename")?$O2->in_get("ship/middlename").' ':'').
		$O2->in_get("ship/lastname");	
   $GTOOLS::TAG{"<!-- SHIP_COMPANY -->"} = ($O2->in_get("ship/company"))?($O2->in_get("ship/company")."<br>"):"";
   $GTOOLS::TAG{"<!-- SHIP_ADDRESS1 -->"} = ($O2->in_get("ship/address1"))?($O2->in_get("ship/address1")."<br>"):"";
   $GTOOLS::TAG{"<!-- SHIP_ADDRESS2 -->"} = ($O2->in_get("ship/address2"))?($O2->in_get("ship/address2")."<br>"):"";
   $GTOOLS::TAG{"<!-- SHIP_CITY -->"} = ($O2->in_get("ship/city"))?($O2->in_get("ship/city").", "):"";
   
   if ($O2->is_domestic('ship')) {
		$GTOOLS::TAG{"<!-- SHIP_STATE -->"} = ($O2->in_get("ship/region"))?($O2->in_get("ship/region")." "):"";
		$GTOOLS::TAG{"<!-- SHIP_ZIP -->"} = ($O2->in_get("ship/postal"))?($O2->in_get("ship/postal")." "):""; 
		}
	else {
		$GTOOLS::TAG{"<!-- SHIP_REGION -->"} = ""; 
		$GTOOLS::TAG{'<!-- SHIP_ZIP -->'} = $O2->in_get('ship/region').', '.$O2->in_get("ship/postal").'<br>'.$O2->in_get('ship/countrycode'); 
		}

   $GTOOLS::TAG{"<!-- SHIP_PHONE -->"} = ($O2->in_get("ship/phone"))?($O2->in_get("ship/phone")."<br>"):"";
   $GTOOLS::TAG{"<!-- SHIP_EMAIL -->"} = ($O2->in_get("ship/email"));	

	# $GTOOLS::TAG{"<!-- BILL_NAME -->"} = ($O2->in_get("bill/fullname"))?($O2->in_get("bill/fullname")):($O2->in_get("bill/firstname")." ".$O2->in_get("bill/lastname"));
	$GTOOLS::TAG{"<!-- BILL_NAME -->"} = 
		$O2->in_get("bill/firstname")." ".
		($O2->in_get("bill/middlename")?$O2->in_get("bill/middlename").' ':'').
		$O2->in_get("bill/lastname");	
   $GTOOLS::TAG{"<!-- BILL_COMPANY -->"} = ($O2->in_get("bill/company"))?($O2->in_get("bill/company")."<br>"):"";
   $GTOOLS::TAG{"<!-- BILL_ADDRESS1 -->"} = ($O2->in_get("bill/address1"))?($O2->in_get("bill/address1")."<br>"):"";
   $GTOOLS::TAG{"<!-- BILL_ADDRESS2 -->"} = ($O2->in_get("bill/address2"))?($O2->in_get("bill/address2")."<br>"):"";
   $GTOOLS::TAG{"<!-- BILL_CITY -->"} = ($O2->in_get("bill/city"))?($O2->in_get("bill/city").", "):"";
   

   if ($O2->is_domestic('bill')) {
		$GTOOLS::TAG{"<!-- BILL_STATE -->"} = ($O2->in_get("bill/region"))?($O2->in_get("bill/region")." "):"";
		$GTOOLS::TAG{"<!-- BILL_ZIP -->"} = ($O2->in_get("bill/postal"))?($O2->in_get("bill/postal")." "):""; 
		}
	else {
		$GTOOLS::TAG{"<!-- BILL_STATE -->"} = ""; 
		$GTOOLS::TAG{'<!-- BILL_ZIP -->'} = $O2->in_get('bill/region').', '.$O2->in_get("bill/postal").'<br>'.$O2->in_get('bill/countrycode'); 
		}

   $GTOOLS::TAG{"<!-- BILL_PHONE -->"} = ($O2->in_get("bill/phone"))?($O2->in_get("bill/phone")."<br>"):"";
   $GTOOLS::TAG{"<!-- BILL_EMAIL -->"} = ($O2->in_get("bill/email"));	

	my $CID = 0;
	if ($O2->customerid()) {
		$CID = $O2->customerid();
		}
	else {
		($CID) = &CUSTOMER::customer_exists($USERNAME,$O2->in_get('bill/email'),$O2->prt());
		}

	if ($O2->in_get('bill/email') eq '') {
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = '';
		}
	elsif ($CID == 0) {
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = '';
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = "<a href=\"#\" onClick=\"jQuery('#utilitiesContent').empty(); navigateTo('/biz/manage/customer/index.cgi?VERB=CREATE&EMAIL=".$O2->in_get('bill/email')."&ORDER=".$O2->oid()."&PRT=".$O2->prt()."\');\">Create Customer Account</a>";		
		}
	elsif ($CID != $O2->customerid()) {
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = "<a href=\"#\" onClick=\"jQuery('#utilitiesContent').empty(); navigateTo('/biz/manage/customer/index.cgi?VERB=SEARCH-NOW&scope=CID&searchfor=$CID&link=".$O2->oid()."\');\">Link Customer Account</a>";		
		}
	elsif ($CID) {
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = "<a href=\"#\" onClick=\"jQuery('#utilitiesContent').empty(); navigateTo('/biz/manage/customer/index.cgi?VERB=SEARCH-NOW&scope=CID&searchfor=$CID\');\">Edit Customer Account</a>";
		}
	else {
		require ZTOOLKIT;
		my $params = &ZTOOLKIT::buildparams(
			{'VERB'=>'CREATE',
			'EMAIL'=>$O2->in_get("bill/email"),
			'FIRST'=>$O2->in_get("bill/firstname"),
			'LAST'=>$O2->in_get("bill/lastname"),
			'ORDER'=>$ID,
			});
		$GTOOLS::TAG{'<!-- CUSTOMER_EDIT -->'} = "<a href=\"#\" onClick=\"jQuery('#utilitiesContent').empty(); navigateTo('/biz/manage/customer/index.cgi?$params\');\">Create New Customer Account</a>";
		}

	if ($O2->payment_method() eq 'PAYPAL') {
#		$GTOOLS::TAG{'<!-- PAYMENTINFO -->'} = qq~
#		<tr><td><br>Paypal Account: $O2->in_get('our/paypal_acct') &nbsp; &nbsp; Transaction Id: $O2->in_get('our/payment_authorization')</td></tr>
#		~;
		}
	elsif ($O2->payment_method() eq 'GOOGLE') {
		my ($payrec) = @{$O2->payments('tender'=>'GOOGLE')}; 
		$GTOOLS::TAG{'<!-- PAYMENTINFO -->'} = qq~<tr><td><br>Google Order #: $payrec->{'txn'}</td></tr>~;
		}	
	if ($O2->in_get('our/schedule') ne '') {
		$GTOOLS::TAG{'<!-- PAYMENTINFO -->'} .= qq~<tr><td>Schedule: ~.$O2->in_get('our/schedule').qq~</td></tr>~;
		}
	#if ($O2->in_get('flow/sc_orderinfo') ne '') {
	#	$GTOOLS::TAG{'<!-- PAYMENTINFO -->'} .= qq~<tr><td>Supply Chain Order: $O2->in_get(('sc_orderinfo')</td></tr>~;
	#	}
	if ($O2->in_get('flow/cancelled_ts')>0) {
		$GTOOLS::TAG{'<!-- PAYMENTINFO -->'} .= qq~<tr><td colspan=2><font color='red'>Order was cancelled on: ~.&ZTOOLKIT::pretty_date($O2->in_get('flow/cancelled_ts'),1).qq~</td></tr>~;
		}


	$GTOOLS::TAG{'<!-- NOTES --'} = '';
	if ($O2->in_get('want/erefid') ne '') {
		$GTOOLS::TAG{'<!-- NOTES -->'} .= sprintf("<td><td><div class=\"hint\">External Reference: %s</div></td></tr>",$O2->in_get('want/erefid'));
		}
	if ($O2->in_get('want/po_number') ne '') {
		$GTOOLS::TAG{'<!-- NOTES -->'} .= sprintf("<tr><td><div class\"hint\">Purchase Order #: %s</div></td></tr>",$O2->in_get('want/po_number'));
		}

	my $order_notes = '';	
	if ($O2->in_get('want/order_notes') ne '') {
		$order_notes = &ZOOVY::incode($O2->in_get('want/order_notes'));
		$order_notes =~ s/\n/<br>/g;
		$GTOOLS::TAG{'<!-- NOTES -->'} .= "<tr><td><div class=\"hint\"><b>Order Notes:</b> ".$order_notes."</div></td></tr>\n";
		
		}

	if ($O2->in_get('flow/private_notes') ne '') {
		## NOTE: these are not *EVER* printable
		my $private_notes = &ZOOVY::incode($O2->in_get('flow/private_notes'));
		$private_notes =~ s/\n/<br>/g;
		$GTOOLS::TAG{'<!-- NOTES -->'} .= "<tr><td><div class=\"hint\"><b>Private Notes:</b><br>".$private_notes."</div></td></tr>\n";
		}


	require ZWEBSITE;
	require IMGLIB::Lite;
	my $out;

	require ZWEBSITE;
	if ($order_notes ne '') {
		$GTOOLS::TAG{'<!-- ORDERNOTES -->'} = "<center><table width='95%'><tr><Td><b>Order Notes:</b> $order_notes</td></tr></table></center>"; 
		}

	my $logo = $merchantref->{'zoovy:logo_invoice'};
	if ($logo eq '') { 
		## LEGACY
		$logo = $merchantref->{'zoovy:invoice_logo'};
		}
	my ($width,$height) = split(/x/,$merchantref->{'zoovy:logo_invoice_xy'});
	if ($width<=0) { $width = 300; }
	if ($height<=0) { $height = 100; }

	$GTOOLS::TAG{"<!-- COMPANY_LOGO -->"} = &IMGLIB::Lite::url_to_image($USERNAME,$logo,$width,$height,'ffffff');
	$GTOOLS::TAG{'<!-- WIDTH -->'} = $width;
	$GTOOLS::TAG{'<!-- HEIGHT -->'} = $height;

	# my $MERCHREF = &ZOOVY::attrib_handler_ref(&ZOOVY::fetchmerchant($USERNAME));	
	$GTOOLS::TAG{"<!-- COMPANY_ADDRESS1 -->"} = ($merchantref->{"zoovy:address1"})?($merchantref->{"zoovy:address1"}."<br>"):"";
	$GTOOLS::TAG{"<!-- COMPANY_ADDRESS2 -->"} = ($merchantref->{"zoovy:address2"})?($merchantref->{"zoovy:address2"}."<br>"):"";
	$GTOOLS::TAG{"<!-- COMPANY_CITY -->"} = ($merchantref->{"zoovy:city"})?($merchantref->{"zoovy:city"}.", "):"";
	$GTOOLS::TAG{"<!-- COMPANY_STATE -->"} = ($merchantref->{"zoovy:state"})?($merchantref->{"zoovy:state"}." "):"";
	$GTOOLS::TAG{"<!-- COMPANY_ZIP -->"} = ($merchantref->{"zoovy:zip"})?($merchantref->{"zoovy:zip"}." "):"";
	$GTOOLS::TAG{"<!-- COMPANY_SUPPORT_PHONE -->"} = ($merchantref->{"zoovy:support_phone"});
	$GTOOLS::TAG{"<!-- COMPANY_SUPPORT_EMAIL -->"} = ($merchantref->{"zoovy:support_email"});	
	$GTOOLS::TAG{"<!-- COMPANY_URL -->"} = ($merchantref->{"zoovy:website_url"});

	my $TAXRATE = $O2->in_get("our/tax_rate");
	my $SHIPPING = $O2->in_get("sum/shp_total");
	
	#if ($CMD eq 'PACKSLIP') {
	#	$out = &build_packslip($USERNAME,$O2);
	#	$template_file = 'view-packslip.shtml';
	#	}
	#elsif ($CMD eq 'INVOICE') {		
	#	($out) = &CART2::VIEW::as_html($O2,'PRINT_INVOICE',{},$SITE);
	#	$template_file = "view-invoice.shtml";
	#	}

	if (length($out)<1) { $out .= "<br><font color='red'>No contents found! [CMD:$CMD]</font>"; }
	if ($O2->in_get('cart/refer') ne '') { $out .= "<br>META: ".$O2->in_get('cart/refer')."<br>\n"; }

	$GTOOLS::TAG{"<!-- DISPLAY_CONTENTS -->"} = "$out";
	($a) = &CART2::VIEW::as_html($O2,'INVOICE',{},$SITE);

	my $ts = time();
	my $ID = $ZOOVY::cgiv->{'ID'};


	my $zom_warning = '';

	my $email = $O2->in_get('bill/email');
	my $phone = $O2->in_get('bill/phone');

	my $DELETE_ORDER_BUTTON = '';
	if ($O2->pool() eq 'DELETED') {
		$DELETE_ORDER_BUTTON = qq~<input type='button' class="button" onClick=\"navigateTo('view.cgi?CMD=DELETE&ID=$ID&ts=$ts');\" value=\"  Delete Order \">~;
		}

	my ($tickets) = $O2->tickets();
	if (scalar(@{$tickets})>0) {
		my $c = '';
		$c .= qq~<table class="zoovytable" width="100%">~;
		$c .= qq~
	<tr class="zoovytableheader">
		<td colspan=4>Open Tickets</td>
	</tr>
	<tr class="zoovysub1header">
		<td>Ticket</td>	
		<td>Status</td>
		<td>Opened</td>
		<td>Closed</td>
	</tr>
	~;
		foreach my $ticketref (@{$tickets}) {
			$c .= "<tr>";
			$c .= sprintf("<td><a href=\"/biz/crm/index.cgi?VERB=EXEC-SEARCH&ticket=%s\">%s</a></td>",$ticketref->{'TKTCODE'},$ticketref->{'TKTCODE'});
			$c .= sprintf("<td>%s</td>",$ticketref->{'STATUS'});
			$c .= sprintf("<td>%s</td>",&ZTOOLKIT::pretty_date($ticketref->{'CREATED_GMT'},1));
			if ($ticketref->{'CLOSED_GMT'}==0) {
				$c .= "<td>OPEN</td>";
				}
			else {
				$c .= sprintf("<td>%s</td>",&ZTOOLKIT::pretty_date($ticketref->{'CLOSED_GMT'},1));
				}
			$c .= "</tr>";
			}
		$c .= qq~</table>~;	
		$GTOOLS::TAG{'<!-- TICKETS -->'} = $c;
		}

	if (length($a)<1) { $a .= "No contents found! [CMD:$CMD]"; }
	if ($O2->in_get('cart/refer') ne '') { $a = "META: ".$O2->in_get('cart/refer')."<br>\n$a"; }
	if ($O2->in_get('our/sdomain') ne '') { $a = "CHECKOUT DOMAIN: ".$O2->in_get('our/sdomain')."<br>\n$a"; }

	$GTOOLS::TAG{"<!-- DISPLAY_CONTENTS -->"} = "$a";
	$template_file = 'view.shtml';

	if (defined $CUSTOMER) {
		my $NOTES = '';
		
		foreach my $note (@{$CUSTOMER->fetch_notes()}) {
			$NOTES .= "<tr><td valign='top' nowrap>".&ZTOOLKIT::pretty_date($note->{'CREATED_GMT'},-1)." $note->{'LUSER'}</td><td valign='top'>&nbsp; - &nbsp; </td><td valign='top'>$note->{'NOTE'}</td></tr>";
			}

		$GTOOLS::TAG{'<!-- CRMNOTES -->'} = qq~
		<table bgcolor="#000000" cellspacing=1 cellpadding=3 width="100%">
		<tr>
			<td bgcolor='FFFFFF'>
				<b>Customer Notes</b> 
				<i>(Reminder: customer notes are shared across all orders - they are never displayed to the customer.)</i><br>
			<table cellpadding='0' cellspacing='0'>
				$NOTES
			</table>
			<table cellpadding='0' cellspacing='0'><tr><td nowrap>
				Add Note: <input maxlength="80" type="textbox" size="80" name="NOTE"> <input onClick="document.thisFrm.CMD.value='SAVENOTE'; document.thisFrm.submit();" class="button" type="button" value=" Add ">	
			</td></tr></table>
			</td>
		</tr>
		</table>
		~;	
		}

my $HEADJS = '';
#my $HEADJS = q~
#<SCRIPT language="JavaScript">
#<!--
#	function printMe() {
#		popupWin.focus(false);
#		popupWin.print();
#		popupWin.close();
#	}
#	function prWindow(location) {
#		popupWin = window.open(location,"x","status=0,width=640,height=480,directories=0,toolbar=1,menubar=1,resizable=1,scrollbars=2,location=0");
#		popupWin.focus(false);
#		return(false);
#	};
#	function openWindow(location) {
#		popupWin = window.open(location,"x","status=0,width=640,height=480,directories=1,toolbar=1,menubar=1,resizable=1,scrollbars=1,location=0");
#		popupWin.focus(false);
#		return(false);
#	};
#	function openWindowNR(location) {
#		popupWin = window.open(location,"x","status=0,width=640,height=480,directories=1,toolbar=1,menubar=1,resizable=1,scrollbars=1,location=0");
#		popupWin.focus(true);
#	};
#//-->
#</SCRIPT>
#~;


&GTOOLS::output('bc'=>\@BC, msgs=>\@MSGS, headjs=>$HEADJS, file=>$template_file,header=>1);





##
##
## parameters: MODE, USERNAME, ID, TAXRATE, SHIPPRICE, SHIPMETHOD
##	MODE is what type of invoice to print currently only "NORM" is supported
##	ID is the order ID
##	TAXRATE is the tax rate for the other (if applicable) in non-decimal format (10 = %10 tax rate)
##	SHIPPRICE is the price of shipping
##	SHIPMETHOD is the text of the method we are shipping
##
#sub build_packslip {
#	my ($USERNAME,$O2) = @_;
#
#	my $out = "";
#
#	my $SHIPMETHOD = $O2->in_get('sum/shp_method');
#
#	my $BGCOLOR = '3366CC';
#	$out .= "<table cellspacing='0' cellpadding='5' width='100%'><tr>";
#	$out .= "<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: FFFFFF'><b>LOCATION</b></font></td>";
#	$out .= "<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: FFFFFF'><b>SKU</b></font></td>";
#	$out .= "<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: FFFFFF'><b>PRODUCT</b></font></td>";
#	$out .= "<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: FFFFFF'><b><center>&nbsp;&nbsp;QTY&nbsp;&nbsp;</center></b></font></td>";
#	$out .= "</tr>";
#
#
##	my ($qtyref,$resref,$locref) = (undef,undef,undef);
##	my @prods = ();
##	foreach my $p (keys %hash) {
##		if (index($p,'*')>=0) { $p = substr($p,index($p,'*')+1); }
##		push @prods, $p;
##		}
#
#	
#	my @stids = $O2->stuff2()->stids();
#	## take out claim number to get correct inv, loc
#	foreach my $stid (@stids) {
#		if (index($stid,'*')>=0) { $stid = substr($stid,index($stid,'*')+1); }
#		}		
#	my ($qtyref,$resref,$locref) = &INVENTORY::fetch_qty($USERNAME,\@stids,undef);
#
#	my $counter = 0;
#	my ($footer,$x) = ('','');
#	foreach my $item (@{$O2->stuff2()->items()}) {
#		my $stid = $item->{'stid'};
#		next if ($item->{'qty'}==0);
#		
#		my $SKU = $item->{'sku'};
#		if ($SKU =~ /^(.*?)\//) { $SKU = $1; }	# strip off non-inventoriable options
#		
#		if ($counter++ % 2) { $BGCOLOR="FFFFFF"; } else { $BGCOLOR='E0E0E0'; }
#		# my ($price,$qty,$weight,$tax,$description) = split(',',$hash{$key},5); 
#		
#		my $extended = sprintf("\$%.2f",$item->{'price'} * $item->{'qty'});
#		my $weight = $item->{'weight'};
#		$weight =~ s/[^0-9\.\#\-]//g;
#
##  '*options' => {
##																							  'A800' => {
##																											  'value' => 'Polished Brass',
##																											  'v' => '00',
##																											  'prompt' => 'Finish',
##																											  'modifier' => ''
##																											},
##																							  'AB07' => {
##																											  'value' => 'With Override Key',
##																											  'v' => '07',
##																											  'prompt' => 'Key Override Options',
##																											  'modifier' => 'w=|p=+10'
##																											}
##																							},
#		my $description = $item->{'prod_name'};
#		if (defined $item->{'*options'}) {
#			$description .= "<br><table bgcolor='$BGCOLOR'>";
#			foreach my $set (keys %{$item->{'*options'}}) {
#				my $pog = $item->{'*options'}->{$set};
#				$description .= sprintf(qq~<tr>
#	<td><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>&nbsp;</font></td>
#	<td valign=top><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>%s</font></td>
#	<td valign=top><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>%s</font></td></tr>~
#,#$pog->{'prompt'},$pog->{'value'});
#				}
#			$description .= "</table>";
#			}
#		my $qty = $item->{'qty'};
#
#		$x = "<tr>";
#
#		my $pullsku = $SKU;
#		if (index($pullsku,'*')>=0) { $pullsku = substr($pullsku,index($pullsku,'*')+1); }
#		$x .= "<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>$locref->{$pullsku}</font></td>";
#
#		$x .= qq~
#<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>$SKU</font></td>
#<td bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'>$description</font></td>
#<td nowrap bgcolor='$BGCOLOR'><font style='font-family: sans-serif, helvetica, arial; font-size: 8pt; color: #000000'><center>$qty</center></font></td>
#~;
#		$x .= "</tr>";
#
#		$out .= $x;
#		}
#	$out .= $footer;
#
#	$out .= "<tr><td colspan='3' align='right' bgcolor='FFFFFF'><font style='font-family: sans-serif, helvetica, arial; font-size: 10pt; color: #3366CC'>Shipping: <B>$SHIPMETHOD</b></font></td></tr>\n";
#
#	$BGCOLOR = '33333';
#
#
#
#	$out .= "</table>";
#	return($out);
#}
#
#undef $SITE::CONFIG;


