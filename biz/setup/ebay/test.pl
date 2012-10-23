#!/usr/bin/perl

$x = q~
<ShippingDetails>
      <CalculatedShippingRate> 
        <InternationalPackagingHandlingCosts currencyID="CurrencyCodeType"> AmountType (double) </InternationalPackagingHandlingCosts>
        <MeasurementUnit> MeasurementSystemCodeType </MeasurementUnit>
        <OriginatingPostalCode> string </OriginatingPostalCode>
        <PackageDepth unit="token" measurementSystem="MeasurementSystemCodeType"> MeasureType (decimal) </PackageDepth>
        <PackageLength unit="token" measurementSystem="MeasurementSystemCodeType"> MeasureType (decimal) </PackageLength>
        <PackageWidth unit="token" measurementSystem="MeasurementSystemCodeType"> MeasureType (decimal) </PackageWidth>
        <PackagingHandlingCosts currencyID="CurrencyCodeType"> AmountType (double) </PackagingHandlingCosts>
        <ShippingIrregular> boolean </ShippingIrregular>
        <ShippingPackage> ShippingPackageCodeType </ShippingPackage>
        <WeightMajor unit="token" measurementSystem="MeasurementSystemCodeType"> MeasureType (decimal) </WeightMajor>
        <WeightMinor unit="token" measurementSystem="MeasurementSystemCodeType"> MeasureType (decimal) </WeightMinor>
      </CalculatedShippingRate>
      <CODCost currencyID="CurrencyCodeType"> AmountType (double) </CODCost>
      <InsuranceDetails> InsuranceDetailsType 
        <InsuranceFee currencyID="CurrencyCodeType"> AmountType (double) </InsuranceFee>
        <InsuranceOption> InsuranceOptionCodeType </InsuranceOption>
      </InsuranceDetails>
      <InsuranceFee currencyID="CurrencyCodeType"> AmountType (double) </InsuranceFee>
      <InsuranceOption> InsuranceOptionCodeType </InsuranceOption>
      <InternationalInsuranceDetails> InsuranceDetailsType 
        <InsuranceFee currencyID="CurrencyCodeType"> AmountType (double) </InsuranceFee>
        <InsuranceOption> InsuranceOptionCodeType </InsuranceOption>
      </InternationalInsuranceDetails>
      <InternationalPromotionalShippingDiscount> boolean </InternationalPromotionalShippingDiscount>
      <InternationalShippingDiscountProfileID> string </InternationalShippingDiscountProfileID>
      <InternationalShippingServiceOption> InternationalShippingServiceOptionsType 
        <ShippingService> token </ShippingService>
        <ShippingServiceAdditionalCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceAdditionalCost>
        <ShippingServiceCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceCost>
        <ShippingServicePriority> int </ShippingServicePriority>
        <ShipToLocation> string </ShipToLocation>
        <!-- ... more ShipToLocation nodes here ... -->
      </InternationalShippingServiceOption>
      <!-- ... more InternationalShippingServiceOption nodes here ... -->
      <PaymentInstructions> string </PaymentInstructions>
      <PromotionalShippingDiscount> boolean </PromotionalShippingDiscount>
      <SalesTax> SalesTaxType 
        <SalesTaxPercent> float </SalesTaxPercent>
        <SalesTaxState> string </SalesTaxState>
        <ShippingIncludedInTax> boolean </ShippingIncludedInTax>
      </SalesTax>
      <ShippingDiscountProfileID> string </ShippingDiscountProfileID>
      <ShippingServiceOptions> ShippingServiceOptionsType 
        <FreeShipping> boolean </FreeShipping>
        <ShippingService> token </ShippingService>
        <ShippingServiceAdditionalCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceAdditionalCost>
        <ShippingServiceCost currencyID="CurrencyCodeType"> AmountType (double) </ShippingServiceCost>
        <ShippingServicePriority> int </ShippingServicePriority>
        <ShippingSurcharge currencyID="CurrencyCodeType"> AmountType (double) </ShippingSurcharge>
      </ShippingServiceOptions>
      <!-- ... more ShippingServiceOptions nodes here ... -->
      <ShippingType> ShippingTypeCodeType </ShippingType>
    </ShippingDetails>
~;

use XML::Simple;

my $ref= XMLin($x,ForceArray=>1,);
use Data::Dumper;
print Dumper($ref);
use YAML;

print YAML::Dump($ref);
