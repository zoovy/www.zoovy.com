#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;

my $dbh = DBI->connect($DBINFO::MYSQL_DSN,$DBINFO::MYSQL_USER,$DBINFO::MYSQL_PASS); 

$x = 0;
srand(time());
while ($x++ < 10000)
{
  $pstmt = "insert into ttable values(0,from_unixtime(unix_timestamp(now())-".int(rand($x)*1000)."),0)\n";
  # print $pstmt;
  print ".";
  if ($x % 60 == 0) { print "\n"; }
  $dbh->do($pstmt);
}

$dbh->disconnect;
