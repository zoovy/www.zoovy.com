package EBAY::CREATE;

use Data::Dumper;
use lib "/httpd/modules";
use XMLTOOLS;
use EBAY::API;
use GTOOLS;
use strict;
use URI::Escape;


##
## converts legacy to unified schema attributes
##
sub convertLegacyToUnified {
	my ($in) = @_;

	## <AttributeSetArray> tag is only present in UnifiedSchema
	if ($in =~ /<AttributeSetArray>/) { return($in); }
	if ($in =~ /^SCALAR/) { return(); }
	## arrgh.. fucking ebay.
	$in =~ s/\& /\&amp; /g;;

	require XML::Parser;
	require XML::Parser::EasyTree;
	require XMLTOOLS;

	# print STDERR "about to parse attributes [$in]\n";
	my $p=new XML::Parser(Style=>'EasyTree');
	my $tree=$p->parse($in);
	# print STDERR "finished parsing attributes\n";

	my $xml = "<AttributeSetArray>\n";
	foreach my $node (@{$tree->[0]->{'content'}}) {
		next if ($node->{'type'} ne 'e');
		my $attributeSetID = $node->{'attrib'}->{'id'};
		$xml .= "\t<AttributeSet attributeSetID=\"$attributeSetID\">\n";
		foreach my $attrib (@{$node->{'content'}}) {
			next if ($attrib->{'type'} ne 'e');
			my $attributeID = $attrib->{'attrib'}->{'id'};
			$xml .= "\t\t<Attribute attributeID=\"$attributeID\">\n";
			foreach my $valuelist (@{$attrib->{'content'}}) {
				next if ($valuelist->{'type'} ne 'e');
				my $info = &XMLTOOLS::XMLcollapse($valuelist->{'content'});
				next if (($info->{'~id'} eq '') && ($info->{'Value.ValueLiteral'} eq '')); 
				$xml .= "\t\t\t<Value>";
				if ($info->{'~id'} ne '') { $xml .= "<ValueID>".&ZOOVY::incode($info->{'~id'})."</ValueID>"; }
				if ($info->{'Value.ValueLiteral'} ne '') { $xml .= "<ValueLiteral>".&ZOOVY::incode($info->{'Value.ValueLiteral'})."</ValueLiteral>"; }
				$xml .= "</Value>\n";
				}
			$xml .= "\t\t</Attribute>\n";
			}
		$xml .= "\t</AttributeSet>\n";
		}
	$xml .= "</AttributeSetArray>\n";
	return($xml);
	}




##
## Tree is xml tree returned by eBay
## RECYCLEID is true if this item was recycled
## $ebayvars is the list of shit we sent to eBay
##
sub parse_errors {
	my ($r,$RECYCLEID,$ebayvars,$zoovyvars) = @_;

	my %result = ();

	## Did we get an error?
	if ($r->{'.ERRORS'}) {
		foreach my $err (@{$r->{'.ERRORS'}}) {

			if (not defined $err) {
				## No severe errors
				}
			elsif ($err->{'ErrorCode'} == 488) {
				## The specified UUID has already been used; ListedByRequestAppId=1, item ID=7236587050.
				$result{'Id'} = $err->{'ErrorParameters.Value'};
				$r->{'Ack'} = 'UnFailure';
				}
			elsif ($err->{'ErrorCode'} == 5116) {
				## Warning: Attribute 15965 dropped. Attribute either has an invalid attribute id or the value(s) for the attribute are invalid.
				}
			elsif ($err->{'ErrorCode'} == 11012) {
				## paypal warning - ignore this. 
				## PayPal added as a payment method because you have set your preference to 'offer PayPal on all listings' (known as Automatic Logo Insertion at PayPal)
				}
			elsif ($err->{'ErrorCode'} == 5119) {
				## A warning that the preset productid has changed. -- can safely be ignored.
				}
			elsif ($err->{'ErrorCode'} == 12302) {
				## Checkout Redirect is incompatible with Live Auctions, Ad format, Merchant Tool, Motors, and Immediate payment. Your item has been listed, but Checkout Redirect was disabled.
				}
			elsif ($err->{'SeverityCode'} eq 'Warning') {
				}
			else {
				$result{'ERROR'} = $err->{'LongMessage'};		
				$result{'ERRORCODE'} = $err->{'ErrorCode'};
				if (not defined $result{'Id'}) { $result{'Id'} = 0; }
				}
			}	
		}

	### Check for an Item
	if ($r->{'Ack'} eq 'UnFailure') {
		## not a success, but not a failure, probably attempted to relist a dupe UUID
		}
	elsif (($r->{'Ack'} eq 'Success') || ($r->{'Ack'} eq 'Warning')) {
		my %FEES = ();
		#foreach my $node (@{$r->{'Fees'}}) { 		
		#	next if ($node->{'type'} ne 'e');
		#	if ($node->{'name'} eq 'Fees') {
		#		foreach my $node2 (@{$node->{'content'}}) { 
		#			next if ($node2->{'type'} ne 'e');
		#			next if ($node2->{'name'} eq 'CurrencyId');
		#			$FEES{$node2->{'name'}} = $node2->{'content'}->[0]->{'content'}; 
		#			}
		#		}
		#	else {
		#		$result{$node->{'name'}} = $node->{'content'}->[0]->{'content'}; 
		#		}
		#	}
		$result{'Id'} = $r->{'ItemID'};
		$result{'EndTime'} = $r->{'EndTime'};
		#$result{'FEES'} = \%FEES;
		# print Dumper(\%info);
		}	

	## recover from a duplicate item id
	if ($result{'Id'}<=0) {		
		$result{'Id'} = $result{'DuplicateItemId'};
		}

	## at this point %info is fully populated	
	## and resembles:
	##
	#    'CategoryFeaturedFee' => '0.00',
	#    'ListingFee' => '0.30',
	 #    'SchedulingFee' => '0.00',
	 #    'StartTime' => '2002-08-02 11:48:54',
	 #    'FeaturedFee' => '0.00',
	 #    'BoldFee' => '0.00',
	 #    'ReserveFee' => '0.00',
	 #    'EndTime' => '2002-08-09 11:48:54',
	 #    'PhotoFee' => '0.00',
	 #    'InsertionFee' => '0.30',
	 #    'AuctionLengthFee' => '0.00',
	 #    'FeaturedGalleryFee' => '0.00',
	 #    'ThirtyDaysAucFee' => '0.00',
	 #    'GiftIconFee' => '0.00',
	 #    'FixedPriceDurationFee' => '0.00',
	 #    'HighLightFee' => '0.00',
	 #    'CurrencyId' => '1',
	 #    'BuyItNowFee' => '0.00',
	 #    'PhotoDisplayFee' => '0.00',
	 #    'Id' => '587262',
	 #    'GalleryFee' => '0.00'
	 
	 

	## CHECK STATUS OF AUCTION_NUM (0 = FAILURE)
	if ((defined $result{'Id'}) && ($result{'Id'}>0)) {
		}
	elsif ($result{'ERRORCODE'} == 196) {
		## Your item was not relisted. Possible reasons: the item does not exist, the item has not ended, or you were not the seller of the item.
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 163) {
		## Inactive application or developer. - yeah right!
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 2) {
		## Unsupported Verb! (4/1/04)
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 17) {
		## gee, couldn't relist.
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 10007) {
		## Internal error to the application.
		### NOTE: this is returned when eBay is DOWN - so we retry 12/26/03
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 97 && $RECYCLEID) {
		## contradicotry shipping
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 190 && $RECYCLEID) {
		## ebay bug! 
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 115 && $RECYCLEID) {
		## relisted price must be higher
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERRORCODE'} == 195 && $RECYCLEID) {
		## ebay bug! The Buy It Now price must be greater than or equal to the minimum bid price. 
		$result{'TRYAGAIN'}++;
		}
	elsif ($result{'ERROR'} =~ /502 Proxy Error/) {
	        ## TREAT THIS AS A CRITICAL FAILURE SO WE BACK OFF
          	warn $result{'ERROR'};
          	die();
                }
	elsif ($result{'ERRORCODE'} == 17412) {
		## SeriousError #17412 - cannot find muse stock photos ?? who the @#$% cares? 	
		$result{'TRYAGAIN'}++;
		my $dbh = &EBAY::API::db_ebay_connect();
		my $qtTITLE = $dbh->quote($ebayvars->{'Item.Title'});
		my $qtEBAYPROD = $dbh->quote($zoovyvars->{'ebay:productid'});

		my $pstmt = "insert into PROD_NO_PICTURES (TITLE,EBAYPROD,CREATED) values ($qtTITLE,$qtEBAYPROD,now())";
		# print STDERR "Stupid eBay doesn't have a picture, we've got to retry!\n$pstmt\n";
		$dbh->do($pstmt);
		&EBAY::API::db_ebay_close();
		}

	return(\%result);
}






