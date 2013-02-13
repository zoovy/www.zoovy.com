#!/usr/bin/perl

use strict;
use CGI;

use lib "/httpd/modules"; 
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require ZSHIP;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my @MSGS = ();

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup/index.cgi','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping/index.cgi','target'=>'_top', };


$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

my $VERB = $ZOOVY::cgiv->{'ACTION'};
if ($VERB eq '') { $VERB = $ZOOVY::cgiv->{'VERB'}; }


print STDERR Dumper($ZOOVY::cgiv);

if ($FLAGS !~ /,SHIP,/) {
	$GTOOLS::TAG{'<!-- ADVANCED_BEGIN -->'} = '<!--';
	$GTOOLS::TAG{'<!-- ADVANCED_END -->'} = '-->';
	}

if (defined($ZOOVY::cgiv->{'MESSAGE'})) {
	push @MSGS, "INFO|+$ZOOVY::cgiv->{'MESSAGE'}";
	}


#if ($FLAGS =~ /,PKG=STAFF,/) {
#	## hide freight center for non-staff accounts.
#	$GTOOLS::TAG{'<!-- FREIGHTCENTER -->'} = "<!--";
#	$GTOOLS::TAG{'<!-- FREIGHTCENTER -->'} = "-->";
#	}


use ZSHIP::UPSAPI;
$GTOOLS::TAG{'<!-- UPS_DISCLAIMER -->'} = $ZSHIP::UPSAPI::DISCLAIMER;
my $template_file = "index.shtml";



my $fdxcfg = undef;
my $SUPPLIER_ID = $ZOOVY::cgiv->{'SUPPLIER_ID'};
require ZSHIP::FEDEXWS;
if ($VERB eq 'FEDEX-PRT-INIT') {
	## do we need to setup a new fedex account?
	## note: rulebuilder.cgi uses this as it's exit link
	($fdxcfg) = ZSHIP::FEDEXWS::load_webdb_fedexws_cfg($USERNAME,$PRT,$webdbref);
	if (($fdxcfg->{'meter'} == 0) || ($fdxcfg->{'account'} == 0)) {
		$VERB = 'FEDEX-PRT-REGISTER'; 
		}
	else {
		$VERB = 'FEDEX-CONFIG';
		}
	}
elsif ($VERB =~ /^FEDEX-PRT/) {
	($fdxcfg) = ZSHIP::FEDEXWS::load_webdb_fedexws_cfg($USERNAME,$PRT,$webdbref);	
	}
elsif ($VERB =~ /^FEDEX-SUPPLIER/) {
	if ($ZOOVY::cgiv->{'SRC'} =~ /^(.*?)\/SUPPLIER\/(.*?)$/) { $SUPPLIER_ID = $2; }
	($fdxcfg) = ZSHIP::FEDEXWS::load_supplier_fedexws_cfg($USERNAME,$SUPPLIER_ID,$webdbref);	
	}
elsif ($VERB =~ /^FEDEX/) {
	if ($ZOOVY::cgiv->{'SRC'} =~ /^(.*?)\/WEBDB\/(.*?)$/) { 
		($fdxcfg) = ZSHIP::FEDEXWS::load_webdb_fedexws_cfg($USERNAME,$PRT,$webdbref);
		}
	elsif ($ZOOVY::cgiv->{'SRC'} =~ /^(.*?)\/SUPPLIER\/(.*?)$/) { 
		$SUPPLIER_ID = $2; 
		($fdxcfg) = ZSHIP::FEDEXWS::load_supplier_fedexws_cfg($USERNAME,$SUPPLIER_ID,$webdbref);	
		}	
	}

print STDERR "VERB: $VERB\n";


