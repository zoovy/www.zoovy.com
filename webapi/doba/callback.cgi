#!/usr/bin/perl

use lib "/httpd/modules";

## u: patti@zoovy.com
## pw: zoovy
## login to doba.com

print "Content-type: text/html\n\n";
use CGI;

my ($q) = CGI->new();

#create table DOBA_CALLBACKS (
#  ID integer unsigned auto_increment,
#  USERNAME varchar(20) default '',
#  RETAILER_ID decimal(10) default 0 not null,
#  CALLBACK_TYPE varchar(25) default '' not null,
#  XML mediumtext,
#  CREATED_GMT integer default 0 not null,
#  PROCESSED_GMT integer default 0 not null,
#  index(RETAILER_ID,PROCESSED_GMT)
#  primary key(ID)
#);

my $rid = 0;
my $ctype = 'unknown';

$q->param('xml') =~ m/<dce>(.*)<\/dce>/s;
my $xml = "<dce>".$1."</dce>"; 

if ($xml =~ /<retailer_id>([\d]+)<\/retailer_id>/) { $rid = int($1); }
if ($xml =~ /<callback_type>([\w]+)<\/callback_type>/) { $ctype = $1; }


## without a retailer_id or callback_type, this callback is useless
if ($rid == 0 || $ctype eq 'unknown') {
	## commented out = patti 2010-04-14
	##	no need to tell support, DOBA is sending blank callbacks
	#&ZOOVY::confess("DOBA","DOBA CALLBACK RID:$RID CTYPE:$CTYPE\n$xml\n");

	#open F, ">>/tmp/doba.unknowns";
	#print F $xml."\n";
	#close F;
	}

else {

	


	use DBINFO;
	my $zdbh = &DBINFO::db_zoovy_connect();
	my ($pstmt) = &DBINFO::insert($zdbh,'DOBA_CALLBACKS',{
		USERNAME=>'',
		RETAILER_ID=>$rid,
		CALLBACK_TYPE=>$ctype,
		XML=>$xml,
		CREATED_GMT=>time(),
		PROCESSED_GMT=>0
		},
	debug=>1+2);

	if (not $zdbh->do($pstmt)) {
		&ZOOVY::confess("DOBA","DOBA CALLBACK INSERT FAILURE RID:$RID CTYPE:$CTYPE\n$xml\n");
		}
	&DBINFO::db_zoovy_close();
	}

exit;
