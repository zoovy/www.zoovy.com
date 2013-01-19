#!/usr/bin/perl

use strict;
use lib "/httpd/modules"; 
require LUSER;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require CART2;
require ZACCOUNT;
require DOMAIN;
require DOMAIN::TOOLS;


my ($LU) = LUSER->authenticate(scalar=>0,flags=>'_S&8');
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
my @MSGS = ();

my $template_file = '';

my $gref = &ZWEBSITE::fetch_globalref($USERNAME);

my ($VERB) = uc($ZOOVY::cgiv->{'VERB'});
if ($VERB eq '') { $VERB = 'GENERAL'; }


##
##
if ($VERB eq 'GENERAL-SAVE') {
	if ($ZOOVY::cgiv->{'order_num'}+0 != $ZOOVY::cgiv->{'hidden_order_num'}+0) {
		&CART2::reset_order_id($USERNAME,$ZOOVY::cgiv->{'order_num'}+0);
		}	
	push @MSGS, "SUCCESS|Successfully Saved Changes";

	$gref->{'wms'} = int($ZOOVY::cgiv->{'wms'});
	$gref->{'erp'} = int($ZOOVY::cgiv->{'erp'});
	$LU->log('SETUP.GLOBAL','Saved Global/Inventory settings','SAVE');

	# &ZWEBSITE::save_website_dbref($USERNAME,$gref);
	&ZWEBSITE::save_globalref($USERNAME,$gref);
	$VERB = 'GENERAL';
	}

if ($VERB eq 'GENERAL') {
	my $order_num = &CART2::next_id($USERNAME,1);
	(undef,undef,$order_num) = split(/-/,$order_num,3);
	$order_num -= 1;

	$GTOOLS::TAG{'<!-- WMS_0_CHK -->'} = ($gref->{'wms'}==0)?'checked':'';
	$GTOOLS::TAG{'<!-- WMS_1_CHK -->'} = ($gref->{'wms'}==1)?'checked':'';

	$GTOOLS::TAG{'<!-- ERP_0_CHK -->'} = ($gref->{'erp'}==0)?'checked':'';
	$GTOOLS::TAG{'<!-- ERP_1_CHK -->'} = ($gref->{'erp'}==1)?'checked':'';

	$GTOOLS::TAG{"<!-- order_num -->"} = $order_num;
	$GTOOLS::TAG{"<!-- hidden_order_num -->"} = $order_num;

	$template_file = 'general.shtml';
	}




if ($VERB eq 'WMS-SAVE') {

	if ($gref->{'wms'} == 1) {	
		$LU->log('SETUP.GLOBAL.WMS','Saved Global/WMS settings','SAVE');

		# &ZWEBSITE::save_website_dbref($USERNAME,$gref);
		&ZWEBSITE::save_globalref($USERNAME,$gref);
		}
	else {
		push @MSGS, "ERROR|WMS settings could not be saved because WMS is not enabled";
		}
	}


if ($VERB eq 'WMS') {	
	if ($gref->{'wms'}==0) {
		push @MSGS, "WARN|WMS is not currently enabled.";
		}
	$template_file = 'wms.shtml';
	}




if ($VERB eq 'ERP-SAVE') {

	if ($gref->{'erp'} == 1) {	
		$LU->log('SETUP.GLOBAL.ERP','Saved Global/ERP settings','SAVE');
		&ZWEBSITE::save_globalref($USERNAME,$gref);
		}
	else {
		push @MSGS, "ERROR|ERP settings could not be saved because ERP is not enabled";
		}
	}


if ($VERB eq 'ERP') {	
	if ($gref->{'erp'}==0) {
		push @MSGS, "WARN|ERP is not currently enabled.";
		}
	$template_file = 'erp.shtml';
	}




