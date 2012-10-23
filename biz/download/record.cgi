#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use ZOOVY;
use CGI;

my $dbh = &DBINFO::db_zoovy_connect();
my ($USERNAME,$FLAGS) = &ZOOVY::authenticate();
$q = new CGI;

print STDERR "USERNAME: $USERNAME FLAGS: $FLAGS\n";
$CODE = $q->param('CODE');
$MAJOR = $q->param('MAJOR');
$MINOR = $q->param('MINOR');

my $requires = '';
if ($CODE =~ /zpm/i) {
	if ($FLAGS =~ /,ZPM(\*[\d]+)?,/) { } else { $requires = 'ZPM'; }
	}
else {
	## 
	}


$USERNAME = $dbh->quote($USERNAME);

$qtCODE = $dbh->quote($CODE);
$qtMAJOR = $dbh->quote($MAJOR);
$qtMINOR = $dbh->quote($MINOR);


$URL = $q->param('URL');

if (not defined $URL) { $URL = $CODE; }
#$URL = 'http://zidsink.simplecdn.net/'.$URL;
if ($URL !~ /^http\:\/\//) {
	# $URL = 'http://e1h1.simplecdn.net/zidsink.zoovy/'.$URL;
	$URL = 'http://s3.amazonaws.com/ZID/'.$URL;
	}
else {
	## the beta downloads page passes http://static.zoovy.com
	}


if ($requires ne '') {
	$URL = "http://www.zoovy.com/biz/configurator?VERB=DETAIL&PACKAGE=$requires";
	}
else {
	#+------------+-------------+------+-----+---------+-------+
	#| Field      | Type        | Null | Key | Default | Extra |
	#+------------+-------------+------+-----+---------+-------+
	#| DTIME      | datetime    | YES  |     | NULL    |       |
	#| USERNAME   | varchar(20) | YES  | MUL | NULL    |       |
	#| CLIENTCODE | varchar(20) | YES  |     | NULL    |       |
	#+------------+-------------+------+-----+---------+-------+
	$pstmt = "replace into DOWNLOAD_LOG (DTIME,USERNAME,CLIENTCODE) values (now(),$USERNAME,$qtCODE)";
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);
	}
#print "Content-type: text/plain\n\n";
print "Location: $URL\n\n";
print STDERR "REDIRECTED TO: $URL\n";


&DBINFO::db_zoovy_close();