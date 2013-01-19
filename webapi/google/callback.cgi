#!/usr/bin/perl

my $ts = time();

use strict;
use Google::Checkout::General::GCO;
use Google::Checkout::General::MerchantCalculationCallback;
use Google::Checkout::General::MerchantCalculationResults;
use Google::Checkout::General::MerchantCalculationResult;
use Google::Checkout::XML::Constants;
use Google::Checkout::General::Util qw/is_gco_error/;
use Google::Checkout::Notification::Factory qw/get_notification_object/;
use Data::Dumper;

use lib "/httpd/modules";
require DBINFO;
require ZOOVY;
require ZTOOLKIT;
require ZPAY::GOOGLE;
require CART2;

%::DEBUGUSER = ();
$::DEBUGUSER{'theh2oguru'}++;

$|++;


my ($USERNAME,$VERSION,$xml) = (undef,undef,undef,undef,undef);

my $PRT = 0;
# print STDERR "$ENV{'REQUEST_URI'}\n";
if ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi\/v=([\d]+)\/u\=([a-zA-Z0-9]+)\/c=([a-zA-z0-9]+)\/prt=([\d]+)$/) {
	($VERSION,$USERNAME,my $CARTID,$PRT) = ($1,$2,$3,$4);
	}
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi\/v=([\d]+)\/u\=([a-zA-Z0-9]+)\/c=([a-zA-z0-9]+)\/$/) {
	($VERSION,$USERNAME,my $CARTID) = ($1,$2,$3);
	}
# https://webapi.zoovy.com/webapi/google/callback.cgi/v=1/u=theh2oguru/prt=0
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi\/v=1\/u\=([a-zA-Z0-9]+)\/prt=([\d]+)$/) {
	print STDERR "USER[$USERNAME] PRT[$PRT]\n";
	($USERNAME,$PRT) = ($1,$2);
	}
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi\/v=1\/u\=([a-zA-Z0-9]+)$/) {	
	($USERNAME) = ($1);
	}
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi\/u=([a-zA-Z0-9]+)\/v=1/) {
	($USERNAME) = ($1);
	}
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/callback\.cgi/) {
	## unspecified username/parameter on command line.
	($VERSION,$USERNAME,my $CARTID) = (1,undef,undef);
#	$xml =~ s/[\r]+//gs;
	}
elsif ($ENV{'REQUEST_URI'} =~ /\/webapi\/google\/notify\.cgi/) {
	## unspecified username/parameter on command line.
	($VERSION,$USERNAME,my $CARTID) = (1,undef,undef);
#	$xml =~ s/[\r]+//gs;
	}
elsif ($ENV{'REQUEST_METHOD'} ne 'POST') {
	warn "Using command line!\n";
	}
else {
	die("Nothing passed on the REQUEST_URI");
  }

if (not defined $USERNAME) {
	die("USERNAME not available");
	}

##
##
##

my $udbh = &DBINFO::db_user_connect($USERNAME);
my $dbID = 0;

my %params = ();

if ($ENV{'REQUEST_METHOD'} eq 'POST') {
	$/ = undef; $xml = <STDIN>; $/ = "\n";
	$xml =~ s/[\r]+//gs;

	my $serial = undef;
	if ($xml =~ /serial-number\=\"(.*?)\"/) { $serial = $1; }

	## crap, no serial #, lets generate something unique!
	if ($serial eq '') { 
		use Data::UUID; 
		$serial = Data::UUID->new()->create_str();
		}

	## check for duplicates
	my $pstmt = "select ID from GOOGLE_NOTIFICATIONS where GOOGLE_SERIAL=".$udbh->quote($serial);
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	if ($sth->rows()) { ($dbID) = $sth->fetchrow(); }
	$sth->finish();
	
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);

	if ($dbID==0) {
		## insert new record
		&DBINFO::insert($udbh,'GOOGLE_NOTIFICATIONS',{
			ID=>0,
			'*CREATED'=>'now()',
			MID=>$MID,
			USERNAME=>$USERNAME,
			PRT=>$PRT,
			DATA=>$xml,
			PROCESSED_GMT=>0,
			GOOGLE_SERIAL=>$serial,
			REQUEST_URI=>$ENV{'REQUEST_URI'}},
			debug=>1);
		my $pstmt = "select last_insert_id()";
		my $sth = $udbh->prepare($pstmt);
		$sth->execute();
		($dbID) = $sth->fetchrow();
		$sth->finish();	
		}
	}
else {
	## hmm.. not a post?

	foreach my $arg (@ARGV) {
		if ($arg !~ /=/) { die("Bad argument - [$arg] plz check syntax in file."); }
		my ($k,$v) = split(/=/,$arg);
		$params{$k} = $v;
		}
	
	if (defined $params{'REPLAY'}) {
		my $pstmt = "select * from GOOGLE_NOTIFICATIONS where ID=".int($params{'REPLAY'});
		# print STDERR $pstmt."\n";
		my $sth = $udbh->prepare($pstmt);
		$sth->execute();
		my ($hashref) = $sth->fetchrow_hashref();
		$sth->finish();	
		$dbID = $hashref->{'ID'};

		$ENV{'REQUEST_URI'} = $hashref->{'REQUEST_URI'};
		$xml = $hashref->{'DATA'};
		# print STDERR "SETTING URI [$ENV{'REQUEST_URI'}]\n";
		}

	if (defined $params{'USERNAME'}) {
		$USERNAME = $params{'USERNAME'};
		}

	if (defined $params{'FILE'}) {
		open F, "<$params{'FILE'}"; $/=undef;
		$xml = <F>;
		close F;  $/="\n";
		}

  }