##
##
##
if ($VERB eq 'PARTITIONS-CREATE') {
	if ($LU->is_zoovy()) {}
	elsif ($FLAGS =~ /,PRT,/) {  }
	else {
		push @MSGS, "ERROR|Sorry $LUSERNAME, Please contact Zoovy Implementation Assistance prior to using this tool.";
		$LU->log('SETUP.PARTITIONS',"Access was denied","DENY");
		$VERB = 'PARTITIONS';
		}
	}


if ($VERB eq 'PARTITIONS-CREATE') {

	my ($globalref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my $i = scalar(@{$globalref->{'@partitions'}});
	my %prt = ();
	$prt{'name'} = $ZOOVY::cgiv->{'PNAME'};
	$prt{'profile'} = $ZOOVY::cgiv->{'PROFILE'};
	$prt{'p_navcats'} = (defined $ZOOVY::cgiv->{'navcats'})?$i:0;
	# $prt{'p_customers'} = (defined $ZOOVY::cgiv->{'customers'})?$i:0;
	$prt{'p_customers'} = $i;
	$globalref->{'@partitions'}->[$i] = \%prt;
	
	push @MSGS, "SUCCESS|Created Partition $i";
	$LU->log("SETUP.PARTITION","Created partition \#$i $prt{'name'} profile=$prt{'profile'} $prt{'p_checkout'}|$prt{'p_messages'}|$prt{'p_customer'}","INFO");
	&ZWEBSITE::save_globalref($USERNAME,$globalref);

	&ZWEBSITE::prt_set_profile($USERNAME,$i,$ZOOVY::cgiv->{'PROFILE'});

	$VERB = 'PARTITIONS';
	}


if ($VERB eq 'PARTITIONS') {
	$template_file = 'partitions.shtml';
	
	my ($globalref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my $c = '';

	my $i = 0;
	my %USED = ();
	foreach my $prt ( @{$globalref->{'@partitions'}} ) {
		if (not defined $prt->{'p_navcats'}) { $prt->{'p_navcats'}=0; }
		if (not defined $prt->{'p_customers'}) { $prt->{'p_customers'}=$i; }
		$c .= "<tr><td>";
		if ($prt->{'profile'} eq '') { $prt->{'profile'} = 'DEFAULT'; }

		$c .= "<h3>PARTITION #$i</h3>";
		$c .= "<ul>";
		if ($prt->{'p_customers'}==$i) {
			$c .= "<li> PARTITION HAS FEDERATED CUSTOMER DATABASE";
			}
		else {
			$c .= "<li> PARTITION SHARES CUSTOMER DATABASE WITH PARTITION #$prt->{'p_customers'}";
			}

		if ($prt->{'p_navcats'}==$i) {
			$c .= "<li> PARTITION HAS FEDERATED NAVIGATION CATEGORIES";
			}
		else {
			$c .= "<li> PARTITION SHARES NAVIGATION WITH PARTITION #$prt->{'p_navcats'}";
			}

		$c .= "<li> ASSOCIATED PROFILE: $prt->{'profile'}<br>";
		## update the website dbref
		my ($dbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$i);

		my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$prt->{'profile'});
		$nsref->{'prt:id'} = $i;
		$c .= "<li> PROFILE $prt->{'profile'} MAPPED TO PARTITION: $nsref->{'prt:id'} (should be $i)";

		my @domains = DOMAIN::TOOLS::domains($USERNAME,PRT=>$i);
		foreach my $domainname (@domains) {
			my ($d) = DOMAIN->new($USERNAME,$domainname);
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$d->{'PROFILE'});
			# next if ($d->{'PRT'} == $i);
			my $ERR = '';
			$c .= "<li> FOUND DOMAIN: $domainname<br>
<font class='hint'>MAPPED TO PROFILE: $d->{'PROFILE'} / PARTITION: $d->{'PRT'} (should be $i)</font>";
			}
		$c .= "</ul>";

#		if ($prt->{'p_shipping'}) { $c .= " Shipping($prt->{'p_shipping'})"; }
#		if ($prt->{'p_checkout'}) { $c .= " Checkout($prt->{'p_checkout'})"; }
#		if ($prt->{'p_payment'}) { $c .= " Payment($prt->{'p_payment'})"; }
#		if ($prt->{'p_messages'}) { $c .= " Messages($prt->{'p_messages'})"; }
#		if ($prt->{'p_customer'}) { $c .= " Customer($prt->{'p_customer'})"; }
		$c .= qq~</td></tr>~;
		$i++;
		}

	if (1) {
		my $c = '';
		foreach my $p (@{&ZOOVY::fetchprofiles($USERNAME)}) {
			next if ($p eq 'DEFAULT');
			next if ($USED{$p});
			$c .= "<option value='$p'>$p</option>";
			}
		$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
		}
	
	$GTOOLS::TAG{'<!-- PARTITIONS -->'} = $c;
	}




