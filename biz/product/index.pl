#!/usr/bin/perl -w

use lib "/httpd/modules";

use CGI;
require GTOOLS;
require ZOOVY;
use strict;

&GTOOLS::init();

&ZOOVY::init();

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/product",2,'_P&2');
if ($USERNAME eq '') { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }


if ($ZOOVY::cgiv->{'FROM_HEADER'}) {
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'product:id') { 
		$GTOOLS::TAG{'<!-- DEST_URL -->'} = 'search.cgi?ACTION=SEARCH&VALUE='.$ZOOVY::cgiv->{'HEADER_VALUE'};
		}
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'product:mkt') { 
		$GTOOLS::TAG{'<!-- DEST_URL -->'} = 'search.cgi?ACTION=MKT&VALUE='.$ZOOVY::cgiv->{'HEADER_VALUE'};
		}
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'QUICKSEARCH') {
	$GTOOLS::TAG{'<!-- DEST_URL -->'} = 'search.cgi?ACTION=SEARCH&VALUE='.$ZOOVY::cgiv->{'VALUE'};
	if (defined $ZOOVY::cgiv->{'DETAIL'}) {
		$GTOOLS::TAG{'<!-- DEST_URL -->'} .= '&DETAIL=1';
		}
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'EDIT') {
	$GTOOLS::TAG{'<!-- DEST_URL -->'} = "edit.cgi?PID=".$ZOOVY::cgiv->{'PID'};
	}
elsif ($ZOOVY::cgiv->{"goto"}) {
   $GTOOLS::TAG{"<!-- DEST_URL -->"} = $ZOOVY::cgiv->{"goto"};
   } 
else { 
	$GTOOLS::TAG{"<!-- DEST_URL -->"} = "edit.cgi?VERB=WELCOME"; 
	}

$GTOOLS::TAG{'<!-- HEIGHT -->'} = $GTOOLS::HEADER_HEIGHT;
&GTOOLS::output(file=>'index.shtml',header=>1);

