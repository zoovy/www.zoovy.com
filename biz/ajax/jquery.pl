#!/usr/bin/perl

use encoding 'utf8';		## tells us to internally use utf8 for all encoding
use locale;  
use utf8 qw();
use Encode qw();
use strict;	

require JSON::Syck;

print "Content-type: application/json\n\n";

my %vars = ();
$vars{'name'} = 'bob';
$vars{'time'} = 'noon';

my $json = JSON::Syck::Dump(\%vars);
print "$json\n";

1;