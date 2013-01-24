#!/usr/bin/perl

use strict;
use CGI;
use lib "/httpd/modules";
use DBINFO;


my $SUCCESS = 0;
my $q = new CGI;
my ($VERB) = $q->param('VERB');
my ($DOMAIN) = $q->param('DOMAIN');

my $zdbh = &DBINFO::db_zoovy_connect();
if ($VERB eq 'LIVE') {
	my $pstmt = "update DOMAINS set STATUS=1,LIVE_GMT=unix_timestamp(now()) where DOMAIN=".$zdbh->quote($DOMAIN);
	if (defined $zdbh->do($pstmt)) {
		$SUCCESS++;
		}
	}
&DBINFO::db_zoovy_close();

print "Content-type: text/plain\n\n";
print "SUCCESS:$SUCCESS\n";
