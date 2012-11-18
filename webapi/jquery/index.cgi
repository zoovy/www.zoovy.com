#!/usr/bin/perl

use utf8 qw();
use strict;
use Data::Dumper;
use JSON::XS;
use lib "/httpd/modules";
require ZOOVY;
require JSONAPI;
require DOMAIN::TOOLS;
require SITE;


$ENV{'REQUEST_METHOD'} =~ tr/a-z/A-Z/;

## NOTE: this code is mirrored in SITE::Vstore
print "X-XSS-Protection: 0\n";
print "Access-Control-Allow-Origin: *\n";
print "Access-Control-Allow-Methods: POST, GET, OPTIONS\n";
print STDERR Dumper(\%ENV);
## HTTP_ACCESS_CONTROL_REQUEST_HEADERS content-type,x-auth,x-authtoken,x-cliendid,x-deviceid
##print "Access-Control-Headers: Content-Type, content-type, x-authtoken, authtoken\n";
print "Access-Control-Max-Age: 0\n";
## NOTE: Access-Control-Allow-Headers does NOT work with * you must specify something (ex: Content-Type)
print "Access-Control-Allow-Headers: Content-Type, x-authtoken, x-version, x-clientid, x-deviceid, x-userid, x-domain\n";
## print "Access-Control-Headers: $ENV{'HTTP_ACCESS_CONTROL_REQUEST_HEADERS'}\n";
print "Vary: Accept-Encoding\n";
if ($ENV{'REQUEST_METHOD'} eq 'OPTIONS') {
	print STDERR "ACKNOWLEDGED OPTIONS HEADER\n";
	foreach my $k (split(/,/,$ENV{'HTTP_ACCESS_CONTROL_REQUEST_HEADERS'})) {
		next if ($k eq 'content-type');
		next if ($k eq 'x-auth');
		next if ($k eq 'x-authtoken');
		}
	print "Content-Length: 0\n";
	print "Keep-Alive: timeout=2, max=100\n";
	print "Connection: Keep-Alive\n";
	print "Content-type: text/plain\n\n";
	exit;
	}

# &ZOOVY::init(); can't run zoovy init.


##
## PHASE1: parse cookies, and input data. 
##
# print STDERR Dumper(\%ENV);

## Read input
my $buffer = undef;
if ($ENV{'REQUEST_METHOD'} eq "GET") {
	$buffer = $ENV{'QUERY_STRING'};
	}
elsif ($ENV{'REQUEST_METHOD'} eq "POST") {
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
	}



## NOW we need to decide 
# print STDERR 'REQUEST: '.Dumper(\%ENV,{$ENV{'CONTENT_TYPE'}=>$buffer});
# print STDERR "BUFFER: $buffer\n";

# Split information into name/value pairs
my $VARS = undef;
my $R = undef;
if ($buffer eq '') {
	warn "No content received\n";
	}
elsif ($ENV{'CONTENT_TYPE'} =~ /^(text|application)\/json/) {
	## text/json
	## application/json
	eval { $VARS = JSON::XS::decode_json($buffer); };
	if ($@) {
		&JSONAPI::set_error($R = {}, 'iseerr', 1, "decode json $@"); 
		}
	}
else {
	warn "content-type other\n";
	my @pairs = split(/&/, $buffer);
	foreach my $pair (@pairs) {
		my ($name, $value) = split(/=/, $pair);
		$value =~ tr/+/ /;
		$value =~ s/%(..)/pack("C", hex($1))/eg;
		$VARS->{$name} = $value;
		}
	}

