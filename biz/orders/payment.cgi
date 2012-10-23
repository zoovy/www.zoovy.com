#!/usr/bin/perl -w

no warnings 'once'; # Keep perl -w from whining about variables used only once

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZPAY;
require ZWEBSITE;
require ZTOOLKIT;
require GIFTCARD;
require CART2;
use Data::Dumper;
use strict;

&DBINFO::db_zoovy_connect();


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $ID = $ZOOVY::cgiv->{'ID'};
my $VERB = $ZOOVY::cgiv->{'VERB'};

if ($ID eq '') { print "Content-type: text/plain\n\nSorry you must pass an order id to use this program.\n"; exit; }
$GTOOLS::TAG{'<!-- TS -->'} = time();
$GTOOLS::TAG{'<!-- ID -->'} = $ID;


my $ERROR = undef;
my @MSGS = ();

# this sometimes had the wrong values.
#my ($o,$err) = ORDER->new($USERNAME,$ID,new=>0);
my ($O2) = CART2->new_from_oid($USERNAME,$ID);

#if ($err) {
#	$ERROR = "Order:$ID error loading $err";
#	$VERB = '';
#	}

my ($C) = undef;
if (not $ERROR) {
	## in order for customer functions to work customer_id must be set in the order!
	if ($O2->customerid()>0) {
		($C) = CUSTOMER->new($USERNAME,'PRT'=>$O2->prt(),'CREATE'=>0,'CID'=>$O2->customerid());
		}
	}


if ($VERB =~ /^(CAPTURE|RETRY|ALLOW-PAYMENT|SET-PAID|REFUND|VOID|OVERRIDE|MARKETPLACE-REFUND|MARKETPLACE-VOID)\:(.*?)$/) {
	($VERB,my $TXNUUID) = ($1,$2);
	my $payrec = $O2->payment_by_uuid($TXNUUID);
	if (not defined $payrec) {
		$ERROR = "Unable to lookup TXN $TXNUUID";
		}
	elsif ($VERB eq 'MARKETPLACE-VOID') {
		my ($reason) = $ZOOVY::cgiv->{"$TXNUUID.marketplace-void.note"};
		$payrec->{'voided'} = time();
		$payrec->{'note'} = $reason;
		my ($newpayrec) = $O2->add_payment($payrec->{'tender'},$payrec->{'amt'},
			'puuid'=>$payrec->{'uuid'},ps=>619,note=>$reason,'luser'=>$LUSERNAME);
		# $O2->order_save();
		}
	elsif ($VERB eq 'MARKETPLACE-REFUND') {
		my ($amt) = $ZOOVY::cgiv->{"$TXNUUID.marketplace-refund.amt"};
		my ($reason) = $ZOOVY::cgiv->{"$TXNUUID.marketplace-refund.note"};
		if (not &ZTOOLKIT::isdecnum($amt)) {
			$ERROR = "Sorry but refund amount: $amt is not valid";
			}
		elsif ($amt<=0) {
			$ERROR = "Sorry but refund amount: $amt must be a positive decimal number.";
			}
		else {
			my ($newpayrec) = $O2->add_payment($payrec->{'tender'},$amt,
				'puuid'=>$payrec->{'uuid'},ps=>319,note=>$reason);
			# $O2->order_save();
			}
		}
	elsif ($VERB eq 'RETRY') {
		$O2->process_payment('INIT',$payrec,'luser'=>$LUSERNAME);		
		# $O2->order_save();
		}
	elsif ($VERB eq 'CAPTURE') {
		my ($amt) = $ZOOVY::cgiv->{"$TXNUUID.capture.amt"};
		if (not &ZTOOLKIT::isdecnum($amt)) {
			$ERROR = "Sorry but capture amount: $amt is not valid";
			}
		elsif ($amt<=0) {
			$ERROR = "Sorry but capture amount: $amt must be a positive decimal number.";
			}
		else {
			$O2->process_payment('CAPTURE',$payrec,amt=>$amt,'luser'=>$LUSERNAME);
			}
		}
	elsif ($VERB eq 'OVERRIDE') {
		my $ps = $ZOOVY::cgiv->{"$TXNUUID.override.ps"};
		my $wasps = $payrec->{'ps'};
		if ($ps eq '') {
			$ERROR = "You must specify a payment status for transaction #$TXNUUID";
			}
		elsif (not defined $ZPAY::PAYMENT_STATUS{$ps}) {
			$ERROR = "Payment status [$ps] is not a valid payment status.";
			}
		elsif ($wasps ne $ps) {
			## update the payment status
			$payrec->{'ps'} = $ps;
			$payrec->{'note'} = $ZOOVY::cgiv->{"$TXNUUID.override.note"};
			$O2->add_history("Override payment status to $ps (was: '$ps') for txn:$TXNUUID",undef,2+8,$LUSERNAME);
			}
		# $O2->order_save();
		}
	elsif ($VERB eq 'SET-PAID') {
		if (not &ZTOOLKIT::isdecnum($payrec->{'amt'})) {
			$ERROR = "Sorry but payment amount: $payrec->{'amt'} is not valid";
			}
		elsif ($payrec->{'amt'}<=0) {
			$ERROR = "Sorry but payment amount: $payrec->{'amt'} must be a positive decimal number.";
			}
		else {
			$payrec->{'ps'} = '000';
			$payrec->{'amt'} = $ZOOVY::cgiv->{"$TXNUUID.set-paid.amt"};
			$payrec->{'note'} = $ZOOVY::cgiv->{"$TXNUUID.set-paid.note"};
			#$O2->sync_action('payment',"$VERB/$TXNUUID");
			#$O2->order_save();
			}
		}
	elsif ($VERB eq 'ALLOW-PAYMENT') {
		## this converts and old 4xx directly to it's 0xx counterpart, unless it's a 499 then it goes to 199
		if ($payrec->{'ps'} eq '499') {
			$payrec->{'ps'} = 199; 
			}
		else {
			$payrec->{'ps'} = '0'.substr($payrec->{'ps'},-2);
			}
		$payrec->{'note'} = $ZOOVY::cgiv->{"$TXNUUID.set-paid.note"};
		$O2->add_history("Set $payrec->{'uuid'} as allowed",undef,2+8);
		#$O2->sync_action('payment',"$VERB/$TXNUUID");
		#$O2->order_save();
		}
	elsif ( 
		(($VERB eq 'REFUND') || ($VERB eq 'CREDIT')) && 
		($payrec->{'tender'} =~ /^(CASH|CHECK|PO)$/)) {
		my ($amt) = $ZOOVY::cgiv->{"$TXNUUID.refund.amt"};
		my ($reason) = $ZOOVY::cgiv->{"$TXNUUID.refund.reason"};
		if (not &ZTOOLKIT::isdecnum($amt)) {
			$ERROR = "Sorry but capture amount: $amt is not valid";
			}
		elsif ($amt<=0) {
			$ERROR = "Sorry but capture amount: $amt must be a positive decimal number.";
			}
		elsif ($amt == $payrec->{'amt'}) { 
			## amount is the same, void the transaction
			$payrec->{'voided'} = time();
			$payrec->{'ps'} = 602; 
			$payrec->{'note'} = $reason;
			}
		else {
			## amount differs
			my ($newpayrec) = $O2->add_payment($payrec->{'tender'},$amt,
				'puuid'=>$payrec->{'uuid'},'ps'=>302,'note'=>$reason,'luser'=>$LUSERNAME);
			$newpayrec->{'puuid'} = $payrec->{'uuid'};
			}
		#$O2->sync_action('payment',"$VERB/$TXNUUID");
		#$O2->order_save();
		}
	elsif ($VERB eq 'VOID') {
		my ($reason) = $ZOOVY::cgiv->{"$TXNUUID.void.reason"};
		$O2->process_payment('VOID',$payrec,'note'=>$reason,'luser'=>$LUSERNAME);
		}
	elsif (($VERB eq 'REFUND') || ($VERB eq 'CREDIT')) {
		my ($amt) = $ZOOVY::cgiv->{"$TXNUUID.refund.amt"};
		my ($reason) = $ZOOVY::cgiv->{"$TXNUUID.refund.reason"};
		if (not &ZTOOLKIT::isdecnum($amt)) {
			$ERROR = "Sorry but capture amount: $amt is not valid";
			}
		elsif ($amt<=0) {
			$ERROR = "Sorry but capture amount: $amt must be a positive decimal number.";
			}
		else {
			$O2->process_payment('REFUND',$payrec,'amt'=>$amt,'note'=>$reason,'luser'=>$LUSERNAME);
			# $O2->order_save();
			}
		}
	else {
		$ERROR = "VERB:$VERB TXNUUID:$TXNUUID PAYREC:".Dumper($payrec);
		}

	if (not $ERROR) {
		$O2->sync_action('payment',"$VERB/$TXNUUID");
		$O2->order_save();
		}

	$VERB = '';
	}

