#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
use CGI;
require ZOOVY;
require NAVCAT;
require ZTOOLKIT;
use strict;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q	 = new CGI;

my $template_file = '';
my $SRC = $q->param('SRC');		## where this prodlist is being pulled/saved from
											## NOTE: this is BLANK for a category, or something like
											## page:someattrib 
$GTOOLS::TAG{'<!-- SRC -->'} = $SRC;
my $CAT = $q->param('CAT');
my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);

if (defined($CAT)) {
	# stuff passed in from the main builder page
	if (substr($CAT,0,1) eq '@') {
		## already set correctly!
		}									
	else {
		$CAT = &NAVCAT::safename($q->param('CAT'));
		}
	}
elsif (substr($q->param('PG'),0,1) eq '@') {	
	## virtual page e.g. @CAMPAIGN:1
	$CAT = $q->param('PG');	
	}
elsif (substr($q->param('PG'),0,1) eq '*') {
	# stuff like  *cart
	$CAT = &NAVCAT::safename($q->param('PG'));
	}
else {
	# stuff passed in from builder preview page
	$CAT = '.'.&NAVCAT::safename($q->param('PG'));
	}

if (!defined($q->param('EXITURL'))) {
	$GTOOLS::TAG{'<!-- EXITURL -->'} = '../main.cgi'; 
	}
else {
	$GTOOLS::TAG{'<!-- EXITURL -->'} = $q->param('EXITURL');
	}

my $ACTION = $q->param('ACTION');

$GTOOLS::TAG{'<!-- CAT -->'} = $CAT;	

print STDERR "ACTION IS: $ACTION\n";

if ($ACTION eq 'SAVE') {
	print STDERR "Running Save..\n";
	my $SORTBY = '';
	my $list = $q->param('listorder');
	if ($CAT eq '') { $CAT = '.'; }
	print STDERR "CAT is: [$CAT]\n";
	$list =~ s/\|/\,/g;
	if (substr($CAT,0,1) eq '@') {
		if ($SRC =~ /^PAGE\:(.*?)$/i) {
			my $ATTRIB = $1;
			require PAGE;
			$FLOW::USERNAME = $USERNAME;
			$FLOW::PG = $CAT;
			my ($PG) = PAGE->new($USERNAME,$CAT,PRT=>$PRT);
			$PG->set($ATTRIB,$list);
			$PG->save();
			}
		}
	else {
		(my $PRETTY, my $CHILDREN, my $CONTENTS, $SORTBY, my $METAREF) = $NC->get($CAT);
		my ($list) = $NC->sort($CAT,$SORTBY);
		$NC->set($CAT,products=>$list);
		$NC->save();
		}


	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Successfully Saved Changes [$CAT] [$list], Press Exit to continue!";
	if ($SORTBY ne '') {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} .= "<br>Automatically resorted category [$SORTBY] - if this is incorrect please change the category sort order.\n";
		}
	$ACTION = '';
	}

my %fullprods = &ZOOVY::fetchproducts_by_name($USERNAME);
if (scalar(%fullprods)<=0) {
	$ACTION = 'ERROR';
	$template_file = 'error-noproducts.shtml';
	}

if ($ACTION eq '') {
	# build a list of products, @prods carries the currently selected products
	# whereas fullprods carries a full list of products.

	my ($pretty,$children,$products,$sortby);
	if (substr($CAT,0,1) eq '@') {
		$pretty = $CAT;
		if ($SRC =~ /^PAGE\:(.*?)$/i) {
			my $ATTRIB = $1; 
			$FLOW::USERNAME = $USERNAME;
			$FLOW::PG = $CAT;
			require PAGE;
			print STDERR "$FLOW::PG $ATTRIB\n";
			my ($PG) = PAGE->new($USERNAME,$CAT,PRT=>$PRT);
			($products) = $PG->get($ATTRIB);
			$PG = undef;
			}
		}
	else {
		($pretty,$children,$products,$sortby) = $NC->get($CAT);
		}

	# if we have children then breadcrumb
	if ($CAT eq '') {
		$GTOOLS::TAG{'<!-- PRETTYCAT -->'} = "[UNKNOWN!!!]"; 
		}
	elsif (substr($CAT,1) =~ /\./) {
		my ($order,$namesref) = $NC->breadcrumb($CAT);
		pop @{$order};	# remove the last element, which is the current category.
		my $PG = '';
		foreach (@{$order}) {
			$GTOOLS::TAG{'<!-- PRETTYCAT -->'} .= "<a href=\"index.cgi?CAT=$_&EXITURL=".CGI->escape($GTOOLS::TAG{'<!-- EXITURL -->'})."\"><font color='white'>".$namesref->{$_}."</font></a> / ";
			}
		$GTOOLS::TAG{'<!-- PRETTYCAT -->'} .= $pretty;
		} else {
		# no children, this is a root node.
		if ($CAT eq '.') { $pretty = "Homepage"; }
		$GTOOLS::TAG{'<!-- PRETTYCAT -->'} = "[$CAT] $pretty";
		}
	my @prods = split(',',$products);

	# step 1: sort through the array of associated products
	my $c = '';
	## NOTE: do not sort this because they might have been manually sorted
	foreach my $prod (@prods) {
		next unless (defined $fullprods{$prod});
		my $name = $fullprods{$prod};
		$name = &ZTOOLKIT::htmlstrip($name);
		$name = &ZOOVY::incode($name);
		$c .= "<option value='$prod'>[$prod] $name</option>\n";		
		delete $fullprods{$prod};
		}
	$GTOOLS::TAG{'<!-- ASSOC_LIST -->'} = $c;	

	# step 2: add the unselected products
	$c = '';
	foreach my $prod (sort keys %fullprods) {
		my $name = $fullprods{$prod};
		$name = &ZTOOLKIT::htmlstrip($name);
		$name = &ZOOVY::incode($name);
		$c .= "<option value=\"$prod\">[$prod] $name</option>\n";		
		}

	$GTOOLS::TAG{'<!-- NOT_INCLUDED -->'} = $c;
	$template_file = "index.shtml";
	}

&GTOOLS::output(title=>'',file=>$template_file,header=>1);

