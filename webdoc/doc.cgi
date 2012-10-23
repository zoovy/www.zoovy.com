#!/usr/bin/perl

use lib "/httpd/modules";

print "Content-type: text/html\n\n";
use Data::Dumper;
print Dumper(\%ENV);
