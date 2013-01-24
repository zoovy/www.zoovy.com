#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;

my $q = new CGI;

use Data::Dumper;

open F, ">/tmp/qbonline.statuschange";
print F Dumper($q);
close F;

print "Content-type: text/xml\n\n";
