#!/usr/bin/perl

use Storable;

use lib "/httpd/modules";
use EBAY2::PROFILE;
use EBAY2;
use ZTOOLKIT;
use strict;
use SITE;

use lib "/httpd/modules";
use GTOOLS;
use GTOOLS::Form;
use PRODUCT::FLEXEDIT;
use CGI;
use ZOOVY;
use LWP::UserAgent;
use Data::Dumper;

my $q = new CGI;
my $template_file = 'index.shtml';

my $ACTION = $q->param('ACTION');
my $CODE = uc($q->param('CODE'));
$CODE =~ s/[^A-Z0-9]+//gs;
$TEMPLATE::NS = substr($CODE,0,10);



my @BC = ();
push @BC, { name=>'Setup', link=>'/biz/setup', target=>'_top' };
push @BC, { name=>'eBay ', link=>'/biz/setup/ebay', target=>'_top' };


$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~
~;

my @MSGS = ();


my @PROFILE_INFO = @{&PRODUCT::FLEXEDIT::get_GTOOLS_Form_grp("ebay.profile")};
my @SHIPPING_INFO = @{&PRODUCT::FLEXEDIT::get_GTOOLS_Form_grp("ebay.shipping")};

use Data::Dumper;
#print STDERR Dumper(\@SHIPPING_INFO);


#if (lc($ENV{'HTTP_HOST'}) eq 'ebayapi.zoovy.net') {
#	print "Location: /biz/manage/ebay\n\n";
#	exit;
#	}

#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("http://app3.zoovy.com/ebayapi",2,"_M&4");
#if (not defined $FLAGS) { $FLAGS = ''; }
#if ($USERNAME eq '') { exit; }

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&4');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my ($edbh) = &DBINFO::db_user_connect($USERNAME);

$TEMPLATE::META{'CHECKFORM'} = '';
$TEMPLATE::USERNAME = $USERNAME;

if ($FLAGS !~ /,EBAY,/) { 
	push @MSGS, "Sorry, you need the EBAY flag to enable service.";
	$ACTION = 'DENIED';
	$template_file = 'denied.shtml';
	}

my $NSREF = undef;
if ($CODE ne '') {
	$NSREF = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$CODE);
	}

##
##
##
if ($ACTION eq 'SAVE-SHORTCUTS') {
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my $ebaygref = $gref->{'%ebay'};
	if (not defined $ebaygref) { $ebaygref = {}; }
	$ebaygref->{'default_new'} = ((defined $ZOOVY::cgiv->{'ebay.default_new'})?1:0);
	$ebaygref->{'powerlister_tcbo1'} = ((defined $ZOOVY::cgiv->{'ebay.powerlister_tcbo1'})?1:0);
	if (&ZWEBSITE::globalset_attribs($USERNAME,'%ebay'=>$ebaygref)) {
		$LU->log("SETUP.EBAY.SHORTCUTS","Updated eBay preferences","SAVE");
		}
	$ACTION = 'SHORTCUTS';
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = '<div class="success">Successfully saved</div>';
	}

