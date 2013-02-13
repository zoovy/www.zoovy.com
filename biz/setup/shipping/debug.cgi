#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZSHIP;
require SITE;
require CART2;
require LISTING::MSGS;
use Data::Dumper;

my @MSGS = ();

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup/index.cgi','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping/index.cgi','target'=>'_top', };
push @BC, { name=>'Debugger',link=>'/biz/setup/shipping/debug.cgi' };

my %FONTS = (
	'1'=>'<b><h2>',
	'32'=>'<font color="blue">',
	'64'=>'<font color="blue" size=-1>',
	'128'=>"<font color='#777777' size='1'><pre>",
	);

$ZSHIP::DEBUG = 1;
$ZSHIP::FIXED::DEBUG = 1;
$ZSHIP::FIXED::FEDEXAPI = 1;
$ZSHIP::FIXED::UPSAPI = 1;

my $template_file = '';
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $SITE = SITE->new($USERNAME,'PRT'=>$PRT,'*CART2'=>$SITE::CART);
$SITE::CART2 = undef;

my $lm = LISTING::MSGS->new($USERNAME);

my $CARTID = $ZOOVY::cgiv->{'CART'};
if ($ZOOVY::cgiv->{'REAL-CART'} ne '') {
	$CARTID = $ZOOVY::cgiv->{'REAL-CART'};
	}

