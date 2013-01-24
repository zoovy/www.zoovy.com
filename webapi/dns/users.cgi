#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;

print "Content-type: text/plain\n\n";

my ($zdbh) = &DBINFO::db_zoovy_connect();
my $pstmt = "select MID,USERNAME,CLUSTER from ZUSERS where BILL_DAY>=0 order by MID";
my ($sth) = $zdbh->prepare($pstmt);
$sth->execute();
while ( my ($MID,$USERNAME,$CLUSTER) = $sth->fetchrow() ) {
	print "$MID|$USERNAME|$CLUSTER\n";
	}
$sth->finish();
&DBINFO::db_zoovy_close();
print "\n\n";
