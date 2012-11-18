#!/usr/bin/perl
use lib "/httpd/modules";
use CGI;
require GTOOLS;
require ZOOVY;
require ZSHIP::RULES;
require WHOLESALE;
use strict;

require LUSER;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;

my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup','target'=>'_top', };
push @BC, { name=>'Shipping',link=>'/biz/setup/shipping','target'=>'_top', };

my @MSGS = ();

my $THIS = $q->param('THIS');
my $ACTION = '';
if ((index($FLAGS,',RBASE,')!=-1) || (index($FLAGS,',L2,')!=-1)) { $FLAGS .= ',SHIP,'; }

my $template_file = '';

if ($FLAGS !~ /,SHIP,/)  {
	$GTOOLS::TAG{'<!-- FLAGS -->'} = $FLAGS;
	$template_file = "rulebuilder-deny.shtml";	
	} 
else {

	my $METHOD = uc($q->param('method'));
	if ($METHOD !~ /^SHIP-/) {
		$METHOD = "SHIP-$METHOD";
		}
	#if (($PRT>0) && ($METHOD !~ /\.[\d]+$/)) {
	#	## add a .## to the METHOD to signify which PARTITION we're working in.
	#	$METHOD = "$METHOD.$PRT";
	#	}

	$GTOOLS::TAG{"<!-- METHOD -->"} = $METHOD;
	my $ACTION = uc($q->param('ACTION'));

	if ($METHOD =~ /^UPSAPI_/) {
		require ZWEBSITE;
		require ZSHIP::UPSAPI;
		my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

		my $upsapi_options = $webdbref->{'upsapi_options'};
		if (($upsapi_options & $ZSHIP::UPSAPI::OPTIONS{'use_rules'})==$ZSHIP::UPSAPI::OPTIONS{'use_rules'}) {
			## rules can run .. iz okay!
			}
		else {
			push @MSGS, "WARN|+UPS Rule processing is currently disabled. To enable rule processing return the UPS Online Tools Setup area.";
			}
		}

	if ($ACTION eq "DELETE") {
		$LU->log("SETUP.SHIPPING.RULES","Deleted Rule for $METHOD","SAVE");
 	   &ZSHIP::RULES::delete_rule($USERNAME,$PRT,$METHOD,$THIS);
 	   $ACTION = "";
		}


	##
	## this code is run when we swap the current rule and the one above it
	##
	if ($ACTION eq "UP") {
		$LU->log("SETUP.SHIPPING.RULES","Move Rule Up for $METHOD","SAVE");
 	 	&ZSHIP::RULES::swap_rule($USERNAME,$PRT,$METHOD,$THIS,$THIS-1);
 	 	$ACTION = "";
		}

	##
	## this code is run when we swap the current rule and the one below it.
	##
	if ($ACTION eq "DOWN") {
	  	my $this = $q->param('THIS');
 	 	my $next = $q->param('NEXT');
		$LU->log("SETUP.SHIPPING.RULES","Move Rule Down for $METHOD","SAVE");
		&ZSHIP::RULES::swap_rule($USERNAME,$PRT,$METHOD,$THIS,$THIS+1);
 	 	$ACTION = "";
	 	}


##
## this code is run to prepare rulebuilder-edit.shtml for editing an existing rule.
##
if ($ACTION eq "EDIT") {
	$GTOOLS::TAG{"<!-- ID -->"} = $THIS;
	$GTOOLS::TAG{"<!-- NEXT_ACTION -->"} = "SAVE-EDIT";
	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,$METHOD);

	my $found = 0;
	my %hash = %{$rules[$THIS]};

	my $c = '';
	$found = 0;
	foreach my $mr (@ZSHIP::RULES::MATCH) {
		next unless ($mr->{'ship'});
		my $id = $mr->{'id'};
		my $selected = ($hash{'MATCH'} eq $id)?'selected':'';
		if ($selected) { $found++; }
		if ($mr->{'short'} eq '') { $mr->{'short'} = $mr->{'txt'}; }
		$c .= "<option value=\"$id\" $selected>$mr->{'short'}</option>\n";
		}
	if ($hash{'EXEC'} eq '') {
		$c = "<option value=\"\">-- NOT CONFIGURED --</option>\n$c";
		}
	elsif (not $found) {
		$c = "<option value=\"$hash{'MATCH'}\">INVALID EXISTING: $hash{'MATCH'}</option>\n$c";
		}

	$GTOOLS::TAG{'<!-- MATCH -->'} = $c;

  	$GTOOLS::TAG{"<!-- NAME_V -->"} = &ZOOVY::incode($hash{'NAME'});
  	$GTOOLS::TAG{"<!-- FILTER -->"}  = &ZOOVY::incode($hash{'FILTER'});

	$c = '';
	$found = 0;
	foreach my $mr (@ZSHIP::RULES::EXEC) {
		next unless ($mr->{'ship'});
		my $id = $mr->{'id'};
		my $selected = ($hash{'EXEC'} eq $id)?'selected':'';
		if ($selected) { $found++; }
		$c .= "<option value=\"$id\" $selected>$mr->{'txt'}</option>\n";
		}
	# $c = "<option>hi nick</option>";
	if ($hash{'EXEC'} eq '') {
		$c = "<option value=\"\">-- NOT CONFIGURED --</option>\n$c";
		}
	elsif (not $found) {
		$c = "<option value=\"$hash{'EXEC'}\">INVALID EXISTING: $hash{'EXEC'}</option>\n$c";
		}
	$GTOOLS::TAG{'<!-- EXEC -->'} = $c;

	$GTOOLS::TAG{"<!-- VALUE_V -->"}  = $hash{'VALUE'};
	$GTOOLS::TAG{'<!-- SCHEDULES -->'} = '';
	if ($FLAGS =~ /,WS,/) {
 		$GTOOLS::TAG{"<!-- SCHEDULES -->"}  = '<option '.(($hash{'SCHEDULE'} eq '*')?'selected':'').' value="*">Any</option>';
		foreach my $s (@{&WHOLESALE::list_schedules($USERNAME)}) {
			$GTOOLS::TAG{"<!-- SCHEDULES -->"} .= "<option ".(($hash{'SCHEDULE'} eq $s)?'selected':'')." value=\"$s\">$s</option>";
      	}
		if ($hash{'SCHEDULE'} eq '*') {
			push @MSGS, qq~WARN|+NOTE: the 'Any' setting requires a schedule be set.\n\n
If no schedule is set the rule will be ignored/skipped.<br>
The Match_All is provided as a convenience shortcut rule for stores that have many pricing schedules, <br>
but desire to have only one set of rules for all schedules.<br>
MOST IMPORTANTLY: If a customer does NOT have schedule pricing, the "Any" setting will NOT apply the rule.
</div>~;
			}
		}

  $GTOOLS::TAG{"<!-- DELETE_BUTTON -->"} = "<td><a href='rulebuilder.cgi?method=$METHOD&ACTION=DELETE&THIS=$THIS'><img border='0' src='/images/bizbuttons/delete.gif'></td>";
  $GTOOLS::TAG{"<!-- WHAT_ARE_WE_DOING -->"} = "Edit Rule $THIS";
  $template_file = "rulebuilder-edit.shtml";
  }

