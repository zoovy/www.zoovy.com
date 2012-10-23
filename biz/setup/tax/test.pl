#!/usr/bin/perl

$start = '92014'; $end = '92102';

foreach my $zip ($start..$end) {
	push @zips, sprintf("%05d",$zip);
	}

## ZIP CODE REDUX: lets see if we can summarize any of those zip codes
my %tmp = ();
foreach my $zip (@zips) { $tmp{ "$zip" }++; }
foreach my $zip (@zips) {
	## look for numbers ending in a zero
	next unless (substr($zip,-1) eq '0');
	## we summarize by tens, so drop last digit
	$zip = substr($zip,0,-1);
	## okay make sure we've got a full set of 0-9
	my $missed = 0;
	foreach my $i (0..9) {
		if (not defined $tmp{ "$zip$i" }) { $missed++; }
		}
	next if ($missed);
	## we've got a full set so add a summary and then remove the set
	$tmp{"$zip*"}++;
	foreach my $i (0..9) { delete $tmp{"$zip$i"}; }
	}
@zips = sort keys %tmp;

use Data::Dumper;
print Dumper(\@zips);