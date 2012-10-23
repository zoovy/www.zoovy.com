#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require WHOLESALE;
require NAVCAT;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $ACTION = $ZOOVY::cgiv->{'ACTION'};
if ($ACTION eq '') { $ACTION = $ZOOVY::cgiv->{'VERB'}; }


my $template_file = 'index.shtml';
if ($FLAGS !~ /,WS,/) {  
	my ($helplink, $helphtml) = GTOOLS::help_link('Wholesale Pricing Schedule Webdoc',50512);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;
	$template_file = 'deny.shtml'; 
	$ACTION = 'DENY';
	}
##
##
##	


if ($ACTION eq 'SAVE') {
	my %S = ();
	$S{'SID'} = uc(substr($ZOOVY::cgiv->{'SID'},0,4));
	$S{'SID'} =~ s/[^\w]+//gs;
	$S{'TITLE'} = $ZOOVY::cgiv->{'title'};
	$S{'discount_amount'} = $ZOOVY::cgiv->{'discount_amount'};
	$S{'discount_amount'} = &WHOLESALE::sanitize_formula($S{'discount_amount'});
	$S{'discount_default'} = ($ZOOVY::cgiv->{'chk_discount_default'} eq 'on')?1:0;

	if (not $LU->is_level(7)) {
		## currency requires level 8.
		$ZOOVY::cgiv->{'currency'} = '';
		$ZOOVY::cgiv->{'chk_realtime_products'} = '';
		$ZOOVY::cgiv->{'chk_dropship_invoice'} = '';
		$ZOOVY::cgiv->{'chk_export_inventory'} = '';
		}
	if (not $LU->is_level(8)) {
		## currency requires level 8.
		$ZOOVY::cgiv->{'currency'} = '';
		$ZOOVY::cgiv->{'chk_realtime_inventory'} = '';
		$ZOOVY::cgiv->{'chk_realtime_orders'} = '';
		$ZOOVY::cgiv->{'chk_rewards'} = '';
		}
	$S{'currency'} = $ZOOVY::cgiv->{'currency'};
	$S{'promotion_mode'} = $ZOOVY::cgiv->{'promotion_mode'};
	$S{'shiprule_mode'} = $ZOOVY::cgiv->{'shiprule_mode'};
	
	$S{'incomplete'} = ($ZOOVY::cgiv->{'chk_incomplete'} eq 'on')?1:0;
	$S{'rewards'} = ($ZOOVY::cgiv->{'chk_rewards'} eq 'on')?1:0;
	$S{'export_inventory'} = ($ZOOVY::cgiv->{'chk_export_inventory'} eq 'on')?1:0;
	$S{'realtime_orders'} = ($ZOOVY::cgiv->{'chk_realtime_orders'} eq 'on')?1:0;
	$S{'realtime_products'} = ($ZOOVY::cgiv->{'chk_realtime_products'} eq 'on')?1:0;
	$S{'realtime_inventory'} = ($ZOOVY::cgiv->{'chk_realtime_inventory'} eq 'on')?1:0;
	$S{'dropship_invoice'} = ($ZOOVY::cgiv->{'chk_dropship_invoice'} eq 'on')?1:0;
	$S{'inventory_ignore'} = ($ZOOVY::cgiv->{'chk_inventory_ignore'} eq 'on')?1:0;
	$S{'welcome_txt'} = $ZOOVY::cgiv->{'welcome_txt'};

	&WHOLESALE::save_schedule($USERNAME,\%S);
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>Saved Schedule $S{'SID'}</font><br>";
	$ACTION = '';
	}


##
##
##
if ($ACTION eq 'NUKE') {
	
	require CUSTOMER::BATCH;
	my %ref = CUSTOMER::BATCH::list_customers($USERNAME,$PRT,
		'SCHEDULE'=>$ZOOVY::cgiv->{'SID'});
	if ( (my $count = (scalar(keys %ref)))>0) {
		use Data::Dumper;
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class=error>NOTE: schedule $ZOOVY::cgiv->{'SID'} cannot be removed because it has $count customers still using it.</div><br>";
		}
	else {
		&WHOLESALE::nuke_schedule($USERNAME,$ZOOVY::cgiv->{'SID'});
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class=success>NOTE: schedule $ZOOVY::cgiv->{'SID'} has been removed.</div><br>";
		}
	$ACTION = '';
	}


