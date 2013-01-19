#!/usr/bin/perl

use encoding 'utf8';		## tells us to internally use utf8 for all encoding
use locale;  
use utf8 qw();
use Encode qw();
use strict;	
use Data::Dumper;

use lib '/httpd/modules';
require ZOOVY;
require TOXML::UTIL;
require LUSER;

##
##
#          'session_id' => 'brian@wcmcweWuRKlawHJkyhILj4u1p@588089@eric@AMZ,API2,APPAREL,BASIC,BETA,CRM,EBAY,PKG=STORE,SC,SHIP,SINCE=2000,STAFF,WEB,WS,XSELL,ZOM,ZPM,_S=255,_P=255,_O=255,_M=255,ADMIN',
#          'data' => 'format=&docid=swirls-yellow',

## pass:
##		v=1 version 1
##			u=username
##			m=method e.g MODULE/Function?k1=v1&k2=v2 OR MODULE/Function and then data=k1%3Dv1%26k2%3Dv2
##			
##		OR

&ZOOVY::init(1);
#$ZOOVY::cgiv = $cgi->parse_form_data;
#foreach my $k (keys %{$ZOOVY::cgiv}) {
#	if (utf8::is_utf8($ZOOVY::cgiv->{$k}) eq '') {
#		$ZOOVY::cgiv->{$k} = Encode::decode("utf8",$ZOOVY::cgiv->{$k});
#		utf8::decode($ZOOVY::cgiv->{$k});
#		}
#	}
#$ZOOVY::cookies = $cgi->parse_cookies;

#close STDOUT;
#open STDOUT, '>>', '/tmp/foo' 
#  or die "Couldn't redirect STDERR: $!";


use CGI;
my $q = new CGI; my ($p);
foreach $p ($q->param())  { 
	my ($x) = $q->param($p);
	if (utf8::is_utf8($x) eq '') {
		$x = Encode::decode("utf8",$x);
		utf8::decode($x);
		}
	$ZOOVY::cgiv->{$p} = $x;
	## fixes an issue with YAML encoding.

#	print STDERR "Q:$p $ZOOVY::cgiv->{$p}\n";
	$ZOOVY::cgiv->{$p} =~ s/\r\n/\n/gs;	
	}
foreach $p ($q->cookie()) { $ZOOVY::cookies->{$p} = $q->cookie($p); }
# print STDERR Dumper($ZOOVY::cgiv, $ZOOVY::cookies);



my %options = ();
$options{'raw'} = 1;
foreach my $param (keys %{$ZOOVY::cgiv}) {
	next if (substr($param,0,1) ne '_');
	$options{$param} = $ZOOVY::cgiv->{$param};
	}

my ($LU) = LUSER->authenticate(%options);
my ($ERR,$ERRMSG) = (0);

if ($ERR>0) {}
elsif (not defined $LU) { ($ERR,$ERRMSG) = (-1,"Received undefined LUSER object"); }
elsif (ref($LU) ne 'LUSER') { ($ERR,$ERRMSG) = (-1,"Received invalid LUSER object"); }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = ();
if ($ERR==0) {
	($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
	if ($MID<=0) { ($ERR,$ERRMSG) = (-2,"Received invalid MID from LUSER->authinfo"); }
	}

my ($LOGIN) = $USERNAME.(($LUSERNAME ne '')?'*'.$LUSERNAME:'');

#my $SESSION = $ZOOVY::cookies->{'session_id'};
#if (not defined $SESSION) { $SESSION = $ZOOVY::cgiv->{'session_id'}; }	## CGI Lite has bugs!
#my ($USERNAME,$TOKEN,$DBID,$RESELLER,$FLAGS) = split('@',$SESSION);
#my ($LOGIN) = $USERNAME;
#print STDERR "SESSION: $SESSION\n";

#my $LUSER = '';
#($USERNAME,$LUSER) = split(/\*/,$USERNAME);
#if (not defined $LUSER) { $LUSER = ''; }
#my $MID = &ZOOVY::resolve_mid($USERNAME);

my ($METHOD,$SUB) = split('/',$ZOOVY::cgiv->{'m'},2);
my $VERSION = $ZOOVY::cgiv->{'v'};

my $dref = undef;
if ($ERR!=0) {
	$METHOD = "FATAL-ERROR";
	}
elsif (($ZOOVY::cgiv->{'data'} eq '') && (defined $ZOOVY::cgiv->{'data'}) && (defined $SUB) && (index($SUB,'?')>=0)) {
	$dref = &ZTOOLKIT::urlparams($SUB);	
	$SUB = substr($SUB,0,index($SUB,'?'));
	foreach my $k (keys %{$dref}) {
		$dref->{$k} =~ s/\r\n/\n/gso;	
		}
	}
elsif (substr($ZOOVY::cgiv->{'data'},0,1) eq '?') {
	$dref = &ZTOOLKIT::urlparams($ZOOVY::cgiv->{'data'});
	foreach my $k (keys %{$dref}) {
		$dref->{$k} =~ s/\r\n/\n/gso;	
		}
	}
else {
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		$dref->{$k} = $ZOOVY::cgiv->{$k};
		$dref->{$k} =~ s/\r\n/\n/gso;	
		if (ref($dref->{$k}) eq 'ARRAY') { $dref->{$k} = $dref->{$k}[0]; }
		}
	}


