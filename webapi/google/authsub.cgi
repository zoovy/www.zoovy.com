#!/usr/bin/perl

use lib "/httpd/modules";
require LUSER;
require ZWEBSITE;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;

#print "Content-type: text/plain\n\n";
#print "Hello $USERNAME\n";
#print "URI: $ENV{'REQUEST_URI'}\n";

my $AUTHFOR = '';
if ($ENV{'REQUEST_URI'} =~ /authsub\.cgi\/(.*?)\?/) {
	$AUTHFOR = $1;
	}

$TOKEN = $q->param('token');

#print "AUTHFOR: $AUTHFOR\n";
#print "TOKEN: $TOKEN\n";

my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
$webdb->{'google_token_'.lc($AUTHFOR)} = $TOKEN;
&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);

if ($TOKEN eq '') {
	print "Location: /biz/setup/plugin/index.cgi?VERB=GOOGAPI-RETURN&RESULT=FAIL\n\n";
	}
else {
	print "Location: /biz/setup/plugin/index.cgi?VERB=GOOGAPI-RETURN&RESULT=SUCCESS&MSG=Setup+$TOKEN+successfully\n\n";
	}

