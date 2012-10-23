#!/usr/bin/perl

use CGI;
use IO::File;


use lib "/httpd/modules";

my $REQFILE = undef;
my $DATAFILE = '';

if ($ENV{'REQUEST_URI'} =~ /suck\.cgi\/(.*?)$/o) { $REQFILE = $1; }

$REMOTE_ADDR = $ENV{'REMOTE_ADDR'};
if ($REMOTE_ADDR eq '66.240.244.204') {
	$REMOTE_ADDR = '192.168.1.1';
	}

if ($REQFILE eq 'published.txt') {
	require PUBLISHER;
	$DATAFILE = "$PUBLISHER::INDEXFILE";
	}
elsif ($REQFILE =~ /^PUBLISHER\/(.*?)$/) {
	my $FILE = $1;
	my ($USERNAME) = (undef);
	if ($FILE =~ /^([a-z0-9]+)\-/) { $USERNAME = $1; }
	# FILENAME: ubergeek-1191303361-v1.tar.bz


	if (defined $USERNAME) {
		require ZOOVY;
		my ($userpath) = &ZOOVY::resolve_userpath($USERNAME);
		$DATAFILE = $userpath."/PUBLISHER/".$FILE;
		}
	}
elsif ($REQFILE =~ /^GET\/(.*)$/) {
	$DATAFILE = $1;
	}
elsif ($REQFILE =~ /^EXISTS\/(.*)$/) {		
	print "Content-type: text/plain\n\n";
	print (-f $1)?1:0;
	$DATAFILE = '*';
	}
else {
	$DATAFILE = '';
	}

if ($REMOTE_ADDR !~ /192\.168\./) {
	print "Content-type: text/plain\n\n";
	print "No file for you $REMOTE_ADDR\n";
	}
elsif ($DATAFILE eq '*') {
	## ALREADY HANDLED
	}
elsif (-f $DATAFILE) {
	print "Content-type: binary/data\n\n";
	my $fh = new IO::File $DATAFILE, "r";
	if (defined $fh) {
		print <$fh>;
		undef $fh;       # automatically closes the file
		}
	}
else {
	print "Content-type: text/plain\n\n";
	use Data::Dumper;
	print Dumper(\%ENV,$DATAFILE,$REQFILE);
	}

