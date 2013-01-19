#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use ZWEBSITE;
use ZTOOLKIT;
use Data::Dumper;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};		## ADD, EDIT, SAVE
my $ID = $ZOOVY::cgiv->{'ID'};			## THE GLOBALLY UNIQUE ID FOR THIS METHOD
$ID = uc($ID);
$ID =~ s/[^A-Z0-9_]+//g;
my @MSGS = ();

my $HANDLER = ''; ## FIXED, WEIGHT, PRICE, PICKUP, SIMPLE
my $HELP = '';
my $template_file = 'universal.shtml';
my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup/index.cgi','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping/index.cgi','target'=>'_top', };

#          {
#            'country' => 'US',
#            'price1' => '2.81',
#            'name' => 'USPS: First Class',
#            'carrier' => '',
#            'handler' => 'WEIGHT',
#            'weight' => '5',
#            'id' => 'WEIGHT_US_0'
#          }

##
##
##
my %ref = ();
my $exist = &ZWEBSITE::ship_get_method($USERNAME,$PRT,$ID);
if (defined $exist) {
	## okay so we've already got some existing data, we'll load that
	%ref = %{$exist};
	$HANDLER = $ref{'handler'};
	# print STDERR Dumper(\%ref);
	}

print STDERR Dumper([$USERNAME,$PRT,$ID],\%ref);


if ($VERB =~ /^UPDATE:/) {
	## this is not a save, this is some other action where only ID is passed, no other save is made.
	## a subverb is passed after the update e.g. :ADD or :DELETE
	}

if ($VERB eq 'SAVE') {
	## these variables SHOULD NOT be changed once we an item has been added.
	# $ref{'id'} = $ID;
	# $ref{'handler'} = uc($HANDLER);	
	
	$ref{'rules'} = (defined $ZOOVY::cgiv->{'METHOD_RULES'})?1:0;
	$ref{'active'} = (defined $ZOOVY::cgiv->{'METHOD_ACTIVE'})?1:0;

	$ref{'region'} = $ZOOVY::cgiv->{'METHOD_REGION'};
	$HANDLER = $ref{'handler'};

	$ref{'name'} = $ZOOVY::cgiv->{'METHOD_NAME'};
	$ref{'name'} =~ s/^[\s]+(.*?)$/$1/g;
	$ref{'name'} =~ s/(.*?)[\s]+$/$1/g;

	$ref{'carrier'} = uc($ZOOVY::cgiv->{'METHOD_CARRIER'});
	$ref{'carrier'} =~ s/^[\s]+(.*?)$/$1/g;
	$ref{'carrier'} =~ s/(.*?)[\s]+$/$1/g;
	$ref{'carrier'} = substr($ref{'carrier'},0,4);

	$ref{'region'} = $ZOOVY::cgiv->{'METHOD_REGION'};
	}
$GTOOLS::TAG{'<!-- HANDLER -->'} = $HANDLER;



if ($VERB eq 'DELETE') {
	&ZWEBSITE::ship_del_method($USERNAME,$PRT,$ID);
	print "Location: /biz/setup/shipping\n\n";
	exit;
	}


if ($VERB eq 'ADD') {
	$HANDLER = $ZOOVY::cgiv->{'_HANDLER'};	## FIXED, WEIGHT, PRICE, PICKUP, SIMPLE
	$ID = $HANDLER.'_'.time();
	$ref{'id'} = $ID;

	$ref{'active'} = 0;
	$ref{'rules'} = 0;
	$ref{'region'} = 'US';
	$ref{'name'} = "$HANDLER Shipping";
	$ref{'carrier'} = 'FOO';
	$ref{'handler'} = $HANDLER;
	

	&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
	$VERB = 'EDIT';
	}

##
##
##




