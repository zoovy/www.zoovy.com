#!/usr/bin/perl

use strict;

use CGI::Lite;

my $cgi = new CGI::Lite;
my $form = $cgi->parse_form_data;

#use Data::Dumper;
#print STDERR Dumper($form);


use lib "/httpd/modules";
require DBINFO;
#require ORDER;
#require CART2;

#my ($q) = CGI->new();
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
my $V = $form->{'V'};
my $TYPE = $form->{'TYPE'};
my $USERNAME = $form->{'USERNAME'};

if ($V eq '') {
	$RESPONSE = "ERR:V= is a required parameter";
	}
elsif ($USERNAME eq '') {
	$RESPONSE = "ERR:USERNAME= is a required parameter";
	}
elsif (($TYPE eq 'ORDER') && ($form->{'OID'} eq '')) {
	$RESPONSE = "ERR:OID is a required parameter for TYPE=ORDER";
	}
elsif ($TYPE eq 'ORDER') {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $qtOID = $udbh->quote($form->{'OID'});
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	my $TB = &DBINFO::resolve_orders_tb($USERNAME,$MID);
	my $pstmt = "select MODIFIED_GMT from $TB where ORDERID=$qtOID and MID=$MID";
	my ($TS) = $udbh->selectrow_array($pstmt);
	if (not defined $TS) {
		$RESPONSE = "ERR:ORDER was not defined";
		}
	else {
		$RESPONSE = "TS:$TS";
		}	
	&DBINFO::db_user_close();
	}
#elsif ($TYPE eq 'ORDER') {
#	my ($O2) = CART2->new_from_oid($USERNAME,$form->{'OID'});
#	#if (defined $err) {
#	#	$RESPONSE = "ERR:ORDER ERROR/$err";
#	#	}
#	if (not defined $O2) {
#		$RESPONSE = "ERR:ORDER was not defined";
#		}
#	elsif (ref($O2) ne 'CART2') {
#		$RESPONSE = "ERR:ORDER did not return an object";
#		}
#	else {
#		my $TS = $O2->in_get('flow/modified_ts');
#		$RESPONSE = "TS:$TS";
#		}
#	}
else {
	$RESPONSE = "ERR:Unknown TYPE=$TYPE";
	}

print "Content-type: text/plain\n\n";
print "$RESPONSE\n";

