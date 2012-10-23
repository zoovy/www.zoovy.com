#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use DBINFO;

my $zdbh = &DBINFO::db_zoovy_connect();

my $pstmt = "select USERNAME from ZUSERS order by MID desc limit 0,100";
my $sth = $zdbh->prepare($pstmt);
$sth->execute();
while ( my ($USERNAME) = $sth->fetchrow() ) {
	print "USRE: $USERNAME\n";
	my $path = &ZOOVY::resolve_userpath($USERNAME);
	mkdir($path);
	chmod 0777, $path;
	mkdir("$path/IMAGES");
	chmod 0777, $path;

	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	if (not defined $gref) {
		$gref = {};
		$gref->{'@partitions'} = [ { name=>"DEFAULT" } ];
		}
	use Data::Dumper; print Dumper($gref);
	&ZWEBSITE::save_globalref($USERNAME,$gref);

	}


&DBINFO::db_zoovy_close();