# print STDERR Dumper(\%ENV,$ZOOVY::cgiv);
my $out = '';
$dref->{'_FLAGS'} = $FLAGS;

# print STDERR "[$USERNAME] AJAX METHOD: $METHOD SUB: $SUB [$SESSION]\n";
# print STDERR Dumper(\%ENV,$dref);

#foreach my $k (keys %{$dref}) {	
	# $dref->{$k} = decode("iso-8859-1", $dref->{$k});		# leaves 1 A
	# Encode::from_to($dref->{$k}, "iso-8859-1", "utf8"); # creates two AA
#	$octets = encode_utf8($dref->{$k});
#	if (! Encode::is_utf8($dref->{$k})) {
#		Encode::encode_utf8($dref->{$k});
#		print STDERR "upgraded $k\n";
#		}
#	else {
#		print STDERR "skipped $k\n";
#		}
#	}
#print STDERR Dumper($dref);


#if ($METHOD eq 'EVENTMGR') {
#	require EVENT::PANELS;
#
#
#	$SUB = uc($SUB);
#	my $id = int($dref->{'_id'});
#	my $html = &EVENT::PANELS::EventEdit($dref);
#	# 'hello world! '.$SUB.' '.Dumper($dref);
#
#	$out = "?m=loadcontent&div=myDiv&html=".&js_encode($html);
#	}
#
#
#if ($METHOD eq 'SYNDICATION') {
#	
#	die();
#
#	}


print STDERR Dumper($METHOD,$ZOOVY::cgiv)."\n";

##
##
##
if ($METHOD eq 'POWERLISTER') {
	require EBAY2::POWER;
	$SUB = uc($SUB);
	my $id = int($dref->{'_id'});
	my $sku = $dref->{'_sku'};
	my $requuid = $dref->{'requuid'};
	my $udbh = &DBINFO::db_user_connect($USERNAME);
	
	require LISTING::EVENT;
	my $VERB = '';
	if ($SUB eq 'NUKE') { $VERB = 'END'; $SUB = 'INFO'; }
	if ($SUB eq 'CLEANUP') { $VERB = 'CLEANUP'; }

	my $LAUNCH_MESSAGE = '';
	if ($VERB ne '') {
		my ($le) = LISTING::EVENT->new(USERNAME=>$USERNAME,LUSER=>$LUSERNAME,
			REQUEST_APP=>'PWRMANAGE',
			REQUEST_APP_UUID=>$requuid,
			SKU=>$sku,
			QTY=>0,
			TARGET=>"POWERLISTER",
			TARGET_UUID=>$id,
			TARGET_LISTINGID=>$id,
			PRT=>$PRT,
			VERB=>$VERB,LOCK=>1);
			$le->dispatch($udbh);
		$LAUNCH_MESSAGE = $le->html_result();
		$out .= "?m=loadcontent&div=$id!info&html=".&js_encode($LAUNCH_MESSAGE);
		}


	#if ($SUB eq 'NUKE') {
	#	my ($le) = 
	#	&EBAY2::POWER::delete_channel($id,$USERNAME);		
	#	}

	#if ($SUB eq 'CLEANUP') {
	#	&EBAY2::POWER::cleanup_channel($id,$USERNAME);
	#	$SUB = 'INFO';
	#	}

	if ($SUB eq 'SAVE') {
		$SUB = 'INFO';		
	
		## effectively we initialize a new hashref with each of the fields on the form
		my %dataref = ();
		foreach my $id (split(/\|/,$dref->{'_fields'})) { $dataref{$id} = ''; }

	
		## then we pull a list of fields from powerfields for those fields on the form
		my @FIELDS = EBAY2::POWER::powerfields(\%dataref);
		
		## then we save it to dataref
		PRODUCT::FLEXEDIT::save($USERNAME,$sku,\@FIELDS,\%dataref,$dref);
		&EBAY2::POWER::info_panel_save($USERNAME,$id,$dref,\%dataref);
		}

	if ($SUB eq 'INFO') {		
		require EBAY2::PANELS;
		my $html = $LAUNCH_MESSAGE;
		$html .= &EBAY2::POWER::info_panel($USERNAME,$id);
		$html .= '<br><table border=0 cellspacing=0 cellpadding=5><tr><td>';
		my $queryset = &EBAY2::POWER::queryset($USERNAME,$id);
		$html .= &EBAY2::PANELS::listings_panel($USERNAME,0,$queryset)."<br>";
		$html .= '</td></tr></table>';
		
		$out .= "?m=loadcontent&div=$id!info&html=".&js_encode($html);
		}
	&DBINFO::db_user_close();

	# print STDERR "OUT: $out\n";
	}


