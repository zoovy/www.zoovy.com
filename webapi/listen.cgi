#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use EBAY2;

&EBAY2:::load_production();

$ACTION = $ENV{'HTTP_SOAPACTION'};
$ACTION = substr($ENV{'HTTP_SOAPACTION'},rindex($ENV{'HTTP_SOAPACTION'},'/')+1,-1);

$in = '';
while (<STDIN>) { $in .= $_; }

#create table EBAY_NOTIFICATIONS (
#  ID integer unsigned not null auto_increment,
#  CREATED_GMT integer unsigned default 0 not null, 
#  PROCESSED_GMT integer unsigned default 0 not null,
#  DATA mediumtext,
#  HAD_ERROR tinyint default 0 not null,
#  primary key(ID),
#  index(PROCESSED_GMT,CREATED_GMT)
#);

my $file = "/tmp/ebay-$ACTION-".time().'.xml';
open F, ">$file";
print F $in;
close F;

#my $xs = new XML::Simple();
#my $ref = $xs->XMLin($in,ForceArray=>0);
#open F, ">/tmp/ebay-$ACTION-".time().".dmp";
#use Data::Dumper;
#print F Dumper($ref);
#close F;

require DBINFO;
my ($zdbh) = &DBINFO::db_zoovy_connect();
&DBINFO::insert($zdbh,'EBAY_NOTIFICATIONS',{
	CREATED_GMT=>time(),
	DATA=>$in,
	},debug=>1+2);

$pstmt = "select last_insert_id()";
my ($id) = $zdbh->selectrow_array($pstmt);
if ($id>0) {
	unlink $file;
	}

&DBINFO::db_zoovy_close();


print "Content-type: text/xml\n\n";

print "<?xml>";
print "<hi_ebay>how are you?</hi_ebay>";