if ($ACTION eq "SAVE-NEW") {
	my %hash = ();
 	$hash{'NAME'} = $q->param('NAME');
  	$hash{'FILTER'} = $q->param('FILTER');
  	$hash{'EXEC'} = $q->param('EXEC');
  	$hash{'MATCH'} = $q->param('MATCH');
  	$hash{'VALUE'} = $q->param('VALUE');
  	$hash{'SCHEDULE'} = $q->param('SCHEDULE');
	$hash{'CREATED'} = &ZTOOLKIT::mysql_from_unixtime(time());

	foreach my $k (keys %hash) { print STDERR "APPEND $k\n"; }

	$LU->log("SETUP.SHIPPING.RULES","Added Rule for $METHOD","SAVE");
	&ZSHIP::RULES::append_rule($USERNAME,$PRT,$METHOD,\%hash);  
	$ACTION = "";	
	}

if ($ACTION eq "SAVE-EDIT") {
	my %hash = ();

	my $ID = $q->param('id');
	$hash{'NAME'} = $q->param('NAME');
	$hash{'FILTER'} = $q->param('FILTER');
  	$hash{'EXEC'} = $q->param('EXEC');
  	$hash{'MATCH'} = $q->param('MATCH');
	$hash{'VALUE'} = $q->param('VALUE');
	$hash{'SCHEDULE'} = $q->param('SCHEDULE');
	$hash{'MODIFIED'} = &ZTOOLKIT::mysql_from_unixtime(time());

	$LU->log("SETUP.SHIPPING.RULES","Updated Rule Content for $METHOD","SAVE");
	&ZSHIP::RULES::update_rule($USERNAME,$PRT,$METHOD,$ID,\%hash);  

	$ACTION = "";	
}