if ($ACTION eq 'SHORTCUTS') {
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	&ZWEBSITE::global_init_defaults($gref);	
	my $ebaygref = $gref->{'%ebay'};
	
	# $GTOOLS::TAG{'<!-- DEBUG -->'} = "<pre>".&Dumper($gref)."</pre>";
	$GTOOLS::TAG{'<!-- CHK_EBAY.DEFAULT_NEW -->'} = ($ebaygref->{'default_new'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_EBAY.POWERLISTER_TCBO1 -->'} = ($ebaygref->{'powerlister_tcbo1'})?'checked':'';

	$template_file = 'shortcuts.shtml';
	}


if ($ACTION eq 'CHECKOUT-SAVE') {

	my ($eb) = EBAY2->new($USERNAME,PRT=>$PRT);
	$eb->set(
		'DO_IMPORT_LISTINGS'=>($ZOOVY::cgiv->{'DO_IMPORT_LISTINGS'})?1:0,
		'DO_CREATE_ORDERS'=>($ZOOVY::cgiv->{'DO_CREATE_ORDERS'})?1:0,
		'IGNORE_ORDERS_BEFORE_GMT'=>int($ZOOVY::cgiv->{'IGNORE_ORDERS_BEFORE_GMT'}),
		);
	$ACTION = 'CHECKOUT';
	}


if ($ACTION eq 'CHECKOUT') {
	my ($eb) = EBAY2->new($USERNAME,PRT=>$PRT);

	my @IGNORE_ORDERS_BEFORE_VALUES = ();
	if (defined $eb) {
		$GTOOLS::TAG{'<!-- EBAY_USERNAME -->'} = $eb->ebay_username();
		$GTOOLS::TAG{'<!-- CHK_DO_IMPORT_LISTINGS -->'} = ($eb->get('DO_IMPORT_LISTINGS'))?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_DO_CREATE_ORDERS -->'} = ($eb->get('DO_CREATE_ORDERS'))?'checked':'';
		push @IGNORE_ORDERS_BEFORE_VALUES, $eb->get('IGNORE_ORDERS_BEFORE_GMT');
		}
	push @IGNORE_ORDERS_BEFORE_VALUES, 0;
	push @IGNORE_ORDERS_BEFORE_VALUES, time();
	push @IGNORE_ORDERS_BEFORE_VALUES, time()-(86400*7);
	
	foreach my $ts ( @IGNORE_ORDERS_BEFORE_VALUES ) {
		$GTOOLS::TAG{'<!-- IGNORE_ORDERS_BEFORE -->'} .= sprintf("<option value=\"%d\">%s</option>\n",$ts,&ZTOOLKIT::pretty_date($ts,1));
		}
	

	$template_file = 'checkout.shtml';
	}


##
##
##
if ($ACTION eq 'FEEDBACK-SAVE') {
	my $pstmt = "select EBAY_EIAS from EBAY_TOKENS where MID=$MID /* $USERNAME */ and PRT=$PRT order by ID";
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	while ( my ($eias) = $sth->fetchrow() ) {
		my $qtMSG = $edbh->quote($ZOOVY::cgiv->{"MSG!$eias"});
		my $qtEIAS = $edbh->quote($eias);
		my $mode = int($ZOOVY::cgiv->{"MODE!$eias"});
		my $pstmt = "update EBAY_TOKENS set FB_POLLED_GMT=0,FB_MESSAGE=$qtMSG,FB_MODE=$mode where MID=$MID and PRT=$PRT and EBAY_EIAS=$qtEIAS";
		print STDERR $pstmt."\n";
		$edbh->do($pstmt);
		}
	$sth->finish();	
	$ACTION = 'FEEDBACK';
	}

##
##
##
if ($ACTION eq 'FEEDBACK') {
	my $pstmt = "select EBAY_USERNAME,EBAY_EIAS,FB_MODE,FB_POLLED_GMT,FB_MESSAGE from EBAY_TOKENS where PRT=$PRT and MID=$MID /* $USERNAME */ order by ID";
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my ($ebuser,$eias,$fbmode,$fbpollgmt,$fbmessage) = $sth->fetchrow() ) {
		$c .= "<tr>";
		$c .= "<td>$ebuser</td>";
		$c .= "<td><select name='MODE!$eias'>";
		$c .= "<option ".(($fbmode==0)?'selected':'')." value=\"0\">disabled</option>";
		$c .= "<option ".(($fbmode==1)?'selected':'')." value=\"1\">on payment</option>";
		$c .= "<option ".(($fbmode==2)?'selected':'')." value=\"2\">recipricate</option>";
		$c .= "</select></td>";
		if ($fbmessage eq '') { $fbmessage = "Great Buyer!"; }
		my $msg = &ZOOVY::incode($fbmessage);
		$c .= "<td><input type='textbox' value=\"$msg\" size=50 name='MSG!$eias'></td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($fbpollgmt,1)."</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- ACCOUNTS -->'} = $c;

#| FB_MODE                     | tinyint(3) unsigned | NO   |     | 1                   |                |
#| FB_POLLED_GMT               | int(10) unsigned    | NO   |     | 0                   |                |
#| FB_MESSAGE                  | varchar(55)         | NO   |     | NULL                |                |

	$template_file = 'feedback.shtml';
	}

##
##
##
#if ($ACTION eq 'SHOWCASE-SAVE') {
#	my %vars = ();
#	foreach my $k ($q->param()) {
#		# save the variables e.g. $q->param(*MSG) becomes $vars{'msg'}
#		if ($k =~ /^\*(.*?)$/) { $vars{lc($1)} = $q->param($k); }
#		}
#
#	my $STYLE = $q->param('STYLE');
#	if (not defined $STYLE) { $STYLE = 0; }
#	my $ENABLE = $q->param('ENABLE');
#	
#	my $VARSTEXT = &ZTOOLKIT::buildparams(\%vars);
#
#	my $MID = &ZOOVY::resolve_mid($USERNAME);
#	if ($ENABLE && $STYLE==0) { $STYLE = 1; }
#
#	my $pstmt = "update EBAY_TOKENS set ";
#	$pstmt .= 'GALLERY_STYLE='.int($STYLE).',';
#	$pstmt .= 'GALLERY_VARS='.$edbh->quote($VARSTEXT);
#	$pstmt .= " where PRT=$PRT and MID=".int($MID).' /* USERNAME='.$edbh->quote($USERNAME)." */";
#	print STDERR $pstmt."\n";
#	$edbh->do($pstmt);
#
#	$ACTION = 'SHOWCASE';
#	}

#| GALLERY_LAST_POLL_GMT       | int(10) unsigned | NO   |     | 0                   |                |
#| GALLERY_NEXT_POLL_GMT       | int(10) unsigned | NO   |     | 0                   |                |
#| GALLERY_POLL_INTERVAL       | int(10) unsigned | NO   |     | 0                   |                |
#|
#if ($ACTION eq 'SHOWCASE') {
#	push @BC, { name=>'Showcase Configuration' };
#	$template_file = 'showcase.shtml';
#	my @subtabs = ();
#
#	my $pstmt = "select GALLERY_STYLE,GALLERY_VARS from EBAY_TOKENS where PRT=$PRT and MID=$MID /* USERNAME=".$edbh->quote($USERNAME)." */ ";
#	print STDERR $pstmt."\n";
#	my $sth = $edbh->prepare($pstmt);
#	$sth->execute();
#	my ($STYLE,$VARSTEXT) = $sth->fetchrow();
#	$sth->finish();
#
#	$GTOOLS::TAG{'<!-- STYLE_0 -->'} = ($STYLE==0)?'selected':'';
#	$GTOOLS::TAG{'<!-- STYLE_2 -->'} = ($STYLE==2)?'selected':'';
#	$GTOOLS::TAG{'<!-- STYLE_3 -->'} = ($STYLE==3)?'selected':'';
#	$GTOOLS::TAG{'<!-- STYLE_8 -->'} = ($STYLE==8)?'selected':'';
#
#	my $VARS = &ZTOOLKIT::parseparams($VARSTEXT);
#	if ($q->param('GOTO')) { $STYLE = $q->param('GOTO'); }
#
#	if ($STYLE == 1) { $STYLE = 0; }
#
#	## no gallery
#	if ($STYLE==0) {
#		$GTOOLS::TAG{'<!-- SHOWCASE_TITLE -->'} = 'Disabled';
#		$GTOOLS::TAG{'<!-- SHOWCASE_BODY -->'} = qq~There is no configuration available because showcase is disabled.~;
#		}
#	
#	if ($STYLE==2 || $STYLE==3) {
#		$GTOOLS::TAG{'<!-- SHOWCASE_TITLE -->'} = 'Original Showcase Configuration';	
#		my $style2 = ($STYLE==2)?'checked':''; 
#		my $style3 = ($STYLE==3)?'checked':''; 
#
#		my %bgcolors = ( 'FFFFFF'=>'White', '000000'=>'Black', 'C0C0C0'=>'Grey', '7777FF'=>'Blue', 'FF7777'=>'Red' ); 
#		my $BGCOLORS = ''; 
#
#		foreach my $bgcolor (sort keys %bgcolors) { $BGCOLORS .= "<option ".(($VARS->{'bgcolor'} eq $bgcolor)?'selected':'')." value='$bgcolor'>$bgcolors{$bgcolor}</option>"; }	
#		my @cols = ( 1,2 ); my $COLS = ''; 
#		foreach my $col (@cols) { $COLS .= "<option ".(($VARS->{'cols'} eq $col)?'selected':'')." value='$col'>$col</option>"; }
#	
#		my @items = ('14','28','56' ); my $ITEMS = '';
#		foreach my $item (@items) { $ITEMS .= "<option ".(($VARS->{'items'} eq $item)?'selected':'')." value='$item'>$item</option>"; }
#
#		my ($helplink, $helphtml) = GTOOLS::help_link('eBay Carousel Webdoc', 50576);	
#		$GTOOLS::TAG{'<!-- SHOWCASE_BODY -->'} = qq~
#<input type="hidden" name="ENABLE" value="1">
#
#The ShowCase Feature will display a flash gallery in your auction listings. <br>
#
#<br>
#The ShowCase can also display items that are not on eBay yet (This increases the amount of items available for cross-selling and reduces eBay fees.)
#To learn more about how the Showcase works please visit $helphtml.<br>
#<br>
#<table>
#<br>
#<b>Preferences:</b><br>
#<table>
#<tr>
#	<td>
#	Background Color: 
#	<select name="*BGCOLOR">
#		$BGCOLORS
#	</select>
#	</td>
#	<td>&nbsp;</td>
#	<td>
#	Columns: 
#	<select name="*COLS">
#		$COLS
#	</select>
#	</td>
#	<td>&nbsp;</td>
#	<td>Number of Items:
#	<select name="*ITEMS">
#		$ITEMS
#	</select>
#	</td>
#</tr>
#</table>
#<center><input type="image" src="http://www.zoovy.com/images/bizbuttons/save.gif"></center>
#
#		~;	
#		}	
#
#	if ($STYLE==8) {
#		$GTOOLS::TAG{'<!-- SHOWCASE_TITLE -->'} = 'Carousel Configuration';	
#
#		my $ITEMS = '';
#		$ITEMS .= '<option '.(($VARS->{'items'}==6)?'selected':'').' value="6">6</option>';
#		$ITEMS .= '<option '.(($VARS->{'items'}==8)?'selected':'').' value="8">8</option>';
#		$ITEMS .= '<option '.(($VARS->{'items'}==10)?'selected':'').' value="10">10</option>';
#		$ITEMS .= '<option '.(($VARS->{'items'}==12)?'selected':'').' value="12">12</option>';
#
#		my $SCHEMES = '';
#		if ($VARS->{'scheme'} eq '') { $VARS->{'scheme'} = 1; }
#		$SCHEMES .= '<option '.(($VARS->{'scheme'}==1)?'selected':'').' value="1">Grey/Orange</option>';
#		$SCHEMES .= '<option '.(($VARS->{'scheme'}==2)?'selected':'').' value="2">Blue/Yellow</option>';
#		$SCHEMES .= '<option '.(($VARS->{'scheme'}==3)?'selected':'').' value="3">Green/Silver</option>';
#		$SCHEMES .= '<option '.(($VARS->{'scheme'}==0)?'selected':'').' value="0">** Custom **</option>';
#
#	
#			$GTOOLS::TAG{'<!-- SHOWCASE_BODY -->'} = qq~
#<input type="hidden" name="ENABLE" value="1">
#<input type="hidden" name="STYLE" value="8">
#<b>Carousel:</b>
#<br>
#Please choose a theme: 
#<input type="hidden" name="*THEME" value="gel">
#
#Maximum Number of products:
#<select name="*ITEMS">
#	$ITEMS
#</select><br>
#<i>Note: actual display number may be less than the maximum due to how products are selected.</i><br>
#<br>
#
#Please choose a color scheme:
#<select name="*SCHEME">
#	$SCHEMES
#</select><br>
#<br>
#Custom Color Scheme: <input type="textbox" size="50" name="*CUSTOM" value="$VARS->{'custom'}"><br>
#<i>Zoovy can create a custom color scheme that matches your auction template.</i><br>
#<br>
#<center><input type="image" src="http://www.zoovy.com/images/bizbuttons/save.gif"></center>
#
#~;
#		}
#
#	
#	if ($STYLE>0) {
#		$GTOOLS::TAG{'<!-- SHOWCASE_PREVIEW -->'} = qq~
#		<br>
#<table border='0' width='640' class='zoovytable'>
#<tr>
#	<td class='zoovytableheader'>Preview</td>
#</tr>
#<tr>
#	<td>
#	<iframe width=100% height=400 src="showcase-preview.cgi?USERNAME=$USERNAME"></iframe>
#	</td>
#</tr>
#</table>
#~;
#		}
#
#
#	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
#	$GTOOLS::TAG{'<!-- ACTION -->'} = '';
#	}





##
## SETTOKEN is returned from https://webapi.zoovy.com/webapi/ebayapi/accept.cgi
###	the following variables are set:
###		USERNAME
###		eb - ebayusername
###		ebaytkn - ebay authentication token
###		tknexp - expiration date [2005-02-04 19:38:37]
##

print STDERR "ACTION: $ACTION\n";

if ($ACTION eq 'SETTOKEN') {

	## we need to set this so we can check it later in the TODO list.
	use lib "/httpd/modules";
	use ZWEBSITE;
	# print STDERR "Saving website attrib $USERNAME/ebay\n";
	&ZWEBSITE::save_website_attrib($USERNAME,'ebay',time());

	my $REC_ID = 0;
	my $eb = $q->param('eb');
	if ($eb eq '') { 
		
		$REC_ID = -1 ; 
		}
	my $tkn = $q->param('ebaytkn');
	my $tknexp = $q->param('tknexp');
	my $PROFILE = $q->param('p');
	$PROFILE = &ZWEBSITE::checkout_profile($USERNAME,$PRT);	
	
	my $pstmt = "select ID,EBAY_EIAS from EBAY_TOKENS where MID=$MID /* ".$edbh->quote($USERNAME)." */ and EBAY_USERNAME=".$edbh->quote($eb);
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	while ( my ($ID,$EIAS) = $sth->fetchrow() ) {
		my $pstmt = "delete from EBAY_TOKENS where MID=$MID /* $USERNAME */ and ID=$ID limit 1";
		$edbh->do($pstmt);

		## clear out any store categories.	
		$pstmt = "delete from EBAYSTORE_CATEGORIES where MID=$MID /* $USERNAME */ and EIAS=".$edbh->quote($EIAS);
		$edbh->do($pstmt);
		}
	$sth->finish();

	## clear out any tokens on this partition.
	$pstmt = "delete from EBAY_TOKENS where MID=$MID /* $USERNAME */ and PRT=$PRT";
	$edbh->do($pstmt);

	my $sb = $q->param('sb');
	if (not defined $sb) { $sb = 0; } else { $sb = int($sb); }

	my $is_epu = 0;
	my ($flags) = &ZOOVY::RETURN_CUSTOMER_FLAGS($USERNAME);
	if ($flags =~ /,EPU,/) { $is_epu++; }

	## now insert the new TOKEN
	if ($REC_ID==0) {
		$pstmt = &DBINFO::insert($edbh,'EBAY_TOKENS',{
			MID=>$MID,
			PRT=>$PRT,
			USERNAME=>$USERNAME,
			EBAY_USERNAME=>$eb,
			IS_SANDBOX=>$sb,
			IS_EPU=>$is_epu,
			EBAY_TOKEN=>$tkn,
			EBAY_TOKEN_EXP=>$tknexp,
			GALLERY_POLL_INTERVAL=>300,
			GALLERY_NEXT_POLL_GMT=>$^T,
			},debug=>1+2);
		print STDERR $pstmt."\n";
		$edbh->do($pstmt);

		$pstmt = "select last_insert_id()";
		my $sth = $edbh->prepare($pstmt); 
		$sth->execute(); 
		($REC_ID) = $sth->fetchrow(); 
		$sth->finish();

		$LU->log("SETUP.EBAY","Token Updated! ebayUser=$eb profile=$PROFILE","SAVE");
		$ACTION = 'SETTOKEN_SUCCESS';
		}


	my %hash = ();
	my ($hasStore,$USERID) = (0,'');
	if ($REC_ID>0) {
		## now we verify the eBay Username
		$hash{'#Site'} = 0;
		$hash{'DetailLevel'} = 'ReturnAll';

#	if ($ENV{'HOSTNAME'} eq 'newdev.zoovy.com') {}
#	else {
			my ($eb2) = EBAY2->new($USERNAME,PRT=>$PRT);
			my ($r) = $eb2->api('GetUser',\%hash,preservekeys=>['User'],xml=>3);
			# print STDERR Dumper($r);

			my $info = &ZTOOLKIT::XMLUTIL::SXMLflatten($r->{"."});
			# my $info = &XMLTOOLS::XMLcollapse($r->{'User'});
			$hasStore = ($info->{'.User.SellerInfo.StoreOwner'} eq 'true')?1:0;

			$USERID = $info->{'.User.UserID'};
			# print STDERR "USERID: $USERID\n";

			if (($REC_ID>0) && ($USERID ne '')) {
				my $qtEIAS = $edbh->quote($info->{'.User.EIASToken'});
				my $qtSUBSCRIPTION = $edbh->quote($info->{'.User.UserSubscription'}?$info->{'.User.UserSubscription'}:'');
				my $qtFEEDBACK = int($info->{'.User.FeedbackScore'});
				$pstmt = "update EBAY_TOKENS set EBAY_FEEDBACKSCORE=$qtFEEDBACK,EBAY_EIAS=$qtEIAS,EBAY_SUBSCRIPTION=$qtSUBSCRIPTION,HAS_STORE=$hasStore,EBAY_USERNAME=".$edbh->quote($USERID)." where ID=$REC_ID and MID=$MID";
				$edbh->do($pstmt);
	
				## remove any duplicate tokens that might be left over.
				$pstmt = "delete from EBAY_TOKENS where EBAY_EIAS=$qtEIAS and ID!=$REC_ID";
				$edbh->do($pstmt);
				}
#		}

		## store the ebay username in all the important fields
		
		my ($epnsref) = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$CODE);
		$epnsref->{'ebay:username'} = $USERID;
		$epnsref->{'ebaystores:username'} = $USERID;
		$epnsref->{'ebaymotor:username'} = $USERID;
		&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$epnsref);
		}

	## validate sandbox users!
	if (($REC_ID>0) && ($sb)) {
		%hash = ();
		$hash{'FeedbackScore'} = 1000;
		my ($eb2) = EBAY2->new($USERNAME,PRT=>$PRT);
		my ($r) = $eb2->api('ValidateTestUserRegistration',\%hash);
		}
	
	if ($REC_ID==-1) {
		$ACTION = 'REGISTER';
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>Failure - you did not specify an eBay Username.</font>";
		}
	elsif ($hasStore) { 
		$ACTION = 'LOAD-STORE-CATEGORIES'; 
		}	
	else {
		$ACTION = 'PROFILES';
		}
	}



