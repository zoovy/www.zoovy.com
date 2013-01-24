#!/usr/bin/perl

##
## This is called via AJAX to quickly resolve a given category name
##

use lib "/httpd/modules";
use SYNDICATION::CATEGORIES;
use CGI;

print "Content-type: text/plain\n\n";
# print time()."\n\n";

my $q = CGI->new();

my ($MKT) = $q->param('MKT');
my ($CATID) = $q->param('CATID');

my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad($MKT);
my ($inforef) = SYNDICATION::CATEGORIES::CDSInfo($CDS,$CATID);

#use Data::Dumper; print STDERR Dumper($inforef);

#if ($inforef->{'Parent'}==-1) { $inforef->{'Path'} = '** INVALID **'; }
print $inforef->{'Path'}."\n";
print STDERR "$inforef->{'Path'}\n";