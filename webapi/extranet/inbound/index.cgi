#!/usr/bin/perl

if ($ENV{'REMOTE_ADDR'} eq '67.214.236.202') {
	## answernet
	}
elsif ($ENV{'REMOTE_ADDR'} eq '66.7.124.35') {
	## my answering
	}
elsif ($ENV{'REMOTE_ADDR'} eq '50.43.101.83') {
	## answerconnect 
	}
elsif ($ENV{'REMOTE_ADDR'} =~ /^208\.74\.184\./) {
	## zoovy
	}
elsif ($ENV{'REMOTE_ADDR'} =~ /^192\.168\./) {
	## zoovy
	}
elsif ($ENV{'REMOTE_ADDR'} =~ /^66\.240\.244/) {
	## zoovy
	}
elsif ($ENV{'REMOTE_ADDR'} =~ /^66\.134\.76/) {
	## tsi
	}
else {
	print "Content-type: text/plain\n\nPermission denied for $ENV{'REMOTE_ADDR'}\n"; exit;
	}

use lib "/httpd/modules";
use ZTOOLKIT;
use GTOOLS;
use ZOOVY;
use CGI;
use SUPPORT;
use SALES;
use strict;

my $REMOTE_USER = $ENV{'REMOTE_USER'};
if (not defined $REMOTE_USER) { $REMOTE_USER = 'extranet'; }

$GTOOLS::TAG{'<!-- HEADER -->'} = qq~
<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="STYLESHEET" type="text/css" href="standard.css">
<style>
td { font-family: arial, sans-serif; font-size: 10pt; }
div.say { background-color: #CCFFCC; font-size: 12pt; }
div.hint { background-color: #DDDDFF; font-size: 10pt; }
</style>
</head>
<body bgcolor="FFFFFF" marginwidth="0" marginheight="0" topmargin="0" leftmargin="0">
<center>
<table width="600">
<tr><td>
~;


$GTOOLS::TAG{'<!-- FOOTER -->'} = qq~
</td></tr></table>
<br>
<table width=600 bgcolor="CCCCCC">
<tr><td>
<hr>
<li><a href="index.cgi?VERB="> Back to beginning</a></a>
</td></tr>
</table>
</center>
</body>
~;

my $file = 'index.shtml';

my $q = new CGI;
my $VERB = $q->param('VERB');

my $USERNAME = $q->param('USERNAME');
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;

if ($VERB eq 'SUPPORT-SAVE') {
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	my $TICKET = int($q->param('TICKET'));
	my $MESSAGE = $q->param('message');
	my $SUBJECT = $q->param('subject');

	my $sdbh = &SUPPORT::db_support_connect();
	if ($TICKET==0) {
		if ($SUBJECT eq '') { $SUBJECT = "Ticket from call center"; }
		($TICKET) = &SUPPORT::createticket($USERNAME,DISPOSITION=>"MED",BODY=>$MESSAGE,NOTIFY=>0,SUBJECT=>$SUBJECT);
		}
	else {
#mysql> desc TICKET_FOLLOWUPS;
#+-------------+------------------+------+-----+---------+----------------+
#| Field       | Type             | Null | Key | Default | Extra          |
#+-------------+------------------+------+-----+---------+----------------+
#| ID          | int(11)          | NO   | PRI | NULL    | auto_increment |
#| MID         | int(10) unsigned | NO   |     | 0       |                |
#| PARENT      | int(11)          | NO   | MUL | 0       |                |
#| CREATED_GMT | int(10) unsigned | NO   |     | 0       |                |
#| CLOSED_GMT  | int(10) unsigned | NO   |     | 0       |                |
#| CREATEDBY   | varchar(20)      | NO   |     | 0       |                |
#| COMMENT     | mediumtext       | YES  |     | NULL    |                |
#| PUBLIC      | tinyint(4)       | NO   |     | 1       |                |
#| ACTION      | varchar(10)      | NO   |     | NULL    |                |
#+-------------+------------------+------+-----+---------+----------------+
#9 rows in set (0.00 sec)

		my $pstmt = &DBINFO::insert($sdbh,'TICKET_FOLLOWUPS',{
			ID=>0,MID=>$MID,PARENT=>$TICKET,CREATED_GMT=>$^T,CREATEDBY=>$REMOTE_USER,COMMENT=>$MESSAGE,PUBLIC=>1,ACTION=>'CC'
			});
		print STDERR $pstmt."\n";
		$sdbh->do($pstmt);
		$pstmt = "update TICKETS set DISPOSITION='MED',FOLLOWUPS=FOLLOWUPS+1,STRESS_BOUNCES=STRESS_BOUNCES+1 where ID=$TICKET limit 1";
		print STDERR $pstmt."\n";
		$sdbh->do($pstmt);
		}
	&SUPPORT::db_support_close();

	$GTOOLS::TAG{'<!-- TICKET -->'} = $TICKET;
	$VERB = 'SUPPORT-THANKS';
	}


if ($VERB eq 'SUPPORT-LOOKUP') {
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	if ($MID<=0) {
		$VERB = 'SUPPORT-LOOKUPFAIL';
		}
	else {
		$VERB = 'SUPPORT-TICKET';
		}
	}


if ($VERB eq 'SUPPORT-TICKET') {
	my $sdbh = &SUPPORT::db_support_connect();
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	my $pstmt = "select ID,SUBJECT,CREATED_GMT from TICKETS where MID=$MID /* $USERNAME */ order by ID desc limit 0,50";
	my $sth = $sdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($id,$subject,$createdgmt) = $sth->fetchrow() ) {
		if ($subject eq '') { $subject = "unknown subject"; }
		my ($created) = &ZTOOLKIT::pretty_date($createdgmt);
		$GTOOLS::TAG{'<!-- TICKETS -->'} .= "<option value=\"$id\">[$id] $subject $created</option>\n";
		}
	$sth->finish();
	
	&SUPPORT::db_support_close();
	}



##################################################################

if ($VERB eq 'EMPLOYEE-SAVE') {
	$VERB = 'EMPLOYEE-SUCCESS';
	my $who = $q->param('EMPLOYEE');
	if ($who eq '') { $who = 'billing'; }

	open MH, "|/usr/sbin/sendmail -t";
	print MH "From: $REMOTE_USER\@zoovy.com\n";
	print MH "To: $who\@zoovy.com\n";
	print MH "Subject: Message from $REMOTE_USER via Extranet\n\n";
	print MH "Username: ".$q->param('username')."\n";
	print MH "Caller: ".$q->param('caller')."\n";
	print MH "Phone: ".$q->param('phone')."\n";
	print MH "Email: ".$q->param('email')."\n";
	print MH $q->param('message');
	close MH;
	}

if (($VERB eq 'EMPLOYEE') || ($VERB eq 'EMPLOYEE-EXISTING')) {
	my $sdbh = &SALES::db_sales_connect();
	my $pstmt = " select USERNAME,FULLNAME from EMPLOYEES order by FULLNAME";
	my $sth = $sdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($u,$fn) = $sth->fetchrow() ) {
		$GTOOLS::TAG{'<!-- EMPLOYEES -->'} .= "<option value=\"$u\">$fn</option>\n";
		}
	$sth->finish();
	&SUPPORT::db_support_close();
	}


