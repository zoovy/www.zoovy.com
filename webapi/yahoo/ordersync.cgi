#!/usr/bin/perl -w
#


#ERROR 1054 (42S22): Unknown column 'ID' in 'order clause'
#mysql> desc YAHOOSTORE_QUEUE;
#+---------------+------------------+------+-----+---------------------+-------+
#| Field         | Type             | Null | Key | Default             | Extra |
#+---------------+------------------+------+-----+---------------------+-------+
#| USERNAME      | varchar(20)      | NO   | MUL |                     |       |
#| CREATED       | datetime         | NO   |     | 0000-00-00 00:00:00 |       |
#| DATA          | mediumtext       | NO   |     |                     |       |
#| PROCESSED_GMT | int(10) unsigned | NO   |     | 0                   |       |
#+---------------+------------------+------+-----+---------------------+-------+
#4 rows in set (0.00 sec)


# Install (a modified version of) this program in your webserver's cgi-bin directory.
# 
# This demo program prints the order into /tmp/yahoo-order; you will probably want
# to do something more interesting with it. Replace the function handle_order
# It also puts the raw key-value fields into /tmp/yahoo-order.raw
#
# Order fields are:
#
# ID
#   A unique order identifier including the Y! Store account name, such as acme-451
#   
# Date
#   Standard date format, in GMT
# 
# {Ship,Bill}-Name, -Firstname, -Lastname
#   These fields are always defined. If your store is configured to have separate first and last
#   name fields on the order page, then -Name will be the concatenation of them. If it is configured to have
#   a single entry field, then the split into Firstname and Lastname will be a guess.
#
#   If you have custom fields, they will appear here too. The field names look like "Ship-Pack in dry ice"
#   for an extra shipping field, and similarily for a billing field.
#
# {Ship,Bill}-Address1, -Address2, -City, -State, -Zip, -Country, -Phone, -Email
#   The shipping and billing address. Both will be filled in, and will be the same if the
#   user only gave one address
#
# Card-Name, -Number, -Expiry
#   Credit card info
#
# Item-Id-N, -Code-N, -Quantity-N, -Unit-Price-N, -Description-N, -Url-N,
#   For values of N from 1 to Item-Count, the relevant attributes of each item are given.
#   This script contains code to separate these into an @items array.
#   Code is from the "Code" field when editing the item, typically an SKU or ISBN
#   Unit-Price takes any quantity pricing into account
#
# Tax-Charge, Shipping-Charge, Total
#   Extra charges, and the order total
# 

require 5.001;
use strict;


if ($ENV{'REQUEST_METHOD'} ne "POST") {
	print "Content-type: text/html\n\n";
	print "You are not using this correctly, you must post an order.\n";
	die("Expecting a POST, bailing");
}

use lib "/httpd/modules";
use ZOOVY;
use ZWEBSITE;
use INVENTORY;
use DBINFO;
require ORDER;
use Data::Dumper;
my $USERNAME = 'def'; 
my $PASS = 'def';


my $URI = $ENV{'REQUEST_URI'}.'/';	# make sure we have a trailing /

## make sure we have credentials
if ($URI =~ /user\=(.*?)\//s) {
	$USERNAME = $1;
	} else {
	print "Status: 400\n";
	print "Content-type: text/plain\n";
	print "argh. no username $ENV{'HTTP_REFERER'} \n";
	exit;
	}
if ($URI =~ /pass\=(.*?)\//s) {
	$PASS = $1;
	} else {
	print "Status: 400\n";
	print "Content-type: text/plain\n";
	print "argh. no pass\n";
	exit;
	}

my ($yordersync,$yorderpass,$ycustomer,$yoptin,$yprocess,$ynotify,$yorderid) = split(',',&ZWEBSITE::fetch_website_attrib($USERNAME,'yahoo_ordersync'));
if ($PASS ne $yorderpass) {
	print "Status: 400\n";
	print "Content-type: text/plain\n";
	print "argh. username [$USERNAME] order pass [$PASS] is invalid - should be [$yorderpass]\n";
	exit;
	}

my $o;
read(STDIN,$o,$ENV{'CONTENT_LENGTH'});

open(RAW,">/tmp/yahoo-order.raw.".time());
print RAW $o;
close(RAW);


my $dbh = &DBINFO::db_zoovy_connect();
my $pstmt = &DBINFO::insert($dbh,'YAHOOSTORE_QUEUE',{
	USERNAME=>$USERNAME,
	'*CREATED'=>'now()',
	DATA=>$o,
	PROCESSED_GMT=>0,
	},debug=>2);
$dbh->do($pstmt);
&DBINFO::db_zoovy_close();

# A successful delivery is indicated by a good HTTP result code.
print "Status: 200 OK\n";
print "\n";

##
## Closing Logging
##

exit(0);


