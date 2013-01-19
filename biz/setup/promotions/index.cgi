#!/usr/bin/perl


use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
use CGI;
require ZSHIP::RULES;
require ZWEBSITE;
use strict;
require CART::COUPON;
require CART2;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @MSGS = ();
my @BC = ();
push @BC,  { name=>'Setup',link=>'/biz/setup/index.cgi' };
push @BC,  { name=>'Promotions &amp; Coupons',link=>'/biz/setup/promotions/index.cgi' };

my %FONTS = (
	'1'=>'<b><h2>',
	'32'=>'<font color="blue">',
	'64'=>'<font color="blue" size=-1>',
	'128'=>"<font color='#777777' size='1'><pre>",
	);

my $THIS = $ZOOVY::cgiv->{'THIS'};

my $webdb = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
my $VERB = $ZOOVY::cgiv->{'VERB'};
if ($VERB eq '') { 

 	if ($webdb->{"promotion_advanced"} && $FLAGS =~ /,XSELL,/ ) {
		$VERB = 'UBER'; 
		}
	else {	
		$VERB = 'SIMPLE'; 
		}
	}

my $template_file = '';

## SIMPLE open to everyone
## COUPONS, UBER only open to XSELL
if ($FLAGS !~ /,XSELL,/ && $VERB ne 'SIMPLE') { 
	$template_file = 'deny.shtml'; $VERB='DENY'; 
	}

my $METHOD = 'PROMO';
if ($ZOOVY::cgiv->{'METHOD'} ne '') { $METHOD = $ZOOVY::cgiv->{'METHOD'}; }
elsif ($ZOOVY::cgiv->{'method'} ne '') { $METHOD = $ZOOVY::cgiv->{'method'}; }

#if (($PRT>0) && ($METHOD !~ /\.[\d]+$/)) {
#	## PARTITION METHODS always have a .### to them
#	$METHOD = "$METHOD.$PRT";
#	}

my $HELP = '#50313';
$GTOOLS::TAG{'<!-- METHOD -->'} = $METHOD;
if ($METHOD =~ /PROMO\-(.*?)$/) {
  $GTOOLS::TAG{'<!-- SID -->'} = $1;
  }



if ($VERB eq 'RUN-DEBUG') {
	$VERB = 'DEBUGGER';


	my $ERROR = '';
	if ($ZOOVY::cgiv->{'ORDER'} ne '') {
		my $orderid = $ZOOVY::cgiv->{'ORDER'};
		$SITE::CART2 = CART2->new_from_oid($USERNAME,$orderid);
		}
	elsif ($ZOOVY::cgiv->{'CARTID'}) {
		$SITE::CART2 = CART2->new_from_persist($USERNAME,$PRT,$ZOOVY::cgiv->{'CARTID'},'is_fresh'=>0);
		delete $SITE2::CART->{'@DEBUG'};
		}

	my $DEBUG = 0;
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		next unless ($k =~ /detail_([\d]+)/);
		$DEBUG |= int($1);
		}

	if ((defined $SITE::CART2) && (ref($SITE::CART2) eq 'CART2')) {
		my $out = '';
		$out .= "<tr><td>DEBUG LEVEL: $DEBUG</td></tr>";

		require LISTING::MSGS;
		my $lm = LISTING::MSGS->new($USERNAME);
		$SITE::CART2->msgs($lm);

		$ZSHIP::DEBUG = $DEBUG;
		$SITE::CART2->recalc(debug=>$DEBUG);

		foreach my $line (@{$lm->msgs()}) {
			#my ($class,$level,$msg) = split(/\|/,$line,3);	
			#$msg = &ZOOVY::incode($msg);
			#my $WIDTH = $level;
			#if ($WIDTH == 2) { $WIDTH = 4; } 
			#elsif ($WIDTH == 4) { $WIDTH = 8; }
			#elsif ($WIDTH == 8) { $WIDTH = 12; }
			#$out .= "<tr><td><table><td><img src='/images/blank.gif' width='$WIDTH' height='1'></td><td>$FONTS{$level}$msg</td></tr></table></td></tr>\n";
		
			my ($msg,$status) = &LISTING::MSGS::msg_to_disposition($line);
			next if ($msg->{'TYPE'} eq 'SHIP');
			# $out .= Dumper($msg);
			$out .= "<tr><td>$msg->{'_'}</td><td>$msg->{'+'}</td></tr>";
			}

		# $out .= Dumper($lm);

		$GTOOLS::TAG{'<!-- OUTPUT -->'} = $out;		
		}
	else {
		$ERROR = "CART undefined!";
		}

	if ($ERROR ne '') {
		push @MSGS, "ERROR|$ERROR";
		}

	if ($ERROR) {
		}
	elsif ($ZOOVY::cgiv->{'detail_255'}) {
		use Data::Dumper;
		$GTOOLS::TAG{'<!-- CART -->'} = Dumper($SITE::CART2);
		}
	else {
		$GTOOLS::TAG{'<!-- CART -->'} = '<i>Not displayed at this detail level.</i>';
		}
	$VERB = 'DEBUGGER';
	}