##
##
##
if ($VERB eq 'ADD-PAYMENT') {

	my $tender = $ZOOVY::cgiv->{'add_payment_method'};
	my $amt = $ZOOVY::cgiv->{'AMOUNT'};
	my %params = ();
	if ($ZOOVY::cgiv->{'NOTE'} ne '') { $params{'note'} = $ZOOVY::cgiv->{'NOTE'}; }
	$params{'luser'} = $LUSERNAME;
	$params{'LU'} = $LUSERNAME;
		
	my $payrec = undef;
	if (not &ZTOOLKIT::isdecnumneg($amt)) {
		$ERROR = "Amount must be a valid number";
		}
	elsif (($amt <= 0) && ($tender ne 'CASH')) {
		$ERROR = "Amount must be greater than zero";
		}
	elsif ($amt>$O2->in_get('sum/balance_due_total')) {
		$ERROR = "Capture Amount is greater than the balance due";
		}
	elsif (($tender eq 'CREDIT') && ($ZOOVY::cgiv->{'cc_capture'}eq '')) {
		$ERROR = "You must select the appropriate auth/capture setting to perform a credit card transaction.";	
		}
	elsif ($tender eq 'CREDIT') {
		$params{'CC'} = $ZOOVY::cgiv->{'CC'};
		$params{'YY'} = $ZOOVY::cgiv->{'YY'};
		$params{'MM'} = $ZOOVY::cgiv->{'MM'};
		$params{'CV'} = $ZOOVY::cgiv->{'CV'};
		($payrec) = $O2->add_payment('CREDIT',$amt,%params);
		if ($ZOOVY::cgiv->{'cc_capture'}==1) {
			## instant
			($payrec) = $O2->process_payment('CHARGE',$payrec,%params);
			}
		elsif ($ZOOVY::cgiv->{'cc_capture'}==2) {
			## external 
			$params{'ps'} = '005';
			($payrec) = $O2->process_payment('SET',$payrec,%params);
			}
		else {
			## auth only
			($payrec) = $O2->process_payment('AUTHORIZE',$payrec,%params);
			}
		}
	elsif ($tender =~ /^WALLET\:([\d]+)$/) {
		$params{'ID'} = $1;
		($payrec) = $O2->add_payment('WALLET',$amt,%params);
		($payrec) = $O2->process_payment('INIT',$payrec,%params);
		}
	elsif ($tender =~ /^GIFTCARD\:([A-Z0-9\-]+)$/) {
		## what needs to happen on a giftcard .. well:
		my ($GCODE) = ($1);
		# 1. load the giftcard
		require GIFTCARD;
		my ($gcref) = &GIFTCARD::lookup($USERNAME,'CODE'=>$GCODE);
		# 2. check the balance to make sure the amt does exceed that (if it does, lower it)
		if (not defined $gcref) {
			$ERROR = "Could not locate GIFTCARD GCODE:$GCODE in the database";
			}
		elsif ($gcref->{'BALANCE'}<$amt) {
			$ERROR = sprintf("Giftcard Balance: \$%0.2f is less than amount:\$%0.2f",$gcref->{'BALANCE'},$amt);
			}
		# 3. add giftcard payment
		if (not $ERROR) {
			my %payment = ('GC'=>$gcref->{'CODE'},'GI'=>$gcref->{'GCID'});
			($payrec) = $O2->add_payment('GIFTCARD',$amt,'acct'=>&ZPAY::packit(\%payment));
			($payrec) = $O2->process_payment('CHARGE',$payrec,%payment);
			}
		}
	elsif ($tender eq 'PO') {
		if ($ZOOVY::cgiv->{'PO'} ne '') {
			$params{'PO'} = $ZOOVY::cgiv->{'PO'};
			$O2->in_set('want/po_number',$params{'PO'});
			}
		($payrec) = $O2->add_payment('PO',$amt,%params);
		}
	elsif (($tender eq 'CHECK') || ($tender eq 'CHKOD') || ($tender eq 'COD') || ($tender eq 'WIRE')) {
		$params{'ps'} = '068';
		($payrec) = $O2->add_payment($tender,$amt,%params);
		}
	elsif ($tender eq 'CASH') {
		$params{'ps'} = '169';
		if ($ZOOVY::cgiv->{'cash-received'}) { 
			$params{'ps'} = '069'; 
			}
		## if the amount is less than zero, then treat it as a refund.	
		if ($amt < 0) { 
			$params{'ps'} = '369'; $amt = 0 - $amt; 
			}
		($payrec) = $O2->add_payment('CASH',$amt,%params);
		}
	elsif ($tender eq 'LAYAWAY') {
		$params{'ps'} = '195';
		($payrec) = $O2->add_payment('LAYAWAY',$amt,%params);		
		}
	elsif ($tender eq 'CASH') {
		$params{'ps'} = '169';
		($payrec) = $O2->add_payment('PICKUP',$amt,%params);		
		}
	elsif ($tender eq 'PAYPAL') {
		$params{'ps'} = '003';
		$params{'auth'} =  $ZOOVY::cgiv->{'paypal.txnid'};
		($payrec) = $O2->add_payment('PAYPAL',$amt,%params);		
		}
	else {
		$ERROR = "Unknown Tender Type[$tender]";
		}


	if (defined $payrec) {
		$O2->order_save();
		}

	$VERB = '';
	}