my ($GN) = undef;
if ($xml ne '') {
	$GN = get_notification_object(xml => $xml);
	# print STDERR "TYPE: ".$GN->type."\n";
	die($GN) if is_gco_error $GN;
	}


##
##
##
if ((defined $GN) && ($GN->type eq 'merchant-calculation-callback')) {

	my ($CART2) = &ZPAY::GOOGLE::decodeCart($GN->get_merchant_private_data);
	my $USERNAME = $CART2->username();
	my $CARTID = $CART2->cartid();

	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	if ($webdbref->{'google_api_merchantcalc'}==0) {
		warn "merchant calculations disabled!";
		die();
		}

	##
	## 
	my @SHIPMETHODS = ();	


	#--
	#-- Show anonymous addresses
	#--
	my $addresses = $GN->get_addresses;

	for my $address (@$addresses) {
		$CART2->pr_set('ship/postal', $address->{'postal_code'});
		$CART2->pr_set('ship/region', $address->{'region'});
		$CART2->pr_set('ship/countrycode', $address->{'country_code'});

#		$CART2->shipping('flush'=>1);    
#		open F, ">>/tmp/cart";
#		print Dumper($cart);
#		close F;

		$address->{'total-tax'} = $CART2->in_get('sum/tax_total');

		foreach my $shipmethod (@{$CART2->shipmethods()}) {
			# print "METHOD: $method\n";
			$address->{'shipping-rate'} = $shipmethod->{'amount'};
			#$address->{'shipping-name'} = sprintf("%s|%s",$shipmethod->{'id'},$shipmethod->{'name'});
			$address->{'shipping-name'} = sprintf("%s",$shipmethod->{'name'});
			
			# $address->{'total-tax'} = 100;
			$address->{'shippable'} = 1;
			if ($address->{'shipping-name'} =~ /Actual Cost/i) { $address->{'shippable'} = 0; }
			if ($shipmethod->{'carrier'} eq 'ERR') { $address->{'shippable'} = 0; }

			## NOTE: this code must be duplicated in new-order-notification
			my $handling = 0;
			foreach my $fee ('sum/hnd_total','sum/spc_total','sum/ins_total') {
				$handling += sprintf("%.2f",$CART2->in_get($fee));
				}

			my $gmethod = Google::Checkout::General::MerchantCalculationResult->new(
             shipping_name                 => $address->{'shipping-name'},
             address_id                    => $address->{'id'},

	## DO NOT COMMENT THIS LINE UNDER PENALTY OF DEATH - MERCHANT CALCULATIONS TAX IS BROKED.
             total_tax                     => $address->{'total-tax'},

             shipping_rate                 => sprintf("%.2f",$address->{'shipping-rate'}+$handling),
             shippable                     => $address->{'shippable'},
   #          valid_coupon                  => 0,
   #          valid_certificate             => 0,
   #          coupon_calculated_amount      => 13.45,
   #          certificate_calculated_amount => 45.56,
   #          coupon_code                   => $coupons[0],
   #          certificate_code              => $certificates[0],
   #          coupon_message                => "coupon is valid",
   #          certificate_message           => "certificate is valid"
				);
	
			push @SHIPMETHODS, $gmethod;


			}

		# $address->{'addrid'} = $addrid;
		#$address->{'shipping-rate'} = $cart->fetch_property('ship.selected_price');
		#$address->{'shipping-name'} = $cart->fetch_property('ship.selected_method');

		#--
		#-- Create a merchant calculation result object.
		#-- All the coupon and certificate stuff are optional
		#--
		}

	
#	open F, ">>/tmp/asdf";
#	use Data::Dumper; print F Dumper(\@SHIPMETHODS);
#	close F;


	#--
	#-- Get a list of coupons and gift certificates. It's up to
	#-- the business partner to determin whether the code is a
	#-- coupon or a gift certificate. We get back an array reference
	#--
	#my $coupons_certificates = $GN->get_merchant_code_strings;
	#
	#my (@coupons, @certificates);
	#
	#for (@$coupons_certificates)
	#{
	#  #--
	#  #-- If the code has the string 'coupon' in it, assume it's a coupon code.
	#  #-- Partner might use a completely different rule to determine this
	#  #--
	#  if (/coupon/i)
	#  {
	#    push @coupons, $_;
	#  }
	#  else
	#  {
	#    push @certificates, $_;
	#  }
	#}

	#--
	#-- This sends the merchant calculation back to GCO.
	#-- Partner will likely run this in some sort of CGI
	#-- enviroment since it outputs a text/xml header as well
	#--
   my $gco = &ZPAY::GOOGLE::buildGCO($USERNAME,$webdbref);
   $gco->send_merchant_calculation(\@SHIPMETHODS);
	$GN = undef;
	}
elsif ($dbID>0) {
	## ALL OTHER REQUESTS ARE PROCESSED SERIALLY
	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	my $gco = &ZPAY::GOOGLE::buildGCO($USERNAME,$webdbref);
	$gco->send_notification_response();
	}
else {
	## Hmm... 
	warn("Google dbID is zero");
	}


if ((time()-$ts)>10) {
	&ZOOVY::confess($USERNAME,"Google Checkout Timeout\nDBID: $dbID\nTook: ".(time()-$ts)." seconds ",justkidding=>1);
	}

&DBINFO::db_user_close();