if ($VARS->{'_callback'}) {
	## jsonp request so parameters passed on get in funky format:
	#			 {
	#				'@cmds' => [],
	#				'@cmds[0][_uuid]' => '1116',
	#				'@cmds[0][status]' => 'requesting',
	#				'_zjsid' => 'EUNNyP9KuE1DX1xitmC94VFHc',
	#				'_cmd' => 'pipeline',
	#				'_uuid' => '1117',
	#				'_callback' => 'bob',
	#				'@cmds[0][_v]' => 'zmvc:201216.20120410143100;browser:mozilla-11.0;OS:WI;',
	#				'@cmds[0][_tag][callback]' => 'translateTemplate',
	#				'_' => '1335282924213',
	#				'@cmds[0][_cmd]' => 'appProfileInfo',
	#				'@cmds[0][profile]' => 'DEFAULT',
	#				'@cmds[0][attempts]' => '0',
	#				'callback' => 'bob',
	#				'@cmds[0][_tag][datapointer]' => 'appProfileInfo|DEFAULT',
	#				'@cmds[0][_tag][parentID]' => 'newID'
	#			 },
	if ($VARS->{'_json'}) {
		my $v = JSON::XS::decode_json($VARS->{'_json'});
		$VARS->{'%v'} = $v;
		print STDERR Dumper($v);
		}
	}



#if ($ENV{'PATH_INFO'} eq '/ie8.js') {
#	## much less efficient ie8 work around
#	my $content = '';
#	open F, sprintf("</tmp/ie8-%s.js",$VARS->{'_uuid'});
#	while (<F>) { $content .= $_; }
#	close F;
#	print "Content-type: text/javascript\n\n";
#	print "$content";
#	die();
#	}


# print STDERR 'VARS: '.Dumper($VARS);

$ZOOVY::cookies = {};
if ($ENV{'HTTP_COOKIE'} ne '') {
	## we got some cookies, lets parse 'em.
	#__utma=98299796.877293812.1256064081.1330024164.1330026365.244; __utmv=98299796.|1=Tier=AA=1; __utmz=98299796.1329264247.238.34.utmcsr=blogger.com|utmccn=(referral)|utmcmd=referral|utmcct=/profile/05925940776420361689; ZOOVY_LEAD=%7C%7C; __utmc=98299796; session_id=; zjsid=**18aUG5RqFiOKhI2lu4vwpITv7?USERNAME=brian|LUSER=ADMIN|X=HGwktX5jzP1I8qKpwY79zrAFV; __utmb=98299796.1.10.1330026365
	foreach my $line (split(/;[\s]*/,$ENV{'HTTP_COOKIE'})) {
		my ($k,$v) = split(/=/,$line,2);
		next if ($v eq "''");
		$ZOOVY::cookies->{$k} = $v;
		if (not defined $VARS->{"_$k"}) { $VARS->{"_$k"} = $v; }
		}
	}

# print STDERR 'COOKIES:'.Dumper($ZOOVY::cookies,$VARS);



## lookup domain, and from that we can get everything else.

#if (substr($VARS->{'_zjsid'},0,2) eq '**') {
#	## admin session.
#	require AUTH;
#	my ($result) = AUTH::fast_validate_session($VARS->{'_zjsid'});
#
#	if ($result) {
#		$SITE = SITE->new($result->{'USERNAME'}, 'PRT'=>$result->{'PRT'}, 'NS'=>$result->{'PROFILE'}, 'DOMAIN'=>$result->{'DOMAIN'} );
#		}
#	}
#elsif (substr($VARS->{'_zjsid'},0,1) eq '*') {
#	## possibly a provisional token issued
#	require AUTH;
#	my %PAIRS = ();
#	foreach my $chunk (split(/\|/,$VARS->{'_zjsid'})) {
#		my ($k,$v) = split(/=/,$chunk);
#		$PAIRS{$k} = $v;
#		}
#	if ($PAIRS{'USERNAME'}) { 
#		$SITE = SITE->new($PAIRS{'USERNAME'});
#		}
#	print STDERR "SITE::MERCHANT_ID: $PAIRS{'USERNAME'}\n"; 
#	}
#if ($ENV{'REQUEST_URI'} =~ /index\.cgi\/(.*?)$/) {
#	my $SDOMAIN = $1;
#	my ($USERNAME,$SSL_DOMAIN,$PRT,$PROFILE) = &DOMAIN::TOOLS::fast_resolve_domain_to_user($SDOMAIN);
#	$SITE = SITE->new($USERNAME, 'PRT'=>$PRT, 'NS'=>$PROFILE, 'DOMAIN'=>$SDOMAIN);
#	}