if ($VERB eq '') {
	my $c = '';
	my $r = '';

	my @WARNINGS = ();
	## 
	foreach my $set (@{$O2->payments_as_chain()}) {		
		## reminder:
		## payments_as_chain() returns first element is a parent transactions, and chainedpayments is an arrayref
		## of any chained transactions
		my ($pref,$chainedpayments) = @{$set};
		my $payid = sprintf("%s-%s",$pref->{'tender'},$pref->{'uuid'});
	
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class='$r'>";
		$c .= sprintf("<td nowrap valign=top>%s</td>",&ZTOOLKIT::pretty_date($pref->{'ts'},2));
		# $c .= qq~<td>$pref->{'uuid'}</td>~;

		my $amt = $pref->{'amt'};

		my @actions = ('-');
		if ($pref->{'voided'}) {
			## if a transaction has been voided, nothing else can be done.
			}
		elsif ($pref->{'tender'} eq 'AMAZON') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'AMZCBA') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'BUY') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'EBAY') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'SEARS') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'HSN') {
			push @actions, 'marketplace-refund';
			push @actions, 'marketplace-void';
			}
		elsif ($pref->{'tender'} eq 'GOOGLE') {
			if ($pref->{'ps'} eq '199') {	push @actions, 'capture'; }			
			if ($pref->{'ps'} eq '011') {
				push @actions, 'refund'; 
				push @actions, 'void';
				}
			}
		elsif ($pref->{'tender'} eq 'PAYPALEC') {
			## PAYPALEC is a separate tender type (but short term it's basically a credit card)
			## long term it will have some specialized actions that are unique exclusively to paypal
			if ($pref->{'ps'} eq '189') {	push @actions, 'capture'; }
			if ($pref->{'ps'} eq '199') {	push @actions, 'capture'; }
			if ($pref->{'ps'} eq '259') { push @actions, 'retry'; }
			if ((substr($pref->{'ps'},0,1) eq '0') || (substr($pref->{'ps'},0,1) eq '4')) { 
				push @actions, 'refund'; 
				push @actions, 'void';
				}
			}
		elsif ($pref->{'tender'} eq 'CREDIT') {
			if ($pref->{'ps'} eq '109') {	push @actions, 'capture'; }	# a special status where we have full CC in ACCT
			elsif ($pref->{'ps'} eq '199') {	push @actions, 'capture'; }
			elsif ($pref->{'ps'} eq '499') {	push @actions, 'capture'; }

			if ((substr($pref->{'ps'},0,1) eq '4') && ($pref->{'ps'} ne '499')) { 
				push @actions, 'allow-payment';
				}

			if ((substr($pref->{'ps'},0,1) eq '0') || (substr($pref->{'ps'},0,1) eq '4')) { 
				push @actions, 'refund'; 
				push @actions, 'void';
				}
			}
		elsif ($pref->{'tender'} eq 'GIFTCARD') {
			if ($pref->{'ps'} eq '070') {
				push @actions, 'refund'; 
				}
			}
		elsif ($pref->{'tender'} =~ /^(CASH|CHECK|PO|MO)$/) {
			if (&ZPAY::ispsa($pref->{'ps'},['3'])) {
				# top level payment is a credit, so we can only perform voids.
				push @actions, 'void'; 
				}
			elsif ($pref->{'voided'}==0) {
				push @actions, 'refund'; 
				push @actions, 'set-paid'; 
				}
			}
		elsif ($pref->{'tender'} eq 'LAYAWAY') {
			push @actions, 'layaway';
			push @actions, 'void';
			}
		elsif ($pref->{'tender'} eq 'PAYPALEC') {
			if ($pref->{'ps'} eq '199') { push @actions, 'capture'; };
			}
		push @actions, 'override';
		if (&ZPAY::ispsa($pref->{'ps'},['9','2'])) {
			## some type of deny or error
			push @actions, 'void';			
			}

		if ($pref->{'uuid'} eq '') { $pref->{'uuid'} = 'UNDEFINED-UUID'; }
		my ($id) = $pref->{'uuid'};
		$id = uc($id);
		# $id =~ s/[^A-Z0-9]//gs;
		# my $jsid = &ZTOOLKIT::jquery_escape($id);
		
		$c .= qq~<td nowrap valign=top><select id="$id" name="$id">~;
		foreach my $a (@actions) {
			my $selected = ($a eq '-')?'selected':'';
			$c .= "<option $selected value=\"$a\">$a</option>";
			}
		
		# my $id = $id;
		# $id =~ s/[^A-Z0-9a-z]//gs;
		# &ZTOOLKIT::jquery_escape($id);		

		$c .= qq~</select>