if (($VERB eq 'FEDEX-PRT-REGISTER-SAVE') || ($VERB eq 'FEDEX-SUPPLIER-REGISTER-SAVE')) {

	$fdxcfg->{'account'} = $ZOOVY::cgiv->{'ACCOUNT'};
	if ($fdxcfg->{'account'} eq '') { push @MSGS, "ERROR|Account # is required"; }

	$fdxcfg->{'register.streetlines'} = $ZOOVY::cgiv->{'ADDRESS1'}.' '.$ZOOVY::cgiv->{'ADDRESS2'};
	$fdxcfg->{'register.city'} = $ZOOVY::cgiv->{'CITY'};
	if ($fdxcfg->{'register.city'} eq '') { push @MSGS, "ERROR|City is required"; }
	$fdxcfg->{'register.state'} = $ZOOVY::cgiv->{'STATE'};
	if ($fdxcfg->{'register.state'} eq '') { push @MSGS, "ERROR|State is required"; }
	$fdxcfg->{'register.zip'} = $ZOOVY::cgiv->{'ZIP'};
	if ($fdxcfg->{'register.zip'} eq '') { push @MSGS, "ERROR|Zip is required"; }
	$fdxcfg->{'register.country'} = $ZOOVY::cgiv->{'COUNTRY'};
	if ($fdxcfg->{'register.country'} eq '') { push @MSGS, "ERROR|Country is required"; }

	$fdxcfg->{'register.firstname'} = $ZOOVY::cgiv->{'FIRSTNAME'};
	if ($fdxcfg->{'register.firstname'} eq '') { push @MSGS, "ERROR|Firstname is required"; }
	$fdxcfg->{'register.lastname'} = $ZOOVY::cgiv->{'LASTNAME'};
	if ($fdxcfg->{'register.firstname'} eq '') { push @MSGS, "ERROR|Lastname is required"; }
	$fdxcfg->{'register.company'} = $ZOOVY::cgiv->{'COMPANY'};
	if ($fdxcfg->{'register.company'} eq '') { push @MSGS, "ERROR|Company is required"; }
	$fdxcfg->{'register.phone'} = $ZOOVY::cgiv->{'PHONE'};
	if ($fdxcfg->{'register.phone'} eq '') { push @MSGS, "ERROR|Phone is required"; }
	$fdxcfg->{'register.email'} = $ZOOVY::cgiv->{'EMAIL'};
	if ($fdxcfg->{'register.email'} eq '') { push @MSGS, "ERROR|Email is required"; }

	$fdxcfg->{'origin.country'} = $fdxcfg->{'register.country'};
	$fdxcfg->{'origin.state'} = $fdxcfg->{'register.state'};
	$fdxcfg->{'origin.zip'} = $fdxcfg->{'register.zip'};

	$VERB =~ s/\-SAVE$//;	# strip off the -SAVE so we return to the sender (if we got an error)
	if (scalar(@MSGS)==0) {
		require ZSHIP::FEDEXWS;
		delete $fdxcfg->{'registration.key'};
		delete $fdxcfg->{'registration.password'};
		$fdxcfg->{'registration.created'} = 0;
		$fdxcfg->{'meter'} = 0;
		($fdxcfg) = &ZSHIP::FEDEXWS::register($USERNAME,$fdxcfg,\@MSGS);
		# push @MSGS, "SUCCESS|".Dumper($fdxcfg);
		if ($fdxcfg->{'registration.created'}>0) { 
			&ZSHIP::FEDEXWS::subscriptionRequest($USERNAME,$fdxcfg,\@MSGS); 
			}
		# print STDERR Dumper($fdxcfg);
		if ($fdxcfg->{'meter'}==0) {
			push @MSGS, "ERROR|Meter was not set following subscriptionRequest";
			}
		elsif ($VERB eq 'FEDEX-PRT-REGISTER') { 
			$VERB = 'FEDEX-CONFIG'; 
			push @MSGS, "SUCCESS|Created meter #$fdxcfg->{'meter'}"; 
			&ZSHIP::FEDEXWS::save_webdb_fedexws_cfg($USERNAME,$PRT,$fdxcfg);
			}
		elsif ($VERB eq 'FEDEX-SUPPLIER-REGISTER') { 
			$VERB = 'FEDEX-SUPPLIER-DONE'; 
			push @MSGS, "SUCCESS|Created Meter for Supplier:$SUPPLIER_ID (meter: #$fdxcfg->{'meter'})"; 
			&ZSHIP::FEDEXWS::save_supplier_fedexws_cfg($USERNAME,$SUPPLIER_ID,$fdxcfg);
			}
		else {
			push @MSGS, "ERROR|Unknown VERB:$VERB\n";
			}
		}

	}


if ($VERB eq 'FEDEX-SUPPLIER-DONE') {
	$template_file = 'fedexws-meter-created.shtml';
	}

