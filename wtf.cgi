#!/usr/bin/perl

use strict;

print "Content-type: text/html; charset=utf8;\n\n";

use lib "/httpd/modules";
use DBINFO;
use ZOOVY;

use CGI;
my $q = new CGI;
my $value = &ZOOVY::incode($q->param('x'));

print "<form action=\"\">";
print "<input type=\"hidden\" value=\"".time()."\">";
print qq~<input type="textbox" name="x" value="$value">~;
print qq~<input type="submit">~;
print "</form>";
print "X: $value<br>\n";

my $dbh = &DBINFO::db_zoovy_connect();
my $pstmt = "delete from TEMP";
$dbh->do($pstmt);
my $pstmt = &DBINFO::insert($dbh,'TEMP',{x=>$value},sql=>1);
$dbh->do($pstmt);

my ($value) = $dbh->selectrow_array("select * from TEMP");
print "DB: $value<br>\n";
&DBINFO::db_zoovy_close();
