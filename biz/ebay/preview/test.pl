#!/usr/bin/perl


use lib "/httpd/modules";
use ZTOOLKIT::XMLUTIL;

$VAR1 = { 'xmlns' => 'urn:ebay:apis:eBLBaseComponents', 'Version' => '673', 'Build' => 'E673_CORE_BUNDLED_11353683_R1', 'Timestamp' => '2010-06-17T22:35:05.534Z', 'Errors' => { '{urn:ebay:apis:eBLBaseComponents}ErrorParameters' => { '{urn:ebay:apis:eBLBaseComponents}Value' => 'Item.ShippingDetails.InternationalInsuranceDetails.InsuranceOption', 'ParamID' => '0' }, '{urn:ebay:apis:eBLBaseComponents}ErrorClassification' => 'RequestError', '{urn:ebay:apis:eBLBaseComponents}ShortMessage' => 'Input data is invalid.', '{urn:ebay:apis:eBLBaseComponents}ErrorCode' => '37', '{urn:ebay:apis:eBLBaseComponents}SeverityCode' => 'Error', '{urn:ebay:apis:eBLBaseComponents}LongMessage' => 'Input data for tag  is invalid or missing. Please check API documentation.' }, 'Ack' => 'Failure' }; 
&ZTOOLKIT::XMLUTIL::stripNamespace($VAR1);
use Data::Dumper;
print Dumper($VAR1);



