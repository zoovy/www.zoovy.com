#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
use CGI;
require ZOOVY;
require ZWEBSITE;
require ZSHIP;
require ZSHIP::PRICE;
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


&ZOOVY::init();
&ZWEBSITE::init();
my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&8');
if ($USERNAME eq '') { exit; }

my @BC = ();
push @BC, { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'http://www.zoovy.com/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Price Based Shipping' };

$ACTION = $ZOOVY::cgiv->{'ACTION'};
$TYPE = $ZOOVY::cgiv->{'TYPE'};
$TYPE = 'dom';

if ($TYPE ne 'INT') { $TYPE eq 'DOM'; }
$TYPE = lc($TYPE);
$GTOOLS::TAG{"<!-- TYPE -->"} = $TYPE;
$GTOOLS::TAG{'<!-- CARRIER -->'} = 'Shipping';
# load webdb
%webdb = &ZWEBSITE::fetch_website_db($USERNAME,$PRT);

if ($ACTION eq "SAVE-CHK") {
   if (uc($ZOOVY::cgiv->{'price_dom'}) eq "ON")
		{
		print STDERR "enabling ship pickup\n";
		$webdb{'price_dom'} = 1;
		} else {
		print STDERR "disabling ship price\n";
		$webdb{'price_dom'} = 0;
		}

	$LU->log("SETUP.SHIPPING.PRICEBASED","Saved Domestic Price Based Shipping Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);
	$ACTION ='';
	}

if ($ACTION eq 'SAVE') {
	$price = $ZOOVY::cgiv->{'PRICE'};
	$carrier = $ZOOVY::cgiv->{'CARRIER'};
	$value = $ZOOVY::cgiv->{'VALUE'};
	$behavior = $ZOOVY::cgiv->{'BEHAVIOR'};

	print STDERR "[$price] [$carrier] [$value]\n";

	if ( (defined($price)) && (defined($carrier)) && (defined($value))) {
		$value =~ s/[^0-9\.]//g;
		$price =~ s/[^0-9\.]//g;
		$carrier = substr($carrier,0,25);
		$hashref = &ZSHIP::PRICE::decode_pricebased_string($webdb{'price_'.$TYPE.'_data'});
		$hashref->{$price} = "$behavior $value $carrier";
		$webdb{'price_'.$TYPE.'_data'} = &ZSHIP::PRICE::encode_pricebased_string($hashref);
		print STDERR "F!!!\n";
		}
	else {
		print STDERR "skipped!\n";
		}


	$LU->log("SETUP.SHIPPING.PRICEBASED","Saved Price Based Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);

	$ACTION = '';
	}

if ($ACTION eq 'DELETE')
	{
	$hashref = &ZSHIP::PRICE::decode_pricebased_string($webdb{'price_'.$TYPE.'_data'});
	delete $hashref->{$ZOOVY::cgiv->{'KEY'}};
	$webdb{'price_'.$TYPE.'_data'} = &ZSHIP::PRICE::encode_pricebased_string($hashref);
	$LU->log("SETUP.SHIPPING.PRICEBASED","Deleted from Price Based Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,\%webdb,$PRT);	
	$ACTION = '';
	}

if ($ACTION eq '')
	{
	# set the enabled checkbox status
	print STDERR $webdb{'ship_pickup'}."\n";
	if ($webdb{'price_dom'}>0) { $GTOOLS::TAG{'<!-- DOM_ENABLED -->'} = " checked "; } 
	else { $GTOOLS::TAG{'<!-- DOM_ENABLED -->'} = " "; }
	if ($webdb{'price_int'}>0) { $GTOOLS::TAG{'<!-- INT_ENABLED -->'} = " checked "; } 
	else { $GTOOLS::TAG{'<!-- INT_ENABLED -->'} = " "; }

	$c = '';
	$hashref = &ZSHIP::PRICE::decode_pricebased_string($webdb{'price_dom_data'});
	foreach $k (sort { $a <=> $b; } keys %{$hashref}) {
		($behavior, $price, $description) = split(' ',$hashref->{$k},3);
		$c .= "<tr><td><a href='price.cgi?ACTION=DELETE&KEY=$k&TYPE=dom'>[DELETE]</a></td><td><font size='1'>for orders up to \$$k</font></td>";
		if ($behavior == 0) {
			$c .= "<td>shipping is \$$price</td>";
			}
		elsif ($behavior == 1) {
			$c .= "<td>shipping is %$price of subtotal</td>";
			}
		$c .= "<td>$description</td></tr>";
		}
	if (length($c)>0)
		{
		$c = "<tr bgcolor='3366CC'><td class='title'>ACTION</td><td class='title'>ORDER TOTAL</td><td class='title'>BEHAVIOR</td><td class='title'>CARRIER</td></tr>".$c;
		} else {
		$c .= "<tr><td>No Entries Have been Added</td></tr>";
		}
	$GTOOLS::TAG{'<!-- DOM_TABLE -->'} = $c;

	$template_file = 'price.shtml';
	}

&GTOOLS::output(title=>"Shipping: Price Based",help=>"#50813",file=>$template_file,header=>1,bc=>\@BC);
