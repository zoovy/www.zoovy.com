#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use GTOOLS;
use EXTERNAL;
use ZOOVY;
require LUSER;

my ($LU) = LUSER->authenticate(flags=>'_O&4');
if (not defined $LU) { exit; }

my $template_file = '';
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }



my $CMD = $ZOOVY::cgiv->{'CMD'};

if ($CMD eq "SAVE")
	{

	my $SKU = $ZOOVY::cgiv->{'PRODUCT'};
	my %info = ();
	$info{'BUYER_EMAIL'} = $ZOOVY::cgiv->{'BUYER_EMAIL'};
	$info{'CHANNEL'} = $ZOOVY::cgiv->{'CHANNEL'};
	$info{'ZOOVY_ORDERID'} = $ZOOVY::cgiv->{'ORDER_ID'};
	$info{'PROD_NAME'} = $ZOOVY::cgiv->{'PRODUCT_NAME'};
	$info{'PRICE'} = sprintf("%.2f",$ZOOVY::cgiv->{'PRODUCT_PRICE'});
	$info{'QTY'} = sprintf("%d",$ZOOVY::cgiv->{'PRODUCT_QUANTITY'});
	if ($info{'QTY'}<=0) { $info{'QTY'} = "1"; }

# test pogs:
#$data{$USERNAME.':pogs'} = 'Deluxe_Polo_Shirt_Color,Deluxe_Polo_Shirt_Sizes,Thread_Color';
#$data{$USERNAME.':pog_Deluxe_Polo_Shirt_Color'} = '<option value="NA1" price="" weight="">Navy_Natura</option><option value="BL0" price="" weight="">Black_Natural_Pebble</option><option value="GR0" price="" weight="">Green_Natural_Pebble</option><option value="NA0" price="" weight="">Natural_Pebble_Black</option>';
#$data{$USERNAME.':pog_Deluxe_Polo_Shirt_Sizes'} = '<option value="1" price="0" weight="0">Small</option><option value="2" price="" weight="">Medium</option><option value="4" price="" weight="">X_Large</option><option value="5" price="+3" weight="+3">2X_Large</option>';
#$data{$USERNAME.':pog_Thread_Color'} = '<option value="4" price="" weight="">Red</option><option value="B" price="" weight="">Pink</option>';

	foreach my $k (keys %info) { print STDERR $k." ->".$info{$k}."\n"; }

	my $ID = &EXTERNAL::create($USERNAME,$PRT,$SKU,\%info);

	%info = %{&EXTERNAL::fetchexternal_full($USERNAME,$ID)};
	$template_file = "add-success.shtml";

	$GTOOLS::TAG{"<!-- ID -->"} = $ID;
	$GTOOLS::TAG{"<!-- PRODUCT -->"} = $info{'SKU'};
	$GTOOLS::TAG{"<!-- PRODUCT_NAME -->"} = $info{'PROD_NAME'};
	$GTOOLS::TAG{"<!-- PRODUCT_PRICE -->"} = $info{'PRICE'};
	$GTOOLS::TAG{"<!-- PRODUCT_QUANTITY -->"} = $info{'QTY'};
	$GTOOLS::TAG{"<!-- CUSTOMER -->"} = $info{'BUYER_EMAIL'};
	
	if ($ID)
		{
		$template_file = "add-success.shtml";
		} else {
		$GTOOLS::TAG{"<!-- MESSAGE -->"} = "Could not save data!<br>\n";
		$template_file = "add.shtml";
		}
} else {
	$GTOOLS::TAG{"<!-- CUSTOMER -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT_NAME -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT_PRICE -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT_TAXABLE -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT_QUANTITY -->"} = "";
	$GTOOLS::TAG{"<!-- PRODUCT_WEIGHT -->"} = "";
	$template_file = "add.shtml";
}

&GTOOLS::output(file=>$template_file,header=>1);

