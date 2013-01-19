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
use Data::Dumper;
use URI::Escape;

my @MSGS = ();

#my ($LU) = LUSER->authenticate(flags=>'_M&16');
my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


my ($VERB) = $ZOOVY::cgiv->{'VERB'};


my ($location) = $ZOOVY::cgiv->{'location'};

print STDERR "Found items : ".$ZOOVY::cgiv->{'items'}."\n";
$ZOOVY::cgiv->{'items'} = URI::Escape::uri_unescape($ZOOVY::cgiv->{'items'});

my @lines = split(/[\n\r]+/,$ZOOVY::cgiv->{'items'});


my $output = '';
my @skus = ();

## location required to Update Location
if ($VERB eq 'UPDATE') {

	#push @MSGS, "INFO|LUSER: trying to find out if $LUSERNAME is an updater";

	if($location eq '') {
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

		my ($qty,$res,$oldlocation,$RESULT) = ();
		if (not defined $SKU) {
			$RESULT = 'MISS';
			push @MSGS, "ERROR|Could not find $item";
			}
		else {
			$RESULT = 'HIT';
			my ($P) = PRODUCT->new($USERNAME,$SKU);

			push @skus, $SKU;
 
			## has inv option or assembly, add children
			if ($SKU !~ /:/ && $P->has_variations('inv')) {
				push @MSGS, "INFO|Found PID with inventorable options";
				foreach my $set (@{$P->list_skus()}) {
					push @skus, $set->[0]; 
					}
				}
			
			## go thru all the SKUs
			foreach my $SKU (@skus) {
				($qty,$res,$oldlocation) = &INVENTORY::fetch_incremental($USERNAME,$SKU);

				## UPDATE
				if ($VERB eq 'UPDATE') {
					&INVENTORY::set_location($USERNAME,$SKU,$location);
					$output .= "<tr><td>$SKU</td><td>$location</td><td>$qty</td></tr>";
					my @AR = ($RESULT,&ZTOOLKIT::pretty_date(time(),1),$LUSERNAME,$item,$SKU,$location,$oldlocation,$qty,$res);
					print F join("\t",@AR)."\n";
					}
				## DISPLAY
				elsif ($VERB eq 'DISPLAY') {
					$output .= "<tr><td>$SKU</td><td>$oldlocation</td><td>$qty</td></tr>";
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


## only add location field to UPDATE or verb = ''
if ($VERB eq 'UPDATE' || $VERB eq '') {
	$GTOOLS::TAG{'<!-- LOCATION_FIELD -->'} =    qq~
	<td>LOCATION: </td>
   <td><input type="textbox" name="location" value=$ZOOVY::cgiv->{'location'}></td>~;

	
	$GTOOLS::TAG{'<!-- COUNTER_VERB_URL -->'} = "/biz/manage/inventory/index.cgi?VERB=DISPLAY&items=".URI::Escape::uri_escape($ZOOVY::cgiv->{'items'});
	$GTOOLS::TAG{'<!-- COUNTER_VERB -->'} = "DISPLAY";
	

	## default to use UPDATE button
	$VERB = "UPDATE";
	}
## DISPLAY
else {
	$GTOOLS::TAG{'<!-- COUNTER_VERB_URL -->'} = "/biz/manage/inventory/index.cgi?items=".URI::Escape::uri_escape($ZOOVY::cgiv->{'items'});
	$GTOOLS::TAG{'<!-- COUNTER_VERB -->'} = "UPDATE";
	}



$GTOOLS::TAG{'<!-- VERB -->'} = $VERB;

## add header to output
if ($output ne '') { 
	$output = qq~<tr><th>SKU</th><th>Location</th><th>QTY</th></tr>~ . $output ;
	}
$GTOOLS::TAG{'<!-- OUTPUT -->'} = $output; 

my @TABS = ();
push @TABS, { name=>"Welcome", link=>"/biz/manage/inventory/index.cgi?VERB=", selected=>($VERB eq '')?1:0, };
push @TABS, { name=>"Cycle Count", link=>"/biz/manage/inventory/index.cgi?VERB=CYCLECOUNT", selected=>($VERB eq 'SUBSCRIBER-LISTS')?1:0, };
push @TABS, { name=>"Update", link=>"/biz/manage/inventory/index.cgi?VERB=Update", selected=>($VERB eq 'CAMPAIGNS')?1:0, };

&GTOOLS::output(file=>'index.shtml',
	tabs=>\@TABS,
	header=>1,
	msgs=>\@MSGS);
