#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use CGI;
require LUSER;
require ZWEBSITE;
require SYNDICATION;

my ($q) = new CGI;


# print Dumper($q);

my ($mktId) = $q->param('marketplaceId');
my ($amzId) = $q->param('merchantId');

my ($REQUSERNAME,$REQPRT) = (undef,undef);
## /webapi/amazon/tokenreturn.cgi/USERNAME=xyzxyz/PRT=12
if ($ENV{'REQUEST_URI'} =~ /\/webapi\/amazon\/tokenreturn\.cgi\/USERNAME\=(.*?)\/PRT\=(.*?)$/) {
	($REQUSERNAME,$REQPRT) = ($1,$2);
	}

my $ERROR = undef;
my ($LU) = LUSER->authenticate(sendto=>"/webapi/amazon/tokenreturn.cgi/USERNAME=$REQUSERNAME/PRT=$REQPRT?marketplaceId=$mktId&merchantId=$amzId",nocache=>1,basic=>0);

if ($LU->username() ne $REQUSERNAME) {
	$ERROR = "Bad user, no cookie.";
	}

if ($ERROR) {
	print "Content-type: text/html\n\n";
	print "ERROR: $ERROR\n";
	}
else {
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($LU->username(),$REQPRT);
	$webdb->{'amz_token'} = "marketplaceId=$mktId&merchantId=$amzId";
	&ZWEBSITE::save_website_dbref($LU->username(),$webdb,$REQPRT);

	require SYNDICATION;
	my ($so) = SYNDICATION->new($LU->username(),"#$REQPRT","AMZ");
	$so->set('aws_mktid',$mktId);
	$so->set('aws_mid',$amzId);
	$so->save();

	print "Location: https://www.zoovy.com/biz/syndication/amazon\n\n";
	}

