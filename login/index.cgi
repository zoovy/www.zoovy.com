#!/usr/bin/perl

use CGI;

my ($q) = CGI->new();

my %kv = ();
$kv{'verb'} = 'login';
foreach my $k ($q->param()) {
	$kv{$k} = $q->param($k);
	}

use lib "/httpd/modules";
use ZTOOLKIT;

print STDERR "SENDING TO: /index.html?".&ZTOOLKIT::buildparams(\%kv)."\n\n";

print "Location: /index.html?".&ZTOOLKIT::buildparams(\%kv)."\n\n";

exit;
