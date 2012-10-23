#!/usr/bin/perl

use CGI::Lite;
my $cgi = new CGI::Lite;


$ZOOVY::cgiv = $cgi->parse_form_data;
$ZOOVY::cookies = $cgi->parse_cookies;


use Data::Dumper;
print STDERR Dumper($ZOOVY::cgiv);

print "Content-type: text/plain\n\n".Dumper($ZOOVY::cgiv);