##
##
##
##
## blah
##
sub shippingXML {
	my ($USERNAME,$PROFILE,$inforef,$varsref,$MSGSREF) = @_;

	require XMLTOOLS;

	my $xml = '';
	my %topref = ();
	my %ref = ();
	my %btmref = ();

	my $currency = 'USD';
	## END OF CALCULATEDSHIPPINGRATE



	if ($varsref->{'use_taxtable'}>0) {
		## tax table is setup in eBay.com account, these settings will be ignored.
		}
	elsif ($varsref->{'salestaxpercent'}>0) {
		$ref{'SalesTax.SalesTaxPercent'} = sprintf("%.3f",$varsref->{'salestaxpercent'});
		$ref{'SalesTax.SalesTaxState'} = uc($varsref->{'salestaxstate'});
		$ref{'SalesTax.ShippingIncludedInTax'} = &XMLTOOLS::boolean($varsref->{'ship_tax'});
		}



	my $NEED_CALCULATED_SHIPPING = 0;
	my $HAS_FIXED_PRICE = 0;
	my $HAS_FREIGHT = 0;
	my ($majorWeight,$minorWeight) = &EBAY::CREATE::smart_weight($varsref->{'base_weight'});

	## DOMESTIC SHIPPING OPTIONS
	if (1) {
		my @lines = split(/[\n\r]+/,$varsref->{'ship_domservices'});
		my $i = 1;
		my $used_product_rates = 0;

		foreach my $line (@lines) {
			my $svc = &ZTOOLKIT::parseparams($line);
			my %x = ();
         my %y = ();
			$y{'ShippingServiceOption.ShippingServicePriority'} = $i;
			$x{'ShippingServiceOptions.ShippingServicePriority'} = $i;
			++$i;

			$y{'ShippingServiceOption.ShippingService'} = $svc->{'service'};
			$x{'ShippingServiceOptions.ShippingService'} = $svc->{'service'};

			if ($svc->{'cost'}==-1) { 
				$svc->{'cost'} = sprintf("%.2f",$varsref->{'ship_cost1'}+$varsref->{'ship_markup'}); 
				if ($used_product_rates++>0) {
					push @{$MSGSREF}, "WARN|Multiple domestic shipping methods have price of -1 for fixed shipping and subsequently will display the same rates.";
					}
				}
			if ($svc->{'addcost'}==-1) { 
				$svc->{'addcost'} = sprintf("%.2f",$varsref->{'ship_cost2'}+$varsref->{'ship_markup'}); 
				}	

			if ($svc->{'free'}) {
				my $isFlat = 0;
				if ($svc->{'service'} eq 'LocalDelivery') { $isFlat++; }
				if ($svc->{'service'} eq 'Delivery') { $isFlat++; }
				if ($svc->{'service'} eq 'Pickup') { $isFlat++; }
				if ($svc->{'service'} eq 'Other') { $isFlat++; }
				if ($svc->{'service'} eq 'ShippingMethodStandard') { $isFlat++; }
				if ($svc->{'service'} eq 'ShippingMethodExpress') { $isFlat++; }
				if ($svc->{'service'} eq 'ShippingMethodOvernight') { $isFlat++; }
				## note: all flat free shipping still requires .SSC, .SSAC  and .S to be set!
				if (($isFlat) && ($svc->{'cost'} eq '')) {
            	$svc->{'cost'} = 0;
           		$svc->{'addcost'} = 0;
					$HAS_FIXED_PRICE |= 1;
					push @{$MSGSREF}, "WARN|please implicitly set the price to zero for any FREE domestic flat rate shipping methods such as: ".$svc->{'service'};
					}
 				$y{'ShippingServiceOption.FreeShipping'} = &XMLTOOLS::boolean($svc->{'free'});
				$x{'ShippingServiceOptions.FreeShipping'} = &XMLTOOLS::boolean($svc->{'free'});
				}
			else {
 				$y{'ShippingServiceOption.FreeShipping'} = &XMLTOOLS::boolean(0);
				$x{'ShippingServiceOptions.FreeShipping'} = &XMLTOOLS::boolean(0);
				}

			if ($svc->{'service'} eq 'Freight') { $HAS_FREIGHT |= 1;	}
			if ($svc->{'service'} eq 'FreightFlat') { $HAS_FREIGHT |= 1;	}
			if ($svc->{'service'} eq 'FreightShipping') { $HAS_FREIGHT |= 1;	}

			if (($svc->{'cost'} ne '') && ($svc->{'cost'}>=0)) { 
				$HAS_FIXED_PRICE |= 1;
				$y{'ShippingServiceOption.SSAC*'} = &XMLTOOLS::currency('ShippingServiceAdditionalCost',$svc->{'addcost'},$currency);
				$x{'ShippingServiceOptions.SSAC*'} = &XMLTOOLS::currency('ShippingServiceAdditionalCost',$svc->{'addcost'},$currency);
				$y{'ShippingServiceOption.SSC*'} = &XMLTOOLS::currency('ShippingServiceCost',$svc->{'cost'},$currency);
				$x{'ShippingServiceOptions.SSC*'} = &XMLTOOLS::currency('ShippingServiceCost',$svc->{'cost'},$currency);
				if ($svc->{'farcost'}>0) {
					$y{'ShippingServiceOption.S*'} = &XMLTOOLS::currency('ShippingSurcharge',$svc->{'farcost'},$currency);
					$x{'ShippingServiceOptions.S*'} = &XMLTOOLS::currency('ShippingSurcharge',$svc->{'farcost'},$currency);
					}
				}
			else {
				$NEED_CALCULATED_SHIPPING |= 1;
				}
			$btmref{'ShippingServiceOptions*'} .= &XMLTOOLS::buildTree(undef,\%x,1);
			$btmref{'XXShippingServiceOptions*'} .= &XMLTOOLS::buildTree(undef,\%y,1);
			}

		}

	## INTERNATIONAL SHIPPING OPTIONS
	if (1) {
		my @lines = split(/[\n\r]+/,$varsref->{'ship_intservices'});
		my $i = 1;

		foreach my $line (@lines) {
			my $svc = &ZTOOLKIT::parseparams($line);

			my $skip = 0;
			if (($svc->{'service'} eq 'USPSFirstClassMailInternational') && ($majorWeight>4)) {				
				## USPS First Class should be dropped.
            push @{$MSGSREF}, "WARN|USPS First Class International Mail has a maximum weight of 4lbs. and was dropped.";
				$skip++;
				}
			next if ($skip);

			my %x = ();
			$x{'InternationalShippingServiceOption.ShippingServicePriority'} = $i;
			$x{'InternationalShippingServiceOption.ShippingService'} = $svc->{'service'};
         ++$i;
         
			my @locs = ();
			if ($svc->{'shipto'} ne '') {
				## custom shipto specified for the shipping method.
				@locs = split(/[,\s]+/,$svc->{'shipto'});
				}
			elsif ($svc->{'service'} eq 'UPSStandardToCanada') {
				## force canada on whenever it's UPSStandardToCanada
				@locs = ('CA');
				}
			else {
				## use default ebay:ship_intlocations
				my $mylocs = &ZTOOLKIT::parseparams($varsref->{'ship_intlocations'},1);
				@locs = keys %{$mylocs};
				}
         if (scalar(@locs)==0) {
            push @{$MSGSREF}, "ERR|internationl shipping is specified, but no locations are.";
            }
            
			foreach my $loc (@locs) {
				$x{'InternationalShippingServiceOption.ShipToLocation-'.$loc.'*'} = '<ShipToLocation>'.$loc.'</ShipToLocation>';
				}

			# print Dumper($svc,\@locs);

			if ((scalar(@locs)==1) && ($locs[0] eq 'CA')) {
				## if we only have canada then use canada fixed price shipping rates!
				if ($svc->{'cost'}==-1) { $svc->{'cost'} = sprintf("%.2f",$varsref->{'ship_can_cost1'}+$varsref->{'ship_markup'}); }
				if ($svc->{'addcost'}==-1) { $svc->{'addcost'} = sprintf("%.2f",$varsref->{'ship_can_cost2'}+$varsref->{'ship_markup'}); }					
				}
			else {
				## use international fixed price rates!
				if ($svc->{'cost'}==-1) { $svc->{'cost'} = sprintf("%.2f",$varsref->{'ship_int_cost1'}+$varsref->{'ship_markup'}); }
				if ($svc->{'addcost'}==-1) { $svc->{'addcost'} = sprintf("%.2f",$varsref->{'ship_int_cost2'}+$varsref->{'ship_markup'}); }	
				}

			if ($svc->{'free'}>0) {
 				$x{'InternationalShippingServiceOption.FreeShipping'} = &XMLTOOLS::boolean($svc->{'free'});
				my $isFlat++;
				if ($svc->{'service'} eq 'OtherInternational') { $isFlat++; }
				if ($svc->{'service'} eq 'UPSStandardToCanada') { $isFlat++; }
				if ($svc->{'service'} eq 'StandardInternational') { $isFlat++; }
				if ($svc->{'service'} eq 'ExpeditedInternational') { $isFlat++; }
				if (($isFlat) && ($svc->{'cost'} eq '')) {
	            $svc->{'cost'} = 0;
 					$svc->{'addcost'} = 0;
					$HAS_FIXED_PRICE |= 2;
					push @{$MSGSREF}, "WARN|please implicitly set the price to zero for any FREE international methods such as: ".$svc->{'service'};
					}
				}
			else {
 				$x{'InternationalShippingServiceOption.FreeShipping'} = &XMLTOOLS::boolean(0);
				}

			if (($svc->{'cost'} ne '') && ($svc->{'cost'}>=0)) {
				$HAS_FIXED_PRICE |= 2;
				$x{'InternationalShippingServiceOption.SSAC*'} = &XMLTOOLS::currency('ShippingServiceAdditionalCost',$svc->{'addcost'},$currency);
				$x{'InternationalShippingServiceOption.SSC*'} = &XMLTOOLS::currency('ShippingServiceCost',$svc->{'cost'},$currency);
				if ($svc->{'farcost'}>0) {
					$x{'InternationalShippingServiceOption.S*'} = &XMLTOOLS::currency('ShippingSurcharge',$svc->{'farcost'},$currency);
					}
				}
			else {
				$NEED_CALCULATED_SHIPPING |= 2;
				}


			
			$btmref{'InternationalPromotionalShippingDiscount'} = &XMLTOOLS::boolean(0);
			$btmref{'InternationalShippingServiceOptions_'.$i.'*'} = &XMLTOOLS::buildTree(undef,\%x,1);
			}
		}


	$ref{'InsuranceDetails.InsuranceOption'} = $varsref->{'ship_dominstype'};
	if ($varsref->{'ship_dominstype'} eq 'NotOffered') {}
	elsif ($varsref->{'ship_dominsfee'}>0) {
		if (($HAS_FIXED_PRICE & 1) && (($NEED_CALCULATED_SHIPPING&1)==0)) {
			$ref{'InsuranceDetails.InsuranceFee*'} = &XMLTOOLS::currency('InsuranceFee',$varsref->{'ship_dominsfee'},$currency);
			}
		else {
			push @{$MSGSREF}, "WARN|Domestic Insurance fee ignored. Insurance fees only apply to Flat rate shipping, listing will use carrier insurance rates.";
			}
		}

	$ref{'InternationalInsuranceDetails.InsuranceOption'} = $varsref->{'ship_intinstype'};
	if ($varsref->{'ship_intinstype'} eq 'NotOffered') {}
	elsif ($varsref->{'ship_intinsfee'}>0) {
		if (($HAS_FIXED_PRICE & 2) && (($NEED_CALCULATED_SHIPPING&2)==0)) {
			$ref{'InternationalInsuranceDetails.InsuranceFee*'} = &XMLTOOLS::currency('InsuranceFee',$varsref->{'ship_intinsfee'},$currency);
			}
		else {
			push @{$MSGSREF}, "WARN|International Insurance fee ignored. Insurance fees only apply to Flat rate shipping, listing will use carrier insurance rates.";
			}
		}


	if (($HAS_FIXED_PRICE&1) && ($NEED_CALCULATED_SHIPPING&1)) {
		push @{$MSGSREF}, "ERR|Unfortunately eBay does not support mixed flat rate and calculated rate domestic shipping methods.";
		}

	if (($HAS_FIXED_PRICE&2) && ($NEED_CALCULATED_SHIPPING&2)) {
		push @{$MSGSREF}, "ERR|Unfortunately eBay does not support mixed flat rate and calculated rate international shipping methods.";
		}

	if ($HAS_FREIGHT>0) {
		$btmref{'ShippingType'} = 'Freight'; 
		## DispatchTimeMax must be set to zero for freight shipments!
		## or eBay throws (completely incorrect) error:
		## #21806 Invalid Domestic Handling Time.: 0 business day(s) is not a valid Domestic Handling Time on site 0.
		## isn't it ironic, that it MUST be set to zero -- even though the error says zero isn't valid.
		$inforef->{'Item.DispatchTimeMax'} = 0;
		}
	elsif (($HAS_FIXED_PRICE==1) && ($NEED_CALCULATED_SHIPPING==2)) {
		## we have fixed domestic, and calculated international
		$btmref{'ShippingType'} = 'FlatDomesticCalculatedInternational';
		}
	elsif (($HAS_FIXED_PRICE==2) && ($NEED_CALCULATED_SHIPPING==1)) {
		## we have calculated domestic, and fixed international
		$btmref{'ShippingType'} = 'CalculatedDomesticFlatInternational';
		# push @{$MSGSREF}, "BH|blah";
		}
	elsif (($HAS_FIXED_PRICE&3) && ($NEED_CALCULATED_SHIPPING==0)) {
		$btmref{'ShippingType'} = 'Flat';
		}
	elsif (($HAS_FIXED_PRICE==0) && ($NEED_CALCULATED_SHIPPING&3)) {
		$btmref{'ShippingType'} = 'Calculated';
		}
	else {
	   warn "((HFP=$HAS_FIXED_PRICE) && (NCS=$NEED_CALCULATED_SHIPPING))\n";
		push @{$MSGSREF}, "WARN|Zoovy did not understand how to set ShippingType properly (HFP=$HAS_FIXED_PRICE NCS=$NEED_CALCULATED_SHIPPING)";
		}
	

	# $NEED_CALCULATED_SHIPPING = 0;	
	if ($NEED_CALCULATED_SHIPPING) {
	   if ($varsref->{'ship_originzip'} eq '') {
	     push @{$MSGSREF}, "ERR|origin zip not set, defaulting to 92024"; 
        $varsref->{'ship_originzip'} = 92024;
        }
		$topref{'CalculatedShippingRate.OriginatingPostalCode'} = $varsref->{'ship_originzip'};	
		if ($NEED_CALCULATED_SHIPPING&1) {
			$topref{'CalculatedShippingRate.PHC*'} = &XMLTOOLS::currency('PackagingHandlingCosts',$varsref->{'ship_dompkghndcosts'},$currency);
			}
		if ($NEED_CALCULATED_SHIPPING&2) {
			$topref{'CalculatedShippingRate.IPHC*'} = &XMLTOOLS::currency('InternationalPackagingHandlingCosts',$varsref->{'ship_intpkghndcosts'},$currency);
			}
		$topref{'CalculatedShippingRate.MeasurementUnit'} = 'English';

		if ($varsref->{'pkg_depth'}) { $topref{'CalculatedShippingRate.PackageDepth'} = $varsref->{'pkg_depth'}; }
		elsif ($varsref->{'prod_depth'}) { $topref{'CalculatedShippingRate.PackageDepth'} = $varsref->{'prod_depth'}; }

		if ($varsref->{'pkg_height'}) { $topref{'CalculatedShippingRate.PackageLength'} = $varsref->{'pkg_height'}; }
		elsif ($varsref->{'prod_height'}) { $topref{'CalculatedShippingRate.PackageLength'} = $varsref->{'prod_height'}; }
		elsif ($varsref->{'pkg_length'}) { $topref{'CalculatedShippingRate.PackageLength'} = $varsref->{'pkg_length'}; }
		elsif ($varsref->{'prod_length'}) { $topref{'CalculatedShippingRate.PackageLength'} = $varsref->{'prod_length'}; }

		if ($varsref->{'pkg_width'}) { $topref{'CalculatedShippingRate.PackageWidth'} = $varsref->{'pkg_width'}; }
		elsif ($varsref->{'prod_width'}) { $topref{'CalculatedShippingRate.PackageWidth'} = $varsref->{'prod_width'}; }

		if ($varsref->{'ship_packagetype'} eq 'None') {}
		elsif ($varsref->{'ship_packagetype'} ne '') {
			$topref{'CalculatedShippingRate.ShippingIrregular'} = &XMLTOOLS::boolean($varsref->{'ship_irregular'});	
			$topref{'CalculatedShippingRate.ShippingPackage'} = $varsref->{'ship_packagetype'};
			}

		$topref{'CalculatedShippingRate.WeightMajor*'} = sprintf("<WeightMajor unit=\"lbs\">%d</WeightMajor>",$majorWeight);
		$topref{'CalculatedShippingRate.WeightMinor*'} = sprintf("<WeightMinor unit=\"lbs\">%d</WeightMinor>",$minorWeight);
		}
	else {
		## there is no calculated shipping
		if ($varsref->{'ship_dompkghndcosts'}>0) {
			push @{$MSGSREF}, "WARN|eBay does not allow handling charges to be applied to flat rate shipping. Handling fee will be ignored.";
			}
		}


#      <ShippingServiceOptions> ShippingServiceOptionsType 
#        <FreeShipping> boolean </FreeShipping>
#        <ShippingService> token </ShippingService>
#        <ShippingServiceAdditionalCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceAdditionalCost>
#        <ShippingServiceCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceCost>
#        <ShippingServicePriority> int </ShippingServicePriority>
#        <ShippingSurcharge currencyID="CurrencyCodeType"> AmountType (double) </ShippingSurcharge>
#      </ShippingServiceOptions>
 #    <InternationalPromotionalShippingDiscount> boolean </InternationalPromotionalShippingDiscount>
 #     <InternationalShippingDiscountProfileID> string </InternationalShippingDiscountProfileID>
 #     <InternationalShippingServiceOption> InternationalShippingServiceOptionsType 
 #       <ShippingService> token </ShippingService>
 #       <ShippingServiceAdditionalCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceAdditionalCost>
 #       <ShippingServiceCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceCost>
 #       <ShippingServicePriority> int </ShippingServicePriority>
 #       <ShipToLocation> string </ShipToLocation>
 #       <!-- ... more ShipToLocation nodes here ... -->
 #     </InternationalShippingServiceOption>
#     <PaymentInstructions> string </PaymentInstructions>
#      <PromotionalShippingDiscount> boolean </PromotionalShippingDiscount>
#      <SalesTax> SalesTaxType 
#        <SalesTaxPercent> float </SalesTaxPercent>
#        <SalesTaxState> string </SalesTaxState>
#        <ShippingIncludedInTax> boolean </ShippingIncludedInTax>
#      </SalesTax>
#      <ShippingDiscountProfileID> string </ShippingDiscountProfileID>
#      <ShippingServiceOptions> ShippingServiceOptionsType 
#        <FreeShipping> boolean </FreeShipping>
#        <ShippingService> token </ShippingService>
#        <ShippingServiceAdditionalCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceAdditionalCost>
#        <ShippingServiceCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceCost>
#        <ShippingServicePriority> int </ShippingServicePriority>
#        <ShippingSurcharge currencyID="CurrencyCodeType"> AmountType (double) </ShippingSurcharge>
#      </ShippingServiceOptions>
#      <!-- ... more ShippingServiceOptions nodes here ... -->
#      <ShippingType> ShippingTypeCodeType </ShippingType>


#	$btmref{'CalculatedShippingRate.'} = '';	
#	$btmref{'CalculatedShippingRate.'} = '';	
#	$btmref{'CalculatedShippingRate.'} = '';	
#	$btmref{'CalculatedShippingRate.'} = '';	
#	$btmref{'CalculatedShippingRate.'} = '';	

  	$xml = XMLTOOLS::buildTree(undef,\%topref,1);
  	$xml .= XMLTOOLS::buildTree(undef,\%ref,1);
  	$xml .= XMLTOOLS::buildTree(undef,\%btmref,1);
	$xml =~ s/></>\n</g;
	untie %ref;

	return($xml);
	}




