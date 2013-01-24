#!/usr/bin/perl -w

use CGI;
use LWP::UserAgent;
use LWP::Simple;
use HTTP::Request::Common;
use HTTP::Cookies;
use strict;
use Data::Dumper;
use lib '/httpd/modules';
require ZPAY;
require ZWEBSITE;
require ZTOOLKIT;
use POSIX qw(strftime);

my $DEBUG     = 0;
my $MAX_TRIES = 3;
my $WAIT_SECS = 5;
my $DIR       = "/tmp/paypal/";

my $now         = 0;
my $mode        = 'OK';
my $merchant_id = '';
if ($ENV{'PATH_INFO'} =~ /\/([a-zA-Z0-9]+)$/) { $merchant_id = $1; }
my $order_id = '';
my $date     = strftime("%y-%m-%d.%H:%M:%S", localtime());

# Load the CGI object
my $cgi    = new CGI;
my $params = {map { $_ => ($cgi->param($_))[0] } $cgi->param};    ## Create a hash of cgi params with scalar (not array ref) values

unless (-d $DIR) { mkdir $DIR; }
my $ox = $params->{'item_number'};
$ox =~ s/[^\d\-]+//g;
my $filename = "$DIR/$date-" . (($merchant_id) ? $merchant_id : '') . "$ox.log";

# Write out a debug file

my $server = defined($ENV{'SERVER_NAME'}) ? $ENV{'SERVER_NAME'} : '';
my $script = defined($ENV{'SCRIPT_NAME'}) ? $ENV{'SCRIPT_NAME'} : '';
my $path   = defined($ENV{'PATH_INFO'})   ? $ENV{'PATH_INFO'}   : '';
my $url    = "http://$server$script$path";

my $dbh = &DBINFO::db_zoovy_connect();
my $mid = &ZOOVY::resolve_mid($merchant_id);
my $invoice     = $dbh->quote(defined($params->{'invoice'})?$params->{'invoice'}:'');

# Did we get a Merchant ID?
if ($merchant_id ne '') {
	}
elsif (defined($params->{'custom'}) && ($params->{'custom'} ne '')) { 
	$merchant_id = $params->{'custom'};
	if ($merchant_id =~ /^(.*?)\*(.*?)$/) {		# new format merchant*orderid
		$merchant_id = $1; $invoice = $2;
		}
	}
elsif ($path =~ m/\/([a-zA-Z0-9\-]+)$/) {
	$merchant_id = $1;
	}

my $username = $dbh->quote($merchant_id);
my $item_number = '';
if (defined $params->{'item_number'}) { $item_number = $params->{'item_number'}; }
if (defined $params->{'item_number1'}) { $item_number = $params->{'item_number1'}; }

if  (($params->{'auction_multi_item'})  && ($params->{'auction_multi_item'}>0)) { $item_number = '**MULTI AUCTION**'; }
elsif (($params->{'num_cart_items'})  && ($params->{'num_cart_items'}>0)) { $item_number = '**MULTI CART**'; }

$item_number = $dbh->quote($item_number);

my $paypal_id   = $dbh->quote(defined($params->{'txn_id'})?$params->{'txn_id'}:'');
	$params->{'DEBUG'} = "THIS WAS DELIVERED TO NOTIFY.";
my $content     = $dbh->quote(&ZTOOLKIT::hashref_to_xmlish($params,'sort'=>1));
my $t = time();
my $pstmt = "insert into PAYPAL_QUEUE (PAYPAL_ID,USERNAME,MID,CREATED,ITEM_NUMBER,INVOICE,DATA,SRC) values ($paypal_id,$username,$mid,$t,$item_number,$invoice,$content,'NOTIFY')";
$dbh->do($pstmt);
&DBINFO::db_zoovy_close();


## new code to disable IPN
print "Pragma: no-cache\n";           # HTTP 1.0 non-caching specification
print "Cache-Control: no-cache\n";    # HTTP 1.1 non-caching specification
print "Expires: 0\n";                 # HTTP 1.0 way of saying "expire now"
print "Content-type: text/plain\n\n";
print "OK\n";

## no more.
exit;