if ($VERB eq "INVENTORY-SAVE") {

	$gref->{'inv_mode'} = 0;
	$gref->{'inv_configproduct'} = 0;
	$gref->{'inv_reserve'} = 0;
	$gref->{'inv_notify'} = 0;
	$gref->{'inv_police_checkout'} = 0; 
	$gref->{'inv_police'} = 0;
	$gref->{'inv_channel'} = 0;

	$gref->{'inv_reserve_action'} = 0;
	$gref->{'inv_rexceed_action'} = 0;
	$gref->{'inv_safety_action'} = 0;

	$gref->{'inv_notify'} = 0;
	$gref->{'inv_outofstock_action'} = 0;
	foreach my $i (1,2,4,8,16,32,64,128,256) {
		$gref->{'inv_notify'} |= (defined $ZOOVY::cgiv->{'inv_notify_'.$i})?$i:0;
		$gref->{'inv_outofstock_action'} |= (defined $ZOOVY::cgiv->{'inv_outofstock_action_'.$i})?$i:0;
		}

	if ($ZOOVY::cgiv->{'inv_mode'} == 0) { $ZOOVY::cgiv->{'inv_mode'} = 1; }


	if ($FLAGS =~ /,API2,/) {
		## don't run the rest of these cases (we'll use our own custom settings later)
		}
	elsif ($ZOOVY::cgiv->{'inv_mode'} == 1) {
		$gref->{'inv_mode'} = 1;
		$gref->{'inv_reserve'} = 1;
		}
	elsif (($ZOOVY::cgiv->{'inv_mode'}==3) || ($ZOOVY::cgiv->{'inv_mode'}==2)) { 
		$gref->{'inv_mode'} = int($ZOOVY::cgiv->{'inv_mode'});
		$gref->{'inv_reserve'} = 1;
		$gref->{'inv_police'} = 2;
		$gref->{'inv_police_checkout'} = 1;
		$gref->{'inv_channel'} = 4;
		$gref->{'inv_reserve_action'} = 0;
		$gref->{'inv_rexceed_action'} = 3;
		$gref->{'inv_outofstock_action'} |= 2;
		}

	if ($FLAGS =~ /,API2,/) {
		## BASIC INVENTORY
		## ADVANCED INVENTORY
		$gref->{'inv_mode'} = int($ZOOVY::cgiv->{'inv_mode'});
		if (defined $ZOOVY::cgiv->{'inv_configproduct'}) { $gref->{'inv_configproduct'} = 1; } else { $gref->{'inv_configproduct'} = 0; }
		if (defined $ZOOVY::cgiv->{'inv_reserve'}) { $gref->{'inv_reserve'} = 1; } else { $gref->{'inv_reserve'} = 0; }	
	
		$gref->{'inv_police_checkout'} = (defined $ZOOVY::cgiv->{'inv_police_checkout'})?1:0;
		$gref->{'inv_police'} = int($ZOOVY::cgiv->{'inv_police'}); 


		$gref->{'inv_channel'} = (defined  $ZOOVY::cgiv->{'inv_channel'})?1:0;	
		$gref->{'inv_reserve_action'} = 0;
		if (defined $ZOOVY::cgiv->{'reserve_remove'}) { $gref->{'inv_reserve_action'} += 1; }
		if (defined $ZOOVY::cgiv->{'reserve_revoke'}) { $gref->{'inv_reserve_action'} += 2; }

		$gref->{'inv_rexceed_action'} = 0;
		if (defined $ZOOVY::cgiv->{'rexceed_remove'}) { $gref->{'inv_rexceed_action'} += 1; }
		if (defined $ZOOVY::cgiv->{'rexceed_revoke'}) { $gref->{'inv_rexceed_action'} += 2; }

		$gref->{'inv_safety_action'} = 0;
		if (defined $ZOOVY::cgiv->{'safety_remove'}) { $gref->{'inv_safety_action'} += 1; }
		if (defined $ZOOVY::cgiv->{'safety_revoke'}) { $gref->{'inv_safety_action'} += 2; }
		my $safety =  $ZOOVY::cgiv->{'safety'};
		$safety =~ s/[^0-9]//g;
		if ($safety eq '') { $safety = 0; }
		$gref->{'inv_safety'} = $safety;
		}
	else {

		if (not $ZOOVY::cgiv->{'inv_website_remove'}) {
			$gref->{'inv_rexceed_action'} = 0;
			$gref->{'inv_outofstock_action'} = 0;
			}
		else {
			## turns on remove from website action.
			$gref->{'inv_rexceed_action'} |= 1;
			$gref->{'inv_outofstock_action'} |= 1;
			}
		}


	push @MSGS, "SUCCESS|Successfully Saved Changes";
	$LU->log('SETUP.GLOBAL','Saved Global/Inventory settings','SAVE');
	&ZWEBSITE::save_globalref($USERNAME,$gref);

	$VERB = 'INVENTORY';
	}



