#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use SITE::EMAILS;
use Data::Dumper;



my $dbh = &DBINFO::db_zoovy_connect();
my $pstmt = "select MID,USERNAME,PROFILE,CODE,GEN_ORDERTYPE,GEN_ORDERSUBJECT,GEN_ORDERBODY,GEN_ORDERNOTES,GEN_ORDEREMAIL,GEN_ORDERBCC,GEN_ORDERATTACH,GEN_ORDEREMAIL_SRC from SUPPLIERS where MODE='GENERIC'";
$sth = $dbh->prepare($pstmt);
$sth->execute();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	print Dumper($hashref);

	if (not defined $hashref->{'PROFILE'}) { 
		$hashref->{'PROFILE'} = 'DEFAULT';
		}

	next if (not defined $hashref->{'MSGBODY'});
	
	my $MSGID = substr('SC.'.$hashref->{'CODE'},0,10);

	$pstmt = &DBINFO::insert($dbh,'SITE_EMAILS',{
		MID=>$hashref->{'MID'},
		USERNAME=>$hashref->{'USERNAME'},
		MSGID=>$MSGID,
		MSGTYPE=>'SUPPLY',
		MSGFORMAT=>'HTML',
		PROFILE=>$hashref->{'PROFILE'},
		PRT=>0,
		MSGBODY=>$hashref->{'GEN_ORDERBODY'},
		MSGSUBJECT=>$hashref->{'GEN_ORDERSUBJECT'},
		MSGFROM=>$hashref->{'GEN_ORDEREMAIL_SRC'},
		MSGBCC=>$hashref->{'GEN_ORDERBCC'},
		CREATED_GMT=>$^T,
		LUSER=>'SYSTEM',
		},key=>['MID','USERNAME','MSGID'],debug=>2);
	print $pstmt."\n";
	$dbh->do($pstmt);

	}
$sth->finish();

#| GEN_ORDERTYPE        | int(1)                                       | NO   |     | 0       |                |
##		1=html, 2=fax
#| GEN_ORDERSUBJECT     | varchar(100)                                 | YES  |     | NULL    |                |
#| GEN_ORDERBODY        | text                                         | YES  |     | NULL    |                |
#| GEN_ORDERNOTES       | int(1)                                       | YES  |     | 0       |                |
##		1=include
#| GEN_ORDEREMAIL       | varchar(50)                                  | YES  |     | NULL    |                |
#| GEN_ORDERBCC         | varchar(50)                                  | YES  |     | NULL    |                |
#| GEN_ORDERFAX         | varchar(20)                                  | YES  |     | NULL    |                |
#| GEN_ORDERATTACH      | int(1)                                       | NO   |     | 1       |                |
##		1=html, 2=txt , 3=xml
#| GEN_ORDEREMAIL_SRC   | varchar(50)                                  | YES  |     | NULL    |                |
#| GEN_EMAIL_MSGID      | varchar(10)                                  | NO   |     | NULL    |                |
#|

#+-------------+------------------------------------------------------------+------+-----+---------+----------------+
#| Field       | Type                                                       | Null | Key | Default | Extra          |
#+-------------+------------------------------------------------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned                                           | NO   | PRI | NULL    | auto_increment |
#| USERNAME    | varchar(20)                                                | NO   |     | NULL    |                |
#| MID         | int(10) unsigned                                           | NO   | MUL | 0       |                |
#| PROFILE     | varchar(10)                                                | NO   |     | NULL    |                |
#| PRT         | smallint(5) unsigned                                       | NO   |     | 0       |                |
#| LANG        | varchar(3)                                                 | NO   |     | ENG     |                |
#| MSGID       | varchar(10)                                                | NO   |     | NULL    |                |
#| MSGFORMAT   | enum('HTML','WIKI','TEXT')                                 | NO   |     | HTML    |                |
#| MSGTYPE     | enum('ORDER','INCOMPLETE','ACCOUNT','PRODUCT','SUPPLY','') | NO   |     | NULL    |                |
#| MSGSUBJECT  | varchar(60)                                                | NO   |     | NULL    |                |
#| MSGBODY     | mediumtext                                                 | NO   |     | NULL    |                |
#| MSGFROM     | mediumtext                                                 | YES  |     | NULL    |                |
#| MSGBCC      | mediumtext                                                 | YES  |     | NULL    |                |
#| CREATED_GMT | int(10) unsigned                                           | YES  |     | 0       |                |
#| LUSER       | varchar(10)                                                | NO   |     | NULL    |                |
#+-------------+------------------------------------------------------------+------+-----+---------+----------------+

&DBINFO::db_zoovy_close();