##
##
##
#if ($METHOD eq 'LAUNCHGROUP') {
#	require LISTING::GROUP;
#	$SUB = uc($SUB);
#	my $uuid = int($dref->{'_id'});
#	if ($SUB eq 'SAVE') {
#		&LISTING::GROUP::info_panel_save($USERNAME,$LUSERNAME,$uuid,$dref);
#		$SUB = 'INFO';
#		}
#
#	if ($SUB eq 'NUKE') {
#		&LISTING::GROUP::set_hold($USERNAME,$uuid,2);
#		}
#
#	if (($SUB eq 'HOLD') || ($SUB eq 'UNHOLD')) {
#		&LISTING::GROUP::set_hold($USERNAME,$uuid, ($SUB eq 'HOLD')?1:0 );
#		}
#
#	if ($SUB eq 'INFO') {
#		my $html = &LISTING::GROUP::info_panel($USERNAME,$uuid,title=>"Edit Launch Group (ID: $uuid)", 
#			saveClick=>qq~saveForm('$uuid!thisFrm');~,
#			deleteClick=>qq~deleteMe('$uuid');~,
#			);		
#		my $stats = &LISTING::GROUP::info_stats($USERNAME,$uuid);
#		$html = qq~<table width=100%><tr><td valign='top'><form id="$uuid!thisFrm" name="$uuid!thisFrm"><input type="hidden" name="m" value="LAUNCHGROUP/Save"><input type="hidden" name="_id" value="$uuid">~.$html.qq~</form></td><td valign='top'>$stats</td></tr></table>~;
#		$out .= "?m=loadcontent&div=$uuid!info&html=".&js_encode($html);
#		}
#	elsif ($SUB eq 'LIST') {
#		my $select = $dref->{'select'};	
#		# print STDERR "SELECT:[$select]\n";
#		my ($html,$ajaxref) = &LISTING::GROUP::src2_options($USERNAME,$dref->{'type'});
#		# $out .= "?m=loadcontent&div=$select&html=".&js_encode($html);
#		$out .= "?m=loadselect&id=$select&".&serialize_hashref($ajaxref);
#		}
#	}
#

##
##
##
########################################################################
#if ($METHOD eq 'ORDERS') {
#	require ORDER::BATCH;
#	require ORDER::PANELS;
#	my $PANEL = $dref->{'_panel'};		
#	my $OID = $dref->{'_oid'};
#	if ($OID eq '') { $OID = $dref->{'oid'}; }
#	my $LU = undef;
#	require ORDER::INCOMPLETE;
#	require GTOOLS::Table;
#	$SUB = uc($SUB);
#
#	my ($o) = ORDER->new($USERNAME,$OID);
#	if ($SUB eq 'LOAD') {
#		## we save the panel state here so we don't save each time the user presses save.
#		if (defined $LU) { $LU->set('orders.'.$PANEL,1); $LU->save(); }
#		}
#
#	if (($SUB eq 'SAVE') || ($SUB eq 'CLOSE')) {
#		if (defined $ORDER::PANELS::func{$PANEL}) {
#			$ORDER::PANELS::func{$PANEL}->($USERNAME,$o,'save',$dref,LUSER=>$LUSERNAME);	
#			}
#		else {
#			die("requested save on panel: $PANEL (which does not exist!)");
#			}
#		if ($SUB eq 'CLOSE') {
#			if (defined $LU) { $LU->set('orders.'.$PANEL,0); $LU->save(); }
#			}
#		}
#
#	if (($SUB eq 'LOAD') || ($SUB eq 'SAVE')) {
#		my $html = '';
#		if (not defined $ORDER::PANELS::func{$PANEL}) {
#			$html .= "<font color='red'>Error: panel $PANEL could not be found!</font>";
#			}
#		else {
#			($html) = $ORDER::PANELS::func{$PANEL}->($USERNAME,$o,'',$dref,LUSER=>$LUSERNAME);
#			}
#		# $out = "?m=loadcontent&div=$PANEL!content&html=".&js_encode($html);
#		$out = "?m=loadcontent&div=panel!$PANEL&html=".&js_encode($html);
#		}
#
#
#	if ($SUB eq 'CHANGEPOOL') {
#		$o->set_attrib('pool',$dref->{'pool'});
#		# print STDERR "POOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOL: ".Dumper($dref,$o)."\n";
#		$o->save();
#		$SUB = 'VIEW';
#		}
#
#	if ($SUB eq 'SAVENOTE') {
#		my $CUSTOMER = undef;
#		if ($ZOOVY::cgiv->{'NOTE'} ne '') {
#			$CUSTOMER->save_note($LUSERNAME,$ZOOVY::cgiv->{'NOTE'});
#			}
#		$SUB = 'VIEW';
#		}
#
#	if ($SUB eq 'VIEW') {
#		$out .= "?m=loadcontent&div=panel!body&html=";
#		# $out .= &js_encode(&ORDER::PANELS::viewOrder($USERNAME,$dref->{'oid'}));
#		$out .= &js_encode(&ORDER::PANELS::viewOrder($USERNAME,$dref->{'oid'},undef,$o));
#		}
#
###	if ($SUB eq 'TAB') {
##		## gets passed: tab=
##		my $STATUS = $dref->{'tab'};
##
##		$out = "?m=loadcontent&div=header!tabs&html=".&js_encode(&GTOOLS::generateTabs(undef,ORDER::PANELS::buildTabs($USERNAME,$STATUS),1));
##		if ($STATUS eq 'INCOMPLETE') {
##			my ($set,$statusref,$createdref) = &ORDER::INCOMPLETE::list_items($USERNAME,'');
##			$out .= "?m=loadcontent&div=order_table&html=".&js_encode(&GTOOLS::Table::buildIncompleteTable($USERNAME,$STATUS,$set));
##			}
##		else {
##			my ($orderset,$statusref,$createdref) = &ORDER::BATCH::list_orders($USERNAME, $STATUS ,0,5000);
##			$out .= "?m=loadcontent&div=order_table&html=".&js_encode(&GTOOLS::Table::buildOrderTable($USERNAME,$STATUS,$orderset));
##			}
##		}
#	}
#
#
###
###
###
#########################################################################
if ($METHOD eq 'PREFERENCE') {
	$SUB = uc($SUB);

	if ($SUB eq 'SET') {
		my $changed = 0;
		foreach my $k (keys %{$dref}) {
			if ($k =~ /SET\:(.*?)$/) {
				my $property = $1;
				# print STDERR "Setting $property to $dref->{$k}\n";
				$LU->set($property,$dref->{$k}); $changed++;
				}
			}
		if ($changed) { $LU->save(); }
		}
	}



