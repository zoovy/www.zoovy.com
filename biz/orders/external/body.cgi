#!/usr/bin/perl

use CGI;
use lib "/httpd/modules";
use GTOOLS;

$q = new CGI;

$c = '';
$REDIRECT = $q->param('REDIRECT');
print STDERR "REDIRECT IS: $REDIRECT\n";
$XFOOTER = $q->param('FOOTER');
if ((!defined($REDIRECT)) || ( $REDIRECT eq '')) { $REDIRECT = 'main.cgi'; }
if ((!defined($XFOOTER)) || ($XFOOTER eq '')) 	
	{
	$XFOOTER = 'blank-footer.shtml';
	if ($REDIRECT eq 'main.cgi') { $XFOOTER = 'main-footer.shtml'; }
	if ($REDIRECT eq 'body.cgi') { $XFOOTER = 'blank-footer.shtml'; }
	if ($REDIRECT eq 'email.cgi') { $XFOOTER = 'blank-footer.shtml'; }
	if ($REDIRECT eq 'add.cgi') { $XFOOTER = 'blank-footer.shtml'; }
	if ($REDIRECT eq 'footer.cgi') { $XFOOTER = 'blank-footer.shtml'; }
	}

$GTOOLS::TAG{'<!-- REDIRECT -->'} = $REDIRECT;
$GTOOLS::TAG{'<!-- XFOOTER -->'} = $XFOOTER;
$EXIDS = '';
$BACKSAFE = '';
my @CLAIMS = ();
foreach $param ($q->param()) {
	# automatically merge checkboxes
	if ($param =~ /\*ID-(.*?)$/) { push @CLAIMS, $1;}
	elsif ($param eq 'REDIRECT') {}
	else {
		$c .= "<input type='hidden' name='$param' value='".$q->param($param)."'>\\n";
		$BACKSAFE .= '&'.$param.'='.CGI->escape($q->param($param));
		}
	}
$EXIDS = join(",",@CLAIMS);

# Strip the old external ids
if ($EXIDS ne '') { $c .= "<input type='hidden' name='EXIDS' value='$EXIDS'>\\n"; }
$GTOOLS::TAG{'<!-- BACKSAFEURL -->'} = $REDIRECT."?EXIDS=".$EXIDS.$BACKSAFE;
print STDERR "BACKSAFEURL: $REDIRECT?EXIDS=$EXIDS$BACKSAFE\n";

$GTOOLS::TAG{'<!-- CONTENT -->'} = $c;
#print STDERR "CONTENT: $c\n";


if ($q->param('CMD') eq 'SEARCH') {
	my $searchfor = $q->param('TEXT');
	$searchfor =~ s/^[\W]*(.*?)[\W]*$/$1/gs;
	$GTOOLS::TAG{'<!-- BACKSAFEURL -->'} = 'main.cgi?XCMD=SEARCH&TEXT='.CGI->escape($searchfor);
	print STDERR "Search URL is: $GTOOLS::TAG{'<!-- BACKSAFEURL -->'}\n";
	}


&GTOOLS::output(title=>'',file=>'body.shtml',header=>1);