if ($ACTION eq "APPEND") {
  $GTOOLS::TAG{"<!-- NEXT_ACTION -->"} = "SAVE-NEW";
	my $c = '';
	foreach my $mr (@ZSHIP::RULES::MATCH) {
		next if ($mr->{'ship'}==0);
		my $id = $mr->{'id'};
		if ($mr->{'short'} eq '') { $mr->{'short'} = $mr->{'txt'}; }
		$c .= "<option value=\"$id\">$mr->{'short'}</option>\n";
		}
	$GTOOLS::TAG{'<!-- MATCH -->'} = $c;

	$c = '';
	foreach my $mr (@ZSHIP::RULES::EXEC) {
		next if ($mr->{'ship'}==0);
		my $id = $mr->{'id'};
		if ($mr->{'short'} eq '') { $mr->{'short'} = $mr->{'txt'}; }
		$c .= "<option value=\"$id\">$mr->{'short'}</option>\n";
		}
	$GTOOLS::TAG{'<!-- EXEC -->'} = $c;

  $GTOOLS::TAG{"<!-- ID -->"} = "";
  $GTOOLS::TAG{"<!-- NAME_V -->"} = "new rule";
  $GTOOLS::TAG{"<!-- FILTER -->"}  = "";
  $GTOOLS::TAG{"<!-- VALUE_V -->"}  = "0.00";
  $GTOOLS::TAG{'<!-- SCHEDULES -->'} = '';
  if ($FLAGS =~ /,WS,/) {
    $GTOOLS::TAG{"<!-- SCHEDULES -->"}  = '<option value="*">Any</option>';
    foreach my $s (@{&WHOLESALE::list_schedules($USERNAME)}) {
      $GTOOLS::TAG{"<!-- SCHEDULES -->"} .= "<option value=\"$s\">$s</option>";
      }
    }
  $GTOOLS::TAG{"<!-- WHAT_ARE_WE_DOING -->"} = "Create a new rule:";
  
  $template_file = "rulebuilder-edit.shtml";  
}