if ($ZOOVY::cgiv->{'ACTION'} eq 'DEBUG') {
	my $SRC = $ZOOVY::cgiv->{'SRC'};
	my $ZIP = '';
	my $STATE  = '';

	require LISTING::MSGS;
	my ($lm) = LISTING::MSGS->new($USERNAME);

	my $TRACE = 0;
	$TRACE += ($ZOOVY::cgiv->{'detail_1'})?1:0;			# general trace info (always enabled)

	#	$TRACE += ($ZOOVY::cgiv->{'detail_2'})?2:0;			# detail trace info
	#	$TRACE += ($ZOOVY::cgiv->{'detail_16'})?3:0;		# shipping rules level 1
	#	$TRACE += ($ZOOVY::cgiv->{'detail_32'})?4:0;		# shipping rules detailed
	#	$TRACE += ($ZOOVY::cgiv->{'detail_128'})?5:0; 		# developer
	$lm->pooshmsg("INFO|+Setting trace level to: $TRACE (going to build cart)");

	if ($SRC eq 'ORDER') {
		## LOAD FROM ORDER
		my $orderid = $ZOOVY::cgiv->{'ORDER'};
		print STDERR "DEBUGGER USING ORDER: $ZOOVY::cgiv->{'ORDER'}\n";
		$SITE::CART2 = CART2->new_from_oid($USERNAME,$orderid);
		$SITE::CART2->msgs($lm);
		$SITE::CART2->is_debug($TRACE);
		}
	elsif ($SRC eq 'DEST') {
		## CREATE A CART
		$SITE::CART2 = CART2->new_memory($USERNAME,$PRT);
		$SITE::CART2->msgs($lm);
		$SITE::CART2->is_debug($TRACE);
		foreach my $x (1..3) {
			
			my $STID = $ZOOVY::cgiv->{'ITEM'.$x};
			next if ($STID eq '');
			my $QTY = $ZOOVY::cgiv->{'QTY'.$x};

			my ($pid,$claim,$invopts,$noinvopts,$virtual) = PRODUCT::stid_to_pid($STID);
			my ($P) = PRODUCT->new($USERNAME,$pid);
			my ($suggested_variations) = $P->suggest_variations('guess'=>1,'stid'=>$STID);
			foreach my $suggestion (@{$suggested_variations}) {
				if ($suggestion->[4] eq 'guess') {
					$lm->pooshmsg("WARN|+STID:$STID POG:$suggestion->[0] VALUE:$suggestion->[1] was guesssed (reason: not specified or invalid)");
					}
				}
			my $variations = STUFF2::variation_suggestions_to_selections($suggested_variations);
			$SITE::CART2->stuff2()->cram( $STID, $QTY, $variations, '*P'=>$P, '*LM'=>$lm );
			}	
		$SITE::CART2->in_set('ship/postal', $ZOOVY::cgiv->{'ZIP'});
		$SITE::CART2->in_set('ship/region', $ZOOVY::cgiv->{'STATE'});
		}
	elsif ($SRC eq 'CART') {
		## USE AN EXISTING CART
		if ($CARTID =~ /^c=(.*?)$/) { 
			push @MSGS, "WARN|+The prefix c= is not needed for the cartid and was removed.";
			$CARTID = $1; 
			}
		print STDERR "USING CART: $CARTID\n";
		$SITE::CART2 = CART2->new_persist($USERNAME,$PRT,$CARTID,'is_fresh'=>0);
		$SITE::CART2->msgs($lm);
		$SITE::CART2->is_debug($TRACE);
		}
	else {
		push @MSGS, 'ERROR|Please select a valid source for products/destination information';
		$SITE::CART2->new_memory($USERNAME,$PRT);
		}


	##
	## SANITY: at this point $SITE::CART is set.
	##

	if (not defined $SITE::CART2) {
		$ZOOVY::cgiv->{'ACTION'} = '';
		$template_file = 'debug.shtml';
		}
	else {

		$lm->pooshmsg("INFO|+Requesting shipmethods");
		$SITE::CART2->shipmethods('flush'=>1);
		# $SITE::CART2->__SYNC__();

		## check for dumb things in the cart

		my ($stuff2) = $SITE::CART2->stuff2();

		foreach my $item (@{$stuff2->items()}) {
			my $stid = $item->{'stid'};
			if ($item->{'virtual'} =~ /[\s]/) { $lm->pooshmsg("ERROR|+Preflight: STID[$stid] has space in supplier virtual field \"$item->{'virtual'}\""); }
			if ($item->{'%attribs'}->{'zoovy:virtual'} =~ /[\s]/) { $lm->pooshmsg("ERROR|+Preflight: STID[$stid] has space in zoovy:virtual field"); }
			if ($item->{'%attribs'}->{'zoovy:virtual'} ne $item->{'virtual'}) { $lm->pooshmsg("ERROR|+Preflight: STID[$stid] has non-matching zoovy:virtual and item.virtual (internal error!?)"); }
			}

		#foreach my $errmsg (@ERRORS) {
		#	$out .= "<div style='color: red; font-size: 20px;'>PREFLIGHT MESSAGE: $errmsg</div>\n";
		#	}


		my $out = '';
		foreach my $msg (@{$lm->msgs()}) {
			my ($d) = LISTING::MSGS::msg_to_disposition($msg);

			my $type = $d->{'_'};
			my $level = int($d->{'trace'});

			my $style = '';
			if ($type eq 'HINT') { 
				$style = 'font-size: 01pt; color: green; border: thin dashed;'; 
				}
			elsif (($type eq 'GOOD') || ($type eq 'SUCCESS') || ($type eq 'PAUSE')) { 
				$style = 'font-size: 10pt; color: blue'; 
				}
			elsif (($type eq 'ISE') || ($type eq 'FAIL') || ($type eq 'STOP') || ($type eq 'PRODUCT-ERROR')) { 
				$style = 'font-size: 12pt; color: red'; 
				}
			elsif (($type eq 'WARN') || ($type eq 'WARNING')) { 
				$style = 'font-size: 12pt; color: orange; border: thin dashed;'; 
				}
			elsif (($type eq 'DEBUG') || ($type eq 'DEV')) {
				$style = 'font-size: 8pt; color: gray;';
				}
			elsif ($type eq 'INFO') { 
				$style = 'font-size: 10pt; font-weight: bold; color: #444444;'; 
				}
			elsif ($type eq 'TITLE') { 
				$style = 'font-size: 12pt; background-color: orange; border: thin dashed; font-weight: bold; color: #000000;'; 
				}
			elsif ($type eq 'SUBTITLE') { 
				$style = 'font-size: 10pt; background-color: #FFB300; border: thin dashed; font-weight: normal; color: #444444;'; 
				}
			elsif (($type eq 'API-REQUEST') || ($type eq 'API-RESPONSE')) {
				## API-REQUEST
				## API-RESPONSE
				$style = "font-size: 8px; border: thin dashed; font-weight: normal; color: #666699;";
				$d->{'+'} = &ZOOVY::incode( $d->{'+'} );
				}
			else {
				}

			my $px = ($level*10);		
			$style = sprintf("margin-left:%dpx; $style",$px);


			$out .= "<div style=\"$style\">";
			# $out .= "[$level]";
			if ($d->{'+'} eq '') {	
				$out .= "INVALID/CORRUPT MSG '$msg'";
				}
			else {
				$out .= " $type: $d->{'+'}";
				}
			# $out .= Dumper($d);
			$out .= "</div>\n";
			}

		#foreach my $line (@{$SITE::CART->{'@DEBUG'}}) {
		#	my ($class,$level,$msg) = split(/\|/,$line,3);	
		#	$msg = &ZOOVY::incode($msg);
		#	$msg =~ s/[\n\r]+/<br>/gs;
#
#			my $style = '';
#			if ($level & 1) { $style = 'font-size: 20px; margin-top: 25px; background-color: #C0C0C0; font-weight: bold;';  } 
#			if ($level & 2) { $style = 'font-size: 20px; ';  } 
#			elsif ($level & 4) { $style = 'font-size: 16px; background-color: #F0F0F0'; }
#			elsif ($level & 8) { $style = 'font-size: 14px; font-weight: bold;'; }
#			elsif ($level & 16) { $style = 'font-size: 12px; margin-left: 20px;'; }
#			elsif ($level & 32) { $style = 'font-size: 10px; margin-left: 30px;'; }
#			elsif ($level & 64) { $style = 'font-size: 8px; font-color: blue; margin-left: 45px'; }
#			elsif ($level & 128) { $style = 'font-size: 10px; color: #FF3333; margin-left: 20px'; }
#			$out .= "<div style='$style' class=\"level$level\"><!-- level:$level -->$msg</div>\n";
#			
#			}
		$GTOOLS::TAG{'<!-- OUTPUT -->'} = $out;
		
		$out = '';
		foreach my $shipmethod (@{$SITE::CART2->shipmethods()}) {
			$out .= "<tr><td><pre>".Dumper($shipmethod)."</pre></td></tr>\n";
			}
		$GTOOLS::TAG{'<!-- RESULTS -->'} = $out;

		if ($ZOOVY::cgiv->{'detail_128'}) {
			delete $SITE::CART2->{'@DEBUG'};
			$GTOOLS::TAG{'<!-- CART -->'} = &ZOOVY::incode(Dumper($SITE::CART2));
			}
		else {
			$GTOOLS::TAG{'<!-- CART -->'} = '<i>Not displayed at this detail level.</i>';
			}
		$template_file = 'debug-output.shtml'; 
		}
	}