if ($VERB eq 'DEBUGGER') {

	$GTOOLS::TAG{'<!-- DETAIL_2 -->'} = (defined $ZOOVY::cgiv->{'detail_2'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_16 -->'} = (defined $ZOOVY::cgiv->{'detail_16'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_32 -->'} = (defined $ZOOVY::cgiv->{'detail_32'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_64 -->'} = (defined $ZOOVY::cgiv->{'detail_64'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_128 -->'} = (defined $ZOOVY::cgiv->{'detail_128'})?'checked':'';
	$GTOOLS::TAG{'<!-- DETAIL_255 -->'} = (defined $ZOOVY::cgiv->{'detail_255'})?'checked':'';

	$GTOOLS::TAG{'<!-- ORDER -->'} = (defined $ZOOVY::cgiv->{'ORDER'})?&ZOOVY::incode($ZOOVY::cgiv->{'ORDER'}):'';
	$GTOOLS::TAG{'<!-- CARTID -->'} = (defined $ZOOVY::cgiv->{'CARTID'})?&ZOOVY::incode($ZOOVY::cgiv->{'CARTID'}):'';

	$template_file = 'debug.shtml';
	}


if ($VERB eq 'UBER-SAVE') {	
	print STDERR "Running SAVEADV\n";
	$webdb->{'promotion_advanced'} = 0;
	if (defined($ZOOVY::cgiv->{'promotion_advanced'})) { $webdb->{"promotion_advanced"} = 1; }
	$LU->log("SETUP.PROMO","Configured Advanced Promotions","SAVE");
   &ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
	$VERB = 'UBER';
	}

if ($VERB eq "UBER-DELETE") {
	$LU->log("SETUP.PROMO","Deleted Promotion for $METHOD","SAVE");
   &ZSHIP::RULES::delete_rule($USERNAME,$PRT, $METHOD,$THIS);
   $VERB = 'UBER';
	}

if ($VERB eq "UBER-UP") {
 	&ZSHIP::RULES::swap_rule($USERNAME,$PRT, $METHOD,$THIS,$THIS-1);
 	$VERB = 'UBER';
	}

if ($VERB eq "UBER-DOWN") {
  	my $this = $ZOOVY::cgiv->{'THIS'};
 	my $next = $ZOOVY::cgiv->{'NEXT'};
	&ZSHIP::RULES::swap_rule($USERNAME,$PRT,$METHOD,$THIS,$THIS+1);
 	$VERB = 'UBER';
 	 }


##
## this code is run to prepare edit_rule.shtml for editing an existing rule.
##
if ($VERB eq "UBER-EDIT") {
	$HELP = '#50337';
	$GTOOLS::TAG{"<!-- ID -->"} = $THIS;
	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,$METHOD);

	push @BC, { name=>"Uber Editor", link=>"/biz/setup/promotions/index.cgi?VERB=UBER-EDIT&ID=$THIS" };

	my %hash = ();
	if ($THIS == -1) {
		$hash{'NAME'} = "New Rule";
		$hash{'VALUE'} = "0.00";
		$GTOOLS::TAG{"<!-- WHAT_ARE_WE_DOING -->"} = "Create a new rule:";
		}
	else {
		%hash = %{$rules[$THIS]};
		$GTOOLS::TAG{"<!-- DELETE_BUTTON -->"} = qq~<td>
<button class="button" onClick="navigateTo('/biz/setup/promotions/index.cgi?method=$METHOD&VERB=UBER-DELETE&THIS=$THIS');">Delete</button>
</td>
~;
		$GTOOLS::TAG{"<!-- WHAT_ARE_WE_DOING -->"} = "Edit Rule $THIS";
		}

	my $c = '';
	foreach my $ref (@ZSHIP::RULES::MATCH) {
		next if ($ref->{'uber'}==0);
		my $selected = (($ref->{'id'} eq $hash{'MATCH'})?'selected':'');
		if ($ref->{'txt'} eq '') { $ref->{'txt'} = $ref->{'short'}; }
		$c .= "<option $selected value=\"$ref->{'id'}\">$ref->{'txt'}</option>";
		}
	$GTOOLS::TAG{'<!-- MATCH -->'} = $c;

	$c = '';
	foreach my $ref (@ZSHIP::RULES::EXEC) {
		next if ($ref->{'uber'}==0);
		my $selected = (($ref->{'id'} eq $hash{'EXEC'})?'selected':'');
		$c .= "<option $selected value=\"$ref->{'id'}\">$ref->{'txt'}</option>";
		}
	$GTOOLS::TAG{'<!-- EXEC -->'} = $c;

  	$GTOOLS::TAG{"<!-- NAME_V -->"} = &ZOOVY::incode($hash{'NAME'});
  	$GTOOLS::TAG{"<!-- FILTER -->"}  = &ZOOVY::incode($hash{'FILTER'});
	$GTOOLS::TAG{"<!-- MATCHVALUE -->"} = &ZOOVY::incode($hash{'MATCHVALUE'});
	$GTOOLS::TAG{"<!-- IMAGE -->"} = &ZOOVY::incode($hash{'IMAGE'});
	if ((not defined $hash{'IMAGE'}) || ($hash{'IMAGE'} eq '')) { $hash{'IMAGE'} = 'blank'; }
	$GTOOLS::TAG{"<!-- THUMBURL -->"} = &GTOOLS::imageurl($USERNAME,$hash{'IMAGE'},50,50,'FFFFFF',1);
	
	$GTOOLS::TAG{"<!-- VALUE_V -->"}  = $hash{'VALUE'};
	$GTOOLS::TAG{"<!-- MATCHVALUE -->"}  = $hash{'MATCHVALUE'};
	$GTOOLS::TAG{"<!-- CODE -->"}  = $hash{'CODE'};

	if ( (!defined($hash{'TAX'})) || ($hash{'TAX'} eq '')) { $hash{'TAX'}='N'; }
	if ($hash{'TAX'} eq 'N') { 
		$GTOOLS::TAG{'<!-- TAX_CB -->'} = ''; 
		$GTOOLS::TAG{'<!-- TAX_WARNING -->'} = "<font color='red'>Warning: tax does NOT apply to this promotion.</font>";
		}
	else { 
		$GTOOLS::TAG{'<!-- TAX_CB -->'} = ' CHECKED'; 
		}

	$GTOOLS::TAG{'<!-- WEIGHT_V -->'} = $hash{'WEIGHT'};
	
	$template_file = "uber-edit.shtml";
	}

##
## 
##
if ($VERB eq "UBER-EDITSAVE") {
	my %hash = ();

	my $ID = int($ZOOVY::cgiv->{'id'});

	$hash{'IMAGE'} = $ZOOVY::cgiv->{'IMAGE'};
	$hash{'MATCH'} = $ZOOVY::cgiv->{'MATCH'};
 	$hash{'NAME'} = $ZOOVY::cgiv->{'NAME'};
  	$hash{'FILTER'} = $ZOOVY::cgiv->{'FILTER'};
  	$hash{'EXEC'} = $ZOOVY::cgiv->{'EXEC'};
  	$hash{'VALUE'} = $ZOOVY::cgiv->{'VALUE'};

	my $CODE = $ZOOVY::cgiv->{'CODE'};
	$CODE =~ s/[\W]+//sg;
	$hash{'CODE'} = $CODE;

	my $WEIGHT = $ZOOVY::cgiv->{'WEIGHT'};
	$WEIGHT =~ s/[^\d]+//g;
	$hash{'WEIGHT'} = $WEIGHT;

	if (defined($ZOOVY::cgiv->{'TAX'})) { $hash{'TAX'} = 'Y'; }  else { $hash{'TAX'} = 'N'; }
	$hash{'MATCHVALUE'} = $ZOOVY::cgiv->{'MATCHVALUE'};

	foreach my $k (keys %hash) { print STDERR "APPEND $k\n"; }
	
	if ($ID == -1) {
		&ZSHIP::RULES::append_rule($USERNAME,$PRT, $METHOD,\%hash);  
		}
	else {
		&ZSHIP::RULES::update_rule($USERNAME,$PRT, $METHOD,$ID,\%hash);  
		}
	$VERB = "UBER";	
	}



if ($VERB eq 'UBER') {
	if ($METHOD eq 'PROMO') { $GTOOLS::TAG{'<!-- METHOD_DESC -->'} = 'Promotion Rules'; }


	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,$METHOD);
	if ( (my $sizeof = &ZOOVY::sizeof(\@rules)) > 50000) {
		push @MSGS, "WARNING|Uber promotions are using $sizeof bytes of database space.\n\nThis is more than the recommended allocation of 25,000 bytes.\n";
		}
	if ( (my $rulecount = scalar(@rules)) > 75) {		
		push @MSGS, "WARNING|There are $rulecount uber promotions.\n\nThis is more than the recommended maximum of 50 rules.\n";
		}

	if ($webdb->{"promotion_advanced"}>0) { 
		$GTOOLS::TAG{"<!-- CHECKED_PROMOTION_ADVANCED -->"} = " CHECKED ";

		my $c = "";
		my $counter = 0;
		print STDERR "Parsing ".scalar(@rules)." rules\n";

		my $r = 'r0';	
		if (scalar(@rules)>0) {

			my %PROMO_EXEC = (); foreach my $ref (@ZSHIP::RULES::EXEC) { $PROMO_EXEC{ $ref->{'id'} } = $ref->{'txt'}; }
			my %PROMO_MATCH = (); foreach my $ref (@ZSHIP::RULES::MATCH) { $PROMO_MATCH{ $ref->{'id'} } = $ref->{'txt'}; }

			my $maxcount = scalar(@rules);	

			$c .= "<tr><td class='zoovysub1header'>ID</td><td class='zoovysub1header'>Change</td>";
			$c .= "<td class='zoovysub1header'>Code: Rule Name</td>";
			$c .= "<td class='zoovysub1header'>Matching Rule</td><td class='zoovysub1header'>Action</td>";
		#	$c .= "<td class='zoovysub1header'>Value</td><td class='zoovysub1header'>Filter</td>";
		#	$c .= "<td class='zoovysub1header'>Rule Name</td></tr>";

			my $r = 'r0';
			foreach my $ruleref (@rules) {
				$r = ($r eq 'r0')?'r1':'r0';

				my $MATCH = $PROMO_MATCH{ $ruleref->{'MATCH'} };
				if (not defined $MATCH) { $MATCH = '***No Rule Action Description specified***'.$ruleref->{'MATCH'}; }
				my $EXEC = $PROMO_EXEC{ $ruleref->{'EXEC'} };
				if (not defined $EXEC) { $EXEC = '***Invalid Execution Content specified***'.$ruleref->{'EXEC'}; }

				$MATCH =~ s/(the )?filter/$ruleref->{'FILTER'}/gs;
				$MATCH =~ s/MATCH VALUE/$ruleref->{'MATCHVALUE'}/gs;
				$EXEC =~ s/modify value/$ruleref->{'VALUE'}/gs;

				$c .= "<tr class=\"$r\">";
				$c .= "<td valign=top  class='A'>$counter</td>";
				$c .= "<td valign=top  class='A' nowrap>";
				# Print the UP arrow
				if ($counter>0) { $c .= "<a href='/biz/setup/promotions/index.cgi?VERB=UBER-UP&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Up' src='/biz/images/arrows/v_up-20x26.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='26' width='20'>"; }
				$c .= '&nbsp;';
				# Print the DOWN arrow
				if (($counter<$maxcount-1) && ($maxcount>1)) { $c .= "<a href='/biz/setup/promotions/index.cgi?VERB=UBER-DOWN&method=$METHOD&THIS=$counter'><img border='0' alt='Move Rule Down' src='/biz/images/arrows/v_down-20x26.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='26' width='20'>"; }
				$c .= '&nbsp;';
				$c .= "<a href='/biz/setup/promotions/index.cgi?VERB=UBER-EDIT&method=$METHOD&THIS=$counter'><img border='0' alt='Change' src='/biz/images/arrows/v_edit-20x26.gif'></a>";$c .= "</td>";
				$c .= "<td valign=top  class='A'>";

				if (($ruleref->{'IMAGE'} ne '') && ($ruleref->{'IMAGE'} ne '<!-- IMAGE -->')) {
					my $thumburl = &GTOOLS::imageurl($USERNAME,$ruleref->{'IMAGE'},50,50,'FFFFFF',1);
					$c .= qq~<img border=0 height=50 width=50 src="$thumburl"><br>~;  
					}
			
				my $tmp = $ruleref->{'CODE'}.": ".$ruleref->{'NAME'};
				$tmp =~ s/\,[\s]*/\, /g;
				$c .= $tmp."</td>";

				$MATCH =~ s/,[\s]*/\, /g;
				$MATCH =~ s/[\n\r]+/<br>/g;
				$c .= "<td valign=top  class='A'>".$MATCH."</td>";
				$EXEC =~ s/,[\s]*/\, /g;
				$c .= "<td valign=top  class='A'>".$EXEC."</td>";
		#		$c .= "<td valign=top  class='A'>".$ruleref->{'VALUE'}."</td>";
				#$c .= "<td valign=top  class='A'>".$ruleref->{'FILTER'}."</td>";
		#		$c .= "<td valign=top  class='A'>".$ruleref->{'NAME'}."</td></tr>";
				$counter++;
				}

			} else {
			$c .= "<tr><td valign=top  bgcolor='FFFFFF'>No rules have been defined.</td></tr>";
			}
		$GTOOLS::TAG{'<!-- ADDNEW -->'} = '<tr><td valign=top  bgcolor="white" colspan="8"><a href="/biz/setup/promotions/index.cgi?method='.$METHOD.'&VERB=UBER-EDIT&THIS=-1">Add a new Rule</a></td></tr>';

		$GTOOLS::TAG{"<!-- EXISTING_RULES -->"} = $c;
		$GTOOLS::TAG{"<!-- RULE_COUNT -->"} = $counter;
		}
	else 
		{ 
		$GTOOLS::TAG{"<!-- CHECKED_PROMOTION_ADVANCED -->"}  = ""; 
		$GTOOLS::TAG{'<!-- RULE_COUNT -->'} = 0;
		$GTOOLS::TAG{'<!-- EXISTING_RULES -->'} = '';
		}

	$GTOOLS::TAG{'<!-- CANCEL -->'} = '<a href="/biz/setup/" TARGET="_top"><img border="0" src="/images/bizbuttons/cancel.gif"></a>&nbsp;&nbsp;&nbsp; ';

	## link for WEBDOC
	my ($helplink, $helphtml)= GTOOLS::help_link('Promotion Rules', 50337);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helplink;


	if ($METHOD =~ /PROMO\-(.*?)$/) {
	    my $SID = $1;
	    $template_file = 'main-schedule.shtml'; 
	    $GTOOLS::TAG{'<!-- CANCEL -->'} = "<a href=\"/biz/manage/schedules/index.cgi?VERB=UBER-EDIT&SID=$SID\"><img border=\"0\" src=\"/images/bizbuttons/cancel.gif\"></a>&nbsp;&nbsp;&nbsp;"; 
	    }

	$template_file = 'index-uber.shtml';
	}












