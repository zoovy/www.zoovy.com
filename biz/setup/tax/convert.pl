#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use ZACCOUNT;
use ZWEBSITE;

foreach my $USERNAME (@{ZACCOUNT::list_users()}) {
	upgrade($USERNAME);
	}
#upgrade("theh2oguru");

##
## tax rule
##		type=state value=CA rate=7.00 
##		type=country value=CA rate=7.00
##		type=local value=92000-93000 rate=3.00
##
##


sub upgrade {
	my ($USERNAME) = @_;

	foreach my $prt (@{ZWEBSITE::list_partitions($USERNAME)}) {
		($prt) = split(/:/,$prt);
		print "\n\n--------------------\n$USERNAME:$prt\n";

		my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$prt);

		print "sales_tax: $webdbref->{'sales_tax'}\n";
		print "local_tax: $webdbref->{'local_tax'}\n";
		print "state_tax: $webdbref->{'state_tax'}\n";
		print "state_tax_other: $webdbref->{'state_tax_other'}\n";
		print "tax_zip: $webdbref->{'tax_zip'}\n";

		my @rules = ();
		push @rules, "# Tax Rules Upgraded by system\n";
		if ($webdbref->{'sales_tax'} eq 'off') {
			push @rules, "# Tax Rules were off during upgrade\n";
			}

		my $ZONE = '';
		my $zipspans = $webdbref->{"tax_zip"};
		my @spans = split(",",$zipspans);
		my %ZIPS = ();
		foreach my $line (@spans) {
			(my $FROMTO,my $AMOUNT,$ZONE) = split('=',$line);
			my ($FROM, $TO) = split('-',$FROMTO);
			if ($ZONE ne '') {
				push @rules, "# $ZONE";
				}
			push @rules, sprintf("zipspan,%05d-%05d,$AMOUNT,0,$ZONE",$FROM,$TO);
			}

		my %STATES = ();
		my @ar	= split(",",$webdbref->{"state_tax"});	
		foreach my $line (@ar) {
			my ($key,$value) = split('=',$line);
			# int is BAD! $value = $value;
			if ($value < 0) { $value = 0; }
			
			# strip blank and invalid values.
			if ($value==0) { delete($STATES{"$key"}); }	
			if ($key && $value<100 && $value>0	) { $STATES{"$key"}=$value; }
			}
		## STATE_TAX_OTHER
		my %STATE_OTHER = ();
		my @ar	= split(",",$webdbref->{"state_tax_other"});	
		foreach my $line (@ar) {
				my ($key,$value) = split('=',$line);
				$value = int($value);
				if ($value < 0) { $value = 0; }

				# strip blank and invalid values.
				if ($value==0) { delete($STATE_OTHER{"$key"}); }	
				if ($key && $value<100 && $value>0	) { $STATE_OTHER{"$key"}=$value; }
				}
		
		foreach my $state (keys %STATES) {
			my $other = $STATE_OTHER{$state};
			$other = $other << 1;
			if ($other>0) { $other = $other+1; }
			
			push @rules, "state,$state,$STATES{$state},$other";
			}

		print join("\n",@rules);
		$webdbref->{'tax_rules'} = join("\n",@rules);
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$prt);

		sleep(0);
		}

	}


exit;


__DATA__

my $AREA_REFERENCE = "index.cgi";

# 
$GTOOLS::TAG{"<!-- SCRIPT_NAME -->"} = $AREA_REFERENCE;	
$GTOOLS::TAG{"<!-- BEGIN_ASK_STATE_TAX -->"} = "<!--";
$GTOOLS::TAG{"<!-- END_ASK_STATE_TAX -->"} = "-->";
$GTOOLS::TAG{"<!-- BEGIN_ASK_LOCAL_TAX -->"} = "<!--";
$GTOOLS::TAG{"<!-- END_ASK_LOCAL_TAX -->"} = "-->";
$GTOOLS::TAG{'<!-- BEGIN_CHARGE_SHIPPING -->'} = '<!--';
$GTOOLS::TAG{'<!-- END_CHARGE_SHIPPING -->'} = '-->';

$GTOOLS::TAG{"<!-- EXISTING LOCAL TAX -->"} = &build_current_zipspan($webdbref->{"tax_zip"});

