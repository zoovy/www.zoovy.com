#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZTOOLKIT;
use DBINFO;

my $q = new CGI;
my $VERB = $q->param('VERB');
my $template_file = 'index.shtml';

#mysql> desc LEADS;
#+-----------------+-------------+------+-----+---------------------+----------------+
#| Field           | Type        | Null | Key | Default             | Extra          |
#+-----------------+-------------+------+-----+---------------------+----------------+
#| ID              | int(11)     | NO   | PRI | NULL                | auto_increment |
#| SRC             | varchar(4)  | NO   |     | NULL                |                |
#| OPERATORID      | varchar(8)  | NO   |     | NULL                |                |
#| CREATED         | datetime    | NO   |     | 0000-00-00 00:00:00 |                |
#| COMPANY_NAME    | varchar(60) | NO   |     | NULL                |                |
#| CONTACT_PERSON  | varchar(60) | NO   |     | NULL                |                |
#| PHONE_NUMBER    | varchar(20) | NO   |     | NULL                |                |
#| WEBSITE         | varchar(50) | NO   |     | NULL                |                |
#| EMAIL           | varchar(65) | NO   |     | NULL                |                |
#| TIMETOCALL      | varchar(10) | NO   |     | NULL                |                |
#| ASSIGN_MID      | int(11)     | NO   |     | 0                   |                |
#| ASSIGN_USERNAME | varchar(20) | NO   |     | NULL                |                |
#| PROCESSED_GMT   | int(11)     | NO   |     | 0                   |                |
#+-----------------+-------------+------+-----+---------------------+----------------+
#13 rows in set (0.02 sec)

$GTOOLS::TAG{'<!-- REMOTE_USER -->'} = $ENV{'REMOTE_USER'};

if ($VERB eq 'SAVE') {
	my $dbh = &DBINFO::db_zoovy_connect();
	my %ref = ();
	$ref{'SRC'} = $ENV{'REMOTE_USER'};
	$ref{'OPERATORID'} = $q->param('operator');
	$ref{'CREATED'} = &ZTOOLKIT::mysql_from_unixtime($^T);
	$ref{'COMPANY_NAME'} = $q->param('company');
	
	my ($first) = $q->param('first');
	my ($last) = $q->param('last');
	if (defined $q->param('contact')) { ($first,$last) = split(/ /,$q->param('contact'),2); }

	$ref{'CONTACT_FIRSTNAME'} = $first;
	$ref{'CONTACT_LASTNAME'} = $last;
	$ref{'PHONE_NUMBER'} = $q->param('phone');
	$ref{'WEBSITE'} = $q->param('website');
	$ref{'EMAIL'} = $q->param('email');
	$ref{'TIMETOCALL'} = $q->param('timetocall');
	$ref{'BATCHID'} = $q->param('batchid');
	my $pstmt = &DBINFO::insert($dbh,'LEADS',\%ref,debug=>2);
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);
	$pstmt = "select last_insert_id()";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($ID) = $sth->fetchrow();
	$sth->finish();

	if ($ID == 0) { 
		$ID = "<font color='red'>An error has occurred, lead cannot be saved. Please contact supervisor.</font><br>";
		}

	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
	
	&DBINFO::db_zoovy_close();
	$template_file = 'thanks.shtml';
	}


&GTOOLS::output(file=>$template_file,header=>1);