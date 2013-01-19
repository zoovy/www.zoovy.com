#!/usr/bin/perl

use lib "/httpd/modules";
use ZPAY::QBMS;

my $xml = '';
read(STDIN, $xml, $ENV{'CONTENT_LENGTH'});
if ($xml ne '') {

	my $xmlout = &ZPAY::QBMS::make_call($xml);
	
	open F, ">/tmp/proxy.xml";
	print F $xml;
	print F "--------------------------------------------------\n";
	print F $xmlout;
	close F;

	print "Content-type: application/x-qbmsxml\n\n";
	print $xmlout;
	}
