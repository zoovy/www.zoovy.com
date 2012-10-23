package IPN;

use lib '/httpd/modules';
require DBINFO;
require ZOOVY;
require ZPAY::PAYPAL;
require ZTOOLKIT;

sub invalid_entry
{
	print "Pragma: no-cache\n";             # HTTP 1.0 non-caching specification
	print "Cache-Control: no-cache\n";      # HTTP 1.1 non-caching specification
	print "Expires: 0\n";                   # HTTP 1.0 way of saying "expire now"
	print "Content-type: text/html\n\n";
	print "<html>\n";
	print "	<head>\n";
	print "		<title>Internal Use Only</title>\n";
	print "	</head>\n";
	print "	<body>\n";
	print "		<h1>Internal Use Only</h1>\n";
	print "		This URL is for internal use with PayPal's online payment system.  To use PayPal\n";
	print "		with your Zoovy account, paste this URL into the Instant Payment Notification (IPN)\n";
	print "		section of your PayPal preferences at\n";
	print "		<a target=\"_new\" href=\"https://www.paypal.com/cgi-bin/webscr?cmd=_profile-ipn-notify\">https://www.paypal.com/cgi-bin/webscr?cmd=_profile-ipn-notify</a>\n";
	print "		(log in to your PayPal account before clicking the link).\n";
	print "	</body>\n";
	print "</html>\n";
	print STDERR "ipn.pl: called from incorrect address or without POST\n";
	exit;
}

sub database_error
{
	## die means that the server will return a 500 which will cause paypal to try again later.
	die "ipn.pl: Could not insert into PAYPAL_QUEUE\n";
}

sub no_username
{
	my ($env,$cgi,$params) = @_;
	print STDERR "ipn.pl: Could not find merchant login:\n";
	print STDERR &ZTOOLKIT::prepend_text('ipn.pl',Data::Dumper->Dump([$params],['$params']));
	print STDERR &ZTOOLKIT::prepend_text('ipn.pl',Data::Dumper->Dump([$env],['$env']));
}


1;
