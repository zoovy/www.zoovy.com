#!/usr/bin/perl

use Data::Dumper; 
use HTTP::Headers;
use HTTP::Request;

## QBONLINE APPID FROM PETER 3/29/05
## 78834671 == webapi.zoovy.com:webapi.zoovy.com
##
## QBMS BETA APPID -- generated 3/29/05
##	57015567 == zoovyapplogin:webapi.zoovy.com
##
## QBMS PRODUCTION APPID -- generated 5/23/05
##	83166487 == webapi.zoovy.com:z00vyinc	[generates error: not designed to work with 1002]
##
## QBMS PRODUCTION APPID -- generated 5/23/05
##	83162751 -- webapi.zoovy.com:z00vy (production)	U: becky@zoovy.com P:qbnzoovy
##	58002316 -- webapi.zoovy.com:z00vy (development)
## 


# $APPID = 79496516;
# $CONNTKT = 'TGT-48-geOBEppZtOvdOg2_jgXa7A';
# $AUTHID = '79503152';

# DEFAULT SSL VERSION
$ENV{HTTPS_VERSION} = '3';

# CLIENT CERT SUPPORT
$ENV{HTTPS_DEBUG} = 1;

# CLIENT CERT SUPPORT
# $ENV{HTTPS_CERT_FILE} = 'certs/webapi.zoovy.com.cer'; $ENV{HTTPS_KEY_FILE}  = 'certs/webapi.zoovy.com.key';
$ENV{HTTPS_CERT_FILE} = 'certs/z00vy.cer'; $ENV{HTTPS_KEY_FILE}  = 'certs/z00vy.key';

# CA CERT PEER VERIFICATION
$ENV{HTTPS_CA_FILE}   = 'certs/intuit.crt';
$ENV{HTTPS_CA_DIR}    = 'certs/';

use lib "/httpd/modules";
use ZPAY::QBMS;

my $conntkt = 'TGT-231-GgTZY1eoSEh4PVDJ0Q8QDQ';

$USERNAME = 'brian';
$webdb = &ZWEBSITE::fetch_website_dbref($USERNAME);

my $contentd = &ZPAY::QBMS::qbms_signonmsg($USERNAME,$webdb);

$contente = qq~
	<QBMSXMLMsgsRq>
	<CustomerCreditCardChargeRq requestID="2">
		<CreditCardNumber>4111111111111111</CreditCardNumber>
		<ExpirationMonth>12</ExpirationMonth>
		<ExpirationYear>2008</ExpirationYear>
		<Amount>399.99</Amount>
		<CreditCardAddress>2500 Garcia Ave</CreditCardAddress>
		<CreditCardPostalCode>94043</CreditCardPostalCode>
		<CommercialCardCode>JDoe</CommercialCardCode>
		<SalesTaxAmount>3.99</SalesTaxAmount>
		<CardSecurityCode>DOE1</CardSecurityCode>
		
	</CustomerCreditCardChargeRq>
	</QBMSXMLMsgsRq>
~;

##
##
##

## From: QBXML docs:
$contenta = qq~<?xml version="1.0"?>
<!DOCTYPE QBMSXML PUBLIC '-//INTUIT//DTD QBMSXML QBMS 1.0//EN' 'http://merchantaccount.ptc.quickbooks.com/dtds/qbmsxml10.dtd'>
<QBMSXML>
	$contentd
	$contente
</QBMSXML>
~;





$content = $contenta . $contentb . $contentc;
print $content;

use XML::Parser;
use XML::Parser::EasyTree;
my $parser = new XML::Parser(Style=>'EasyTree');
my $tree = $parser->parse($content);
#print Dumper($tree);
#exit;


use LWP::UserAgent;
my $ua = new LWP::UserAgent;
my $header = HTTP::Headers->new();
$header->header('Content-Type' => 'application/x-qbmsxml'); 
my $req = new HTTP::Request('POST', 'https://webmerchantaccount.ptc.quickbooks.com/j/AppGateway', $header, $content);
my $res = $ua->request($req);
print $res->code."\n";
print Dumper($res);

exit;


my $req = new HTTP::Request('GET', "https://login.quickbooks.com/j/qbn/sdkapp/connauth?appid=$APPID&serviceid=2004&conntkt=$CONNTKT&sessiontkt=");
my $res = $ua->request($req);
print $res->code."\n";
print Dumper($res);




$x = qq~
where
-https://login.quickbooks.com/j/qbn/sdkapp/connauth
is the location of the confirmation page.

-appid
is the appID assigned to your application when you registered the
application.
-conntkt
is connection ticket from the authorization.
myTkt
is the (first) session ticket obtained from the authorization.


In the following snippet, the callback checks for the presence of the
session ticket, and if there is one, constructs the confirmation URL, 
and invokes GET using that URL. The first four characters in this 
response are the session ticket, so this is parsed and stored.

if (tkt != null) {
log("In processQBTicket, need to process new sess ticket");
String mySubSvr = "https://login.quickbooks.com";
String loginPath = "/j/qbn/sdkapp/connauth";
String myTkt = tkt;
String authURL = mySubSvr + loginPath + "?appid=" + appid
+ "&serviceid=2004" + "&conntkt=" + conntkt
+ "&sessiontkt=" + myTkt;
log("\tauthURL = " + authURL);
try {
String resp = doRequest(authURL, "", "GET");
log("Result from authURL is: " + resp);
String status = resp.substring(0, 3);
if (status.compareTo("000") != 0) {
String err = "Problem updating session ticket: "
+ status;
log(err);
} else {
resp = resp.substring(4);
storeTicket(appdata,"sessiontkt",resp);
}
} catch (Exception e) {
log("process Session Ticket caught exception: " + e.toString());
}
}
~;