##
## Check to see if we have a valid eBay Token
##
if ($ACTION ne 'DENIED') {
	my $pstmt = "select count(*) from EBAY_TOKENS where MID=$MID /* $USERNAME */ and PRT=$PRT";
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();
	if ($count == 0) { 
		$ACTION = 'REGISTER'; 
		} 
	elsif ($ACTION eq '') { 
		$ACTION = 'PROFILES'; 
		}
	}



if ($ACTION eq 'DEACTIVATE') {
	$GTOOLS::TAG{'<!-- ID -->'} = $q->param('ID');
	$template_file = 'mgr-deactivate.shtml';
	}

if ($ACTION eq 'DEACTIVATE_CONFIRM') {
	my $ID = $q->param('ID');

	my $pstmt = "select ID,EBAY_EIAS from EBAY_TOKENS where ID=".$edbh->quote($ID)." and MID=$MID /* ".$edbh->quote($USERNAME)." */ limit 1";
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	while ( my ($ID,$EIAS) = $sth->fetchrow() ) {
		my $pstmt = "delete from EBAY_TOKENS where MID=$MID /* $USERNAME */ and ID=$ID limit 1";
		$edbh->do($pstmt);
	
		$pstmt = "delete from EBAYSTORE_CATEGORIES where MID=$MID /* $USERNAME */ and EIAS=".$edbh->quote($EIAS);
		$edbh->do($pstmt);

		$LU->log("SETUP.EBAY","Token Removed EIAS=$EIAS","SAVE");
		}
	$sth->finish();


	$ACTION = 'REGISTER';
	}



if ($ACTION eq 'SAVEUNPAID') {
	my $pstmt = "update EBAY_TOKENS set ";
	$pstmt .= "UPI_AUTODISPUTE=".$edbh->quote($q->param('AUTODISPUTE'));
	$pstmt .= " where PRT=$PRT and MID=$MID /* ".$edbh->quote($USERNAME)." */";
	# print STDERR $pstmt."\n";
	$edbh->do($pstmt);

	$ACTION = 'UNPAID';
	}

if ($ACTION eq 'UNPAID') {
	$template_file = 'mgr-unpaid.shtml';

	$GTOOLS::TAG{'<!-- AUTODISPUTE_0 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_3 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_5 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_7 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_10 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_14 -->'} = '';
	$GTOOLS::TAG{'<!-- AUTODISPUTE_28 -->'} = '';

	my $pstmt = "select UPI_AUTODISPUTE from EBAY_TOKENS where PRT=$PRT and MID=$MID /* ".$edbh->quote($USERNAME)." */";
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	my ($AUTODISPUTE) = $sth->fetchrow();
	$sth->finish();
	
	$GTOOLS::TAG{'<!-- AUTODISPUTE_'.$AUTODISPUTE.' -->'} = 'selected';
	}

##
##
##


if ($ACTION eq 'PROFILE-SHIPPING-SAVE') {
	$NSREF = &GTOOLS::Form::serialize(\@SHIPPING_INFO,$ZOOVY::cgiv,$NSREF);
	my $qtTOKEN = ($NSREF->{'ebay:token'})?$edbh->quote($NSREF->{'ebay:token'}):'TOKEN';
	$NSREF->{'ebay:calcshipping'}=2;

	if (1) {
		my $locref = retrieve("ShippingLocationDetails.bin");
		my %locs = ();
		foreach my $loc (@{$locref}) {
			my $id = $loc->{'ShippingLocation'};
			if (defined $ZOOVY::cgiv->{"loc.$id"}) { $locs{$id}++; }
			}
		$NSREF->{'ebay:ship_intlocations'} = &ZTOOLKIT::buildparams(\%locs,1);
		}

	&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$NSREF);
	$LU->log("SETUP.EBAY","Saved Shipping Settings (Profile=$CODE)","SAVE");
	push @MSGS, "SUCCESS|Saved Shipping Settings (Profile=$CODE Prt=$PRT)";
	$ACTION = 'PROFILE-SHIPPING';
	}



##
##
##
if (($ACTION eq 'PROFILE-SHIPPING-DOM-DELETE') || ($ACTION eq 'PROFILE-SHIPPING-INT-DELETE')) {
	my $key = ($ACTION =~ /-DOM-/)?'ebay:ship_domservices':'ebay:ship_intservices';

	my @lines = split(/[\n\r]+/,$NSREF->{$key});
	$lines[ int($ZOOVY::cgiv->{'ID'})-1 ] = '';
	my $buf = join("\n",@lines);
	$buf =~ s/[\n\r]+/\n/gs;
	$buf =~ s/^[\n\r]+//gs;
	$buf =~ s/[\n\r]+$//gs;
	$NSREF->{$key} = $buf;
	$LU->log("SETUP.EBAY","Saved Shipping Settings (Profile=$CODE / $ACTION)","SAVE");
	&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$NSREF);
	$ACTION = 'PROFILE-SHIPPING';
	}


