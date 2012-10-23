#!/usr/bin/perl

use lib '/httpd/modules';
use DBINFO;

#mysql> desc LEADS;
#+--------------------+---------------------+------+-----+---------------------+----------------+
#| Field              | Type                | Null | Key | Default             | Extra          |
#+--------------------+---------------------+------+-----+---------------------+----------------+
#| ID                 | int(11)             | NO   | PRI | NULL                | auto_increment |
#| SRC                | varchar(4)          | NO   |     | NULL                |                |
#| OPERATORID         | varchar(8)          | NO   |     | NULL                |                |
#| CREATED            | datetime            | NO   |     | 0000-00-00 00:00:00 |                |
#| COMPANY_NAME       | varchar(60)         | NO   |     | NULL                |                |
#| CONTACT_FIRSTNAME  | varchar(30)         | NO   |     | NULL                |                |
#| CONTACT_LASTNAME   | varchar(30)         | NO   |     | NULL                |                |
#| PHONE_NUMBER       | varchar(20)         | NO   |     | NULL                |                |
#| WEBSITE            | varchar(50)         | NO   |     | NULL                |                |
#| EMAIL              | varchar(65)         | NO   |     | NULL                |                |
#| TIMETOCALL         | varchar(10)         | NO   |     | NULL                |                |
#| ASSIGN_MID         | int(11)             | NO   |     | 0                   |                |
#| ASSIGN_USERNAME    | varchar(20)         | NO   |     | NULL                |                |
#| ASSIGN_SALESPERSON | varchar(10)         | NO   |     | NULL                |                |
#| REFERRER           | varchar(20)         | NO   |     | NULL                |                |
#| IPADDRESS          | varchar(16)         | NO   |     | NULL                |                |
#| PROCESSED_GMT      | int(11)             | NO   |     | 0                   |                |
#| SUGARGUID          | varchar(65)         | NO   | MUL | NULL                |                |
#| IS_DUPLICATE       | tinyint(4)          | NO   |     | -1                  |                |
#| META               | varchar(255)        | NO   |     | NULL                |                |
#| BATCHID            | varchar(10)         | NO   |     | NULL                |                |
#| PHONE_VERIFIED     | tinyint(4)          | NO   |     | 0                   |                |
#| PHONE_ATTEMPTS     | tinyint(3) unsigned | NO   |     | 0                   |                |
#| DATA               | mediumtext          | NO   |     | NULL                |                |
#+--------------------+---------------------+------+-----+---------------------+----------------+
#24 rows in set (0.01 sec)


use Data::Dumper;

my $dbh = &DBINFO::db_zoovy_connect();
my $pstmt = "select * from LEADS where ID>8750 limit 0,1";
$sth = $dbh->prepare($pstmt);
$sth->execute();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	print Dumper($hashref)."\n";	
	
  ## NOTIFY SALESFORCE:
  require LWP::Simple;
  require ZTOOLKIT;
  my %foo = ();
  $foo{'encoding'} = 'UTF-8';
  $foo{'oid'} = '00DA0000000Z19B';
  $foo{'retURL'} = 'http://www.zoovy.com/thanks!';
  $foo{'first_name'} = $hashref->{'CONTACT_FIRSTNAME'};
  $foo{'last_name'} = $hashref->{'CONTACT_LASTNAME'};
  $foo{'email'} = $hashref->{'EMAIL'};
  $foo{'company'} = $hashref->{'COMPANY_NAME'};
  $foo{'phone'} = $hashref->{'PHONE_NUMBER'};
  $foo{'URL'} = $hashref->{'WEBSITE'};
  $foo{'lead_source'} = 'site-zoovy.com';
	# CAMPAIGN
  # $foo{'00N80000003Pyp7'} = "$hashref->{'META'}|$hashref->{'OPERATORID'}";
  $foo{'00NA0000003BOfp'} = "$hashref->{'META'}|$hashref->{'OPERATORID'}";
  ## Correlation Data:
  $foo{'00NA0000003BOfo'} = '';
  ## CorrelationID:
  # $foo{'00N80000003Pyp5'} = "LEAD-$hashref->{'ID'}";
  $foo{'00NA0000003BOfn'} = "LEAD-$hashref->{'ID'}";
	
  ## send to salesforce
  my $paramstr = &ZTOOLKIT::buildparams(\%foo);
  my ($r) = LWP::Simple::get("https://www.salesforce.com/servlet/servlet.WebToLead?$paramstr");
	print Dumper($r);

	}
$sth->finish();
&DBINFO::db_zoovy_close();