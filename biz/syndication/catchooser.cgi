#!/usr/bin/perl


##
## CALLED: http://www.zoovy.com/biz/syndication/catchooser.cgi?FRM=catFrm&MKT=JLY&NAVCAT=navcat-$greatlookzglovesforwholesale&VAL=0
##

use strict;
use lib "/httpd/modules";
require SYNDICATION::CATEGORIES;
require GTOOLS;
require ZOOVY;
use Data::Dumper;

&ZOOVY::init();

my $template_file = 'catchooser.shtml';

my $MKT = $ZOOVY::cgiv->{'MKT'};
$GTOOLS::TAG{'<!-- MKT -->'} = $MKT;

my $FRM = $ZOOVY::cgiv->{'FRM'};
if ($FRM eq '') { $FRM = 'catFrm'; }

my $NC = $ZOOVY::cgiv->{'NAVCAT'};
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

print "Content-type: text/html\n\n";
print qq~
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="STYLESHEET" type="text/css" href="/biz/standard.css"/>
</head>
<body>

<script>
<!--

function save(myselect) {
	window.opener.document.forms['$FRM']['$NC'].value = myselect.value;
	var span = window.opener.document.getElementById('txt!$NC');
	window.opener.focus();
	span.innerHTML = myselect.options[myselect.selectedIndex].text;
	window.close();
	}


//-->
</script>

Category: $NC<br>
<br>

<b>Please select a category:</b><br>

<br>

<form name="myFrm" id="myFrm">
<input type="hidden" name="NAVCAT" value="$NC">
<select onChange="save(this);" style="font-size: 8pt; font-face: sans-serif, arial;" name="category">
<option value="0">-- Not Selected --</option>
$c
</select>
</form>
</body>
~;



#$GTOOLS::TAG{'<!-- CATEGORY -->'} = $c;
#&GTOOLS::output('*LU'=>$LU,file=>$template_file,header=>1);
