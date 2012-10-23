#!/usr/bin/perl -w

use strict;
use CGI;

use Data::Dumper;
use lib '/httpd/modules';
require DBINFO;
require ZOOVY;
require ZTOOLKIT;
require ZWEBSITE;

use lib ".";

my ($DBID) = 0;

if (1) {
	&ZOOVY::init();
	&DBINFO::init();

	## Set up $env, $cgi and $params hashes
	my $env    = \%ENV;
	my $cgi    = new CGI;
	my $params = { map { $_ => ($cgi->param($_))[0] } $cgi->param() }; ## Create a hash of cgi params with scalar (not array ref) values

	############################################################
	## Begin shared code with /httpd/scripts/paypal/ipn_import.pl (test script from old notify.cgi)
	## If the CGI call isn't a post from the paypal server, bail
	my $method  = defined($env->{'REQUEST_METHOD'}) ? $env->{'REQUEST_METHOD'} : '' ;
	my $address = defined($env->{'REMOTE_ADDR'})    ? $env->{'REMOTE_ADDR'}    : '' ;
	
	## paypal original address 65.206.229.140
	## paypal changed address to 64.4.241.140 on Oct 23rd

	## Get the username, first from the URL path, then from the custom variable,
	## then from the custom variable parsed as a set of key-value pairs
	my $username;
	my $prt = 0;
	if (defined($env->{'PATH_INFO'}) && ($env->{'PATH_INFO'} =~ m/^\/([a-zA-Z0-9]+)$/)) {
		## Got it from the URL path
		$username = $1;
		}
	elsif (defined($env->{'PATH_INFO'}) && ($env->{'PATH_INFO'} =~ m/^\/prt=([\d]+)\/([a-zA-Z0-9]+)$/)) {
		## Got it from the URL path -- with partition.
		$prt = $1;
		$username = $2;
		}
	elsif ((defined $params->{'custom'}) && ($params->{'custom'} =~ m/[a-zA-Z0-9\-]+/)) {
		## Got it from the whole username in the custom parameter
		$username = $params->{'custom'};
		}
	elsif ((defined $params->{'custom'}) && ($params->{'custom'} =~ m/\//)) {
		## Got it from the key-value pairs encoded into the paypal custom variable
		my $custom = {};
		foreach my $keyval (split /\//, $params->{'custom'}) {
			my ($key,$val) = split /\:/, $keyval, 2;
			if (not defined $key) { $key = ''; }
			if (not defined $val) { $val = ''; }
			$custom->{$key} = $val;
			}
		$username = $custom->{'username'};
		}
		
	my $mid   = &ZOOVY::resolve_mid($username);
	if ($mid == 0) {
		open F, ">>/tmp/paypal.log";
		print F "\nERROR: MID is zero!\n";
		print F Dumper($params);
		close F;
		}

	my $webdb = &ZWEBSITE::fetch_website_dbref($username);

	print STDERR "USERNAME: $username\n";
	## Then dump the entry into the database
	my $dbh = &DBINFO::db_zoovy_connect();
	$username = $dbh->quote($username);
	my $item_number = $dbh->quote(defined($params->{'item_number'})?$params->{'item_number'}:'');
	my $invoice     = $dbh->quote(defined($params->{'invoice'})?$params->{'invoice'}:'');
	my $paypal_id   = $dbh->quote(defined($params->{'txn_id'})?$params->{'txn_id'}:'');
	my $content     = $dbh->quote(&ZTOOLKIT::hashref_to_xmlish($params,'sort'=>1));
	my $t = time();
	my $pstmt = "insert into PAYPAL_QUEUE (PAYPAL_ID,USERNAME,MID,CREATED,ITEM_NUMBER,INVOICE,DATA,SRC) values ($paypal_id,$username,$mid,$t,$item_number,$invoice,$content,'IPN')";
	my $rv = $dbh->do($pstmt);

	($DBID) = $dbh->selectrow_array("select last_insert_id()");

	&DBINFO::db_zoovy_close();
	unless (defined $rv) {
		open F, ">>/tmp/paypal.log";
		print F "\nERROR: could not add to database!\n$pstmt\n";
		print F Dumper($params);
		close F;
		}

	## Tell PayPal everything's OK (even if we're lying)
	}
	
print "Pragma: no-cache\n";           # HTTP 1.0 non-caching specification
print "Cache-Control: no-cache\n";    # HTTP 1.1 non-caching specification
print "Expires: 0\n";                 # HTTP 1.0 way of saying "expire now"
print "Content-type: text/plain\n\n";
print "OK\n";


if ($DBID>0) {
	my $CMD = "/httpd/modules/ZPAY/paypalprocess.pl dbid=$DBID 1>> /tmp/paypal-$DBID.txt 2>> /tmp/paypal-$DBID.txt";
	$ENV{'SHELL'} = '/bin/bash';
	open H, "|/usr/bin/at -q b now + 1 minutes";
	print H $CMD."\n";
	close H;
	}
