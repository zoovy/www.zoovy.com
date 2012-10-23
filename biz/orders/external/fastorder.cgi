#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require EXTERNAL;
require ZSHIP;
require CUSTOMER;
require ZPAY;
require INVENTORY;
require CART2;
require PRODUCT;
require STUFF2;

use Data::Dumper;
use Lingua::EN::AddressParse;
use strict;

&ZOOVY::init();
&GTOOLS::init();
&DBINFO::db_zoovy_connect();

my @MSGS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = '';
my $CMD = $ZOOVY::cgiv->{'CMD'};
my $ID = $ZOOVY::cgiv->{'ID'};
$GTOOLS::TAG{'<!-- EMAIL -->'} = '';
$GTOOLS::TAG{'<!-- PHONE -->'} = '';
$GTOOLS::TAG{'<!-- NOTES -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'NOTES'});



my ($CART2) = CART2->new_memory($USERNAME,$PRT);
my $STUFF2 = $CART2->stuff2();
my $LM = LISTING::MSGS->new($USERNAME,'stderr'=>1);

if (1) {

	my @STIDS = ();
	my $EXIDS = $ZOOVY::cgiv->{'EXIDS'};
	if (($EXIDS ne '') && ($ZOOVY::cgiv->{'NOTES'} eq '')) {
		$GTOOLS::TAG{'<!-- NOTES -->'} = "Created from incomplete items $EXIDS\n";
		foreach my $CLAIM (split(/,/,$EXIDS)) {
			push @STIDS, "$CLAIM*";
			}
		}

	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /^SKU-(.*?)$/) { push @STIDS, $1; }
		}
	
   foreach my $ID (@STIDS) {
		next if ($ID eq '');

		print STDERR "ID: $ID\n";

		my $stid = $ID;
		if ($ZOOVY::cgiv->{"SKU-$ID"}) { $stid = $ZOOVY::cgiv->{"SKU-$ID"}; }
		next if (substr($stid,0,1) eq '%');	## don't add %A, %B, %C to stuff unless they have an actual sku.

		my $CLAIM = 0;
		if ($ID =~ /^([\d]+)\*$/) { $CLAIM = int($1); }
		if ($CLAIM > 0) {
			my $ref = &EXTERNAL::fetchexternal_full($USERNAME,$CLAIM);
			$stid = "$CLAIM*$ref->{'SKU'}";
			}

		my ($pid,$claim,$invopts,$noinvopts,$virtual) = PRODUCT::stid_to_pid($stid);
		print STDERR "ID: $ID SKU: $stid\n";

#		my $incref = undef;
#			$incref = &EXTERNAL::fetchexternal_full($USERNAME,$1);
#
#			$stid = $incref->{'ID'}.'*'.$incref->{'SKU'};
#			if ($ZOOVY::cgiv->{'EMAIL'} eq '') {
#				$ZOOVY::cgiv->{'EMAIL'} = $incref->{'BUYER_EMAIL'};
#				}			
#			}

		my ($P) = PRODUCT->new($USERNAME,$pid, 'CLAIM'=>$CLAIM);

#		my $prodref = {};
#		my ($pid,$claim,$invopts,$noinvopts,$virtual) = &PRODUCT::stid_to_pid($stid);
#		if (not defined $P) {
#			## prodref will already be defined if we are creating an incomplete item that we needed to looup.
#			($P) = PRODUCT->new($USERNAME,$pid, 'CLAIM'=>$claim);
#			$prodref = $P->prodref();
#			}
#		if (defined $incref) {
#	      my $incprodref = &ZOOVY::attrib_handler_ref($incref->{'DATA'});
#			foreach my $k (keys %{$incprodref}) {
#				$prodref->{$k} = $incprodref->{$k};
#				}
#			}

#		my %item = ();
#		$item{'stid'} = $stid;
#		$item{'product'} = $pid;
#		$item{'full_product'} = $prodref;
#		$item{'claim'} = $claim;
#		$item{'force_qty'} = 1;


		my %params = ();
		$params{'*P'} = $P;
		$params{'*LM'} = $LM;

		## re-entrant load from CGI params
		my $qty = int($ZOOVY::cgiv->{"QTY-$ID"});
		if ($qty == 0) { $qty = 1; }

		if ($ZOOVY::cgiv->{"PRICE-$ID"} ne '') {
			$params{'force_price'} = sprintf("%.2f",$ZOOVY::cgiv->{"PRICE-$ID"}); 
			}
		
#		$item{'taxable'} = (defined($ZOOVY::cgiv->{"TAXABLE-$ID"}))?'Y':'N';
#		$item{'qty'} = int($ZOOVY::cgiv->{"QTY-$ID"});
#		if ($ZOOVY::cgiv->{"QTY-$ID"} eq '') { $item{'qty'} = 1; }
#		$item{'base_price'} = sprintf("%.2f",$ZOOVY::cgiv->{"PRICE-$ID"});
#		if ($ZOOVY::cgiv->{"PRICE-$ID"} eq '') { $item{'base_price'} = sprintf("%.2f",$prodref->{'zoovy:base_price'}); }
#		$item{'base_weight'} = $ZOOVY::cgiv->{"WEIGHT-$ID"};
#		if ($item{'base_weight'} eq '') { $item{'base_weight'} = $prodref->{'zoovy:base_weight'}; }
#		$item{'prod_name'} = $ZOOVY::cgiv->{"TITLE-$ID"};
#		if ($item{'prod_name'} eq '') { $item{'prod_name'} = $prodref->{'zoovy:prod_name'}; }
#		next if ($item{'qty'}==0);
#		$item{'description'} = $item{'prod_name'};
			
#		if (($invopts) || ($noinvopts) || (&ZOOVY::prodref_has_variations($prodref)) ) {
#			## we have options!
#			my ($pogs2) = &ZOOVY::fetch_pogs($USERNAME,$prodref);
#			(my $optionsref, $stid) = POGS::default_options($USERNAME,$stid,$pogs2);	
#			# $item{'optionstr'} = $stid;
#			$item{'%options'} = $optionsref;
#			}

		if (not &ZOOVY::productidexists($USERNAME,$pid)) {
			$LM->pooshmsg("ERROR|+Sorry but product '$pid' is not valid");
			}

		# print STDERR Dumper(\%item);
		# print STDERR Dumper($P);

		if (defined $P) {
			my $variations = STUFF2::variation_suggestions_to_selections( $P->suggest_variations('stid'=>$stid) );
			my ($item) = $STUFF2->cram($pid,$qty,$variations,%params);
			print STDERR Dumper($item);
			}
		
#		open F, ">/tmp/dump";
#		print F Dumper($STUFF2);
#		close F;


		}

	if (not $LM->can_proceed()) { 
		my $c = '';
		foreach my $msg (@{$LM->msgs()}) {
			my ($ref) = &LISTING::MSGS::msg_to_disposition($msg);
			$c .= "<div class=\"$ref->{'_'}\">$ref->{'_'} $ref->{'+'}</div>";
			}
		$GTOOLS::TAG{'<!-- ERRORS -->'} = $c;
		$CMD = ''; 
		}

	}

