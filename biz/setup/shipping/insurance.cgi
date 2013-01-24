#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require ZTOOLKIT;
use strict;

my @MSGS = ();

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Insurance' };

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $template_file = 'insurance.shtml';

if ($FLAGS !~ /,SHIP,/) {
	$template_file = 'noaccess.shtml';
	}

my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

if ($ZOOVY::cgiv->{'ACTION'} eq 'WEIGHT_EDIT') {

	require ZSHIP;
	my $area = $ZOOVY::cgiv->{'weight_area'};
	if ($area ne '') {
		my $ref = &ZTOOLKIT::parseparams($webdb->{'ins_weight_'.$area});
		$ref = fixup($ref);
		my $wt = &ZSHIP::smart_weight($ZOOVY::cgiv->{'weight_upto'});
		my $fee = $ZOOVY::cgiv->{'weight_fee'};
		if ($fee eq '') {
			delete $ref->{$wt}; 
			}
		else {
			$ref->{$wt} = $fee;
			}
		$webdb->{'ins_weight_'.$area} = &ZTOOLKIT::buildparams($ref);
		}
	$ZOOVY::cgiv->{'ACTION'} = 'SAVE';
	}

if ($ZOOVY::cgiv->{'ACTION'} eq 'PRICE_EDIT') {

	require ZSHIP;
	my $area = $ZOOVY::cgiv->{'price_area'};
	if ($area ne '') {
		my $ref = &ZTOOLKIT::parseparams($webdb->{'ins_price_'.$area});
		$ref = fixup($ref);
		my $price = sprintf("%.2f",$ZOOVY::cgiv->{'price_upto'});
		my $fee = $ZOOVY::cgiv->{'price_fee'};
		if ($fee eq '' || $fee eq '0') {
			delete $ref->{$price}; 
			}
		else {
			$ref->{$price} = $fee;
			}
		$webdb->{'ins_price_'.$area} = &ZTOOLKIT::buildparams($ref);
		}
	$ZOOVY::cgiv->{'ACTION'} = 'SAVE';
	}



if ($ZOOVY::cgiv->{'ACTION'} eq 'SAVE') {

	$webdb->{'insurance'} = $ZOOVY::cgiv->{'insurance'};

	$webdb->{'ins_optional'} = int($ZOOVY::cgiv->{'ins_optional'});

	$webdb->{'ins_flat'} = ($ZOOVY::cgiv->{'flat'})?1:0;
	$webdb->{'ins_dom_item1'} = $ZOOVY::cgiv->{'dom_item1'};
	$webdb->{'ins_can_item1'} = $ZOOVY::cgiv->{'can_item1'};
	$webdb->{'ins_int_item1'} = $ZOOVY::cgiv->{'int_item1'};
	$webdb->{'ins_dom_item2'} = $ZOOVY::cgiv->{'dom_item2'};
	$webdb->{'ins_can_item2'} = $ZOOVY::cgiv->{'can_item2'};
	$webdb->{'ins_int_item2'} = $ZOOVY::cgiv->{'int_item2'};

	$webdb->{'ins_product'} = $ZOOVY::cgiv->{'product'};
	$webdb->{'ins_weight'} = ($ZOOVY::cgiv->{'weight'})?1:0;
	$webdb->{'ins_price'} = ($ZOOVY::cgiv->{'price'})?1:0;

	push @MSGS, "SUCCESS|+saved";
	$LU->log("SETUP.SHIPPING.INSURANCE","Saved Settings","SAVE");	
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);	
	}


$GTOOLS::TAG{'<!-- INSURANCE_0 -->'} = '';
$GTOOLS::TAG{'<!-- INSURANCE_1 -->'} = '';
$GTOOLS::TAG{'<!-- INSURANCE_2 -->'} = '';
$GTOOLS::TAG{'<!-- INSURANCE_'.$webdb->{'insurance'}.' -->'} = 'checked'; 

$GTOOLS::TAG{'<!-- INS_OPTIONAL_0 -->'} = '';
$GTOOLS::TAG{'<!-- INS_OPTIONAL_1 -->'} = '';
$GTOOLS::TAG{'<!-- INS_OPTIONAL_'.$webdb->{'ins_optional'}.' -->'} = 'checked'; 