##
##
########################################################################
if (($METHOD eq 'PRODEDIT') || ($METHOD eq 'DOMAINEDIT') || ($METHOD eq 'BUILDEREDIT')) {
	# print STDERR 'dref: '.Dumper($dref);

	my $PANEL = $dref->{'_panel'};		
	my $PID = $dref->{'_pid'};
	$SUB = uc($SUB);
	my $PANELSFUNC = undef;
	my $statevar = '';
	my $objref = undef;
	my $FUNC = undef;


	if ($METHOD eq 'BUILDEREDIT') {
		require DOMAIN;
		require DOMAIN::PANELS;
		($FUNC,my $NS) = split(/:/,lc($PANEL));		
		$statevar = 'builder.'.$PANEL;		
		$PANELSFUNC = \%DOMAIN::PANELS::func; 
		# print STDERR "NS:$NS\n";
		$objref = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);
		# print STDERR "WTF: $objref->{'zoovy:profile'}\n";
		} 
	#elsif ($METHOD eq 'PRODEDIT') {
	#	require PRODUCT::PANELS;
	#	$statevar = 'prodedit.'.$PANEL;		
	#	$FUNC = $PANEL;
	#	$PANELSFUNC = \%PRODUCT::PANELS::func; 
	#	$objref = &ZOOVY::fetchproduct_as_hashref($USERNAME,$PID);
	#	}
	elsif ($METHOD eq 'PRODEDIT') {
		require PRODUCT::PANELS;
		$statevar = 'prodedit.'.$PANEL;		
		$FUNC = $PANEL;
		# $PANELSFUNC = \%PRODUCT::PANELS::func;
		my $PANELSREF = &PRODUCT::PANELS::get_panelref($PANEL);
		$PANELSFUNC = { $PANEL => $PANELSREF->{'func'} };
		$objref = PRODUCT->new($LU,$PID);
		}
	elsif ($METHOD eq 'DOMAINEDIT') {
		require DOMAIN;
		require DOMAIN::PANELS;
		($FUNC,my $DOMAINNAME) = split(/:/,lc($PANEL));		
		$statevar = 'domain.'.$PANEL;		
		$PANELSFUNC = \%DOMAIN::PANELS::func; 
		$objref = DOMAIN->new($USERNAME,$DOMAINNAME);
		}

	##
	# print STDERR "SUB: $SUB [PID: $PID]\n";
	if ($SUB eq 'LOAD') {
		## we save the panel state here so we don't save each time the user presses save.
		if (defined $LU) { $LU->set($statevar,1); $LU->save(); }
		}

	if (($SUB eq 'SAVE') || ($SUB eq 'CLOSE')) {
		if (not defined $PANELSFUNC->{$FUNC}) {
			die("requested save on panel: $PANEL (which does not exist!) FUNCTION:$FUNC");
			}
		elsif ($METHOD eq 'PRODEDIT') {
			$PANELSFUNC->{$FUNC}->($LU,$objref,'SAVE',$dref,PRT=>$PRT);
			}
		else {
			$PANELSFUNC->{$FUNC}->($LU,$PID,'SAVE',$objref,$dref,PRT=>$PRT);
			}
		if ($SUB eq 'CLOSE') {
			if (defined $LU) { 
				$LU->set($statevar,0); $LU->save(); 
				}
			}
		}

	##
	# if (($SUB eq 'LOAD') || ($SUB eq 'SAVE')) {
	if ($SUB ne 'CLOSE') {
		if (($SUB eq 'LOAD') || ($SUB eq 'SAVE')) { $SUB = ''; $dref = {}; }
		my $html = '';
		if (not defined $PANELSFUNC->{$FUNC}) {
			($html) = "<font color='red'>Error: panel $PANEL could not be found! (function: $FUNC)</font>";
			}
		elsif ($METHOD eq 'PRODEDIT') {
			($html) = $PANELSFUNC->{$FUNC}->($LU,$objref,$SUB,$dref,PRT=>$PRT);
			}
		else {
			# print STDERR "SUB: $SUB [PID: $PID]\n";
			($html) = $PANELSFUNC->{$FUNC}->($LU,$PID,$SUB,$objref,$dref,PRT=>$PRT);
			}
		## $html = &ZTOOLKIT::stripUnicode($html);	## NECESSARY FOR EBAY RESPONSE
		$out = "?m=loadcontent&div=$PANEL!content&html=".&js_encode($html);
		}

	#open F, ">/tmp/x";
	#print F "OUT: $out\n";
	#close F;
	}



