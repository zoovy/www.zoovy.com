#!/usr/bin/perl

use XML::Simple;

require XML::SAX::Simple;
require IO::String;

use Data::Dumper;

open F, "<test3";
while (<F>) { $DATA .= $_; }
close F;

my $io = IO::String->new($DATA);
my $ref = eval { XML::SAX::Simple::XMLin($io,ForceArray=>1,ContentKey=>'_content'); };
if ($@) { $ERROR = $@; }

print Dumper($ref);


                  