if ($ACTION eq "")
{

$GTOOLS::TAG{'<!-- CANCEL_LOCATION -->'} = "/biz/setup/shipping/index.cgi";

my $method = ''; my $desc = 'Unknown'; my $script = '/biz/setup/shipping/index.cgi';
## NOTE: METHOD or METHOD.### (where ### is a partition) are both valid.
if ($METHOD =~ /^SHIP-USPS_DOM(\.[\d]+)?$/) { $method = 'US Postal Service'; $desc = 'Domestic'; $script = '/biz/setup/shipping/usps.cgi'; }
elsif ($METHOD =~ /^SHIP-DHL_DOM_E(\.[\d]+)?$/) { $method = 'DHL'; $desc = 'Domestic Express'; $script = '/biz/setup/shipping/dhl.cgi'; }
elsif ($METHOD =~ /^SHIP-DHL_DOM_E(\.[\d]+)?$/) { $method = 'DHL'; $desc = 'Domestic Nextday'; $script = '/biz/setup/shipping/dhl.cgi'; }
elsif ($METHOD =~ /^SHIP-DHL_DOM_E(\.[\d]+)?$/) { $method = 'DHL'; $desc = 'Domestic Sameday'; $script = '/biz/setup/shipping/dhl.cgi'; }
elsif ($METHOD =~ /^SHIP-DHL_DOM_E(\.[\d]+)?$/) { $method = 'DHL'; $desc = 'Domestic Ground'; $script = '/biz/setup/shipping/dhl.cgi'; }
elsif ($METHOD =~ /^SHIP-DHL_DOM_E(\.[\d]+)?$/) { $method = 'DHL'; $desc = 'Domestic General'; $script = '/biz/setup/shipping/dhl.cgi'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic General'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_NEXTEARLY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Early Delivery'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_NEXTNOON(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Next Noon'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_NEXTDAY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Next Day'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_2DAY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic 2 Day'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_3DAY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic 3 Day'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_GROUND(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Ground'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_HOME_EVE(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Home Evening'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_DOM_HOME(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'Domestic Home'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_INT(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'International General'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_INT_NEXTEARLY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'International Next Day Early'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_INT_NEXTNOON(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'International Next Noon'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_INT_2DAY(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'International 2 Day'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
elsif ($METHOD =~ /^SHIP-FEDEXAPI_INT_GROUND(\.[\d]+)?$/) { $method = 'FedEx'; $desc = 'International Ground'; $script = '/biz/setup/shipping/index.cgi?VERB=FEDEX-PRT-INIT'; }
#elsif ($METHOD =~ /^SHIP-FIXED_SINGLE(\.[\d]+)?$/) { $method = 'Legacy Fixed'; $desc = 'Single Item'; $script = '/biz/setup/shipping/legacyfixed.cgi'; }
#elsif ($METHOD =~ /^SHIP-FIXED_MULTI(\.[\d]+)?$/) { $method = 'Legacy Fixed'; $desc = 'Multi Item'; $script = '/biz/setup/shipping/legacyfixed.cgi'; }
#elsif ($METHOD =~ /^SHIP-FIXED_COMBO(\.[\d]+)?$/) { $method = 'Legacy Fixed'; $desc = 'Combo Item'; $script = '/biz/setup/shipping/legacyfixed.cgi'; }
#elsif ($METHOD =~ /^SHIP-FIXED_STORE(\.[\d]+)?$/) { $method = 'Legacy Fixed'; $desc = 'Store Only'; $script = '/biz/setup/shipping/legacyfixed.cgi'; }
elsif ($METHOD =~ /^SHIP-HANDLING(\.[\d]+)?$/) { $method = 'Handling'; $desc = 'General'; $script = '/biz/setup/shipping/handling.cgi'; }
elsif ($METHOD =~ /^SHIP-INSURANCE(\.[\d]+)?$/) { $method = 'Insurance'; $desc = 'General'; $script = '/biz/setup/shipping/insurance.cgi'; }
elsif ($METHOD =~ /^SHIP-PRICE_DOM(\.[\d]+)?$/) { $method = 'Price Based'; $desc = 'Domestic'; $script = '/biz/setup/shipping/price.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLEMULTI_DOM(\.[\d]+)?$/) { $method = 'Fixed'; $desc = 'Domestic'; $script = '/biz/setup/shipping/simplemulti.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLEMULTI_CAN(\.[\d]+)?$/) { $method = 'Fixed'; $desc = 'Canada'; $script = '/biz/setup/shipping/fixed.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLEMULTI_INT(\.[\d]+)?$/) { $method = 'Fixed'; $desc = 'International'; $script = '/biz/setup/shipping/fixed.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE_DOM(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'Domestic #1'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE2_DOM(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'Domestic #2'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE4_DOM(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'Domestic #3'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE_INT(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'International #1'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE2_INT(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'International #2'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-SIMPLE4_INT(\.[\d]+)?$/) { $method = 'Simple'; $desc = 'International #3'; $script = '/biz/setup/shipping/simple.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic General'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_GND(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic Ground'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_3DS(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 3 Day'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_2DA(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 2 Day'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_2DM(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 2 Day AM'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_1DP(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 1 Day PM'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_1DA(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 1 Day AM'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_DOM_1DM(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'Domestic 1 Day Early AM'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_INT(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'International'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_INT_STD(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'International Canada'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_INT_XPR(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'International Express'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_INT_XDM(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'International Worldwide Express Plus'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-UPSAPI_INT_XPD(\.[\d]+)?$/) { $method = 'UPS'; $desc = 'International Worldwide Expedited'; $script = '/biz/setup/shipping/upsapi.cgi'; }
elsif ($METHOD =~ /^SHIP-USPS_DOM(\.[\d]+)?$/) { $method = 'US Postal Service'; $desc = 'Domestic'; $script = '/biz/setup/shipping/usps.cgi'; }
elsif ($METHOD =~ /^SHIP-USPS_INT(\.[\d]+)?$/) { $method = 'US Postal Service'; $desc = 'International'; $script = '/biz/setup/shipping/usps.cgi'; }
elsif ($METHOD =~ /^SHIP-WEIGHT_DOM(\.[\d]+)?$/) { $method = 'Weight Based'; $desc = 'Domestic'; $script = '/biz/setup/shipping/weight.cgi'; }
elsif ($METHOD =~ /^SHIP-WEIGHT_INT(\.[\d]+)?$/) { $method = 'Weight Based'; $desc = 'International'; $script = '/biz/setup/shipping/weight.cgi'; }
elsif ($METHOD =~ /^SHIP-OCL_DOM(\.[\d]+)?$/) { $method = 'OC Logistics Freight'; $desc = 'Domestic'; $script = '/biz/setup/shipping/oclogistics.cgi'; }
else {
	$method = "Universal ($METHOD) ";
	$desc = $method;
	my $umethod = $METHOD;
	$umethod =~ s/\.[\d]+$//g;	## remove the .1
	$umethod =~ s/SHIP-//g;
	$script = '/biz/setup/shipping/universal.cgi?VERB=EDIT&ID='.$umethod;
	}

$GTOOLS::TAG{"<!-- METHOD_DESC -->"} = $method.' Shipping';  
$GTOOLS::TAG{"<!-- CANCEL_LOCATION -->"} = $script;
push @BC, { name=>$method.' Shipping', link=>'/biz/setup/shipping/'.$script, };
push @BC, { name=>$desc.' Rules', };


print STDERR "Running..\n";
my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,$METHOD);
my $c = "";
my $counter = 0;
print STDERR "Parsing ".scalar(@rules)." rules\n";

if (scalar(@rules)>0) {
	my $maxcount = scalar(@rules);
	print STDERR "rulebuilder.cgi Found ".scalar(@rules)."\n";
	$c .= "<tr class='zoovytableheader'>";
	$c .= "<td >ID</td><td >Change</td>";
	$c .= "<td >Matching Rule</td><td>Filter</td><td>Action</td>";
	$c .= "<td >Value</td>";
	$c .= "<td >Rule Name</td>";
   $c .= "<td >Price Sched.</td></tr>";

	for (my $counter=0; $counter<scalar(@rules); $counter++) {
		my $rulehash = $rules[$counter];
		my $MATCH = ''; my $EXEC = '';
	
		foreach my $mr (@ZSHIP::RULES::MATCH) {
			next if ($mr->{'ship'}==0);
			if ($rulehash->{'MATCH'} eq $mr->{'id'}) { $MATCH = $mr->{'txt'}; }
			}

		foreach my $mr (@ZSHIP::RULES::EXEC) {
			next if ($mr->{'ship'}==0);
			if ($rulehash->{'EXEC'} eq $mr->{'id'}) { $EXEC = $mr->{'txt'}; }
			}
	

	
		$c .= "<tr><td class='A'>$counter</td><td class='A'>";
		# Print the UP arrow
		if ($counter>0) { $c .= "<a href='/biz/setup/shipping/rulebuilder.cgi?ACTION=UP&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Down' src='images/up.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='16' width='16'>"; }
		$c .= '&nbsp;';
		# Print the DOWN arrow
		if (($counter<$maxcount-1) && ($maxcount>1)) { $c .= "<a href='/biz/setup/shipping/rulebuilder.cgi?ACTION=DOWN&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Up' src='images/down.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='16' width='16'>"; }
		$c .= '&nbsp;';
		$c .= "<a href='/biz/setup/shippping/rulebuilder.cgi?ACTION=EDIT&method=$METHOD&THIS=$counter'><img border='0' alt='Change' src='images/change.gif'></a>";
		$c .= "</td><td class='A'>".$MATCH."</td>";
		$c .= "<td class='A'>".$rulehash->{'FILTER'}."</td>";
		$c .= "<td class='A'>".$EXEC."</td>";
		$c .= "<td class='A'>".$rulehash->{'VALUE'}."</td>";
		$c .= "<td class='A'>".$rulehash->{'NAME'}."</td>";
		$c .= "<td class='A'>".$rulehash->{'SCHEDULE'}."</td></tr>";
		print STDERR "Ran here!\n";
		}

  } else {
	  $c .= "<tr><td><div class=\"warning\">No rules have been defined.</div></td></tr>";
  }
$GTOOLS::TAG{"<!-- EXISTING_RULES -->"} = $c;
$GTOOLS::TAG{"<!-- RULE_COUNT -->"} = $counter;
$template_file = "rulebuilder.shtml";

}

} # end of FLAG != RBASE


&GTOOLS::output(
	title=>"Shipping: Rule Builder",
	help=>"#50339",
	file=>$template_file,
	jquery=>1,
	msgs=>\@MSGS,
	header=>1,
	bc=>\@BC);

