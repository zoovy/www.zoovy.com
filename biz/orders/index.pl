#!/usr/bin/perl -w

use lib "/httpd/modules";
use CGI;
use GTOOLS;
require ZOOVY;
use strict;

#print "Content-type: text/plain\n\n";
#print "We are temporarily down for maintenance - be back by 11:30pm PST.\n\n";
#exit;

&ZOOVY::init();


if (not defined $GTOOLS::HEADER_HEIGHT) {}; 	# stop perl from being a whiny knash.

my ($MERCHANT,$FLAGS,$MID,$USERNAME,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,undef);
if (not defined $FLAGS) { $FLAGS = ''; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }
# if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }


my $MAIN = 'recent.shtml';
if (index($FLAGS,'ZOMONLY')!=-1) {
	$MAIN = 'zomonly.shtml';
	&GTOOLS::output(file=>$MAIN,header=>1); exit;
	}

if ($ZOOVY::cgiv->{'FROM_HEADER'}) {
	## this is coming from the quicksearch in the tabs
	my $TEXT = $ZOOVY::cgiv->{'HEADER_VALUE'};

	# FROM_HEADER:
	#	<option value="order:orderid">order id</option>
	#	<option value="order:google">google order #</option>
	#	<option value="order:amazon">amazon order #</option>
	my $STATUS = '';
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'order:orderid') { $STATUS = 'ANY'; }
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'order:google') { $STATUS = 'GOOGLECHECKOUT'; }
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'order:amazon') { $STATUS = 'AMAZON'; }
	$MAIN = 'search-bounce.cgi?CMD=SEARCH&find_text='.$TEXT.'&search_field='.$STATUS;
	}


if ($ZOOVY::cgiv->{'VERB'} eq 'LOAD-ORDER') {
	$MAIN = 'view.cgi?ID='.$ZOOVY::cgiv->{'ID'};
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'QUICKSEARCH') {
	my $TEXT = $ZOOVY::cgiv->{'find_text'};
	if ($ZOOVY::cgiv->{'search_field'} eq 'INCOMPLETE') {
		$MAIN = '/biz/orders/external/body.cgi?CMD=SEARCH&TEXT='.$TEXT;
		}
	else {
		$MAIN = 'search-bounce.cgi?CMD=SEARCH&find_text='.$TEXT.'&search_field='.$ZOOVY::cgiv->{'search_field'};
		}
	}
elsif ($ZOOVY::cgiv->{'main'}) {
	$MAIN = $ZOOVY::cgiv->{'main'};
	}
print "Content-type: text/html\n\n";
print "<html>";
print "<frameset rows=\"".$GTOOLS::HEADER_HEIGHT.",*\" frameborder=0 framespacing=0 border=0>";
print "<frame src=\"title.pl\" id=\"title\" name=\"title\" frameborder=0 border=0 noresize scrolling='no'>";
print "<frame src=\"$MAIN\" id=\"body\" name=\"body\" frameborder=0 border=0>";
print "</frameset>";
print "</html>";

