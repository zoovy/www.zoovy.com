#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;

my ($q) = CGI->new();

use Data::Dumper;
print STDERR Dumper($q);

my $XML = '';
my $fh = $q->param('Filedata');
my $filename = $fh;
print STDERR "FILENAME: $filename\n";
if (not defined $fh) {
   ## Crap, not defined!
   }
elsif (defined $fh) {
   while (<$fh>) { $XML .= $_; }
   }


print STDERR Dumper($XML);

print "Content-type: text/html\n\n";