##
##
##
##
sub doit2 {
	my ($listing,$dbh) = @_;

	my $dataref = $listing->{'DATAREF'};
	my $ID = $listing->{'ID'};
	my $CHANNEL = $listing->{'CHANNEL'};
	my $MERCHANT = $listing->{'MERCHANT'};
	my $MID = $listing->{'MID'};
	my $PRODUCT = $listing->{'PRODUCT'};
	my $RECYCLEID = $listing->{'RECYCLED_ID'};
	my $ERROR = '';
	my @MSGS = ();

	# print STDERR Dumper($dataref)."\n";
	# print STDERR "!blah: $dataref->{'ebay:quantity'} $dataref->{'ebay'}\n";

	## legacy compatibility
	if (not defined $dataref->{'ebay:version'}) {}
	elsif ($dataref->{'ebay:version'} < 200) {
		delete $dataref->{'ebay:ship_type'}; 	# usually set to something silly like zero.
		}

	if ($listing->{'PROFILE'} eq '') {
		## hopefully this will catch any blank profiles.
		$listing->{'PROFILE'} = &ZOOVY::fetchproduct_attrib($MERCHANT,$PRODUCT,'zoovy:profile');
		}
	# print STDERR "QUANTITY: $dataref->{'ebay:quantity'} cat: $dataref->{'ebay:category'}\n";
	# print STDERR "PRODREF: ".((defined $dataref->{'zoovy:ship_int_cost1'})?1:0)."\n";

	my $prodref = &ZOOVY::fetchproduct_as_hashref($MERCHANT,$PRODUCT);
	if (defined $prodref) {
		if (($prodref->{'ebay:use_gallery'} eq '') || ($prodref->{'ebay:use_gallery'} eq 'ON')) { delete $prodref->{'ebay:use_gallery'}; }
		if (($prodref->{'ebaystores:use_gallery'} eq '') || ($prodref->{'ebaystores:use_gallery'} eq 'ON')) { delete $prodref->{'ebaystores:use_gallery'}; }


		foreach my $k (keys %{$prodref}) {
			next if ($k eq 'ebay:ship_type');	## ooh.. this field changed significantly.
			next if ($k eq 'ebaystores:price');	## yipes.. this field is evil.
			next if (defined $dataref->{$k});	## never overwite something in the product/channel data itself.

			if ($listing->{'CLASS'} eq 'STORE') {
				if ((substr($k,0,11) eq 'ebaystores:') || (substr($k,0,6) eq 'zoovy:')) {
					$dataref->{$k} = $prodref->{$k};
					}
				}
			elsif ($listing->{'CLASS'} ne 'STORE') {
				if ((substr($k,0,5) eq 'ebay:') || (substr($k,0,6) eq 'zoovy:')) {
					$dataref->{$k} = $prodref->{$k};
					}
				}
			}
		undef $prodref;
		}
	# print "DATAREF: $dataref->{'zoovy:ship_int_cost1'}\n";

	if ($listing->{'CLASS'} eq 'STORE') {
		## ebaystores:quantity should override ebay;quantity for store listings.
		if ($dataref->{'ebay:storeqty'}) {}	# great, they've got storeqty set - lets use that.
		elsif ($dataref->{'ebaystores:quantity'}) { $dataref->{'ebay:storeqty'} = $dataref->{'ebaystores:quantity'}; }
		elsif ($dataref->{'ebay:quantity'}) { $dataref->{'ebay:storeqty'} = $dataref->{'ebay:quantity'}; }

		$dataref->{'ebay:quantity'} = $dataref->{'ebay:storeqty'};		# since this is a store listing, this is what the quantity ought to be.
		}
	# print STDERR "QUANTITY: $dataref->{'ebay:quantity'}\n";

	my $nsref = &ZOOVY::fetchmerchantns_ref($MERCHANT,$listing->{'PROFILE'});
	if (defined $nsref) {
		if (($nsref->{'ebaystores:use_gallery'} eq '') || ($nsref->{'ebaystores:use_gallery'} eq 'ON')) { delete $nsref->{'ebaystores:use_gallery'}; }
		foreach my $k (keys %{$nsref}) {
			next if ($k eq '');		## causes "bizzare copy of hash in sassign"
			next if ($k =~ /price/);
			next if (($k !~ /ship/) && ($k =~ /cost/));	
			next if ($k =~ /buyitnow/);
			if (defined $dataref->{$k}) {
				push @MSGS, "INFO|The PROFILE property \"$k\" is set implicitly to \"$dataref->{$k}\" in the product or channel.";
				}
			next if (defined $dataref->{$k});	## never overwite something in the product/channel data itself.
			$dataref->{$k} = $nsref->{$k};
			}
		}


	my $html = undef;
	# print STDERR "QUANTITY: $dataref->{'ebay:quantity'} CATEGORY: $dataref->{'ebay:category'}\n";
	if ($dataref->{'zoovy:html'} ne '') { 
		## CUSTOM HTML SPECIFIED
      ## LEGACY listing has zoovy:html in it.
      $html = $dataref->{'zoovy:html'};
		push @MSGS, 'WARN|Property zoovy:html was found in your product, the HTML wizard if specified will be ignored.';
      }
	else {
      my $wizard = $nsref->{'ebay:template'};
		require TOXML;
      my ($toxml) = TOXML->new('WIZARD',$wizard,USERNAME=>$MERCHANT);
		if (not defined $toxml) {
			$ERROR = "Could not load/render wizard $MERCHANT/$wizard";
			}
		else {
			if ($::DEBUG) { print STDERR "BEGIN RENDER!\n"; }
	      $html = $toxml->render(USERNAME=>$MERCHANT,
   	      SKU=>$PRODUCT, PROFILE=>$listing->{'PROFILE'}, MARKET=>'ebay', UUID=>$ID, CHANNEL=>$CHANNEL,
   	  	    nsref=>$nsref, sref=>$dataref);
			if ($::DEBUG) { print STDERR "END RENDER!\n"; }

			#open F, ">>/tmp/$MERCHANT.debug.log";
			#print F Dumper(USERNAME=>$MERCHANT,
         #   SKU=>$PRODUCT, PROFILE=>$listing->{'PROFILE'}, MARKET=>'ebay', UUID=>$ID, CHANNEL=>$CHANNEL,
         #    nsref=>$nsref, sref=>$dataref);
			#close F;
			}
	
		$html = qq~<!--
		  USERNAME: $MERCHANT
  		  PRODUCT: $PRODUCT
		  PROFILE: $listing->{'PROFILE'} [$wizard]
		  TIME: ~.time().qq~ -->~.$html;
      }
	# print STDERR "QUANTITY: $dataref->{'ebay:quantity'} cat: $dataref->{'ebay:category'}\n";

	if (not defined $dataref->{'ebay:storecat'}) { 
		$dataref->{'ebay:storecat'} = $dataref->{'ebaystores:storecat'}; 
		}

	## build %vars - which strips off the tag owner. (so zoovy:profile becomes simply "profile")
	##		note: keys are done in a reverse sorted order, so ebay: tags will overwrite zoovy: tags.
	my %vars = ();
	foreach my $k (reverse sort keys %{$dataref}) {
		next if ((substr($k,0,4) ne 'ebay') && (substr($k,0,5) ne 'zoovy')); ## note: ebay will also get ebaystores, ebaymotor
		next if (substr($k,0,1) eq '/');
		if ($k =~ /^.*?\:(.*?)$/) {
			$vars{lc($1)} = $dataref->{$k};
			$vars{lc($1)} =~ s/^[\s]+(.*?)[\s]+$/$1/gos;	 # strip leading + trailing whitespace
			# print STDERR "FOO: $k lc($1) = $dataref->{$k}\n";
			}
		}


	## powerlister special settings.
	if ($listing->{'IS_POWERLISTER'}>0) { 
		# first lets figure out a good title.
		my @titles = ();
		foreach my $i (1..5) {
			## ebay:title1, ebay:title2 .. etc.
			if (length($dataref->{'ebay:title'.$i})>5) { push @titles, $dataref->{'ebay:title'.$i}; }
			}

		# if (scalar(@titles)==0) { $ERROR = 'No valid titles!';  }
		# if ($vars{'zoovy:do_preset'}) { $ERROR = ''; }	# preset doesn't need a title, it'll get it from eBay!

		if (scalar(@titles)>0) {
			$vars{'title'} = substr($titles[ ( time % scalar(@titles)  ) ],0,55); 
			}
		}

	my $checkoutmsg;

	## default to COR
	if ($vars{'checkout'} eq '') { $vars{'checkout'} = 'COR'; }

	if ($vars{'checkout'} eq 'TOP') { $vars{'checkout'} = 'COR'; }
	elsif ($vars{'checkout'} eq 'BOTTOM') { $vars{'checkout'} = 'COR'; }

	if ($vars{'checkout'} eq 'COR') { 
		$html .= '<br><center><table width="95%" bgcolor="white"><tr><td align="center"><font color="black" face="arial, helvetica" size="2"><b>Attention Winning Bidder</b>: <a href="https://ebaycheckout.zoovy.com/legacycheckout.cgi?UUID='.$ID.'&channel='.$CHANNEL.'">Click Here for Zoovy Instant Checkout after the Auction is Over!</a></font></td></tr></table></center><br>';
		$html .= "<br><center><a href=\"https://ebaycheckout.zoovy.com/legacycheckout.cgi?MERCHANT=$MERCHANT&UUID=$ID&channel=$CHANNEL\"><img border=\"0\" src=\"http://www.zoovy.com/htmlwiz/instantcheckout.jpg\" alt=\"Click here for Zoovy Instant Checkout when the Auction is Over\"></a></center><br>";
		}
	$html .= &EBAY::API::addBranding($MERCHANT,$vars{'branding'});	

	my $gallery = '';
	if ($listing->{'IS_MOTORS'}) { $gallery = &addGallery($MERCHANT,$listing->{'PROFILE'},$PRODUCT,'ebaymotors'); }
	else { $gallery = &addGallery($MERCHANT,$listing->{'PROFILE'},$PRODUCT,'ebay'); }

	if ($::DEBUG) { print STDERR "CATEGORY: $vars{'category'}\n"; }

	if ($html =~ /\<\!\-\- EBAY_GALLERY \-\-\>/s) {
		$html =~ s/\<\!\-\- EBAY_GALLERY \-\-\>/$gallery/s;
		}
	else {
		$html .= $gallery;
		}

	if ($vars{'counter'} ne '') {
		require ZOOVY;
		my $BORDER = 0;
		if (($vars{'counter'} eq 'blank') || ($vars{'counter'} eq 'hidden')) { $BORDER = 0; } else { $BORDER = 1; }
		my $UUID = $listing->{'ID'};
		$html .= "<br><center><img border=$BORDER src='http://track.zoovy.com/counter.pl?MID=$MID&MERCHANT=$MERCHANT&PRODUCT=".URI::Escape::uri_escape($PRODUCT)."&UUID=$UUID&TS=".time()."&CHANNEL=$CHANNEL&STYLE=".$vars{'counter'}."'><br></center>";
		}

	## Handle Catalog pieces
	my %info = ();
   my $currency = 'USD';
	if ($vars{'category'} =~ /([\d]+)\.([\d]+)/) { 
		## handle ebay motors .100 categories.
		$info{'#Site'} = $2; $vars{'category'} = $1;
		if ($info{'#Site'}==100) { $listing->{'IS_MOTORS'}=100; }
      if ($info{'#Site'}==15) { $currency = 'AUD'; }
		}

	if ($listing->{'CLASS'} eq 'STORE') {}
	elsif ($vars{'usefixedprice'}>0) { 
		$listing->{'CLASS'} = 'FIXED'; 
		}

	if ($vars{'autopay'}) {
		## autopay not compatible with non-fixedprice or non-buy it now.
		if ($vars{'buyitnow'}>0) {}
		elsif ($vars{'usefixedprice'}>0) {}
		else { $vars{'autopay'} = 0; }
		}

  ## when choosing eBay category, we show UPC/ISBN/EAN field in DVDs, Books, CDs cats
  ## if was selected - pass to eBay	

     #12025	 	Search found too many matches with product identifier <026359294129>, type <UPC>        
   if ($vars{'prod_upc'} eq '026359294129') {
      }
  elsif ($vars{'ext_pid_type'} and $vars{'ext_pid_value'}) {
    $info{'Item.ExternalProductID.Value'} = $vars{'ext_pid_value'};
    $info{'Item.ExternalProductID.Type'} = $vars{'ext_pid_type'};
    }

   if ($vars{'prod_upc'} eq '026359294129') {
      }
	elsif ($vars{'catalog'} eq 'BOOK' || $vars{'catalog'} eq 'DVD' || 
		$vars{'catalog'} eq 'VHS' || $vars{'catalog'} eq 'GAME' || $vars{'catalog'} eq 'CD') {

		## removed profane works
		$vars{'title'} =~ s/ fuck / F**K /igs;
		$vars{'title'} =~ s/ fucking / F***ing /igs;
		$vars{'title'} =~ s/ shit / S**T /igs;

		if ($vars{'catalog'} eq 'BOOK' && $vars{'prod_isbn'} ne '') {
			$info{'Item.ExternalProductID.Value'} = $vars{'prod_isbn'};
			$info{'Item.ExternalProductID.Type'} = 'ISBN';
			$vars{'category'} = 378;
			}
		elsif ($vars{'catalog'} eq 'VHS' && $vars{'prod_upc'} ne '') {
			$info{'Item.ExternalProductID.Value'} = $vars{'prod_upc'};
			$info{'Item.ExternalProductID.Type'} = 'UPC';
			}
		elsif ($vars{'catalog'} eq 'DVD' && $vars{'prod_upc'} ne '') {
			$info{'Item.ExternalProductID.Value'} = $vars{'prod_upc'};
			$info{'Item.ExternalProductID.Type'} = 'UPC';
			$vars{'category'} = 617;
			}


		if ($listing->{'IS_REVISION'}) {
			print STDERR "Can't revise LookupAttributes attributes!\n";
			}
		elsif (uc($vars{'prod_condition'}) eq 'NEW') {
			$info{'Item.LookupAttributeArray.LookupAttribute.Name'} = 'Condition';
			$info{'Item.LookupAttributeArray.LookupAttribute.Value'} = 'New';
			}
		}	
	elsif ($vars{'do_preset'}) {

		if ($vars{'productid'} eq '') {
			require EBAYATTRIBS;
			my %datahash = ($vars{'prod_upc'}=>'');
	#		print STDERR "EBAYATTRIBS::resolve_productids: ".Dumper($MERCHANT,$vars{'catalog'},\%datahash,'',$vars{'password'});
			my ($titleref,$metaref) = &EBAYATTRIBS::resolve_productids($MERCHANT,$vars{'catalog'},\%datahash,'',$vars{'password'});
			$vars{'productid'} = $datahash{ $vars{'prod_upc'} };
			
			if ($titleref->{$vars{'prod_upc'}} eq '') {
				$ERROR = "Preset for catalog [$vars{'catalog'}] KEY [$vars{'prod_upc'}] missing or not available";
				}
			elsif ($vars{'title'} eq '') {
				$vars{'title'} = substr($titleref->{$vars{'prod_upc'}},0,55);
				if (length($vars{'title'})<35) { $vars{'title'} .= uc($vars{'catalog'}).'!'; }
				}

			## Preset Category Rules
			if ($vars{'category'} eq '') {
				$vars{'catalog'} = uc($vars{'catalog'});
				if ($vars{'catalog'} eq 'DVD') { $vars{'category'} = 617; }
				if ($vars{'catalog'} eq 'BOOK') { 
					if ($vars{'category'} eq '') {
						$vars{'category'} = 378; 	## non-fiction books
						}
					}
				if ($vars{'catalog'} eq 'CD') { $vars{'category'} = 307; }
				if ($vars{'catalog'} eq 'VHS') { $vars{'category'} = 309; }
				}
	
			if ($vars{'attributeset'} eq '') {
				$vars{'attributeset'} = $vars{'preset_attrib'};
				}
			
			if ($metaref->{$vars{'prod_upc'}}->{'image'} ne '') {
				if ($vars{'prod_thumb'} eq '') { $vars{'prod_thumb'} = $metaref->{$vars{'prod_upc'}}->{'image'}; }
				if ($vars{'prod_image1'} eq '') { $vars{'prod_image1'} = $metaref->{$vars{'prod_upc'}}->{'image'}; }
				}
			}
		
		# print STDERR "PRESET PRODUCTID: $vars{'productid'} [$vars{'title'}] $vars{'prod_image1'} $vars{'prod_thumb'}\n";
		}


	if ($vars{'attributeset'} eq '') {
		$vars{'attributeset'} = $vars{'preset_attrib'};
		}

	$vars{'reserve'} += 0;
	if ($listing->{'CLASS'} eq 'STORE') {
		## ebaystores:price is a special "starting price" for ebay stores.
		if ($vars{'price'}>0) { $vars{'buyitnow'} = $vars{'price'}; }
		}

	$info{'Item.StartPrice*'} = &XMLTOOLS::currency('StartPrice',$vars{'startprice'},$currency);
	$info{'Item.ReservePrice*'} = &XMLTOOLS::currency('ReservePrice',$vars{'reserve'},$currency);
	if ($vars{'buyitnow'}>0) {
		$info{'Item.BuyItNowPrice*'} = &XMLTOOLS::currency('BuyItNowPrice',$vars{'buyitnow'},$currency);
		}

	my $galleryenable = 0;
	my $galleryurl;
	
	if ($vars{'use_gallery'} eq '_') { $vars{'use_gallery'} = '0'; }
	if ($vars{'use_gallery'} eq 'ON') { $vars{'use_gallery'} = 11; }

	if (($vars{'use_gallery'}>0) && ($vars{'prod_thumb'} eq '')) {
		## wants gallery, but has no image.
		$vars{'prod_thumb'} = $vars{'prod_image1'};
		}

	if (($vars{'use_gallery'}>0) && ($vars{'prod_thumb'} ne '')) {
		## was 96,96
		$galleryurl = &GTOOLS::imageurl($MERCHANT,$vars{'prod_thumb'},0,0,'FFFFFF',0,'jpg');
		$galleryenable = 1;
		## bitwise: 1=auction, 2=fixed, 8=store
		if ($listing->{'CLASS'} eq 'STORE') { $galleryenable = (int($vars{'use_gallery'}) & 8)?8:0; }
		elsif ($listing->{'CLASS'} eq 'FIXED') { $galleryenable = (int($vars{'use_gallery'}) & 2)?2:0; }
		else { $galleryenable = (int($vars{'use_gallery'}) & 1)?1:0; }
		} 
	else {
		## NOTE: this must be blank, because if we send eBay *ANYTHING* related to the gallery they enable it.
		$galleryurl = '';
		$galleryenable = 0;
		if ($::DEBUG) { warn "($vars{'use_gallery'}>0) && ($vars{'prod_thumb'} ne '')"; }
		# die();
		}

	if ($vars{'feature_border'}) { $info{'Item.feature_border*'} = "<ListingEnhancement>Border</ListingEnhancement>"; }
	if ($vars{'feature_bold'}) { $info{'Item.feature_boldtitle*'} = "<ListingEnhancement>BoldTitle</ListingEnhancement>"; }
	if ($vars{'feature_featured'}) { $info{'Item.feature_featured*'} = "<ListingEnhancement>Featured</ListingEnhancement>"; }
	if ($vars{'feature_highlight'}) { $info{'Item.feature_highlight*'} = "<ListingEnhancement>Highlight</ListingEnhancement>"; }
	if ($vars{'feature_homepagefeatured'}) { $info{'Item.feature_homepagefeatured*'} = "<ListingEnhancement>HomePageFeatured</ListingEnhancement>"; }
	if ($vars{'feature_propack'}) { $info{'Item.feature_propack*'} = "<ListingEnhancement>ProPackBundle</ListingEnhancement>"; }
	if ($vars{'feature_valuepack'}) { $info{'Item.feature_valuepack*'} = "<ListingEnhancement>ValuePackBundle</ListingEnhancement>"; }
	if ($vars{'feature_propackplus'}) { $info{'Item.feature_propackplus*'} = "<ListingEnhancement>ProPackPlusBundle</ListingEnhancement>"; }

	my $type = 'Chinese';
	if ($vars{'quantity'}>1) { 
		# dutch auction is type 2
		$type = 'Dutch'; 
		delete $info{'Item.ReservePrice*'};
		}
	
	## other Type: Half, PersonalOffer
	if ($listing->{'IS_SYNDICATED'}>0) {  
		$listing->{'CLASS'} = 'STORE'; 
		}	## hmm... (somehow this is set to FIXED)

	if ($vars{'duration'}==30) {
		## 30 day listing is only good for fixed price.
		$vars{'usefixedprice'}++;
		}

	if (($vars{'usefixedprice'}>0) || ($listing->{'CLASS'} eq 'STORE')) { 
		$type = 'FixedPriceItem'; 
		if ($listing->{'CLASS'} eq 'STORE') { $type = 'StoresFixedPrice'; }
		
		$info{'Item.StartPrice*'} = &XMLTOOLS::currency('StartPrice',$vars{'buyitnow'},$currency);
		delete $info{'Item.ReservePrice*'};
		delete $info{'Item.BuyItNowPrice*'};
		}
	$info{'Item.ListingType'} = $type;
	
	my $VERB = 'AddItem';	
	if ((defined $listing->{'LISTINGID'}) && ($listing->{'LISTINGID'}>0)) {
		$VERB = 'ReviseItem';
		$info{'Item.ItemID'} = $listing->{'LISTINGID'};
		}
	elsif ((defined $RECYCLEID) && ($RECYCLEID>0)) {
		$VERB = 'RelistItem';
		$info{'Item.ItemID'} = $RECYCLEID;
		if (not defined $info{'Item.BuyItNowPrice*'}) { $info{'Item.BuyItNowPrice*'} = &XMLTOOLS::currency('BuyItNowPrice',0,$currency);	}
		if (not defined $info{'Item.ReservePrice*'}) { $info{'Item.ReservePrice*'} = &XMLTOOLS::currency('ReservePrice',0,$currency); }
		print STDERR "Running RelistItem! [$RECYCLEID]\n";

                ## OKAY SO WE'LL FLAG IT AS RECYCLED NOW (BUT IT REALLY HASN'T BEEN YET)
      $listing->{'RECYCLED_ID'} = $RECYCLEID;
		my $pstmt = "update RECYCLE_BIN set RECYCLED_GMT=$^T,RELISTED_EBAY_ID=0,ATTEMPTS=ATTEMPTS+1 where EBAY_ID=".$dbh->quote($RECYCLEID)." and MID=$listing->{'MID'} /* $listing->{'MERCHANT'} */ limit 1";
		print STDERR $pstmt."\n";
		$dbh->do($pstmt);
		}
  $info{'#Verb'} = $VERB;

	## Global fields
   if ($listing->{'ID'} == 33706138) {
 #    my $offset = 22;
 #     print substr($html,$offset*1024,1024);
 #     $html = substr($html,$offset*1024);
      $html =~ s/Google Checkout//gis;
      }
	$info{'Item.Description'} = $html;
	
	
	if ($ID==0) { $ID = time(); }	## 0 is no longer a valid UUID
	$info{'Item.UUID'} = sprintf("%032d",$ID);
	$info{'Item.ThirdPartyCheckout'} = 'true';
  
	if ($listing->{'IS_MOTORS'}) { $info{'Item.ThirdPartyCheckout'} = 'false'; }
	elsif ($vars{'autopay'}) { $info{'Item.ThirdPartyCheckout'} = 'false'; }

	$info{'Item.ThirdPartyCheckoutIntegration'} = 'true';
	if ($listing->{'IS_MOTORS'}) { $info{'Item.ThirdPartyCheckoutIntegration'} = 'false'; }

if ($MERCHANT eq 'pastgentoys') {
#  $vars{'checkout'} = 'EBAY';
  $vars{'autopay'} = 0;
	 }

	if ($vars{'checkout'} eq 'EBAY') {
		$info{'Item.ThirdPartyCheckout'} = 'false';
		$info{'Item.ThirdPartyCheckoutIntegration'} = 'false'; 
		}

	$info{'Item.ApplicationData'} = $listing->{'ID'};
	$info{'Item.CategoryBasedAttributesPrefill'} = 'true';
	$info{'Item.CategoryMappingAllowed'} = 'true';
	# $info{'Item.HitCounter'} = '';
	$info{'Item.Currency'} = $currency;
	$info{'Item.Country'} = 'US';

	## Profile Fields
	$info{'Item.ApplyShippingDiscount'} = &XMLTOOLS::boolean($vars{'applyshippingdiscount'});	
	$info{'Item.AutoPay'} = &XMLTOOLS::boolean($vars{'autopay'});	
	$info{'Item.BuyerRequirements.LinkedPayPalAccount'} = &XMLTOOLS::boolean($vars{'buyreq_linkedpaypal'});
	if (int($vars{'buyreq_maxitemcount'})>0) {
		$info{'Item.BuyerRequirements.MaximumItemRequirements.MaximumItemCount'} = int($vars{'buyreq_maxitemcount'});
		}
	if (int($vars{'buyreq_minfeedback'})>0) {
		$info{'Item.BuyerRequirements.MaximumItemRequirements.MinimumFeedbackScore'} = int($vars{'buyreq_minfeedback'});
		## note there are TWO of these.
		# Item.BuyerRequirements.MinimumFeedbackScore can be -1, -2, -3
		}
	if (int($vars{'buyreq_maxupistrikes'})>0) {
		$info{'Item.BuyerRequirements.MaximumUnpaidItemStrikes'} = &XMLTOOLS::boolean($vars{'buyreq_maxupistrikes'});
		}
	
	## only supported for eBay China
	## $info{'Item.BuyerRequirements.ZeroFeedbackScore'} = &XMLTOOLS::boolean($vars{'buyreq_zerofeedback'});
	## $info{'Item.BuyerRequirements.VerifiedUserRequirements.VerifiedUser'} = &XMLTOOLS::boolean($vars{'buyreq_verifieduser'});
	$info{'Item.BuyerRequirements.ShipToRegistrationCountry'} = 'true';
	
	if ($vars{'location'} eq '') { $vars{'location'} = 'eBay - where else?'; }
	$info{'Item.Location'} = $vars{'location'};
	if ($vars{'lotsize'} ne '') { 
		$info{'Item.LotSize'} = $vars{'lotsize'};
		}

	if ($listing->{'IS_MOTORS'}) {
		$info{'Item.BuyerResponsibleForShipping'} = &XMLTOOLS::boolean($vars{'motor_buyer_does_shipping'});
		$info{'Item.LimitedWarrantyEligible'} = &XMLTOOLS::boolean($vars{'motor_limited_warranty'});
		}

	$info{'Item.DispatchTimeMax'} = int($vars{'dispatchmaxtime'});
	if ($info{'Item.DispatchTimeMax'}==0) {
		$info{'Item.DispatchTimeMax'} = 1;
		}

	$info{'Item.GetItFast'} = &XMLTOOLS::boolean($vars{'getitfast'});	
	$info{'Item.NowAndNew'} = &XMLTOOLS::boolean($vars{'now_and_new'});

	if ($vars{'use_bestoffer'}>0) {
		## ebay:use_bestoffer allows reverse haggle pricing
		$info{'Item.BestOfferDetails.BestOfferEnabled'} = 'true'; 
		}

	## second chance offers
   # if ((defined $vars{'autosecond'}) && ($vars{'autosecond'} eq '1')) {
   if ($vars{'minsellprice'}>0) {
       $listing->{'IS_SCOK'} = sprintf("%.2f",$vars{'minsellprice'});
       }
   #   }

	my $paymentxml = '';
	# (in/out) No payment method specified. For example, no payment methods would be specified for Ad format listings.  
	if ($vars{'pay_none'}) { $paymentxml .= "<PaymentMethods>None</PaymentMethods>\n"; }
	# (in/out) Money order/cashiers check.  
	if ($vars{'pay_mocc'}) { $paymentxml .= "<PaymentMethods>MOCC</PaymentMethods>\n"; }
	# (in/out) American Express.  
	if ($vars{'pay_amex'}) { $paymentxml .= "<PaymentMethods>AmEx</PaymentMethods>\n"; }
	# (in/out) Payment instructions are contained in the item's description.  
	if ($vars{'pay_seeitem'}) { $paymentxml .= "<PaymentMethods>PaymentSeeDescription</PaymentMethods>\n"; }

	# (in/out) Credit card. Not applicable to Real Estate or US/CA eBay Motors listings.  
	# if ($vars{'pay_ccaccepted'}) { $paymentxml .= "<PaymentMethods>CCAccepted</PaymentMethods>\n"; }

	# (in/out) Personal check.  
	if ($vars{'pay_check'}) { $paymentxml .= "<PaymentMethods>PersonalCheck</PaymentMethods>\n"; }
	# (in/out) Cash on delivery. This payment method is obsolete (ignored) for the US, US eBay Motors, UK, and Canada sites. See "Field Differences for eBay Sites" in the eBay Web Services Guide for a list of sites that accept COD as a payment method. Not applicable to Real Estate listings. When revising an item (on sites that still support COD), you can add or change its value.  
	if ($vars{'pay_cod'}) { $paymentxml .= "<PaymentMethods>COD</PaymentMethods>\n"; }
	# (in/out) Visa/Mastercard.  
	if ($vars{'pay_visamc'}) { $paymentxml .= "<PaymentMethods>VisaMC</PaymentMethods>\n"; }
	# (in/out) PaisaPay (for India site only).  
	if ($vars{'pay_paisapay'}) { $paymentxml .= "<PaymentMethods>PaisaPayAccepted</PaymentMethods>\n"; }
	# (in/out) Other forms of payment. Some custom methods are accepted by seller as the payment method in the transaction.  
	if ($vars{'pay_other'}) { $paymentxml .= "<PaymentMethods>Other</PaymentMethods>\n"; }
	# (in/out) PayPal is accepted as a payment method. If true for a listing, Item.PayPalEmailAddress must also be set for the listing. If you don't pass PayPal in the listing request but the seller's eBay preferences are set to accept PayPal on all listings, eBay will add PayPal as a payment method and return a warning. PayPal must be accepted when the seller requires immediate payment (Item.AutoPay) or offers other PayPal-based features, such as a finance offer (Item.FinanceOfferID). PayPal must be accepted for charity listings. PayPal must be accepted for event ticket listings when the venue is in New York state or Illinois, so that eBay can offer buyer protection (per state law). (For some applications, it may be simplest to use errors returned from VerifyAddItem to flag the PayPal requirement for New York and Illinois ticket listings.) For additional information about PayPal, see the eBay Web Services Guide.  
	if ($vars{'pay_paypal'}) { 
		$paymentxml .= "<PaymentMethods>PayPal</PaymentMethods>\n"; 
		$info{'Item.PayPalEmailAddress'} = $vars{'paypalemail'};
		}
	# (in/out) Discover card.  
	if ($vars{'pay_discover'}) { $paymentxml .= "<PaymentMethods>Discover</PaymentMethods>\n"; }
	# (in/out) Payment on delivery. Not applicable to Real Estate or US/CA eBay Motors listings.  
	if ($vars{'pay_cashonpickup'}) { $paymentxml .= "<PaymentMethods>CashOnPickup</PaymentMethods>\n"; }
	# (in/out) Direct transfer of money.  

	if ($info{'#Site'} == 223) {
		## China specific stuff.
		if ($vars{'pay_moneyxfer'}) { $paymentxml .= "<PaymentMethods>MoneyXferAccepted</PaymentMethods>\n"; }
		# (in/out) If the seller has bank account information on file, and MoneyXferAcceptedInCheckout = true, then the bank account information will be displayed in Checkout. Applicable only to certain global eBay sites. See the "International Differences Overview" in the eBay Web Services Guide.  
		if ($vars{'pay_moneyxfercheckout'}) { $paymentxml .= "<PaymentMethods>MoneyXferAcceptedInCheckout</PaymentMethods>\n"; }
		# (in/out) All other online payments.  
		if ($vars{'pay_otheronline'}) { $paymentxml .= "<PaymentMethods>OtherOnlinePayments</PaymentMethods>\n"; }
		# (in/out) China site payment method: Escrow managed payment. If a seller on the eBay China site has a feedback score less than 5 OR a positive feedback rate less than 90% OR the seller is unverified (CN verified status), then escrow is required for the seller to list an item. If escrow is required and an attempt is made to list an item without offering escrow, then an error message is returned. For additional information, see the International Differences Overview in the eBay Web Services Guide.  
		if ($vars{'pay_escrow'}) { $paymentxml .= "<PaymentMethods>Escrow</PaymentMethods>\n"; }
		# (in/out) Cash On Delivery After Paid. Applicable for eBay China site only (site ID 223).  
		if ($vars{'pay_codprepay'}) { $paymentxml .= "<PaymentMethods>CODPrePayDelivery</PaymentMethods>\n"; }
		# (in/out) China site payment method: PostalTransfer.  
		if ($vars{'pay_postaltransfer'}) { $paymentxml .= "<PaymentMethods>PostalTransfer</PaymentMethods>\n"; }
		}

	# (in/out) Loan check option (applicable only to the US eBay Motors site, except in the Parts and Accessories category, and the eBay Canada site for motors).  
	if ($vars{'pay_motor_loancheck'}) { $paymentxml .= "<PaymentMethods>LoanCheck</PaymentMethods>\n"; }
	# (in/out) Cash-in-person option. Applicable only to US and Canada eBay Motors vehicles, (not the Parts and Accessories category).  
	if ($vars{'pay_motor_cash'}) { $paymentxml .= "<PaymentMethods>CashInPerson</PaymentMethods>\n"; }
	if ($info{'Item.AutoPay'} ne 'true') { 
		$paymentxml .= "<PaymentMethods>PaymentSeeDescription</PaymentMethods>";
		}
	$info{'Item.PaymentMethods*'} = $paymentxml;
	if ($vars{'zip'} ne '') { $info{'Item.PostalCode'} = $vars{'zip'};  }

	if (defined($vars{'prod_image1'})) { $vars{'prod_image1'} = &GTOOLS::imageurl($MERCHANT,$vars{'prod_image1'},0,0,'FFFFFF',0,'jpg'); }
	if ($vars{'prod_image1'} eq '') { $vars{'prod_image1'} = 'http://www.zoovy.com/images/blank.gif'; }
	$vars{'prod_image1'} =~ s/\.jpg\.jpg$/\.jpg/g;		# fix image lib screw up


	## Item Specific Fields
	$info{'Item.PictureDetails.Picture'} = 'VendorHostedPicture';
	$info{'Item.PictureDetails.PictureURL'} = $vars{'prod_image1'};

	$info{'Item.Title'} = substr($vars{'title'},0,55);
	if ($vars{'subtitle'} ne '') {
		$info{'Item.SubTitle'} = substr($vars{'subtitle'},0,55);
		}
	elsif ($RECYCLEID>0) {
		$info{'Item.Subtitle*'} = '<Subtitle action="remove"/>';
		}

	##
	## item_condition is set in the profile as a Default if zoovy:prod_condition is NOT set.	
	##		note: eventually we may need to map more complex types e.g. "damaged" to "used"
	##				for now we'll assume ebay does that.
	if ($vars{'prod_condition'} ne '') {}	# use prod_condition!
	elsif ($vars{'item_condition'} eq 'New') { $vars{'prod_condition'} = 'New'; }
	elsif ($vars{'item_condition'} eq 'Used') { $vars{'prod_condition'} = 'Used'; }
	if ($vars{'prod_condition'} ne '') {
		## NOTE: This is apparently only valid for MEDIA categories (fuckers)
		# $info{'Item.LookupAttributeArray.LookupAttribute.Name'} = 'Condition';
		# $info{'Item.LookupAttributeArray.LookupAttribute.Value'} = $vars{'prod_condition'};
		}

	$info{'Item.Quantity'} = $vars{'quantity'};
	$info{'Item.PrivateListing'} = ($vars{'list_private'})?'true':'false';
	$info{'Item.PrivateNotes'} = "SKU: $PRODUCT | Channel: $CHANNEL";  


	if ($listing->{'CLASS'} eq 'STORE') { $info{'Item.Storefront.StoreCategoryID'} = 0; }

   if (($MERCHANT eq 'gogoods') && (int($vars{'storecat'})>=0)) {
      $vars{'storecat'} = $listing->{'STORECAT'};
      }
      
	if (int($vars{'storecat'})>=0) {
		#   0=Not an eBay Store item
		#   1=Other
		#    2=Category 1
		#    3=Category 2
		#    ...
		#    19=Category 18
		#    20=Category 19
		#if ($vars{'storecat'}<100) { $vars{'storecat'}++; }	## NOTE: we treat "0" as other, so category 1 can be 1 (duh!)
		$info{'Item.Storefront.StoreCategoryID'} = $vars{'storecat'};
		if ($info{'Item.Storefront.StoreCategoryID'}<=100) { $info{'Item.Storefront.StoreCategoryID'}++; } 
		}

	if (int($vars{'storecat2'})>0) {
		## second eBay store category
		#if ($vars{'storecat2'}<100) { $vars{'storecat2'}++; }	## NOTE: we treat "0" as other, so category 1 can be 1 (duh!)
		$info{'Item.Storefront.StoreCategory2ID'} = $vars{'storecat2'};
		if ($info{'Item.Storefront.StoreCategory2ID'}<=100) { $info{'Item.Storefront.StoreCategory2ID'}++; } 
		}

   ##
   if ($vars{'attributeset'} eq '') {
     if ($vars{'item_condition'} eq 'New') { 
        ## if no attributes were specified use "New" setting
        $vars{'attributeset'} = qq~<AttributeSetArray><AttributeSet><Attribute attributeID="10244"><Value><ValueID>10425</ValueID></Value></Attribute></AttributeSet></AttributeSetArray>~;
        }
      elsif ($vars{'item_condition'} eq 'Used') { 
        ## if no attributes were specified use "Used" setting
        $vars{'attributeset'} = qq~<AttributeSetArray><AttributeSet><Attribute attributeID="10244"><Value><ValueID>10426</ValueID></Value></Attribute></AttributeSet></AttributeSetArray>~;
        }
     ##  <AttributeSet attributeSetID="1900"><Attribute attributeID="10244"><Value><ValueID>10426</ValueID></Value></Attribute></AttributeSet>
     }                                         

     
     
	if (($vars{'attributeset'} ne '') && ($vars{'attributeset'} !~ /<AttributeSet>/)) {
		## legacy attributes
		$vars{'attributeset'} = &EBAY::CREATE::convertLegacyToUnified($vars{'attributeset'});
		}
	if ($vars{'attributeset'} =~ /attributeSetID=""/) {
      }
    elsif ($vars{'attributeset'} ne '') {
		$info{'Item.AttributeSetArray*'} = $vars{'attributeset'};
		}

	if ($vars{'financeoffer'} ne '') { $info{'Item.FinanceOfferID'} = $vars{'financeoffer'}; }
	if ($listing->{'CLASS'} eq 'STORE') { 
		$vars{'duration'} = 'Days_30';
		if (uc($vars{'storeduration'}) eq 'GTC') {
			## GTC is treated as value. Doh!
			$vars{'duration'} = 'GTC';
			}
		elsif ($vars{'storeduration'}<=30) { 
			$vars{'duration'}='Days_30'; 
			} 
		}
   elsif (int($vars{'duration'})==0) {
      $ERROR = "Invalid value for ebay:duration '$vars{'duration'}' .. hint: must be a number";
      }
	else {
		$vars{'duration'} = 'Days_'.$vars{'duration'};
		}

	$info{'Item.ListingDuration'} = $vars{'duration'};
	$info{'Item.PictureDetails.GalleryType'} = ($galleryenable>0)?'Gallery':'None';
	if ($vars{'featured'} eq '') { $vars{'featured'} = '0'; }
	if (&ZOOVY::is_true($vars{'featured'})) { 
		$info{'Item.PictureDetails.GalleryType'} = 'Featured';
		}
   elsif (&ZOOVY::is_true($vars{'feature_galleryfirst'})) {
      $info{'Item.PictureDetails.GalleryType'} = 'Featured';
      }
	$info{'Item.PictureDetails.GalleryURL'} = $galleryurl;
	## eBay doesn't accept blank gifs into the gallery
	if ($info{'Item.PictureDetails.GalleryURL'} =~ /images\/blank\.gif$/) { $info{'Item.PictureDetails.GalleryURL'} = ''; }
	if ($info{'Item.PictureDetails.GalleryURL'} eq '') { 
		$info{'Item.PictureDetails.GalleryType'} = 'None';
		delete $info{'Item.PictureDetails.GalleryURL'}; 
		if ($RECYCLEID>0) { $info{'Item.PictureDetails.GalleryType'} = 'None'; }
		}
		# only on US site

	$info{'Item.PrimaryCategory.CategoryID'} = $vars{'category'};
	if ($vars{'category'} eq '') {
		$ERROR = "Primary Category not set";
		# die("Category not set!\n");
		}
	if (int($vars{'category2'})>0) {
		$info{'Item.SecondaryCategory.CategoryID'} = $vars{'category2'};
		}
	$info{'Item.SellerInventoryID'} = $PRODUCT;
	$info{'Item.SKU'} = $PRODUCT;

	if ($vars{'skypeid'} ne '') {
		$info{'Item.SkypeEnabled'} = 'true';
		$info{'Item.SkypeID'} = $vars{'skypeid'};
		$info{'Item.SkypeOption'} = $vars{'skypeoption'};
		}
		


	## new eBay Pre-Filled Item Specifics
	if ($vars{'productid'} =~ /[<>]+/) { $vars{'productid'} = ''; } # fix corrupt product id's
	if ($vars{'productid'} ne '') {
		## see if eBay has a stock photo
		my $dbh = &EBAY::API::db_ebay_connect();
		my $pstmt = "select count(*) from PROD_NO_PICTURES where EBAYPROD=".$dbh->quote($vars{'productid'});
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		my ($missingpic) = $sth->fetchrow();
		$sth->finish();
		&EBAY::API::db_ebay_close();
		
		my $includestock = 'false';
		if (not $missingpic) { $includestock = 'true'; } 

		#$hash{'**ProductInfo'} = qq~
  		#	<ProductInfo id="$vars{'productid'}">
		#		<IncludeStockPhotoURL>$includestock</IncludeStockPhotoURL>
		#		<IncludePrefilledItemInformation>1</IncludePrefilledItemInformation>
		#		<UseStockPhotoURLAsGallery>$includestock</UseStockPhotoURLAsGallery>
		#	</ProductInfo>
		#	~;
		$info{'Item.ProductListingDetails.ProductID'} = $vars{'productid'};
		$info{'Item.ProductListingDetails.IncludeprefilledItemInformation'} = 1;
		$info{'Item.ProductListingDetails.IncludeStockPhotoURL'} = $includestock;
		$info{'Item.ProductListingDetails.UseStockPhotoURLAsGallery'} = $includestock;
		}
	

	##
	## SHIPPING!
	##
	if ($vars{'calcshipping'}<2) {
		push @MSGS, "WARN|This profile uses deprecated ebay shipping, please hit 'SAVE' in setup/ebay to update.";
		}
	else {
		$info{'Item.ShippingDetails.x*'} = shippingXML($MERCHANT,$listing->{'PROFILE'},\%info,\%vars,\@MSGS);
		$info{'Item.CheckoutDetailsSpecified'} = &XMLTOOLS::boolean(1);
		$info{'Item.UseTaxTable'} = &XMLTOOLS::boolean($vars{'use_taxtable'});

		if ($vars{'ship_intlocations'} ne '') {
			my $mylocs = &ZTOOLKIT::parseparams($vars{'ship_intlocations'},1);
			my @locs = ();
		#	if ($mylocs->{'Europe'}) {
		#		delete $mylocs->{'Europe'};
		#		push @locs, ('DE','UK','FR','IT','GR');
		#		}
		#	if ($mylocs->{'Asia'}) {
		#		push @locs, ('CN','VT');
		#		}
			if ($mylocs->{'Worldwide'}) {
				@locs = ('WorldWide');
				$mylocs = {};
				}
			push @locs, keys %{$mylocs};
			## wow the documentation is fucking stupid, it's ShipToLocation not ShipToLocation(s)
			foreach my $loc (@locs) {
				$info{'Item.ShipToLocations-'.$loc.'*'} = "<ShipToLocations>$loc</ShipToLocations>";
				}
			}
		# <ShipToLocations> string </ShipToLocations>
		}


	if ($vars{'return_desc'} ne '') {
		$info{'Item.ReturnPolicy.Description'} = $vars{'return_desc'};
		}

	if ($vars{'return_acceptpolicy'} ne '') {
		$info{'Item.ReturnPolicy.ReturnsAcceptedOption'} = $vars{'return_acceptpolicy'};
		# Item.ReturnPolicy.RefundOption
		if ($vars{'return_refundpolicy'} ne '') {
			$info{'Item.ReturnPolicy.RefundOption'} = $vars{'return_refundpolicy'};
			}
		# Item.ReturnPolicy.ReturnsWithinOption
		if ($vars{'return_withinpolicy'} ne '') {
			$info{'Item.ReturnPolicy.ReturnsWithinOption'} = $vars{'return_withinpolicy'};
			}
		# Item.ReturnPolicy.ShippingCostPaidByOption
		if ($vars{'return_shipcostpolicy'} ne '') {
			$info{'Item.ReturnPolicy.ShippingCostPaidByOption'} = $vars{'return_shipcostpolicy'};
			}
		## *** NOT SUPPORTED YET ***
		# Item.ReturnPolicy.WarrantyDurationOption
		# Item.ReturnPolicy.WarrantyOfferedOption
		# Item.ReturnPolicy.WarrantyTypeOption
		}

	open F, ">/tmp/dump.$MERCHANT";
	print F Dumper($MERCHANT,\%info,\%vars,$nsref,$dataref);
	close F;
	chmod 0666, "/tmp/dump.$MERCHANT";

	return($ERROR,\%info,\@MSGS);	
	}




