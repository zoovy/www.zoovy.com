#!/usr/bin/perl

my $json_text = qq~
{"asdf":1}
{"foo":2}~;

use JSON;
my $json = JSON->new();
#print $json->encode([ { asdf=>1 }]);
$json_text = "[$json_text]";
$perl_scalar = eval { $json->decode($json_text) } or die($@);

use Data::Dumper;
print Dumper($perl_scalar);