if (($ACTION eq 'PROFILE-SHIPPING-DOM-SAVE') || ($ACTION eq 'PROFILE-SHIPPING-INT-SAVE')) {
	my $key = ($ACTION =~ /-DOM-/)?'ebay:ship_domservices':'ebay:ship_intservices';

	my @lines = split(/[\n\r]+/,$NSREF->{$key});
	my %svc = ();
	foreach my $k ('cost','addcost','farcost','service','priority','free','shipto') {
		if ($ACTION =~ /-DOM-/) {
			$svc{$k} = $ZOOVY::cgiv->{"dom.$k"};
			}
		else {
			$svc{$k} = $ZOOVY::cgiv->{"int.$k"};
			}
		}
	$svc{'free'} = ($svc{'free'} ne '')?1:0;
	my $pos = $svc{'priority'};
	if ($pos>0) { $pos = $pos - 1; }

	my $newline = &ZTOOLKIT::buildparams(\%svc,1);
	$lines[ $pos ] = $newline;
	my $buf = join("\n",@lines);
	$buf =~ s/[\n\r]+/\n/gs;
	$NSREF->{$key} = $buf;



	$LU->log("SETUP.EBAY","Saved Shipping Settings (Profile=$CODE / $ACTION)","SAVE");
	push @MSGS, "SUCCESS|Saved Shipping Settings (Profile=$CODE / $ACTION)";
	&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$NSREF);
	$ACTION = 'PROFILE-SHIPPING';
	}


if ($ACTION eq 'PROFILE-SHIPPING') {

	my ($eb2) = EBAY2->new($USERNAME,PRT=>$PRT);
	my ($err) = $eb2->VerifyConfig($CODE);
	if ($err ne '') {
		$GTOOLS::TAG{'<!-- XML -->'} = "<table width=\"600\"><tr><td>$err</td></tr></table><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- XML -->'} = "<i>Listing will most likely launch with this shipping configuration.</i><br>";
		}

	# $GTOOLS::TAG{'<!-- DOM_CONFIGURED -->'} = "<pre>".$NSREF->{'ebay:ship_domservices'}."</pre>";
	if (1) {
		my $c = '';
		$c .= "<tr class='zoovysub2header'><td></td><td width=20>#</td><td width=100>Service</td><td width=\"99\%\">Pricing</td></tr>";
		my $i = 1;
		foreach my $line (split(/[\n\r]+/,$NSREF->{'ebay:ship_domservices'})) {
			next if ($i>3);
			my $svc = &ZTOOLKIT::parseparams($line);
			my $pricetxt = '';
			if ($svc->{'free'}>0) { $pricetxt = 'Free'; }
			elsif ($svc->{'cost'}<0) { 
				$pricetxt = 'Product Fixed Pricing'; 
				if ($svc->{'addcost'}>=0) { $pricetxt .= sprintf(" additional items: \$%.2f",$svc->{'addcost'}); }
				}
			elsif ($svc->{'cost'}>0) { $pricetxt = sprintf("\$%.2f 1st item, \$%.2f 2nd item",$svc->{'cost'},$svc->{'addcost'}); }
			else { $pricetxt = 'Using eBays estimated Carrier Rates'; }
			if ($svc->{'farcost'}>0) { $pricetxt .= sprintf('; $%.2f AK+HI',$svc->{'farcost'}); }
			my $delete = "<a href=\"index.cgi?ACTION=PROFILE-SHIPPING-DOM-DELETE&CODE=$CODE&ID=$i\">DELETE</a>";
			$c .= "<tr><td>$delete</td><td width=\"20\">$i</td><td>$svc->{'service'}</td><td>$pricetxt</td></tr>\n";
			$i++;
			}
		$GTOOLS::TAG{'<!-- DOM_CONFIGURED -->'} .= $c;
		if ($NSREF->{'ebay:ship_domservices'} eq '') { 
			$GTOOLS::TAG{'<!-- DOM_CONFIGURED -->'} = '<font color="red">WARNING: none configured. at least one domestic method is required!</font>'; 
			}
		}

	if (1) {
		my $c = '';
		$c .= "<tr class='zoovysub2header'><td></td><td width=20>#</td><td width=100>Service</td><td width=\"99\%\">Pricing</td></tr>";
		my $i = 1;
		foreach my $line (split(/[\n\r]+/,$NSREF->{'ebay:ship_intservices'})) {
			next if ($i>3);
			my $svc = &ZTOOLKIT::parseparams($line);
			my $pricetxt = '';
			if ($svc->{'free'}>0) { $pricetxt = 'Free'; }
			elsif ($svc->{'cost'}<0) { 
				$pricetxt = 'Fixed Pricing (loaded from product)'; 
				if ($svc->{'addcost'}>=0) { $pricetxt .= sprintf(" additional items: \$%.2f",$svc->{'addcost'}); }
				}
			elsif ($svc->{'cost'}>0) { $pricetxt = sprintf("\$%.2f 1st item, \$%.2f 2nd item",$svc->{'cost'},$svc->{'addcost'}); }
			else { $pricetxt = 'Using eBays estimated Carrier Rates'; }
			if ($svc->{'farcost'}>0) { $pricetxt .= sprintf('; $%.2f AK+HI',$svc->{'farcost'}); }
			if ($svc->{'shipto'} ne '') { $pricetxt .= ", ships to: ".$svc->{'shipto'}; }


			my $delete = "<a href=\"index.cgi?ACTION=PROFILE-SHIPPING-INT-DELETE&CODE=$CODE&ID=$i\">DELETE</a>";
			$c .= "<tr><td valign=top>$delete</td><td valign=top width=\"20\">$i</td><td valign=top>$svc->{'service'}</td><td valign=top>$pricetxt</td></tr>\n";
			if ($svc->{'service'} eq 'USPSFirstClassMailInternational') {
				$c .= "<tr><td></td><td colspan=5><div class='hint'>REMINDER: items &gt; 4lbs. not allowed for service $svc->{'service'}.</div></div>";
				}
			$i++;
			}
		$GTOOLS::TAG{'<!-- INT_CONFIGURED -->'} .= $c;
		}

	if (1) {
		my $locref = retrieve("ShippingLocationDetails.bin");
		my $c = '<tr>';
		my $i = 0;
		my $mylocs = &ZTOOLKIT::parseparams($NSREF->{'ebay:ship_intlocations'},1);
		foreach my $loc (@{$locref}) {
			my $id = $loc->{'ShippingLocation'};
			my $checked = ($mylocs->{$id})?'checked':'';
			if (($i>0) && (($i%4)==0)) { $c .= "</tr><tr>"; }
			$c .= "<td width='25%'>";
			$c .= "<input $checked type=\"checkbox\" name=\"loc.$id\">";
			$c .= "$loc->{'Description'}";
			my $hint = '';

			if ($id eq 'None') { $hint = "Not Delivered/Digital"; }
			elsif (length($id)<=2) { $hint = $id; }

			if ($hint ne '') {
				$c .= " <span class='hint'>($hint)</div>"; 
				}
			$c .= "</td>";
			$i++;
			}
		$c .= "</tr>";
		$GTOOLS::TAG{'<!-- INT_COUNTRIES -->'} = $c;
		}

	foreach my $fields (@SHIPPING_INFO) {
		# print STDERR Dumper($fields);
		my $type = $fields->{'type'};
		my $key = $fields->{'key'};
		next if (($type eq '') || (not defined $GTOOLS::Form::funcs{$type}));
		# print STDERR "TYPE: $type\n";

		$fields->{'data'} = $NSREF->{$key};
		$GTOOLS::TAG{'<!-- '.$type.'!'.$key.' -->'} = 	$GTOOLS::Form::funcs{$type}->(%{$fields});
		}	
	$template_file = 'profile-shipping.shtml';
	$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;

	my $domsvc = '';
	my $intsvc = '';
	my $ssdref = retrieve 'ShippingServiceDetails.bin';
	foreach my $ssd (@{$ssdref}) {
		#next unless (ref($ssd->{'ShippingPackage'}) eq 'ARRAY');

		##  'ShippingService' => 'FreightShippingInternational'
		if ($ssd->{'ShippingServiceID'}==50015) { $ssd->{'ValidForSellingFlow'} = 'true'; }
		##  'ShippingService' => 'Freight',
		if ($ssd->{'ShippingServiceID'}==50) { 
			$ssd->{'ValidForSellingFlow'} = 'true'; 
			$ssd->{'Description'} = 'Flat Priced Freight';
			}
		##   'ShippingService' => 'FreightShipping',
		if ($ssd->{'ShippingServiceID'}==16) { $ssd->{'ValidForSellingFlow'} = 'true'; }

		## apparently 'ShippingService' => 'USPSGlobalExpress' is no longer valid but still returned by API call
		next if ($ssd->{'ShippingServiceID'} eq '50003');
		next if ($ssd->{'ValidForSellingFlow'} ne 'true');

		#next if ($ssd->{'ShippingServiceID'} eq '14');


		if ($ssd->{'InternationalService'} eq 'true') {
			$intsvc .= "<option value=\"$ssd->{'ShippingService'}\">$ssd->{'Description'}</option>\n";
			}
		else {
			$domsvc .= "<option value=\"$ssd->{'ShippingService'}\">$ssd->{'Description'}</option>\n";
			}
		}
	$GTOOLS::TAG{'<!-- DOM_SERVICES -->'} = $domsvc;
	$GTOOLS::TAG{'<!-- INT_SERVICES -->'} = $intsvc;
	

	

 #	$GTOOLS::TAG{"<!-- XML -->"} = "<table width=100%><tr><td align='left'><font size=1><pre>XML:".
	#	&ZOOVY::incode(&shippingXML($USERNAME,$NSREF)).
	#	"</pre></font></td></tr></table>";
	}








