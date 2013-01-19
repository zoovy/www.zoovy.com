#!/usr/bin/perl

use strict;

use CGI;
use lib "/httpd/modules";
#require ORDER;
require CART2;

my ($q) = CGI->new();

# http://webapi.zoovy.com/webapi/check.cgi?V=123&TYPE=ORDER&USERNAME=hotnsexymama&OID=2010-10-1751

#
# http://webapi.zoovy.com/webapi/check.cgi or
# http://webapi.zoovy.com/webapi/check.pl
#
# parameters
#	V=CLIENT-VERSION
# 	TYPE=ORDER
#	USERNAME=USERNAME
#	OID=####-##-######
#	DIGEST=base64digest
#
# RESPONSE FORMAT PLAINTEXT HTTP/200 = SUCCESS
#	TS:########
#	ERR:xyz
#

my $RESPONSE = '';

# leave the digest out for the testing
my $V = $q->param('V');
my $TYPE = $q->param('TYPE');
my $USERNAME = $q->param('USERNAME');

if ($V eq '') {
	$RESPONSE = "ERR:V= is a required parameter";
	}
elsif ($USERNAME eq '') {
	$RESPONSE = "ERR:USERNAME= is a required parameter";
	}
elsif (($TYPE eq 'ORDER') && ($q->param('OID') eq '')) {
	$RESPONSE = "ERR:OID is a required parameter for TYPE=ORDER";
	}
elsif ($TYPE eq 'ORDER') {
	my ($O2) = CART2->new_from_oid($USERNAME,$q->param('OID'));
	#if (defined $err) {
	#	$RESPONSE = "ERR:ORDER ERROR/$err";
	#	}
	if (not defined $O2) {
		$RESPONSE = "ERR:ORDER was not defined";
		}
	elsif (ref($O2) ne 'CART2') {
		$RESPONSE = "ERR:ORDER did not return an object";
		}
	else {
		my $TS = $O2->in_get('flow/modified_ts');
		$RESPONSE = "TS:$TS";
		}
	}
else {
	$RESPONSE = "ERR:Unknown TYPE=$TYPE";
	}

print "Content-type: text/plain\n\n";
print "$RESPONSE\n";

