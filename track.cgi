#!/usr/bin/perl

use CGI;
use strict;

my $q = new CGI;

if (defined $q->param('HELP')) {
	print "Content-type: text/plain\n\n";

	print qq~
============================
RECEIVED URI PARAMETERS 
============================
~;
	foreach my $k ($q->param()) {
		print "$k=".$q->param($k)."\n";
		}

print "\n\nEXISTING COOKIE:\n";
print ((not defined $q->cookie('ZOOVY_LEAD'))?'None':$q->cookie('ZOOVY_LEAD'));

	print qq~

============================
APPLICATION USAGE
============================
www.zoovy.com/track.cgi usage instructions

this program sets a cookie called "ZOOVY_LEAD" which is used to track the buyer through 
EVERY SINGLE SIGNUP/LEAD ACQUISITION FORM EVER BUILT.

It sets the cookie, then uses the SENDTO parameter to send them some other place on the site.

Parameters are URI encoded which means that it looks like:
www.zoovy.com/track.cgi?PARAM1=VALUE1&PARAM2=VALUE2

the order of the parameters is not important, just that they begin after a
? and are delimited by an &

Example:
http://www.zoovy.com/track.cgi?SENDTO=/amazon&SRC=GOOG&META=sell+on+amazon


**** TESTING GOTCHA ****
track.cgi will track the *FIRST* instance a buyer gets to the site, in other words
if a person comes to the site from campaign 1, then leaves, and comes in again from
campaign 2 (with the ZOOVY_LEAD cookie set), then campaign 1 will get credit.  This is 
invaluable for tracking, but if you're trying to *TEST* you must remember to delete your
ZOOVY_LEAD cookie before any test.

ZOOVY_LEAD cookie is currently set to last 336 hours or 14 days.

============================
VALID PARAMETERS:
============================

HELP=1 -- displays this screen, also echo's any known parameters you passed

SENDTO=/some/path/on/site.html

SRC=CODE		-- usually a 4-6 digit code to designate a campaign -- MOST IMPORTANT!!
OPERID=		-- if we're using a call center, or need to track back to a specific individual
					(usually used for commission purposes)
META=			-- detailed information about the lead, e.g. "keywords used"


~;
exit;
	}

##
## 
##
my $URL = lc($q->param("SENDTO"));
# 
if (substr($URL,0,1) eq '/') {
	## it's going to / something, so it's safe!
	}
else {
	$URL = '/?offsite-redirect-not-allowed';
	}

# rewrite SENDTO:
if ($URL eq "") { $URL = "http://www.zoovy.com"; }

#if ($URL eq "/affiliate/promo") { $URL = "http://www.zoovy.com/affiliate/promo/december"; }
#if ($URL) { $URL = "http://www.zoovy.com/affiliate/wtf"; }
#$URL = "http://www.zoovy.com/";

my $SRC = $q->param('SRC');
my $OPERID = $q->param('OPERID');
my $META = $q->param('META');

if (defined $q->param('P')) {
	## LEGACY COMPATIBILITY MODE
	##	for P and C variables 
	$SRC = 'WEB';
	my $PARTNER = $q->param("P");
	if (!defined($PARTNER)) { $PARTNER = $q->param("PARTNER"); }
	$PARTNER =~ s/\W+//g;
	if ($PARTNER eq '') { $PARTNER = 'UNKNOWN'; }
	$OPERID = $PARTNER;

	my $CAMPAIGN = $q->param("C");
	if (!$CAMPAIGN) { $CAMPAIGN = $q->param("CAMPAIGN"); }
	$META = $CAMPAIGN;
	}

my $COOKIE = "$SRC|$OPERID|$META";

# run the PARTNER through a sanity check.

##
## The format for the ZOOVY_AFFILIATE cookie is a pipe delimited.
##		SRC	e.g. WEB,USER
##		OPERID	e.g. FEDEX,AMAZON for WEB, or userid for USER
##		META	this is additional information which will be stored in the META field.
##

if (not defined $q->cookie('ZOOVY_LEAD')) {
	## don't set the cookie if one was already set.
	print "Set-cookie: ", $q->cookie(-name=>'ZOOVY_LEAD',-value=>"$COOKIE",-expires=>'+336h',-path=>'/',-domain=>'.zoovy.com',-secure=>0), "\n";
	}

print $q->redirect($URL);

