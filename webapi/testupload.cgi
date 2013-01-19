#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use ZOOVY;

$|++;
$q = new CGI;

open F, ">/tmp/testupload.output";
my $filename = $q->param('FILENAME');

print F "USERNAME: ".$q->param('USERNAME')."\n";
print F "PASSWORD: ".$q->param('PASSWORD')."\n";
print F "METHOD: ".$q->param('METHOD')."\n";

if (1)
{
my $BUFFER = "";
while (<$filename>)
   {
    $BUFFER .= $_; 
   }

print F "CONTENTS:\n".$BUFFER;
close F;
} else {
 print STDERR "no file received.\n";
}

print $q->header();
print "bleh!";
