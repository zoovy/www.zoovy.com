#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $DOCID = $ZOOVY::cgiv->{'DOCID'};
my $FORMAT = $ZOOVY::cgiv->{'FORMAT'};

require TOXML::CHOOSER;
my ($t) = TOXML->new($FORMAT,$DOCID,USERNAME=>$USERNAME);
my $html = TOXML::CHOOSER::showDetails($USERNAME,$t);		
if (not defined $html) { $html = "<i>Could not load $FORMAT:$DOCID user=$USERNAME</i><br>"; }

&GTOOLS::output(html=>$html,header=>1);



