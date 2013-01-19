#!/usr/bin/perl

use strict;

use CGI;

use lib "/httpd/modules";
use SUPPORT;
use GTOOLS;
use Data::Dumper;

my $q = new CGI;

my $VERB = $q->param('VERB');

#+------------------+-----------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| Field            | Type                                                                                          | Null | Key | Default             | Extra          |
#+------------------+-----------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| ID               | int(11)                                                                                       | NO   | PRI | NULL                | auto_increment |
#| CREATED_GMT      | int(10) unsigned                                                                              | NO   |     | 0                   |                |
#| OPENED_GMT       | int(10) unsigned                                                                              | NO   |     | 0                   |                |
#| CLOSED_GMT       | int(10) unsigned                                                                              | NO   |     | 0                   |                |
#| CUSTOMER         | varchar(50)                                                                                   | NO   | MUL | NULL                |                |
#| USERNAME         | varchar(20)                                                                                   | NO   |     | NULL                |                |
#| LUSER            | varchar(10)                                                                                   | NO   |     | NULL                |                |
#| MID              | int(10) unsigned                                                                              | NO   | MUL | 0                   |                |
#| TECH             | varchar(10)                                                                                   | NO   | MUL | NULL                |                |
#| SALESPERSON      | varchar(10)                                                                                   | NO   |     | NULL                |                |
#| ORIGIN           | enum('PHONE','EMAIL','VM','WEB','OTHER')                                                      | NO   |     | OTHER               |                |
#| NOTES            | mediumtext                                                                                    | YES  |     | NULL                |                |
#| DISPOSITION      | enum('LOW','MED','HIGH','ACTIVE','OTHER','CLOSED','WAITING','INCIDENT','CALLBACK','NEEDINFO') | NO   | MUL | OTHER               |                |
#| HAS_FASTTRACK    | enum('Y','N')                                                                                 | YES  |     | N                   |                |
#| SUBJECT          | varchar(80)                                                                                   | NO   |     | NULL                |                |
#| FOLLOWUPS        | int(11)                                                                                       | NO   |     | 0                   |                |
#| LAST_FOLLOWUP    | datetime                                                                                      | NO   |     | 0000-00-00 00:00:00 |                |
#| HAS_INCIDENT     | tinyint(4)                                                                                    | NO   |     | 0                   |                |
#| GROUPCODE        | varchar(10)                                                                                   | NO   |     | NULL                |                |
#| TIER             | char(1)                                                                                       | NO   |     | ?                   |                |
#| DIRTY            | int(1)                                                                                        | YES  |     | 0                   |                |
#| REVIEWED_GMT     | int(11)                                                                                       | NO   | MUL | 0                   |                |
#| STRESS_HOURSOPEN | smallint(5) unsigned                                                                          | NO   |     | 0                   |                |
#| STRESS_HOURSWAIT | smallint(5) unsigned                                                                          | NO   |     | 0                   |                |
#| STRESS_BOUNCES   | smallint(5) unsigned                                                                          | NO   |     | 0                   |                |
#| STRESS_SCORE     | int(10) unsigned                                                                              | NO   |     | 0                   |                |
#| STRESS_EXEMPT    | tinyint(4)                                                                                    | NO   |     | 0                   |                |
#| TRANSCENDED_GMT  | int(10) unsigned                                                                              | NO   |     | 0                   |                |
#+------------------+-----------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+

#mysql> desc TICKET_FOLLOWUPS;
#+-----------------+------------------+------+-----+---------+----------------+
#| Field           | Type             | Null | Key | Default | Extra          |
#+-----------------+------------------+------+-----+---------+----------------+
#| ID              | int(11)          | NO   | PRI | NULL    | auto_increment |
#| MID             | int(10) unsigned | NO   |     | 0       |                |
#| PARENT          | int(11)          | NO   | MUL | 0       |                |
#| CREATED_GMT     | int(10) unsigned | NO   | MUL | 0       |                |
#| CLOSED_GMT      | int(10) unsigned | NO   |     | 0       |                |
#| CREATEDBY       | varchar(20)      | NO   |     | 0       |                |
#| COMMENT         | mediumtext       | YES  |     | NULL    |                |
#| PUBLIC          | tinyint(4)       | NO   |     | 1       |                |
#| ACTION          | varchar(10)      | NO   |     | NULL    |                |
#| TRANSCENDED_GMT | int(10) unsigned | NO   |     | 0       |                |
#+-----------------+------------------+------+-----+---------+----------------+
#10 rows in set (0.00 sec)

my $sdbh = &SUPPORT::db_support_connect();
my $template_file = 'index.shtml';

if ($VERB eq 'VIEW') {
	my $c = '';
	my $ID = int($q->param('ID'));
	$GTOOLS::TAG{'<!-- TICKET -->'} = $ID;
	my $pstmt = "select * from TICKETS where ID=$ID";
	my $sth = $sdbh->prepare($pstmt);
	$sth->execute();
	my $ticketref  = $sth->fetchrow_hashref();
	$sth->finish();

	my $NOTES = &ZOOVY::incode(Text::Wrap::wrap("","",$ticketref->{'NOTES'}));

	$c .= Dumper($ticketref);
	$GTOOLS::TAG{'<!-- NOTES -->'} = $NOTES;

	$pstmt = "select * from TICKET_FOLLOWUPS where PARENT=$ID";
	$sth = $sdbh->prepare($pstmt);
	$sth->execute();
	while ( my $fref = $sth->fetchrow_hashref() ) {
		$c .= Dumper( $fref );
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- C -->'} = $c;
	$template_file = 'ticket.shtml';
	}

if ($VERB eq '') {
	my $c = '';
	my $pstmt = "select * from TICKETS where DISPOSITION in ('LOW','MED','HIGH','ACTIVE','NEEDINFO','OTHER') and TRANSCENDED_GMT=0";
	my $sth = $sdbh->prepare($pstmt);
	$sth->execute();
	my $bg = '';
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		if ($bg eq 'FFFFFF') { $bg = 'CCCCCC'; } else { $bg = 'FFFFFF'; }
		$c .= "<tr bgcolor='$bg'><td><a href='index.cgi?VERB=VIEW&ID=$hashref->{'ID'}'>$hashref->{'ID'}</a></td><td>$hashref->{'USERNAME'}</td><td>$hashref->{'SUBJECT'}</td></tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- TICKETS -->'} = $c;	
	$template_file = 'index.shtml';
	}

&SUPPORT::db_support_close();

&GTOOLS::output(file=>$template_file,header=>1);
