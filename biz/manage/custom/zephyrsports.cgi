#!/usr/bin/perl

use strict;
use lib "/httpd/modules";

##
## custom code for zephyrsports
## - input SKU/UPC/MFG_ID and new location (of SKU)
## - if the process finds the SKU, it will update the inv location
##

use LUSER;
use ZOOVY;
use INVENTORY;
use GTOOLS;
use PRODUCT::BATCH;
use POGS;
use Data::Dumper;
use URI::Escape;

my @MSGS = ();

#my ($LU) = LUSER->authenticate(flags=>'_M&16');
my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


my ($VERB) = $ZOOVY::cgiv->{'VERB'};


my ($location) = uc($ZOOVY::cgiv->{'location'});

print STDERR "Found items : ".$ZOOVY::cgiv->{'items'}."\n";
$ZOOVY::cgiv->{'items'} = URI::Escape::uri_unescape($ZOOVY::cgiv->{'items'});

my @lines = split(/[\n\r]+/,$ZOOVY::cgiv->{'items'});


my $output = '';
my @skus = ();

## location required to Update Location
if ($VERB eq 'UPDATE') {

	## yes, yes... we will move this to file bob can edit at some point
	my @updaters = (
		'bob',
		'bob2',
		'rpm',
		'tholley',
		'mmoore',
		'apatron',
		'warehouse',
		'dramirez',
		'clinman',
		'raguilera',
		'jvalles',
		'randy',
		'admin',
		'dcruz',
		## added 2011-10-03
		'warehouse2',
		'warehouse3',
		'warehouse4',
		);

	#push @MSGS, "INFO|LUSER: trying to find out if $LUSERNAME is an updater";
	my $found = 0;
	foreach my $luser (@updaters) {
		if (uc($luser) eq uc($LUSERNAME)) {
			$found++;
			last;
			}
		}

	if ($found == 0 ) {
		$VERB = 'DISPLAY';
		push @MSGS, "WARN|LUSER: $LUSERNAME is not an updater";
		}

	if ($location eq '') {
		push @MSGS, "ERROR|Location is a required field";
		@lines = ();
		}
	## create log file
	my $userpath = &ZOOVY::resolve_userpath($USERNAME);
	open F, ">>$userpath/IMAGES/really-spiffy-inventory-location-updates.csv";

	}
	

## go thru SKUs
if ($VERB eq 'DISPLAY' || $VERB eq 'UPDATE') {
	foreach my $line (@lines) {
		my $item = $line;
		$item =~ s/^[\s]+//gs;
		$item =~ s/[\s]+$//gs;
		$item =~ s/[\n\r]+//gs;
		$item = uc($item);

		if ($item eq '') {
			push @MSGS, "WARN|SKU, UPC or MFG_ID must be provided";
			}	
		my $SKU = undef;
		if (&ZOOVY::productidexists($USERNAME,$item)) {
			$SKU = $item;
			}
		if (not defined $SKU) {
			($SKU) = @{&PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:prod_upc',$item)};
			}	
		if (not defined $SKU) {
			($SKU) = @{&PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:prod_mfgid',$item)};
			}	
		if (not defined $SKU) {
			($SKU) = INVENTORY::resolve_sku($USERNAME,'META_UPC',$item);
			}
		if (not defined $SKU) {
			($SKU) = INVENTORY::resolve_sku($USERNAME,'META_MFGID',$item);
			}

		@skus = ();

		my ($qty,$res,$oldlocation,$RESULT) = ();
		if (not defined $SKU) {
			$RESULT = 'MISS';
			push @MSGS, "ERROR|Could not find $item";
			}
		else {
			$RESULT = 'HIT';
			my ($P) = PRODUCT->new($USERNAME,$SKU);

			# my ($prodref) = ZOOVY::fetchproduct_as_hashref($USERNAME,$SKU);
			#push @MSGS, "INFO|POGS: ".Dumper($prodref);
			
			push @skus, $SKU;
 
			## has inv option or assembly, add children
			if ($SKU =~ /:/) { 
				push @MSGS, "INFO|Found PID with inventorable options";
				foreach my $set (@{$P->list_skus('verify'=>1)}) {
					push @skus, $set->[0];
					}
				}
			
			## go thru all the SKUs
			foreach my $SKU (@skus) {
				($qty,$res,$oldlocation) = &INVENTORY::fetch_incremental($USERNAME,$SKU);

				if ($VERB eq 'UPDATE') {
					## UPDATE
					if ($oldlocation ne $location) {
						&INVENTORY::set_location($USERNAME,$SKU,$location);
						}
					$output .= "<tr><td>$SKU</td><td>$oldlocation</td><td>$location</td><td>$qty</td></tr>";
					my @AR = ($RESULT,&ZTOOLKIT::pretty_date(time(),1),$LUSERNAME,$item,$SKU,$location,$oldlocation,$qty,$res);
					print F join("\t",@AR)."\n";
					}
				elsif ($VERB eq 'DISPLAY') {
					## DISPLAY
					$output .= "<tr><td>$SKU</td><td>$oldlocation</td><td></td><td>$qty</td></tr>";
					}
				}
			}
		}

	## NO SKUS
	if (scalar(@lines)==0) {
		#push @MSGS, "ERROR|You need to put in at least one SKU";
		}

	close F;
	}


## pre-fill items text area

$GTOOLS::TAG{'<!-- ITEMS -->'} = $ZOOVY::cgiv->{'items'};
#$GTOOLS::TAG{'<!-- ITEMS -->'} = join("\n",@skus);
$GTOOLS::TAG{'<!-- LOCATION -->'} = $ZOOVY::cgiv->{'location'};

## only add location field to UPDATE or verb = ''
$GTOOLS::TAG{'<!-- VERB -->'} = $VERB;

## add header to output
if ($output ne '') { 
	$output = qq~<tr><th>SKU</th><th>Old Location</th><th>New Location</th><th>QTY</th></tr>~ . $output ;
	}
$GTOOLS::TAG{'<!-- OUTPUT -->'} = $output; 



&GTOOLS::output('*LU'=>$LU,file=>'zephyrsports.shtml',header=>1,msgs=>\@MSGS);