#print STDERR Dumper($STUFF);
#die();

##
## AT this point @stuff is populated with items.
##



if ($CMD eq 'SAVE') {
	# let'see if we can process this data

	$CART2->in_set('bill/email',$ZOOVY::cgiv->{'EMAIL'});
	$CART2->in_set('ship/email',$ZOOVY::cgiv->{'EMAIL'});
	$CART2->in_set('bill/phone',$ZOOVY::cgiv->{'PHONE'});
	$CART2->in_set('ship/phone',$ZOOVY::cgiv->{'PHONE'});
	$CART2->in_set('pool','RECENT');
	$CART2->in_set('created',time());
	$CART2->in_set('sum/shp_method',$ZOOVY::cgiv->{'SHIPMETHOD'});
	$CART2->in_set('sum/shp_total',$ZOOVY::cgiv->{'SHIPPRICE'});
	$CART2->in_set('want/order_notes',$ZOOVY::cgiv->{'NOTES'});

#	# okay, lets parse the address, steps: split into lines, take the last line
	my @lines = ();
	# take the address, and strip blank lines
	foreach my $line (split("\n",$ZOOVY::cgiv->{'ADDRESS'})) { $line =~ s/[\n\f\r]+//g; if ($line ne '') { push @lines, $line; } }
	my $citystatezip = '';

#	if (1) {
#		my $address = new Lingua::EN::AddressParse({
#			auto_clean=>1, force_case=>1,abbreviate_subcountry=>0,abbreviated_subcountry_only=>1
#			});
#		my $error = $address->parse($ZOOVY::cgiv->{'ADDRESS'});
#		}

	
	print "Scalar is: ".scalar(@lines)."\n";
	if (scalar(@lines)==3) {
		$CART2->in_set('bill/address1', $lines[0]);
		$CART2->in_set('bill/address2', $lines[1]);
		my ($city,$state,$zip) = citystatezip($lines[2]);
		## Attempt to normalize state and zip info (added by AK to attempt to stop stray periods from appearing
		## in order files in the state field ('NY.' instead of 'NY').
		$state = &ZSHIP::correct_state($state,'');
		$zip = &ZSHIP::correct_zip($zip,'');	
		$CART2->in_set('bill/city',$city);
		$CART2->in_set('bill/region',$state);
		$CART2->in_set('bill/postal',$zip);
		} 
	elsif (scalar(@lines)==2) {
		# handle two line format:
		$CART2->in_set('bill/address1', $lines[0]);
		my ($city,$state,$zip) = citystatezip($lines[1]);
		## Attempt to normalize state and zip info (added by AK to attempt to stop stray periods from appearing
		## in order files in the state field ('NY.' instead of 'NY').
		$state = &ZSHIP::correct_state($state,'');
		$zip = &ZSHIP::correct_zip($zip,'');	
		$CART2->in_set('bill/city',$city);
		$CART2->in_set('bill/region',$state);
		$CART2->in_set('bill/postal',$zip);
		}

		
	my ($firstname,$lastname) = split(/[\s]+/,$ZOOVY::cgiv->{'NAME'},2);
	$CART2->in_set('bill/firstname',$firstname);
	$CART2->in_set('bill/lastname',$lastname);
	my %taxes = &ZSHIP::getTaxes($USERNAME,$PRT,
		'city'=> $CART2->in_get('bill/city'),
		'state'=>$CART2->in_get('bill/region'),
		'country'=>$CART2->in_get('bill/country'),
		'address1'=>$CART2->in_get('bill/address1'),
		'zip'=>$CART2->in_get('bill/postal')
		);

	$CART2->in_set('sum/tax_rate_state', $taxes{'state_rate'});
	$CART2->in_set('sum/tax_rate_zone', $taxes{'local_rate'});
	
	foreach my $field (@CART2::VALID_ADDRESS) {
		$CART2->in_set("ship/$field",$CART2->in_get("bill/$field"));	
		}

	#if (defined $ZOOVY::cgiv->{'add_promotions'}) {		
	#	require CART2;
	#	$SITE::merchant_id = $USERNAME;
	#	if ($SITE::merchant_id) {};
	#	# &CART::promo_stuff(undef,$o);
	#	}

	if (defined $ZOOVY::cgiv->{'create_customer'}) {
		$CART2->in_set('want/create_customer',1);
		}
	
	my %final_params = ();
	$final_params{'skip_inventory'} = (defined $ZOOVY::cgiv->{'remove_inventory'})?1:0;

	## *** NEEDS LOVE *** add_promotions option

	my ($lm) = $CART2->finalize_order(%final_params);
	foreach my $msg (@{$lm->msgs()}) {
		my ($ref) = LISTING::MSGS::msg_to_disposition($msg);
		next if ($ref->{'_'} eq 'INFO');
		push @MSGS, sprintf("FINALIZE %s[%s] ",$ref->{'_'},$ref->{'+'});
		}

	$GTOOLS::TAG{'<!-- ORDER_ID -->'} = $CART2->oid();
	my @events = ();
	push @events, 'Manually created order on website via fastorder.cgi';
	$LU->log("ORDER.CREATE","Created order ".$CART2->oid(),"INFO");

	if (defined $ZOOVY::cgiv->{'remove_inventory'}) {
		push @events, 'Decrementing items from inventory';
		&INVENTORY::checkout_cart_stuff2($USERNAME,$STUFF2,$CART2->id());
		}

	$CART2->order_save();
	$template_file = 'fastorder-next.shtml';
	}




if ($CMD eq '') {
	$GTOOLS::TAG{'<!-- NAME -->'} = ZOOVY::incode($ZOOVY::cgiv->{'NAME'});
	$GTOOLS::TAG{'<!-- EMAIL -->'} = ZOOVY::incode($ZOOVY::cgiv->{'EMAIL'});
	$GTOOLS::TAG{'<!-- PHONE -->'} = ZOOVY::incode($ZOOVY::cgiv->{'PHONE'});
	$GTOOLS::TAG{'<!-- ADDRESS -->'} = ZOOVY::incode($ZOOVY::cgiv->{'ADDRESS'});

	$CART2->set_stuff2_please($STUFF2);

	my $customer_management = &ZWEBSITE::fetch_website_attrib($USERNAME,"customer_management");
	if ($customer_management ne 'DISABLED') {
		$GTOOLS::TAG{'<!-- CREATE_CUSTOMER_CHECKED -->'} = 'checked';
		}
	else {
		$GTOOLS::TAG{'<!-- CREATE_CUSTOMER_CHECKED -->'} = '';
		}

	my %contents = ();
	my $c = '';
	my ($taxable,$sku,$qty,$title,$price,$weight);
	foreach my $STID ( $STUFF2->stids() ,'%A','%B','%C') {
		next if ($STID eq '');

		my $itemref = {};
		if (substr($STID,0,1) ne '%') {
			## not a virtual sku
			$itemref = $STUFF2->item('stid'=>$STID);
			# $CART->cart_add_stuff($itemref);
			}

		$c .= "<tr>";
		if (substr($STID,0,1) eq '%') {
			## allow the user to specify a sku.
			$c .= "<td><input type=\"textbox\" value=\"".&ZOOVY::incode($itemref->{'stid'})."\" name=\"SKU-$STID\" size='15'></td>";
			}
		else {
			$c .= "<td>$STID<input type=\"hidden\" value=\"".&ZOOVY::incode($itemref->{'stid'})."\" name=\"SKU-$STID\"</td>";
			}

		$c .= "<td><input type=\"textbox\" value=\"".&ZOOVY::incode($itemref->{'qty'})."\" name=\"QTY-$STID\" size='3'></td>";
		$c .= "<td><input type=\"textbox\" value=\"".&ZOOVY::incode($itemref->{'price'})."\" name=\"PRICE-$STID\" size='10'></td>";
		$c .= "<td><input type=\"textbox\" value=\"".&ZOOVY::incode($itemref->{'prod_name'})."\" name=\"TITLE-$STID\" size=\"45\"></td>";
		$c .= "</tr>\n";
		}

	$GTOOLS::TAG{'<!-- CONTENTS -->'} = $c;
	# $CART2->shipping();

	my $shipprice = $CART2->in_get('sum/shp_total');
	my $shipmethod = $CART2->in_get('cart/shipping_id');

	$GTOOLS::TAG{'<!-- SHIPPRICE -->'} = $shipprice;
	$GTOOLS::TAG{'<!-- SHIPMETHOD -->'} = $shipmethod;
	$template_file = 'fastorder.shtml';
	}

&GTOOLS::output(msgs=>\@MSGS,file=>$template_file,header=>1);

&DBINFO::db_zoovy_close();


sub citystatezip
{
	my ($line) = @_;
	my $city = '';
	my $state = '';
	my $zip = '';
	
	# city comes before the first comma:
	($city,$line) = split(',',$line,2);
	# state comes after the first period
	($state,$zip) = split(' ',$line,2);

	$state =~ s/^[ ]+//g;
	$state =~ s/[ ]+\$//g;
	$state =~ s/\n//g;
	$zip =~ s/^[ ]+//g;
	$zip =~ s/[ ]+\$//g;
	$zip =~ s/\n//g;
	$city =~ s/^[ ]+//g;
	$city =~ s/[ ]+\$//g;
	$city =~ s/\n//g;

	return($city,$state,$zip);
}


