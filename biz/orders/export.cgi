#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use ZTOOLKIT;
use ZWEBSITE;
use CGI;
use EXPORT;

&ZOOVY::init();

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&1');
if ($USERNAME eq '') { exit; }

if ($FLAGS =~ /,L3,/) { $FLAGS .= ',API,'; }
if (!$USERNAME) { exit; }
$q = new CGI;
$CMD = uc($ZOOVY::cgiv->{'CMD'});
if (!defined($CMD)) { $CMD = ''; }

if ($FLAGS !~ /,API,/) {
	&GTOOLS::print_form('','export-deny.shtml',1);
	exit;
	}

$ORDERS = $ZOOVY::cgiv->{'ORDERS'};
$GTOOLS::TAG{'<!-- ORDERS -->'} = $ORDERS;

if ($CMD eq '')
	{
	print "Content-type: text/html\n\n";
	print "<body>Javascript command failure, please retry. If this message persists please contact technical support.</body>\n";

	} elsif ($CMD eq 'EXPORT') {

	my $foo = 
		$ZOOVY::cgiv->{'billing_info'}.','.
		(($ZOOVY::cgiv->{'strip_prices'})?1:0).','.
		(($ZOOVY::cgiv->{'strip_payment'})?1:0).','.
		uc($ZOOVY::cgiv->{'order_format'}).','.	
		(($ZOOVY::cgiv->{'smart_recovery'})?1:0).','.'0,0,0,'.
		$ZOOVY::cgiv->{'export_url'};
	($billing_info,$strip_prices,$strip_payment,$format,$recovery) = split(',',$foo);

	# create a read only copy of webdb which we can pass to override defaults in EXPORT::order_dispatch
	%WEBDBREF = &ZWEBSITE::fetch_website_dbref($USERNAME);
	$WEBDBREF->{'order_dispatch_defaults'} = $foo;
	$WEBDBREF->{'order_dispatch_mode'} = 9;		# always dispatch
	$WEBDBREF->{'order_dispatch_url'} = $ZOOVY::cgiv->{'dispatch_url'};
	
	print "Content-type: text/html\n\n";
	print "<head><STYLE>\n<!--\nTD { font-face: arial; font-size: 10pt; }\n-->\n</STYLE>\n</head>\n";
	print "<body><center>";

	# $merchantref = &ZOOVY::attrib_handler_ref(&ZOOVY::fetchmerchant($USERNAME));
	my $merchantref = &ZOOVY::fetchmerchant_ref($USERNAME);

	@ar = split(/,/,$ORDERS);
	print "<h1>Sending order ".scalar(@ar)." orders.</h1>";
	print "<table width='60%'><tr><Td><center>When complete, use the buttons along the top to return.</center><br><b>Output Results:</b></td></tr></table>\n";

	foreach $order (sort @ar) { 
#		print STDERR "Handling Order: $order\n";
		if ($order ne '') {
			print "Order: $order<br>\n";
			($success,$message) = &EXPORT::order_dispatch($USERNAME,$order,$merchantref,$WEBDBREF);
			if ($success == 0) {
				print "Order $order Export Success! ($message)\n<br>";
				}
			else {
				print "Order $order Export Failed! (REASON: $message)\n<br>";
				}

			}

		} # end of foreach loop
		print "<h1>Finished.</h1>\n";
		print "<a target='body' href='move.cgi?AREA=$AREA&SORTBY=$SORTBY'>Click here to Exit</a></center></body>";

	} # end of out if/then

exit;