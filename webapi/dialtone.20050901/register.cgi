#!/usr/bin/perl

use lib "/httpd/modules";
require DIALTONE;
require ZAUTH;
use strict;

my $q = new CGI;

my $USER = $q->param('USERNAME');
my $PASS = $q->param('PASSWORD');
my $CUID = $q->param('CUID');
my $V = $q->param('VERSION');

my $MESSAGE = '';
my ($MERCHANT,$LUSER) = split(/\*/,$USER,2);
if ($LUSER eq '') { $MESSAGE = 'Login user was not set'; }
elsif (not &ZAUTH::get_user_password($USER,$PASS)) { $MESSAGE = 'User/Password incorrect'; }
else {
	my $dbh = &DBINFO::db_zoovy_connect();
	my $MID = &ZOOVY::resolve_mid($MERCHANT);
	my $pstmt = "update ZUSER_LOGIN set DT_CUID=".$dbh->quote($CUID).",DT_REGISTER_GMT=".time()." where MID=$MID and LUSER=".$dbh->quote($LUSER)." limit 1";
	$dbh->do($pstmt);
	&DBINFO::db_zoovy_close();
	}

#+--------------------+----------------------+------+-----+---------+----------------+
#| UID                | smallint(5) unsigned |      | PRI | NULL    | auto_increment |
#| MID                | int(11)              |      | MUL | 0       |                |
#| MERCHANT           | varchar(20)          |      | MUL |         |                |
#| LUSER              | varchar(20)          |      |     |         |                |
#| FULLNAME           | varchar(50)          |      |     |         |                |
#| JOBTITLE           | varchar(50)          |      |     |         |                |
#| EMAIL              | varchar(60)          |      |     |         |                |
#| PHONE              | varchar(20)          |      |     |         |                |
#| CREATED_GMT        | int(11)              |      |     | 0       |                |
#| LASTLOGIN_GMT      | int(11)              |      |     | 0       |                |
#| LOGINS             | int(10) unsigned     |      |     | 0       |                |
#| IS_CUSTOMERSERVICE | enum('Y','N')        | YES  |     | NULL    |                |
#| IS_ADMIN           | enum('Y','N')        | YES  |     | NULL    |                |
#| EXPIRES_GMT        | int(11)              |      |     | 0       |                |
#| FLAG_SETUP         | int(11)              |      |     | 0       |                |
#| FLAG_PRODUCTS      | int(11)              |      |     | 0       |                |
#| FLAG_ORDERS        | int(11)              |      |     | 0       |                |
#| FLAG_MANAGE        | int(11)              |      |     | 0       |                |
#| FLAG_ZOM           | int(10) unsigned     |      |     | 0       |                |
#| FLAG_ZWM           | int(10) unsigned     |      |     | 0       |                |
#| PASSWORD           | varchar(20)          |      |     |         |                |
#| DT_CUID            | varchar(128)         |      |     |         |                |
#| DT_REGISTER_GMT    | int(11)              |      |     | 0       |                |
#| DT_LASTPOLL_GMT    | int(11)              |      |     | 0       |                |
#+--------------------+----------------------+------+-----+---------+----------------+


my %output = ();
$output{'USERNAME'} = $USER;
if ($MESSAGE ne '') {
	$output{'STATUS'} = 'FAIL';
	$output{'MESSAGE'} = $MESSAGE;	
	}
else {
	$output{'STATUS'} = 'SUCCESS';
	$output{'CUID'} = $CUID;
	}

&DIALTONE::output(\%output);

## return:
#STATUS=SUCCESS|FAIL
#MESSAGE=reason why denied.
#USERNAME=


