#!/usr/bin/perl

use CGI;
use strict;

use lib "/httpd/modules";
use DIALTONE;

my $q = CGI->new();

my $USERNAME = $q->param('USERNAME');
my $PRODUCT = $q->param('PRODUCT');
my $PAGE = $q->param('PAGE');		 

my $V = $q->param('V');
my $TYPE = $q->param('TYPE');
my $DIAL = $q->param('DIAL');
my $IP = $q->param('IP');
my $SESSION = $q->param('SESSION');
my $METHOD = $q->param('METHOD');


## return:
#STATUS=SUCCESS|FAIL
#MESSAGE=reason why denied.
#USERNAME=

##
## STATUS:
##		RINGING, NOANSWER, CONNECTING, DONE
##

my $STATUS = 'RINGING';

print "Content-type: text/xml\n\n";
print "<?xml version=\"1.0\"?>\n";

if ($METHOD eq 'STATUS') {
	my ($count) = &DIALTONE::operator_count($USERNAME);
	print qq~<clientStatus><operators count="$count"/></clientStatus>~;
	}
elsif ($METHOD eq 'CALL') {
	($STATUS) = &DIALTONE::create_call($USERNAME,$TYPE,$SESSION,$DIAL,$PAGE,$PRODUCT);
	print qq~<clientResponse><call session="$SESSION" status="$STATUS"/></clientResponse>~;
	}


