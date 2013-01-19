#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use ZTOOLKIT;
use CGI;
use strict;

my $cgi    = new CGI;
my $params = { map { $_ => ($cgi->param($_))[0] } $cgi->param() }; ## Create a hash of cgi params with scalar (not array ref) values

my $dbh = &DBINFO::db_zoovy_connect();

my $item_number = $dbh->quote(defined($params->{'item_number'})?$params->{'item_number'}:'');
my $invoice     = $dbh->quote(defined($params->{'invoice'})?$params->{'invoice'}:'');
my $paypal_id   = $dbh->quote(defined($params->{'txn_id'})?$params->{'txn_id'}:'');
my $DATA = &ZTOOLKIT::hashref_to_xmlish($params,'sort'=>1);

&DBINFO::insert($dbh,'BS_PAYPALIPN', {
	'*CREATED'=>'now()',
	INVOICE=>$invoice,
	DATA=>$DATA,
	PROCESSED_GMT=>0,
	});
&DBINFO::db_zoovy_close();

## send a copy via email
open MH, "|/usr/bin/sendmail -t";
print MH "To: brian\@zoovy.com\n";
print MH "Cc: billing\@zoovy.com\n";
print MH "From: brian\@zoovy.com\n";
print MH "Subject: Paypal IPN Notification\n\n";
print MH $DATA;
close MH;

## Tell PayPal everything's OK (even if we're lying)
print "Pragma: no-cache\n";           # HTTP 1.0 non-caching specification
print "Cache-Control: no-cache\n";    # HTTP 1.1 non-caching specification
print "Expires: 0\n";                 # HTTP 1.0 way of saying "expire now"
print "Content-type: text/plain\n\n";
print "OK\n";
exit;
