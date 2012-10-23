#!/usr/bin/perl


@x = (
	{ id=>1, name=>'id1' },
	{ id=>4, name=>'id4' },
	{ id=>1000, name=>'id1000' },
	{ id=>3, name=>'id3' },
	{ id=>5, name=>'id5' },
	{ id=>5, name=>'id5b' },
	{ id=>5, name=>'id5c' },
	{ id=>2, name=>'id2' },
	);


my @y = sort { ($a->{'id'} <= $b->{'id'})?-1:1 } @x;

use Data::Dumper;
print Dumper(\@x);
print Dumper(\@y);



exit;

use lib "/httpd/modules";
use ZPAY::GOOGLE;
use ZWEBSITE;

$USERNAME = 'google';

				my $gco = &ZPAY::GOOGLE::buildGCO($USERNAME);
				require Google::Checkout::Command::AddMerchantOrderNumber;		
				my $add_merchant_order = Google::Checkout::Command::AddMerchantOrderNumber->new(
                         order_number          => '265568456959908',
                         merchant_order_number => $ORDERID);
				my $run_diagnose = 1;
				my $response = $gco->command($add_merchant_order, $run_diagnose);

use Data::Dumper;
print Dumper($response);
