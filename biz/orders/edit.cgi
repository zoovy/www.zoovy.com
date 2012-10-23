#!/usr/bin/perl 

no warnings 'once'; # Keep perl -w from bitching about variables that are only used once.

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

&DBINFO::db_zoovy_connect();
&GTOOLS::init();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&4');
#if ($USERNAME eq '') { exit; }
# used to fix fucked up js location rewrite
$GTOOLS::TAG{'<!-- TIME -->'} = time();

my $a = "";   # this is used throughout the program as scratch

my $CMD = defined($ZOOVY::cgiv->{"CMD"}) ? $ZOOVY::cgiv->{"CMD"} : '';
$CMD = uc($CMD);
my $ID = $ZOOVY::cgiv->{'ID'};
$GTOOLS::TAG{"<!-- ID -->"} = $ID;

if ($ID eq '') {
	$CMD = 'ERROR';
	print "Content-type: text/plain\n\n";
	print "INTERNAL ERROR - NO ORDER ID WAS RECEIVED! PLEASE CONTACT ZOOVY SUPPORT AND LET THEM KNOW THE ORDER # YOU WERE WORKING ON.\n";
	exit;
	}


my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $gref = &ZWEBSITE::fetch_globalref($USERNAME);

my $cname = &ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:company_name");
if (length($cname)<1) { $cname = $USERNAME; }
$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = $cname;


my ($O2) = CART2->new_from_oid($USERNAME,$ID);
my $stuff2 = $O2->stuff2();
my %oref = ();
tie %oref, 'CART2', 'CART2'=>$O2;

my $template_file = '';


########  TAX POPUP EVENT CHAIN RUNS THROUGH EDIT.CGI #############