if ($VERB eq "SIMPLE-SAVE") {
	push @MSGS, "SUCESS|Changes saved";

	if (uc($ZOOVY::cgiv->{'promotion_discount'}) eq "ON") { $webdb->{"promotion_discount"} = 1; } else { $webdb->{"promotion_discount"} = 0; }
   if (uc($ZOOVY::cgiv->{'promotion_freeshipping'}) eq "ON") { $webdb->{"promotion_freeshipping"} = 1; } else { $webdb->{"promotion_freeshipping"} = 0; }
	if (uc($ZOOVY::cgiv->{'promotion_external'}) eq "ON") { $webdb->{"promotion_external"} = 1; } else { $webdb->{"promotion_external"} = 0; }

   $webdb->{"promotion_freeshipping_amount"} = $ZOOVY::cgiv->{'promotion_freeshipping_amount'}; 
	$webdb->{"promotion_freeshipping_amount"} =~ s/[^0-9\.]+//igs;
   $webdb->{"promotion_discount_amount"} = $ZOOVY::cgiv->{'promotion_discount_amount'};
	$webdb->{"promotion_discount_amount"} =~ s/[^0-9\.\%]+//igs;
   $webdb->{"promotion_discount_after"} = $ZOOVY::cgiv->{'promotion_discount_after'};
	$webdb->{"promotion_discount_after"} =~ s/[^0-9\.]+//igs;
	$LU->log("SETUP.PROMO","Update Simple Promotions","SAVE");
   &ZWEBSITE::save_website_dbref($USERNAME,$webdb,$PRT);
	$VERB = 'SIMPLE';
   }

