#!/usr/bin/perl

use IO::String;
use XML::SAX::Simple;
use Data::Dumper;
use lib "/httpd/modules";
require ZTOOLKIT::XMLUTIL;
require DBINFO;
require INVENTORY;
require EXTERNAL;



my $xml = q~<INCOMPLETEITEMS>
   <INCOMPLETE ID="0">
      <buyer_email>brian@zoovy.com</buyer_email>
      <sku>sku:1234</sku><product>sku</product>
      <qty>1</qty><price>1.00</price>
      <mkt>US1</mkt>
      <mkt_listingid></mkt_listingid>
      <mkt_transactionid></mkt_transactionid>
      <mkt_orderid></mkt_orderid>
      <prod_name>only if different</prod_name>
      <buyer_userid></buyer_userid>
		<email_msgid>ECREATE</email_msgid>
   </INCOMPLETE>
</INCOMPLETEITEMS>
~;

my $USERNAME = 'brian';
my $PRT = 0;

my ($io) = IO::String->new($xml);
my $ref = eval { XML::SAX::Simple::XMLin($io,ForceArray=>1,ContentKey=>'_content'); };

# print Dumper($ref,$dataref);

print Dumper($ref);
print XML::SAX::Simple::XMLout($ref,'RootName'=>'INCOMPLETE');

foreach my $incarelement (@{$ref->{'INCOMPLETE'}}) {
	

	my $incref = ZTOOLKIT::XMLUTIL::SXMLflatten($incarelement,out=>'');
	print Dumper($incref);
	die();

	## Phase1: data cleanup!
	if (($incref->{'.sku'} ne '') && ($incref->{'.product'} ne '')) {
		## sku and product both set, leave 'em alone
		}
	elsif ($incref->{'.sku'} ne '') {
		($incref->{'.product'}) = &INVENTORY::stid_to_pid($incref->{'.sku'});
		}
	elsif ($incref->{'.product'} ne '') {
		$incref->{'.sku'} = $incref->{'.product'};
		}

	$incref->{'.mkt'} = uc($incref->{'.mkt'});

	if (defined $incref->{'.emailmsg'}) {
		$incref->{'.autoemail'} = 1;
		}
	elsif (not defined $incref->{'.autoemail'}) {
		$incref->{'.autoemail'} = 0;
		}

	## Phase2: prep the data into an array to incomplete

	## change $incref->'.mkt' into $data{'MKT'}
	my %data = ();
	foreach my $k (keys %{$incref}) {
		$data{ uc(substr($k,1)) } = $incref->{$k};
		}
	print Dumper(\%data);

	my ($CLAIM) = &EXTERNAL::create($USERNAME,$PRT,$incref->{'.sku'},\%data,{
		'AUTOEMAIL'=>$incref->{'.autoemail'},
		'EMAIL_MSGID'=>$incref->{'.email_msgid'},
		});

	
	print Dumper($inc);
	}




__DATA__

open F, "</tmp/zephyrsports.csv";
my %UPCS = ();
while (<F>) {
	chomp($_);
	my ($UPC,$SKU) = split(/\t/,$_,2);
	$UPCS{$UPC}++;
	print "UPC:$UPC SKU:$SKU\n";
	}
close F;

my ($udbh) = DBINFO::db_user_connect("zephyrsports");
foreach my $UPC (keys %UPCS) {
	next if ($UPCS{$UPC}<=1);
	$pstmt = "update INVENTORY_20000 set META_UPC='' where MID=29669 and META_UPC='$UPC' /* found: $UPCS{$UPC} */;\n";
	print $pstmt."\n";
	$udbh->do($pstmt);
	}
&DBINFO::db_user_close();