#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use FUSEMAIL;

my ($dbh) = &DBINFO::db_zoovy_connect();
$pstmt = "select UID,MERCHANT,LUSER from ZUSER_LOGIN where HAS_EMAIL='N' and MERCHANT='caboots'";
$sth = $dbh->prepare($pstmt);
$sth->execute();
while ( my ($ID,$USERNAME,$LUSER) = $sth->fetchrow() ) {
	print "USER: $USERNAME LUSER: $LUSER\n";
	my ($pass) = FUSEMAIL::getpassword("$LUSER\@$USERNAME.zoovy.com");
	if (defined $pass) {
		print "PASS: $pass\n";
		$pstmt = "update ZUSER_LOGIN set HAS_EMAIL='Y' where UID=$ID";
		print $pstmt."\n";
		$dbh->do($pstmt);
		}
	}
$sth->finish();