if ($VERB eq 'SIMPLE') {
	if ($webdb->{"promotion_freeshipping"}>0)
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_FREESHIPPING -->"} = " CHECKED "; }
	else 
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_FREESHIPPING -->"}  = ""; }

	if ($webdb->{"promotion_discount"}>0)
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_DISCOUNT -->"} = " CHECKED "; }
	else 
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_DISCOUNT -->"}  = ""; }

	if ($webdb->{"promotion_external"}>0)
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_EXTERNAL -->"} = " CHECKED "; }
	else 
		{ $GTOOLS::TAG{"<!-- CHECKED_PROMOTION_EXTERNAL -->"}  = ""; }


	if ( ($webdb->{'promotion_freeshipping'} || $webdb->{'promotion_discount'}) 
			&& $webdb->{'promotion_advanced'}) {
		push @MSGS, "ERROR|You cannot have both simple promotions and advanced (uber) promotions enabled at the same time.";
		}

	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_FREESHIPPING_AMOUNT -->"} = " VALUE=\"".$webdb->{"promotion_freeshipping_amount"}."\" ";
	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_DISCOUNT_AMOUNT -->"} = " VALUE=\"".$webdb->{"promotion_discount_amount"}."\" ";
	$GTOOLS::TAG{"<!-- VALUE_PROMOTION_DISCOUNT_AFTER -->"} = " VALUE=\"".$webdb->{"promotion_discount_after"}."\" ";
	$template_file = 'index-simple.shtml';
	}




