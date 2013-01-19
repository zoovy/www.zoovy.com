#!/usr/bin/perl

use strict;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
my ($udbh) = &DBINFO::db_user_connect($USERNAME);

if ($VERB eq 'LOGIN') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID,INIT=>0x1);

	$LU->log("MANAGE.CUSTOMER","Logged into customer account: $CID","INFO");

	my $login = $C->email();
	my $pass = $C->get('INFO.PASSWORD');

	require DOMAIN::TOOLS;
	my $sdomain = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
	my $url = undef;

	# $SITE::SREF->{'+sdomain'} = $sdomain;
	if (not defined $sdomain) {
		$url = "#SORRY_NO_PRIMARY_DOMAIN_CONFIGURED_FOR_USERNAME=$USERNAME\_PRT=$PRT";
		print "Content-Type: text/plain\n\n";
		print "NO PRIMARY DOMAIN FOR USER:$USERNAME PRT:$PRT\n";
		}
	else {
		require SITE;
		($url) = SITE->new($USERNAME,'PRT'=>$PRT,'DOMAIN'=>"www.$sdomain")->URLENGINE()->get("login");
		print STDERR "SENDING TO: $url?login=$login&password=$pass\n";
		print "Location: $url?login=$login&password=$pass\n\n";
		}

	# print "Content-type: text/plain\n\n";
	exit;
	}

&DBINFO::db_user_close();