if (($ACTION eq 'PROFILE-SAVE') || ($ACTION eq 'PROFILE-SAVE-EDIT') || ($ACTION eq 'CHOOSER')) {

	# print STDERR "CODE: $CODE\n";

#	my $qtBGCOLOR = $edbh->quote($q->param('SHOWCASE_BGCOLOR')?$q->param('SHOWCASE_BGCOLOR'):'FFFFFF');
#	my $qtITEMS = $edbh->quote(int($q->param('SHOWCASE_ITEMS')?$q->param('SHOWCASE_ITEMS'):'14'));
#	my $qtCOLS = $edbh->quote(int($q->param('SHOWCASE_COLS')?$q->param('SHOWCASE_COLS'):'1'));

	my ($epnsref) = EBAY2::PROFILE::fetch($USERNAME,$PRT,$CODE);
	my ($eb) = EBAY2->new($USERNAME,PRT=>$PRT);
	$epnsref->{'ebay:eias'} = $eb->ebay_eias();
	# $ref->{'ebay:eias'} = (defined $q->param('eias'))?$q->param('eias'):'';
	$epnsref->{'ebay:template'} = (defined $q->param('template'))?$q->param('template'):'';

	# print STDERR Dumper($ref,$eb); die();

	open F, "/httpd/static/counters.txt";
	my %counters = ();
	while (<F>) { 
		next if (/#/);
		my ($categoryname,$flag,$directory,$pretty, $width, $height) = split("\t",$_);	
		## /images/samples/counters/$directory.gif
		$counters{ $directory }= "$categoryname/$pretty ($width x $height)"
		}
	close F;
	push @PROFILE_INFO, { 'type'=>'select', key=>'ebay:counter', set=>\%counters };

	$epnsref = &GTOOLS::Form::serialize(\@PROFILE_INFO,$ZOOVY::cgiv,$epnsref);
#	print STDERR "CODE:$CODE $ref->{'ebay:eias'}\n";
	&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$epnsref);
	push @MSGS, "SUCCESS|Successfully updated EBAY_PROFILE:$CODE PRT:$PRT";

#	my $qtTOKEN = ($ref->{'ebay:token'})?$edbh->quote($ref->{'ebay:token'}):'TOKEN';
#	&DBINFO::insert($edbh,'EBAY_PROFILES',{
#		MERCHANT=>$USERNAME,
#		MID=>$MID,
#		CODE=>$CODE,
#		TOKEN=>$ref->{'ebay:token'},
#		CONFIG_UPDATED_GMT=>$^T,		
#		CONFIG_VERSION=>3,
#		},key=>['MID','CODE']);

	$LU->log("SETUP.EBAY","Updated Properties Profile=$CODE","SAVE");
	if ($ACTION eq 'PROFILE-SAVE-EDIT') { 
		$ACTION = 'PROFILE-POLICYEDIT'; 
		}
	elsif ($ACTION ne 'CHOOSER') { 
		$ACTION = 'PROFILES'; 
		}
	}






if ($ACTION eq 'REALLY_DELETE_PROFILE') {
		
	my $err = '';
	$ZOOVY::cgiv->{'REMOVE1'} =~ s/[^A-Z0-9]//gs;
	$ZOOVY::cgiv->{'REMOVE1'} = substr($ZOOVY::cgiv->{'REMOVE1'},0,10);

	if ($ZOOVY::cgiv->{'REMOVE1'} eq '') {
		$err = 'Profile not selected';
		}
	elsif ($ZOOVY::cgiv->{'REMOVE2'} ne $ZOOVY::cgiv->{'REMOVE1'}) {
		$err = 'You must select the same profile twice to confirm'; 
		}
	elsif (not defined $ZOOVY::cgiv->{'CHECK1'}) {
		$err = 'Please check the box indicating you understand the risks of removing a profile.';
		}
	elsif (not defined $ZOOVY::cgiv->{'CHECK2'}) {
		$err = 'Please check the box indicating you are sure.';
		}
	elsif (not defined $ZOOVY::cgiv->{'CHECK3'}) {
		$err = 'Please check the box indicating you are really, really sure.';
		}


	if ($err eq '') {
		$LU->log('SETUP.PROFILE',"REMOVED PROFILE: $ZOOVY::cgiv->{'REMOVE1'}",'INFO');
		EBAY2::PROFILE::nuke($USERNAME,$PRT,$ZOOVY::cgiv->{'REMOVE1'});
		push @MSGS, "SUCCESS|REMOVED PROFILE: $ZOOVY::cgiv->{'REMOVE1'}";
		$ACTION = 'PROFILES';		
		}
	else {
		$ACTION = 'PROFILE-REMOVE';
		push @MSGS, "ERROR|$err";
		}

	}


if ($ACTION eq 'PROFILE-REMOVE') { 

	my $prefs = &EBAY2::PROFILE::list($USERNAME);
	my @PROFILES = ();
	foreach my $pref (@{$prefs}) {
		push @PROFILES, $pref->{'CODE'};
		}
	my $c = '';
	foreach my $p (sort @PROFILES) {
		next if ($p eq 'DEFAULT');
		$c .= "<option value=\"$p\">$p</option>\n";
		}
	$GTOOLS::TAG{'<!-- REMOVE -->'} = $c;

	$template_file = 'profile-remove.shtml';
	}


##
## SAVE_PREVIEW is the "Save / Preview" button (should save + reload + cause refresh)
if (($ACTION eq 'PROFILE-WIZARDSAVE') || ($ACTION eq 'PROFILE-PREVIEWSAVE') || ($ACTION eq 'PROFILE-COMPANYSAVE') || ($ACTION eq 'PROFILE-LOAD')) {

	if ($ACTION eq 'PROFILE-LOAD') { $ACTION = 'PROFILE-COMPANYEDIT'; }
	elsif ($ACTION eq 'PROFILE-WIZARDSAVE') { 
		$ACTION = 'PROFILE-COMPANYEDIT'; 
		}
	elsif ($ACTION eq 'PROFILE-PREVIEWSAVE') { 
		$ACTION = 'PROFILE-COMPANYEDIT'; 
		$GTOOLS::TAG{'<!-- AUTOLOAD_PREVIEW -->'} = qq~<script><!--
doPreview();
//--></script>~;
		}
	else { 
		$ACTION = 'PROFILES'; 
		}

	my $NS = $ZOOVY::cgiv->{'NS'};
	$GTOOLS::TAG{'<!-- MKT -->'} = uc('ebay');
	$GTOOLS::TAG{'<!-- NS -->'} = $NS;

	my ($epnsref) = EBAY2::PROFILE::fetch($USERNAME,$PRT,$NS);
	$epnsref->{'ebay:template'} = $ZOOVY::cgiv->{'template'};

	foreach my $p (keys %{$ZOOVY::cgiv}) {
		next unless ($p =~ /^[\w]+\:[\w]+$/);
		$epnsref->{$p} = $ZOOVY::cgiv->{$p};
		print STDERR "SAVING: $p=[$ZOOVY::cgiv->{$p}]\n";
		}

	EBAY2::PROFILE::store($USERNAME,$PRT,$NS,$epnsref);
	}

if ($ACTION eq 'PROFILE-COMPANYEDIT') {
	my $NS = $ZOOVY::cgiv->{'NS'};
	my $epnsref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$NS);	
	if ($epnsref->{'ebay:template'} eq '') { $ACTION = 'PROFILE-CHOOSE_WIZARD'; }
	}


if ($ACTION eq 'PROFILE-CHOOSE_WIZARD') {
	my $NS = $ZOOVY::cgiv->{'NS'};
	$GTOOLS::TAG{'<!-- NS -->'} = $NS;

	require TOXML::CHOOSER;
	my $epnsref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$NS);	
	$GTOOLS::TAG{'<!-- WIZARD_CHOOSER -->'} = TOXML::CHOOSER::buildChooser($USERNAME,'WIZARD',selected=>$epnsref->{'ebay:template'});

	$template_file = 'profile-choosewizard.shtml';
	}