##
## attempts to create a listing with bogus values to test configuration.
##
##	
sub VerifyConfig {
	my ($USERNAME,$PROFILE,%options) = @_;

	my %vars = ();
	$vars{'ebay:pkg_depth'} = 1;
	$vars{'ebay:pkg_length'} = 1;
	$vars{'ebay:pkg_width'} = 1;
	$vars{'ebay:ship_intpkghndcosts'} = '1.00';
	$vars{'ebay:ship_dompkghndcosts'} = '1.00';
	$vars{'ebay:ship_irregular'} = 0;
	$vars{'ebay:pay_visamc'}++;
	$vars{'ebay:category'} = 38097;

	my $MID = &ZOOVY::resolve_mid($USERNAME);
	my $edbh = &EBAY::API::db_ebay_connect();
	
	require EBAY::LISTING;
	my ($listing) = EBAY::LISTING->new($USERNAME,'EBAY',channel=>0);
	$listing->{'DATAREF'} = \%vars;
	$listing->{'CLASS'} = 'AUCTION';
	$listing->{'MERCHANT'} = $USERNAME;
	$listing->{'PRODUCT'} = '**DUMMY**';
	$listing->{'MID'} = $MID;
	$listing->{'PROFILE'} = $PROFILE;

	my ($err,$hashref,$msgs) = EBAY::CREATE::doit2($listing,$edbh); 
	$hashref->{'Item.Quantity'} = 1;
	$hashref->{'Item.Description'} = 'testitem';
	$hashref->{'Item.Title'} = 'this is the title';
	$hashref->{'Item.StartPrice*'} = &XMLTOOLS::currency('StartPrice','1.00','USD');
	if ($options{'dumper'}) { print Dumper($err,$msgs); }
	
	my ($r) =  &EBAY::API::doRequest($USERNAME,$PROFILE,'VerifyAddItem',$hashref,preservekeys=>['Item'],noflatten=>['Fees'],xml=>1);
	my ($resultref) = &EBAY::CREATE::parse_errors($r,0,$hashref,\%vars);
	&EBAY::API::db_ebay_close();

	use Data::Dumper;
	if ($options{'dumper'}) { print Dumper($hashref,$err,$resultref,$msgs,$r); }

	my $errmsg = '';
	foreach my $err (@{$r->{'.ERRORS'}}) {
      #                   {
       #                    'ShortMessage' => 'Shipping Surcharge fee is not applicable',
      #                     'ErrorCode' => 219214,
      #                     'SeverityCode' => 'Error',
      #                     'LongMessage' => 'Shipping Surcharge fee is not applicable for this shipping service.',
      #                     'ErrorClassification' => 'RequestError'
      #                   }
		#

		## eBay is a bunch of fucking idiots.
		## The specified UUID has already been used; ListedByRequestAppId=1, item ID=7236587050.
		next if ($err->{'ErrorCode'} == 488);
	
		my $hint = '';
		if ($err->{'ErrorCode'} == 38) {
			## Your application encountered an error. This request is missing required value in input tag <InternationalShippingServiceOption>.<ShipToLocation>.
			$hint = "Try specifying one more /Permitted International Shipping Destinations/ if you want to ship internationally";
			}
		elsif ($err->{'ErrorCode'} == 12519) {
			## Shipping service Other (see description)(14) is not available.
			$hint = "You probably need to specify fixed shipping prices to utilize this shipping method.";
			}
		elsif ($err->{'ErrorCode'} == 219214) {
			$hint = "eBay is aware that the US Postal service has no handling fee to AK/HI, so they won't let you charge one. (Use UPS Shipping)";
			}

		if ($hint ne '') { $hint = "<br><font color='blue'>RECOMMENDATION: $hint<br></font>"; }
		$err->{'LongMessage'} = &ZOOVY::incode($err->{'LongMessage'});
		$err->{'ShortMessage'} = &ZOOVY::incode($err->{'ShortMessage'});
		$errmsg .= "<tr><td valign='top'>EBAY-$err->{'SeverityCode'} #$err->{'ErrorCode'}</td><td valign='top'><b>$err->{'ShortMessage'}</b><br><div class='hint'>$err->{'LongMessage'}$hint</div></td></tr>";
		}
	foreach my $msg (@{$msgs}) {
		my ($type) = '';
		if ($msg =~ /\|/) { ($type,$msg) = split(/\|/,$msg,2); }
		next if ($type eq 'INFO');
		$msg =~ s/[\<\>]+//gs;
		$msg = &ZOOVY::incode($msg);
		$errmsg .= "<tr><td>Z-$type</td><td>$msg</td></tr>";
		}

	if ($errmsg ne '') {
		$errmsg = "<table width=100% class='zoovytable'><tr class='zoovysub2header'><td>Code</td><td>Detail</td></tr>\n$errmsg</table>";
		}

	return($errmsg);
	}


























































































































