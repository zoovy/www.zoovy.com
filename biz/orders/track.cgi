#!/usr/bin/perl

use lib "/httpd/modules";
require ZSHIP;
require GTOOLS;
require ZOOVY;
require LUSER;
use CGI;
use strict;

my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;

my $ID = $q->param('ID');
my $CMD = $q->param('CMD');
my @MSGS = ();
$GTOOLS::TAG{"<!-- ID -->"} = $ID;

if ($ID eq '') { 
	$CMD = 'ERROR'; 
	print "Content-type: text/plain\n\n";
	print "Did not receive order id in CGI params - please contact Zoovy technical support\n\n";
	exit;
	}

require CART2;
my ($O2) = CART2->new_from_oid($USERNAME,$ID);

if ($CMD eq 'SAVE') {
	my $counter = 0;
	my $tracking = $O2->tracking();
	my $changed=0;
	for ($counter=scalar(@{$tracking})-1;$counter>=0;--$counter) {
		my $trkref = $tracking->[$counter];
		next if (not defined $trkref);
		if (defined $q->param('delete-'.($trkref->{'track'}))) {
			#delete $tracking->[$counter];
			$trkref->{'void'} = time();
			$changed++;
			}
		}

	my $method = $q->param('method');
	my $value = $q->param('value');	## tracking number
	my $actualwt = $q->param('actualwt');
	my $notes = $q->param('notes');
	my $cost = $q->param('cost');
	$cost =~ s/\$//g;		## take out any dollar signs
	$cost = sprintf("%.2f",$cost); ## adjust to 2 decimal places
	$value =~ s/[^\w-]+//g;
	if ($value ne '') {
		$O2->set_tracking($method,$value,$notes,$cost,$actualwt);
		$changed++;
		}

	if ($changed) {
		$O2->order_save();
		}
	push @MSGS, "<div class='success'>Order Tracking ID's have been added/updated!</div>\n";
	}

my $template_file = "track.shtml";

my $c = '';
foreach my $trkref (@{$O2->tracking()}) {
	my ($method, $value) = ($trkref->{'carrier'},$trkref->{'track'});
	my $notes = $trkref->{'notes'};
	my $cost = $trkref->{'cost'};
	my $actualwt = $trkref->{'actualwt'};

	next if ($value eq '');
	## skip deleted/hidden/voided tracking numbers
	## 	we're keeping all numbers per uPick terms/conditions

	if ($trkref->{'void'} > 0) {
		$c .= "<tr style='text-decoration: line-through'>";
		$c .= "<td>&nbsp;</td>";
		$c .= "<td><b>VOIDED</b></td>";
		}
	else {
		$c .= "<tr>";
		$c .= "<td>&nbsp;</td>";
		$c .= "<td><input type=\"checkbox\" name=\"delete-$value\"></td>";
		}


	my $shipref = &ZSHIP::shipinfo($trkref->{'carrier'});

	$c .= "<td>$shipref->{'method'}</td>";
	$c .= "<td>$trkref->{'track'}</td>";
	if ($trkref->{'track'} eq '') {
		$c .= "<td bgcolor='FFFFFF'>Not Provided</td>";
		}
	else {
		my ($link,$text) = &ZSHIP::trackinglink($shipref,$trkref->{'track'});
		$c .= "<td bgcolor='FFFFFF'><a target=\"_blank\" href=\"$link\">$text</a></td>";
		}		
	$c .= "</tr>";

	if ($actualwt || $cost || $notes) {
		$c .= "<tr><td>&nbsp;</td><td>&nbsp;</td><td colspan='4'>";
		if ($cost) { $c .= "Shipping Cost: $cost<br>"; }
		if ($actualwt) { $c .= "Actual Weight: ".$actualwt."<br>"; }
		if ($notes) { $c .= "Shipping Notes: ".$notes."<br>"; }
		$c .= "</td></tr>";
		}

	}

if ($c eq '') {
	$c = "<tr bgcolor='white'><td></td><td colspan='3'><i>Sorry, no tracking information is available.</td></tr>";
	}

$GTOOLS::TAG{"<!-- CONTENTS -->"} = $c;
&GTOOLS::output(msgs=>\@MSGS,header=>1,file=>$template_file);