<script>
	\$('#$id').change(function () {
		\$('div[id^=$id]').hide();
		\$('div[id=$id'+'\\\\.'+this.value+']').show();
      }).change();
  \$(document).ready(
		function(){
		\$('#$id').change();		
     });
</script>
</td>~;
		$c .= sprintf("<td nowrap valign=top>%s</td>",$pref->{'tender'});
		my ($amt) = (substr($pref->{'ps'},0,1) eq '3')?0-$pref->{'amt'}:$pref->{'amt'};


		$c .= "<td nowrap valign=top>";
		if (&ZPAY::ispsa($pref->{'ps'},['2','6','9'])) {
			$c .= sprintf("<del>\$%.2f</del>",$amt);
			}
		elsif (&ZPAY::ispsa($pref->{'ps'},['3'])) {
			$c .= sprintf("<font color='red'>(\$%.2f)</font>",$amt);
			}
		elsif (&ZPAY::ispsa($pref->{'ps'},['0','4'])) {
			$c .= sprintf("<font color='blue'>+\$%.2f</font>",$amt);
			}
		elsif (&ZPAY::ispsa($pref->{'ps'},['1'])) {
			$c .= sprintf("<font color='green'>~\$%.2f (auth)</font>",$amt);
			}
		else {
			$c .= "-ERR-";
			}
		$c .= "</td>";

	
		my $debug = '';
		if ($pref->{'voided'}) {
			$debug .= qq~<div class="hint"><b>THIS TRANSACTION HAS BEEN VOIDED BY A CHAINED PAYMENT TRANSACTION.</b></div>~;
			}
		if ($pref->{'note'} ne '') {
			$debug .= qq~<div class="hint">NOTE: $pref->{'note'}</div>~;
			}

		if (&ZPAY::ispsa($pref->{'ps'},['2','9'])) {
			if ($pref->{'debug'} ne '') {
				$debug .= qq~<div class="hint">DEBUG: $pref->{'debug'}</div>~;
				}
			elsif ($pref->{'r'} ne '') {
				$debug .= qq~<div class="hint">API RESPONSE: $pref->{'r'}</div>~;
				}
			else {
				$debug .= qq~<div class="hint">No Debug or API dump Available</div>~;
				}
			if ($ZPAY::PAYMENT_STATUS_HELPER{$pref->{'ps'}}) {
				$debug .= qq~<div class="hint"><a target=\"webdoc\" href=\"http://webdoc.zoovy.com/doc/50456\">Learn more about payment status $pref->{'ps'} in webdoc 51456</a></div>~;
				}
			}


		if ($pref->{'tender'} eq 'PAYPALEC') {
			$debug .= qq~<div class="hint">Paypal Transaction ID: $pref->{'auth'}</div>~;
			}
		if ($pref->{'tender'} eq 'PAYPAL') {
			$debug .= qq~<div class="hint">Paypal Transaction ID: $pref->{'auth'}</div>~;
			}
		if ($pref->{'tender'} eq 'GOOGLE') {
			$debug .= qq~<div class="hint">Google Order ID: $pref->{'txn'}</div>~;
			}
		if ($pref->{'tender'} eq 'EBAY') {
			$debug .= qq~<div class="hint">eBay Payment Transaction ID: $pref->{'txn'}</div>~;
			}
		if ($pref->{'tender'} eq 'GIFTCARD') {
			my ($acct) = &ZPAY::unpackit($pref->{'acct'});
			$debug .= sprintf(qq~<div class="hint">Giftcard: %s</div>~,&GIFTCARD::obfuscateCode($acct->{'GC'},2));			
			}
		if ($pref->{'tender'} eq 'BUY') {
			my ($acct) = &ZPAY::unpackit($pref->{'acct'});
			if ($acct->{'BO'} ne '') { $debug .= sprintf(qq~<div class="hint">Buy.com Order #: %s</div>~,$acct->{'BO'}); }
			}


		if ($pref->{'tender'} eq 'PO') {
			my ($acct) = &ZPAY::unpackit($pref->{'acct'});
			if ($acct->{'PO'} eq '') {
				$acct->{'PO'} = $O2->in_get('want/po_number');
				}
			$debug .= sprintf(qq~<div class="hint">PO: %s</div>~,$acct->{'PO'});	
			}

		if ($pref->{'tender'} eq 'ECHECK') {
			# |EA:948029707|EN:Gordon Austin|ES:|EI:|CM:|EB:Chase|ER:04000037
			if ($pref->{'auth'} || $pref->{'txn'}) {
				$debug .= qq~<div class="hint">Gateway Response: ~;
				if ($pref->{'auth'} ne '') {
					$debug .= sprintf(q~<span class="hint">Auth=%s</span> &nbsp; ~,$pref->{'auth'});
					}
				if ($pref->{'txn'} ne '') {
					$debug .= sprintf(q~<span class="hint">Settlement=%s</span>~,$pref->{'txn'});
					}
				$debug .= qq~</div>~;
				}
			my ($acct) = &ZPAY::unpackit($pref->{'acct'});
			if ($acct->{'EA'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Account #%d</div>",$acct->{'EA'});
				}
			if ($acct->{'ER'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Routing #%d</div>",$acct->{'ER'});
				}
			if ($acct->{'EI'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Check #: %d</div>",$acct->{'EI'});
				}
			if ($acct->{'ET'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Account Type: %s</div>",$acct->{'ET'});
				}
			if ($acct->{'EN'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Name on Account: %s</div>",$acct->{'EN'});
				}
			if ($acct->{'EB'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Bank Name: %s</div>",$acct->{'EB'});
				}
			if ($acct->{'ES'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Bank State: %s</div>",$acct->{'EN'});
				}
			if ($acct->{'EZ'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Driver License State: %s</div>",$acct->{'EZ'});
				}
			if ($acct->{'EL'} ne '') {
				$debug .= sprintf("<div class=\"hint\">Drivers License #: %s</div>",$acct->{'EL'});
				}
			}


		if ($pref->{'tender'} eq 'CREDIT') {
			if ($pref->{'auth'} || $pref->{'txn'}) {
				$debug .= qq~<div class="hint">Gateway Response: ~;
				if ($pref->{'auth'} ne '') {
					$debug .= sprintf(q~<span class="hint">Auth=%s</span> &nbsp; ~,$pref->{'auth'});
					}
				if ($pref->{'txn'} ne '') {
					$debug .= sprintf(q~<span class="hint">Settlement=%s</span>~,$pref->{'txn'});
					}
				$debug .= qq~</div>~;
				}
			my ($acct) = &ZPAY::unpackit($pref->{'acct'});
			if ($acct->{'CM'} ne '') {
				$debug .= sprintf("<div class=\"hint\">%s %s EXP:%02d/%02d</div>",
					&ZPAY::cc_type_from_number($acct->{'CM'}),$acct->{'CM'},$acct->{'MM'},$acct->{'YY'});
				}
			else {
				$debug .= qq~<div class="hint">Card Information not Present</div>~;
				}
			}
		$debug .= qq~<div class="hint">Zoovy Transaction ID: $payid</div>~;


		$c .= sprintf("<td valign=top>(%s) %s%s</td>",$pref->{'ps'},$ZPAY::PAYMENT_STATUS{$pref->{'ps'}},$debug);
		$c .= "</tr>";

		$c .= "<tr class=\"$r\"><td></td><td colspan=5>";

		foreach my $action (@actions) {
			next if ($action eq '-');

			$c .= qq~\n<!-- $id.$action -->\n<div id="$id.$action" style="display:none">~;

			if ($action eq 'layaway') {
				$c .= qq~
				<div class="zoovysub2header">LAYAWAY $id</div>
				<div class="hint">This interface is incomplete.</div>
				</div>
				~;
				}
			elsif ($action eq 'retry') {
				$c .= qq~
				<div class="zoovysub2header">RETRY $id</div>
				<input onClick="thisFrm.VERB.value='RETRY:$id'; thisFrm.submit();" class="minibutton" type="button" value="Retry Request" >
				~;						
				}
			elsif ($action eq 'capture') {
				$c .= qq~
				<div class="zoovysub2header">CAPTURE $id</div>
				Amount: \$<input size=5 type="textbox" name="$id.capture.amt" value="$amt"> 
				<input onClick="thisFrm.VERB.value='CAPTURE:$id'; thisFrm.submit();" class="minibutton" type="button" value="Capture" >
				~;		
				}
			elsif ($action eq 'refund') {
				$c .= qq~
				<div class="zoovysub2header">REFUND $id</div>
				Amount: \$<input size=5 type="textbox" name="$id.refund.amt" value="$amt"> 
				Reason: <input size=20 type="textbox" name="$id.refund.reason">
				<input onClick="thisFrm.VERB.value='REFUND:$id'; thisFrm.submit();" class="minibutton" type="button" value="Refund" >
				~;
				}
			elsif ($action eq 'set-paid') {
				$c .= qq~
				<div class="zoovysub2header">SET PAID $id</div>
				<div class="hint">It is your responsibility to ensure payment was actually received.</div>
				Amount Received: \$<input size=5 type="textbox" name="$id.set-paid.amt" value="$amt"> 
				Note: <input size=20 type="textbox" name="$id.set-paid.note">
				<input onClick="thisFrm.VERB.value='SET-PAID:$id'; thisFrm.submit();" class="minibutton" type="button" value="Set Paid" >
				~;
				}
			elsif ($action eq 'allow-payment') {
				$c .= qq~
				<div class="zoovysub2header">ALLOW PAYMENT $id</div>
				<div class="hint">This will flag a review transaction as 'reviewed', if you choose not to accept this payment
				you will likely need to perform a refund of some sort.</div>
				Note: <input size=20 type="textbox" name="$id.allow-payment.note">
				<input onClick="thisFrm.VERB.value='ALLOW-PAYMENT:$id'; thisFrm.submit();" class="minibutton" type="button" value="Allow Payment" >
				~;
				}
			elsif ($action eq 'void') {
				$c .= qq~
				<div class="zoovysub2header">VOID $id</div>
				Reason: <input size=20 type="textbox" name="$id.void.reason">
				<input onClick="thisFrm.VERB.value='VOID:$id'; thisFrm.submit();" class="minibutton" type="button" value="Void" >
				<div class="hint">
				REMINDER: this will void a payment, void must be done before your settlement time (contact your merchant bank).
If you are planning to cancel an order you will probably need to change the workflow status as well.
				</div>
				~;
				}
			elsif ($action eq 'marketplace-refund') {
				$c .= qq~
<div class="zoovysub2header">MARKETPLACE PARTIAL REFUND</div>
<div class="warning">IMPORTANT: 
You will need to adjust the payment manually on the marketplace then update the records here.
Zoovy does not have a way to automatically issue refunds on the marketplace.
</div>
Amount: <input type="textbox" size="5" name="$id.marketplace-refund.amt" value=""><br>
Note: <input type="textbox" size="20" name="$id.marketplace-refund.note" value=""><br>
<input onClick="thisFrm.VERB.value='MARKETPLACE-REFUND:$id'; thisFrm.submit();" class="minibutton" type="button" value="Refund"><br>
<div class="hint">
Hint1: Refund is for partial credits, use void to refund an entire payment.
Hint2: Since this amount is a refund you do not need to use a negative (-) sign. <br>
</div>

~;
				}
			elsif ($action eq 'marketplace-void') {
				$c .= qq~
<div class="zoovysub2header">MARKETPLACE VOID</div>
<div class="warning">IMPORTANT: 
You will need to cancel the order on the marketplace then update the records here.
Zoovy does not have a way to automatically update/process cancellations on the marketplace.
</div>
Void Reason: <input type="textbox" size="20" name="$id.marketplace-void.reason" value=""><br>
<input onClick="thisFrm.VERB.value='MARKETPLACE-VOID:$id'; thisFrm.submit();" class="minibutton" type="button" value="Void"><br>

~;
				}
			elsif ($action eq 'override') {
				$c .= qq~
				<div class="zoovysub2header">OVERRIDE $id</div>
				New Payment Status: <input type="textbox" size="3" name="$id.override.ps" value="$pref->{'ps'}"><br>
				Note: <input type"textbox" name="$id.override.note" value="~.&ZOOVY::incode($pref->{'note'}).qq~"><br>
				<input onClick="thisFrm.VERB.value='OVERRIDE:$id'; thisFrm.submit();" class="minibutton" type="button" value="Set" >
				<div class="hint">This is an advanced interface intended for experts only. 
				Do not use without the guidance of technical support.
				<div>
				<a target="webdoc" href="http://webdoc.zoovy.com/doc/50456">WEBDOC #50456: Payment Status Codes</a>
				</div>
				</div>
				~;
				}
			else {
				$c .= "Unknown action[$action]\n";
				}
			$c .= qq~<br><br></div>\n~;
			}
		$c .= "</td></tr>";

#		next;	# wtf - this line breaks a ton of stuff (no credit/re-attempts displayed)
		
		my $chainedcss = "color: #888888;";
		foreach my $chainedpref (@{$chainedpayments}) {	
			my $chainpayid = sprintf("%s-%s",$pref->{'tender'},$pref->{'uuid'});

			$c .= qq~<tr class=\"$r\">~;
			# $c .= qq~<td>$chainedpref->{'uuid'}</td>~;
			$c .= sprintf(qq~<td nowrap style="$chainedcss" valign=top>%s</td>~,&ZTOOLKIT::pretty_date($chainedpref->{'ts'},2));
			$c .= qq~<td valign="top" style="$chainedcss" align='center'>[chained]</td>~;
			$c .= qq~<td valign="top" style="$chainedcss" align='center'>&quot;</td>~;
			my ($amt) = (substr($chainedpref->{'ps'},0,1) eq '3')?0-$chainedpref->{'amt'}:$chainedpref->{'amt'};
			if (&ZPAY::ispsa($chainedpref->{'ps'},['2','6','9'])) {
				$c .= sprintf("<td style=\"$chainedcss\" nowrap valign=top><del>\$%.2f</del></td>",$amt);
				}
			elsif (&ZPAY::ispsa($chainedpref->{'ps'},['3'])) {
				$c .= sprintf("<td style=\"$chainedcss\" nowrap valign=top><font color='red'>(\$%.2f)</font></td>",$amt);
				}
			elsif (&ZPAY::ispsa($chainedpref->{'ps'},['0','4'])) {
				$c .= sprintf("<td style=\"$chainedcss\" nowrap valign=top><font color='blue'>+\$%.2f</font></td>",$amt);
				}
			elsif (&ZPAY::ispsa($chainedpref->{'ps'},['1'])) {
				$c .= sprintf("<td nowrap valign=top><font color='green'>~\$%.2f (auth)</font></td>",$amt);
				}
			else {
				$c .= "<td style=\"$chainedcss\" nowrap valign=top>-ERR-</td>";
				}
			# $c .= sprintf(qq~<td nowrap style="$chainedcss" valign=top>\$%.2f</td>~,$amt);
			my $debug = '';
			if ($chainedpref->{'note'} ne '') {
				$debug .= qq~<div class="hint">NOTE: $chainedpref->{'note'}</div>~;
				}
			if (&ZPAY::ispsa($chainedpref->{'ps'},['2','9'])) {
				if ($chainedpref->{'debug'} eq '') {
					$debug .= qq~<div class="hint">No General Debug Available</div>~;
					}
				else {
					$debug .= qq~<div class="hint">DEBUG: $chainedpref->{'debug'}</div>~;
					}
				if ($chainedpref->{'r'} eq '') {
					$debug .= qq~<div class="hint">No API Debug Available</div>~;
					}
				else {
					$debug .= qq~<div class="hint">API RESPONSE: $chainedpref->{'r'}</div>~;
					}
				$debug .= qq~<div class="hint">Zoovy Transaction ID: $chainpayid</div>~;
				}
			$c .= sprintf(qq~<td style="$chainedcss" valign=top>(%s) %s $debug</td>~,$chainedpref->{'ps'},$ZPAY::PAYMENT_STATUS{$chainedpref->{'ps'}});
			$c .= qq~</tr>~;
			}
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No Payments have been recorded.</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PAYMENTS -->'} = $c;

	
	if ($O2->in_get('sum/balance_due_total')<0) {
		push @WARNINGS, sprintf(qq~Based on the current payments applied to this order, this customer has overpaid by %.2f. Please correct this by either editing the order to increase the amount, or void/refund one or more payments to avoid reconcilation errors.~,$O2->in_get('sum/balance_due_total'));
		}
	if (($O2->in_get('sum/balance_due_total')==0) && ($O2->in_get('sum/balance_auth_total')>0)) {
		push @WARNINGS, sprintf(qq~Your order is paid in full, however you currently have %.2f in authorizations pending. You should void these authorizations to release the funds to the customers credit card or other payment method.~,$O2->in_get('sum/balance_auth_total'));
		}
	foreach my $payrec (@{$O2->payments()}) {
		if (substr($payrec->{'ps'},-2) eq '00') { 
			my $payid = sprintf("%s-%s",$payrec->{'tender'},$payrec->{'uuid'});
			## x00 payment codes are user set.
			push @WARNINGS, "Zoovy Transaction ID: $payid has a manually set payment status of '$payrec->{'ps'}' no automated functionality can be performed.";
			}
		}

	##
	##
	##
	$c = "";
	

	my $ar = ZPAY::payment_methods($USERNAME,prt=>$O2->prt(),admin=>1,'*C'=>$C);
	## NOTE: at some point we'll want to remove 'PAYPAL' legacy from this list using admin=>1
	##			but we'd need to build in support for getting a paypal authroization for an ORDER (not a cart)
	##			which is really more appropriate for a quote, not an order.
	#my $ar = ZPAY::payment_methods($USERNAME,prt=>$O2->prt(),admin=>1);
	#use Data::Dumper;
	#$GTOOLS::TAG{'<!-- DEBUG -->'} = '<pre>'.Dumper($ar).'</pre>'; 

	$GTOOLS::TAG{'<!-- ORDER_POOL -->'} = $O2->pool();
	my $FOUND = 0;
	foreach my $pmref (@{$ar}) {
		my $tender = $pmref->{'id'};
		if ($tender =~ /^(.*?)\:/) { $tender = $1; }

		$c .= "<input type=\"radio\" name=\"add_payment_method\" value='$pmref->{'id'}'>$tender: $pmref->{'pretty'}<br>";
		# $c .= "<pre>".Dumper($pmref)."</pre>";
		if ($pmref->{'id'} eq 'CREDIT') {
			$c .= qq~
			<div style="padding-left: 25px;">
			Card Number: <input type="textbox" size="20" maxlength="20" name="CC"><br>
			Card Exp MO: <input type="textbox" size="2" maxlength="2" name="MM"> YR:<input type="textbox" size="2" maxlength="2" name="YY">
			CVV/CID: <input size="4" maxlength="4" type="textbox" name="CV"><br>
			Mode: 
		<select name="cc_capture">
		<option value=""></option>
		<option value="0">Authorization</option>
		<option value="1">Auth+Capture</option>
		<option value="2">Processed Externally</option>
		</select>
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'ECHECK') {
			$c .= qq~
			<div style="padding-left: 25px;">
			ABA/Routing #: <input type="textbox" size="10" name="echeck_aba_number"><br>
			Account #: <input type="textbox" size="10" name="echeck_acct_number"> YR:<input type="textbox" size="2" name="cc_exp_year">
			Check #: <input type="textbox" size="6" name="echeck_check_number"><br>
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'PO') {
			$c .= qq~
			<div style="padding-left: 25px;">
			PO Number: <input type="textbox" name="PO">
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'PAYPAL') {
			$c .= qq~
			<div style="padding-left: 25px;">
			Paypal Transaction ID: <input name="paypal.txnid" type="textbox"> <span class="hint">*if not provided, then payment will be marked as pending.</span>
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'GIFTCARD') {
			$c .= qq~
			<div style="padding-left: 25px;">
			Giftcard: <input type="textbox" name="giftcard">
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'CASH') {
			$c .= qq~
			<div style="padding-left: 25px;"><input type="checkbox" name="cash-received"> Cash has already been received (treat payment as PAID IN FULL).
			<div class="hint">HINT: You can provide refunds to an order by applying a negative cash value.</div>
			</div>
			~;
			}
		elsif ($pmref->{'id'} eq 'LAYAWAY') {
			$c .= qq~
			<div style="padding-left: 25px;"><div class="hint">
WILLCALL payments are always "pending", they are typically used for quotes. 
Customer can login at http://www.yourdomain.com/order/status?orderid=~.$O2->oid().qq~
to pay for this order.
</div>
</div>
			~;
			}
		#else {
		#	$c .= qq~<div style="padding-left: 25px;">
		#	$pmref->{'id'}
		#	</div>
		#	~;
		#	}		
		}
	# if we made a match on accepted payment the ASSUME its a valid payment type
	# otherwise, don't and show this payment type as a custom.
	#if (!$FOUND) {
	#	$c .= "<option value='".$O2->in_get('our/payment_method')."' selected>".$O2->in_get('our/payment_method')."</option>";
	#	}
	$GTOOLS::TAG{"<!-- AVAILABLE_PAYMENTS -->"} = $c;
	$GTOOLS::TAG{'<!-- IP_ADDRESS -->'} = $O2->in_get('cart/ip_address');
	$GTOOLS::TAG{'<!-- EREFID -->'} = $O2->in_get('want/erefid');

	my $warnings = '';
	foreach my $w (@WARNINGS) {
		$GTOOLS::TAG{'<!-- WARNINGS -->'} .= qq~<div class="warning">WARNING: $w</div>~;
		}
	}


my $c = '';
my $PAYMENTSTATUS ='';

$c = '';
my ($ts,$k);
## step 1: create a hash of key=uuid value=ts
my %SORT = ();
my %EVENTS = ();
foreach my $e (@{$O2->history()}) {
	if (defined $e->{'contents'}) { $e->{'content'} = $e->{'contents'}; }
	$SORT{$e->{'uuid'}} = $e->{'ts'};
	$EVENTS{$e->{'uuid'}} = $e;
	}

foreach my $uuid (&ZTOOLKIT::value_sort(\%SORT,'numerically')) {
	my $e = $EVENTS{$uuid};
	my $bgcolor = 'FFFFFF';
	if ($e->{'etype'} & 32) { $bgcolor = '33FFFF'; } # marketplace
#	elsif ($e->{'etype'} & 16) { $bgcolor = 'FF33FF'; } # supply chain/shipping
	elsif ($e->{'etype'} & 8) { $bgcolor = 'FFCCCC'; } # error
#	elsif ($e->{'etype'} & 4) { $bgcolor = 'CCCCFF'; } # status
#	elsif ($e->{'etype'} & 2) { $bgcolor = 'EEEEFE'; } # payment
	elsif ($e->{'etype'} & 256) { $bgcolor = 'CCCCCC'; } # payment

	$c .= qq~
<tr bgcolor='$bgcolor'>
	<td valign=top>$e->{'luser'}</td>
	<td valign=top>~.&ZTOOLKIT::pretty_date($e->{'ts'},2).qq~</td>
	<td valign=top>$e->{'content'}</td>
</tr>~;
	}

if ($c eq '') {
	$c .= "<tr><td colspan=4><i>No history has been recorded! [This is probably an error]</i></td></tr>\n";
	}
$GTOOLS::TAG{'<!-- EVENTS -->'} = qq~
<table border=1>
<tr>
	<td>user</td>
	<td>date</td>
	<td>message</td>
</tr>
$c
</table>
~;

$GTOOLS::TAG{'<!-- PRT -->'} = $O2->prt();

my $x = undef;
$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = sprintf("\$%s",&ZOOVY::f2money($O2->in_get('sum/order_total')));
$GTOOLS::TAG{'<!-- BALANCE_DUE -->'} = sprintf("\$%s",&ZOOVY::f2money($O2->in_get('sum/balance_due_total')));
$GTOOLS::TAG{'<!-- BALANCE_DUE_PLAIN -->'} = sprintf("%s",&ZOOVY::f2money($O2->in_get('sum/balance_due_total')));

$GTOOLS::TAG{'<!-- BALANCE_AUTH -->'} = sprintf("\$%s",&ZOOVY::f2money($O2->in_get('sum/balance_auth_total')));
$GTOOLS::TAG{'<!-- PAYMENT_METHOD -->'} = ($x = sprintf("%s",$O2->in_get('flow/payment_method')))?$x:'<div class="warning">PAYMENT_METHOD_NOT_SET</div>';
$GTOOLS::TAG{'<!-- PAYMENT_STATUS -->'} = ($x = sprintf("%s",$O2->in_get('flow/payment_status')))?"[$x]: $ZPAY::PAYMENT_STATUS{$x}":'<div class="warning">PAYMENT_STATUS_NOT_SET</div>';

##### FEES
$c = '';
my $TOTAL = 0;
foreach my $fee (@{$O2->fees(1)}) {
	print STDERR Dumper($fee);
	$c .= "<tr><td>$fee->{'code'}</td><td>$fee->{'name'}</td><td>\$".sprintf("%.2f",$fee->{'amount'})."</td></tr>";
	$TOTAL += $fee->{'amount'};
	}

if ($c eq '') 
	{ $c .= "<tr><td><i>No fees have been recorded for this order.</i></td></tr>"; }
else 
	{ $c .= "<tr><td></td><td><b>TOTAL</b></td><td><b>\$".sprintf("%.2f",$TOTAL)."</b></td></tr>\n";  }
$GTOOLS::TAG{'<!-- FEES -->'} = $c;


if ($ERROR ne '') {
	push @MSGS, "ERROR|$ERROR";
	}
if (scalar(@MSGS)>0) {
	$GTOOLS::TAG{'<!-- MESSAGES -->'} = &GTOOLS::show_msgs(\@MSGS);
	}

&GTOOLS::output(title=>"",file=>'payment.shtml',header=>1,jquery=>1);

&DBINFO::db_zoovy_close();

exit;
#
#