sub build_current_zipspan {
	($SPAN) = @_;
	@ar = split(",",$SPAN);
	$RESULT = "";
	%SPECIFIED = ();
	foreach my $x (sort @ar) {
		my ($FROMTO,$AMOUNT,$ZONE) = split('=',$x);
		my ($FROM, $TO) = split('-',$FROMTO);
		if ($FROM && $TO && $AMOUNT) { 
			$RESULT .= "<tr><td valign='top'><font align='right' size='1' face='Arial,Helevetica'>$FROM</td>";
			$RESULT .= "<td valign='top'><font size='1' align='right' face='Arial, Helevetica'>$TO</td>";
			$RESULT .= "<td valign='top'><font size='1' align='right' face='Arial, Helevetica'>\%$AMOUNT</td>";
			$RESULT .= "<td valign='top'><font size='1' align='right' face='Arial, Helevetica'>$ZONE</td>";
			$RESULT .= "<td><font color='red'>";
			foreach my $y ($FROM..$TO) {
				if (defined $SPECIFIED{$y}) { $RESULT .= "WARNING: $y already specified in $SPECIFIED{$y}<br>"; }
				else { $SPECIFIED{$y} = $FROMTO; }
				}
			$RESULT .= "</font></td></tr>"; 
			} 
		}

	if ($RESULT) {
		$RESULT = "<tr><td width=50><font size='2' align='right' face='Arial, Helvetica'>From</td><td width='50'><font size='2' align='right' face='Arial, Helvetica'>To</td><td width='50'><font size='2' align='right' face='Arial, Helvetica'>Amount</td><td width='50'><font size='2' align='right' face='Arial, Helvetica'>Tax Zone</td></tr>".$RESULT;
		$RESULT = "<font size='2'><i>*Hint: To remove an entry, simply re-enter the FROM and TO zip codes with a rate of ZERO<i></font><br><table>$RESULT</table>";
		}	 

	return($RESULT);
	}





if ($webdbref->{"sales_tax"} eq "state" || $webdbref->{"sales_tax"} eq "zip") {
	my $state_tax = ();
	foreach $kv (split(/,/,$webdbref->{"state_tax"})) {
		next if ($kv eq '');
		my ($k,$v) = split(/=/,$kv);
		$state_tax{$k} = $v;
		}
	my $state_tax_other = ();
	foreach $kv (split(/,/,$webdbref->{"state_tax_other"})) {
		next if ($kv eq '');
		my ($k,$v) = split(/=/,$kv);
		$state_tax_other{$k} = $v;
		}


	my $out = '<table>';
	$out = qq~
		<table>
			<tr>
				<td><b>STATE</b></td>
				<td><b>RATE</b></td>
				<td><b>Shipping</b></td>
				<td><b>Handling</b></td>
				<td><b>Insurance</b></td>
				<td><b>Speciality</b></td>
			</tr>
		~;

	foreach $state (keys %state_tax) {
		$out .= "<tr><td>$state</td><td>$state_tax{$state}\%</td>";
		$out .= "<td align='center'>".((($state_tax_other{$state} & 1)==1)?'Yes':'No').'</td>';
		$out .= "<td align='center'>".((($state_tax_other{$state} & 2)==2)?'Yes':'No').'</td>';
		$out .= "<td align='center'>".((($state_tax_other{$state} & 4)==4)?'Yes':'No').'</td>';
		$out .= "<td align='center'>".((($state_tax_other{$state} & 8)==8)?'Yes':'No').'</td>';
		$out .= "</tr>";
		}
	$out .= "</table>";
	
	 $GTOOLS::TAG{"<!-- EXISTING STATE TAX -->"} = $out;
	 } 
else {
	 $GTOOLS::TAG{"<!-- EXISTING STATE TAX -->"} = "None Defined";
	 }


if ($webdbref->{"sales_tax"} eq "state")
	 {
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_STATE_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- END_ASK_STATE_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- SALES_TAX_OFF -->"} = "";
	 $GTOOLS::TAG{"<!-- SALES_TAX_STATE -->"} = " CHECKED ";
	$GTOOLS::TAG{"<!-- SALES_TAX_ZIP -->"} = "";
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_LOCAL_TAX -->"} = " <!-- ";
	 $GTOOLS::TAG{"<!-- END_ASK_LOCAL_TAX -->"} = " --> ";
	 } 
elsif ($webdbref->{"sales_tax"} eq "zip") {
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_STATE_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- END_ASK_STATE_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_LOCAL_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- END_ASK_LOCAL_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- SALES_TAX_OFF -->"} = "";
	 $GTOOLS::TAG{"<!-- SALES_TAX_STATE -->"} = "";
	$GTOOLS::TAG{"<!-- SALES_TAX_ZIP -->"} = " CHECKED ";
	} 
else {
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_STATE_TAX -->"} = "<!--";
	 $GTOOLS::TAG{"<!-- END_ASK_STATE_TAX -->"} = "-->";
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_LOCAL_TAX -->"} = " <!-- ";
	 $GTOOLS::TAG{"<!-- END_ASK_LOCAL_TAX -->"} = " --> ";
	 $GTOOLS::TAG{"<!-- SALES_TAX_OFF -->"} = " CHECKED ";
	 $GTOOLS::TAG{"<!-- SALES_TAX_STATE -->"} = "";
	 $GTOOLS::TAG{"<!-- SALES_TAX_ZIP -->"} = " ";
	 }


if ($webdbref->{"sales_tax"} eq "zip")
	 {
	 $GTOOLS::TAG{"<!-- BEGIN_ASK_LOCAL_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- END_ASK_LOCAL_TAX -->"} = "";
	 $GTOOLS::TAG{"<!-- LOCAL_TAX_CHECKED -->"} = " CHECKED ";
	 } else {
	 }

$GTOOLS::TAG{'<!-- TAXSHIP_STATES -->'} = $webdbref->{'taxship_states'};
# handle general parameters.


# disabled novice mode
#if (($webdbref->{"novice_mode"} eq "on") && !$q->param('novice-completed'))
#{ $template_file = "novice.shtml";	}