sub addGallery {	
	my ($USERNAME, $profile, $PRODUCT, $market, $STYLE, $VARSTEXT, $PREVIEWUSER) = @_;

	$USERNAME = lc($USERNAME);
	if ($market eq '') { $market = 'ebay'; }

	my $hashref = undef;
	my $text = '';

	if ((not defined $STYLE) || (not defined $VARSTEXT)) {
		my $dbh = &EBAY::API::db_ebay_connect();
		my ($MID) = &ZOOVY::resolve_mid($USERNAME);
		my $pstmt = "select * from EBAY_TOKENS where MID=$MID /* $USERNAME */ order by ID desc";
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		if ($sth->rows>0) {
			$hashref = $sth->fetchrow_hashref();
			}
		$sth->finish();
		$STYLE = $hashref->{'GALLERY_STYLE'};
		$VARSTEXT = $hashref->{'GALLERY_VARS'};
		&EBAY::API::db_ebay_close();
		}

	if (defined $PREVIEWUSER) { $USERNAME = $PREVIEWUSER; }

	my $vars = &ZTOOLKIT::parseparams($VARSTEXT);

	if ($STYLE==0) {
		}
	elsif ($STYLE==1) {
		if ($market eq 'ebaymotors') { $market = 'ebay'; }
		######################################################################################################
		## Text Gallery Link!
		######################################################################################################
		$text = '<br>';
		$text .= "<a href=\"http://$USERNAME.zoovy.com/gallery.cgis?marketplace=$market&profile=$profile\">$vars->{'msg'}</a>";
		}
	elsif ($STYLE==2) {
		######################################################################################################
		## Showcase style 1 (no search)
		######################################################################################################
		my $bgcolor = ($vars->{'bgcolor'})?$vars->{'bgcolor'}:'FFFFFF';
		my $cols = ($vars->{'cols'})?$vars->{'cols'}:'1';
		my $limit = ($vars->{'items'})?$vars->{'items'}:'14';

		my ($face,$background,$arrow,$other,$highlight,$textcolor);

		if ($bgcolor eq '000000') {
			$bgcolor = '999999';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('C0C0C0','FFFFFF','E0E0E0','AAAAAA','F0F0F0','FFFFFF');
			}
		elsif ($bgcolor eq 'C0C0C0') {
			}
		elsif ($bgcolor eq '7777FF') {
			$bgcolor = 'E1E1E1';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','000000','000000','555599','222299','777799');
			}
		elsif ($bgcolor eq 'FF7777') {
			$bgcolor = 'C0C0C0';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','000000','000000','995555','992222','997777');
			}
		else {
			## default to white
			$bgcolor = 'EFEFEF';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','247700','006600','333333','F0F0F0','000000');
			}
		
		$text .= qq~
<OBJECT classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"
 codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,0,0"
 WIDTH="600" HEIGHT="360" id="auction_gallery" ALIGN="center">
 <PARAM NAME=movie VALUE="http://gfx.zoovy.com/gallery/gallery.swf">
<PARAM NAME=FlashVars VALUE="merchant=$USERNAME&product=$PRODUCT&thumbcols=$cols&limit=$limit&face=0x$face&background=0x$background&arrow=0x$arrow&darkshadow=0x$other&highlight=0x$highlight&highlight3d=0x$other&scrolltrack=0x$other&selection=0x$other&textselected=0x$textcolor&textcolor=0x$textcolor&textsize=10&profile=$profile">
<PARAM NAME=quality VALUE=high> 
<PARAM NAME=bgcolor VALUE=#$bgcolor>
<EMBED src="http://gfx.zoovy.com/gallery/gallery.swf" FlashVars="merchant=$USERNAME&product=$PRODUCT&thumbcols=$cols&limit=$limit&face=0x$face&background=0x$background&arrow=0x$arrow&darkshadow=0x$other&highlight=0x$highlight&highlight3d=0x$other&scrolltrack=0x$other&selection=0x$other&textselected=0x$textcolor&textcolor=0x$textcolor&textsize=10&profile=$profile" quality=high bgcolor=#$bgcolor WIDTH="600" HEIGHT="360" NAME="auction_gallery" ALIGN="center"
TYPE="application/x-shockwave-flash" PLUGINSPAGE="http://www.macromedia.com/go/getflashplayer"></EMBED>
</OBJECT>
		~		
		}
	elsif ($STYLE==3) {
		######################################################################################################
		## Showcase style 2 (with search)
		######################################################################################################
		my $bgcolor = ($vars->{'bgcolor'})?$vars->{'bgcolor'}:'FFFFFF';
		my $cols = ($vars->{'cols'})?$vars->{'cols'}:'1';
		my $limit = ($vars->{'items'})?$vars->{'items'}:'14';

#		my $face = 'ffffff'; my $background = '247700'; my $arrow = '006600';  my $other = '006600';
#		my $highlight = 'EFEFEF'; my $textcolor = '000000';
		my ($face,$background,$arrow,$other,$highlight,$textcolor);

		if ($bgcolor eq '000000') {
			$bgcolor = '999999';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('C0C0C0','FFFFFF','E0E0E0','AAAAAA','F0F0F0','FFFFFF');
			}
		elsif ($bgcolor eq 'C0C0C0') {
			}
		elsif ($bgcolor eq '7777FF') {
			$bgcolor = 'E1E1E1';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','000000','000000','555599','222299','777799');
			}
		elsif ($bgcolor eq 'FF7777') {
			$bgcolor = 'C0C0C0';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','000000','000000','995555','992222','997777');
			}
		else {
			## default to white
			$bgcolor = 'EFEFEF';
			($face,$background,$arrow,$other,$highlight,$textcolor) = ('ffffff','247700','006600','333333','F0F0F0','000000');
			}

		$text .= qq~
<OBJECT classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"
 codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,0,0"
 WIDTH="616" HEIGHT="364" id="auction_gallery" ALIGN="center">
 <PARAM NAME=movie VALUE="http://gfx.zoovy.com/gallery/gallery2.swf">
<PARAM NAME=FlashVars VALUE="merchant=$USERNAME&product=$PRODUCT&thumbcols=$cols&limit=$limit&face=0x$face&background=0x$background&arrow=0x$arrow&darkshadow=0x$other&highlight=0x$highlight&highlight3d=0x$other&scrolltrack=0x$other&selection=0x$other&textselected=0x$textcolor&textcolor=0x$textcolor&textsize=10&profile=$profile">
<PARAM NAME=quality VALUE=high> 
<PARAM NAME=bgcolor VALUE=#$bgcolor>
<EMBED src="http://gfx.zoovy.com/gallery/gallery2.swf" FlashVars="merchant=$USERNAME&product=$PRODUCT&thumbcols=$cols&limit=$limit&face=0x$face&background=0x$background&arrow=0x$arrow&darkshadow=0x$other&highlight=0x$highlight&highlight3d=0x$other&scrolltrack=0x$other&selection=0x$other&textselected=0x$textcolor&textcolor=0x$textcolor&textsize=10&profile=$profile" quality=high bgcolor=#$bgcolor WIDTH="600" HEIGHT="360" NAME="auction_gallery" ALIGN="center"
TYPE="application/x-shockwave-flash" PLUGINSPAGE="http://www.macromedia.com/go/getflashplayer"></EMBED>
</OBJECT>

		~;
		}
	elsif ($STYLE==8) {
		######################################################################################################
		###  Carousel
		######################################################################################################
		my $COLORS = '';

		if ($vars->{'scheme'} eq '') { $vars->{'scheme'} = 1; }
		if ($vars->{'items'} eq '') { $vars->{'items'} = 8; }

		if ($vars->{'scheme'}==1) {$COLORS = "button_on=0xCD8500&button_off=0x607B8B&frame_bg_color=0x607B8B&frame_hilite_color=0xCD8500&data_frame_color=0xCD8500&image_bg_color=607B8B&text_color=0x000000&alt_text_color=0xffffff"; }
		elsif ($vars->{'scheme'}==2) { $COLORS = "button_on=0xFFC70C&button_off=0x3D64B1&frame_bg_color=0x3D64B1&frame_hilite_color=0xFFC70C&data_frame_color=0xCDCDCD&image_bg_color=3D64B1&text_color=0x000000&alt_text_color=0xffffff"; }
		elsif ($vars->{'scheme'}==3) { $COLORS = "button_on=0xCCCCCC&button_off=0x006633&frame_bg_color=0x006633&frame_hilite_color=0xCCCCCC&data_frame_color=0xCDCDCD&image_bg_color=006633&text_color=0x000000&alt_text_color=0xffffff"; }
		elsif ($vars->{'scheme'}==0) { $COLORS = $vars->{'custom'}; }

		$COLORS .= '&limit='.$vars->{'items'};

		$text .= qq~
<center>
<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://fpdownload.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=7,0,0,0" width="550" height="235" id="Carousel" align="middle">
<param name="allowScriptAccess" value="sameDomain" />
<param name="movie" value="http://gfx.zoovy.com/carousel/carousel.swf" />
<param name="quality" value="high" />
<param name="bgcolor" value="#ffffff" />
<param name="flashvars" value="hidecontrol=0&theme=gel&merchant=$USERNAME&product=$PRODUCT&profile=$profile&$COLORS"/>
<param name="CreatedBy" value="Zoovy" />
<embed src="http://gfx.zoovy.com/carousel/carousel.swf" quality="high" bgcolor="#ffffff" width="550" height="235" name="Carousel" align="middle" allowScriptAccess="sameDomain" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" FlashVars="hidecontrol=0&theme=gel&merchant=$USERNAME&product=$PRODUCT&profile=$profile&$COLORS"/>
</object>
</center>
		~;

		}

	$text .= "<!-- $USERNAME -->";

	return($text);
	}















