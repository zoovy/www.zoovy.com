#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use LUSER;
use ZAUTH;
use CGI;

my ($q) = CGI->new();
my $key = $q->param('key');

# CCBC:DEFAULT:livechatinc*mariusz:welcome
my ($xMID,$PROFILE,$USER,$PASS) = split(/:/,$key,4);
$xMID = hex($xMID);

my ($success) = int(&ZAUTH::get_user_password($USER,$PASS));

print "Content-type: text/plain\n\n";
print "USERID: $xMID\n";
print "SUCCESS: $success\n\nNOTE: Eventually this will set an authentication token and redirect\n";
