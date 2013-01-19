#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require ZTOOLKIT;
use strict;



require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @MSGS = ();


my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };
push @BC, { name=>'Handling' };

my $template_file = 'handling.shtml';

if ($FLAGS !~ /,SHIP,/) {
	$template_file = 'noaccess.shtml';
	}

my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

use Data::Dumper; print STDERR Dumper($ZOOVY::cgiv);

if ($ZOOVY::cgiv->{'ACTION'} eq 'WEIGHT_EDIT') {

	require ZSHIP;
	my $area = $ZOOVY::cgiv->{'weight_area'};
	if ($area ne '') {
		my $ref = &ZTOOLKIT::parseparams($webdb->{'hand_weight_'.$area});
		my $wt = &ZSHIP::smart_weight($ZOOVY::cgiv->{'weight_upto'});
		my $fee = $ZOOVY::cgiv->{'weight_fee'};
		if ($fee eq '') {
			delete $ref->{$wt}; 
			}
		else {
			$ref->{$wt} = $fee;
			}
		$webdb->{'hand_weight_'.$area} = &ZTOOLKIT::buildparams($ref);
		}
	$ZOOVY::cgiv->{'ACTION'} = 'SAVE';
	}

if ($ZOOVY::cgiv->{'ACTION'} eq 'SAVE') {

	$webdb->{'handling'} = $ZOOVY::cgiv->{'handling'};
	$webdb->{'hand_flat'} = ($ZOOVY::cgiv->{'flat'})?1:0;
	$webdb->{'hand_dom_item1'} = $ZOOVY::cgiv->{'dom_item1'};
	$webdb->{'hand_can_item1'} = $ZOOVY::cgiv->{'can_item1'};
	$webdb->{'hand_int_item1'} = $ZOOVY::cgiv->{'int_item1'};
	$webdb->{'hand_dom_item2'} = $ZOOVY::cgiv->{'dom_item2'};
	$webdb->{'hand_can_item2'} = $ZOOVY::cgiv->{'can_item2'};
	$webdb->{'hand_int_item2'} = $ZOOVY::cgiv->{'int_item2'};

	$webdb->{'hand_product'} = $ZOOVY::cgiv->{'product'};

	$webdb->{'hand_weight'} = ($ZOOVY::cgiv->{'weight'})?1:0;

	push @MSGS, "SUCCESS|+saved";
	$LU->log("SETUP.SHIPPING.HANDLING","Saved Settings","SAVE");	
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);	
	}


$GTOOLS::TAG{'<!-- HANDLING_0 -->'} = '';
$GTOOLS::TAG{'<!-- HANDLING_1 -->'} = '';
$GTOOLS::TAG{'<!-- HANDLING_2 -->'} = '';
$GTOOLS::TAG{'<!-- HANDLING_'.$webdb->{'handling'}.' -->'} = 'checked'; 

$GTOOLS::TAG{'<!-- HAND_FLAT -->'} = ($webdb->{'hand_flat'})?'checked':'';
$GTOOLS::TAG{'<!-- HAND_DOM_ITEM1 -->'} = $webdb->{'hand_dom_item1'};
$GTOOLS::TAG{'<!-- HAND_CAN_ITEM1 -->'} = $webdb->{'hand_can_item1'};
$GTOOLS::TAG{'<!-- HAND_INT_ITEM1 -->'} = $webdb->{'hand_int_item1'};
$GTOOLS::TAG{'<!-- HAND_DOM_ITEM2 -->'} = $webdb->{'hand_dom_item2'};
$GTOOLS::TAG{'<!-- HAND_CAN_ITEM2 -->'} = $webdb->{'hand_can_item2'};
$GTOOLS::TAG{'<!-- HAND_INT_ITEM2 -->'} = $webdb->{'hand_int_item2'};

$GTOOLS::TAG{'<!-- HAND_PRODUCT -->'} = ($webdb->{'hand_product'})?'checked':'';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_0 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_1 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_2 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_4 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_6 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_7 -->'} = '';
$GTOOLS::TAG{'<!-- HAND_PRODUCT_'.int($webdb->{'hand_product'}).' -->'} = 'checked'; 

$GTOOLS::TAG{'<!-- HAND_WEIGHT -->'} = ($webdb->{'hand_weight'})?'checked':'';

$GTOOLS::TAG{'<!-- WEIGHT_DOM -->'} = &build_weight_tb($webdb->{'hand_weight_dom'});
$GTOOLS::TAG{'<!-- WEIGHT_CAN -->'} = &build_weight_tb($webdb->{'hand_weight_can'});
$GTOOLS::TAG{'<!-- WEIGHT_INT -->'} = &build_weight_tb($webdb->{'hand_weight_int'});

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

&GTOOLS::output('*LU'=>$LU,
	help=>'#50381',
	file=>$template_file,
	header=>1,
	bc=>\@BC, msgs=>\@MSGS,
	);