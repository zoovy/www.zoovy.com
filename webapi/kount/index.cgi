#!/usr/bin/perl

use strict;

use CGI;
use Data::Dumper;
use Digest::MD5;
use lib "/httpd/modules";
use PLUGIN::KOUNT;

my ($q) = CGI->new();

my $TMPFILE = "/tmp/kount.txt.".time();

open F, ">>$TMPFILE";
print F Dumper(\%ENV,$q);
close F;

print "Content-type: text/plain\n\n";
print "Hello world!\n";

use lib "/httpd/modules";
use DBINFO;

# $ENV{'REQUEST_URI'} = //webapi/kount/listen.cgi/200130
my $KOUNTID = 0;
if ($ENV{'REQUEST_URI'} =~ /listen\.cgi\/([\d]+)$/) {
	$KOUNTID = int($1);
	}

my ($USERNAME,$PRT) = &PLUGIN::KOUNT::resolve_userprt($KOUNTID);

my ($zdbh) = &DBINFO::db_zoovy_connect();

my $KOUNT_ACCOUNT = 0;
# 'REQUEST_URI' => '//webapi/kount/listen.cgi/200090',
if ($ENV{'REQUEST_URI'} =~ /listen\.cgi\/([\d]+)$/) {
	$KOUNT_ACCOUNT = int($1);
	}

my $xmldata = $q->param('POSTDATA');
my $digest = Digest::MD5::md5_hex($xmldata);
my $OID = '';
if ($xmldata =~ /order_number\=\"(.*?)\"/) {
	$OID = $1;
	}

my $pstmt = &DBINFO::insert($zdbh,'KOUNT_NOTIFICATIONS',{
	'USERNAME'=>$USERNAME,
	'ORDERID'=>$OID,
	'DIGEST'=>$digest,
	'KOUNT_ACCOUNT'=>$KOUNT_ACCOUNT,
	'CREATED_GMT'=>time(),
	'XMLDATA'=>$xmldata,
	},
sql=>1);

print STDERR Dumper($pstmt);
my $DBID = 0;
if ($zdbh->do($pstmt)) {
	rename($TMPFILE,"$TMPFILE.processed");
	($DBID) = $zdbh->last_insert_id();
	}


if ($DBID>0) {
	}


&DBINFO::db_zoovy_close();