#################################################################

if ($VERB eq 'SALES-SAVE') {
	$VERB = 'SALES-SUCCESS';
	my $who = $q->param('EMPLOYEE');
	if ($who eq '') { $who = 'sales'; }

	open MH, "|/usr/sbin/sendmail -t";
	print MH "From: $REMOTE_USER\@zoovy.com\n";
	print MH "Cc: info\@zoovy.com\n";
	print MH "To: $who\@zoovy.com\n";
	print MH "Subject: Message from $REMOTE_USER via Extranet\n\n";
	print MH "Caller: ".$q->param('caller')."\n";
	print MH "To: $who\n";
	print MH "Phone: ".$q->param('phone')."\n";
	print MH $q->param('message');
	close MH;
	}

if ($VERB eq 'SALES') {
	my $sdbh = &SALES::db_sales_connect();
	my $pstmt = " select USERNAME,FULLNAME from EMPLOYEES where IS_SALES>0 order by FULLNAME";
	my $sth = $sdbh->prepare($pstmt);
	$sth->execute();
	while ( my ($u,$fn) = $sth->fetchrow() ) {
		$GTOOLS::TAG{'<!-- SALES_EMPLOYEES -->'} .= "<option value=\"$u\">$fn</option>\n";
		}
	$sth->finish();
	&SUPPORT::db_support_close();
	}

if ($VERB ne '') {
	$file = lc($VERB).'.shtml';	
	}

&GTOOLS::output(file=>$file,header=>1);