##
##
###################################################################################
if ($METHOD eq 'PRODFINDER') {
	require PRODUCT::FINDER;
	$SUB = uc($SUB);

	if ($SUB eq 'NEW') {		
		## requires: div,src

		print STDERR 'DEFREF'.Dumper($dref)."\n";

		my $div = $dref->{'div'};	# the div we are going to update.
		my ($html) = PRODUCT::FINDER::buildMain($USERNAME,$PRT,$SUB,$dref);
		$out = "?m=loadcontent&div=$div&html=".&js_encode($html)."\n";
		# $out .= "?m=eval&js=".&js_encode("PF(\"PF/$div\",\"$dref->{'src'}\");")."\n";
		}

	# print STDERR "SUB: $SUB\n";

	if ($SUB eq 'SHOWMORE') {
		my ($html) = PRODUCT::FINDER::showMore($USERNAME,$PRT,$SUB,$dref);
		my $ID = $dref->{'id'};
		my $div = "$ID!results";
		$out = "?m=loadcontent&div=$div&html=".&js_encode($html) . "\n" . $out;
		}
	elsif (($SUB eq 'SHOWLIST') || ($SUB eq 'SHOWCAT')) {
		my ($html) = PRODUCT::FINDER::showItems($USERNAME,$PRT,$SUB,$dref);
		my $ID = $dref->{'id'};
		my $div = "$ID!results";
		$out = "?m=loadcontent&div=$div&html=".&js_encode($html) . "\n" . $out;
		}
	
	if (($SUB eq 'INSERT') || ($SUB eq 'REMOVE') || ($SUB eq 'FLIP')) {		
		## saves the currently selected products based on the source.
		# print STDERR Dumper($USERNAME,$SUB,$dref);
		my ($prodstr,$sortby) = PRODUCT::FINDER::doAction($USERNAME,$PRT,$SUB,$dref);
		}

	if ($SUB eq 'LOAD') {
		my $ID = $dref->{'id'};
		my ($html) = &PRODUCT::FINDER::loadPids($USERNAME,$PRT,$SUB,$dref);		
#		if ($dref->{'btn'} ne 'current') {
#			$html .= qq~<input type="button" class="button" onClick="value=" Add All ">~;
#			}

		my $div = "$ID!results";
		# $out = "?m=loadcontent&div=$div&html=".&js_encode($html) . "\n" . $out;
		$out = "?m=loadcontent&div=$div&html=".&js_encode($html) . "\n" . $out;
		}

	# print STDERR "OUT: $out\n";
	}


