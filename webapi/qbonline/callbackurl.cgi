#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use CGI;
use ZWEBSITE;

use Data::Dumper;
my $q = new CGI;


## sessiontkt --
##		

open F, ">/tmp/qbms";
print F Dumper($q);
close F;

my ($USERNAME,$PRT) = split(/:/,$q->param('appdata'));
if (not defined $PRT) { $PRT = 0; }

my $APPID = $q->param('appid');
my $ConnectionTicket = $q->param('conntkt');

my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
$webdb->{'qbms_conntkt'} = $ConnectionTicket;
$webdb->{'qbms_appid'} = $APPID;
&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);

print STDERR Data::Dumper($q);

print "Content-type: text/plain\n\n";
print "Thank you, come again!\n";



