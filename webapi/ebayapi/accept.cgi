#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use URI::Escape;

## stupid #$%^&* ebay requires we pass a secure URL.
$q = new CGI;

my $PROFILE = $q->param('p');

$uri = $ENV{'REQUEST_URI'};
if ($uri =~ /reject/) {
	print "Location: http://www.zoovy.com/biz/setup/ebay/index.cgi?ACTION=HANDOFF&USERNAME=".$q->param('m')."&p=$PROFILE&eb=".URI::Escape::uri_escape($q->param('eb'))."&sb=".$q->param('sb')."&ERROR=eBay+Rejected+Login\n\n";
	}
elsif ($uri =~ /accept/) {
	print "Location: http://www.zoovy.com/biz/setup/ebay/index.cgi?ACTION=SETTOKEN&USERNAME=".$q->param('m')."&p=$PROFILE&eb=".URI::Escape::uri_escape($q->param('eb'))."&sb=".$q->param('sb')."&ebaytkn=".URI::Escape::uri_escape($q->param('ebaytkn'))."&tknexp=".URI::Escape::uri_escape($q->param('tknexp'))."\n\n";
	}
else {
	use Data::Dumper;
	print "Content-type: text/plain\n\n";
	print Dumper($q);
	}