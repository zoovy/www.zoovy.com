#!/usr/bin/perl

use CGI;
use Data::Dumper;
use lib "/httpd/modules";
use ZTOOLKIT;

my $q = new CGI;

#$POSTDATA = '';
#while (<>) {
#	$POSTDATA .= $_;
#	}

my $xml = '';
if (0) {
	$xml = '<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body>
<AddVendor>
<Credentials d4p1:APIUsername="becky" d4p1:APIToken="112121121" xmlns:d4p1="http://new.webservice.namespace" />
<VendorDetail d4p1:Contact="Zoovy Test" d4p1:Addr1="123 Main St." d4p1:City="Carlsbad" xmlns:d4p1="http://new.webservice.namespace" /></AddVendor></soap:Body></soap:Envelope>';
	}
elsif ($q->param('POSTDATA')) {
	$xml = $q->param('POSTDATA');
	open F, ">/tmp/soap";
	print F Dumper($q,\%ENV,$q->param('POSTDATA'));
	close F;
	}

use XML::SAX::Simple;
# use XML::Simple;
my $hash = XML::Simple::XMLin($xml,ForceArray=>1,NSExpand=>0);
foreach my $payload (@{$hash->{'soap:Body'}}) {
	my ($cmd) = keys %{$payload};
	# print Dumper($cmd,$payload);
	}

print "Content-Type: text/xml; charset=\"utf-8\"\n\n";
#die();
#print Dumper($hash);
#die();

# http://cpan.uwinnipeg.ca/htdocs/WSDL-Generator/WSDL/Generator.html

# print "Content-Type: text/xml\n\n";

#<?xml version="1.0" encoding="utf-8"?>
#<soap:Envelope
#   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
#   xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
#   xmlns:tns="http://www.zoovy.com/webapi/zoovy-20110801.wsdl"
#   xmlns:types="http://www.zoovy.com/webapi/zoovy-20110801.wsdl/encodedTypes"
#   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
#<soap:Body soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
#<q1:sayHello xmlns:q1="urn:examples:helloservice">
#<firstName xsi:type="xsd:string">Karlo</firstName>
#</q1:sayHello>
#</soap:Body>
#</soap:Envelope>

#print qq~<?xml version="1.0" encoding="utf-8"?>\n~;
#print qq~<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
#<soap:Body>
#<AddSupplierResponse>
#<greeting>hello</greeting>
#</AddSupplierResponse></soap:Body>
#</soap:Envelope>
#~;
#__DATA__


#print q~<?xml version="1.0" encoding="utf-8"?>
#<soap:Envelope 
#	xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
#	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#	xmlns:xsd="http://www.w3.org/2001/XMLSchema">
#<soap:Body>
#<AddVendorResponse xmlns="http://www.webservicex.net/">
#<APIUsername>asdf</APIUsername>
#</AddVendorResponse>
#</soap:Body>
#</soap:Envelope>
#~;
#

#__DATA__


## WORKS:
print q~<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body>
<AddVendorResponse xmlns="http://www.zoovy.com">
<AddVendorResult>
<VendorCode>xyz</VendorCode>
</AddVendorResult>
</AddVendorResponse>
</soap:Body>
</soap:Envelope>
~;

__DATA__
print q~<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body>
<GetGeoIPResponse xmlns="http://www.webservicex.net/">
<GetGeoIPResult>
<ReturnCode>1</ReturnCode>
<IP>192.168.1.000</IP>
<ReturnCodeDetails>Success</ReturnCodeDetails>
<CountryName>Reserved</CountryName>
<CountryCode>BEC</CountryCode>
	<XCode>Test</XCode>
</GetGeoIPResult>
</GetGeoIPResponse>
</soap:Body>
</soap:Envelope>
~;



__DATA__
print q~<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope 
	xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body>
<RegisterWebCspUserReply xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <HighestSeverity xmlns="http://fedex.com/ws/registration/v2">SUCCESS</HighestSeverity>
  <Notifications xmlns="http://fedex.com/ws/registration/v2">
    <Severity>SUCCESS</Severity>
    <Source>fcas</Source>
    <Code>0000</Code>
    <Message>Success</Message>
  </Notifications>
  <Version xmlns="http://fedex.com/ws/registration/v2">
    <ServiceId>fcas</ServiceId>
    <Major>2</Major>
    <Intermediate>1</Intermediate>
    <Minor>0</Minor>
  </Version>
  <Credential xmlns="http://fedex.com/ws/registration/v2">
    <Key>4qMHdrjtQTJQw3Ip</Key>
    <Password>3zxSF3cldeiWu7kIeUdzmIgj4</Password>
  </Credential>
</RegisterWebCspUserReply>
</soap:Body>
</soap:Envelope>

~;

__DATA__


__DATA__

## 

print qq~
<soap:Envelope
   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
   xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
   xmlns:tns="http://www.zoovy.com/webapi/zoovy-20110801.wsdl"
   xmlns:types="http://www.zoovy.com/webapi/zoovy-20110801.wsdl/encodedTypes"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body use="literal">
<AddVendorResponse>
<Vendor QbReferenceID="1" VendorName="1"  VendorCode="1" Phone="1" Email="1" Contact="1" Addr2="1" Addr1="1" City="1">
<QbReferenceID>1</QbReferenceID>
<VendorName>1</VendorName>
<VendorCode>1</VendorCode>
<Phone>1</Phone>
<Email>1</Email>
<Contact>1</Contact>
<Addr2>1</Addr2>
<Addr1>1</Addr1>
<City>1</City>
</Vendor>
</AddVendorResponse>
<DeleteVendorResponse>
<Parameter>The time is: ~.&ZTOOLKIT::pretty_date(time(),2).qq~!</Parameter>
</DeleteVendorResponse>
</soap:Body>
</soap:Envelope>
~;



__DATA__

WORKS:

print qq~
<soap:Envelope
   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
   xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
   xmlns:tns="http://www.zoovy.com/webapi/zoovy-20110801.wsdl"
   xmlns:types="http://www.zoovy.com/webapi/zoovy-20110801.wsdl/encodedTypes"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body use="literal">
<AddVendorResponse>
<Vendor>The time is: ~.&ZTOOLKIT::pretty_date(time(),2).qq~!</Vendor>
</AddVendorResponse>
</soap:Body>
</soap:Envelope>
~;


print qq~<?xml version="1.0" encoding="utf-8"?>\n~;
print qq~
<soap:Envelope
   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
   xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/"
   xmlns:tns="http://www.zoovy.com/webapi/zoovy-20110801.wsdl"
   xmlns:types="http://www.zoovy.com/webapi/zoovy-20110801.wsdl/encodedTypes"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<soap:Body soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<AddVendor>
<greeting xsi:type="xsd:string">The time is: ~.&ZTOOLKIT::pretty_date(time(),2).qq~!</greeting>
<vendor xsi:type="xsd:string">The time is: ~.&ZTOOLKIT::pretty_date(time(),2).qq~!</vendor>

</AddVendor>
</soap:Body>
</soap:Envelope>
~;

