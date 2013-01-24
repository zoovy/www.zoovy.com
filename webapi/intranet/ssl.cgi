#!/usr/bin/perl

use strict;

##
## the purpose of this application is to dump all ssl certificate information 
##	so it can be loaded by an SSL proxy (which does not have a DB connection)
##

if ($ENV{'REMOTE_ADDR'} =~ /66\.240\.244/) {}
elsif ($ENV{'REMOTE_ADDR'} =~ /208.74.184\./) {}
elsif ($ENV{'REMOTE_ADDR'} =~ /192\.168\./) {}
elsif ($ENV{'REMOTE_ADDR'} eq '') {}
else {
	print "Content-type: text/plain\n\nAccess denied for IP: $ENV{'REMOTE_ADDR'}\n";
	exit;
	}

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use Data::Dumper;
use YAML;
use CGI;
use DOMAIN::RESOLVE;

my ($q) = new CGI;
my $VERB = $q->param('VERB');
my $CLUSTER = $q->param('CLUSTER');
if ($CLUSTER eq '') {
	print "Content-type: text/plain\n\nCLUSTER IS REQUIRED!\n"; die();
	}

#mysql> desc SSL_CERTIFICATES;
#+-----------------+------------------+------+-----+---------+----------------+
#| Field           | Type             | Null | Key | Default | Extra          |
#+-----------------+------------------+------+-----+---------+----------------+
#| ID              | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| IP_ADDRESS      | varchar(16)      | NO   | UNI | NULL    |                |
#| PROVISIONED_GMT | int(10) unsigned | NO   |     | 0       |                |
#| PROVISIONED_TXN | int(10) unsigned | NO   |     | 0       |                |
#| USERNAME        | varchar(20)      | YES  |     | NULL    |                |
#| MID             | int(10) unsigned | YES  | MUL | NULL    |                |
#| DOMAIN          | varchar(65)      | YES  |     | NULL    |                |
#| KEYTXT          | mediumtext       | NO   |     | NULL    |                |
#| CSRTXT          | mediumtext       | NO   |     | NULL    |                |
#| PEMTXT          | mediumtext       | NO   |     | NULL    |                |
#| CERTTXT         | mediumtext       | NO   |     | NULL    |                |
#+-----------------+------------------+------+-----+---------+----------------+
#11 rows in set (0.01 sec)


my $udbh = &DBINFO::db_user_connect("\@$CLUSTER");

if ($VERB eq 'GOLIVE') {
	print "Content-type: text/plain\n\n";
	my $SSLDOMAIN = $q->param('DOMAIN');
	my $ID = $q->param('ID');

	

	my $pstmt = "update SSL_CERTIFICATES set LIVE_TS=now() where DOMAIN=".$udbh->quote($SSLDOMAIN)." and ID=".int($ID);
	print STDERR "$pstmt\n";
	$udbh->do($pstmt);

	$pstmt = "update SSL_IPADDRESSES set LIVE_TS=now() where DOMAIN=".$udbh->quote($SSLDOMAIN);
	print STDERR "$pstmt\n";
	$udbh->do($pstmt);

	$pstmt = "select IP_ADDRESS from SSL_IPADDRESSES where DOMAIN=".$udbh->quote($SSLDOMAIN);
	my ($IPADDRESS) = $udbh->selectrow_array($pstmt);

	if (($SSLDOMAIN =~ /^secure\.(.*)$/) && ($IPADDRESS ne '')) {
		my ($DOMAIN) = $1;
		my $qtIPADDR = $udbh->quote($IPADDRESS);

		## so on a renewed ssl cert, the SSL_PROVISIONED_GMT will be set to now, but the LIVE_GMT date for the domain
		##		will be in the past, effectively knocking the SSL certificate off because it doesn't appear that dns
		##		is live yet. to fix this we use the SSL statement below.
		$pstmt = "update DOMAINS set LIVE_GMT=unix_timestamp(now())+1 where DOMAIN=".$udbh->quote($DOMAIN)." and SSL_PROVISIONED_GMT>0";
		print $pstmt."\n";
		$udbh->do($pstmt);

		## now we can safely reset the SSL_PROVISIONED_GMT to right now, since it will be LIVE 1 sec in the future.
		$pstmt = "update DOMAINS set SSL_PROVISIONED_GMT=unix_timestamp(now()),SSL_IPADDR=$qtIPADDR where DOMAIN=".$udbh->quote($DOMAIN);
		print $pstmt."\n";
		$udbh->do($pstmt);
		}

	print "Success!\n";
	}


if ($VERB eq 'DOWNLOAD') {
	## we need to get the proper IP for each certificate
	my %DOMAIN_TO_IP = ();
	my $pstmt = "select IP_ADDRESS,DOMAIN from SSL_IPADDRESSES";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($IP,$DOMAIN) = $sth->fetchrow() ) {
		$DOMAIN_TO_IP{lc($DOMAIN)} = $IP;
		}
	$sth->finish();
	
	$pstmt = "select * from SSL_CERTIFICATES where ACTIVATED_TS>0 group by DOMAIN order by ACTIVATED_TS desc";
	$sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @SSL = ();
	while ( my $ref = $sth->fetchrow_hashref() ) {

		$ref->{'CLUSTER'} = &ZOOVY::resolve_cluster($ref->{'USERNAME'});
		$ref->{'IP_ADDRESS'} = $DOMAIN_TO_IP{lc($ref->{'DOMAIN'})};

		push @SSL, $ref;
		}
	$sth->finish();	
	print "Content-type: text/yaml\n\n";
	print YAML::Dump(\@SSL);	
	}

&DBINFO::db_user_close();

