#!/usr/bin/perl


use lib "/httpd/modules";
use ORDER;
use GIFTCARD;
use DBINFO;
use ZOOVY;
use ZTOOLKIT;


#my ($OID) = ORDER::lookup_cartid('rickf','fDO6cQGdsXdnGNFHHWmOHcRsE');
if (my $OID = ORDER::lookup_cartid('rickf','kAm9PzkWdiywp8VbxwIXPxl16')) {
	print "OID:$OID\n";
	}

die();

$USERNAME = 'hotnsexymama';

      my ($gcref) = &GIFTCARD::list($USERNAME,TS=>0);
      $XML = &ZTOOLKIT::arrayref_to_xmlish_list($gcref,'tag'=>'GIFTCARD',content=>'log');
      $XML = "<GIFTCARDS TS=\"".(time()-1)."\">$XML</GIFTCARDS>";

print "XML:$XML\n";

$XML =~ s/\<GIFTCARDS.*?\>(.*?)\<\/GIFTCARDS\>/$1/s;
my $ref = &ZTOOLKIT::xmlish_list_to_arrayref($XML,tag_attrib=>'GIFTCARD');
use Data::Dumper; print Dumper($ref);

print $XML."\n";