if ($VERB eq 'COUPON-RULE-DELETE') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($ID) = int($ZOOVY::cgiv->{'ID'});
   &ZSHIP::RULES::delete_rule($USERNAME,$PRT,"COUPON-$CODE",$ID);
   $VERB = 'COUPON-EDIT';
	}
	
if ($VERB eq 'COUPON-RULE-UP') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($ID) = int($ZOOVY::cgiv->{'ID'});
 	&ZSHIP::RULES::swap_rule($USERNAME,$PRT,"COUPON-$CODE",$ID,$ID-1);
   $VERB = 'COUPON-EDIT';
	}

if ($VERB eq 'COUPON-RULE-DOWN') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($ID) = int($ZOOVY::cgiv->{'ID'});
 	my $next = $ZOOVY::cgiv->{'NEXT'};
	&ZSHIP::RULES::swap_rule($USERNAME,$PRT,"COUPON-$CODE",$ID,$ID+1);
   $VERB = 'COUPON-EDIT';
	}

if ($VERB eq 'COUPON-RULE-SAVE') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($ID) = int($ZOOVY::cgiv->{'ID'});

	my %hash = ();
	$hash{'CODE'} = $CODE;
	$hash{'HINT'} = $ZOOVY::cgiv->{'HINT'};
	$hash{'MATCH'} = $ZOOVY::cgiv->{'MATCH'};
  	$hash{'FILTER'} = $ZOOVY::cgiv->{'FILTER'};
  	$hash{'EXEC'} = $ZOOVY::cgiv->{'EXEC'};
  	$hash{'VALUE'} = $ZOOVY::cgiv->{'VALUE'};
	$hash{'MATCHVALUE'} = $ZOOVY::cgiv->{'MATCHVALUE'};

	if ($ID == -1) {
		&ZSHIP::RULES::append_rule($USERNAME,$PRT,"COUPON-$CODE",\%hash);  
		}
	else {
		&ZSHIP::RULES::update_rule($USERNAME,$PRT,"COUPON-$CODE",$ID,\%hash);  
		}
   $VERB = 'COUPON-EDIT';
	}


if ($VERB eq 'COUPON-RULE-ADD') {
	$ZOOVY::cgiv->{'ID'} = -1;
	$VERB = 'COUPON-RULE-EDIT';
	}