sub save_profile {
	my ($MERCHANT,$CODE,$p) = @_;

	my $dbh = &EBAY::API::db_ebay_connect();

	my $ref = &ZOOVY::fetchmerchantns_ref($MERCHANT,$CODE);
	foreach my $k (keys %{$p}) {
		$ref->{$k} = $p->{$k};
		}
	&ZOOVY::savemerchantns_ref($MERCHANT,$CODE,$ref);
	return($ref);


	my $MID = &ZOOVY::resolve_mid($MERCHANT);
	my $qtMERCHANT = $dbh->quote($MERCHANT);
	if ($CODE eq '') { $CODE = 'DEFAULT'; }
	my $qtCODE = $dbh->quote($CODE);

	my $pstmt = "select count(*) from EBAY_PROFILES where MID=$MID /* $MERCHANT */ and CODE=$qtCODE";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();
	print STDERR "[$count] $pstmt\n";
	if ($count==0) {
		$pstmt = "insert into EBAY_PROFILES (MID,MERCHANT,CODE) values ($MID,$qtMERCHANT,$qtCODE)";
		# print STDERR $pstmt."\n";
		$dbh->do($pstmt);
		}

	$pstmt = "update EBAY_PROFILES set CONFIG_UPDATED_GMT=".time();

	## variables we need to handle special
	if (defined $p->{'ebay:salestaxpercent'}) {
		$pstmt .= ',CONFIG_SALESTAXSTATE='.$dbh->quote($p->{'ebay:salestaxpercent'});
		delete $p->{'ebay:ssalestaxpercent'};
		}

	foreach my $k (keys %{$p}) {
		## key is: ebay:var or zoovy:var
		my ($owner,$val) = split(/:/,$k);
		$val =~ s/\W+//g;
		$val = uc($val);
		if ($val eq 'NOTES_DEFAULT') {}
		elsif (($val eq 'TOKEN') || ($val eq 'TEMPLATE')) {
			$pstmt .= ','.uc($val).'='.$dbh->quote($p->{$k});	## no CONFIG_
			}
		else {
			$pstmt .= ',CONFIG_'.uc($val).'='.$dbh->quote($p->{$k});
			}
		}
	$pstmt .= " where CODE=$qtCODE and MID=$MID /* ".$dbh->quote($MERCHANT)." */";
	# print STDERR $pstmt."\n";
	$dbh->do($pstmt);

	&ZOOVY::savemerchantns_attrib($MERCHANT,$CODE,'ebay:template',$p->{'ebay:template'});

	&EBAY::API::db_ebay_close();
	}


