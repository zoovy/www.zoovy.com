#!/usr/bin/perl


##
## CALLED: http://www.zoovy.com/biz/syndication/catchooser.cgi?FRM=catFrm&MKT=JLY&NAVCAT=navcat-$greatlookzglovesforwholesale&VAL=0
##

use strict;
use lib "/httpd/modules";
require SYNDICATION::CATEGORIES;
require ZOOVY;
require GTOOLS;
use Data::Dumper;

my ($USERNAME) = &ZOOVY::authenticate();
my $template_file = 'catchooser.shtml';

my $MKT = $ZOOVY::cgiv->{'MKT'};
$GTOOLS::TAG{'<!-- MKT -->'} = $MKT;

my $FRM = $ZOOVY::cgiv->{'FRM'};
if ($FRM eq '') { $FRM = 'catFrm'; }
$GTOOLS::TAG{'<!-- FRM -->'} = $FRM;

my $NC = $ZOOVY::cgiv->{'NAVCAT'};
$GTOOLS::TAG{'<!-- NAVCAT -->'} = $NC;
my $VAL = int($ZOOVY::cgiv->{'VAL'});

my ($CDS) = &SYNDICATION::CATEGORIES::CDSLoad($MKT);
my ($flatref) = SYNDICATION::CATEGORIES::CDSFlatten($CDS);

my $c = '';
my %cats = ();
my %top = ();
foreach my $ref (@{$flatref}) {
	$ref->[1] =~ s/\>/ &gt; /g;
	$cats{$ref->[1]} = $ref->[0];
	
	$ref->[1] =~ /^(.*?) &gt; /;
	$top{$1}++
	}

## added sorting by the category name
$c .= "<option value=\"-1\">Do not Send</option>\n";
foreach my $name (sort keys %cats) {
	my $val = $cats{$name};
	my ($selected) = ($VAL == $val)?'selected':'';
	$c .= "<option $selected value=\"$val\">$name</option>\n";
	}
$GTOOLS::TAG{'<!-- CATEGORY -->'} = $c;

&GTOOLS::output(file=>$template_file,header=>1);