if (($VERB eq 'COUPON-RULE-EDIT')) {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	my ($ID) = int($ZOOVY::cgiv->{'ID'});
	$GTOOLS::TAG{"<!-- ID -->"} = $ID;

	push @BC, { name=>"Coupons", link=>'/biz/setup/promotions/index.cgi?VERB=COUPON' };
	push @BC, { name=>"Coupon $CODE", link=>"/biz/setup/promotions/index.cgi?VERB=COUPON-EDIT&CODE=$CODE" };
	push @BC, { name=>"Rule $ID", link=>"/biz/setup/promotions/index.cgi?VERB=COUPON-RULE-EDIT&CODE=$CODE&ID=$ID" };
		
	my %hash = ();
	$hash{'CODE'} = $ID;
	if ($ID==-1) {
		$hash{'HINT'} = 'New Rule';
		}
	else {
		my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,"COUPON-$CODE");
		%hash = %{$rules[$ID]};
		$GTOOLS::TAG{"<!-- DELETE_BUTTON -->"} = qq~
<td>
<button class="button" onClick="navigateTo('/biz/setup/promotions/index.cgi?CODE=$CODE&VERB=COUPON-RULE-DELETE&ID=$ID');">Delete</button></td>~;

		}

	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
	$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;
	$GTOOLS::TAG{'<!-- HINT -->'} = &ZOOVY::incode($hash{'HINT'});
  	$GTOOLS::TAG{"<!-- FILTER -->"}  = &ZOOVY::incode($hash{'FILTER'});
	$GTOOLS::TAG{"<!-- MATCHVALUE -->"} = &ZOOVY::incode($hash{'MATCHVALUE'});
	$GTOOLS::TAG{"<!-- VALUE_V -->"}  = $hash{'VALUE'};

	my $c = '';
	foreach my $ref (@ZSHIP::RULES::MATCH) {
		next if ($ref->{'cpn'}==0);
		my $selected = (($ref->{'id'} eq $hash{'MATCH'})?'selected':'');
		$c .= "<option $selected value=\"$ref->{'id'}\">$ref->{'txt'}</option>";
		}
	$GTOOLS::TAG{'<!-- MATCH -->'} = $c;

	$c = '';
	foreach my $ref (@ZSHIP::RULES::EXEC) {
		next if ($ref->{'cpn'}==0);
		my $selected = (($ref->{'id'} eq $hash{'EXEC'})?'selected':'');
		$c .= "<option $selected value=\"$ref->{'id'}\">$ref->{'txt'}</option>";
		}
	$GTOOLS::TAG{'<!-- EXEC -->'} = $c;


	$template_file = 'coupon-ruleedit.shtml';
	}


if ($VERB eq 'COUPON-NEW') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	if ($CODE eq '') { $ZOOVY::cgiv->{'CODE'} = substr(time(),-5); }
	CART::COUPON::add($USERNAME,$PRT,$ZOOVY::cgiv->{'CODE'});
	$LU->log("SETUP.PROMO","Created Coupon $CODE","SAVE");
	$VERB = 'COUPON-EDIT'; 
	}

if ($VERB eq 'COUPON-SAVE') {
	require Date::Parse;

	my $CODE = $ZOOVY::cgiv->{'CODE'};
	my %ref = ();

	$ref{'begins_gmt'} = 0;
	if ($ZOOVY::cgiv->{'begins'} ne '') {
		$ref{'begins_gmt'} = Date::Parse::str2time($ZOOVY::cgiv->{'begins'});
		}
	$ref{'expires_gmt'} = 0;
	if ($ZOOVY::cgiv->{'expires'} ne '') {
		$ref{'expires_gmt'} = Date::Parse::str2time($ZOOVY::cgiv->{'expires'});
		}

	$ref{'taxable'} = ($ZOOVY::cgiv->{'taxable'})?1:0;
	$ref{'stackable'} = ($ZOOVY::cgiv->{'stackable'})?1:0;
	$ref{'disabled'} = ($ZOOVY::cgiv->{'disable'})?1:0;
	$ref{'limiteduse'} = ($ZOOVY::cgiv->{'limiteduse'})?1:0;
	$ref{'title'} = $ZOOVY::cgiv->{'title'};
	$ref{'profile'} = $ZOOVY::cgiv->{'profile'};
	$ref{'image'} = $ZOOVY::cgiv->{'IMAGE'};

	CART::COUPON::save($USERNAME,$PRT,$CODE,%ref);
	$LU->log("SETUP.PROMO","Updated/Saved Coupon $CODE","SAVE");
	$VERB = 'COUPON-EDIT';
	}


if ($VERB eq 'COUPON-DELETE') {
	require Date::Parse;

	my $CODE = $ZOOVY::cgiv->{'CODE'};
	CART::COUPON::delete($USERNAME,$PRT,$CODE);
	$LU->log("SETUP.PROMO","Deleted Coupon for $CODE","SAVE");

	$VERB = 'COUPON';
	}



