#!/usr/bin/perl

use Data::Dumper;

use strict;
use CGI::Lite;
use XML::Simple;
use lib "/httpd/modules";
use ZSHIP;
use CART2;

##
## callback.cgi
##
## processes inbound callback requests from checkout by amazon (CBA)
##	http://amazonservices.s3.amazonaws.com/Payments/documents/Callback_API_Guide.pdf
## (code still needs modifications, ie copied from paypal/ec-callback.cgi)

my $q = new CGI;
my %v = ();
# Signature=([a-zA-Z0-9]+)\&UUID=([a-z0-9\-])\&Timestamp=(.*)\&ordercalculations-request=(.*)/) {
foreach my $p ($q->param()) {
	$v{"$p"} = $q->param($p);
	}


## REQUEST
## will need to modify per CBA specs
## https://webapi.zoovy.com/webapi/amazon/callback.cgi?
## 	Signature=[Signature_value]&UUID=[UUID_value]&Timestamp=[Timestamp_value]&ordercalculations-request=[request_value]
##
## values need to be decoded
foreach my $str (split(/\//,$ENV{'REQUEST_URI'})) {
  next unless ($str =~ /\=/);
  my ($k1,$v1) = split(/=/,$str);
  $v{"_$k1"} = $v1;
  }

## parse out REQUEST, 
##	calculate promos, shipping, taxtables
##
## - define itemsref, fyi Ids are really codes not numbers
##	$itemsref->{$SKU}->{'TaxTableId'}
##	$itemsref->{$SKU}->{'PromotionIds'}
##	$itemsref->{$SKU}->{'ShippingMethodIds'}
## - populate definitions for Ids
##	use $taxtableref, $promosref, $methodsref or output directly to ID DEFINITIONs
my $requestAddressXML = '';	## pull from REQUEST	
## example:
##		  <AddressId>addressId1</AddressId>
##		  <AddressFieldOne>123 Fir St.</AddressFieldOne>
##		  <AddressFieldTwo>Apartment 109</AddressFieldTwo>
##		  <City>Seattle</City>
##		  <State>WA</State>
##		  <PostalCode>98104</PostalCode>
##		  <CountryCode>US</CountryCode>
my $itemsref = (); my $promosref = (); my $taxtableref = ();


#%v = (
#          '_prt' => '0',
#          'aws-access-key-id' => 'AKIAIR62HCONZEQMDAPA',
#          '_u' => 'smbsi',
#          'order-calculations-request' => '<?xml version="1.0" encoding="UTF-8"?><OrderCalculationsError xmlns="http://payments.amazon.com/checkout/2008-11-30/"><OrderCalculationsErrorCode>HttpError</OrderCalculationsErrorCode><OrderCalculationsErrorMessage>Either there was a problem connecting to your endpoint or the merchant endpoint returned an invalid response status code.</OrderCalculationsErrorMessage><OrderCalculationsRequest xmlns="http://payments.amazon.com/checkout/2008-11-30/"><CallbackReferenceId>1-dfe8b93d-160e-4513-89de-0534d816463e</CallbackReferenceId><OrderCalculationCallbacks><CalculateTaxRates>true</CalculateTaxRates>
#<CalculatePromotions>false</CalculatePromotions>
#<CalculateShippingRates>true</CalculateShippingRates>
#<OrderCallbackEndpoint>https://webapi.zoovy.com/webapi/amazon/callback.cgi/u=smbsi/prt=0/c=JfDnYc9RoX1z0wx0zpbvlV0mK</OrderCallbackEndpoint>
#<ProcessOrderOnCallbackFailure>false</ProcessOrderOnCallbackFailure>
#</OrderCalculationCallbacks><ClientRequestId>JfDnYc9RoX1z0wx0zpbvlV0mK</ClientRequestId><IntegratorId>ZOOVY</IntegratorId><IntegratorName>ZOOVY</IntegratorName><Cart>
#<Items>
#<Item><SKU>OCCINTERLACEDISCT</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>  OCC Lip Tar Discontinued Packaging - Interlace</Title>
#<Price><Amount>8.00</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>1</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#<Item><SKU>OCCTONEDISCT</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>  OCC Lip Tar Discontinued Packaging - Tone</Title>
#<Price><Amount>8.00</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>1</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#<Item><SKU>OCCCLEARDISCT</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>OCC Lip Tar Discontinued Packaging - Clear - A MUST HAVE!!!</Title>
#<Price><Amount>8.00</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>1</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#<Item><SKU>OCCMELANGEDISCT</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>  OCC Lip Tar Discontinued Packaging - Melange</Title>
#<Price><Amount>8.00</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>1</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#<Item><SKU>OCCLIPTARGRANDMA</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>  OCC Lip Tar - Grandma</Title>
#<Price><Amount>16.00</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>1</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#</Items>
#
#</Cart><CallbackOrders><CallbackOrder><Address><AddressId>jmmknxmoko</AddressId></Address><CallbackOrderItems><CallbackOrderItem><SKU>OCCINTERLACEDISCT</SKU></CallbackOrderItem><CallbackOrderItem><SKU>OCCTONEDISCT</SKU></CallbackOrderItem><CallbackOrderItem><SKU>OCCCLEARDISCT</SKU></CallbackOrderItem><CallbackOrderItem><SKU>OCCMELANGEDISCT</SKU></CallbackOrderItem><CallbackOrderItem><SKU>OCCLIPTARGRANDMA</SKU></CallbackOrderItem></CallbackOrderItems></CallbackOrder></CallbackOrders></OrderCalculationsRequest><OrderCalculationsResponse><![CDATA[The OrderCalculationsResponse provided was not returned or was considered invalid. Please consult the documentation for the valid response format.]]></OrderCalculationsResponse></OrderCalculationsError>',
#          'Timestamp' => '2012-10-25T00:22:15.330Z',
#          'Signature' => 'wrhRXg9ltrLnDSuyOIKLBTYkvIY=',
#          '_c' => 'JfDnYc9RoX1z0wx0zpbvlV0mK',
#          'UUID' => 'a901d565-0e07-4276-82f8-3d51d4f4f9e1'
#        );
#
#
#%v = (
#          '_prt' => '0',
#          'aws-access-key-id' => 'AKIAIR62HCONZEQMDAPA',
#          '_u' => 'smbsi',
#          'order-calculations-request' => '<?xml version="1.0" encoding="UTF-8"?><OrderCalculationsError xmlns="http://payments.amazon.com/checkout/2008-11-30/"><OrderCalculationsErrorCode>HttpError</OrderCalculationsErrorCode><OrderCalculationsErrorMessage>Either there was a problem connecting to your endpoint or the merchant endpoint returned an invalid response status code.</OrderCalculationsErrorMessage><OrderCalculationsRequest xmlns="http://payments.amazon.com/checkout/2008-11-30/"><CallbackReferenceId>2-bcaffab2-db57-48fc-b59d-656cd8dafb6d</CallbackReferenceId><OrderCalculationCallbacks><CalculateTaxRates>true</CalculateTaxRates>
#<CalculatePromotions>false</CalculatePromotions>
#<CalculateShippingRates>true</CalculateShippingRates>
#<OrderCallbackEndpoint>https://webapi.zoovy.com/webapi/amazon/callback.cgi/u=smbsi/prt=0/c=1ziOHi9S2j1opV12MhpXv4r4L</OrderCallbackEndpoint>
#<ProcessOrderOnCallbackFailure>false</ProcessOrderOnCallbackFailure>
#</OrderCalculationCallbacks><ClientRequestId>1ziOHi9S2j1opV12MhpXv4r4L</ClientRequestId><IntegratorId>ZOOVY</IntegratorId><IntegratorName>ZOOVY</IntegratorName><Cart>
#<Items>
#<Item><SKU>UDESBLAZE</SKU>
#<MerchantId>AS99Q4LOPAXSN</MerchantId>
#<Title>URBAN DECAY Eye Shadow - Blaze</Title>
#<Price><Amount>10.99</Amount><CurrencyCode>USD</CurrencyCode>
#</Price><Quantity>4</Quantity>
#<Weight><Amount>0.12</Amount>
#<Unit>lb</Unit>
#</Weight>
#<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
#</Item>
#</Items>
#
#</Cart><CallbackOrders><CallbackOrder><Address><AddressId>jnmpkrjsll</AddressId></Address><CallbackOrderItems><CallbackOrderItem><SKU>UDESBLAZE</SKU></CallbackOrderItem></CallbackOrderItems></CallbackOrder></CallbackOrders></OrderCalculationsRequest><OrderCalculationsResponse><![CDATA[The OrderCalculationsResponse provided was not returned or was considered invalid. Please consult the documentation for the valid response format.]]></OrderCalculationsResponse></OrderCalculationsError>',
#          'Timestamp' => '2012-10-31T03:02:06.072Z',
#          'Signature' => 'LBSBp3BgBKG4JFwquS8Ne35YN8c=',
#          '_c' => '1ziOHi9S2j1opV12MhpXv4r4L',
#          'UUID' => '342bff27-c6a3-460a-9125-81c817d0ce74'
#        );
#
#

my ($udbh) = &DBINFO::db_user_connect($v{'_u'});

if ($v{'order-calculations-error'}) {
	## hmm.. maybe generate a ticket?
	&ZOOVY::confess($v{'_u'},"AMAZON CBA CALLBACK ERROR".Dumper(\%ENV,\%v));
	}

## dump request to temp file
use Data::Dumper;
#open F, ">>/tmp/amazoncallback.txt.".time();
#@print F Dumper(\%v);
#close F;

### to create the inbound signature we:
###	concatenate UUID and timestamp calculate HMAC_SHA1 using your access key id and then URI encode it.
## print STDERR Dumper($v{'order-calculations-request'});

my ($x) = XML::Simple::XMLin($v{'order-calculations-request'}, ForceArray=>1);

print STDERR 'V IS: '.Dumper(\%v);

my ($CART2) = CART2->new_persist($v{'_u'},int($v{'_prt'}),$v{'_c'},'create'=>0);
if (not defined $CART2) {
	my ($MID) = int(&ZOOVY::resolve_mid($v{'_u'}));
	my ($qtCARTID) = $udbh->quote($v{'_c'});
	my $pstmt = "select CART from AMZPAY_ORDER_LOOKUP where MID=$MID and CARTID=$qtCARTID";
	print STDERR "$pstmt\n";
	my ($xml) = $udbh->selectrow_array($pstmt);
	print STDERR "XML:$xml\n";
	if ($xml ne '') {
		$CART2 = CART2->new_memory()->from_xml($xml,CART2::v(),"amzcba-callback"); 
		if (ref($CART2) eq 'CART2') { 
			$CART2->add_history("CBA Had to recover from XML backu");
			}
		}
	}



#print Dumper($CART2);
#die();


my $address = $x->{'CallbackOrders'}->[0]->{'CallbackOrder'}->[0]->{'Address'}->[0];
$CART2->in_set('ship/address1',$address->{'AddressFieldOne'}->[0]);
$CART2->in_set('ship/postal', $address->{'PostalCode'}->[0]);
$CART2->in_set('ship/city', $address->{'City'}->[0]);
$CART2->in_set('ship/region', $address->{'State'}->[0]);
#$CART2->in_set('ship/countrycode', $address->{'CountryCode'}->[0]);
## made this change 2009-07-22 patti - should fix intl shipping issues
$CART2->in_set('ship/countrycode', $address->{'CountryCode'}->[0]);
$CART2->shipmethods('flush'=>1);  

my $itemshipxml = '';		## goes inside the <ShippingMethods>
my $shipxml = '';		## goes inside the <ShippingMethodIds>

## SHIPPING
##
## interate through shipping methods to create two xml strings:
##	itemshipxml (goes inside items), and shipxml (goes at bottom)
##
require ZSHIP;
foreach my $shipmethod (@{$CART2->shipmethods()}) {

	## this 'next' forces us only to grab the first (and least expensive) method
	## which gets assigned to ServiceLevel Standard
	##	we currently do not support Expediated, etc
	next unless ($itemshipxml eq '');
	
	$itemshipxml .= '<ShippingMethodId>'.$shipmethod->{'id'}.'</ShippingMethodId>';

	$shipxml .= "<ShippingMethod>\n";
	$shipxml .= &tag("ShippingMethodId",$shipmethod->{'id'});
	
	## ServiceLevel, Amz defined (OneDay | TwoDay | Standard | Expedited)
	$shipxml .= &tag("ServiceLevel","Standard");
	
	$shipxml .= "<Rate>\n";
	## WeightBased, ItemQuantityBased, or ShipmentBased	
	$shipxml .= "<ShipmentBased>";

	my ($price) = $shipmethod->{'amount'};
	## 9/24/09 - apparently amazon has no support for handling, or insurance. so we'll combine with shipping.
	$price += $CART2->in_get('sum/hnd_total');
	$price += $CART2->in_get('sum/spc_total');
	$price += $CART2->in_get('sum/ins_total');
	$shipxml .= &priceTag($price);

	#$shipxml .= &priceTag(3.50);
	$shipxml .= "</ShipmentBased>";
	$shipxml .= "</Rate>\n";
	
	$shipxml .= "<IncludedRegions>\n";
	$shipxml .= &tag("USZipRegion",$address->{'PostalCode'}->[0]);
	$shipxml .= "</IncludedRegions>\n";
	
	## if shipping not supported for this order...
	## also send the below code (fyi - IncludedRegions is also required, even if it's the same zip)
	#$shipxml .= "<ExcludedRegions>\n";
	#$shipxml .= &tag("USZipRegion",$methodsref->{$methodid}->{'Zip'});
	#$shipxml .= "</ExcludedRegions>\n";
	
	$shipxml .= "</ShippingMethod>\n";
	}

if ($itemshipxml eq '') {
   use Data::Dumper;
   open F, ">>/tmp/amzcba-$v{'_u'}-".time();
   print F Dumper($CART2);
   close F;
   }


## TAXES
##
## goes inside <TaxTables>
my $taxxml .= "<TaxTable>\n";
$taxxml .= &tag("TaxTableId","TAX01");
$taxxml .= "<TaxRules><TaxRule>\n";
	
## Rate, use format .075 for 7.5%
my $calculate_tax = 0;
my $tax_rate = sprintf("%.4f",$CART2->in_get('our/tax_rate')/100);
$taxxml .= &tag("Rate",$tax_rate);
$taxxml .= &tag("IsShippingTaxed",($CART2->in_get('is/shp_taxable')==1?'true':'false'));
$taxxml .= &tag("USZipRegion",$address->{'PostalCode'}->[0]);
$taxxml .= "</TaxRule></TaxRules></TaxTable>\n";


## RESPONSE
## build XML response to use in order-calculations-response
my $xml = "";
$xml .= qq~<?xml version="1.0" encoding="UTF-8"?>~;
$xml .= qq~<OrderCalculationsResponse xmlns="http://payments.amazon.com/checkout/2008-11-30/">~;
$xml .= "<Response>";
$xml .= "<CallbackOrders>\n<CallbackOrder>\n";
$xml .= "<Address><AddressId>".$address->{'AddressId'}->[0]."</AddressId></Address>\n";	## this info is in the REQUEST
$xml .= "<CallbackOrderItems>";
## go thru each item in the order (from request)
## return tax, promotions, shipping methods
## validate to make sure cart geometry hasn't changed.
foreach my $item (@{$x->{'Cart'}->[0]->{'Items'}->[0]->{'Item'}}) {
	$xml .= "<CallbackOrderItem>";
	$xml .= &tag("SKU",$item->{'SKU'}->[0]);

	## comment out to turn off Tax Calculations
	$xml .= 	"<TaxTableId>TAX01</TaxTableId>";
	
	## Promotions
	## REMEMBER: this needs to match OrderCalculationCallbacks in ZPAY::AMZPAY
	#$xml .= "<PromotionIds>";
	#foreach my $promo (@{$itemsref->{$SKU}->{'PromotionIds'}}) {
	#	$xml .= &tag("PromotionId",$promo);	 
	#	}
	#$xml .= "</PromotionIds>";
	 
	## Shipping Methods
	$xml .= "<ShippingMethodIds>";	
	$xml .= $itemshipxml;
	$xml .= "</ShippingMethodIds>";

	$xml .= "</CallbackOrderItem>"
	}	
$xml .= "</CallbackOrderItems>\n</CallbackOrder>\n</CallbackOrders>\n</Response>\n";


## ID DEFINITIONS
## Promotion defns
## (this xml could/should be defined above when getting promo info, vs putting in hash)
#$xml .= "<Promotions>\n";
#foreach my $promoid (@{$promosref}) {
#	$xml .= "<Promotion>\n";
#	$xml .= &tag("PromotionId",$promoid);
#	$xml .= &tag("Description",$promosref->{$promoid}->{'Description'});
#	
#	$xml .= "<Benefit>\n";
#	## FixedAmountDiscount or DiscountRate	
#	$xml .= "<".$promosref->{$promoid}->{'BenefitType'}.">";
#	$xml .= &priceTag($promosref->{$promoid}->{'Amount'});
#	$xml .= "</".$promosref->{$promoid}->{'BenefitType'}.">\n";
#	$xml .= "</Benefit>\n</Promotion>\n";
#	}
#$xml .= "</Promotions>\n";

## comment out to turn off Tax Calculations
$xml .= "<TaxTables>\n".$taxxml."</TaxTables>";
$xml .= "<ShippingMethods>\n".$shipxml."</ShippingMethods>";

$xml .= "</OrderCalculationsResponse>\n";
## end of XML RESPONSE	


## create URL-encoded response callback
## order-calculations-response=[response_value]&Signature=[Signature_value]&aws-accesskey-id=[access_key_value]
## 	Signature/aws-accesskey-id - should only be included for signed carts (setting in SellerCentral)



print "Content-type: text/html; charset=utf-8\n\n";

use URI::Escape;
print "order-calculations-response=".URI::Escape::uri_escape($xml);

my $digest = '';
if (1) {
	## soooper secret signing stuff.
	my $webdbref = &ZWEBSITE::fetch_website_dbref($CART2->username(),$CART2->prt());
	my $sk = $webdbref->{'amz_secretkey'};

	use Digest::HMAC_SHA1;
	use MIME::Base64;
	my $hmac = Digest::HMAC_SHA1->new($sk);
	$hmac->add($xml);
	$digest = MIME::Base64::encode_base64($hmac->digest);
	
	## important line, don't remove!!
	$digest =~ s/[\n\r]+//gs;
	
	$digest = URI::Escape::uri_escape($digest);	
	print "&Signature=$digest";
	my $awskey = URI::Escape::uri_escape($webdbref->{'amz_accesskey'});
	print "&aws-access-key-id=$awskey";
	}

open F, ">/tmp/amazontax.request.".time();
print F $xml;
#print F Dumper(\%rc);
print F $taxxml."\n";
#print F Dumper($cart);
close F;

## subs copied from ZPAY::AMZPAY.pm, let's put them somewhere more general?
## encode content, put in XML
sub tag {
	my ($tag,$content) = @_;
	if ($content eq '') { return(); }
	return("<$tag>".&ZOOVY::incode($content)."</$tag>\n");
	}

## encode content, format as price put in XML
sub priceTag {
	my ($price) = @_;
	my $tags = &tag("Amount",sprintf("%.2f",$price)).&tag("CurrencyCode","USD");
	$tags =~ s/[\n\r]+//g;
	$tags = "$tags\n";
	return($tags);
	}


&DBINFO::db_user_close();

__DATA__
REQUEST
<?xml version="1.0" encoding="UTF-8"?>
<OrderCalculationsRequest xmlns="http://payments.amazon.com/checkout/2008-11-30/">
/* */
/* THIS IS THE UNIQUE CALLBACKREFERENCEID FOR THIS REQUEST */
/* */
<CallbackReferenceId>
1-f1b06763-b30c-47de-ab95-b4d8fef91ef5
</CallbackReferenceId>
/* */
/* THIS SECTION IS A COPY OF THE MERCHANTCALCULATIONCALLBACK */
/* SECTION YOU SENT IN THE CART XML */
/* */
<OrderCalculationCallbacks>
<CalculateTaxRates>true</CalculateTaxRates>
<CalculatePromotions>true</CalculatePromotions>
<CalculateShippingRates>true</CalculateShippingRates>
<OrderCallbackEndpoint>https://my.endpoint.com/receive.php</OrderCallbackEndpoint>
<ProcessOrderOnCallbackFailure>true</ProcessOrderOnCallbackFailure>
</OrderCalculationCallbacks>
/* */
/* THIS SECTION IS A COPY OF THE ORDER INFORMATION IN THE CART XML */
/* */
<ClientRequestId>1A2B3C4D5E</ClientRequestId>
<IntegratorId>VWXYZ98765VWXYZ</IntegratorId>
<IntegratorName>IntegratorWorld</IntegratorName>
<Cart>
<Items>
<Item>
<SKU>JKL909</SKU>
<MerchantId>AEIOU1234AEIOU</MerchantId>
<Title>Calvin and Hobbes Reliquary</Title>
<Description>By Bill Watterson</Description>
<Price>
<Amount>29.99</Amount>
<CurrencyCode>USD</CurrencyCode>
</Price>
<Quantity>3</Quantity>
<Weight>
<Amount>2.0</Amount>
<Unit>lb</Unit>
</Weight>
<URL>mysite.com/item?909</URL>
<Category>Books</Category>
<Condition>New</Condition>
The Callback API Guide
<FulfillmentNetwork>MERCHANT</FulfillmentNetwork>
<Images>
<Image>
<URL>https://mysite.com/pix?alpha.jpg</URL>
</Image>
</Images>
</Item>
</Items>
</Cart>
/* */
/* THIS SECTION IS THE SHIPPING INFORMATION FOR THE ORDER */
/* YOUR SERVICE USES THIS INFORMATION TO CALCULATE THE REQUIRED */
/* INFORMATION, SHIPPING, TAXES, OR PROMOTIONAL DISCOUNTS */
/* */
	<CallbackOrders>
	 <CallbackOrder>
		<Address>
			<AddressId>addressId1</AddressId>
			<AddressFieldOne>123 Fir St.</AddressFieldOne>
			<AddressFieldTwo>Apartment 109</AddressFieldTwo>
			<City>Seattle</City>
			<State>WA</State>
			<PostalCode>98104</PostalCode>
			<CountryCode>US</CountryCode>
		</Address>
		<CallbackOrderItems>
			<CallbackOrderItem>
			 <SKU>JKL909</SKU>
			</CallbackOrderItem>
		</CallbackOrderItems>
	 </CallbackOrder>
	</CallbackOrders>
</OrderCalculationsRequest>

##########
RESPONSE
Response 	Contains one of the two types of responses, CallbackOrders or Error.
CallbackOrders 	Used to specify all the information for various CallbackOrders in the callback
					 request. CallbackOrders must have at least one CallbackOrder section.
TaxTables 	Referenced from the order.xsd; contains the same information as
					 TaxTables used if it occurred in cart XML. Indicates tax rates calculation
					 information for SKUs or items in the order. TaxTables contains
					 TaxTableIds specified at CallbackOrderItem level for each
					 CallbackOrderItem if requested.
Promotions 	Referenced from the order.xsd; contains the same information as
					 Promotions element if it is present in the cart XML. Promotions contains
					 definitions for promotion IDs specified at the CallbackOrderItem level for
					 each CallbackOrderItem if requested.
ShippingMethods Referencedfrom the order.xsd; contains the same information as
					 ShippingMethods element if it is present in the cart XML.
					 ShippingMethods contains definitions for ShippingMethodIds that are
					 specified at the CallbackOrderItem level for each CallbackOrderItem if
					 requested.
CartPromotionId Referenced from the order.xsd; contains the same information as in the
					 order.xsd. CartPromotionId is a string that represents the PromotionId
					 that overrides all promotions on the order. If specified, this overrides any
					 PromotionId specified at CallbackOrderItem level
Error 		Indicates that an error occurred generating response in your webservice.

Valid Callback Response Example
Here is a valid callback response, formatted as readable XML, with tax tables, promotions, and
shipping methods included in the response. It assumes an order going to a Seattle address, and
provides four shipping options for the buyer. It also calculates a 6% tax rate for the order total and
the shipping charges, and provides a $10.00-off promotion.