#if (defined $ERROR) {
#	}
#elsif (scalar(@{$CMDS})==0) {
#	$ERROR = "No commands found";
#	warn "**** NO COMMANDS ****";
#	}
#elsif (not defined $SITE) {
#	## gosh, hopefully it's a login call.
#	## print STDERR "*** BLANK ZJSID LOOK FOR appAdminInit CMD and use LOGIN for now. ***\n";
#
#	foreach my $cmdref (@{$CMDS}) {
#		if (defined $SITE) {
#			}
#		elsif ($cmdref->{'domain'}) {
#			my ($USERNAME) = &DOMAIN::TOOLS::fast_resolve_domain_to_user($cmdref->{'domain'});
#			$SITE = SITE->new($USERNAME);
#			}
#		elsif ($cmdref->{'login'}) {
#			require AUTH;
#			my ($user,$luser) = &AUTH::parse_login($cmdref->{'login'});
#			$SITE = SITE->new($user,'LUSER'=>$luser,'IS_SITE'=>0);
#			}
#		}
#	}


my $JSAPI = JSONAPI->new();

if (not defined $R) {
	$R = $JSAPI->init($VARS,'%ENV'=>\%ENV);
	}



my ($utf8_encoded_json_text);
if ($R) {
	## preflight error
	$R->{'_rcmd'} = 'err';
	($utf8_encoded_json_text) = JSON::XS->new->utf8->allow_blessed(1)->convert_blessed(1)->encode($R);
	}
else {
	my ($udbh) = &DBINFO::db_user_connect($JSAPI->username());

	my ($R,$cmdlines);
	eval { ($R,$cmdlines) = $JSAPI->handle($ENV{'REQUEST_URI'},$VARS); };
	if ($@) {
		&JSONAPI::set_error($R = {}, 'iseerr', 1, "Internal Error $@");
		&ZOOVY::confess( $JSAPI->username(), "JSONAPI $@", justkidding=>1 );
		}

	#if (&ZOOVY::servername() eq 'newdev') {
	#	use Clone;
	#	open Fx, ">>/tmp/trace.log";
	#	print Fx $$.Dumper($cmdlines)."\n";
	#	print Fx "-------------------------------------------------\n";
	#	close Fx;
	#	}

	## NOTE: utf8 crashes prodlists (talk to jt -- for now ascii is fine)
	## ($utf8_encoded_json_text) = JSON::XS->new->utf8()->allow_blessed(1)->convert_blessed(1)->encode($R);
	($utf8_encoded_json_text) = JSON::XS->new->ascii()->allow_blessed(1)->convert_blessed(1)->encode($R);

	#	print STDERR 'PAGE::JQUERY::handle response: '.Dumper($R,$cmdlines,$utf8_encoded_json_text);
	if ($JSAPI->has_cart2()) {
		$JSAPI->cart2()->save();
		}

	&DBINFO::db_user_close();
	}



#if (0) {
#	## hmm. if we have an error AND it wasn't a valid request type then we should run this code which displays
#	## browser/user interpretable code
#	warn "returning - could not determine credentials\n";
#	warn "ZJSID:$VARS->{'_zjsid'}\n";
#	print "Content-type: text/plain\n\n";
#	print "could not determine credentials, login or domain in request\n";
#	exit;
#	}
#if ($VARS->{'_callback'}) {
#	# $ENV{'PATH_INFO'} eq '/jsonp.js') {
#	## specialized ie8 handler, leaves a file, which is picked up later.
#	require MEDIA;
#	print "Content-type: image/gif\n\n";
#	print MEDIA::blankout();
#	# print "Content-type: text/javascript\n\n";
#	print "Content-type: application/json\n\n";
#	my $callbackjs = sprintf("%s(%s);\n",$VARS->{'_callback'},$utf8_encoded_json_text);
#	print $callbackjs;
#	open F, sprintf(">/tmp/callback-%s.js",$VARS->{'_uuid'});
#	print F $callbackjs;
#	close F;
#	}
#else {
	print "Content-type: text/json\n";
	print "Content-Length: ".length($utf8_encoded_json_text)."\n";
	print "\n";
	print $utf8_encoded_json_text;
#	}
#print STDERR "UFT8 RESPONSE: $utf8_encoded_json_text\n";

1;
