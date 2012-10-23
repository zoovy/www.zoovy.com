#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use ZOOVY;
use ZWEBSITE;
use NAVCAT::FEED;
use ZSHIP;
use INVENTORY;
use GTOOLS;
use WHOLESALE;
use SYNDICATION;
use SYNDICATION::POWERREV;
use CGI;

# http://webapi.zoovy.com/webapi/nextag/index.cgi/USERNAME.PROFILE.txt
my $USERNAME = $ENV{'REQUEST_URI'};
if ($USERNAME =~ /\/([a-zA-Z0-9\.]+)\.txt$/) { $USERNAME = $1; } else { $USERNAME = ''; }
my $PROFILE = 'DEFAULT';

## separate USERNAME+PROFILE 
if ($USERNAME =~ /\./) {
	($USERNAME,$PROFILE) = split(/\./,$USERNAME);
	}

my $ERROR = undef;

if ((not defined $ERROR) && ($USERNAME eq '')) { 
	$ERROR = 'Could not find username.'; 
	}

if ($ERROR eq '') {
	#if ($PROFILE eq '') {
	#	($PROFILE) = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
	#	}

	print "Content-type: text/plain\n\n";
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'NXT');

	#if ($so->get('.url') =~ /^site\:\/\/(.*?)$/) {
	#	my $file = $1;
	#	print "FILE: $file\n";
	#	my $userpath = &ZOOVY::resolve_userpath($USERNAME);
	#	if (-f "$userpath/IMAGES/$file") {
	#		open F, "<$userpath/IMAGES/$file";
	#		while (<F>) {
	#			print $_;
	#			}
	#		close F;	
	#		}
	#	else {
	#		print "FILE $file does not appear to actually exist (even though it should).\n";
	#		}
	#	}
	if ($so->guid() ne '') {
		require LUSER::FILES;
		my ($lf) = LUSER::FILES->new($USERNAME);
		my ($FILETYPE,$FILENAME) = $lf->lookup_by_guid($so->guid());
		if ($FILENAME ne '') {
			print $lf->file_contents($FILENAME);
			}
		else {
			print "PRIVATE FILE $FILENAME does not appear to actually exist (even though it should).\n";
			}
		}
	else {	
		print "REGRETABLY, THE $USERNAME HAS NOT GENERATED FILE FOR PROFILE $PROFILE\n";
		}
	}
else {
	print "Content-type: text/error\n\nERROR: $ERROR\n";
	}

