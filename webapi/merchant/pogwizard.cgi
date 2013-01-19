#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use CGI;
use GTOOLS;
use STUFF::CGI;
use STUFF2;
use POGS;
use strict;
use Data::Dumper;

#
# http://www.zoovy.com/webapi/merchant/pogwizard.cgi?USERNAME=jefatech&PRODUCT=GD58			(legacy)
# http://www.zoovy.com/webapi/merchant/pogwizard.cgi?USERNAME=jefatech&PRODUCT=RV245RD		(rich)
# http://www.zoovy.com/webapi/merchant/pogwizard.cgi?USERNAME=outpost&PRODUCT=W9732			(non-inv)
# http://www.zoovy.com/webapi/merchant/pogwizard.cgi?USERNAME=1stproweddingalbums&PRODUCT=WBK101015PBSPKG			(excessive)
#

my $q = new CGI;
my $USERNAME = $q->param('USERNAME');
my $PRODUCT = $q->param('PRODUCT');
if ((not defined $PRODUCT) || ($PRODUCT eq '')) { $PRODUCT = $q->param('product'); }

my $CLIENT = $q->param('CLIENT');
my $STID = $q->param('STID');
my $COMPAT = int($q->param('COMPAT'));
if ($COMPAT==0) { $COMPAT = 107; }
print STDERR "USER:$USERNAME PRODUCT:$PRODUCT COMPAT: $COMPAT\n";

my $VERB = $q->param('VERB');

my ($P) = PRODUCT->new($USERNAME,$PRODUCT,'create'=>0);
# my @pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},1);
my $selectedref = {};
#if (0) {
#	print "Content-type: text/plain\n\n";
#	print Dumper(\@pogs,$prodref);
#	exit;
#	}

my $lm = LISTING::MSGS->new($USERNAME);
my ($stuff2) = STUFF2->new($USERNAME);

if ($VERB eq 'SAVE') {
	require STUFF::CGI;

	## Build a hashref of key/value pairs!
	my %params = ();
	my %lcparams = ();
	foreach my $k ($q->param()) { 
		$params{$k} = $q->param($k); 
		$lcparams{lc($k)} = $params{$k};
		}
	
	#my $stuff = STUFF->new($USERNAME);
	#my @errors = ();
	#my @items = &STUFF::CGI::parse_products($USERNAME,\%lcparams,0,\@errors);
	#foreach my $item (@items) {
	#	$stuff->legacy_cram($item);
	#	}

	## note: we need to pass zero_qty_okay but it seems like legacy_parse already does that for us
	($stuff2,$lm) = &STUFF::CGI::legacy_parse($stuff2,\%lcparams,'*LM'=>$lm);

#	if (0) {
#		print "Content-type: text/plain\n\n";
#		print Dumper($q,$stuff,$stid,\%params);	
#		}

	# my ($xml,$errors) = $stuff2->as_legacy_stuff()->as_xml();

	if (not $lm->can_proceed()) {
		$VERB = 'TRYAGAIN';
		# print STDERR 'TRY AGAIN: '.Dumper($stuff2,$lm);
		}
	}


if ($VERB eq 'SAVE') {


	my ($xml,$errors) = $stuff2->as_xml($COMPAT);
#	print STDERR "XML: $xml\n";
#	print STDERR "STUFF2: ".Dumper($stuff2)."\n";

	print "Content-type: text/html\n\n";
	print qq~
<html>
<font color="blue">Success!</font><br>
<b>This window should close automatically in a moment.</b><br>
<!--
<POGWIZARD>$xml</POGWIZARD>
-->~;
	print qq~</html>~;
	}


if (($VERB eq '') || ($VERB eq 'TRYAGAIN')) { 
	print "Content-type: text/html\n\n";


	my $msgs = '';
	if ($VERB eq 'TRYAGAIN') {
		my @msgs = ();
		foreach my $msg (@{$lm->msgs()}) {
			my ($msgref,$status) = LISTING::MSGS::msg_to_disposition($msg);
			push @msgs, "$status|$msgref->{'+'}";
			}
		$msgs = &GTOOLS::show_msgs(\@msgs);
		}


	my $html = &POGS::struct_to_html($P,$selectedref,4);

	print qq~
<head>
<link rel="STYLESHEET" type="text/css" href="/biz/standard.css">
</head>
<body> 
	<form method=post action="/webapi/merchant/pogwizard.cgi">
	<input type="hidden" name="USERNAME" value="$USERNAME">
	<input type="hidden" name="product" value="$PRODUCT">
	<input type="hidden" name="CLIENT" value="$CLIENT">
	<input type="hidden" name="VERB" value="SAVE">
	<input type="hidden" name="COMPAT" value="$COMPAT">
	$msgs
	$html
	<input type="submit" value=" Submit ">
	</form>
</body>
	~;
	}