# handle general parameters.
if ($VERB eq 'INVENTORY') {

	$template_file = 'inventory.shtml';

	## INVENTORY!
	my $mode = $gref->{'inv_mode'};
	if (!defined $mode) { $mode = 0; }
	$mode =~ s/[^0-9]//g;
	
	$GTOOLS::TAG{'<!-- INV_MODE_1 -->'} = ($gref->{'inv_mode'}==1)?'checked':'';
	$GTOOLS::TAG{'<!-- INV_MODE_2 -->'} = ($gref->{'inv_mode'}==2)?'checked':'';
	$GTOOLS::TAG{'<!-- INV_MODE_3 -->'} = ($gref->{'inv_mode'}==3)?'checked':'';

	if ($gref->{'inv_mode'} == 0) {
		push @MSGS, qq~WARN|Inventory is currently disabled, if any orders are received while inventory is disabled then your counts may be off<br>~;
		}
	if ($gref->{'inv_mode'} == 1 && $gref->{'inv_police'}>0) {
		push @MSGS, qq~WARN|Incompatible Options Selected: "Internal Use Only" and "Inventory Policing" should not be used together.~;
		}
	if (($gref->{'inv_mode'}<=0) || ($gref->{'inv_mode'}>3)) {
		push @MSGS, qq~WARN|Invalid inventory mode: $gref->{'inv_mode'} please update your settings.~;
		}

	my $safety = $gref->{'inv_safety'};
	if (!defined $safety) { $safety = '0'; }
	$safety = &ZOOVY::incode($safety);
	my $html = '';

	##
	## CHK_INV_NOTIFY_16: Item quantity met reorder level
	## CHK_INV_NOTIFY_32: Item quantity below reorder level
	## 
	foreach my $i (1,2,4,8,16,32,64,128) {
		$GTOOLS::TAG{'<!-- CHK_INV_NOTIFY_'.$i.' -->'} = (($gref->{'inv_notify'}&$i)==$i)?'checked':'';
		}


	if ($FLAGS =~ /,API2,/) {
	##
	## ADVANCED INVENTORY
	##

	$html = 
	qq~
<Tr>
	<td colspan='2'>
	<b>General Settings:</b><br>
	&nbsp;&nbsp; <input type='checkbox' name='inv_reserve' ~.(($gref->{'inv_reserve'})?'checked':'').qq~> Track Reserved Inventory <B>RECOMMENDED</b><br>
	</td>
</tr>
<tr bgcolor='F0F0F0'>
	<td colspan='2'>
	<b>Checkout Settings: </b><br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_police'}==0)?'checked':'').qq~ name='inv_police' value='0'> Allow customers to purchase quantities larger than the inventory in stock.</font><br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_police'}==1)?'checked':'').qq~ name='inv_police' value='1'> Reduce quantity in cart to match actual quantity available.</font><br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_police'}==2)?'checked':'').qq~ name='inv_police' value='2'> Reduce quantity in cart to match reserved quantity available. <B>RECOMMENDED</B></font><br>
		~;

	if ($FLAGS !~ /,API2,/) {
		## API2 have more graular control
		$html .= qq~
		&nbsp;&nbsp; <input type='checkbox' name='inv_notify'  ~.(($gref->{'inv_notify'})?'checked':'').qq~>&nbsp;&nbsp;<font size='2'> Notifications: send email on all inventory events.</font><br>
		~;
		};

	$html .= q~
		&nbsp;&nbsp; <input type="checkbox" name='inv_police_checkout' ~.(($gref->{'inv_police_checkout'})?'checked':'').qq~>&nbsp;&nbsp;<font size='2'> Verify Contents During Checkout <B>RECOMMENDED</B><br>
	<br>
	</td>