if ($ACTION eq 'PROFILE-COMPANYEDIT') {
	$template_file = 'profile-edit.shtml';
	my $NS = $ZOOVY::cgiv->{'NS'};
	$GTOOLS::TAG{'<!-- NS -->'} = $NS;

	my $epnsref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$NS);	
	my $c = $epnsref->{lc('ebay:template')};
	if ($c eq '') { $c = "Not Set"; }
	$GTOOLS::TAG{'<!-- TEMPLATE -->'} = $c;
	$GTOOLS::TAG{'<!-- TEMPLATEATTRIB -->'} = lc('ebay:template');

	my ($SITE) = SITE->new($USERNAME,$PRT,'FORMAT'=>'WIZARD','DOCID'=>'ebay.profile','LAYOUT'=>$epnsref->{'ebay:template'});
	$SITE->sset('_NS',$NS);
	$SITE->setSTID('');
	$SITE->layout( $epnsref->{'ebay:template'} );
	$SITE->{'%NSREF'} = $epnsref;	
	#$SREF->{'_WIZARD'} = $epnsref->{'ebay:template'};
	#$SREF->{'%NSREF'} = $epnsref;
	$GTOOLS::TAG{'<!-- _SREF -->'} = $SITE->siteserialize();

	if ($epnsref->{'ebay:template'}) {
		require TOXML;
		require TOXML::EDIT;
		my $HWIZDOCID = $epnsref->{'ebay:template'};
		my ($toxml) = TOXML->new('WIZARD',$HWIZDOCID,USERNAME=>$USERNAME,MID=>$MID);
		my $elementref = [];
		if (defined $toxml) {
			$elementref = $toxml->getElements('@PROFILE');
			}

		# open F, ">/tmp/foo"; use Data::Dumper; print F Dumper($elementref); close F;

		$c = '';	
		my $max = scalar(@{$elementref});
		my $color_counter = 0;
		my ($HELP,$COL1,$COL2,$COL3) = ();
		my $BGCOLOR = '';
		for (my $x=0; $x<$max; $x++) {
			my $iniref = $elementref->[$x];
			my $TYPE = $iniref->{'TYPE'};
			my $STYLE = undef;
			if (not defined($TYPE)) { $TYPE = 'unknown'; }
	
			next if ($iniref->{'name'} eq 'LIST');

			# print STDERR "TYPE is: $TYPE\n";
			my $PROMPT = $iniref->{'PROMPT'};
			if (++$color_counter%2 == 0) { $BGCOLOR = 'f0f0f0'; } else { $BGCOLOR = 'FFFFFF'; }
	
			# print STDERR Dumper($TYPE);
			if (defined $TOXML::EDIT::edit_element{$TYPE}) {
				($STYLE, $COL1, $COL2, $COL3, $HELP) = $TOXML::EDIT::edit_element{$TYPE}->($iniref,$toxml,$SITE);
				}
		
			if ($STYLE eq 'LONGTEXT') { $STYLE = 'TEXTBOX'; }
			elsif ($STYLE eq 'NUMBER') { $STYLE = 'TEXTBOX'; }
			elsif ($STYLE eq 'HTML') { $STYLE = 'TEXTBOX'; }
			elsif ($STYLE eq 'TREE') { $STYLE = 'RADIO'; }
	
			if ($STYLE eq 'TEXTBOX') { $c .= "<tr bgcolor='".$BGCOLOR."'><td class=\"PROMPT\">$COL1:</td><td class=\"INPUT\" colspan='2'>$COL2</td></tr>\n"; }
			elsif ($STYLE eq 'TEXTAREA' || $STYLE eq 'TEXTLIST') { $c .= "<tr bgcolor='$BGCOLOR'><td colspan='3' style='padding-left: 12px;'>$COL1</td></tr>\n"; }
			elsif ($STYLE eq 'IMAGE') { $c .= "<tr bgcolor='$BGCOLOR'><td>$COL1</td><td align='left'>$COL2</td><td valign='middle' align='left'>$COL3\n</td></tr>\n"; }
			elsif ($STYLE eq 'SELECT') { $c .= "<tr bgcolor='$BGCOLOR'><td>$COL1:</td><td colspan='2'>$COL2<br></td></tr>\n"; }
			elsif ($STYLE eq 'SKU') { $c .= "<tr bgcolor='$BGCOLOR'><td>$COL1:</td><td colspan='2'>$COL2<br></td></tr>\n"; }
			elsif ($STYLE eq 'CHECKBOX') { $c .= "<tr colspan='3' bgcolor='$BGCOLOR'><td>$COL1: $COL2<br></td></tr>\n"; }
			elsif ($STYLE eq 'RADIO') { $c .= "<tr colspan='3' bgcolor='$BGCOLOR'><td>$COL1:<br>$COL2<br></td></tr>\n"; }
			elsif ($STYLE eq 'HIDDEN') { $c .= $COL1; }
			elsif ($STYLE eq 'NULL') {}
			else { $c .= "<tr bgcolor='red'><td>Unknown TYPE in syndication editor: [$TYPE] generated style: $STYLE\n</td></tr>"; }
			}
	
		$GTOOLS::TAG{"<!-- CHECKFORM -->"} = "function checkForm()\n{\n".$DOCID::META{'CHECKFORM'}."\n return(true); \n}\n";
		$GTOOLS::TAG{'<!-- CONTENTS -->'} = $c;
		# $GTOOLS::TAG{'<!-- DEBUG -->'} = '<pre>'.Dumper($elementref).'</pre>';
		}

	}



##
##	
## 
if ($ACTION eq 'PROFILE-ADD') {
	my $prefs = &EBAY2::PROFILE::list($USERNAME,$PRT);
	my @PROFILES = ();
	foreach my $ref (@{$prefs}) {
		push @PROFILES, $ref->{'CODE'};
		}
	
	my $c = '';
	foreach my $p (sort @PROFILES) {
		$c .= "<option value=\"$p\">$p</option>\n";
		}
	$GTOOLS::TAG{'<!-- COPYFROM -->'} = $c;

	$template_file = 'profile-add.shtml';	
	}



##
##
##
if ($ACTION eq 'PROFILE-CREATE') {
	$ACTION = 'PROFILES';
	my $CODE = $ZOOVY::cgiv->{'CODE'};
	$CODE =~ s/[\W_]+//gs;
	if (length($CODE)<3) { 
		$ACTION = 'PROFILE-ADD'; 
		push @MSGS, "ERROR|Code must be at least 3 characters long";
		}
	else {
		my $ref = {};
		if ($ZOOVY::cgiv->{'COPYFROM'} ne '') {
			$ref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$ZOOVY::cgiv->{'COPYFROM'});
			}
		$ref->{'prt:id'} = int($ZOOVY::cgiv->{'PRT'});
		$ref->{'zoovy:site_partition'} = $ref->{'prt:id'};
		&EBAY2::PROFILE::store($USERNAME,$PRT,$CODE,$ref);
		push @MSGS, "SUCCESS|Created profile: $CODE";
		}
	}

##



##
##
##
if ($ACTION eq 'CHOOSER-PREVIEW') {
	my $HWIZTEMPLATE = $ZOOVY::cgiv->{'TEMPLATE'};
	if (!defined($HWIZTEMPLATE)) { $HWIZTEMPLATE = ''; }
	$GTOOLS::TAG{'<!-- TEMPLATE -->'} = $HWIZTEMPLATE;

	
	if (defined($ZOOVY::cgiv->{'JSMAPPING'}) && ($ZOOVY::cgiv->{'JSMAPPING'} ne '')) { 
		%TEMPLATE::JSMAPPING = %{&ZTOOLKIT::fast_deserialize($ZOOVY::cgiv->{'JSMAPPING'})}; 
		} 
	else { 
		%TEMPLATE::JSMAPPING = (); 
		}

	my %HIDEHASH;
	foreach my $zuri (keys %TEMPLATE::JSMAPPING) {
		$TEMPLATE::HIDEHASH{$TEMPLATE::JSMAPPING{$zuri}} = $ZOOVY::cgiv->{$zuri};
		}
	$GTOOLS::TAG{'<!-- JSMAPPING -->'} = &ZTOOLKIT::fast_serialize(\%TEMPLATE::JSMAPPING);

	my ($path, $style) = split('-',$HWIZTEMPLATE);
	$NSREF->{'ebay:template'} = $HWIZTEMPLATE;
	&EBAY2::PROFILE::store($USERNAME,$PRT,$TEMPLATE::NS,$NSREF);
	# &ZOOVY::savemerchantns_attrib($USERNAME,$TEMPLATE::NS,'ebay:template',$HWIZTEMPLATE);
	$TEMPLATE::PRODUCT = '***GREEK***';

	my $elementref = HTMLWIZ::fetch_elements($USERNAME,$HWIZTEMPLATE);

	## GREEKIFY NON-MERCHANT ELEMENTS
	require Text::Greeking;
	my $g = Text::Greeking->new;
	$g->paragraphs(1,2); # min of 1 paragraph and a max of 2
   $g->sentences(2,5); # min of 2 sentences per paragraph and a max of 5
	$g->words(8,16); # min of 8 words per sentence and a max of 16
	foreach my $e (@{$elementref}) {
		# print STDERR Dumper($e);
		my $TYPE = $e->{'attrib'}->{'TYPE'};
		if (not defined($TYPE)) { $TYPE = 'unknown'; }
		if ($e->{'attrib'}->{'NAME'} !~ /^merchant\:/) {		## only do non-global
			$e->{'attrib'}->{'LOADFROM'} = '';

			if ($TYPE eq 'IMAGE') { $e->{'attrib'}->{'VALUE'} = '[logo]'; }
			elsif ($TYPE eq 'TEXTBOX') { $e->{'attrib'}->{'VALUE'} = $TYPE.': '.substr($g->generate,0,80); }
			else { $e->{'attrib'}->{'VALUE'} = $TYPE.': '.$g->generate; }
			$TEMPLATE::HIDEHASH{ $e->{'attrib'}->{'NAME'} } = $e->{'attrib'}->{'VALUE'};
			}
		else {
			&TEMPLATE::smart_save($e->{'attrib'}->{'NAME'}, \$TEMPLATE::HIDEHASH{$e->{'attrib'}->{'NAME'}});
			}
		}
	## END GREEKING

	my $html = &HTMLWIZ::fetch_html($USERNAME,$HWIZTEMPLATE);
	$html = &HTMLWIZ::buildHTML($USERNAME,$html,$elementref,0);

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $html;
	$GTOOLS::TAG{'<!-- DATE -->'} = &ZTOOLKIT::pretty_date(time(),1);
	$template_file = 'chooser-preview.shtml';

	push @BC, { name=>'Profile Edit: '.$CODE };
	push @BC, { name=>'Template Preview' };
	}









