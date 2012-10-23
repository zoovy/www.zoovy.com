#!/usr/bin/perl

use strict;

use Data::Dumper;
use Mail::Message;
use lib "/httpd/modules";
use SUPPORT;

my ($file,$in) = (undef,undef);
if (1) {
	$file = "/tmp/gotmail.$$.".time();
	$/ = undef; $in = <STDIN>; $/ = "\n";
	open F, ">$file";
	print F $in;
	close F;
	}
else {
	open F, "</tmp/gotmail"; $/ = undef; $in = <F>; $/ = "\n"; close F;
	}



use Mail::Box::Message;
#print "$in\n";
my ($mbm) = Mail::Message->read($in, strip_status_fields=>1);
my ($TO) = $mbm->get('X-Original-To'); $TO =~ s/[\n\r]+//gs;

my ($USERNAME,$PRT) = (undef,undef);

my $PARTNER = '';
if ($TO =~ /^([\d]+)\@kount\.zoovy\.net$/) {
	$PARTNER = 'KOUNT';
	require PLUGIN::KOUNT;
	($USERNAME,$PRT) = PLUGIN::KOUNT::resolve_userprt($1);
	}
#elsif ($TO =~ /^(.*?)\@veruta\.zoovy\.net$/) {
#	my $AT = ($1);
#	$PARTNER = 'VERUTA';
#	## veruta is domain.com@veruta.zoovy.net or 
#	##		username@veruta.zoovy.net
#	if (index($AT,'.')>=0) {
#		## domain.com@veruta.zoovy.net
#		require DOMAIN::TOOLS;
#		($USERNAME) = &DOMAIN::TOOLS::fast_resolve_domain_to_user($AT);
#		}
#	elsif ($AT =~ /^[A-Za-z0-9]{3,20}$/) {
#		## username
#		$USERNAME = $AT;
#		}
#
#	#require PLUGIN::KOUNT;
#	#($USERNAME,$PRT) = PLUGIN::KOUNT::resolve_userprt($1);
#	}
else {
	$PARTNER = 'UNKNOWN';
	}

if ($USERNAME eq '') { $USERNAME = $PARTNER; }

my $SUBJECT = $mbm->subject();
my $SENDER = $mbm->sender()->address();  $SENDER =~ s/[\n\r]+//gs;

## $mbm->body() returns base64 encoded payloads
my $BODYTXT = $mbm->decoded();


my ($TICKET) = SUPPORT::createticket(
	$USERNAME,
	'ORIGIN'=>'PARTNER',
	'DISPOSITION'=>'ACTIVE',
	BODY=>qq~
Partner Communication: $PARTNER
SUBJECT: $SUBJECT
TO: $TO
FROM: $SENDER

$BODYTXT
~,
	PUBLIC=>1,
	SUBJECT=>$SUBJECT,
	'TECH'=>"*$PARTNER",
	'SALESPERSON'=>'',
	);


#unlink("$file");

print "Content-type: text/plain\n\n";
print $TICKET;

