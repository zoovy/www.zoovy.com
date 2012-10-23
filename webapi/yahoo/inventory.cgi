#!/usr/bin/perl

#
# Install (a modified version of) this program in your webserver's cgi-bin 
# directory.
#
# This demo program handles a request to return inventory information for
# .catalog=&.id=_fake_yahoo_item_&.code=_fake_yahoo_code_
# It returns the item availability information as its response.
#

require 5.001;
use strict;

my $o;
my $USERNAME;
read(STDIN,$o,$ENV{'CONTENT_LENGTH'});

if ($ENV{'REQUEST_URI'} =~ /inventory\.cgi\/(.*?)$/) {
	$USERNAME = $1;
	} else {
	print "Status: 200\n";
	print "Available: -1\n";
	print "Content-type: text/plain\n";
	print "Inventory-Message: you must supply a valid username to Zoovy.\n\n";
	exit;
	}

use lib "/httpd/modules";
use INVENTORY;
use ZWEBSITE;

my ($yahoo_sync,$yahoo_behavior) = split(',',&ZWEBSITE::fetch_website_attrib($USERNAME,'inv_yahoo'));
if (!defined($yahoo_sync)) { 
	print "Status: 200\n";
	print "Content-Type: text/plain\n";
	print "Available: -1\n";
	print "Inventory-Message: yahoo inventory synchronization not enabled with http://$USERNAME.zoovy.com\n";
	exit;
	}

my %o;
for (split(/&/,$o)) {
    $_ =~ s/\+/ /g;
    my($key,$val) = split(/=/,$_,2);
    for ($key,$val) {
        $_ =~ s/%([0-9a-fA-F][0-9a-fA-F])/chr(hex($1))/ge;
    }
    $o{$key} = $val;
}
# at this point %o contains the key's and values

use Data::Dumper;
print STDERR Dumper(\%ENV);

sub YahooFakeItem {
    my($info)=@_;
    my $itemid=$info->{".id"};


    if (defined $itemid && $itemid eq "_fake_yahoo_item_") {
        return 1;
    } else {
        return 0;
    }
}

sub GetItemAvailability {
    my($info)=@_;

    my $catalog=$info->{".catalog"};
    my $code=$info->{".code"};

    #
    # Replace this with your code to determine whether an item is in stock.
    # Return -1, if the item is unknown
    #        available quantity, if the item is valid.
    #

	my ($qtyonhand,$reserveqty) = &INVENTORY::fetch_incremental($USERNAME,$code);
	if (!defined($qtyonhand)) { return -1; }
	elsif ($yahoo_behavior eq 'actual') { return($qtyonhand); }
	elsif ($yahoo_behavior eq 'reserve') {
		return($qtyonhand-$reserveqty);
		}
	elsif ($yahoo_behavior eq 'safe') { 
		my $safe = &ZWEBSITE::fetch_website_attrib($USERNAME,'inv_safety'); 	
		$qtyonhand -= $safe;
		return($qtyonhand);
		}
	elsif ($yahoo_behavior eq 'inflate') {
		my $safe = &ZWEBSITE::fetch_website_attrib($USERNAME,'inv_safety'); 	
		if ($qtyonhand > $safe) { return($qtyonhand*10); } else { return($qtyonhand); }
		}
	return -1;


}
my($avail);

if (YahooFakeItem(\%o)) {
    $avail="-1";
} else {
    $avail=GetItemAvailability(\%o);
}
print "Status: 200\n";
print "Content-Type: text/plain\n";
print "Available: $avail\n";


if ($avail <= 0) {
 print "Inventory-Message: The item is not currently available. Please check back later.\n";
   }

print "\n";