if ($ACTION eq 'PROFILES') {
	$template_file = 'index-profiles.shtml';
	
	my ($aref) = EBAY2::list_accounts($USERNAME);
	my %TOKENS = ();
	my %EIAS = ();
	foreach my $act (@{$aref}) { 
		$TOKENS{$act->{'EBAY_EIAS'}} = $act->{'EBAY_USERNAME'}; 
		}

	require ZOOVY;
	my ($profilesref) = &EBAY2::PROFILE::list($USERNAME,$PRT);
	my @PROFILES = ();
	foreach my $p (@{$profilesref}) { push @PROFILES, $p->{'CODE'}; }
	my $c = '';
	my $i = 0;
	foreach my $code (sort @PROFILES) {
		my $ref = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$code);
		my $eias = $ref->{'ebay:eias'};
		my $ebayuser = '<font color="red"><i>Not Configured</i></font>';
		if (defined $TOKENS{$eias}) {
			$ebayuser = $TOKENS{$eias};
			}

		my $ebaytemplate = $ref->{'ebay:template'};
		if ($ebaytemplate eq '') {
			$ebaytemplate = '<font color="red"><i>Not Configured</i></font>';
			}

		$c .= "<tr class=\"".((($i++%2)==0)?'r0':'r1')."\">";
		$c .= "<td><a href=\"index.cgi?ACTION=PROFILE-COMPANYEDIT&NS=$code\">[Listing Template]</a></td>";
		$c .= "<td><a href=\"index.cgi?ACTION=PROFILE-POLICYEDIT&CODE=$code\">[eBay Policies]</a></td>";
		$c .= "<td><a href=\"index.cgi?ACTION=PROFILE-SHIPPING&CODE=$code\">[eBay Shipping]</a></td>";
		$c .= "<td nowrap>$code</td>";	
		$c .= "<td nowrap>$ebayuser</td>";
		$c .= "<td nowrap>$ebaytemplate</td>";	
#		if (not defined $version) { 
#			$c .= '<td nowrap><font color="red"><b>NOT CONFIGURED</b></font></td><td></td>'; 
#			}
#		else { 
			my $guid = time().'-'.$i;
			$c .= "<td nowrap><a href=\"/biz/batch/index.cgi?VERB=NEW&EXEC=UTILITY&APP=EBAY_UPDATE&GUID=$guid&.function=refresh&.profile=$code\">[Refresh Listings]</a></td>";
#			}
		$c .= "</tr>";
		}

	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;

	push @BC, { name=>'View Profiles' };
	}


