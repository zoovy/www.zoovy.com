#!/usr/bin/perl


use strict;
use lib "/httpd/modules";
#use ZAUTH;
use AUTH;
use LUSER;
use CGI;

# ($CODE, $USERNAME, $LUSER) = &ZOOVY::verify_cookie();
my ($SERVER_NAME) = $ENV{'SERVER_NAME'};

my ($MID,$USERNAME,$LUSERNAME,$FLAGS) = LUSER->authenticate(sendto=>"/biz",scalar=>1,nocache=>1);

if ($MID>0) {
#	$dbh = &DBINFO::db_zoovy_connect();
#	print STDERR "USERNAME: $USERNAME LUSER: $LUSER\n";
#	my $pstmt = "DELETE FROM COOKIE_CACHE WHERE LUSER=".$dbh->quote($LUSERNAME)." and USERNAME=".$dbh->quote($USERNAME);
#	print STDERR $pstmt."\n";
#	$dbh->do($pstmt);
#	ZAUTH::set_session_cookie('');
#	&DBINFO::db_zoovy_close();

	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "delete from SESSIONS where MID=$MID and LUSER=".$udbh->quote($LUSERNAME);
	print STDERR "$pstmt\n";
	$udbh->do($pstmt);
	&DBINFO::db_user_close();

	&AUTH::set_zjsid_cookie('');
	}

print "Location: http://$SERVER_NAME\n\n";
