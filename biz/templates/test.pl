#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use Data::Dumper;

      my $mkts = 2048;
      my $bits = {}; # a hash keyed by DST (ex: AMZ, EBAY, etc.)
      if ($mkts ne '') {
         foreach my $id (@{&ZOOVY::bitstr_bits($mkts)}) {
            my $intref = &ZOOVY::fetch_integration(id=>$id);
            $bits->{"#$id"}++;      ## add #1 or #10
            $bits->{$intref->{'dst'}}++; ## add EBAY so we can reference by pnuemonic
            }
         }
		print Dumper($bits);


die();


use Date::Calc;

# calc_rebate
# returns an array 
#  first element is an amount to credit for the current month (positive number) in dollars
#  second element is a description of the credit suitable for posting to the transaction table.
sub calc_rebate
{
	($AMOUNT) = @_;

	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday) = localtime();


 	# make months go from 1 to 12
 	$mon += 1;
	# make days go from 1 to ..
	$mday += 1;

	# calc the total number of days in this (the current) month
	$daysmon = Date::Calc::Days_in_Month($year+1900, $mon);
	$credit = ($mday / $daysmon) * $AMOUNT;

	# get the pretty text version of the month
	$month = Date::Calc::Month_to_Text($mon);
		
	return(sprintf("%.2f",$credit),"REBATE: $month ".($year+1900)." ($mday of $daysmon days)");
}

@ar = &calc_rebate(19.95);
print @ar[0]."\n";
print @ar[1]."\n";