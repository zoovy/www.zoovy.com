#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use GT;
#use DBINFO;
use STATS;
use ZOOVY;
use ZTOOLKIT;
$q = new CGI;

$q = new CGI;
my $sdbh = &STATS::db_stats_connect();
($USERNAME) = &ZOOVY::authenticate("/biz");

$ACTION = $q->param('ACTION');

$qtUSERNAME = $sdbh->quote($USERNAME);

if ($ACTION eq 'RESET')
	{
	$template_file = 'reset.shtml';
	}

if ($ACTION eq 'CONFIRM')
	{
	# $pstmt = "delete from STATISTICS_REFER where USERNAME=$qtUSERNAME";
	$MID = &ZOOVY::resolve_mid($USERNAME);
	$TB = &STATS::resolve_tb($USERNAME,'STATISTICS_REFER');
	$pstmt = "delete from $TB where MID=$MID";
	print STDERR $pstmt."\n";
	$sdbh->do($pstmt);
	$ACTION = '';
	}


if ($ACTION eq '')
	{

	# build the list of most popular products by view
	$MID = &ZOOVY::resolve_mid($USERNAME);
	$TB = &STATS::resolve_tb($USERNAME,'STATISTICS_REFER');
	$pstmt = "select REFER,MAGIC_DAY,COUNT from $TB where MID=$MID order by ID desc";
	# $pstmt = "select REFER,MAGIC_DAY,COUNT from STATISTICS_REFER where USERNAME=$qtUSERNAME order by ID desc";
	$sth = $sdbh->prepare($pstmt);
	$sth->execute;
	$c = "";
	$counter = 0;
	while (($REFER, $MAGIC_DAY, $COUNT) = $sth->fetchrow())
		{
		$MAGIC_DAY = &ZTOOLKIT::pretty_date($MAGIC_DAY*86400);
		$c .= "<tr><td>$MAGIC_DAY</td><td>$REFER</td><td align='center'>$COUNT</td></tr>";
		}
	$sth->finish;
	$GT::TAG{"<!-- REFERRER -->"} = $c;
	$template_file = "index.shtml";
	}


print $q->header();
&GT::print_form("",$template_file);

&STATS::db_stats_close();
