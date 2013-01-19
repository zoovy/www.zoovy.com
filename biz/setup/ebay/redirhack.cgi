#!/usr/bin/perl

use strict;
use CGI;
use URI::Escape;
my $q = new CGI;

use lib "/httpd/modules";
use EBAY2;
&EBAY2::load_production();

#if ($q->param('eb') eq '') {
#	print "Location: /biz/setup/ebay/index.cgi?ACTION=HANDOFF\n\n";
#	}
#else {
if (1) {
	my $URL = 'https://signin.ebay.com/saw-cgi/eBayISAPI.dll?SignIn';
	my $sandbox = $q->param('sandbox');
	if ($sandbox eq 'on') { 
		$sandbox = 1; 
		$URL = 'https://signin.sandbox.ebay.com/ws/eBayISAPI.dll?SignIn';
		&EBAY2::load_sandbox();
		} 
	else { 
		$sandbox = 0; 
		}

	my $esc = URI::Escape::uri_escape("m=".$q->param('m').'&p='.$q->param('PROFILE').'&eb='.$q->param('eb').'&sb='.$sandbox);
	print "Location: $URL&runame=$EBAY2::runame&ruparams=$esc\n\n";
	}
