#!/usr/bin/perl

use lib "/httpd/ebayapi/modules";
use CGI;
use EBAYAPI;
use lib "/httpd/servers/modules";
use ZOOVYLITE;

$q = new CGI;
my $MERCHANT = $q->param('merchant');
my $PRODUCT = $q->param('product');


my $EBAY_ID = 0;
my $QUANTITY = -1;
my $ITEMSOLD = 0;
my $PRICE = 0;

if ($PRODUCT ne '') {
	$dbh = &EBAYAPI::db_ebay_connect();
	$pstmt = "select EBAY_ID,QUANTITY,ITEMS_SOLD,DATA from STORE_MONITOR_QUEUE where MERCHANT=".$dbh->quote($MERCHANT)." and PRODUCT=".$dbh->quote($PRODUCT)." limit 0,1";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	if ($sth->rows()>0) {
		($EBAY_ID,$QUANTITY,$ITEMSOLD,$DATA) = $sth->fetchrow();
		%data = &ZOOVYLITE::attrib_handler($DATA);
		$PRICE = $data{'ebaystores:price'};
		}
	$sth->finish();
	&EBAYAPI::db_ebay_close();
	}

print "Content-type: text/xml\n\n";
print "<?xml version=\"1.0\"?>\n";
print "<ProdInfo>\n";
print "<StoreItem>$EBAY_ID</StoreItem>\n";
print "<StoreQty>".($QUANTITY-$ITEMSOLD)."</StoreQty>\n";
print "<StorePrice>".sprintf("%.2f",$PRICE)."</StorePrice>\n";
print "</ProdInfo>\n";
