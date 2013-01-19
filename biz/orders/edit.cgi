#!/usr/bin/perl 

no warnings 'once'; # Keep perl -w from bitching about variables that are only used once.

use Data::Dumper;
use lib "/httpd/modules";
require DBINFO;
require GTOOLS;
require ZOOVY;
require ZSHIP;
require CART2;
require INVENTORY;
require ZWEBSITE;
require PRODUCT;
use strict;

my @MSGS = ();
# push @MSGS, "WARNING|+11/19/2012 - we are currently working on this utility. Please use desktop order manager temporarily. Anticipated resolution 9pm.";

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&4');
#if ($USERNAME eq '') { exit; }
# used to fix fucked up js location rewrite
$GTOOLS::TAG{'<!-- TIME -->'} = time();

my $VERB = defined($ZOOVY::cgiv->{"VERB"}) ? $ZOOVY::cgiv->{"VERB"} : '';
$VERB = uc($VERB);
my $OID = $ZOOVY::cgiv->{'OID'};
$GTOOLS::TAG{"<!-- OID -->"} = $OID;


if ($OID eq '') {
	$VERB = 'ERROR';
	print "Content-type: text/plain\n\n";
	print "INTERNAL ERROR - NO ORDER OID WAS RECEIVED! PLEASE CONTACT ZOOVY SUPPORT AND LET THEM KNOW THE ORDER # YOU WERE WORKING ON.\n";
	exit;
	}


my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $gref = &ZWEBSITE::fetch_globalref($USERNAME);

my ($O2) = CART2->new_from_oid($USERNAME,$OID);
my $stuff2 = $O2->stuff2();
my %oref = ();
tie %oref, 'CART2', 'CART2'=>$O2;
my $template_file = 'edit.shtml';

my @BC = ();
push @BC, { name=>"Orders", link=>"/biz/orders/index.cgi" };
push @BC, { name=>sprintf("[ %s ]",$O2->pool()), link=>sprintf("/biz/orders/index.cgi?VERB=SHOW:%s",$O2->pool()) };
push @BC, { name=>$O2->oid(), link=>"/biz/orders/edit.cgi?OID=".$O2->oid() };


print STDERR "VERB: $VERB\n";

if ($VERB eq 'SET-TAX') {		
	$oref{'our/tax_rate'} = sprintf("%0.3f",$ZOOVY::cgiv->{'tax-rate'});
	$oref{'sum/tax_rate_state'} =  $oref{'our/tax_rate'};
	$oref{'sum/tax_rate_city'} = 0;
	$oref{'sum/tax_rate_region'} = 0;
	$oref{'sum/tax_rate_zone'} = 0;
	my $taxrate = ($ZOOVY::cgiv->{'tax-rate'}/100);
	$oref{'sum/items_taxdue'} = sprintf("%.2f", int($oref{'sum/items_taxable'}*100) * $taxrate / 100 );

	$VERB = 'SAVE';
	}

if ($VERB eq 'SET-SHIPPING') {
	my $CARRIER = '';
	my $TOTAL = '';
	#if ($ZOOVY::cgiv->{'SHIPPING'} eq "") {
   #   # this means they want to use CUSTOM
   #   $CARRIER = $ZOOVY::cgiv->{'CUSTOM_SHIP_TYPE'};
   #   $TOTAL = $ZOOVY::cgiv->{'CUSTOM_SHIP_AMOUNT'};
	#	} 
	#else {
	#	# this means they want to use CALC 
	#	($TOTAL,$CARRIER) = split(',',$ZOOVY::cgiv->{'SHIPPING'},2);
	#	}
	$O2->in_set("sum/shp_method",$ZOOVY::cgiv->{'sum/shp_method'});
	$O2->in_set("sum/shp_total",$ZOOVY::cgiv->{'sum/shp_total'});
	$O2->add_history("Updated shipping",undef,0,$LU->login());
	$LU->log('ORDER.EDIT.SHIP',"Updated shipping for order $OID","SAVE");
	$VERB = 'SAVE';
	}