##
## 
##
if ($ACTION eq 'SAVELISTS') {
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe ($NC->paths()) {
		next unless (substr($safe,0,1) eq '$');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
	
		my $changed = 0;
		if (not defined $metaref->{'WS'}) { $metaref->{'WS'} = 0; }

		if ((defined $ZOOVY::cgiv->{$safe}) && ($metaref->{'WS'}==1)) {}
		elsif ((not defined $ZOOVY::cgiv->{$safe}) && ($metaref->{'WS'}==0)) {}
		else {
			$metaref->{'WS'} = (defined $ZOOVY::cgiv->{$safe})?1:0;
			$NC->set($safe, metaref=>$metaref);
			}
		}
	$NC->save();
	undef $NC;
	$ACTION = '';
	}

##
## 
##
if (($ACTION eq 'ADD') || ($ACTION eq 'EDIT')) {


	my $SID = $ZOOVY::cgiv->{'SID'};
	my $S = {};
	if ($ACTION eq 'ADD') {
		$S->{'promotion_mode'} = 1;
		$S->{'shiprule_mode'} = 1;
		$S->{'incomplete'} = 1;
		$S->{'dropship_invoice'} = 1;
		$S->{'inventory_ignore'} = 0;
		$S->{'realtime_orders'} = 1;
		$S->{'realtime_products'} = 1;
		$S->{'realtime_inventory'} = 1;
		$S->{'export_inventory'} = 1;
		$GTOOLS::TAG{'<!-- SID_INPUT -->'} = qq~
			<input type="textbox" maxlength=4 size="4" name="SID" value=""><br>
			<font class="hint">(4 character max, allowed: A-Z/0-9)</font><br>
			<font class="hint">* If you wish to have unique quantity pricing per product the first two letters of the schedule id must be "QP"</font><br>
			<font class="hint">* If you wish to have unique minimum quantities, increment quantities (per schedule) the first two letters of the schedule id must be "MP"</font><br>
			~;
			
		}
	else {
		($S) = WHOLESALE::load_schedule($USERNAME,$SID);
		$GTOOLS::TAG{'<!-- SID_INPUT -->'} = $S->{'SID'}."<input type=\"hidden\" name=\"SID\" size=\"4\" maxlength=\"4\" value=\"$SID\">";
		$GTOOLS::TAG{'<!-- PROMO -->'} =  qq~(<a href="/biz/setup/promotions/index.cgi?METHOD=PROMO-$SID">Configure</a>)~;
		$GTOOLS::TAG{'<!-- SHIPRULES -->'} =  qq~(<a href="/biz/setup/shipping/rulebuilder.cgi?SID=$SID">Configure</a>)~;
		}
		
		
	$GTOOLS::TAG{'<!-- TITLE -->'} = $S->{'TITLE'};
	$GTOOLS::TAG{'<!-- DISCOUNT_AMOUNT -->'} = $S->{'discount_amount'};
	$GTOOLS::TAG{'<!-- CHK_DISCOUNT_DEFAULT -->'} = (($S->{'discount_default'})?'checked':'');
	if (not defined $S->{'promotion_mode'}) { $S->{'promotion_mode'} = 1; }
	$GTOOLS::TAG{'<!-- PROMOTION_MODE_0 -->'} = (($S->{'promotion_mode'}==0)?'checked':'');
	$GTOOLS::TAG{'<!-- PROMOTION_MODE_1 -->'} = (($S->{'promotion_mode'}==1)?'checked':'');
	$GTOOLS::TAG{'<!-- PROMOTION_MODE_2 -->'} = (($S->{'promotion_mode'}==2)?'checked':'');
	
	if (not defined $S->{'shiprule_mode'}) { $S->{'shiprule_mode'} = 1; }
	$GTOOLS::TAG{'<!-- SHIPRULE_MODE_0 -->'} = (($S->{'shiprule_mode'}==0)?'checked':'');
	$GTOOLS::TAG{'<!-- SHIPRULE_MODE_1 -->'} = (($S->{'shiprule_mode'}==1)?'checked':'');

	$GTOOLS::TAG{'<!-- CHK_INCOMPLETE -->'} = (($S->{'incomplete'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_REWARDS -->'} = (($S->{'rewards'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_REALTIME_ORDERS -->'} = (($S->{'realtime_orders'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_REALTIME_PRODUCTS -->'} = (($S->{'realtime_products'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_EXPORT_INVENTORY -->'} = (($S->{'export_inventory'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_REALTIME_INVENTORY -->'} = (($S->{'realtime_inventory'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_DROPSHIP_INVOICE -->'} = (($S->{'dropship_invoice'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_INVENTORY_IGNORE -->'} = (($S->{'inventory_ignore'})?'checked':'');
	$GTOOLS::TAG{'<!-- WELCOME_TXT -->'} = &ZOOVY::incode($S->{'welcome_txt'});

	$GTOOLS::TAG{'<!-- CURRENCY_USD -->'} = ($S->{'currency'} eq 'USD')?'selected':'';
	$GTOOLS::TAG{'<!-- CURRENCY_EUR -->'} = ($S->{'currency'} eq 'EUR')?'selected':'';

	if (($S->{'discount_amount'} ne '') && (not &WHOLESALE::validate_formula($S->{'discount_amount'}))) {
		$GTOOLS::TAG{'<!-- FORMULA_ERROR -->'} = "<font color='red'>There is an error in your formula - please check the documentation.</font><br>";
		}
	elsif (not $S->{'discount_default'}) {
		$GTOOLS::TAG{'<!-- FORMULA_ERROR -->'} = "<font color='red'>Warning: Without a default pricing formula, the price of each item must be set individually. HINT: You probably don't want to do this. Try using \"BASE\"</font><br>";		
		}
	
	$template_file = 'edit.shtml';
	}



if ($ACTION eq 'JEDI-BUMP') {
	my $dbh = &DBINFO::db_zoovy_connect();
	my $ID = int($ZOOVY::cgiv->{'ID'});
	my $pstmt = "update WHOLESALE_JEDI_PACKAGES set VERSION=VERSION+1 where MID=$MID and ID=$ID /* $USERNAME */";
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);
	&DBINFO::db_zoovy_close();
	$ACTION = 'JEDI';
	}

##
## creates a new jedi package.
##
if ($ACTION eq 'JEDI-ADDPACKAGE') {
	my $dbh = &DBINFO::db_zoovy_connect();
	my %x = ();
	foreach my $k ('title','visibility','about','schedule','wrapper','prt') {
		$x{$k} = $ZOOVY::cgiv->{$k};
		}
	$x{'inc_sogs'} = ($ZOOVY::cgiv->{'inc_socs'} eq 'on')?1:0;
	$x{'inc_readme'} = ($ZOOVY::cgiv->{'inc_readme'} eq 'on')?1:0;
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		next unless ($k =~ /^LAYOUT:(.*?)$/);
		$x{'layouts'} .= "|$1";
		}

	$x{'USERNAME'} = $USERNAME;
	$x{'MID'} = $MID;
	$x{'VERSION'} = 0;
	$x{'*CREATED'} = 'now()';

	my $pstmt = &DBINFO::insert($dbh,'WHOLESALE_JEDI_PACKAGES',\%x,debug=>1+2);
	$dbh->do($pstmt);
	&DBINFO::db_zoovy_close();
	$ACTION = 'JEDI';
	}

	
##
##
##
if ($ACTION eq 'JEDI') {

	my $dbh = &DBINFO::db_zoovy_connect();
	my $pstmt = "select * from WHOLESALE_JEDI_PACKAGES where MID=$MID /* $USERNAME */";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my $info = $sth->fetchrow_hashref() ) {
		my $ID = $info->{'ID'};
		my $V = $info->{'VERSION'}+1; 
		$c .= "<tr>";
		$c .= "<td>$info->{'title'}</td>";
		$c .= "<td>$info->{'PUBLISHED'}</td>";
		$c .= "<td>";
			$c .= "<a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=UTILITY&APP=JEDI_PACKAGE&GUID=JEDI-$USERNAME-$ID-$V&.type=JEDI&.package=$ID\">[Publish]</a>";
			$c .= "<a href=\"index.cgi?VERB=JEDI-BUMP&ID=$ID\">[Bump Version]</a>";
		$c .= "</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	if ($c eq '') {
		$c .= "<tr><td><i>No existing JEDI Packages, please add one.</i></td></tr>";
		}
	else {
		$c = qq~
<tr class='zoovysub1header'>
	<td>TITLE</td>
	<td>PUBLISHED</td>
	<td>ACTION</td>		
</tr>
$c
~;
		}
	&DBINFO::db_zoovy_close();
	$GTOOLS::TAG{'<!-- EXISTING_PACKAGES -->'} = $c;


	## compile list of schedules
	$c = '';
	foreach my $sid (@{&WHOLESALE::list_schedules($USERNAME)}) {
		$c .= "<option value=\"$sid\">$sid</option>";
		}
	$GTOOLS::TAG{'<!-- SIDS -->'} = $c;

	## compile list of wrappers
	$c = '';
	require TOXML::UTIL;
	my (@docs) = TOXML::UTIL::favoriteDocs($USERNAME,'WRAPPER');
	foreach my $docid (@docs) {
		$c .= "<option value=\"$docid\">$docid</option>";
		}
	$GTOOLS::TAG{'<!-- WRAPPERS -->'} = $c;

	require TOXML::UTIL;
	$c = '';
	my ($docsref) = TOXML::UTIL::listDocs($USERNAME,'LAYOUT',DETAIL=>0,SORT=>1);
	foreach my $docref (@{$docsref}) {
		next if ($docref->{'MID'}<=0);
		my $docid = $docref->{'DOCID'};
		
		next if (substr($docid,0,1) ne '~');
		$c .= "<input type=checkbox name=\"LAYOUT:$docid\">$docid<br>";
		}
	if ($c eq '') {
		$c = '<i>No custom favorite layouts available</i>';
		}
	$GTOOLS::TAG{'<!-- LAYOUTS -->'} = $c;

	##
	##	
	$c = '';
	require ZWEBSITE;
	my ($prts) = &ZWEBSITE::list_partitions($USERNAME);
	foreach my $prtpretty (@{$prts}) {
		my ($prt) = split(/:/,$prtpretty);
		$c .= "<option value=\"$prt\">$prtpretty</option>";
		}
	$GTOOLS::TAG{'<!-- PRTS -->'} = $c;


	$template_file = 'jedi.shtml';
	}


if ($ACTION eq 'SAVE-SIGNUP') {
	require WHOLESALE::SIGNUP;
	
	my ($cfg) = &WHOLESALE::SIGNUP::load_config($USERNAME,$PRT);

	$cfg->{'v'} = 1;
	$cfg->{'saveinfo'} = "$LUSERNAME|".&ZTOOLKIT::pretty_date(time(),2);
	$cfg->{'json'} = $ZOOVY::cgiv->{'json'};
	$cfg->{'initial_schedule'} = $ZOOVY::cgiv->{'initial_schedule'};
	$cfg->{'enabled'} = ($ZOOVY::cgiv->{'enabled'})?1:0;
	$cfg->{'auto_lock'} = ($ZOOVY::cgiv->{'auto_lock'})?1:0;
	$cfg->{'send_email'} = ($ZOOVY::cgiv->{'send_email'})?1:0;
	$cfg->{'make_todo'} = ($ZOOVY::cgiv->{'make_todo'})?1:0;
	$cfg->{'make_ticket'} = ($ZOOVY::cgiv->{'make_ticket'})?1:0;

	&WHOLESALE::SIGNUP::save_config($USERNAME,$PRT,$cfg);

	$ACTION = 'SIGNUP';
	}


if ($ACTION eq 'SIGNUP') {
	my $c = '';
	require WHOLESALE::SIGNUP;

	my ($cfg) = &WHOLESALE::SIGNUP::load_config($USERNAME,$PRT);

	$GTOOLS::TAG{'<!-- JSON -->'} = &ZOOVY::incode($cfg->{'json'});
	$GTOOLS::TAG{'<!-- CHK_ENABLED -->'} = ($cfg->{'enabled'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_AUTO_LOCK -->'} = ($cfg->{'auto_lock'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_SEND_EMAIL -->'} = ($cfg->{'send_email'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_MAKE_TODO -->'} = ($cfg->{'make_todo'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_MAKE_TICKET -->'} = ($cfg->{'make_ticket'}?'checked':'');

	foreach my $schedule (@{WHOLESALE::list_schedules($USERNAME)}) {
		my ($selected) = ($cfg->{'initial_schedule'} eq $schedule)?'selected':'';
		$GTOOLS::TAG{'<!-- SCHEDULES -->'} = "<option $selected value=\"$schedule\">$schedule</option>";		
		}

	require DOMAIN::TOOLS;
	my ($domain) = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
	$GTOOLS::TAG{'<!-- SIGNUP_LINK -->'} = "http://www.$domain/customer/signup";

	$template_file = 'signup.shtml';
	}


##
##
##
if ($ACTION eq 'LISTS') {
	## LISTS
	my $c = '';
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe ($NC->paths()) {
		next unless (substr($safe,0,1) eq '$');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);

		$c .= qq~
			<tr>
			<td><input type='checkbox' ~.(($metaref->{'WS'}==1)?'checked':'').qq~ name='$safe'></td>
			<td>$pretty</td>
			<td>($safe)</td>
			</tr>
			~;
		}
	undef $NC;
	$GTOOLS::TAG{'<!-- LISTINGS -->'} = $c;
	$template_file = 'lists.shtml';
	}

##
##
##
if ($ACTION eq '') {
	my $c = '';
	my $r = '';
	foreach my $sid (@{&WHOLESALE::list_schedules($USERNAME)}) {
		$r = ($r eq 'r0')?'r1':'r0';
		my ($S) = &WHOLESALE::load_schedule($USERNAME,$sid);
		if ($S->{'TITLE'} eq '') { $S->{'TITLE'} = "Untitled Schedule"; }
		$c .= "<tr class=\"$r\">";
		$c .= "<td><a href=\"/biz/manage/customer/index.cgi?VERB=SEARCH-NOW&scope=WS&searchfor=$sid\">Customers</a></td><td>|</td>";
		$c .= "<td><a href=\"index.cgi?ACTION=EDIT&SID=$sid\">Edit</a></td><td>|</td>";
		$c .= "<td><a href=\"index.cgi?ACTION=NUKE&SID=$sid\">Delete</a></td>";
		$c .= "<td>$sid</td>";
		$c .= "<td>$S->{'TITLE'}</td>";
		$c .= "</tr>";
		}
	
	if ($c eq '') {
		$GTOOLS::TAG{'<!-- SCHEDULES -->'} = '<i>No schedules currently exist.</i>'; 
		}
	else {
		$GTOOLS::TAG{'<!-- SCHEDULES -->'} = qq~<table>
		<option value="">none</option>
		$c
		</table>~;
		}


	$template_file = 'index.shtml';
	}


my @TABS = ();
push @TABS, { selected=>($ACTION eq '')?1:0, name=>"Schedules", link=>"/biz/utilities/wholesale/index.cgi?ACTION=" };
push @TABS, { selected=>($ACTION eq 'LISTS')?1:0, name=>"Export Lists", link=>"/biz/utilities/wholesale/index.cgi?ACTION=LISTS" };
push @TABS, { selected=>($ACTION eq 'JEDI')?1:0, name=>"JEDI", link=>"/biz/utilities/wholesale/index.cgi?ACTION=JEDI" };
push @TABS, { selected=>($ACTION eq 'SIGNUP')?1:0, name=>"Sign-Up Form", link=>"/biz/utilities/wholesale/index.cgi?ACTION=SIGNUP" };


&GTOOLS::output(
	'file'=>$template_file,
	'header'=>1,
	'tabs'=>\@TABS,
	'help'=>'#50512',
	'js'=>1,
	'bc'=>[ { 'name'=>'Utilities'}, {'name'=>'Wholesale Pricing Schedules'} ],
	);