if ($ZOOVY::cgiv->{'ACTION'} eq '') {
	$template_file = 'debug.shtml';
	$GTOOLS::TAG{'<!-- DETAIL_2 -->'} = (defined $ZOOVY::cgiv->{'detail_2'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_16 -->'} = (defined $ZOOVY::cgiv->{'detail_16'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_32 -->'} = (defined $ZOOVY::cgiv->{'detail_32'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_128 -->'} = (defined $ZOOVY::cgiv->{'detail_128'})?'checked':'';

	$GTOOLS::TAG{'<!-- ITEM1 -->'} = $ZOOVY::cgiv->{'ITEM1'};
	$GTOOLS::TAG{'<!-- QTY1 -->'} = $ZOOVY::cgiv->{'QTY1'};
	$GTOOLS::TAG{'<!-- ITEM2 -->'} = $ZOOVY::cgiv->{'ITEM2'};
	$GTOOLS::TAG{'<!-- QTY2 -->'} = $ZOOVY::cgiv->{'QTY2'};
	$GTOOLS::TAG{'<!-- ITEM3 -->'} = $ZOOVY::cgiv->{'ITEM3'};
	$GTOOLS::TAG{'<!-- QTY3 -->'} = $ZOOVY::cgiv->{'QTY3'};
	my $DEST_ZIP = $ZOOVY::cgiv->{'ZIP'};
	$GTOOLS::TAG{'<!-- ZIP -->'} = $DEST_ZIP;
	my $STATE = $ZOOVY::cgiv->{'STATE'};
	$GTOOLS::TAG{'<!-- STATE -->'} = $STATE;
	$GTOOLS::TAG{'<!-- ORDER -->'} = $ZOOVY::cgiv->{'ORDER'};
#	my $c = '';
#	foreach my $d (%{$ZOOVY::cookies}) {
#		next if ($d !~ /-cart$/);
#		$c .= "<input type='radio' name='CART' value='$ZOOVY::cookies->{$d}'>$d ($ZOOVY::cookies->{$d})<br>";
#		}
#	if ($c eq '') { $c = '<i>Sorry, no carts were found.</i>'; }
#	$GTOOLS::TAG{'<!-- CARTS -->'} = $c;
	}

&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,
	'header'=>1,
	'title'=>'Shipping: Debugger',
	'help'=>'#50810',
	'file'=>$template_file,
	'msgs'=>\@MSGS,
	'bc'=>\@BC,
	);

