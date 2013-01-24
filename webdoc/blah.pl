#!/usr/bin/perl

use lib "/httpd/modules";
use WEBDOC;
use Data::Dumper;

$wdbh = &WEBDOC::db_webdoc_connect();
$pstmt = "select ID from WEBDOC_FILES";
$sth = $wdbh->prepare($pstmt);
$sth->execute();
while ( my ($ID) = $sth->fetchrow() ) {
	my $doc = WEBDOC->new($ID);
	my $sum = $doc->summarize();

	$pstmt = "update WEBDOC_FILES set SUMMARY=".$wdbh->quote($sum)." where ID=$ID";
	print $pstmt."\n";
	$wdbh->do($pstmt);
	}
$sth->finish();


&WEBDOC::db_webdoc_close();