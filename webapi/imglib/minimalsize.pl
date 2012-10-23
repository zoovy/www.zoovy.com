#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;

my $q = new CGI;

my $USERNAME = $q->param('USERNAME');
my $IMAGENAME = $q->param('IMAGENAME');
my $REQWIDTH = $q->param('REQWIDTH');
my $REQHEIGHT = $q->param('REQHEIGHT');

use IMGLIB;

my $ERROR = '';

if ($USERNAME eq '') {
	$ERROR = 'No username passed';
	}

if ($ERROR eq '') {
	my ($w,$h) = &IMGLIB::minimal_size($USERNAME,$IMAGENAME,$REQWIDTH,$REQHEIGHT);
	print "Content-type: text/plain\n\n";
	print $w.'x'.$h."\n";
	}
else {
	print "Content-type: text/plain\n\nERROR: $ERROR\n";
	}