if ($ACTION eq 'PROFILE-POLICYEDIT') {
	$template_file = 'mgr-config.shtml';
	$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;

	require GTOOLS::Form;
	my ($eb) = EBAY2->new($USERNAME,PRT=>$PRT);
	if (not defined $eb) {
		}
	else {
		$GTOOLS::TAG{'<!-- EBAY_ACCOUNT -->'} = $eb->ebay_username();
		$GTOOLS::TAG{'<!-- EBAY_EIAS -->'} = $eb->ebay_eias();
		$GTOOLS::TAG{'<!-- CHKOUT_STYLE -->'} = $eb->get('CHKOUT_STYLE');
		}

	if ($eb->ebay_eias() ne $NSREF->{'ebay:eias'}) {
		$GTOOLS::TAG{'<!-- EBAY_ACCOUNT -->'} = '?';
		push @MSGS, "WARN|This profile is mapped to another account (possibly on another partition), the eBay username: ".$eb->ebay_username()." will be configured *AFTER* the save button below is pressed.";
		}

	open F, "/httpd/static/counters.txt";
	my %counters = ();
	while (<F>) { 
		next if (/#/);
		my ($categoryname,$flag,$directory,$pretty, $width, $height) = split("\t",$_);	
		next if ($directory eq '');
		## /images/samples/counters/$directory.gif
		$counters{ $directory }= "$categoryname/$pretty ($width x $height)"
		}
	close F;
	push @PROFILE_INFO, { 'type'=>'select', sort=>'value', js=>qq~
		onChange="thisFrm.counterimg.src='/images/samples/counters/'+thisFrm.elements['ebay:counter'].value+'.gif';"
		~, key=>'ebay:counter', set=>\%counters, default=>'blank' };
	if (not defined $counters{$NSREF->{'ebay:counter'}}) { $NSREF->{'ebay:counter'} = 'blank'; }
	$GTOOLS::TAG{'<!-- ebay:counter -->'} = $NSREF->{'ebay:counter'}; 

	foreach my $fields (@PROFILE_INFO) {
		# print STDERR Dumper($fields);
		my $type = $fields->{'type'};
		my $key = $fields->{'key'};
		next if (($type eq '') || (not defined $GTOOLS::Form::funcs{$type}));
		print STDERR "TYPE: $type\n";

		$fields->{'data'} = $NSREF->{$key};
		$GTOOLS::TAG{'<!-- '.$type.'!'.$key.' -->'} = 	$GTOOLS::Form::funcs{$type}->(%{$fields});
		}	
	$GTOOLS::TAG{'<!-- TEMPLATE -->'} = $NSREF->{'ebay:template'};

	
	my ($aref) = EBAY2::list_accounts($USERNAME);
	my $c = ''; my $found = 0;
	foreach my $act (@{$aref}) {
		if ($NSREF->{'ebay:eias'} eq $act->{'EBAY_EIAS'}) {
			$found++;
			$c .= "<option selected ";
			}
		else {
			$c .= "<option ";
			}
		$c .= " value=\"$act->{'EBAY_EIAS'}\">$act->{'EBAY_USERNAME'}</option>\n"; 
		}
	if (not $found) { $c = "<option value=0>Not Selected - Cannot Launch</option>".$c; }
	$GTOOLS::TAG{"<!-- TOKENS -->"} = $c;

	push @BC, { name=>'View Profiles',link=>'/biz/setup/ebay/index.cgi?ACTION=PROFILES', target=>'_top' };
	push @BC, { name=>'Profile Edit: '.$CODE };
	}



if ($ACTION eq 'REPORTS') {
	$template_file = 'index-reports.shtml';
	push @BC, { name=>'Reports' };
	}


##
## pass in an empty array (OUTPUTREF) - this calls itself recursively and populates the OUTPUTREF
##
sub herdStoreCats {
	my ($PATH,$catsref,$OUTPUTREF) = @_;

	my %cats = ();
   foreach my $ci0 (@{$catsref}) {
		next unless ($ci0->{'name'} eq 'CustomCategory') || ($ci0->{'name'} eq 'ChildCategory');
		my %vars = ();
		my @CHILDREN = ();
		foreach my $e0 (@{$ci0->{'content'}}) {
			next if ($e0->{'type'} ne 'e');
			if ($e0->{'name'} eq 'ChildCategory') {
				push @CHILDREN, $e0;
				}
			else {
				$vars{ $e0->{'name'} } = $e0->{'content'}->[0]->{'content'};
				}
			}

		# print "in [$PATH] $vars{'CategoryID'} $vars{'Name'}\n";
		if (scalar(@CHILDREN)>0) {
			# print "PATH: $vars{'CategoryID'} $vars{'Name'} has children\n";
			herdStoreCats("$vars{'Name'} ($vars{'CategoryID'})",\@CHILDREN,$OUTPUTREF);
			}
		else {
			if ($vars{'CategoryID'}<100) { $vars{'CategoryID'}--; }	# shift down by 1 so Category 1=1 (instead of 2 which is how eBay does it)
			push @{$OUTPUTREF}, [ $vars{'CategoryID'}, (($PATH ne '')?"$PATH / ":'')."$vars{'Name'}" ];
			}
		}

	}


if ($ACTION eq 'LOAD-STORE-CATEGORIES') {
	require EBAY2::STORE;
	my ($count) = &EBAY2::STORE::rebuild_categories($USERNAME,$ZOOVY::cgiv->{'EIAS'});
	if ($count <= 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class=\"warning\">WARNING: Found $count eBay Store categories.<br><div class=\"hint\">Please verify your token is valid and that the account has an eBay store associated with it.</div></div>";
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class=\"success\">SUCCESS: Loaded $count eBay Store categories</div>";
		}
	$ACTION = 'SETUP';
	}



if ($ACTION eq 'FIX-PROFILE') {
	my ($epnsref) = &EBAY2::PROFILE::fetch($USERNAME,$PRT,$ZOOVY::cgiv->{'PROFILE'});
	$epnsref->{'ebay:eias'} = $ZOOVY::cgiv->{'EIAS'};
	&EBAY2::PROFILE::store($USERNAME,$PRT,$ZOOVY::cgiv->{'PROFILE'},$epnsref);
	# &ZOOVY::savemerchantns_attrib($USERNAME,$ZOOVY::cgiv->{'PROFILE'},'ebay:eias',$ZOOVY::cgiv->{'EIAS'});
	$ACTION = 'SETUP';
	}


if ($ACTION eq 'SETUP') {
	$template_file = 'index-accounts.shtml';

	require EXTERNAL;
	my ($accountsref) = &EBAY2::list_accounts($USERNAME);


	my $c = '';
	my $i = 0;
	my %PRT = ();
	foreach my $act (@{$accountsref}) {


		my $sandbox = (!$act->{'IS_SANDBOX'})?'':q~ <font color=red>SANDBOX</font> ~;
		$i++;
		$c .= "<tr class=\"".(($i%2==0)?'r0':'r1')."\">";
		$c .= "<td valign='top'>#$act->{'PRT'}</td>";
		$c .= "<td valign='top'>
		<div>$act->{'EBAY_USERNAME'} $sandbox</div>
		</td>";
		$c .= "<td valign='top'>$act->{'EBAY_TOKEN_EXP'}</td>";


		if ($act->{'IS_EPU'}>0) {
			$c .= qq~<br><font color='success'><b>EBAY POWER USER (EPU): ENABLED</b></font>~;
			}

		if (not defined $PRT{$act->{'PRT'}}) {
			$PRT{$act->{'PRT'}} = $act->{'EBAY_USERNAME'};
			}
		else {
			$c .= qq~<br>
<font color='red'>
WARNING: this account shares partition with eBay account $PRT{$act->{'PRT'}} (each eBay account *should* be on it's own partition)
</font>~;
			}


		if ($act->{'EBAY_EIAS'} eq '') {
			$c .= "<br><font color='red'>CRITICAL ERROR: this token does not know the EIAS of the ebay account it's associated with. please remove it and re-create.</font><br>";
			}
#		elsif ($profEIAS eq '') {
#			$c .= "<br><font color='red'>WARNING: checkout profile[$profile] is not configured yet (hint: you still need to associate the profile with this eBay account).</font>";
#			}
#		elsif ($profEIAS ne $act->{'EBAY_EIAS'}) {
#			require URI::Escape;
#			my $x = URI::Escape::uri_escape($act->{'EBAY_EIAS'});
#			$c .= qq~<br>
#<font color='red'>
#WARNING: EIAS in profile[$profile] 
#points at different eBay account!
#Checkout &amp; Emails will not work properly.<br>
#<a href="index.cgi?ACTION=FIX-PROFILE&PROFILE=$profile&EIAS=$x">[CLICK HERE TO FIX]</a>
#</font>~;
#			}
		$c .= "</td>";
		

		$c .= "<td valign='top'>";
		$c .= "<a href=\"index.cgi?ACTION=DEACTIVATE&ID=$act->{'ID'}\">[Deactivate]</a><br>";
		# $c .= "<a href=\"index.cgi?ACTION=FEEDBACK&DBID=$act->{'ID'}\">[Feedback]</a><br>";
		if ($act->{'HAS_STORE'}) { $c .= "<a href=\"index.cgi?ACTION=LOAD-STORE-CATEGORIES&ID=$act->{'ID'}\">[Refresh Store Categories]</a><br>"; }
		$c .= "<a href=\"redirhack.cgi?SignIn&m=$USERNAME&eb=$act->{'EBAY_USERNAME'}&sandbox=".($act->{'IS_SANDBOX'}?'on':'')."\"> [Refresh Authorization Token]</a><br>"; 
		$c .= "<br>";
		$c .= "</td>";
		$c .= "<td valign=top nowrap>";

		my %hash = ();
		$hash{'#Site'} = 0;
		$hash{'DetailLevel'} = 'ReturnAll';
		my $r = undef; 
		my ($eb2) = EBAY2->new($USERNAME,PRT=>$PRT);
		if (defined $eb2) {
			($r) = $eb2->api('GetUser',\%hash,preservekeys=>['User']);
			}

		if ((not defined $r) && (not defined $eb2)) {
			## 
			$c .= "<div class='error'>EBAY TOKEN NOT INITIALIZED</div>";
			}
		elsif ((defined $r->{'.ERRORS'}) && (scalar(@{$r->{'.ERRORS'}})>0)) {
			if ((defined $r->{'.ERRORS'}->[0]->{'id'}) && ($r->{'.ERRORS'}->[0]->{'id'} eq 'HTTP:500')) {
				$c .= "<div class='error'>Could not connect to eBay API</div>";
				}
			else {
				$c .= "<div class='error'>STATUS: INVALID</div>";
				if ($LU->is_zoovy()) {
					$c .= 'UNHANDLED DUMP (ZOOVY EMPLOYEES ONLY):<pre>'.Dumper($r).'</pre>';
					}
				}
			}
		elsif (&ZTOOLKIT::mysql_to_unixtime($act->{'EBAY_TOKEN_EXP'})<time()) {
			$c .= "<div class='error'>STATUS: EXPIRED</div><br>";
			$c .= "<div class='hint'>This token has expired. eBay requires you renew your authentication token once per year.</div>";
			}
		elsif ($act->{'ERRORS'}>999) {
			$c .= "STATUS: SOFT-FAILURE<br>";
			$c .= "ERRORS: $act->{'ERRORS'}<br>";
			$c .= "<div class='hint'>This token has received more than 1,000 errors without a success - which indicates a configuration problem. It has been disabled/suspended BY ZOOVY and must be reset after the problems are corrected.</div><br>";
			}
		else {
			$c .= "<div class='success'>STATUS: VALID</div>";
			if ($act->{'DO_IMPORT_LISTINGS'}==0) {
				$c .= "<div class='warning'>AUTO-SYNC: Disabled</div>";
				}
			else {
				$c .= "<div class='success'>AUTO-SYNC: Enabled</div>";
				}
			$c .= "ERRORS: $act->{'ERRORS'}<br>";
			$c .= "LISTINGS POLL: ".&ZTOOLKIT::pretty_date($act->{'LAST_POLL_GMT'},1)."<br>";
			}
		$c .= "</td>";		
#		$c .= "<td><pre>".Dumper($r)."</pre></td>";

		$c .= "</tr>\n";


		}
	$c = "<tr class='zoovysub1header'>
	<td>Partition</td>
	<td>Username</td>
	<td>Token Expires</td>
	<td>Actions</td>
	<td>Token Status</td>
</tr>".$c;
	$GTOOLS::TAG{'<!-- ACCOUNTS -->'} = $c;

	push @BC, { name=>'eBay Accounts', target=>'_top' },
	}

if ($ACTION eq 'REGISTER') {
	$template_file = 'index-register.shtml';
	if ($FLAGS =~ /,PKG=Z4FX,/) { $template_file = 'index-z4fx-register.shtml'; }

#	require DOMAIN::TOOLS;
#	my ($dref) = DOMAIN::TOOLS::syndication_profiles($USERNAME);
#	my $c = '';
#	foreach my $k (sort keys %{$dref}) {
#		$c .= "<option value=\"$k\">[$k] $dref->{$k}</option>";
#		}
#	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
	$GTOOLS::TAG{'<!-- PROFILE -->'} = &ZWEBSITE::checkout_profile($USERNAME,$PRT);

	my %NEED = ();
	if ($LU->get('todo.setup.ebay')) {
		require TODO;
	   my $t = TODO->new($USERNAME);
   	my ($need,$tasks) = $t->setup_tasks('ebay',LU=>$LU);
	   $GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('ebay',$tasks);
	   }

	push @BC, { name=>'Register eBay Account', target=>'_top' },
	}

if ($ACTION eq 'SETTOKEN_SUCCESS') {
	$template_file = 'index-settoken_success.shtml';
	}


$GTOOLS::TAG{'<!-- MERCHANT -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- ACTION -->'} = '';
$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;

my @TABS = ();
push @TABS, { name=>'eBay Account', link=>'/biz/setup/ebay/index.cgi?ACTION=SETUP', selected=>($ACTION eq 'SETUP')?1:0 };
push @TABS, { name=>'Checkout', link=>'/biz/setup/ebay/index.cgi?ACTION=CHECKOUT', selected=>($ACTION eq 'CHECKOUT')?1:0 };
push @TABS, { name=>'Profiles', link=>'/biz/setup/ebay/index.cgi?ACTION=PROFILES',  selected=>(($ACTION eq 'PROFILES-SHIPPING') || ($ACTION eq 'PROFILES'))?1:0  };
#push @TABS, { name=>'Showcase', link=>'/biz/setup/ebay/index.cgi?ACTION=SHOWCASE',  selected=>($ACTION eq 'SHOWCASE')?1:0  };
push @TABS, { name=>'Feedback', link=>'/biz/setup/ebay/index.cgi?ACTION=FEEDBACK',  selected=>($ACTION eq 'FEEDBACK')?1:0  };
push @TABS, { name=>'Global Shortcuts &amp; Notes', link=>'/biz/setup/ebay/index.cgi?ACTION=SHORTCUTS',  selected=>($ACTION eq 'SHORTCUTS')?1:0  };

my $foo = '';
&GTOOLS::output(
	'title'=>'eBay Account Manager',
	'file'=>$template_file,	
	'bc'=>\@BC,
	'tabs'=>\@TABS,
	'abslink'=>1,
	'msgs'=>\@MSGS,
	'help'=>"#50726",
	'todo'=>1,
	'header'=>1);
&DBINFO::db_user_close();