##
##
##
if ($METHOD eq 'NAVCAT') {
	require NAVCAT;
	require NAVCAT::CHOOSER;

	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	my $safe = $dref->{'safe'};

	# print STDERR Dumper($dref);

	if ($SUB eq 'Delete') {
		$NC->nuke($safe); 
		$safe = $NC->parentOf($safe);		# go up a level in the tree.
		# print STDERR "NEW SAFE: $safe\n";
		}	

	if ($SUB eq 'Rename') {
		my $pretty = $dref->{'pretty'};
		$NC->set($safe, pretty=>$pretty);
		$safe = $NC->parentOf($safe);
		}


	if ($SUB eq 'Add') {
		my $pretty = $dref->{'pretty'};
		my $subsafe = &NAVCAT::safename($pretty,new=>1);
		my $safe = '';
		if ($dref->{'type'} eq 'list') {
			## list
			$safe = '.';
			$NC->set( '$'.$subsafe, pretty=>$pretty);
			}
		else {
			## navcat
			$safe = $dref->{'safe'};
			# print STDERR "SAFE BEFORE: $safe\n";
			$safe = (($safe ne '.')?$safe.'.':'.').$subsafe;
			# print STDERR "Saving safe[$safe] pretty=[$pretty]\n";
			$NC->set( $safe, pretty=>$pretty);
			}
		}

	if ($SUB eq 'ShowProducts') {
		my ($pretty,$children,$products) = $NC->get($safe);
		my @pids = split(/,/,$products);
		my $html = '';
		if (scalar(@pids)>0) { 
			require GTOOLS::Table;
			($html) = &GTOOLS::Table::buildProductTable($USERNAME,\@pids);
			}
		else {
			$html = "<i>No Products Currently Exist In this Category</i>";
			}
		##
		## note: the showNavcatProducts in navcat.js looks for this to know if the products are already
		##			displayed on the page (if it finds it then a click will collapse and no Ajax method will
		##			be performed.
		$html = "<input type=\"hidden\" id=\"show_products_navcat:$safe\" value=\"1\">".$html;

		$out = "?m=loadcontent&div=~".$safe."&html=".&js_encode($html);	
		$SUB = '';
		}

	my $PID = $dref->{'_pid'};
	if (($PID eq '') || ($PID eq 'undefined')) { $PID = ''; }

	my $div = ($safe eq '.')?'_root':$safe;
	if ($SUB eq '') {
		}
	elsif ($SUB eq 'Collapse') {
		$out = "?m=loadcontent&div=".$div."&html=";
		# print STDERR "SAFE: $safe\n";
		if ($safe ne '.') {
			$out .= "?m=setGraphic&id=ICON_$safe&src=/biz/ajax/navcat_icons/miniup.gif";
			}
		if (defined $LU) { 
			$LU->set('nc:'.$safe,undef); $LU->save(); 
			}
		}
	else {
		# print STDERR "REBUILDING: $safe\n";	
		my ($html,$js) = NAVCAT::CHOOSER::buildLevel($LU, $NC, $safe, LUSER=>$LUSERNAME, product=>$PID);
		$out = "?m=loadcontent&div=".$div."&html=".&js_encode($html);
		if ($safe ne '.') {
			$out .= "?m=setGraphic&id=ICON_$safe&src=/biz/ajax/navcat_icons/minidown.gif";
			}
		if ($js ne '') { $out .= "?m=eval&js=".&js_encode($js); }
		if (defined $LU) { $LU->set('nc:'.$safe,1); $LU->save(); }
		}

#	if ($expanded ne '') {
#		print STDERR "SAFE: $safe\n";
#		my $tmpsafe = $safe.'.';
#		my $newexpanded = '';
#		foreach my $esafe (split('!',$expanded)) {		
#			next if ($esafe eq '');
#			$esafe .= '.';
#			if (($tmpsafe eq $esafe) || # the current cat
#				((length($tmpsafe) >= length($esafe)) && (substr($tmpsafe,0,length($esafe)) eq $esafe)) # a parent of ours??
#				) {
#				$newexpanded .= '!'.substr($esafe,0,-1);
#				}
#			else {
#				## this should be collapsed
#				$out .= "?m=loadcontent&html=&div=".substr($esafe,0,-1);	
#				$out .= "?m=setGraphic&id=STATE_".substr($esafe,0,-1)."&src=/biz/ajax/navcat_icons/miniup.gif";	
#				$out .= "?m=collapse&safe=".substr($esafe,0,-1);
#				print STDERR "CLOSING: [$safe] ".substr($esafe,0,-1)."\n";
#				}
#			}
#		$out .= "?m=eval&js=".&js_encode(qq~
#			\$('_catfocus').value = '$safe'; 
#			\$('_expanded').value = '$newexpanded';
#			~);
#		}

	undef $NC;
	# print STDERR "OUT: $out\n";
	}