if ($CMD =~ /CHANGE-TAX/) {
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
if ($CMD eq "CHANGE-TAX-POPUP")
  { $GTOOLS::TAG{"<!-- DEFINE_POPUP -->"} = "<input type='hidden' name='POPUP' value='1'>"; }
#
# if they don't have a javascript, then reload the edit page
if ($CMD eq "HIT-SAVE-TAX" && !$ZOOVY::cgiv->{'POPUP'})
  { $template_file = "edit.shtml";  $CMD = "EDIT"; }	

# if they have javascript just close the window, since the parent will still be there!
if ($CMD eq "HIT-SAVE-TAX" && $ZOOVY::cgiv->{'POPUP'})
  { $template_file = "close-popup.shtml"; } 

# we still need to do the actual save too!
if ($CMD eq "HIT-SAVE-TAX") {
   $oref{"sum/tax_rate_zone"} = $ZOOVY::cgiv->{'LOCAL_RATE'};
   $oref{"sum/tax_rate_state"} = $ZOOVY::cgiv->{'STATE_RATE'};
	$oref{"our/tax_rate"} = $ZOOVY::cgiv->{'LOCAL_RATE'} + $ZOOVY::cgiv->{'STATE_RATE'};
	$oref{'is/shp_taxable'} = (defined($ZOOVY::cgiv->{'TAX_SHIPPING'}))?1:0;

	$O2->add_history("Updated tax",undef,0,$LU->login());
	$LU->log('ORDER.EDIT.TAX',"Updated tax for order $ID","SAVE");
	$O2->order_save();
	}

################ END OF TAX MODIFICATION POPUP/HANDOFF ######################





########  SHIPPING POPUP EVENT CHAIN RUNS THROUGH EDIT.CGI #############
	
if ($CMD =~ /CHANGE-SHIPPING/) {

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
if ($CMD eq "CHANGE-SHIPPING-POPUP")
  { $GTOOLS::TAG{"<!-- DEFINE_POPUP -->"} = "<input type='hidden' name='POPUP' value='1'>"; }

# if they don't have a javascript, then reload the edit page
if ($CMD eq "HIT-SAVE-SHIPPING" && !$ZOOVY::cgiv->{'POPUP'})
  { $template_file = "edit.shtml";  $CMD = "EDIT"; }	

# if they have javascript just close the window, since the parent will still be there!
if ($CMD eq "HIT-SAVE-SHIPPING" && $ZOOVY::cgiv->{'POPUP'})
  { $template_file = "close-popup.shtml"; } 

# we still need to do the actual save too!
if ($CMD eq "HIT-SAVE-SHIPPING") {
	my $CARRIER = '';
	my $TOTAL = '';
	if ($ZOOVY::cgiv->{'SHIPPING'} eq "") {
      # this means they want to use CUSTOM
      $CARRIER = $ZOOVY::cgiv->{'CUSTOM_SHIP_TYPE'};
      $TOTAL = $ZOOVY::cgiv->{'CUSTOM_SHIP_AMOUNT'};
		} 
	else {
		# this means they want to use CALC 
		($TOTAL,$CARRIER) = split(',',$ZOOVY::cgiv->{'SHIPPING'},2);
		}
#  $CARRIER = "";
#  $TOTAL = "";
	$O2->in_set("sum/shp_method",$CARRIER);
	$O2->in_set("sum/shp_total",$TOTAL);

	$O2->add_history("Updated shipping",undef,0,$LU->login());
	$LU->log('ORDER.EDIT.SHIP',"Updated shipping for order $ID","SAVE");
	$O2->order_save();
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


if ($CMD eq "HIT-SAVE-DOM") {
	require INVENTORY;
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

	my $stuff2 = $O2->stuff2();
	my %INVDIFF = ();
	foreach my $x (0..$ZOOVY::cgiv->{'KEYCOUNT'}) {

		my $STID = uc($ZOOVY::cgiv->{"stid$x"});
		$STID =~ s/[^A-Z0-9\_\-\:\/\*\#\@\%]+/_/gs;

		if ($STID eq '') {
			$STID = $ZOOVY::cgiv->{"key$x"};
			}
		next if ($STID eq '');
	
#		$STID = uc($STID);
#		$STID =~ s/[^A-Z0-9a-z_\-\#\:\/\*]+//gs;	# strip invalid (non-SKU) characters

		my $QTY = $ZOOVY::cgiv->{"qty$x"};
		$QTY =~ s/^[^\d]+$//g;
		$QTY = int($QTY);

		my $PRICE = $ZOOVY::cgiv->{"price$x"};
		my $WEIGHT = $ZOOVY::cgiv->{"weight$x"};
		my $TAX = $ZOOVY::cgiv->{"tax$x"};
		my $WEIGHT = $ZOOVY::cgiv->{"weight$x"};
		my $TEXT = $ZOOVY::cgiv->{"text$x"};

		print STDERR "QTY: $QTY\n";

		my ($P) = PRODUCT->new($USERNAME,$STID);

		my $item = $stuff2->item('stid'=>$STID);
		if (defined $item) {
			## existing item: quantity/price change
			## so if we reduce qty from 4 to 3 .. then we should end up with a +1
			$item->{'inv_diff'} += ($item->{'qty'} - $QTY);
			$item->{'qty'} = $QTY;
			$item->{'price'} = $PRICE;
			$item->{'weight'} = $WEIGHT;
			$item->{'taxable'} = &ZOOVY::is_true($TAX);
			$item->{'prod_name'} = $TEXT;
			push @MSGS, "SUCCESS|Updated existing item '$STID'";
			}
		elsif (substr($STID,0,1) eq '%') {
			$stuff2->promo_cram($STID,$QTY,$PRICE,$TEXT);
			push @MSGS, "SUCCESS|Added promotional item '$STID'";
			}
		elsif (defined $P) {
			## new item being legacy_crammed into stuff object

			my ($pid,$claim,$invopts,$noinvopts,$virtual) = &PRODUCT::stid_to_pid($STID);
			# my $optionstr = (($invopts)?":$invopts":'').(($noinvopts)?"/$noinvopts":'');
			if ($QTY eq '') { $QTY = 1; }

			my $variations = &STUFF2::variation_suggestions_to_selections( $P->suggest_variations('stid'=>$STID) );
			my ($item,$lm) = $stuff2->cram($pid,$QTY,$variations,'force_qty'=>$QTY);
			
			#	inv_diff=>int(0-$QTY),
			#	product=>$pid,
			#	optionstr=>$optionstr,
			#	price=>$PRICE,
			#	qty=>$QTY,
			#	# pogs=>$prodref->{'zoovy:pogs'},
			#	# full_product=>$prodref,
			#	weight=>$WEIGHT,
			#	taxable=>$TAX,
			#	prod_name=> $TEXT,
			#	force_qty=>1,
			#	},$oref{{'schedule'});
			foreach my $msg (@{$lm->msgs()}) {
				my ($ref) = LISTING::MSGS::msg_to_disposition($msg);
				push @MSGS, "$ref->{'_'}|$ref->{'+'}";
				}			
			}
		else {
			push @MSGS, "SUCCESS|Added basic (non-inventory) item '$STID'";
			$stuff2->basic_cram($STID,$QTY,$PRICE,$TEXT);
			}
		}

	# use Data::Dumper; print STDERR Dumper($stuff);
	&INVENTORY::checkout_cart_stuff2($USERNAME, $stuff2, $O2->oid());

#	use Data::Dumper; print STDERR Dumper($stuff);

	$LU->log('ORDER.EDIT.SHIP',"Updated order $ID","SAVE");
	$O2->add_history("Edited+saved order via online interface [".($stuff2->count('show'=>'real'))." actual items]",undef,0,$LU->login());
	$O2->order_save(); 
	$CMD = "EDIT";
	}


if ($CMD eq "" || $CMD eq "EDIT") {

	if (&is_us($oref{'ship/countrycode'})) { $oref{'ship/countrycode'} = ''; }
	if (&is_us($oref{'bill/countrycode'})) { $oref{'bill/countrycode'} = ''; }

	# $GTOOLS::TAG{"<!-- SHIP_NAME -->"} = ($oref{"ship/fullname"})?($oref{"ship/fullname"}):($oref{"ship/firstname"}." ".$oref{"ship/lastname"});
	$GTOOLS::TAG{'<!-- SHIP_FIRSTNAME -->'} = ($oref{'ship/firstname'})?($oref{"ship/firstname"}.''):'';
	$GTOOLS::TAG{'<!-- SHIP_MIDDLENAME -->'} = ($oref{'ship/middlename'})?($oref{"ship/middlename"}.''):'';
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

	# GTOOLS::TAG{"<!-- SHIP_NAME -->"} = ($oref{"bill/fullname"})?($oref{"bill/fullname"}):($oref{"bill/firstname"}." ".$oref{"bill/lastname"});
	# if ($oref{'bill/firstname'} eq $oref{'bill/lastname'}) { ($oref{'bill/firstname'},$oref{'bill/lastname'}) = split(' ',$oref{'bill/fullname'},2);	 }
	$GTOOLS::TAG{'<!-- BILL_FIRSTNAME -->'} = ($oref{'bill/firstname'})?($oref{"bill/firstname"}.''):'';
	$GTOOLS::TAG{'<!-- BILL_MIDDLENAME -->'} = ($oref{'bill/middlename'})?($oref{"bill/middlename"}.''):'';
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

	my $SHIPMETHOD = $oref{"sum/shp_method"};
	my $shipping_tax = $oref{"sum/shp_tax"};
	if ($shipping_tax eq '') { $shipping_tax = 0; }
	my $SHIPPING = $oref{"sum/shp_total"};

	# my $a = &build_order_contents($USERNAME,$ID,$o);
	my $a = '';
	## BUILD ORDER CONTENTS

	my $TAXRATE = $oref{'our/tax_rate'};
	my $SHIPPRICE = $oref{'sum/shp_total'};
	my $SHIPMETHOD = $oref{'sum/shp_method'};

	my $a = "";
	my $subtotal = $oref{'sum/items_total'};
	my $totaltax = $oref{'sum/tax_total'};

	my $BGCOLOR = '333333';
	$a .= "\n<table><tr class='zoovytableheader'>";
	$a .= "<td class='zoovytableheader'>SKU</td>";
	$a .= "<td class='zoovytableheader'>PRODUCT</td>";
	$a .= "<td class='zoovytableheader'><center>&nbsp;&nbsp;QUANTITY&nbsp;&nbsp;</center></td>";
	if ($gref->{'inv_mode'} > 0) {
		$a .= "<td class='zoovytableheader'><center>&nbsp;&nbsp;IN_STOCK/RESERVE&nbsp;&nbsp;</center></td>";
		}

	$a .= "<td class='zoovytableheader'><center>&nbsp;&nbsp;PRICE&nbsp;&nbsp;</center></td>";
	$a .= "<td class='zoovytableheader'><center>&nbsp;TAX&nbsp;</center></td>";
	$a .= "<td class='zoovytableheader'><center>WEIGHT</center></td>";
	$a .= "<td class='zoovytableheader'>&nbsp;EXTENDED&nbsp;&nbsp;&nbsp;</td>";
	$a .= "</tr>\n\n";

	my $counter = 0;


	my $footer = '';


	my @stids = $O2->stuff2()->stids();
	my ($invref,$reserveref) = &INVENTORY::fetch_incrementals($USERNAME,\@stids,$gref);

	my $stuff2 = $O2->stuff2();
	foreach my $item (@{$O2->stuff2()->items()}) {	
		my $sku = $item->{'sku'};

		my ($xtop,$xfoot) = add_item($counter++, $item, $gref->{'inv_mode'}, $invref->{$sku}, $reserveref->{$sku});
		$footer .= $xfoot;
		$a .= $xtop;
		}

	my ($xtop,$xfoot) = add_item($counter++, { stid=>'', prod_name=>'New Item' } ,$gref->{'inv_mode'},'?','?');
	$a .= $xtop;
	my ($xtop,$xfoot) = add_item($counter++, { stid=>'', prod_name=>'New Item' }, $gref->{'inv_mode'},'?','?');
	$a .= $xtop;
	$a .= "<INPUT TYPE='HIDDEN' name='KEYCOUNT' value='$counter'>\n";
	$a = $a . $footer;

	$BGCOLOR = '33333';
 	print STDERR "SUBTOTAL: $subtotal\n";

	# Add the Subtotal piece
	$subtotal = sprintf("%.2f",$subtotal);
	$a .= "<tr>";
	$a .= "<td colspan='3' rowspan='4' bgcolor='FFFFFF'><center><table>";
	
	$a .= "<tr>";
	$a .= "<td colspan='3' align='right' bgcolor='FFFFFF'><font color='000000' size='2' face='Arial'><B>Handling:</b> ".($oref{'sum/hnd_method'})."</font></td>";
	$a .= "<td colspan='1' nowrap bgcolor='FFFFFF'><font size='2' color='black' face='Arial'>&nbsp;<b>\$</B>";
	$a .= "<input style='font-size: 8pt;' type='textbox' name='hnd_total' value='".sprintf("%.2f",$oref{'sum/hnd_total'})."' size='5'>";
	$a .= "</font></td></tr>\n";

	$a .= "<tr>";
	$a .= "<td colspan='3' align='right' bgcolor='FFFFFF'><font color='000000' size='2' face='Arial'><B>Specialty:</b> ".($oref{'sum/spc_method'})."</font></td>";
	$a .= "<td colspan='1' nowrap bgcolor='FFFFFF'><font size='2' color='black' face='Arial'>&nbsp;<b>\$</B>";
	$a .= "<input style='font-size: 8pt;' type='textbox' name='spc_total' value='".sprintf("%.2f",$oref{'sum/spc_total'})."' size='5'>";
	$a .= "</font></td></tr>\n";

	$a .= "<tr>";
	$a .= "<td colspan='3' align='right' bgcolor='FFFFFF'><font color='000000' size='2' face='Arial'><B>Insurance:</b> ".($oref{'sum/ins_method'})."</font></td>";
	$a .= "<td colspan='1' nowrap bgcolor='FFFFFF'><font size='2' color='black' face='Arial'>&nbsp;<b>\$</B>";
	$a .= "<input style='font-size: 8pt;' type='textbox' name='ins_total' value='".sprintf("%.2f",$oref{'sum/ins_total'})."' size='5'>";
	$a .= "</font></td></tr></table><br>\n";

	$a .= "<font face='Arial' size='1'>Hint: To delete an item change the quantity to Zero and press SAVE.</font></center></td>";

	$a .= "<td colspan='3' align='right' bgcolor='FFFFFF'><font color='000000' size='2' face='Arial'><B>Subtotal:</b></font></td>";
	$a .= "<td colspan='1' nowrap bgcolor='FFFFFF'><font size='2' color='black' face='Arial'>&nbsp;<b>\$";
	$a .= "<input type='textbox' style='font-size: 8pt;' size='7' name='subtotal' value='$subtotal'>";
	$a .= "</b></font></td></tr>\n";
	
	$totaltax = sprintf("%.2f",$totaltax);
	$a .= "<tr>";
	$a .= "<td colspan='3' align='right' bgcolor='FFFFFF'><font color='000000' size='2' face='Arial'><B>Tax (%";
	$a .= sprintf("%.2f",$TAXRATE)."):</b></font></td>";
	$a .= "<td colspan='1' nowrap bgcolor='FFFFFF'><font size='2' color='black' face='Arial'>&nbsp;<b>\$";
	$a .= "$totaltax</b>";
	$a .= "</font></td><td>";
	$a .= "<input class='minibutton' type='button' value='Calc. Tax' onClick='return(popupChangeTax());'>";
	$a .= "</td></tr>\n";
	
	if ($SHIPMETHOD) { $SHIPMETHOD .= ":"; } else { $SHIPMETHOD = "SHIPPING: "; }
	$SHIPPRICE = sprintf("%.2f",$SHIPPRICE);
	$a .= "<tr>";
	$a .= "<td colspan='3' align='right'><font size='2' face='Arial'><B>$SHIPMETHOD</b></font></td>";
	$a .= "<td nowrap colspan='1'><font size='2' color='black' face='Arial'>&nbsp;<b>\$$SHIPPRICE</b></font>";
	$a .= "</td><td>";
	$a .= "<input class='minibutton' type='button' value='Calc. Shipping' onClick='return(popupChangeShipping());'>";
	$a .= "</td></tr>\n";

	

	my $GRANDTOTAL = sprintf("%.2f",$oref{'sum/order_total'});	
	$a .= "<tr>";
	$a .= "<td colspan='3' align='right'><font color='000000' size='2' face='Arial'><B>GRAND TOTAL:</b></font></td>";
	$a .= "<td nowrap colspan='1'><font color='black' size='2' face='Arial'>&nbsp;<b>\$";
	$a .= "<input type='textbox' size='7' style='font-size: 8pt;' name='grandtotal' value='$GRANDTOTAL'></b></font></td></tr>\n";
	

	$a .= "</table>\n";




	if (length($a)<1) { $a = "No contents found!"; }
	$GTOOLS::TAG{"<!-- DISPLAY_CONTENTS -->"} = "$a";


	foreach my $msg (@MSGS) {
		my ($msgtype,$txt) = split(/\|/,$msg);
		my $class = '';
		if ($msgtype eq 'SUCCESS') { $class = 'success'; }
		if ($msgtype eq 'ERROR') { $class = 'error'; }
		$GTOOLS::TAG{'<!-- MESSAGES -->'} .= qq~<div class="$class">$txt</div>\n~;
		}

	$template_file = "edit.shtml";	
	} 
	# END of CMD eq "EDIT"

&GTOOLS::output(file=>$template_file,header=>1,'head'=>qq~
<SCRIPT language="JavaScript">
<!--//
	function popupChangeShipping() {
	  popupWin = window.open('edit.cgi?CMD=CHANGE-SHIPPING-POPUP&ID=$ID','Shipping','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
	  popupWin.focus(true);
	  return false;
	  }
	function popupAddProduct() {
	  popupWin = window.open('edit.cgi?CMD=ADD-PRODUCT-POPUP&ID=$ID','AddProduct','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
	  popupWin.focus(true);
	  return false;
	  }
	function popupChangeTax() {
	  popupWin = window.open('edit.cgi?CMD=CHANGE-TAX-POPUP&ID=$ID','ChangeTax','status=0,width=380,height=330,directories=0,toolbar=0,menubar=0,resizable=1,scrollbars=1,location=0')
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

&DBINFO::db_zoovy_close();

exit;


##
##
## parameters: MODE, USERNAME, ID, TAXRATE, SHIPPRICE, SHIPMETHOD
##	 MODE is what type of invoice to print currently only "NORM" is supported
##	 ID is the order ID
##	 TAXRATE is the tax rate for the other (if applicable) in non-decimal format (10 = %10 tax rate)
##	 SHIPPRICE is the price of shipping
##	 SHIPMETHOD is the text of the method we are shipping
##






##
## this adds an item to the edit form
##
sub add_item {
		my ($counter,$item,$inv_mode,$invqty,$rsvqty) = @_;
		my $footer = '';
		my $x = '';

		my $BGCOLOR = '';

		my $price = $item->{'price'};
		my $qty = $item->{'qty'};
		my $weight = $item->{'weight'};
		my $description = $item->{'prod_name'};
		if ($description eq '') { $description = $item->{'description'}; }
		$description = &ZOOVY::incode($description);

		my $tax = &ZOOVY::is_true($item->{'taxable'});

		if ($counter % 2) { $BGCOLOR="E1E1E1"; } else { $BGCOLOR='FFFFFF'; }
		if (substr($item->{'stid'},0,1) eq '%') { $BGCOLOR='D0D0D0'; }
		my $extended = sprintf("\$%.2f",$price * $qty);
		$weight =~ s/[^0-9\.#\-]//g;

		$x = qq~<tr><td bgcolor='$BGCOLOR'><font face='Arial' size='2'>~;

		## this stores a mapping to let us know what the sku was (not that it can change, but just in case)
		$x .= qq~<input type='hidden' name='stid$counter' value='$item->{'stid'}'>~;

		if ($item->{'stid'} eq '') {
			$x .= qq~<input type='textbox' name='key$counter' value="" size="15">~;
			}
		else {
			$x .= qq~$item->{'stid'}~;
			}

		$x .= qq~</font></td>
	<td bgcolor='$BGCOLOR'><font face='Arial' size='2'>
	<input type='textbox' size='30' name='text$counter' value="$description"></font></td>
	<td bgcolor='$BGCOLOR'><font face='Arial' size='2'><center><input type='textbox' size='3' value='$qty' name="qty$counter"></center></font></td>~;

	if ($inv_mode>0) {
		if ($invqty eq '') { $invqty = '*'; }
		if ($rsvqty eq '') { $rsvqty = '*'; }
		$x .=qq~<td bgcolor='$BGCOLOR'><center>$invqty / $rsvqty</center></font></td>~;
		}
	
		$x .= qq~
	<td nowrap bgcolor='$BGCOLOR'><font face='Arial' size='2'><center><b>\$</b><input type='textbox' size='7' value='$price' name="price$counter"></center></font></td>
	<td bgcolor='$BGCOLOR'><font face='Arial' size='2'><center>
		<select name='tax$counter'>
			~;

		$x .= "<option ".(&ZOOVY::is_true($item->{'taxable'})?'selected':'')." value='1'>Yes</option>";
		$x .= "<option ".(&ZOOVY::is_true($item->{'taxable'})?'':'selected')." value='0'>No</option>"; 

		$x .= qq~
		</select></font></center></td>
	<td bgcolor='$BGCOLOR'><font face='Arial' size='2'><center><input type='textbox' size='5' value='$weight' name="weight$counter"></center></font></td>
				<td bgcolor='$BGCOLOR'><font face='Arial' size='2'><input type='textbox' size='10' value='$extended' name="extended$counter"></font></td>
</tr>
~;
		## is this is a regular product??
		if (substr($item->{'stid'},0,1) eq '%') {
			$footer = $x;
			$x = '';
			}
		return($x,$footer);

	}

