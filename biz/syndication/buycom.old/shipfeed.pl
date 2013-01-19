#!/usr/bin/perl

use strict;
use Data::Dumper;
use Text::CSV_XS;
use Data::Dumper;
use lib '/httpd/modules';
use ORDER;
use ORDER::BATCH;


my $USERNAME = 'brian';

my $::csv = Text::CSV_XS->new({'sep_char'=>"\t",binary=>1});           # create a new object


## SHIP CONFIRM
print "receipt-id,receipt-item-id,Quantity,tracking-type,tracking-number,Ship-date\n";
## REFUND
print "receipt-id,receipt-item-id,refund-type,shipping-refund-amount,refund-reason,customer-note\n";
## CANCELLATION FEED
print "receipt-id,receipt-item-id,Quantity,customer-note\n";

my ($oref) = ORDER::BATCH::report($USERNAME,TS=>0);
foreach my $xref (@{$oref}) {
	my ($OID) = $xref->{'ORDERID'};

	print "OID: $OID\n";

	my $status = $csv->combine(@columns);    # combine columns into a string
	if ($status) {
		($line) = $csv->string();               # get the combined string
		}
	else {
		die($status);
		}
	}