###########################################################
## 
## website builder functions:
## parameters: page, id (the element we are targeting)
##
#if ($METHOD eq 'BUILDER') {
#	require TOXML::EDIT;
#	require TOXML::SAVE;
#	require TOXML::PREVIEW;
#	require SITE::MSGS;
#	require SITE;
#
#
#	#use Data::Dumper;
#	#print STDERR Dumper($dref);
#
#	$SUB = uc($SUB);
#	my $ID = $dref->{'id'};
#	my $CMD = $dref->{'_cmd'};
#
#	my $SITE = 	SITE->new($USERNAME,'PRT'=>$PRT);
#
##	my %SREF = ();
##	$SREF{'_SKU'} = ''; ## ?? 
##	$SREF{'_NS'} = 'DEFAULT';
##	$SREF{'_USERNAME'} = $USERNAME;
##	$SREF{'+prt'} = $PRT;
#	if ($dref->{'_SREF'}) {
#		$SITE = SITE::sitedeserialize($USERNAME,$dref->{'_SREF'});
##		# my $kvpairs = &ZTOOLKIT::fast_deserialize($dref->{'_SREF'});
##		# print STDERR "KVPAIRS: ".Dumper($kvpairs);
##		foreach my $k (keys %{$kvpairs}) { 
##			$SITE::SREF->{$k} = $k;
##			$SREF{$k} = $kvpairs->{$k}; 
#			}
#		}
#	else {
#		warn "_SREF (SITE) was not passed to method BUILDER!\n";
#		}
#
#	# print STDERR Dumper(\%SREF);
#	# print STDERR Dumper(\%SREF,$dref);
#
#	my $html = '';
#	my $ERROR = undef;
#	my ($t,$el,$TYPE);
#	my $LOGTYPE = '';
#
#	my $FORMAT = $SITE->format();
#	my $LAYOUT = $SITE->layout();
#
#	if (defined $ERROR) {}				## skip if we encountered an error
#	elsif ($SITE->format() eq 'WRAPPER') {
#		# $LAYOUT = $SITE->layout();
#		$LOGTYPE = "WRAPPER=$LAYOUT";
#		}
#	elsif ($SITE->format() eq 'PRODUCT') {	## if sku is set, then set $SREF->{'
#		# $LAYOUT = PRODUCT->new($USERNAME,$SITE->sku())->fetch('zoovy:fl');
#		# $LAYOUT = &ZOOVY::fetchproduct_attrib($USERNAME,$SITE->sku(),'zoovy:fl');
#		# set flow style to 'P' for proper defaulting?!?! (probably not necessary)
#		$LOGTYPE = sprintf("PRODUCT=%s LAYOUT=$LAYOUT",$SITE->sku());
#		}
#	elsif ($SITE->format() =~ /^(PAGE|NEWSLETTER)$/) { 		## default 
#		#require PAGE;
#		#my ($p) = PAGE->new($USERNAME,$SITE->pageid(),NS=>$SITE->profile(),PRT=>$SITE->prt());
#		#if (not defined $p) { $ERROR = sprintf("Could not load page [%s] for user:%s",$SITE->pg(),$SITE->username()); } 
#		#else { $LAYOUT = $p->docid(); }
#		#undef $p;
#		$LOGTYPE = sprintf("PAGE=%s LAYOUT=$LAYOUT PROFILE=%s",$SITE->pageid(),$SITE->profile());
#		}
#	else {	
#		## yeah it's all good.
#		}
#	
#	if (not defined $ERROR) {
#		($t) = TOXML->new($SITE->format(),$SITE->layout(),USERNAME=>$USERNAME,SUBTYPE=>$SITE->fs());
#		use Data::Dumper;
#		if (not defined $t) { $ERROR = "Could not load TOXML layout FORMAT=[$FORMAT] LAYOUT=[$LAYOUT]".Dumper($SITE); }
#		}
#	if (not defined $ERROR) {
#		($el) = $t->fetchElement($ID,$SITE->div());
#		$LOGTYPE .= " ELEMENT=".$el->{'ID'};
#		if (not defined $el) { $ERROR = "Could not find element ID[$ID] from Toxml file FORMAT[$FORMAT] LAYOUT[$LAYOUT].".Dumper($SITE); }
#		}
#
#	##
#	## SANITY: at this point the following variables are either setup or $ERROR is set.
#	##		p=Current Page, t=Current TOXML document, el=current element in focus, type=>
#	##
#	open F, ">/tmp/foo";
#	print F Dumper($SITE,$SUB);
#
#
#	if ($SUB eq 'SAVE') {	
#		## note if we recive a variable of ACTION=reload then we'll go back and try editing again.
#		## used to reload options based on a choice (e.g. prodlist)
#
# #print STDERR "CGIV DREF\n".Dumper(
##	&ZTOOLKIT::buildparams({"cgiv"=>$ZOOVY::cgiv->{'toptext'}}),
##	&ZTOOLKIT::buildparams({"dref"=>$dref->{'toptext'}})
##	);
#		
#		if (not defined $ERROR) {
#			$TYPE = $el->{'TYPE'};
#			if (($TYPE eq 'PRODLIST') && ($dref->{'func'} eq 'LISTEDITOR')) {	$TYPE = 'LISTEDITOR'; }
#			if ($TYPE eq '') { $ERROR = "Element type was not set (how odd??)[1]"; }
#			elsif (not defined $TOXML::EDIT::edit_element{ $TYPE }) { $ERROR = "Undefined editor for TYPE=[$TYPE]"; }
#			else {
#				# use Data::Dumper; print STDERR Dumper($el,$dref,$SREF); 
#				# print STDERR "SAVING: $TYPE\n";
#
#				# print "MYPARAMS: ".&ZTOOLKIT::buildparams($dref)."\n";
#
#				print F Dumper({$TYPE,$el,$dref,$SITE});
#
#				($TYPE,my $prompt,$html) = $TOXML::SAVE::save_element{$TYPE}->($el,$dref,$SITE); 
#				$LU->log("AJAX.BUILDER.SAVE",$LOGTYPE,"INFO");
#				}
#			}
#
#		if ($ERROR ne '') {
#			warn $ERROR;
#			}
#
#		$out .= "?m=hideeditor";
#		# if (uc($dref->{'ACTION'}) eq 'RELOAD') { $SUB = 'EDIT'; $out =''; }	
#		my ($html) = $t->render('*SITE'=>$SITE);
#		# open F, ">/tmp/foo"; print F Dumper($SREF,$html); close F;
#
#		# $html = "FL: $SREF->{'_FL'} | PG: $SREF->{'_PG'} | SKU: $SREF->{'_SKU'} | FS: $SREF->{'_FS'}<br><hr>".$html;
#		$out .= "?m=loadcontent&html=".&js_encode($html);
#
#		if (uc($CMD) eq 'RELOAD') { $SUB = 'EDIT'; }
#		}
#
#	close F;
#
#	if ($SUB eq 'EDIT') {
#		if (not defined $ERROR) {
#			$TYPE = $el->{'TYPE'};
#			if (($TYPE eq 'PRODLIST') && ($dref->{'func'} eq 'LISTEDITOR')) {	$TYPE = 'LISTEDITOR'; }
#
#			# print STDERR "TYPE IS: $TYPE\n";
#			if ($TYPE eq '') { $ERROR = "Element type was not set (how odd??)[2]"; }
#			elsif (not defined $TOXML::EDIT::edit_element{ $TYPE }) { $ERROR = "Undefined editor for TYPE=[$TYPE]"; }
#			else { 
#				$el->{'_FORM'} = "thisFrm-$ID";
#				(my $STYLE,my $prompt,$html,my $extra) = $TOXML::EDIT::edit_element{$TYPE}->($el,$t,$SITE,$dref); 
#				
#				## normally we'd just call saveElement, but for LISTEDITOR we need to do some other stuff.
#				my $jsaction = qq~saveElement('$TYPE','$ID');~;
#				#if ($TYPE eq 'LISTEDITOR') {
#				#	$jsaction = qq~setorder(document.thisFrm.list1,document.thisFrm.listorder); $jsaction~;
#				#	}
#
#				## NOTE: textarea's return the input in the PROMPT (how dumb!)
#				if ($STYLE eq 'TEXTAREA') {
#					$html = $prompt; $prompt = $el->{'PROMPT'};
#					}
#				elsif ($STYLE eq 'IMAGE') {
#					$html = "<table border=0><tr><td valign='top'>$html</td><td valign='top'>$extra</td></tr></table>";
#					}
#
#
#				my $SREFstr = $SITE->siteserialize();
#
#				if ($STYLE eq 'EDITOR_ACTION') {}
#				else {
#
#				$html = &GTOOLS::std_box($prompt,qq~
#<form id="$el->{'_FORM'}" name="$el->{'_FORM'}" action="javascript:$jsaction">
#<input type="hidden" name="_SREF" value="$SREFstr">
#$html
#<input type="button" value="Save" onClick="$jsaction"> 
#</form>~);
#					}
#
#				}
#			}
#		if (defined $ERROR) {
#			$html = Dumper($SITE)." Editor for page=[$dref->{'page'}] element id=[$dref->{'id'}]<br><font color='red'>Error: $ERROR</font>";
#			}
#		$out .= "?m=loadeditor&id=$ID&html=".&js_encode($html);
#		}	
#	
#	if ($SUB eq 'CONTENT') {
#		# use Data::Dumper; print STDERR Dumper($SREF);
#		my ($html) = $t->render('*SITE'=>$SITE);
#		# $html = "FL: $SREF->{'_FL'} | PG: $SREF->{'_PG'} | SKU: $SREF->{'_SKU'} | FS: $SREF->{'_FS'}<br><hr>".$html;
#		$out = "?m=loadcontent&id=$ID&html=".&js_encode($html);
#		}
#	
#	# print STDERR "OUT: $out\n";
#
#	undef $t; undef $el;
#	}
#
#