if (($VERB eq 'FEDEX-PRT-REGISTER') || ($VERB eq 'FEDEX-SUPPLIER-REGISTER')) {
	my $merchantref = &ZOOVY::fetchmerchant_ref($USERNAME);

	push @BC, { name=>'Fedex Registration' };
	if ($VERB eq 'FEDEX-PRT-REGISTER') {
		push @BC, { name=>'Partition: '.$PRT };
		}
	elsif ($VERB eq 'FEDEX-SUPPLIER-REGISTER') {
		push @BC, { name=>$fdxcfg->{'src'} };
		}
	
	$GTOOLS::TAG{'<!-- SRC -->'} = ($fdxcfg->{'src'})?$fdxcfg->{'src'}:"ERROR"; 
	$GTOOLS::TAG{'<!-- VERB -->'} = "$VERB-SAVE";
	$GTOOLS::TAG{'<!-- ACCOUNT -->'}   = (defined $ZOOVY::cgiv->{'ACCOUNT'})  ?$ZOOVY::cgiv->{'ACCOUNT'}  :$fdxcfg->{'account'};
	$GTOOLS::TAG{'<!-- FIRSTNAME -->'} = (defined $ZOOVY::cgiv->{'FIRSTNAME'})?$ZOOVY::cgiv->{'FIRSTNAME'}:$merchantref->{'zoovy:firstname'}.' '.$merchantref->{'zoovy:lastname'};
	$GTOOLS::TAG{'<!-- LASTNAME -->'} = (defined $ZOOVY::cgiv->{'LASTNAME'})?$ZOOVY::cgiv->{'LASTNAME'}:$merchantref->{'zoovy:lastname'};
	$GTOOLS::TAG{'<!-- COMPANY -->'} = (defined $ZOOVY::cgiv->{'COMPANY'})?$ZOOVY::cgiv->{'COMPANY'}:$merchantref->{'zoovy:company'};
	$GTOOLS::TAG{'<!-- ADDRESS1 -->'} = (defined $ZOOVY::cgiv->{'ADDRESS1'})?$ZOOVY::cgiv->{'ADDRESS1'}:$merchantref->{'zoovy:address1'};
	$GTOOLS::TAG{'<!-- ADDRESS2 -->'} = (defined $ZOOVY::cgiv->{'ADDRESS2'})?$ZOOVY::cgiv->{'ADDRESS2'}:$merchantref->{'zoovy:address2'};
	$GTOOLS::TAG{'<!-- CITY -->'} = (defined $ZOOVY::cgiv->{'CITY'})?$ZOOVY::cgiv->{'CITY'}:$merchantref->{'zoovy:city'};
	$GTOOLS::TAG{'<!-- STATE -->'} = (defined $ZOOVY::cgiv->{'STATE'})?$ZOOVY::cgiv->{'STATE'}:$merchantref->{'zoovy:state'};
	$GTOOLS::TAG{'<!-- ZIP -->'} = (defined $ZOOVY::cgiv->{'ZIP'})?$ZOOVY::cgiv->{'ZIP'}:$merchantref->{'zoovy:zip'};
	$GTOOLS::TAG{'<!-- COUNTRY -->'} = (defined $ZOOVY::cgiv->{'COUNTRY'})?$ZOOVY::cgiv->{'COUNTRY'}:"US";
	$GTOOLS::TAG{'<!-- PHONE -->'} = (defined $ZOOVY::cgiv->{'PHONE'})?$ZOOVY::cgiv->{'PHONE'}:$merchantref->{'zoovy:phone'};
	$GTOOLS::TAG{'<!-- EMAIL -->'} = (defined $ZOOVY::cgiv->{'EMAIL'})?$ZOOVY::cgiv->{'EMAIL'}:$merchantref->{'zoovy:email'};
	$GTOOLS::TAG{'<!-- FAX -->'} = (defined $ZOOVY::cgiv->{'FAX'})?$ZOOVY::cgiv->{'FAX'}:$merchantref->{'zoovy:facsimile'};
	$template_file = 'fedexws-register.shtml';
	}


if ($VERB eq 'FEDEX-CONFIG-SAVE') {
	if (defined $ZOOVY::cgiv->{'PRIMARY_SHIPPER'}) {
		$webdbref->{'primary_shipper'} = 'FEDEX';
		}
	$fdxcfg->{'rates'} = $ZOOVY::cgiv->{'rates'};
	$fdxcfg->{'enabled'} = 0;
	if ($ZOOVY::cgiv->{'dom'}) { $fdxcfg->{'enabled'} |= 1; }
	if ($ZOOVY::cgiv->{'int'}) { $fdxcfg->{'enabled'} |= 2; }
	$fdxcfg->{'dom.nextearly'} = ($ZOOVY::cgiv->{'dom_nextearly'})?1:0;
	$fdxcfg->{'dom.nextnoon'} = ($ZOOVY::cgiv->{'dom_nextnoon'})?1:0;
	$fdxcfg->{'dom.nextday'} = ($ZOOVY::cgiv->{'dom_nextday'})?1:0;
	$fdxcfg->{'dom.2day'} = ($ZOOVY::cgiv->{'dom_2day'})?1:0;
	$fdxcfg->{'dom.3day'} = ($ZOOVY::cgiv->{'dom_3day'})?1:0;
	$fdxcfg->{'dom.ground'} = ($ZOOVY::cgiv->{'dom_ground'})?1:0;
	$fdxcfg->{'dom.home'} = ($ZOOVY::cgiv->{'dom_home'})?1:0;
	$fdxcfg->{'dom.home_eve'} = ($ZOOVY::cgiv->{'dom_home_eve'})?1:0;
	$fdxcfg->{'int.nextearly'} = ($ZOOVY::cgiv->{'int_nextearly'})?1:0;
	$fdxcfg->{'int.nextnoon'} = ($ZOOVY::cgiv->{'int_nextnoon'})?1:0;
	$fdxcfg->{'int.2day'} = ($ZOOVY::cgiv->{'int_2day'})?1:0;
	$fdxcfg->{'int.ground'} = ($ZOOVY::cgiv->{'int_ground'})?1:0;
	if ($fdxcfg->{'src'} =~ /^(.*?)\/WEBDB\/(.*?)$/) { 
		&ZSHIP::FEDEXWS::save_webdb_fedexws_cfg($USERNAME,$PRT,$fdxcfg,$webdbref);
		push @MSGS, "SUCCESS|Saved website $fdxcfg->{'src'} Settings";
		}
	elsif ($fdxcfg->{'src'} =~ /^(.*?)\/SUPPLIER\/(.*?)$/) { 
		my $SUPPLIER_ID = $2; 
		&ZSHIP::FEDEXWS::save_supplier_fedexws_cfg($USERNAME,$SUPPLIER_ID,$fdxcfg);	
		push @MSGS, "SUCCESS|Saved Supplier $fdxcfg->{'src'} Settings";
		}	
	else {
		push @MSGS, "ERROR|Unknown src: $fdxcfg->{'src'}";
		}
	$VERB = 'FEDEX-CONFIG';
	}