sub load_profile {
	my ($MERCHANT,$CODE,$resultref) = @_;

	my $ref = &ZOOVY::fetchmerchantns_ref($MERCHANT,$CODE);
	return($ref);

	return;

	if (not defined $resultref) {
		my %results;
		$resultref = \%results;
		}

	my $dbh = &EBAY::API::db_ebay_connect();
	my $MID = &ZOOVY::resolve_mid($MERCHANT);
	my $pstmt = "select * from EBAY_PROFILES where MID=$MID /* ".$dbh->quote($MERCHANT)." */ ";
	if ($CODE eq '') { $CODE = 'DEFAULT'; }
	if ($CODE ne '') { $pstmt .= " and CODE=".$dbh->quote($CODE); }

	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($hashref) = $sth->fetchrow_hashref();
	$sth->finish();

	if ($hashref->{'CONFIG_UPDATED_GMT'}==0) {
		$resultref->{'ebay:config_updated'} = 0;
		$resultref->{'ebay:salestaxstate'} = '';
		$resultref->{'ebay:salestaxpercent'} = '';
		$resultref->{'ebay:ship_tax'} = 0;
		$resultref->{'ebay:location'} = 'eBay - where else?';
		$resultref->{'ebay:country'} = 'us'; 
		$resultref->{'ebay:regional_list'} = '0'; 
		$resultref->{'ebay:ship_international'} = 'siteonly'; 
		$resultref->{'zoovy:paypalemail'} = '';
		$resultref->{'ebay:checkout'} = 'BOTTOM';
		$resultref->{'ebay:checkoutmsg'} = '';
		$resultref->{'ebay:northamerica'} = '';
		$resultref->{'ebay:europe'} = '';
		$resultref->{'ebay:oceania'} = '';
		$resultref->{'ebay:asia'} = '';
		$resultref->{'ebay:southamerica'} = '';
		$resultref->{'ebay:africa'} = '';
		$resultref->{'ebay:latinamerica'} = '';
		$resultref->{'ebay:middleeast'} = '';
		$resultref->{'ebay:caribbean'} = '';
		$resultref->{'zoovy:allow_moneyorder'} = '';
		$resultref->{'zoovy:allow_paypal'} = '';
		$resultref->{'zoovy:allow_personalcheck'} = '';
		$resultref->{'zoovy:allow_visamastercard'} = '';
		$resultref->{'zoovy:allow_amex'} = '';
		$resultref->{'zoovy:allow_discover'} = '';
		$resultref->{'zoovy:allow_other'} = '';
		$resultref->{'zoovy:zip'} = '';
		$resultref->{'ebay:shipmethods'} = '';
		$resultref->{'ebay:token'} = 0;
		}
	else {
		$resultref->{'ebay:config_updated'} = $hashref->{'CONFIG_UPDATED_GMT'};
		$resultref->{'ebay:salestaxstate'} = $hashref->{'CONFIG_SALESTAXSTATE'};
		$resultref->{'ebay:salestaxpercent'} = $hashref->{'CONFIG_SALESTAXPERCENT'};
		$resultref->{'ebay:ship_tax'} = $hashref->{'CONFIG_SHIP_TAX'};
		$resultref->{'ebay:location'} = $hashref->{'CONFIG_LOCATION'};
		$resultref->{'ebay:country'} = $hashref->{'CONFIG_COUNTRY'};
		$resultref->{'ebay:regional_list'} = $hashref->{'CONFIG_REGIONAL_LIST'};
		$resultref->{'ebay:ship_international'} = $hashref->{'CONFIG_SHIP_INTERNATIONAL'}; 
		$resultref->{'zoovy:paypalemail'} = $hashref->{'CONFIG_PAYPALEMAIL'};
		$resultref->{'ebay:checkout'} = $hashref->{'CONFIG_CHECKOUT'};
		$resultref->{'ebay:checkoutmsg'} = $hashref->{'CONFIG_CHECKOUTMSG'};
		## checkboxes!
		$resultref->{'ebay:northamerica'} = $hashref->{'CONFIG_NORTHAMERICA'};
		$resultref->{'ebay:europe'} = $hashref->{'CONFIG_EUROPE'};
		$resultref->{'ebay:oceania'} = $hashref->{'CONFIG_OCEANIA'};
		$resultref->{'ebay:asia'} = $hashref->{'CONFIG_ASIA'};
		$resultref->{'ebay:southamerica'} = $hashref->{'CONFIG_SOUTHAMERICA'};
		$resultref->{'ebay:africa'} = $hashref->{'CONFIG_AFRICA'};
		$resultref->{'ebay:latinamerica'} = $hashref->{'CONFIG_LATINAMERICA'};
		$resultref->{'ebay:middleeast'} = $hashref->{'CONFIG_MIDDLEEAST'};
		$resultref->{'ebay:caribbean'} = $hashref->{'CONFIG_CARIBBEAN'};
		$resultref->{'zoovy:allow_paypal'} = $hashref->{'CONFIG_ALLOW_PAYPAL'};
		$resultref->{'zoovy:allow_moneyorder'} = $hashref->{'CONFIG_ALLOW_MONEYORDER'};
		$resultref->{'zoovy:allow_personalcheck'} = $hashref->{'CONFIG_ALLOW_PERSONALCHECK'};
		$resultref->{'zoovy:allow_visamastercard'} = $hashref->{'CONFIG_ALLOW_VISAMASTERCARD'};
		$resultref->{'zoovy:allow_amex'} = $hashref->{'CONFIG_ALLOW_AMEX'};
		$resultref->{'zoovy:allow_discover'} = $hashref->{'CONFIG_ALLOW_DISCOVER'};
		$resultref->{'zoovy:allow_other'} = $hashref->{'CONFIG_ALLOW_OTHER'};	
		$resultref->{'zoovy:zip'} = $hashref->{'CONFIG_ZIP'}; 
		$resultref->{'ebay:shipmethods'} = $hashref->{'CONFIG_SHIPMETHODS'};
		$resultref->{'ebay:token'} = $hashref->{'TOKEN'};
		}
	$resultref->{'ebay:template'} = &ZOOVY::fetchmerchantns_attrib($MERCHANT,$CODE,'ebay:template');
	
	&EBAY::API::db_ebay_close();
	return($resultref);
	}




sub smart_weight
{
   my ($weight) = @_;
	use lib "/httpd/modules";
	require ZTOOLKIT;
   if (not defined $weight) { $weight = 0; } ## Make sure its defined
   $weight =~ s/\s+//gs; ## Strip spaces
   if ($weight eq '') { $weight = '0'; }
   my $oz = 0;
   my $lbs = 0;
   if ($weight =~ m/^(\d+\.?|\d*\.\d+)$/) { $oz = $1; }
   elsif ($weight =~ m/^(\d+\.?|\d*\.\d+)?\#(\d+\.?|\d*\.\d+)?$/) { $lbs = &ZTOOLKIT::def($1,0); $oz = &ZTOOLKIT::def($2,0); }
   else { return undef; }

	## error cases
	## more than 16 oz
	if ($lbs==0 && $oz>=16) {
		$lbs = int($oz/16);
		$oz = $oz % 16;
		}

	if ($lbs==0 && $oz<1) {
		# ebay won't accept less than 1oz
		$oz = 1;
		}

   return ($lbs,$oz);
}



1;