##
## required parameters:
##		docid
##		format
##
##		toxml chooser functions:
##
if ($METHOD eq 'TOXML') {

	$SUB = uc($SUB);	# REMEMBER or FORGET
	my $DOCID = $dref->{'docid'};
	my $FORMAT = $dref->{'format'};

	if ($SUB eq 'REMEMBER') {
		# print STDERR "Remembering $FORMAT:$DOCID for $USERNAME\n";
		TOXML::UTIL::remember($USERNAME,$FORMAT,$DOCID);
		}
	elsif ($SUB eq 'FORGET') {
		# print STDERR "Forgetting $FORMAT:$DOCID for $USERNAME\n";
		TOXML::UTIL::forget($USERNAME,$FORMAT,$DOCID);
		}
	elsif ($SUB eq 'PREVIEWDETAILS') {
		require TOXML::CHOOSER;
		my ($t) = TOXML->new($FORMAT,$DOCID,USERNAME=>$USERNAME);
		my $html = TOXML::CHOOSER::showDetails($USERNAME,$t);		
		if (not defined $html) { $html = "<i>Could not load $FORMAT:$DOCID user=$USERNAME</i><br>"; }
		$out = '?m=setdetails&html='.&js_encode($html);
		}
	}


if ($METHOD eq 'FATAL-ERROR') {
	$out = "?m=eval&js=".&js_encode(qq~alert("ERR[$ERR] $ERRMSG");~);
	}

# print STDERR Dumper($SUB,$dref);

print "Expires: -1\n";
print "Content-Type: text/plain; charset=utf-8\n\n";
print "$out";
#print STDERR "OUT: $out\n";

## converts a hashref to a set of js_encoded key value pairs 
sub serialize_hashref {
	my ($ref) = @_;

	my $str = '';
	foreach my $k (keys %{$ref}) {
		$str .= sprintf("%s=%s&",&js_encode($k),&js_encode($ref->{$k}));
		}
	chop($str); 	# remove trailing &
	# print STDERR "serialized result: $str\n";
	return($str);
	}

##
## performs minimal uri encoding
##
sub js_encode {
	my ($str) = @_;

	if (not Encode::is_utf8($str)) {
		$str = Encode::encode_utf8($str);
		}

	my $string = '';
	foreach my $ch (split(//,$str)) {
		my $oi = ord($ch);
		if ((($oi>=48) && ($oi<58)) || (($oi>64) &&  ($oi<=127))) { $string .= $ch; }
		## don't encode <(60) or >(62) /(47)
		elsif (($oi==32) || ($oi==60) || ($oi==62) || ($oi==47)) { $string .= $ch; }
		else { $string .= '%'.sprintf("%02x",ord($ch));  }
		}
	return($string);
	}