$GTOOLS::TAG{'<!-- INS_FLAT -->'} = ($webdb->{'ins_flat'})?'checked':'';
$GTOOLS::TAG{'<!-- INS_DOM_ITEM1 -->'} = $webdb->{'ins_dom_item1'};
$GTOOLS::TAG{'<!-- INS_CAN_ITEM1 -->'} = $webdb->{'ins_can_item1'};
$GTOOLS::TAG{'<!-- INS_INT_ITEM1 -->'} = $webdb->{'ins_int_item1'};
$GTOOLS::TAG{'<!-- INS_DOM_ITEM2 -->'} = $webdb->{'ins_dom_item2'};
$GTOOLS::TAG{'<!-- INS_CAN_ITEM2 -->'} = $webdb->{'ins_can_item2'};
$GTOOLS::TAG{'<!-- INS_INT_ITEM2 -->'} = $webdb->{'ins_int_item2'};

$GTOOLS::TAG{'<!-- INS_PRODUCT -->'} = ($webdb->{'ins_product'})?'checked':'';
$GTOOLS::TAG{'<!-- INS_PRODUCT_0 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_1 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_2 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_4 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_6 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_7 -->'} = '';
$GTOOLS::TAG{'<!-- INS_PRODUCT_'.int($webdb->{'ins_product'}).' -->'} = 'checked'; 

$GTOOLS::TAG{'<!-- INS_WEIGHT -->'} = ($webdb->{'ins_weight'})?'checked':'';

$GTOOLS::TAG{'<!-- WEIGHT_DOM -->'} = &build_weight_tb($webdb->{'ins_weight_dom'});
$GTOOLS::TAG{'<!-- WEIGHT_CAN -->'} = &build_weight_tb($webdb->{'ins_weight_can'});
$GTOOLS::TAG{'<!-- WEIGHT_INT -->'} = &build_weight_tb($webdb->{'ins_weight_int'});

$GTOOLS::TAG{'<!-- INS_PRICE -->'} = ($webdb->{'ins_price'})?'checked':'';

$GTOOLS::TAG{'<!-- PRICE_DOM -->'} = &build_price_tb($webdb->{'ins_price_dom'});
$GTOOLS::TAG{'<!-- PRICE_CAN -->'} = &build_price_tb($webdb->{'ins_price_can'});
$GTOOLS::TAG{'<!-- PRICE_INT -->'} = &build_price_tb($webdb->{'ins_price_int'});

##
## str is a params hash "key=value&key=value"
##
sub build_weight_tb {
	my ($str) = @_;
	my $out = '';

	if ((not defined $str) || ($str eq '')) { 
		$out = "<i>Not Configured</i>";
		}
	else {
		$out = "<table>";
		my $ref = &ZTOOLKIT::parseparams($str);
		foreach my $oz (sort { $a <=> $b; } keys %{$ref}) {

			$out .= "<tr><td>up to ".sprintf("%d# %doz",($oz/16),($oz%16))."</td><td>=</td><td>\$".sprintf("%.2f",$ref->{$oz})."</td></tr>\n";
			}
		$out .= "</table>";
		}
	return($out);
	}


sub build_price_tb {
	my ($str) = @_;
	my $out = '';

	if ((not defined $str) || ($str eq '')) { 
		$out = "<i>Not Configured</i>";
		}
	else {
		$out = "<table>";
		my $ref = &ZTOOLKIT::parseparams($str);
		$ref = fixup($ref);
		use Data::Dumper; print STDERR Dumper($ref);
		foreach my $price (sort { $a <=> $b; } keys %{$ref}) {
			$out .= "<tr><td>up to ".sprintf("\$%.2f",$price)."</td><td>pays</td><td>\$".sprintf("%.2f",$ref->{$price})."</td></tr>\n";
			}
		$out .= "</table>";
		}
	return($out);
	}


##
## designed to remove encoding in keys
##		put in there by bug in parseparams (which encoded keys, but did not decode them)
##
sub fixup {
	my ($ref) = @_;

	use URI::Escape;

	my $changed = 0;
	foreach my $k (keys %{$ref}) {
		if (URI::Escape::uri_unescape($k) ne $k) {
			$changed++;
			$ref->{URI::Escape::uri_unescape($k)} = $ref->{$k};
			delete $ref->{$k};
			}
		}
	if ($changed) { return( fixup($ref)); }
	return($ref);
	}

&GTOOLS::output('*LU'=>$LU,
	title=>'Shipping: Insurance',
	help=>'#50382',
	file=>$template_file,
	'jquery'=>1,
	header=>1,
	bc=>\@BC, msgs=>\@MSGS,
	);