if (($VERB eq 'EDIT') || ($VERB eq 'SAVE') || ($VERB =~ /^UPDATE/)) {
	$GTOOLS::TAG{'<!-- CHK_METHOD_RULES -->'} = ($ref{'rules'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_METHOD_ACTIVE -->'} = ($ref{'active'})?'checked':'';
	$GTOOLS::TAG{'<!-- METHOD_NAME -->'} = &ZOOVY::incode($ref{'name'});
	$GTOOLS::TAG{'<!-- METHOD_CARRIER -->'} = &ZOOVY::incode(substr(uc($ref{'carrier'}),0,4));

	if ($ref{'carrier'} eq '') {
		my $help_link = &GTOOLS::help_link("","#51171");
		$GTOOLS::TAG{'<!-- WARN_CARRIER_CODE -->'} = "<div class=\"hint\">Hint: using carrier codes can improve your shipping efficiency, read about them in $help_link</div>";
		}
	elsif ($VERB ne 'SAVE') {
		}
	elsif ($ref{'carrier'} eq 'FOO') {
		my $help_link = &GTOOLS::help_link("","#51171");
		$GTOOLS::TAG{'<!-- WARN_CARRIER_CODE -->'} = "<div class=\"hint\">Hint: carrier code \"FOO\" is a placeholder and doesn't actually work! You should probably change it - read about carrier codes in $help_link</div>";
		}

	my @AVAILABLE_REGIONS = (
		['US','United States'],
		['CA','Canada'],
		['INT','International']
		);
	if ($HANDLER eq 'LOCAL') {
		@AVAILABLE_REGIONS = ( ['US','United States'] );
		}
	if ($HANDLER eq 'LOCAL_CANADA') {
		@AVAILABLE_REGIONS = ( ['CA', 'Canada'] );
		}

	my $c = '';
	foreach my $r (@AVAILABLE_REGIONS) {
		my $selected = (($ref{'region'} eq $r->[0])?'selected':'');
		$c .= "<option $selected value=\"$r->[0]\">$r->[1]</option>\n";
		}
	$GTOOLS::TAG{'<!-- AVAILABLE_REGIONS -->'} = $c;

	#$GTOOLS::TAG{'<!-- METHOD_REGION_US -->'} = ($ref{'region'} eq 'US')?'selected':'';
	#$GTOOLS::TAG{'<!-- METHOD_REGION_CA -->'} = ($ref{'region'} eq 'CA')?'selected':'';
	#$GTOOLS::TAG{'<!-- METHOD_REGION_INT -->'} = ($ref{'region'} eq 'INT')?'selected':'';
	if ($ref{'active'}==0) {	
		push @MSGS, "WARN|This method is currently not active and will be ignored except during tests.";
		}
	}



##
##
##
if (($VERB eq 'SAVE') && ($HANDLER eq 'FIXED')) {
	&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
	$VERB = 'EDIT';
	}

if (($VERB eq 'EDIT') && ($HANDLER eq 'FIXED')) {
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Fixed Price Shipping";
	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
Fixed price shipping accepts two shipping prices per product.
A first item shipping price, and a second item shipping price. 
<br>
On multiple-item orders the first price is used for the item with the most expensive shipping price, 
and the second item price for all other items. 
~;

		$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
<tr>
	<td class="zoovysub1header" colspan=5>Configure Notes</td>
</tr>
<tr>
	<td colspan=5>
	At this time you can only configure one fixed shipping method per destination region.
	</td>
</tr>
~;

#		$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
#<tr>
#	<td class="zoovysub1header" colspan=5>Advanced Configuration</td>
#</tr>
#<tr>
#	<td>1st Item Product Attribute:</td>
#	<td><input type="textbox" name="METHOD_attrib1"></td>
#	<td>&nbsp;</td>
#	<td>Additional Item Product Attribute:</td>
#	<td><input type="textbox" name="METHOD_attrib2"></td>
#</tr>
#~;
		}



print STDERR "VERB: $VERB\n";


##
##
##
if ( ($VERB =~ /^(SAVE|UPDATE)([\:]?.*?)$/) && ($HANDLER eq 'LOCAL')) {
	$VERB = $1;
	my ($SUBVERB) = ($VERB eq 'UPDATE')?$2:'';	

	# print STDERR "SUBVERB: $SUBVERB\n";
	my $changes = 0;
	if ($SUBVERB eq ':DELETE') {
		my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
		delete $hashref->{$ZOOVY::cgiv->{'KEY'}};
		$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
		$changes++;
		}
	elsif ($SUBVERB eq ':ADD') {
		my $startzip = $ZOOVY::cgiv->{'startzip'};
		$startzip =~ s/[^0-9]//g;
		my $endzip = $ZOOVY::cgiv->{'endzip'};
		$endzip =~ s/[^0-9]//g;
		my $price = $ZOOVY::cgiv->{'price'};
		my $key = $startzip.'-'.$endzip;

		# print STDERR "DATA: $ref{'data'}\n";
		if (length($startzip)!=5) {
			push @MSGS, "ERR|Starting zip is invalid, cannot save.";
			}
		elsif (length($endzip)!=5) {
			push @MSGS, "ERR|Ending zip is invalid, cannot save.";
			}
		else {
			my $hashref =  &ZTOOLKIT::parseparams($ref{'data'});
			$hashref->{$key} = sprintf("%.2f",$price);
			$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
			&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
			$changes++;
			}
		}
	elsif ($VERB eq 'SAVE') {
		$changes++;
		}

	if ($changes) {
		push @MSGS, "SUCCESS|Successfully saved settings.";
		&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
		}

	$VERB = 'EDIT';
	}


##
##
##
if ( ($VERB =~ /^(SAVE|UPDATE)([\:]?.*?)$/) && ($HANDLER eq 'LOCAL_CANADA')) {
	$VERB = $1;
	my ($SUBVERB) = ($VERB eq 'UPDATE')?$2:'';	

	# print STDERR "SUBVERB: $SUBVERB\n";
	my $changes = 0;
	if ($SUBVERB eq ':DELETE') {
		my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
		delete $hashref->{$ZOOVY::cgiv->{'KEY'}};
		$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
		$changes++;
		}
	elsif ($SUBVERB eq ':ADD') {
		my $zippattern = uc($ZOOVY::cgiv->{'zippattern'});
		$zippattern =~ s/[^A-Z0-9]+//g;	 #strip whitespace
		my $instructions = $ZOOVY::cgiv->{'instructions'};
		$instructions =~ s/^[\s]+//g;		# remove leading whitespace
		$instructions =~ s/[\s]+$//g;		# remove trailing whitespace
		$instructions =~ s/\|//g;			# pipes are now allowed
		my $price = $ZOOVY::cgiv->{'price'};

		# print STDERR "DATA: $ref{'data'}\n";
		if (length($zippattern)==0) {
			push @MSGS, "WIN|Pattern is blank, cannot save.";
			}
		else {
			my $hashref =  &ZTOOLKIT::parseparams($ref{'data'});
			$hashref->{$zippattern} = sprintf("%.2f|%s",$price,$instructions);
			$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
			&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
			$changes++;
			}
		}
	elsif ($VERB eq 'SAVE') {
		$changes++;
		}

	if ($changes) {
		push @MSGS, "WIN|Successfully saved settings.";
		&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
		}

	$VERB = 'EDIT';
	}






if (($VERB eq 'EDIT') || ($VERB eq 'SAVE')) {
	require ZSHIP::RULES;
	my $METHOD = uc($ID);
	#if (($PRT>0) && ($METHOD !~ /\.[\d]+$/)) {
	#	## add a .## to the METHOD to signify which PARTITION we're working in.
	#	$METHOD = "$METHOD.$PRT";
	#	}

	print STDERR "PRT: $PRT ($METHOD)\n";
	if ($METHOD !~ /^SHIP-/) { $METHOD = "SHIP-$METHOD"; }
	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,"$METHOD");
	my $c = "";
	my $counter = 0;
	# print STDERR "Parsing ".scalar(@rules)." rules\n";

	if (scalar(@rules)>0) {
		my $maxcount = scalar(@rules);
		$c .= "<tr>";
		$c .= "<td class='zoovysub2header'>ID</td>";
		$c .= "<td class='zoovysub2header'>Change</td>";
		$c .= "<td class='zoovysub2header'>Matching Rule</td>";
		$c .= "<td class='zoovysub2header'>Filter</td>";
		$c .= "<td class='zoovysub2header'>Action</td>";
		$c .= "<td class='zoovysub2header'>Value</td>";
		$c .= "<td class='zoovysub2header'>Rule Name</td>";
		$c .= "<td class='zoovysub2header'>Price Sched.</td>";
		$c .= "</tr>";

		my $row = '';	
		for (my $counter=0; $counter<scalar(@rules); $counter++) {
			my $rulehash = $rules[$counter];
			my $MATCH = ''; my $EXEC = '';
	
			$row = ($row eq 'r0')?'r1':'r0';

			foreach my $mr (@ZSHIP::RULES::MATCH) {
				if ($rulehash->{'MATCH'} eq $mr->{'id'}) { $MATCH = $mr->{'txt'}; }
				}
			foreach my $mr (@ZSHIP::RULES::EXEC) {
				if ($rulehash->{'EXEC'} eq $mr->{'id'}) { $EXEC = $mr->{'txt'}; }
				}
	
			$c .= "<tr>";
			$c .= "<td class='$row'>$counter</td><td class='A'>";
			# Print the UP arrow
			if ($counter>0) { $c .= "<a href='/biz/setup/shipping/rulebuilder.cgi?ACTION=UP&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Down' src='images/up.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='16' width='16'>"; }
			$c .= '&nbsp;';
			# Print the DOWN arrow
			if (($counter<$maxcount-1) && ($maxcount>1)) { $c .= "<a href='/biz/setup/shipping/rulebuilder.cgi?ACTION=DOWN&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Up' src='images/down.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='16' width='16'>"; }
			$c .= '&nbsp;';
			$c .= "<a href='/biz/setup/shipping/rulebuilder.cgi?ACTION=EDIT&method=$METHOD&THIS=$counter'><img border='0' alt='Change' src='images/change.gif'></a>";
			$c .= "</td><td class='A'>".$MATCH."</td>";
			$c .= "<td class='$row'>".$rulehash->{'FILTER'}."</td>";
			$c .= "<td class='$row'>".$EXEC."</td>";
			$c .= "<td class='$row'>".$rulehash->{'VALUE'}."</td>";
			$c .= "<td class='$row'>".$rulehash->{'NAME'}."</td>";
			$c .= "<td class='$row'>".$rulehash->{'SCHEDULE'}."</td>";
			$c .= "</tr>";
			}
	  }
	else {
		$c .= "<tr><td bgcolor='FFFFFF'><i>No rules have been defined. $METHOD</i></td></tr>";
		}

	if ($FLAGS =~ /,SHIP,/)  {
		$c .= qq~<tr><td colspan=7 bgcolor='FFFFFF'><a href="/biz/setup/shipping/rulebuilder.cgi?ACTION=APPEND&method=$METHOD&id=0">[Add Rule]</a></td></tr>~;
		}
	else {
		$c .= qq~<tr><td colspan=7 bgcolor='FFFFFF'>WARNING: Shipping Bundle not enabled, rules may not work after next system upgrade.</td></tr>~;
		}


	$GTOOLS::TAG{'<!-- RULES -->'} = $c;
	}




#if (($VERB eq 'EDIT') && ($HANDLER eq 'FEDEX-DOM')) {
#	push @BC, { name=>'FedEx International Shipping' };
#																																																																																																					$GTOOLS::TAG{'<!-- TITLE -->'} = "FedEx Domestic Shipping";
#	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
#~;
#	}
#
#if (($VERB eq 'EDIT') && ($HANDLER eq 'FEDEX-INT')) {
#	push @BC, { name=>'FedEx International Shipping' };
#	$GTOOLS::TAG{'<!-- TITLE -->'} = "FedEx International Shipping";
#	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
#~;
#	}
#
#if (($VERB eq 'EDIT') && ($HANDLER eq 'UPS-DOM')) {
#	push @BC, { name=>'UPS Domestic Shipping' };
#	$GTOOLS::TAG{'<!-- TITLE -->'} = "UPS Domestic Shipping";
#	}
#
#if (($VERB eq 'EDIT') && ($HANDLER eq 'UPS-INT')) {
#	push @BC, { name=>'UPS International Shipping' };
#	$GTOOLS::TAG{'<!-- TITLE -->'} = "UPS International Shipping";
#	}
#
#if (($VERB eq 'EDIT') && ($HANDLER eq 'USPS-DOM')) {
#	push @BC, { name=>'USPS Domestic Shipping' };
#	$GTOOLS::TAG{'<!-- TITLE -->'} = "USPS Domestic Shipping";
#qq~
#	<tr>
#		<td valign="top"><b>OFFER PARCEL POST:</b></td>
#		<td valign="top" align="center"><input type="checkbox" <!-- USPS_DOM_BULKRATE --> name="usps_dom_bulkrate" value="1"></td>
#		<td valign="top" align="center"></td>
#	</tr>
#	<tr>
#		<td valign="top"><b>+Insurance:</b></td>
#		<td valign="top" align="center"><select name="usps_dom_ins">
#				<option <!-- USPS_DOM_INS_0 --> value="0">Without</option>
#				<option <!-- USPS_DOM_INS_1 --> value="1">With &amp; Without</option>
#				<option <!-- USPS_DOM_INS_2 --> value="2">With Only</option>
#			</select>
#		<td valign="top" align="center"><select name="usps_int_ins">
#				<option <!-- USPS_INT_INS_0 --> value="0">Without</option>
#				<option <!-- USPS_INT_INS_1 --> value="1">With &amp; Without</option>
#				<option <!-- USPS_INT_INS_2 --> value="2">With Only</option>
#			</select>
#		</td>
#	</tr>
#~;
#
#	}
#
#if (($VERB eq 'EDIT') && ($HANDLER eq 'USPS-INT')) {
#	push @BC, { name=>'USPS International Shipping' };
#	$GTOOLS::TAG{'<!-- TITLE -->'} = "USPS International Shipping";
#	push @BC, { name=>'USPS International' };
#	
#	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
#Origin Zip: <input type="textbox" name="">
#
#USPS Rating Engine
#USAGE: Please select the method(s) of United States Postal Service shipping to offer to customers. 
#During checkout the price will be derived from USPS based on the total weight of the order, 
#and making the assumption that it will fit into a standard box size.
#For this	method to accurately calculate shipping from your origin to the customers destination address. 
#The handling fee (if any) will be added to the USPS quoted rates, after insurance has been applied. 
#</p>
#	<tr>
#		<td valign="top"><b>OFFER PRIORITY MAIL:</b>(6-10 days)</td>
#		<td valign="top" align="center"><input type="checkbox" <!-- USPS_DOM_PRIORITY --> name="usps_dom_priority" value="1"></td>
#		<td valign="top" align="left">
#			<input type="checkbox" <!-- USPS_INT_PRIORITY_1 --> name="usps_int_priority_1" value="1"> Other Pkg.<br>
#			<input type="checkbox" <!-- USPS_INT_PRIORITY_2 --> name="usps_int_priority_2" value="2"> Flat Box.<br>
#			<input type="checkbox" <!-- USPS_INT_PRIORITY_4 --> name="usps_int_priority_4" value="4"> Flat Env.<br>
#		</td>
#	</tr>
#	<tr>
#		<td valign="top"><b>OFFER EXPRESS MAIL:</b><br>(3-5 days)</td>
#		<td valign="top" align="center"><input type="checkbox" <!-- USPS_DOM_EXPRESS --> name="usps_dom_express" value="1"></td>
#		<td valign="top" align="left">
#			<input type="checkbox" <!-- USPS_INT_EXPRESS_1 --> name="usps_int_express_1" value="1"> Other Pkg.<br>
#			<input type="checkbox" <!-- USPS_INT_EXPRESS_2 --> name="usps_int_express_2" value="2"> Flat Env.<br>
#		</td>
#	</tr>
#	<tr>
#		<td valign="top"><b>OFFER GLOBAL EXPRESS GUARANTEED:</b><br>(1-3 days)</td>
#		<td valign="top" align="left"></td>
#		<td valign="top" align="left">
#			<input type="checkbox" <!-- USPS_INT_EXPRESSG_1 --> name="usps_int_expressg_1" value="1"> Other Pkg.<br>
#			<input type="checkbox" <!-- USPS_INT_EXPRESSG_2 --> name="usps_int_expressg_2" value="2"> Rectangular.<br>
#			<input type="checkbox" <!-- USPS_INT_EXPRESSG_4 --> name="usps_int_expressg_4" value="4"> Non-Rectangular.<br>
#		</td>
#	</tr>
#	<tr>
#		<td valign="top"><b>+Insurance:</b></td>
#		<td valign="top" align="center">
#			<select name="usps_int_ins">
#				<option <!-- USPS_INT_INS_0 --> value="0">Without</option>
#				<option <!-- USPS_INT_INS_1 --> value="1">With &amp; Without</option>
#				<option <!-- USPS_INT_INS_2 --> value="2">With Only</option>
#			</select>
#		</td>
#	</tr>
#	<tr>
#		<td valign="top"><b>Insurance Fee*:</b></td>
#		<td valign="top" align="center"><input type="textbox" size='6' name="usps_int_insprice" value="<!-- USPS_INT_INSPRICE -->"></td>
#	</tr>
#	<tr>
#		<td valign="top" colspan="3">
#		<i>* Either a flat fee or a percentage of the sale.   
#			Zoovy does not quote actual USPS Insurance rates since they do not provide an API for retrieving them</i>
#		</td>
#	</tr>
#	<tr>
#		<td valign="top">+Handling Charge:</td>
#		<td valign="top" align="center"><input type="textbox" size='6' name="usps_int_handling" value="<!-- USPS_INT_HANDLING -->"></td>
#	</tr>
#</table>
#
#~;

#	# load the zip spans into the select box
#	my @ar = split(',',$webdbref->{'ship_pickup_zips'});
#	my $c = "";
#	foreach my $k (sort @ar) { $c .= "<option value=''>$k</option>\n"; }
#	$GTOOLS::TAG{"<!-- ZIP_SPANS -->"} = $c;
#
#	# load up the help
#	$c = &ZOOVY::incode($webdbref->{'ship_pickup_help'});
#	if ($c eq "") { $c = "Sample: Please visit our store at 123 main street during our normal business hours.
#	If you want us to have your order ready, please call in advance."; }
#	$GTOOLS::TAG{"<!-- HELP -->"} = $c;

#	my $c = '';
#	my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
#	}






if (($VERB eq 'EDIT') && ($HANDLER eq 'LOCAL')) {
	$HELP = '#50812';
	push @BC, { name=>'Local Delivery' };
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Delivery/Pickup Options";
	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
Delivery/Pickup filters by geography, allowing clients to visit to your store, or opt for delivery
rather than using a standard carrier.<br>
<br>

If you plan to deliver to a small geographic area, or are able to accept customer walk-ins then 
this can be a great way to give customers the convience of purchasing online without the expense of shipping.<br>
<br>
~;

#	# load the zip spans into the select box
#	my @ar = split(',',$webdbref->{'ship_pickup_zips'});
#	my $c = "";
#	foreach my $k (sort @ar) { $c .= "<option value=''>$k</option>\n"; }
#	$GTOOLS::TAG{"<!-- ZIP_SPANS -->"} = $c;
#
#	# load up the help
#	$c = &ZOOVY::incode($webdbref->{'ship_pickup_help'});
#	if ($c eq "") { $c = "Sample: Please visit our store at 123 main street during our normal business hours.
#	If you want us to have your order ready, please call in advance."; }
#	$GTOOLS::TAG{"<!-- HELP -->"} = $c;

	my $c = '';
	my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
	foreach my $k (sort { $a <=> $b; } keys %{$hashref}) {
		my ($price) = $hashref->{$k};
		my ($startzip,$endzip) = split(/-/,$k);
		$c .= "<tr><td><a href='/biz/setup/shipping/universal.cgi?VERB=UPDATE:DELETE&ID=$ID&KEY=$k'>[DELETE]</a></td><td>$startzip</td><td>$endzip</td><td>\$$price</td></tr>";
		}
	if (length($c)>0) {
		$c = "<tr class='zoovysub2header'><td>ACTION</td><td>START ZIP</td><td>END ZIP</td><td>SHIP PRICE</td></tr>".$c;
		} 
	else {
		$c .= "<tr><td colspan=4><i>No Entries Have been Added</i></td></tr>";
		}
	$c .= q~
<tr>
	<td>&nbsp;</td>
	<td>Start Zip: <input size=5 maxlength=5 type=textbox name=startzip></td>
	<td>End Zip: <input size=5 maxlength=5 type=textbox name=endzip></td>
	<td>Ship Price $<input size=5 type=textbox name=price></td>
	<td><button type="submit" onClick=" document.thisFrm.VERB.value='UPDATE:ADD'; " class="button">Add</button></td>
</tr>
~;


	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
<tr class="zoovysub1header">
	<td colspan=5>Zip Code Restrictions</td>
</tr>
<tr>
	<td colspan=5>
	Specify Eligible Zip Codes (leave blank for all zip codes 00000-99999)<br>
	You may specify a range of zip codes (eg: 92000 to 92111) for your local area.<br>
	To specify a single zip code you must enter it twice (as both the starting and ending number).<br>
	For single Zip codes use the same number in both beginning and ending. (eg: 11111-11111)<br>
	Please avoid using ZIP+4 routing codes, only enter 5 digit Zip codes<br>
	<br>
	<table>
	$c 
	</table>
	</td>
</tr>
~;
 	}


if (($VERB eq 'EDIT') && ($HANDLER eq 'LOCAL_CANADA')) {
	$HELP = '#50812';
	push @BC, { name=>'Canada Local Delivery' };
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Canada Delivery/Pickup Options";
	$GTOOLS::TAG{'<!-- ABOUT -->'} = q~
Delivery/Pickup filters by geography, allowing clients to visit to your store, or opt for delivery
rather than using a standard carrier.<br>
<br>

If you plan to deliver to a small geographic area, or are able to accept customer walk-ins then 
this can be a great way to give customers the convience of purchasing online without the expense of shipping.<br>
<br>
~;

	my $c = '';
	my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
	foreach my $zippattern (sort keys %{$hashref}) {
		my ($price,$instructions) = split(/\|/,$hashref->{$zippattern},2);
		my $outputzip = sprintf("%s %s",substr($zippattern,0,3),substr($zippattern,3));
		$c .= "<tr><td valign=top><a href='/biz/setup/shipping/universal.cgi?VERB=UPDATE:DELETE&ID=$ID&KEY=$zippattern'>[DELETE]</a></td><td valign=top>$outputzip</td><td valign=top>\$$price</td><td valign=top>$instructions</td></tr>";
		}

	if (length($c)>0) {
		$c = "<tr class='zoovysub2header'><td>ACTION</td><td>ZIP PATTERN</td><td>SHIP PRICE</td><td>INSTRUCTIONS</td></tr>".$c;
		} 
	else {
		$c .= "<tr><td colspan=4><i>No Entries Have been Added</i></td></tr>";
		}
	$c .= q~
<tr>
	<td valign=top>&nbsp;</td>
	<td valign=top>Zip Code Pattern: <input size=6 maxlength=6 type=textbox name=zippattern></td>
	<td valign=top>Ship Price $<input size=5 type=textbox name=price></td>
	<td valign=top><button type="submit" onClick="document.thisFrm.VERB.value='UPDATE:ADD';" class="button">Add</button></td>
</tr>
<tr>
	<td colspan=5 valign=top>Pickup Instructions:<br>
		<textarea cols=50 name="instructions"></textarea>
		<div class="hint">Not currently displayed - future enhancement</div>
	</td>
</tr>
~;


	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
<tr class="zoovysub1header">
	<td colspan=5>Zip Code Restrictions</td>
</tr>
<tr>
	<td colspan=5>
	Specify Eligible Zip Code patterns either partial ex: "9XA" or full: "9XA 1A1"
	<br>
	<table>
	$c 
	</table>
	</td>
</tr>
~;
 	}






##
##
##
if (($VERB eq 'SAVE') && ($HANDLER eq 'FREE')) {

	push @BC, { name=>'Simple Shipping' };
	my $itemprice = sprintf("%.2f",$ZOOVY::cgiv->{'total'});
	$ref{'total'} = $itemprice;

	&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
	$VERB = 'EDIT';
	}

if (($VERB eq 'EDIT') && ($HANDLER eq 'FREE')) {
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Free Shipping";
	$GTOOLS::TAG{'<!-- ABOUT -->'} = qq~
Free Shipping can be easily configured to offer free shipping when the order or package total reaches a set amount.
<br>
~;
	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = q~
<tr class="zoovysub1header">
	<td colspan=5>Order Total</td>
</tr>
<tr>
	<td>Amount:</td>
	<td>$<input type="textbox" size=6 maxlength="6" name="total" value="~.$ref{'total'}.q~"></td>
	<td colspan=3><i>The mininum order/package total that qualifies for free shipping (ex: use zero dollars for free shipping on every order/package)</i></td>
</tr>
~;
	}






##
##
##
if (($VERB eq 'SAVE') && ($HANDLER eq 'SIMPLE')) {

	push @BC, { name=>'Simple Shipping' };
	my $itemprice = sprintf("%.2f",$ZOOVY::cgiv->{'itemprice'});
	$ref{'itemprice'} = $itemprice;
	my $addprice = sprintf("%.2f",$ZOOVY::cgiv->{'addprice'});
	$ref{'addprice'} = $addprice;

	&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
	$VERB = 'EDIT';

	}

if (($VERB eq 'EDIT') && ($HANDLER eq 'SIMPLE')) {
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Simple Shipping";
	$GTOOLS::TAG{'<!-- ABOUT -->'} = qq~
Simple Shipping calculates the shipping based on the number of items purchased.<br>
Pricing cannot be configured on a per product basis, use this if all items you sell have identical shipping policies.
<br>
~;
	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = q~
<tr class="zoovysub1header">
	<td colspan=5>Pricing</td>
</tr>
<tr>
	<td>First Item:</td>
	<td>$<input type="textbox" size=6 maxlength="6" name="itemprice" value="~.$ref{'itemprice'}.q~"></td>
	<td colspan=3><i>The price if only one item is in the cart.</i></td>
</tr>
<tr>
	<td>Additional Item:</td>
	<td>$<input type="textbox" size=6 maxlength="6" name="addprice" value="~.$ref{'addprice'}.q~"></td>
	<td colspan=3><i>This amount will be added to the first item price for each additional item.</i></td>
</tr>
~;
	}


##
##
##
if ( ($VERB =~ /^(SAVE|UPDATE)([\:]?.*?)$/) && ($HANDLER eq 'WEIGHT')) {
	$VERB = $1;
	my ($SUBVERB) = ($VERB eq 'UPDATE')?$2:'';	
	require ZSHIP;

	my $changes++;
	if ($VERB eq 'SAVE') {
		$ref{'min_wt'} = $ZOOVY::cgiv->{'minwt'};
		$changes++;
		}
	
	# print STDERR "SUBVERB: $SUBVERB\n";
	if ($SUBVERB eq ':DELETE') {
		my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
		delete $hashref->{$ZOOVY::cgiv->{'KEY'}};
		$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
		push @MSGS, "WIN|Successfully removed weight based method.";
		$changes++;
		}

	if ($SUBVERB eq ':ADD') {
		my $weight = &ZSHIP::smart_weight_new($ZOOVY::cgiv->{'weight'});
		my $price = $ZOOVY::cgiv->{'price'};
		# print STDERR "DATA: $ref{'data'}\n";
		if (defined($weight) && defined($price)) {
			$weight =~ s/[^0-9\.]//g;
			$price =~ s/[^0-9\.]//g;
			if (($weight eq '') || ($weight<=0)) {
				push @MSGS, "ERR|Weight must be set, and greater than zero, not saved.";
				}
			elsif (($price eq '') || (int($price)<0)) {
				push @MSGS, "ERR|Price must be set to a non-negative number, not saved.";
				}
			else {
				my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
				$hashref->{$weight} = sprintf("%.2f",$price);
				$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
				$changes++;
				}
			}
		}


	if ($changes) {
		push @MSGS, "WIN| Sucessfully saved settings.";		
		&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
		}
	$VERB = 'EDIT';
	}

##
##
##
if (($VERB eq 'EDIT') && ($HANDLER eq 'WEIGHT')) {
	push @BC, { name=>'Weight Based' };
	$GTOOLS::TAG{'<!-- TITLE -->'} = 'Weight based shipping';
	$GTOOLS::TAG{'<!-- ABOUT -->'} = qq~
Simple Weight Calculator allows you to specify a simple handling rate based on the total weight of 
a particular package. During checkout the least value, which is greater than the total cart weight will match. If the 
cart weighs more than the greatest amount, and no other shipping methods are available then an error will be displayed.<br>
~;

	my $c = '';
	my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
	foreach my $k (sort { $a <=> $b; } keys %{$hashref}) {
		my ($price) = $hashref->{$k};
		$c .= "<tr><td><a href='/biz/setup/shipping/universal.cgi?VERB=UPDATE:DELETE&ID=$ID&KEY=$k'>[DELETE]</a></td><td>$k <font size='1'>ounces</font></td><td>\$$price</td></tr>";
		}
	if (length($c)>0) {
		$c = "<tr class='zoovysub2header'><td>ACTION</td><td>WEIGHT</td><td>SHIP PRICE</td></tr>".$c;
		} 
	else {
		$c .= "<tr><td colspan=4><i>No Entries Have been Added</i></td></tr>";
		}
	$c .= q~
<tr>
	<td>&nbsp;</td>
	<td>Max Weight: <input size=6 type=textbox name=weight></td>
	<td>Ship Price $<input size=5 type=textbox name=price></td>
	<td><button type="submit" onClick="document.thisFrm.VERB.value='UPDATE:ADD';" class="button">Add</button></td>
</tr>
~;

	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
<tr class="zoovysub1header">
	<td colspan=5>Weight Restrictions</td>
</tr>
<tr>
	<td nowrap>Min weight:</td>
	<td><input size=6 type="textbox" value="~.&ZOOVY::incode($ref{'min_wt'}).qq~" name="minwt"></td>
	<td colspan=3><i>The minimum weight of a cart in order to use this method. Use zero for none.</i></td>
</tr>
<tr class="zoovysub1header">
	<td colspan=5>Table</td>
</tr>
<tr>
	<td colspan=5>
	<table>
	$c 
	</table>
	</td>
</tr>
~;
	}



##
##
##

if ( ($VERB =~ /^(SAVE|UPDATE)([\:]?.*?)$/) && ($HANDLER eq 'PRICE')) {
	$VERB = $1;
	my ($SUBVERB) = ($VERB eq 'UPDATE')?$2:'';	

	if ($VERB eq 'SAVE') {
		$ref{'min_price'} = $ZOOVY::cgiv->{'minprice'};
		}
	
	# print STDERR "SUBVERB: $SUBVERB\n";
	if ($SUBVERB eq ':DELETE') {
		my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
		delete $hashref->{$ZOOVY::cgiv->{'KEY'}};
		$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
		}

	if ($SUBVERB eq ':ADD') {
		my $subtotal = sprintf("%.2f",$ZOOVY::cgiv->{'subtotal'});

		## strip any whitespace
		$subtotal =~ s/[\s]+//g;

		my $price = 0;
		if (substr($ZOOVY::cgiv->{'price'},0,1) eq '%') {
			## percentage!
			$price = $ZOOVY::cgiv->{'price'};
			}
		else {
			$price = sprintf("%.2f",$ZOOVY::cgiv->{'price'});
			}
		# print STDERR "DATA: $ref{'data'}\n";
		if (defined($subtotal) && defined($price)) {
			my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
			$hashref->{$subtotal} = $price;
			$ref{'data'} = &ZTOOLKIT::buildparams($hashref,1);
			}
		}

	# print STDERR "DATA: $ref{'data'}\n";

	&ZWEBSITE::ship_add_method($USERNAME,$PRT,\%ref);
	$VERB = 'EDIT';
	}




if (($VERB eq 'EDIT') && ($HANDLER eq 'PRICE')) {

	push @BC, { name=>'Price Based' };
	$GTOOLS::TAG{'<!-- TITLE -->'} = 'Price based shipping';
	$GTOOLS::TAG{'<!-- ABOUT -->'} = qq~
Simple Price allows you to specify a shipping fee based on the subtotal of an order. 
During checkout the least value, which is greater than the total cart price (before shipping, tax, etc.) will match. 
If the cart costs more than the greatest amount, and no other shipping methods are available then the message 
"Actual Shipping To Be Determined" will be displayed.<br>
~;

	my $c = '';
	my $hashref = &ZTOOLKIT::parseparams($ref{'data'});
	foreach my $k (sort { $a <=> $b; } keys %{$hashref}) {
		my ($price) = $hashref->{$k};
		my $op = '';
		if (substr($price,0,1) eq '%') { $op = '%'; $price = substr($price,1); }
		elsif (substr($price,0,1) eq '=') { $op = 'formula:'; $price = substr($price,1); }
		else { $op = '$'; }
		$c .= "<tr><td><a href='/biz/setup/shipping/universal.cgi?VERB=UPDATE:DELETE&ID=$ID&KEY=$k'>[DELETE]</a></td><td><font size='1'>up to </font>\$$k</td><td><font size='1'>shipping is:</font> $op$price</td></tr>";
		}
	if (length($c)>0) {
		$c = "<tr class='zoovysub2header'><td>ACTION</td><td>SUBTOTAL</td><td>SHIP PRICE</td></tr>".$c;
		} 
	else {
		$c .= "<tr><td colspan=4><i>No Entries Have been Added</i></td></tr>";
		}
	$c .= q~
<tr>
	<td>&nbsp;</td>
	<td>Subtotal: <input size=6 type=textbox name=subtotal></td>
	<td>Ship Price $<input size=5 type=textbox name=price></td>
	<td><button type="submit" onClick="document.thisFrm.VERB.value='UPDATE:ADD';" class="button">Add</button></td>
</tr>
<tr>
	<td>&nbsp;</td>
	<td colspan=3>
	<div class="hint">HINT: Specify %#.## in shipping price to use a percentage of the cart subtotal</div>
	</td>
</tr>
~;


	$GTOOLS::TAG{'<!-- UPPER_CONTENT -->'} = qq~
<tr class="zoovysub1header">
	<td colspan=5>Price Restrictions</td>
</tr>
<tr>
	<td nowrap>Min price:</td>
	<td>\$<input size=6 type="textbox" value="~.&ZOOVY::incode($ref{'min_price'}).qq~" name="minprice"></td>
	<td colspan=3><i>The minimum price of a cart in order to use this method.</i></td>
</tr>
<tr class="zoovysub1header">
	<td colspan=5>Table</td>
</tr>
<tr>
	<td colspan=5>
	<table>
	$c 
	</table>
	</td>
</tr>
~;
	}



$GTOOLS::TAG{'<!-- ID -->'} = $ID;
$GTOOLS::TAG{'<!-- MESSAGES -->'} = '<tr><td>'.&GTOOLS::show_msgs(\@MSGS).'</td></tr>';
&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,file=>$template_file,'jquery'=>'1',help=>$HELP,bc=>\@BC, header=>1);