if ($VERB eq 'ADD-SKU') {
	$VERB = 'SAVE';	

	my $SKU = $ZOOVY::cgiv->{'add-sku'};
	my $QTY = $ZOOVY::cgiv->{'add-qty'};
	$QTY =~ s/^[^\d]+$//g;
	$QTY = int($QTY);
	my $PRICE = $ZOOVY::cgi->{'add-price'};
	my $VALID = $ZOOVY::cgiv->{'add-valid'};

	$SKU =~ s/[^A-Z0-9\_\-\:\/\*\#\@\%]+/_/gs;

	if ($SKU eq '') {
		push @MSGS, "ERROR|+SKU is required";
		}

	my $P = undef;
	if (substr($SKU,0,1) eq '%') {
		$stuff2->promo_cram($SKU,$QTY,$PRICE,"New Promo Item");
		push @MSGS, "SUCCESS|+Added promotional item '$SKU'";
		}
	else {
		($P) = PRODUCT->new($USERNAME,$SKU);
		if ((not defined $P) && ($VALID)) {
			push @MSGS, "ERROR|+PRODUCT could not be located.";
			$P = undef;
			}
		}

	if (scalar(grep(/^ERROR\|/,@MSGS))>0) {
		## we already have errors.
		}
	elsif (defined $P) {
		## new item being legacy_crammed into stuff object

		my ($pid,$claim,$invopts,$noinvopts,$virtual) = &PRODUCT::stid_to_pid($SKU);
		# my $optionstr = (($invopts)?":$invopts":'').(($noinvopts)?"/$noinvopts":'');
		if ($QTY eq '') { $QTY = 1; }

		my $variations = &STUFF2::variation_suggestions_to_selections( $P->suggest_variations('stid'=>$SKU) );
		my ($item,$lm) = $stuff2->cram($pid,$QTY,$variations,'force_qty'=>$QTY);
		foreach my $msg (@{$lm->msgs()}) {
			my ($ref) = LISTING::MSGS::msg_to_disposition($msg);
			push @MSGS, "$ref->{'_'}|$ref->{'+'}";
			}
		if (scalar(@MSGS)==0) {
			push @MSGS, "ERROR|+no messages returned from cram";
			}
		}
	elsif ($VALID) {
		push @MSGS, "ERROR|+Cannot add invalid SKU";
		}
	else {
		push @MSGS, "SUCCESS|+Added basic (non-inventory) item '$SKU'";
		$stuff2->basic_cram($SKU,$QTY,$PRICE,"New Item");
		}

	print STDERR Dumper(\@MSGS);

	$VERB = 'SAVE';
	}

if ($VERB eq 'SAVE') {
	$oref{'ship/firstname'} = $ZOOVY::cgiv->{'ship_firstname'};
	$oref{'ship/lastname'} = $ZOOVY::cgiv->{'ship_lastname'};
	$oref{'ship/company'} = $ZOOVY::cgiv->{'ship_company'};
	$oref{'ship/address1'} = $ZOOVY::cgiv->{'ship_address1'};
	$oref{'ship/address2'} = $ZOOVY::cgiv->{'ship_address2'};
	$oref{'ship/city'} = $ZOOVY::cgiv->{'ship_city'};
	$oref{'ship/region'} = $ZOOVY::cgiv->{'ship/region'};
	$oref{'ship/postal'} = $ZOOVY::cgiv->{'ship/postal'};
	$oref{'ship/countrycode'} = $ZOOVY::cgiv->{'ship_country'};

	$oref{'ship/phone'} = $ZOOVY::cgiv->{'ship_phone'};
	$oref{'ship/email'} = $ZOOVY::cgiv->{'ship_email'};
	# if ($oref{'bill/firstname'} eq $oref{'bill/lastname'}) { ($oref{'bill/firstname'},$oref{'bill/lastname'}) = split(' ',$ZOOVY::cgiv->{'bill_fullname'},2); }
	$oref{'bill/firstname'} = $ZOOVY::cgiv->{'bill_firstname'};
	$oref{'bill/lastname'} = $ZOOVY::cgiv->{'bill_lastname'};

	$oref{'bill/company'} = $ZOOVY::cgiv->{'bill_company'};
	$oref{'bill/address1'} = $ZOOVY::cgiv->{'bill_address1'};
	$oref{'bill/address2'} = $ZOOVY::cgiv->{'bill_address2'};
	$oref{'bill/city'} = $ZOOVY::cgiv->{'bill_city'};
	$oref{'bill/region'} = $ZOOVY::cgiv->{'bill/region'};
	$oref{'bill/postal'} = $ZOOVY::cgiv->{'bill/postal'};
	$oref{'bill/countrycode'} = $ZOOVY::cgiv->{'bill_country'};
	$oref{'bill/phone'} = $ZOOVY::cgiv->{'bill_phone'};
	$oref{'bill/email'} = $ZOOVY::cgiv->{'bill_email'};

	$oref{'sum/hnd_total'} = $ZOOVY::cgiv->{'hnd_total'};
	$oref{'sum/spc_total'} = $ZOOVY::cgiv->{'spc_total'};
	$oref{'sum/ins_total'} = $ZOOVY::cgiv->{'ins_total'};

	## 
	## the following block of code  assumes $contentref has been populated with 
	## the contents of the order (which is saved on disk) - we will attempt to compare that with the
	## the new contents and adjust inventory appropriately.
	##

	#my $stuff2 = $O2->stuff2();
	#my %INVDIFF = ();
	#foreach my $x (0..$ZOOVY::cgiv->{'KEYCOUNT'}) {
	#	}

	# use Data::Dumper; print STDERR Dumper($stuff);
	#&INVENTORY::checkout_cart_stuff2($USERNAME, $stuff2, $O2->oid());
	
	my $stuff2 = $O2->stuff2();
	my $r = 0;
	my $html = '';
	my $i = scalar(@{$O2->stuff2()->items()})-1;
	my %INVENTORY = ();
	foreach my $i (0..$i) {
		my $stid = $ZOOVY::cgiv->{"stid.$i"};
		print STDERR "[$i] STID: $stid\n";
		my $item = $O2->stuff2()->item('stid'=>$stid);
		print STDERR Dumper($item);
		$item->{'price'} = $ZOOVY::cgiv->{"price.$i"};
		my $qty_was = $item->{'qty'};
		$item->{'qty'} = $ZOOVY::cgiv->{"qty.$i"};
		if ($item->{'qty'} != $qty_was) {
			my $diff = $item->{'qty'} - $qty_was;
			$item->{'inv_diff'} = 0-$diff;
			push @MSGS, "SUCCESS|+Changed $stid inventory ".(($diff>0)?"+$diff":"$diff");
			}
		else {
			$item->{'inv_diff'} = 0;
			}

		$item->{'prod_name'} = $ZOOVY::cgiv->{"text.$i"};
		$item->{'description'} = $ZOOVY::cgiv->{"text.$i"};
		$item->{'taxable'} = $ZOOVY::cgiv->{"tax.$i"};		
		}
	&INVENTORY::checkout_cart_stuff2($USERNAME, $O2->stuff2(), $O2->oid());
	$O2->order_save();
	}


## dump all order properties
foreach my $group (@CART2::VALID_GROUPS) {
	my $group = $O2->{"%$group"};
	next if (not defined $group); 
	foreach my $k (keys %{$group}) {
		$GTOOLS::TAG{"<!-- $group\_$k -->"} = &ZOOVY::incode($group->{$k});
		$GTOOLS::TAG{uc("<!-- $k -->")} =  &ZOOVY::incode($group->{$k});
		}
	}


# $GTOOLS::TAG{"<!-- SHIP_NAME -->"} = ($oref{"ship/fullname"})?($oref{"ship/fullname"}):($oref{"ship/firstname"}." ".$oref{"ship/lastname"});
$GTOOLS::TAG{'<!-- SHIP_FIRSTNAME -->'} = ($oref{'ship/firstname'})?($oref{"ship/firstname"}.''):'';
$GTOOLS::TAG{'<!-- SHIP_MOIDDLENAME -->'} = ($oref{'ship/middlename'})?($oref{"ship/middlename"}.''):'';
$GTOOLS::TAG{'<!-- SHIP_LASTNAME -->'} = ($oref{'ship/lastname'})?($oref{"ship/lastname"}.''):'';
$GTOOLS::TAG{"<!-- SHIP_COMPANY -->"} = ($oref{"ship/company"})?($oref{"ship/company"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_ADDRESS1 -->"} = ($oref{"ship/address1"})?($oref{"ship/address1"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_ADDRESS2 -->"} = ($oref{"ship/address2"})?($oref{"ship/address2"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_CITY -->"} = ($oref{"ship/city"})?($oref{"ship/city"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_COUNTRY -->"} = ($oref{"ship/countrycode"})?($oref{"ship/countrycode"}):"";
$GTOOLS::TAG{"<!-- SHIP_POSTAL -->"} = ($oref{"ship/postal"})?($oref{"ship/postal"}):""; 
$GTOOLS::TAG{"<!-- SHIP_REGION -->"} = ($oref{"ship/region"})?($oref{"ship/region"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_PHONE -->"} = ($oref{"ship/phone"})?($oref{"ship/phone"}.""):"";
$GTOOLS::TAG{"<!-- SHIP_EMAIL -->"} = ($oref{"ship/email"});	

$GTOOLS::TAG{'<!-- BILL_FIRSTNAME -->'} = ($oref{'bill/firstname'})?($oref{"bill/firstname"}.''):'';
$GTOOLS::TAG{'<!-- BILL_MOIDDLENAME -->'} = ($oref{'bill/middlename'})?($oref{"bill/middlename"}.''):'';
$GTOOLS::TAG{'<!-- BILL_LASTNAME -->'} = ($oref{'bill/lastname'})?($oref{"bill/lastname"}.''):'';
$GTOOLS::TAG{"<!-- BILL_COMPANY -->"} = ($oref{"bill/company"})?($oref{"bill/company"}.""):"";
$GTOOLS::TAG{"<!-- BILL_ADDRESS1 -->"} = ($oref{"bill/address1"})?($oref{"bill/address1"}.""):"";
$GTOOLS::TAG{"<!-- BILL_ADDRESS2 -->"} = ($oref{"bill/address2"})?($oref{"bill/address2"}.""):"";
$GTOOLS::TAG{"<!-- BILL_CITY -->"} = ($oref{"bill/city"})?($oref{"bill/city"}.""):"";
$GTOOLS::TAG{'<!-- BILL_COUNTRY -->'} = ($oref{"bill/countrycode"})?($oref{"bill/countrycode"}):"";
$GTOOLS::TAG{"<!-- BILL_REGION -->"} = ($oref{"bill/region"})?($oref{"bill/region"}.""):"";
$GTOOLS::TAG{'<!-- BILL_POSTAL -->'} = ($oref{"bill/postal"})?($oref{"bill/postal"}):""; 
$GTOOLS::TAG{"<!-- BILL_PHONE -->"} = ($oref{"bill/phone"})?($oref{"bill/phone"}."	"):"";
$GTOOLS::TAG{"<!-- BILL_EMAIL -->"} = ($oref{"bill/email"});	

$GTOOLS::TAG{'<!-- TAX_RATE -->'} = $oref{'our/tax_rate'};
$GTOOLS::TAG{'<!-- TAX_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/tax_total'});

my @stids = $O2->stuff2()->stids();
my ($invref,$reserveref) = &INVENTORY::fetch_incrementals($USERNAME,\@stids,$gref);

my $stuff2 = $O2->stuff2();
my $r = 0;
my $html = '';
my $i = 0;
foreach my $item (@{$O2->stuff2()->items()}) {	
	my $line = '';
	my $price = $item->{'price'};
	my $qty = $item->{'qty'};
	my $weight = $item->{'weight'};
	my $description = $item->{'prod_name'};
	if ($description eq '') { $description = $item->{'description'}; }
	$description = &ZOOVY::incode($description);

	my $tax = &ZOOVY::is_true($item->{'taxable'});

	$r = ($r eq 'r0')?'r1':'r0';
	my $extended = sprintf("\$%.2f",$price * $qty);
	$weight =~ s/[^0-9\.#\-]//g;

	$line .= qq~<tr class="$r">~;

	## this stores a mapping to let us know what the sku was (not that it can change, but just in case)
	$line .= "<td>";
	$line .= qq~<input type='hidden' name='stid.$i' value='$item->{'stid'}'>~;
	$line .= qq~$item->{'stid'}~;
	$line .= "</td>";

	$line .= qq~<td><input type='textbox' size='30' name='text.$i' value="$description"></td>~;
	$line .= qq~<td><center><input type='textbox' size='3' value='$qty' name="qty.$i"></center></td>~;

	my ($invqty) = $invref->{ $item->{'sku'} };		
	my ($rsvqty) = $reserveref->{ $item->{'sku'} };		

	if ($invqty eq '') { $invqty = '*'; }
	if ($rsvqty eq '') { $rsvqty = '*'; }
	$line .= qq~<td><center>$invqty / $rsvqty</center></td>~;
	
	$line .= qq~<td nowrap><center><b>\$</b><input type='textbox' size='7' value='$price' name="price.$i"></center></td>~;
	$line .= qq~<td><center><select name='tax.$i'>~;

	$line .= "<option ".(&ZOOVY::is_true($item->{'taxable'})?'selected':'')." value='1'>Yes</option>";
	$line .= "<option ".(&ZOOVY::is_true($item->{'taxable'})?'':'selected')." value='0'>No</option>"; 
	$line .= qq~</select></td>~;

	$line .= qq~<td><center><input type='textbox' size='5' value='$weight' name="weight.$i"></center></td>~;
	$line .= qq~<td><input type='textbox' size='10' value='$extended' name="extended.$i"></td>~;

	$line .= "</tr>";

	## is this is a regular product??
	if ($item->{'is_basic'} || $item->{'is_promo'} || (substr($item->{'stid'},0,1) eq '%')) {
		$GTOOLS::TAG{"<!-- PROMOS -->"} .= $line;
		}
	else {
		$GTOOLS::TAG{"<!-- ITEMS -->"} .= $line;
		}
	$i++;
	}



&GTOOLS::output(jquery=>1,'msgs'=>\@MSGS,'bc'=>\@BC,file=>$template_file,header=>1,'headjs'=>qq~
<style>
.table { background:#333; }
.table ul { float:left; margin:0; padding:0; border:1px solid #C9C9C9; }
.table ul li { list-style:none; padding:5px 10px; }
.table ul li.title { font-weight:bold; background:#333; color:#fff; }
.table ul li.even { background:#fff }
.table ul li.odd { background:#FFFFE6 }
</style>
~);









__DATA__

my $template_file = '';


########  TAX POPUP EVENT CHAIN RUNS THROUGH EDIT.CGI #############

if ($VERB =~ /CHANGE-TAX/) {
	my %taxes = &ZSHIP::getTaxes($USERNAME,$PRT,webdb=>$webdbref,
		state=>$oref{"ship/region"},
		zip=>$oref{"ship/postal"},
		country=>$oref{"ship/countrycode"},
		shp_total=>$oref{'sum/shp_total'},
		subtotal=>$oref{'sum/items_total'});


	$GTOOLS::TAG{"<!-- CURRENT_STATE_RATE -->"} = $taxes{'state_rate'};
	$GTOOLS::TAG{"<!-- CURRENT_LOCAL_RATE -->"} = $taxes{'local_rate'};
	$GTOOLS::TAG{'<!-- TAX_SHIPPING -->'} = (($taxes{'tax_applyto'}&2)==0)?'checked':'';
	$GTOOLS::TAG{'<!-- CORRECT_STATE_RATE -->'} = $taxes{'state_rate'};
	$GTOOLS::TAG{'<!-- CORRECT_LOCAL_RATE -->'} = $taxes{'local_rate'};
	$template_file = "change-tax.shtml";
	}

# if they have javascript then enable the POPUP variable to be set, so when we submit we know to close
# the window, rather than reload form.
if ($VERB eq "CHANGE-TAX-POPUP") { 
	$GTOOLS::TAG{"<!-- DEFINE_POPUP -->"} = "<input type='hidden' name='POPUP' value='1'>"; 
	}

# if they don't have a javascript, then reload the edit page
if ($VERB eq "HIT-SAVE-TAX" && !$ZOOVY::cgiv->{'POPUP'}) { 
	$template_file = "edit.shtml";  $VERB = "EDIT"; 
	}	

# if they have javascript just close the window, since the parent will still be there!
if ($VERB eq "HIT-SAVE-TAX" && $ZOOVY::cgiv->{'POPUP'})
  { $template_file = "close-popup.shtml"; } 

# we still need to do the actual save too!
if ($VERB eq "HIT-SAVE-TAX") {
   $oref{"sum/tax_rate_zone"} = $ZOOVY::cgiv->{'LOCAL_RATE'};
   $oref{"sum/tax_rate_state"} = $ZOOVY::cgiv->{'STATE_RATE'};
	$oref{"our/tax_rate"} = $ZOOVY::cgiv->{'LOCAL_RATE'} + $ZOOVY::cgiv->{'STATE_RATE'};
	$oref{'is/shp_taxable'} = (defined($ZOOVY::cgiv->{'TAX_SHIPPING'}))?1:0;

	$O2->add_history("Updated tax",undef,0,$LU->login());
	$LU->log('ORDER.EDIT.TAX',"Updated tax for order $OID","SAVE");
	$O2->order_save();
	}
################ END OF TAX MODIFICATION POPUP/HANDOFF ######################




########  SHIPPING POPUP EVENT CHAIN RUNS THROUGH EDIT.CGI #############
if ($VERB =~ /CHANGE-SHIPPING/) {

	my %hash = ();
	my %extra = ();

	my $CARRIER  = $oref{"sum/shp_method"};
	my $SHIPAMOUNT = $oref{"sum/shp_total"};
	my $WEIGHT = $oref{'sum/pkg_weight'};
  
	$GTOOLS::TAG{"<!-- SHIP_AMOUNT -->"} = $SHIPAMOUNT;
	$GTOOLS::TAG{"<!-- SHIP_METHOD -->"} = $CARRIER;
	$GTOOLS::TAG{"<!-- WEIGHT -->"} = $WEIGHT;

	my $shipping_method_string   = "<SELECT NAME='SHIPPING' SINGLE>";
	$shipping_method_string .= "<OPTION VALUE=''>Use Custom</OPTION>\n";
	foreach my $shipmethod (@{$O2->shipmethods('force_update'=>1)}) { 
		my $val = sprintf("%.2f",$shipmethod->{'amount'});
		my $notes = '';
		if ($shipmethod->{'guaranteed_delivery_days'}>0) {
			## todo: display the date.
			}
      $shipping_method_string .= "<OPTION VALUE=\"$val,$shipmethod->{'name'}\">$shipmethod->{'name'} $notes (\$$val)</OPTION>\n"; 
		}
	$shipping_method_string .= "</SELECT>";	
	$GTOOLS::TAG{"<!-- SELECT_SHIPPING -->"} = "$shipping_method_string";
	$template_file = "change-shipping.shtml";
	}

# if they have javascript then enable the POPUP variable to be set, so when we submit we know to close
# the window, rather than reload form.
if ($VERB eq "CHANGE-SHIPPING-POPUP")
  { $GTOOLS::TAG{"<!-- DEFINE_POPUP -->"} = "<input type='hidden' name='POPUP' value='1'>"; }

# if they don't have a javascript, then reload the edit page
if ($VERB eq "HIT-SAVE-SHIPPING" && !$ZOOVY::cgiv->{'POPUP'})
  { $template_file = "edit.shtml";  $VERB = "EDIT"; }	

# if they have javascript just close the window, since the parent will still be there!
if ($VERB eq "HIT-SAVE-SHIPPING" && $ZOOVY::cgiv->{'POPUP'})
  { $template_file = "close-popup.shtml"; } 

# we still need to do the actual save too!
if ($VERB eq "HIT-SAVE-SHIPPING") {
	}
############### END OF SHIPPING MODIFICATION POPUP/HANDOFF ######################

sub is_us {
	my ($country) = @_;

	$country = uc($country);
	if ($country eq '') { return(1); }
	if ($country eq 'US') { return(1); }
	if ($country eq 'USA') { return(1); }
	if ($country eq 'UNITED STATES') { return(1); }

	return(0);
	}


if ($VERB eq "SAVE") {
	require INVENTORY;

#	use Data::Dumper; print STDERR Dumper($stuff);

	$LU->log('ORDER.EDIT.SHIP',"Updated order $OID","SAVE");
	$O2->add_history("Edited+saved order via online interface [".($stuff2->count('show'=>'real'))." actual items]",undef,0,$LU->login());
	$O2->order_save(); 
	$VERB = "EDIT";
	}


if ($VERB eq "" || $VERB eq "EDIT") {


	my $SHIPMETHOD = $oref{"sum/shp_method"};
	my $shipping_tax = $oref{"sum/shp_tax"};
	if ($shipping_tax eq '') { $shipping_tax = 0; }
	my $SHIPPING = $oref{"sum/shp_total"};

	my $TAXRATE = $oref{'our/tax_rate'};
	my $SHIPPRICE = $oref{'sum/shp_total'};
	my $SHIPMETHOD = $oref{'sum/shp_method'};

	my $subtotal = $oref{'sum/items_total'};
	my $totaltax = $oref{'sum/tax_total'};

	my $BGCOLOR = '333333';
	my $c = "";
	my $footer = '';


#	my ($xtop,$xfoot) = add_item($counter++, { stid=>'', prod_name=>'New Item' } ,$gref->{'inv_mode'},'?','?');
#	$c .= $xtop;
#	my ($xtop,$xfoot) = add_item($counter++, { stid=>'', prod_name=>'New Item' }, $gref->{'inv_mode'},'?','?');
#	$c .= $xtop;
#	$c .= "<INPUT TYPE='HIDDEN' name='KEYCOUNT' value='$counter'>\n";
#	$c = $c . $footer;

	$BGCOLOR = '33333';
 	print STDERR "SUBTOTAL: $subtotal\n";

	# Add the Subtotal piece
	$subtotal = sprintf("%.2f",$subtotal);

	$GTOOLS::TAG{'<!-- HND_METHOD -->'} = $oref{'sum/hnd_method'};
	$GTOOLS::TAG{'<!-- HND_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/hnd_total'});
	$GTOOLS::TAG{'<!-- INS_METHOD -->'} = $oref{'sum/ins_method'};
	$GTOOLS::TAG{'<!-- INS_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/ins_total'});
	$GTOOLS::TAG{'<!-- SPC_METHOD -->'} = $oref{'sum/spc_method'};
	$GTOOLS::TAG{'<!-- SPC_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/spc_total'});
	$GTOOLS::TAG{'<!-- SHP_METHOD -->'} = $oref{'sum/shp_method'};
	$GTOOLS::TAG{'<!-- SHP_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/shp_total'});



	$GTOOLS::TAG{'<!-- ORDER_TOTAL -->'} = sprintf("%0.2f",$oref{'sum/order_total'});
		
	$totaltax = sprintf("%.2f",$totaltax);
	
	if ($SHIPMETHOD) { $SHIPMETHOD .= ":"; } else { $SHIPMETHOD = "SHIPPING: "; }
	$SHIPPRICE = sprintf("%.2f",$SHIPPRICE);

	my $GRANDTOTAL = sprintf("%.2f",$oref{'sum/order_total'});	
	if (length($c)<1) { $c = "No contents found!"; }


	$template_file = "edit.shtml";	
	} 


&GTOOLS::output(jquery=>1,file=>$template_file,header=>1,'headjs'=>qq~
<style>
.table { background:#333; }
.table ul { float:left; margin:0; padding:0; border:1px solid #C9C9C9; }
.table ul li { list-style:none; padding:5px 10px; }
.table ul li.title { font-weight:bold; background:#333; color:#fff; }
.table ul li.even { background:#fff }
.table ul li.odd { background:#FFFFE6 }
</style>
~);



__DATA__

,'head'=>qq~
<SCRIPT language="JavaScript">
<!--//
	function popupChangeShipping() {
	  popupWin = window.open('edit.cgi?VERB=CHANGE-SHIPPING-POPUP&OID=$OID','Shipping','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
	  popupWin.focus(true);
	  return false;
	  }
	function popupAddProduct() {
	  popupWin = window.open('edit.cgi?VERB=ADD-PRODUCT-POPUP&OID=$OID','AddProduct','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
	  popupWin.focus(true);
	  return false;
	  }
	function popupChangeTax() {
	  popupWin = window.open('edit.cgi?VERB=CHANGE-TAX-POPUP&OID=$OID','ChangeTax','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
	  popupWin.focus(true);
	  return false;
	  }
	function reCalc() {
		var num_items = document.forms[0].total_items.value
		var subtotal = 0;
		var total = 0;
		for (i=1;i<=num_items;i++) {
			var itemValue = eval("document.forms[0].item_total_" + i + ".value")
			if (itemValue.indexOf('.',0) == 0) {
				var tempnum = itemValue.split('.')
				var newnum = tempnum[0] + tempnum[1]
			}
			else {
				var newnum = itemValue * 100
			}
			subtotal += eval(newnum)
			total += eval(newnum)
		}
		subtotal = eval(subtotal/100)
		document.forms[0].order_subtotal.value = subtotal
		var state_tax = document.forms[0].state_tax.value
		var zip_tax = document.forms[0].zip_tax.value
		var shipping_total = document.forms[0].shipping_total.value
		if (state_tax.indexOf('.',0) == 0) {
			var tempnum = state_tax.split('.')
			var newnum = tempnum[0] + tempnum[1]
		}
		else {
			var newnum = state_tax * 100
		}
		total += eval(newnum)
		state_tax = eval(state_tax/100)
		if (zip_tax.indexOf('.',0) == 0) {
			var tempnum = zip_tax.split('.')
			var newnum = tempnum[0] + tempnum[1]
		}
		else {
			var newnum = zip_tax * 100
		}
		total += eval(newnum)
		zip_tax = eval(zip_tax/100)
		if (shipping_total.indexOf('.',0) == 0) {
			var tempnum = shipping_total.split('.')
			var newnum = tempnum[0] + tempnum[1]
		}
		else {
			var newnum = shipping_total * 100
		}
		total += eval(newnum)
		shipping_total = eval(shipping_total/100)
		total = eval(total/100)
		document.forms[0].order_total.value = total	
	}
	//-->
	</SCRIPT>
~
);


exit;


##
##
## parameters: MODE, USERNAME, OID, TAXRATE, SHIPPRICE, SHIPMETHOD
##	 MODE is what type of invoice to print currently only "NORM" is supported
##	 OID is the order OID
##	 TAXRATE is the tax rate for the other (if applicable) in non-decimal format (10 = %10 tax rate)
##	 SHIPPRICE is the price of shipping
##	 SHIPMETHOD is the text of the method we are shipping
##






##
## this adds an item to the edit form
##
sub add_item {
		return($x,$footer);

	}