</tr>
<tr bgcolor='FFFFFF'>
	<td colspan='2'>
	<b>Channel Settings:</b><br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_channel'}==0)?'checked':'').qq~  name='inv_channel' value='0'> Always let me create channels regardless of inventory settings.<br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_channel'}==2)?'checked':'').qq~  name='inv_channel' value='2'> Do not create channels when quantity exceeds actual inventory.<br>
		&nbsp;&nbsp; <input type='radio' ~.(($gref->{'inv_channel'}==4)?'checked':'').qq~ name='inv_channel' value='4'> Do not create channels when quantity exceeds reserved inventory.<br>
 	<br>
	</td>
</tr>
<tr bgcolor='FFFFFF'>
	<td colspan='2'>
	<b>INVENTORY ACTIONS:</b><br>
	<i>Usage: Inventory actions are run during finalization which occurs after orders are received, 
or inventory is manually updated. 
	Although inventory counts are immediately updated, 
the finalization process can take anywhere from a few minutes to several hours to occur (based on system load). </i>
	<br>
	<u>Reserve Exceeded Actions:</u> [ actual# - reserve# &lt; 0 ]<br>
	(what happens if the amount reserved exceeds the available inventory)<br>
	 	&nbsp;&nbsp; <input type='checkbox' name='rexceed_remove'  ~.((($gref->{'inv_rexceed_action'} & 1) == 1)?'checked':'').qq~> Remove from Website Navigation Categories/Lists<br>
		&nbsp;&nbsp; <input type='checkbox' name='rexceed_revoke'  ~.((($gref->{'inv_rexceed_action'} & 2) == 2)?'checked':'').qq~> Revoke any active channels (recommended)<br>
		<br>
	<u>Reserve Met Actions:</u> [ actual# - reserve# &lt; 1 ]<br>
	(what happens when we have allocated, but not exceeded the inventory in all channels)<br>
	 	&nbsp;&nbsp; <input type='checkbox' name='reserve_remove' ~.((($gref->{'inv_reserve_action'} & 1) == 1)?'checked':'').qq~> Remove from Website<br>
		&nbsp;&nbsp; <input type='checkbox' name='reserve_revoke' ~.((($gref->{'inv_reserve_action'} & 2) == 2)?'checked':'').qq~> Revoke any active channels (not recommended)<br>
		<br>
	<u>Safety Met Actions:</u> [ actual# - safety# &lt; 1 ]<br>
	(useful for situations where inventory may be overstated e.g. drop shipping)<br>
		&nbsp;&nbsp; Safety Quantity <input type='textbox' value="$safety" name='safety' size='2'> (set to zero to disable safety behavior)<br>
		&nbsp;&nbsp; <input type='checkbox' name='safety_remove'  ~.((($gref->{'inv_safety_action'} & 1) == 1)?'checked':'').qq~> Remove from Website<br>
		&nbsp;&nbsp; <input type='checkbox' name='safety_revoke'  ~.((($gref->{'inv_safety_action'} & 2) == 2)?'checked':'').qq~> Revoke any active channels<br>
		&nbsp;&nbsp; <input type='checkbox' name='inv_notify_64'  ~.((($gref->{'inv_notify'} & 64) == 64)?'checked':'').qq~> Notify when safety reached.<br>
		<br>
	<u>Out of Stock Actions:</u> [ actual# &lt; 1 ]<br>
	(what happens when the actual inventory on hand drops to zero)<br>
		&nbsp;&nbsp; <input type='checkbox' name='inv_outofstock_action_1'  ~.((($gref->{'inv_outofstock_action'} & 1) == 1)?'checked':'').qq~> Remove from Website<br>
		&nbsp;&nbsp; <input type='checkbox' name='inv_outofstock_action_2'  ~.((($gref->{'inv_outofstock_action'} & 2) == 2)?'checked':'').qq~> Revoke any active channels<br>
		<br>
	</td>
</tr>
	~;
		}
	else {
		my $remove_items = (($gref->{'inv_outofstock_action'} &1) & ($gref->{'inv_rexceed_action'} & 1))?1:0;
		$html .= qq~
<tr>
	<td colspan=2>
	<u>Out of Stock/Reserve Exceeded:</u><br>
(what happens when the actual inventory on hand drops to zero, or the reserve is exceeded)<br>
	&nbsp;&nbsp; <input type='checkbox' name='inv_website_remove'  ~.(($remove_items)?'checked':'').qq~> Remove from Website<br>
<!--
	&nbsp;&nbsp; <input type='checkbox' name='inv_website_remove'  ~.(($remove_items)?'checked':'').qq~> Remove from Syndication Feeds<br>
-->


</tr>
~;
		}


	$GTOOLS::TAG{'<!-- ADVANCED_INVENTORY -->'} = $html;	
	}


my @TABS = ();
push @TABS, { name=>'General', selected=>($VERB eq 'GENERAL')?1:0, link=>'/biz/setup/global/index.cgi?VERB=GENERAL', target=>'_top' };
push @TABS, { name=>'Inventory', selected=>($VERB eq 'INVENTORY')?1:0, link=>'/biz/setup/global/index.cgi?VERB=INVENTORY', target=>'_top' };
push @TABS, { name=>'WMS', selected=>($VERB eq 'WMS')?1:0, link=>'/biz/setup/global/index.cgi?VERB=WMS', target=>'_top' };
push @TABS, { name=>'Partitions', selected=>($VERB eq 'PARTITIONS')?1:0, link=>'/biz/setup/global/index.cgi?VERB=PARTITIONS', target=>'_top' };

&GTOOLS::output('*LU'=>$LU,
   'title'=>'Setup : Global Account Settings',
   'file'=>$template_file,
   'header'=>'1',
   'tabs'=>\@TABS,
	'msgs'=>\@MSGS,
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Global Setup',link=>'http://www.zoovy.com/biz/setup/global','target'=>'_top', },
      ],
   );




exit;


