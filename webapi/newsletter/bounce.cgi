#!/usr/bin/perl

use lib "/httpd/modules";
use strict;

my $q = CGI->new();

##
## CGI parameters are:
##
my $EMAIL = $q->param('EMAIL');
my $USERNAME = $q->param('USERNAME');
my $DOMAIN = $q->param('DOMAIN');
my $CPG = $q->param('CPG');
my $CPNID = $q->param('CPNID');
my $PRT = $q->param('PRT');

print "Content-type: text/plain\n\n";

my $MID = &ZOOVY::resolve_mid($USERNAME);

if (($USERNAME eq '') && ($DOMAIN ne '')) {
	# require DOMAIN::TOOLS;
	# ($USERNAME) = &DOMAIN::TOOLS::fast_resolve_domain_to_user($DOMAIN);
	($USERNAME,$PRT) = &DOMAIN::TOOLS::domain_to_userprt($DOMAIN);
	print "Found-User: $USERNAME\n";
	print "Found-PRT: $PRT\n";
	}

my $CID = 0;
if ($EMAIL ne '') {
	($CID) = &CUSTOMER::resolve_customer_id($USERNAME,$PRT,$EMAIL);
	print "Resolve-CID: $CID [$USERNAME,$EMAIL]\n";
	}

if ($CID==0) {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = &DBINFO::insert($udbh,'EMAIL_LOG',{
		MID=>$MID,
		USERNAME=>$USERNAME,
		EMAIL=>$EMAIL,
		'*CREATED'=>'now()',
		'STATE'=>'OPTOUT',
		},sql=>1);
	$udbh->do($pstmt);
	&DBINFO::db_user_close();
	print "Saved-Log: 0 [$USERNAME,$EMAIL]\n";
	}

if (($CID==0) && ($CPNID>0) && ($CPG>0)) {
	($CID) = &CUSTOMER::RECIPIENT::lookup_CID($USERNAME,$CPG,$CPNID);
	print "Resolve-CID: $CID [$USERNAME,$CPG,$CPNID]\n";
	}

if ($CID>0) {
	use CUSTOMER;
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID,INIT=>0x01);
	if (defined $C) {
		print "Removed-Customer: $EMAIL\n";
		$C->set_attrib('INFO.NEWSLETTER',0);
		$C->save();
		}
	}

if (($USERNAME ne '') && ($CPG>0)) {
	print "Recorded-Bounce: CPG=$CPG|CPNID=$CPNID\n";
	use CUSTOMER::RECIPIENT;
	CUSTOMER::RECIPIENT::coupon_action($USERNAME,'BOUNCED',CPG=>$CPG,CPNID=>$CPNID);
	}