if ($VERB eq 'FEDEX-CONFIG') {
	push @BC, { name=>'Fedex Configuration' };

	# $GTOOLS::TAG{'<!-- DEBUG -->'} = Dumper($fdxcfg);

	$GTOOLS::TAG{'<!-- SRC -->'} = ($fdxcfg->{'src'})?$fdxcfg->{'src'}:"ERROR"; 
	$GTOOLS::TAG{'<!-- METER -->'} = $fdxcfg->{'meter'};
	$GTOOLS::TAG{'<!-- ORIGIN_ZIP -->'} = $fdxcfg->{'origin.zip'};
	$GTOOLS::TAG{'<!-- ORIGIN_STATE -->'} = $fdxcfg->{'origin.state'};
	$GTOOLS::TAG{'<!-- ORIGIN_COUNTRY -->'} = $fdxcfg->{'origin.country'};
	$GTOOLS::TAG{'<!-- PRIMARY_SHIPPER -->'} = ($webdbref->{'primary_shipper'} eq 'FEDEX')?'checked':'';
	$GTOOLS::TAG{'<!-- RATES_ACTUAL -->'} = (($fdxcfg->{'rates'} eq 'actual')?'checked':'');
	$GTOOLS::TAG{'<!-- RATES_RETAIL -->'} = (($fdxcfg->{'rates'} eq 'retail')?'checked':'');
	$GTOOLS::TAG{'<!-- DOM -->'} = (($fdxcfg->{'enabled'}&1)==1)?'checked':'';
	$GTOOLS::TAG{'<!-- INT -->'} = (($fdxcfg->{'enabled'}&2)==2)?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_NEXTEARLY -->'} = ($fdxcfg->{'dom.nextearly'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_NEXTNOON -->'} = ($fdxcfg->{'dom.nextnoon'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_NEXTDAY -->'} = ($fdxcfg->{'dom.nextday'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_2DAY -->'} = ($fdxcfg->{'dom.2day'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_3DAY -->'} = ($fdxcfg->{'dom.3day'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_GROUND -->'} = ($fdxcfg->{'dom.ground'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_HOME_EVE -->'} = ($fdxcfg->{'dom.home_eve'})?'checked':'';
	$GTOOLS::TAG{'<!-- DOM_HOME -->'} = ($fdxcfg->{'dom.home'})?'checked':'';

	$GTOOLS::TAG{'<!-- INT_NEXTEARLY -->'} = ($fdxcfg->{'int.nextearly'})?'checked':'';
	$GTOOLS::TAG{'<!-- INT_NEXTNOON -->'} = ($fdxcfg->{'int.nextnoon'})?'checked':'';
	$GTOOLS::TAG{'<!-- INT_2DAY -->'} = ($fdxcfg->{'int.2day'})?'checked':'';
	$GTOOLS::TAG{'<!-- INT_GROUND -->'} = ($fdxcfg->{'int.ground'})?'checked':'';

	$GTOOLS::TAG{'<!-- METER_LINK -->'} = qq~
		<input class='button' type='button' onClick="navigateTo('/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-REGISTER');" value='New Meter'>
		~;

	$template_file = 'fedexws-config.shtml';
	}



#if ($VERB eq "SIMPLE-SAVE") {
#	push @MSGS, "SUCESS|Changes saved";
#
##	if (uc($ZOOVY::cgiv->{'promotion_discount'}) eq "ON") { $webdb->{"promotion_discount"} = 1; } else { $webdb->{"promotion_discount"} = 0; }
#   if (uc($ZOOVY::cgiv->{'promotion_freeshipping'}) eq "ON") { $webdb->{"promotion_freeshipping"} = 1; } else { $webdb->{"promotion_freeshipping"} = 0; }
##	if (uc($ZOOVY::cgiv->{'promotion_external'}) eq "ON") { $webdb->{"promotion_external"} = 1; } else { $webdb->{"promotion_external"} = 0; }
#
#   $webdb->{"promotion_freeshipping_amount"} = $ZOOVY::cgiv->{'promotion_freeshipping_amount'}; 
#	$webdb->{"promotion_freeshipping_amount"} =~ s/[^0-9\.]+//igs;
##	$webdb->{"promotion_discount_amount"} = $ZOOVY::cgiv->{'promotion_discount_amount'};
##	$webdb->{"promotion_discount_amount"} =~ s/[^0-9\.\%]+//igs;
##	$webdb->{"promotion_discount_after"} = $ZOOVY::cgiv->{'promotion_discount_after'};
##	$webdb->{"promotion_discount_after"} =~ s/[^0-9\.]+//igs;
#	$LU->log("SETUP.PROMO","Update Simple Promotions","SAVE");
#   &ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
#	$VERB = 'SIMPLE';
#   }

#if ($VERB eq 'SIMPLE') {
#	if ($webdb->{"promotion_freeshipping"}>0)
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_FREESHIPPING -->"} = " CHECKED "; }
#	else 
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_FREESHIPPING -->"}  = ""; }
#
#	if ($webdb->{"promotion_discount"}>0)
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_DISCOUNT -->"} = " CHECKED "; }
#	else 
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_DISCOUNT -->"}  = ""; }
#
#	if ($webdb->{"promotion_external"}>0)
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_EXTERNAL -->"} = " CHECKED "; }
#	else 
#		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_EXTERNAL -->"}  = ""; }
#
#
#	if ( ($webdb->{'promotion_freeshipping'} || $webdb->{'promotion_discount'}) 
#			&& $webdb->{'promotion_advanced'}) {
#		push @MSGS, "ERROR|You cannot have both simple promotions and advanced (uber) promotions enabled at the same time.";
#		}
#
#	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_FREESHIPPING_AMOUNT -->"} = " VALUE=\"".$webdb->{"promotion_freeshipping_amount"}."\" ";
#	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_DISCOUNT_AMOUNT -->"} = " VALUE=\"".$webdb->{"promotion_discount_amount"}."\" ";
#	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_DISCOUNT_AFTER -->"} = " VALUE=\"".$webdb->{"promotion_discount_after"}."\" ";
#	$template_file = 'index-simple.shtml';
#	}





if ($VERB eq 'SAVE') {			
	my $errors = 0;

	$webdbref->{"chkout_deny_ship_po"} = ($ZOOVY::cgiv->{'chkout_deny_ship_po'})?1:0;
	$webdbref->{'ebay_merge_shipping'} = ($ZOOVY::cgiv->{'ebay_merge_shipping'})?1:0;
  
	## DESTINATIONS
	$webdbref->{'ship_int_risk'} = $ZOOVY::cgiv->{'ship_int_risk'};
	
	## ORIGIN ZIP	
	$ZOOVY::cgiv->{'ship_origin_zip'} =~ s/[^\d]+//g;
	my ($state) = &ZSHIP::zip_state($ZOOVY::cgiv->{'ship_origin_zip'});
	if ($state eq '') {
		$errors++;
		push @MSGS, "ERROR|ZIP code does not appear to be valid!";
		}
	else { 
		$webdbref->{'ship_origin_zip'} = $ZOOVY::cgiv->{'ship_origin_zip'};
		}
	
	## FULFILLMENT LATENCY
	$ZOOVY::cgiv->{'ship_latency'} =~ s/\D//g;
	if ($ZOOVY::cgiv->{'ship_latency'} ne '') {
		if ($ZOOVY::cgiv->{'ship_latency'} !~ /\d/) {
			$errors++;
			push @MSGS, "ERROR|Default Fulfillment latency is invalid!";
      	}
   	else { 
			$webdbref->{'ship_latency'} = $ZOOVY::cgiv->{'ship_latency'};
			}
		}

	## FULFILLMENT CUTOFF
	if ($ZOOVY::cgiv->{'ship_cutoff'} ne '') {
		if ($ZOOVY::cgiv->{'ship_cutoff'} !~ /\d\d:\d\d/) {
			$errors++;
			push @MSGS, "ERROR|Fulfillment cut off time is invalid! (Ex. 14:00 or 08:00)";
			}
		else { 
			$webdbref->{'ship_cutoff'} =  $ZOOVY::cgiv->{'ship_cutoff'};
			}
		}

	## RESULTS
	if ($errors == 0) { 
		push @MSGS, "SUCCESS|Changes saved";
		}

	$LU->log("SETUP.SHIPPING","Saved Shipping Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = '';
	}



if ($VERB eq 'BANNED-NUKE') {
	my $id = int($ZOOVY::cgiv->{'ID'});
	my $i = 0;
	my $c = '';
	my $removedline = '';
	foreach my $line (split(/[\n\r]+/,$webdbref->{'banned'})) {
		if ($i == $id) {
			$removedline = $line;
			}
		else {
			$c .= $line."\n";
			}
		$i++;
		}
	$webdbref->{'banned'} = $c;
	$LU->log("SETUP.SHIPPING.BANNED","Removed banned entry #$id","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);		
	$VERB = 'BANNED';
	}

##
##
##
if ($VERB eq 'BANNED-SAVE') {
	if ($ZOOVY::cgiv->{'type'} eq '') {
		}
	elsif ($ZOOVY::cgiv->{'matches'} eq '') {
		}
	else {
		my $type = uc($ZOOVY::cgiv->{'type'});
		my $matches = uc($ZOOVY::cgiv->{'matches'});
		$matches =~ s/^[\s]+//g;	# strip leading space
		$matches =~ s/[\s]+$//g;	# strip trailing space
	
		my $line = $type.'|'.$matches."|".time()."\n";
		$webdbref->{'banned'} .= $line;
		$LU->log("SETUP.SHIPPING.BANNED","Add banned entry type=$ZOOVY::cgiv->{'type'} matches=$ZOOVY::cgiv->{'matches'} Settings","SAVE");	
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);	
		}
	$VERB = 'BANNED';
	}

##
##
##
if ($VERB eq 'BANNED') {
	my $c = '';
	my $i = 0;
	foreach my $line (split(/[\n\r]+/,$webdbref->{'banned'})) {
		my ($type,$match,$created) = split(/\|/,$line);
		$c .= "<tr>";
		$c .= "<td><a href='/biz/setup/shipping/index.cgi?ACTION=BANNED-NUKE&ID=$i'>[Del]</a></td>";
		$c .= "<td>$type</td>";
		$c .= "<td>$match</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($created,2)."</td>";
		$c .= "</tr>";	
		$i++;
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=4><i>No entries</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- BANNED_LIST -->'} = $c;
	$template_file = 'banned.shtml';
	}


if ($VERB eq 'FILTER-ADDBLOCK') {
	my ($info) = &ZSHIP::resolve_country('ISOX'=>$ZOOVY::cgiv->{'BLOCK'});
	$webdbref->{'ship_blacklist'} = $webdbref->{'ship_blacklist'}.(($webdbref->{'ship_blacklist'} ne '')?',':'').$info->{'ISOX'};
	$LU->log("SETUP.SHIPPING.BLACKLIST","Updated Shipping Blacklist Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = 'COUNTRIES';
	}

if ($VERB eq 'FILTER-DELBLOCK') {
	$webdbref->{'ship_blacklist'} = ','.$webdbref->{'ship_blacklist'}.',';
	my $qtISO = quotemeta($ZOOVY::cgiv->{'ISOX'});
	$webdbref->{'ship_blacklist'} =~ s/$qtISO//gs;
	$webdbref->{'ship_blacklist'} =~ s/^,//gs;
	$webdbref->{'ship_blacklist'} =~ s/,$//gs;
	$webdbref->{'ship_blacklist'} =~ s/[,]+/,/gs;
	$LU->log("SETUP.SHIPPING.BLACKLIST","Deleted from Blacklist Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = 'COUNTRIES';
	}


if ($VERB eq 'COUNTRIES') {
	$template_file = 'index-filters.shtml';	


	if ($FLAGS =~ /,SHIP,/) {
		my $c = '';
		foreach my $isox (split(/,/,$webdbref->{'ship_blacklist'})) {
			next if ($isox eq '');
			my ($info) = &ZSHIP::resolve_country(ISOX=>$isox);
			$c .= "<tr><td><a href='/biz/setup/shipping/index.cgi?ACTION=FILTER-DELBLOCK&ISOX=$isox'>[Del]</a></td><td>$info->{'Z'} ($isox)</td></tr>";
			}
		$GTOOLS::TAG{'<!-- BLOCK_LIST -->'} = $c;
	
		my $DSTS = &ZSHIP::available_destinations(undef,$webdbref);
		$c = '';
		foreach my $ref (@{$DSTS}) {
			$c .= qq~<option value="$ref->{'ISOX'}">$ref->{'Z'} ($ref->{'ISOX'})</option>\n~;
			}
		$GTOOLS::TAG{'<!-- BLOCK -->'} = $c;
		}
	else {
		$GTOOLS::TAG{'<!-- BLOCK -->'} = '<option value="">Not Available</option>';
		}


	}


if (($VERB eq 'COUNTRIES') || ($VERB eq 'BANNED')) {
	if ($webdbref->{'paypal_email'}) {
		push @MSGS, "WARN|Paypal Express checkout, Google Checkout, and Checkout by Amazon use the respective fraud filters for each payment type, purchasers will be able to place orders that avoid this block list (refer to each payment types individual fraud policies.)";
		}
	}



if ($VERB eq '') {


	if ($webdbref->{'ship_origin_zip'} eq '') {
		push @MSGS, "WARN|ship_origin_zip is not set - many types of zone based shipping will not work";
		}

#	if ($webdbref->{'promotion_freeshipping_amount'}>0) {
#		$GTOOLS::TAG{'<!-- FREE_SHIPPING_PROMO_WARN -->'} = 
#			sprintf(qq~
#<div class="warning">
#NOTE: Simple Promotion will give FREE SHIPPING on orders over %.2f
#<a href="/biz/setup/promotions/index.cgi?VERB=SIMPLE">[Configure]</a>
#</div>
#~,$webdbref->{'promotion_freeshipping_amount'});
#		}


	if ($webdbref->{'global_enable'}) {
		$GTOOLS::TAG{'<!-- GLOBALTUNE_LEGACY -->'} = qq~
		<Tr>
  	 <td valign="middle" align="center" ><font size='2' face="Arial"><a href='global.cgi'><center><img src='images/globaltuning.gif' border=0></a></td>
  	 <td valign="middle" ><font size='2' face="Arial"> -- </td>M
  	 <td valign="middle" ><font size='2' face="Arial"> -- </td>M
		<td>Deprecated</td>
		</tr>
	~;
		}


	$GTOOLS::TAG{'<!-- CHKOUT_DENY_SHIP_PO_CHECKED -->'} = ($webdbref->{'chkout_deny_ship_po'})?'checked':'';
	$GTOOLS::TAG{'<!-- EBAY_MERGE_SHIPPING_CHECKED -->'} = ($webdbref->{'ebay_merge_shipping'})?'checked':'';


	## UNIVERSAL FLAT RATE METHODS (universal)
	# print STDERR "USERNAME: $USERNAME PRT: $PRT\n";
	my $methods = &ZWEBSITE::ship_methods($USERNAME,prt=>$PRT);
	my $c = '';
	my $r = '';

	foreach my $region ('US','CA','INT') {

		## now go through each method (so we do this 3 times, or once per region)
		foreach my $m (@{$methods}) {
			next if ($m->{'region'} ne $region);	## this allows us to do grouping!

			$r = ($r eq 'r0')?'r1':'r0';
			if ($m->{'active'}==0) { 
				$r = 'rs'; 
				$m->{'name'} = "NOT ACTIVE: ".$m->{'name'};
				}

			my $has_rules = '';
			use Data::Dumper;
			$has_rules = scalar(&ZSHIP::RULES::fetch_rules($USERNAME,$PRT,"SHIP-$m->{'id'}"));
			# $has_rules = Dumper($m->{'id'},&ZSHIP::RULES::fetch_rules($USERNAME,$PRT,"SHIP-$m->{'id'}"));
			if ($m->{'rules'}==0) { $has_rules = 'OFF'; }
			# $has_rules = 1;

			my $summary = '';

			if ($m->{'handler'} eq 'FIXED') {
				$summary = '';
				}
			elsif ($m->{'handler'} eq 'WEIGHT') {
				my $hashref = &ZTOOLKIT::parseparams($m->{'data'});
				my $max = '';
				foreach my $k (sort { $a <=> $b; } keys %{$hashref}) { $max = $k };
				$m->{'min_wt'} = &ZSHIP::smart_weight($m->{'min_wt'});

				$summary = 'Range: '.$m->{'min_wt'}.'oz to '.$max.'oz';
				}

			$c .= qq~
<tr class="$r">
	<td valign=top>
<button class="button" onClick="navigateTo('/biz/setup/shipping/universal.cgi?VERB=EDIT&ID=$m->{'id'}'); return false;">Edit</button></td>
	<td valign=top>~.$m->{'handler'}.qq~</td>
	<td valign=top>~.$m->{'region'}.qq~</td>
	<td valign=top>~.&ZOOVY::incode($m->{'name'}).qq~</td>
	<td valign=top>~.$has_rules.qq~</td>
	<td valign=top>~.$summary.qq~</td>
</tr>
~;
			}
		}

	if (scalar(@{$methods})==0) {
		$c = '<tr><td colspan=3><i>No flex rating methods have been defined.</td></tr>';
		}
	else {
		$c = q~
<tr class="zoovysub1header">
	<td>&nbsp;</td>
	<td>TYPE</td>
	<td>REGION</td>
	<td>NAME</td>
	<td>RULES</td>
	<td>SUMMARY</td>
</tr>
~.$c;
		}
	$GTOOLS::TAG{'<!-- FLEX_RATES -->'} = $c;

#	$GTOOLS::TAG{'<!-- DISPLAY_EXTERNAL -->'} =
#		($webdbref->{'ship_external_url'} ne '')? $webdbref->{'ship_external_url'} : 'Disabled';

 	$GTOOLS::TAG{"<!-- SHIP_INT_NONE -->"} ='';
	$GTOOLS::TAG{"<!-- SHIP_INT_ALL51 -->"} ='';
	$GTOOLS::TAG{"<!-- SHIP_INT_SOME -->"} ='';
	$GTOOLS::TAG{"<!-- SHIP_INT_FULL -->"} ='';
	my $SHIP_INT_RISK = uc($webdbref->{"ship_int_risk"});
	$GTOOLS::TAG{'<!-- SHIP_ORIGIN_ZIP -->'} = $webdbref->{"ship_origin_zip"};
	$GTOOLS::TAG{'<!-- SHIP_LATENCY -->'} = $webdbref->{"ship_latency"};
	$GTOOLS::TAG{'<!-- SHIP_CUTOFF -->'} = $webdbref->{"ship_cutoff"};

	# this assumes that the $SHIP_INT_RISK variable is represented aboe
	$GTOOLS::TAG{'<!-- SHIP_INT_'.$SHIP_INT_RISK.' -->'} = ' CHECKED ';

	##
	## Begin index.shtml setup of international settings
	##
	my ($fdxcfg) = ZSHIP::FEDEXWS::load_webdb_fedexws_cfg($USERNAME,$PRT,$webdbref);	
	$GTOOLS::TAG{"<!-- DISPLAY_FEDEXAPI_DOM -->"}=(($fdxcfg->{'enabled'}&1)==1)?'Enabled':'Disabled';
	$GTOOLS::TAG{"<!-- DISPLAY_FEDEXAPI_INT -->"}=(($fdxcfg->{'enabled'}&2)==2)?'Enabled':'Disabled';
	$GTOOLS::TAG{"<!-- DISPLAY_USPS_DOM -->"}=($webdbref->{"usps_dom"}>0)         ?'Enabled':'Disabled';
	$GTOOLS::TAG{"<!-- DISPLAY_USPS_INT -->"} = ($webdbref->{"usps_int"}>0)?'Enabled':'Disabled';
	$GTOOLS::TAG{"<!-- DISPLAY_UPSAPI_DOM -->"}=($webdbref->{"upsapi_dom"}>0)        ?'Enabled':'Disabled';
	$GTOOLS::TAG{"<!-- DISPLAY_UPSAPI_INT -->"} = ($webdbref->{"upsapi_int"}>0)?'Enabled':'Disabled';
#	$GTOOLS::TAG{'<!-- DISPLAY_FREIGHTCENTER_DOM -->'}=($webdbref->{"freightcenter_enable"}>0)?'Enabled':'Disabled';

	if ($webdbref->{"ship_int_risk"} eq "none") {
		$GTOOLS::TAG{"<!-- DISPLAY_UPSAPI_INT -->"} = "Will Not Ship";
		$GTOOLS::TAG{"<!-- DISPLAY_USPS_INT -->"} = "Will Not Ship";
		$GTOOLS::TAG{"<!-- DISPLAY_FEDEX_INT -->"} = "Will Not Ship";
		}
	elsif ($FLAGS !~ /,BASIC,/) {
		$GTOOLS::TAG{"<!-- DISPLAY_UPSAPI_INT -->"} = "Not Available";
		$GTOOLS::TAG{"<!-- DISPLAY_USPS_INT -->"} = "Not Available";
		$GTOOLS::TAG{"<!-- DISPLAY_FEDEX_INT -->"} = "Not Available";
		} 
	}


my @TABS = ();
push @TABS, { name=>'General', selected=>($VERB eq '')?1:0, link=>'/biz/setup/shipping/index.cgi?ACTION=' };
push @TABS, { name=>'Countries', selected=>($VERB eq 'COUNTRIES')?1:0, link=>'/biz/setup/shipping/index.cgi?ACTION=COUNTRIES' };
push @TABS, { name=>'Block-List', selected=>($VERB eq 'BANNED')?1:0, link=>'/biz/setup/shipping/index.cgi?ACTION=BANNED' };
push @TABS, { name=>'Debugger', link=>'debug.cgi' };

&GTOOLS::output('*LU'=>$LU,
	help=>'#50620',
	title=>'Setup: Shipping',
	header=>1, 
	tabs=>\@TABS,
	file=>$template_file,
	'jquery'=>1,
	bc=>\@BC,
	msgs=>\@MSGS,
	todo=>1);

exit;

