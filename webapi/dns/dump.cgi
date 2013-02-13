#!/usr/bin/perl

#New name server is ready and updated.  
#	Currently it has a firewall dropping everything but ssh from the IP ranges we talked about.  
# It has nothing installed really except postfix, which I have not configured.  
# I removed the last IP from pub1 and gave it that.  I made the password unique: 
# 66.240.207.135
# 23D0gsb1t3

use strict;
use lib "/httpd/modules";

use ZOOVY;
use DOMAIN;
use YAML::Syck;
use Data::Dumper;
$YAML::Syck::ImplicitTyping = 0;
my @a = ();


##
## 
##

my %DOMAINS = ();

my ($q) = new CGI;
my @CLUSTERS = ();
my $CLUSTER = $q->param('CLUSTER');

if ($CLUSTER eq '') {
	@CLUSTERS = @{&ZOOVY::return_all_clusters()};
	}
else {
	push @CLUSTERS, $CLUSTER;
	}

print "Content-type: text/yaml\n\n";

#my $dbh = &DBINFO::db_zoovy_connect();
## get the ghosts of christmas future, ssl certificates which aren't actually provisioned yet.
my %SECURE_USERDOMAINS = ();


foreach my $CLUSTER (@CLUSTERS) {
	
	my ($udbh) = &DBINFO::db_user_connect("\@$CLUSTER");
	
	my %SECURE_USERDOMAINS = ();
	my $pstmt = "select USERNAME,DOMAIN,IP_ADDRESS from SSL_IPADDRESSES";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($USERNAME,$HOSTDOMAIN,$IPADDR) = $sth->fetchrow() ) {
		next if ($USERNAME eq '');
		$HOSTDOMAIN = lc($HOSTDOMAIN);
		if ($HOSTDOMAIN =~ /^(www|secure|app|m)\.(.*?)$/i) {
			my ($HOST,$DOMAIN) = ($1,$2);
			push @{$SECURE_USERDOMAINS{ lc("$USERNAME|$DOMAIN") }}, { 'IP'=>$IPADDR, 'HOST'=>$HOST, 'DOMAIN'=>$DOMAIN };
			}
		}
	$sth->finish();
	# print Dumper(\%SECURE_USERDOMAINS);	die();

	# my $pstmt = "select MID,USERNAME,DOMAIN,STATUS,HOST_TYPE,REG_TYPE,SUB_MASTER,EMAIL_TYPE,FWD_TARGET_EMAIL,EXTERNAL_MX1,EXTERNAL_MX2,SSL_IPADDR,SSL_PROVISIONED_GMT,DKIM_PUBKEY,MODIFIED_GMT from DOMAINS ";
	my $pstmt = "select MID,PRT,USERNAME,DOMAIN,STATUS,REG_TYPE,EMAIL_TYPE,EMAIL_CONFIG,WWW_HOST_TYPE,WWW_CONFIG,M_HOST_TYPE,M_CONFIG,APP_HOST_TYPE,APP_CONFIG,SSL_IPADDR,SSL_PROVISIONED_GMT,DKIM_PUBKEY,MODIFIED_GMT,NEWSLETTER_ENABLE from DOMAINS ";
	$pstmt .= " order by DOMAIN";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my $dref = $sth->fetchrow_hashref() ) {

		next if (lc(&ZOOVY::resolve_cluster($dref->{'USERNAME'})) ne lc($CLUSTER));

		$DOMAINS{$dref->{'DOMAIN'}}++;
		my $DOMAIN = $dref->{'DOMAIN'};
		my $USERDOMAIN = lc(sprintf("%s|%s",$dref->{'USERNAME'},$dref->{'DOMAIN'}));

		if (defined $SECURE_USERDOMAINS{$USERDOMAIN}) {
			$dref->{'@SSLHOSTS'} = $SECURE_USERDOMAINS{$USERDOMAIN};
			}

		delete $dref->{'SSL_IPADDR'};
		$dref->{'DKIM_PUBKEY'} =~ s/[\-]+(.*?)[\-]+//g;
		$dref->{'DKIM_PUBKEY'} =~ s/[\n\r]+//gs;
		$dref->{'CLUSTER'} = &ZOOVY::resolve_cluster($dref->{'USERNAME'});
		push @a, $dref;
		}
	$sth->finish();

	my $pstmt = "select DOMAIN from DOMAINS_POOL where MID=0";
	$sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($DOMAIN) = $sth->fetchrow() ) {
		push @a, { 'REG_TYPE'=>'RESERVATION', 'CLUSTER'=>$CLUSTER, 'DOMAIN'=>$DOMAIN };
		}
	$sth->finish();

	&DBINFO::db_user_close();
	}

# &DBINFO::db_zoovy_close();

print YAML::Syck::Dump(\@a);