if ($VERB eq 'COUPON-EDIT') {
	my ($CODE) = $ZOOVY::cgiv->{'CODE'};
	$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;

	require Date::Parse;
	require POSIX;

	push @BC, { name=>"Coupons", link=>'/biz/setup/promotions/index.cgi?VERB=COUPON' };
	push @BC, { name=>"Coupon $CODE", link=>"/biz/setup/promotions/index.cgi?VERB=COUPON-EDIT&CODE=$CODE" };

	my ($cpnref) = &CART::COUPON::load($USERNAME,$PRT,$CODE);
	$GTOOLS::TAG{'<!-- CB_DISABLED -->'} = ($cpnref->{'disabled'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_LIMITEDUSE -->'} = ($cpnref->{'limiteduse'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_TAXABLE -->'} = ($cpnref->{'taxable'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_STACKABLE -->'} = ($cpnref->{'stackable'})?'checked':'';
	$GTOOLS::TAG{'<!-- TITLE -->'} = &ZOOVY::incode($cpnref->{'title'});

	$GTOOLS::TAG{'<!-- BEGINS -->'} = '';
	if ($cpnref->{'begins_gmt'}>0) {
		$GTOOLS::TAG{'<!-- BEGINS -->'} = POSIX::strftime("%m/%d/%Y %H:%M:%S",localtime($cpnref->{'begins_gmt'}));
		}
	
	$GTOOLS::TAG{'<!-- EXPIRES -->'} = '';
	if ($cpnref->{'expires_gmt'}>0) {
		$GTOOLS::TAG{'<!-- EXPIRES -->'} = POSIX::strftime("%m/%d/%Y %H:%M:%S",localtime($cpnref->{'expires_gmt'}));
		}
	
	$GTOOLS::TAG{'<!-- IMAGE -->'} = &ZOOVY::incode($cpnref->{'image'});
	if ((not defined $cpnref->{'image'}) || ($cpnref->{'image'} eq '')) { $cpnref->{'image'} = 'blank'; }
	$GTOOLS::TAG{"<!-- THUMBURL -->"} = &GTOOLS::imageurl($USERNAME,$cpnref->{'image'},50,50,'FFFFFF',1);

#<!--
#	<tr>
#		<td valign="top">Profile:</td>
#		<td valign="top">
#			<select name="profile">
#				<option value="">** ALL **</option>
#				<!-- PROFILES_SELECT -->
#			</select>
#			<div class="hint">HINT: Coupon code is only available when on a site using this profile.</div>
#		</td>
#	</tr>
#-->

#	my $c = '';
#	require DOMAIN::TOOLS;
#	my ($profilesref ) = DOMAIN::TOOLS::syndication_profiles($USERNAME);
#	foreach my $k (sort keys %{$profilesref}) {
#		my ($selected) = ($k eq $cpnref->{'profile'})?'selected':'';
#		$c .= "<option $selected value=\"$k\">$k</option>";
#		}
#	$GTOOLS::TAG{'<!-- PROFILES_SELECT -->'} = $c;


	my @rules = &ZSHIP::RULES::fetch_rules($USERNAME,$PRT,"COUPON-$CODE");
	if ( (my $sizeof = &ZOOVY::sizeof(\@rules)) > 2500) {
		push @MSGS, "WARNING|This coupon is more than 2500 bytes. Try using product tagging to reduce the size of the coupon and get some performance.";
		}

	if (1) { 
		my $counter = 0;
		my $c = '';
		if (scalar(@rules)>0) {
			my %PROMO_EXEC = (); foreach my $ref (@ZSHIP::RULES::EXEC) { $PROMO_EXEC{ $ref->{'id'} } = $ref->{'txt'}; }
			my %PROMO_MATCH = (); foreach my $ref (@ZSHIP::RULES::MATCH) { $PROMO_MATCH{ $ref->{'id'} } = $ref->{'txt'}; }

			my $maxcount = scalar(@rules);	

			$c .= "<tr><td class='zoovysub1header'>ID</td><td class='zoovysub1header'>Change</td>";
			$c .= "<td class='zoovysub1header'>HINT</td>";
			$c .= "<td class='zoovysub1header'>Matching Rule</td><td class='zoovysub1header'>Action</td>";

			my $r = '';
			foreach my $ruleref (@rules) {
				$r = ($r eq 'r0')?'r1':'r0';

				my $MATCH = $PROMO_MATCH{ $ruleref->{'MATCH'} };
				if (not defined $MATCH) { $MATCH = '***Invalid Matching Content specified***'; }
				my $EXEC = $PROMO_EXEC{ $ruleref->{'EXEC'} };
				if (not defined $EXEC) { $EXEC = '***Invalid Execution Content specified***'.$ruleref->{'EXEC'}; }

				$MATCH =~ s/(the )?filter/$ruleref->{'FILTER'}/gs;
				$MATCH =~ s/MATCH VALUE/$ruleref->{'MATCHVALUE'}/gs;
				$EXEC =~ s/modify value/$ruleref->{'VALUE'}/gs;

				$c .= "<tr class=\"$r\">";
				$c .= "<td valign=top >$counter</td>";
				$c .= "<td valign=top nowrap>";
				# Print the UP arrow
				if ($counter>0) { $c .= "<a href='/biz/setup/promotions/index.cgi?VERB=COUPON-RULE-UP&CODE=$CODE&ID=$counter'><img border='0' alt='Move Rule Up' src='/biz/images/arrows/v_up-20x26.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='26' width='20'>"; }
				$c .= '&nbsp;';
				# Print the DOWN arrow
				if (($counter<$maxcount-1) && ($maxcount>1)) { $c .= "<a href='/biz/setup/promotions/index.cgi?VERB=COUPON-RULE-DOWN&CODE=$CODE&ID=$counter'><img border='0' alt='Move Rule Down' src='/biz/images/arrows/v_down-20x26.gif'></a>"; } else { $c .= "<img src='/images/blank.gif' height='26' width='20'>"; }
				$c .= '&nbsp;';
				$c .= "<a href='/biz/setup/promotions/index.cgi?VERB=COUPON-RULE-EDIT&CODE=$CODE&ID=$counter'><img border='0' alt='Change' src='/biz/images/arrows/v_edit-20x26.gif'></a>";
				$c .= "</td>";
				$c .= "<td valign=top>$ruleref->{'HINT'}</td>";
				$MATCH =~ s/,/, /g;
				$c .= "<td valign=top>".$MATCH."</td>";
				$c .= "<td valign=top>".$EXEC."</td>";
				$counter++;
				}

			} else {
			$c .= "<tr><td bgcolor='FFFFFF'><font color='red'>No rules have been defined - this coupon will not do anything.</font></td></tr>";
			}

		$GTOOLS::TAG{"<!-- EXISTING_RULES -->"} = $c;
		$GTOOLS::TAG{"<!-- RULE_COUNT -->"} = $counter;
		}
	
	$template_file = 'coupon-edit.shtml';	
	}


if ($VERB eq 'COUPON') {
	push @BC, { name=>"Coupons", link=>'/biz/setup/promotions/index.cgi?VERB=COUPON' };

	my $results = CART::COUPON::list($USERNAME,$PRT);	
	if ( (my $sizeof = &ZOOVY::sizeof($results)) > 100000) {
		push @MSGS, "WARNING|You have $sizeof bytes allocated to coupons - which is more than recommended 100,000 bytes of coupons.\n\nTry and reduce the number and/or size of each coupon.";
		}
	if ( (my $count = scalar(@{$results})) >200) {
		push @MSGS, "WARNING|You have $count coupons - this more than the recommended 250 coupons.\n\nThis number seems excessive, you're probably using coupons in a way other than how they were intended.";
		}

	my $c = '';
	my $row = 'r0';
	foreach my $ref (@{$results}) {
		$row = ($row eq 'r0')?'r1':'r0';
		if ($ref->{'title'} eq '') { $ref->{'title'} = "<i>COUPON NAME NOT CURRENTLY CONFIGURED!</i>"; }
		my $info = '';
		if ($ref->{'disabled'}>0) {
			$info = "<b>DISABLED</b>";
			}
		elsif ($ref->{'expires_gmt'}<$^T) {
			$info = "<b>EXPIRED</b>";
			}
		else {
			$info = "<b>ACTIVE</b>";
			}

		$c .= "<tr class=\"$row\">";
		$c .= "<td><button onClick=\"navigateTo('/biz/setup/promotions/index.cgi?VERB=COUPON-EDIT&CODE=$ref->{'code'}');\"><img border='0' alt='Change' src='/biz/images/arrows/v_edit-20x26.gif'></button></td>";
		$c .= "<td>$ref->{'code'}</td>";
		$c .= "<td>$ref->{'title'}</td>";
		my $stackable = ($ref->{'stackable'})?'Yes':'No';
		$c .= "<td>$stackable</td>";
		$c .= "<td>$info</td>";
		$c .= "</tr>";
		}
	if ($c eq '') { 
		$c = "<tr><td colspan=5><i>There are currently no coupons configured.</i></td></tr>"; 
		}
	else {
		$c = "<tr class=\"zoovysub1header\"><td>&nbsp;</td><td>CODE</td><td>TITLE</td><td width=100>STACKABLE</td><td> STATUS</td></tr>".$c;
		}

	$GTOOLS::TAG{'<!-- COUPONS -->'} = $c;
	$template_file = 'index-coupon.shtml';
	}




my @TABS = ();
push @TABS, { name=>'Simple', selected=>($VERB eq 'SIMPLE')?1:0, link=>'/biz/setup/promotions/index.cgi?VERB=SIMPLE', };
push @TABS, { name=>'Coupons', selected=>($VERB =~ /COUPON/)?1:0, link=>'/biz/setup/promotions/index.cgi?VERB=COUPON', };
push @TABS, { name=>'Uber Promotions', selected=>($VERB =~ /UBER/)?1:0, link=>'/biz/setup/promotions/index.cgi?VERB=UBER', };
push @TABS, { name=>'Debugger',selected=>($VERB eq 'DEBUGGER')?1:0, link=>'/biz/setup/promotions/index.cgi?VERB=DEBUGGER', };
#push @TABS, { name=>'API',selected=>($VERB eq 'API')?1:0, link=>'/biz/setup/promotions/index.cgi?VERB=API', };


print STDERR Dumper(\@BC);

&GTOOLS::output(
   'title'=>'Setup : Promotions : '.$PRT,
   'file'=>$template_file,
   'header'=>'1',
   'help'=>$HELP,
	'jquery'=>'1',
	'bc'=>\@BC,
   'tabs'=>\@TABS, 
	'msgs'=>\@MSGS,
	'js'=>1,
   );





