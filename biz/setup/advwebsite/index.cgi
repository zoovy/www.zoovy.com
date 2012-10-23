#!/usr/bin/perl

use strict;
use lib "/httpd/modules"; 
use CGI;
use Storable;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require ORDER;
require LUSER;
require DOMAIN::TOOLS;

my ($LU) = LUSER->authenticate(flags=>'_S&8');

if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

if ($USERNAME eq '') { exit; }

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
my $VERB = $ZOOVY::cgiv->{'MODE'};
if ($VERB eq '') { $VERB = 'GENERAL'; }

my $ACTION = $ZOOVY::cgiv->{'ACTION'};
my $HELP = '';

my $template_file = '';
my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);

my @MSGS = ();

if ($VERB eq 'CUSTOMERADMIN-SAVE') {
	
	$webdbref->{"order_status_notes_disable"} = (defined $ZOOVY::cgiv->{'order_status_notes_disable'})?1:0;
	$webdbref->{"order_status_disable_login"} = (defined $ZOOVY::cgiv->{'order_status_disable_login'})?1:0;
	$webdbref->{"order_status_hide_events"} = (defined $ZOOVY::cgiv->{'order_status_hide_events'})?1:0;
	$webdbref->{'order_status_reorder'} = (defined $ZOOVY::cgiv->{'order_status_reorder'})?1:0;
	$webdbref->{"disable_cancel_order"} = (defined $ZOOVY::cgiv->{'disable_cancel_order'})?1:0;
	$LU->log("SETUP.CHECKOUT.CUSTOMER","Updated Customer Admin Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = 'CUSTOMERADMIN';
	}

if ($VERB eq 'CUSTOMERADMIN') {
	$template_file = 'customeradmin.shtml';
	my $c = '';


	$GTOOLS::TAG{'<!-- ORDER_STATUS_NOTES_DISABLE -->'} = ($webdbref->{"order_status_notes_disable"})?'checked':'';
	$GTOOLS::TAG{"<!-- ORDER_STATUS_DISABLE_LOGIN_CHECKED -->"} = ($webdbref->{"order_status_disable_login"}) ? 'checked':'';
	$GTOOLS::TAG{"<!-- ORDER_STATUS_HIDE_EVENTS_CHECKED -->"} = ($webdbref->{"order_status_hide_events"}) ? 'checked':'';
	$GTOOLS::TAG{'<!-- ORDER_STATUS_REORDER -->'} = ($webdbref->{'order_status_reorder'})?'checked':'';
	$GTOOLS::TAG{"<!-- DISABLE_CANCEL_ORDER -->"} = ($webdbref->{"disable_cancel_order"}) ? 'checked':'';

	$GTOOLS::TAG{'<!-- HEADER_PANELS -->'} = $c;	
	}



if ($VERB eq 'INTERNATIONAL') {
	## 
	my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$PRT);
	
	my %currency = ( 'USD'=>1 );
	my %language = ( 'ENG'=>1 );
	if ($ACTION eq 'INTERNATIONAL-SAVE') {
		foreach my $x (keys %{$ZOOVY::cgiv}) {
			if ($x =~ /C\*(.*?)$/) { $currency{uc($1)}++; }
			if ($x =~ /L\*(.*?)$/) { $language{uc($1)}++; }			
			}
		$currency{'USD'}++;
		$language{'ENG'}++;

		$prtinfo->{'currency'} = join(',', sort keys %currency);
		$prtinfo->{'language'} = join(',', sort keys %language);
		&ZWEBSITE::prtsave($USERNAME,$PRT,$prtinfo);
		}

	foreach my $cur (split(',',$prtinfo->{'currency'})) { $currency{$cur}++; }
	foreach my $lang (split(',',$prtinfo->{'language'})) { $language{$lang}++; }

	require SITE::MSGS;
	my $checked = ''; my $r = '';
	my $c = '';
	foreach my $cur (sort keys %SITE::MSGS::CURRENCIES) {
		my $curref = $SITE::MSGS::CURRENCIES{$cur};
		if (defined $currency{$cur}) { $r='rs'; $checked = ' checked '; } else { $r='r0'; $checked = ''; }

		$c .= "<tr class=\"$r\"><td><input type=\"checkbox\" $checked name=\"C*$cur\"></td><td>$cur</td><td>$curref->{'pretty'}</td><td>$curref->{'region'}</td></tr>";
		}
	$GTOOLS::TAG{'<!-- CURRENCIES -->'} = $c;

	$c = '';
	foreach my $lang (sort keys %SITE::MSGS::LANGUAGES) {
		my $langref = $SITE::MSGS::LANGUAGES{$lang};
		if (defined $language{$lang}) { $r = 'rs'; $checked = ' checked '; } else { $r='r0'; $checked = ''; }
		
		$c .= "<tr class=\"$r\"><td><input type=\"checkbox\" $checked name=\"L*$lang\"></td><td>$lang</td><td>$langref->{'pretty'}</td><td>$langref->{'in'}</td></tr>";
		}
	$GTOOLS::TAG{'<!-- LANGUAGES -->'} = $c;


	$template_file = 'international.shtml';
	}


if ($VERB eq 'CREATE-MESSAGE') {
	require SITE::MSGS;
	my ($SM) = SITE::MSGS->new($USERNAME,RAW=>1,PRT=>$PRT);

	my $ERROR = '';

	my $MSGID = $ZOOVY::cgiv->{'ID'};
	if ($MSGID eq '') { $ERROR = "MSGID is blank"; }
	my $LANG = $ZOOVY::cgiv->{'LANG'};
	my $MSG = "New Message";
	my $TITLE = $ZOOVY::cgiv->{'TITLE'};
	my $CATEGORY = $ZOOVY::cgiv->{'CATEGORY'};
	$SM->create($MSGID,$LANG,$LUSERNAME,$TITLE,$CATEGORY);		

	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>successfully created message $MSGID, go to the appropriate category to edit.</div>";
	
	$VERB = 'NEW-MESSAGE';
	}


if ($VERB eq 'NEW-MESSAGE') {
	require SITE::MSGS;	
	my $c = "<option>-</option>";
	foreach my $l (keys %SITE::MSGS::LANGUAGES) {
		$c .= sprintf("<option value=\"%s\">%s</option>",$l,$SITE::MSGS::LANGUAGES{$l}->{'pretty'});
		}
	$GTOOLS::TAG{'<!-- LANGUAGES -->'} = $c;

	$c = "<option>-</option>";
	foreach my $l (keys %SITE::MSGS::CATEGORIES) {
		$c .= "<option value=\"$l\">$SITE::MSGS::CATEGORIES{$l}</option>";
		}
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;	

	$template_file = 'new-message.shtml';
	}


if ( ($VERB eq 'CC-MESSAGES') || ($VERB eq 'CHK-MESSAGES') || ($VERB eq 'SYS-MESSAGES') || ($VERB eq 'PAY-MESSAGES') || ($VERB eq 'PAGE-MESSAGES')) {
	require SITE::MSGS;
	my ($SM) = SITE::MSGS->new($USERNAME,RAW=>1,PRT=>$PRT);

	$GTOOLS::TAG{'<!-- EDITOR -->'} = "<tr><td><i>Please select a message to edit.</i></td></tr>";
	my $EDITID = '';
	my $LANG = '';

	if ($ACTION eq 'SAVE') {
		$EDITID = $ZOOVY::cgiv->{'ID'};
		$LANG = $ZOOVY::cgiv->{'LANG'};

		my $BLOCKED = 0;
		if (not defined $ZOOVY::cgiv->{'MSG'}) {
			## it's always okay to reset it.
			}
		elsif ($ZOOVY::cgiv->{'MSG'} =~ /\<script/) {
			## javascript warning.
			if ($LU->is_zoovy()) {
				push @MSGS, "WARNING|ZOOVY EMPLOYEE: It is NOT recommended/support placing Javascript into the System Messages, please use Setup | Plugins instead.";
				}
			elsif ($LU->is_bpp()) {
				push @MSGS, "ERROR|BPP settings prohibit Javascript from being placed into System Messages, please Setup | Plugins instead.";
				$BLOCKED++;
				}
			elsif ($LU->is_level('7')) {
				push @MSGS, "WARNING|It is NOT recommended/support placing Javascript into the System Messages, please use Setup | Plugins instead.";
				}
			else {
				push @MSGS, "ERROR|Your account type may not place Javascript into System Messages. Please use Setup | Plugins instead."; 
				$BLOCKED++;
				}
			}
		elsif ($ZOOVY::cgiv->{'MSG'} =~ /src\=[\"\']?http\:/) {
			## system messages.
			if ($LU->is_zoovy()) {
				push @MSGS, "WARNING|ZOOVY EMPLOYEE: It is NOT recommended/support placing Javascript into the System Messages, please use Setup | Plugins instead.";
				}
			elsif ($LU->is_bpp()) {
				push @MSGS, "ERROR|BPP settings prohibit insecure (http) references from being placed into System Messages, please Setup | Plugins instead.";
				$BLOCKED++;
				}
			elsif ($LU->is_level('7')) {
				## no warning, 
				push @MSGS, "WARNING|Please review your content, it appears you may have an insecure reference in your html that could cause issues.";
				}
			else {
				push @MSGS, "ERROR|Your account type may not place Javascript into System Messages. Please use Setup | Plugins instead."; 
				$BLOCKED++;
				}
			}
	
		my ($result) = -1;
		if (not $BLOCKED) {
			$result = $SM->save($EDITID,$ZOOVY::cgiv->{'MSG'},$LANG,$LUSERNAME);
			}

		if ($result==-1) {
			push @MSGS, "WARNING|We're sorry, but your save attempt was blocked by account safety/recommended usage guidelines.";
			}
		elsif ($result==0) {
			$LU->log("SETUP.SYSTEMMSG","Reset/Restored System Message $EDITID ($LANG)","SAVE");
			}
		else {
			$LU->log("SETUP.SYSTEMMSG","Updated Message $EDITID ($LANG)","SAVE");
			}
		push @MSGS, "SUCCESS|Successfully Saved $EDITID ($LANG)";
		}

	if ($ACTION eq 'EDIT') {
		$EDITID = $ZOOVY::cgiv->{'ID'};
		$LANG = $ZOOVY::cgiv->{'LANG'};

		my ($msgref) = $SM->getref($EDITID, $LANG);
		
		my $jsorig = $msgref->{'defaultmsg'};
		$jsorig = &ZOOVY::incode($jsorig);
		$jsorig =~ s/'/\\'/gs;

		$GTOOLS::TAG{'<!-- EDITOR -->'} = qq~
<tr>
	<td>Field Name: <b>$msgref->{'pretty'}</b></td>
</tr>
~;

		if ($msgref->{'hint'} ne '') {
			$GTOOLS::TAG{'<!-- EDITOR -->'} .= qq~
<tr>
	<td><span class="hint">$msgref->{'hint'}</span></td>
</tr>
~;
			}

		$GTOOLS::TAG{'<!-- EDITOR -->'} .= qq~
<tr>
	<td>
	<textarea rows=3 cols=60 onFocus="this.rows=25;" style="font-size: 8pt;"  name="MSG">~.&ZOOVY::incode($msgref->{'msg'}).qq~</textarea>

	<div class="warning">
	Placing tracking iframes or Javascript code into messages is NOT recommended or supported in any way - in fact we're positive doing so will break something you don't intend.
	Tracking code should ONLY be placed in the third party area in Setup / Plugins.
	</div>

	</td>
</tr>
<tr>
	<td>
	<input type="submit" class="button" value=" Save ">
	<input type="button" class="button" value=" Reset " onClick="
document.thisFrm.MSG.value='$jsorig'; return(true);
">
	</td>
</tr>
~;


if ($msgref->{'cat'} == 50) {
	## CHECKOUT MESSAGE!
	$GTOOLS::TAG{'<!-- EDITOR -->'} .= qq~
<tr>
	<td class="zoovysub1header">Payment Messages Help</td>
</tr>
<tr><td>
<div align="left">
<div class="hint">
Remember that these messages may contain HTML, however the HTML will be stripped for text based email.
</div>
<table>
	<tr><td class="zoovysub1header" colspan='2'><font class='title'>Variables available for substitution:</font></td></tr>
	~;

	foreach my $macroref (@SITE::MSGS::MACROS) {	
		next if ($macroref->[0] != 50);	# payment!
		if ($macroref->[1] eq '') {
			## title
			$GTOOLS::TAG{'<!-- EDITOR -->'} .= "<tr><td class='zoovysub1header' colspan=2>$macroref->[2]</td></tr>";
			}
		else {
			## macro
			$GTOOLS::TAG{'<!-- EDITOR -->'} .= "<tr><td>$macroref->[1]</td><td>$macroref->[2]</td></tr>";
			}
		}
	
	$GTOOLS::TAG{'<!-- EDITOR -->'} .= qq~
</table>
</td></tr>

~;
		}
	}


	$GTOOLS::TAG{'<!-- LANG -->'} = $LANG;
	$GTOOLS::TAG{'<!-- EDITID -->'} = $EDITID;


	my $c = '';
	my $r = '';

	my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$PRT);
	my @LANGUAGES = split(',',$prtinfo->{'language'});
	$GTOOLS::TAG{'<!-- MODE -->'} = $VERB;

	my @msgids = ();
	my $SMDREF = $SM->fetch_msgs();

	if ($VERB eq 'CHK-MESSAGES') {

		my ($webdbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,0);
		if ((defined $webdbref->{'@CHECKFIELD'}) && (scalar($webdbref->{'@CHECKFIELD'})>0)) {
			## make a copy of the SITE::MSG::DEFAULTS so we don't trash the global one!
			$SMDREF = Storable::dclone(\%SITE::MSGS::DEFAULTS);
			foreach my $ref (@{$webdbref->{'@CHECKFIELD'}}) {
				$ref->{'defaultmsg'} = '';
				$ref->{'created_gmt'} = 0;
				$ref->{'cat'} = 10;
				$ref->{'pretty'} = 'Custom Checkout Field: '.$ref->{'type'};
				$SMDREF->{'~'.$ref->{'id'}} = $ref;
				}
			}
		}

	@msgids = reverse sort keys %{$SMDREF};

	use Data::Dumper;
	print STDERR Dumper($SMDREF);


	foreach my $msgid (@msgids) {
		foreach my $lang (@LANGUAGES) {
			my ($msgref) = $SM->getref($msgid,$lang);


			next if (($VERB eq 'CHK-MESSAGES') && ($msgref->{'cat'}!=10) && ($msgref->{'cat'}>0));
			next if (($VERB eq 'PAY-MESSAGES') && ($msgref->{'cat'}!=50)  && ($msgref->{'cat'}>0));
			next if (($VERB eq 'SYS-MESSAGES') && ($msgref->{'cat'}!=1)  && ($msgref->{'cat'}>0));
			next if (($VERB eq 'PAGE-MESSAGES') && ($msgref->{'cat'}!=11)  && ($msgref->{'cat'}>0));
			next if (($VERB eq 'CC-MESSAGES') && ($msgref->{'cat'}!=20)  && ($msgref->{'cat'}>0));
			
			if (substr($msgid,0,1) eq '~') {
				foreach my $k (keys %{$SMDREF->{$msgid}}) {
					next if (defined $msgref->{$k});
					$msgref->{$k} = $SMDREF->{$msgid}->{$k};
					}
				}

			$r = ($r eq 'r0')?'r1':'r0';

			if (($EDITID eq $msgid) && ($lang eq $LANG)) { $r = 'rs'; }	## display as currently selected.
			$c .= "<tr class=\"$r\">";
			$c .= "<td valign='top'><a href=\"index.cgi?MODE=$VERB&ACTION=EDIT&LANG=$lang&ID=$msgid\">$msgid</a></td>";
			$c .= "<td valign='top'>".&ZOOVY::incode($msgref->{'pretty'})."</td>";
			$c .= "<td valign='top'>".&ZTOOLKIT::pretty_date($msgref->{'created_gmt'},-1)." : $msgref->{'luser'}</td>";
			$c .= "<td align=center>$lang</td>";
			$c .= "</tr>";
			}
		}


	$GTOOLS::TAG{'<!-- MESSAGES -->'} = $c;
	$template_file = 'messages.shtml';
	}



if (uc($ACTION) eq 'WEBUI-SAVE') {

	}

if (uc($ACTION) eq "GENERAL-SAVE") {

	$webdbref->{"cart_quoteshipping"} = $ZOOVY::cgiv->{'cart_quoteshipping'};
	my $customer_management = $ZOOVY::cgiv->{'customer_management'};
	if (!defined($customer_management)) { $customer_management = 'DEFAULT'; }
	$webdbref->{"customer_management"} = $customer_management;

	$webdbref->{'checkout'} = $ZOOVY::cgiv->{'checkout'};

	if ($FLAGS =~ /WEB/) {	
		$webdbref->{'chkout_phone'} = $ZOOVY::cgiv->{'chkout_phone'};

		if ($ZOOVY::cgiv->{'order_num'}+0 != $ZOOVY::cgiv->{'hidden_order_num'}+0) {
			&ORDER::reset_order_id($USERNAME,$ZOOVY::cgiv->{'order_num'}+0);
			}
		if ($ZOOVY::cgiv->{'chkout_order_notes'}) { $webdbref->{"chkout_order_notes"} = 1; } 
		else { $webdbref->{"chkout_order_notes"} = 0; }

		$webdbref->{'chkout_payradio'} = (defined $ZOOVY::cgiv->{'chkout_payradio'})?1:0;
		$webdbref->{'chkout_shipradio'} = (defined $ZOOVY::cgiv->{'chkout_shipradio'})?1:0;

		$webdbref->{"chkout_save_payment_disabled"} = (defined $ZOOVY::cgiv->{'chkout_save_payment_disabled'})?1:0;
		$webdbref->{"chkout_allowphone"} = (defined $ZOOVY::cgiv->{'chkout_allowphone'})?1:0;
		$webdbref->{"chkout_billshipsame"} = (defined $ZOOVY::cgiv->{'chkout_billshipsame'})?1:0;
		$webdbref->{'chkout_roi_display'} = (defined $ZOOVY::cgiv->{'chkout_roi_display'})?1:0;

	
		my $customer_privacy = $ZOOVY::cgiv->{'customer_privacy'};
		if (!defined($customer_privacy)) { $customer_privacy = 'NONE'; }
		$webdbref->{"customer_privacy"} = $customer_privacy;

#		if ($ZOOVY::cgiv->{'adult_content'} =~ /on/i) { 
#			$webdbref->{"adult_content"} = "on";
#			if ($FLAGS !~ /,ADULT,/) { &ZACCOUNT::create_exception_flags($USERNAME,'ADULT',0,0); }
#			} 
#		else {
#			$webdbref->{"adult_content"} = "off";
#			if ($FLAGS =~ /,ADULT,/) { &ZACCOUNT::delete_exception_flags(0,$USERNAME,'ADULT'); }
#			}

		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = 
		"<div>Some settings on this page require the <a href='/biz/configurator?VERB=VIEW&BUNDLE=WEB'>WEB</a><br> feature bundle to change, because they require functionality which is not currently available to your account.</div>";
		}


	$LU->log("SETUP.CHECKOUT","Updated Checkout Settings","SAVE");
	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	$VERB = 'GENERAL';
	}


# handle general parameters.
if ($VERB eq 'GENERAL') {

	my $chkout = $webdbref->{'checkout'};
	$GTOOLS::TAG{'<!-- CHECKOUT_LEGACY -->'} = ($webdbref->{'checkout'} eq '')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP1 -->'} = ($webdbref->{'checkout'} eq 'op1')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP2 -->'} = ($webdbref->{'checkout'} eq 'op2')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP3 -->'} = ($webdbref->{'checkout'} eq 'op3')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP4 -->'} = ($webdbref->{'checkout'} eq 'op4')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP5 -->'} = ($webdbref->{'checkout'} eq 'op5')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP6 -->'} = ($webdbref->{'checkout'} eq 'op6')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP7 -->'} = ($webdbref->{'checkout'} eq 'op7')?'checked':'';
	$GTOOLS::TAG{'<!-- CHECKOUT_OP8 -->'} = ($webdbref->{'checkout'} eq 'op8')?'checked':'';

	my $chkout_phone = $webdbref->{'chkout_phone'};
	if (!defined($chkout_phone)) { $chkout_phone = 'REQUIRED'; }
	$GTOOLS::TAG{'<!-- CHKOUT_PHONE_REQUIRED -->'} = '';
	$GTOOLS::TAG{'<!-- CHKOUT_PHONE_OPTIONAL -->'} = '';
	$GTOOLS::TAG{'<!-- CHKOUT_PHONE_UNREQUESTED -->'} = '';
	$GTOOLS::TAG{'<!-- CHKOUT_PHONE_'.$chkout_phone.' -->'} = ' checked ';

	$GTOOLS::TAG{'<!-- CHKOUT_PAYRADIO -->'} = ($webdbref->{"chkout_payradio"})?'checked':'';
	$GTOOLS::TAG{'<!-- CHKOUT_SHIPRADIO -->'} = ($webdbref->{"chkout_shipradio"})?'checked':'';
	
	$GTOOLS::TAG{'<!-- CM_STANDARD -->'} = '';
	$GTOOLS::TAG{'<!-- CM_NICE -->'} = '';
	$GTOOLS::TAG{'<!-- CM_STRICT -->'} = '';
	$GTOOLS::TAG{'<!-- CM_PASSIVE -->'} = '';
	$GTOOLS::TAG{'<!-- CM_DISABLED -->'} = '';
	$GTOOLS::TAG{'<!-- CM_PRIVATE -->'} = '';
	$GTOOLS::TAG{'<!-- CM_MEMBER -->'} = '';	
	my $customer_management = $webdbref->{"customer_management"};
	if (!defined($customer_management)) { $customer_management = 'STANDARD'; }
	if ($customer_management eq 'DEFAULT') { $customer_management = 'STANDARD'; }
	$GTOOLS::TAG{'<!-- CM_'.$customer_management.' -->'} = ' CHECKED ';

	$GTOOLS::TAG{'<!-- CP_NONE -->'} = '';
	$GTOOLS::TAG{'<!-- CP_SAFE -->'} = '';
	$GTOOLS::TAG{'<!-- CP_OTHER -->'} = '';
	my $customer_privacy = $webdbref->{"customer_privacy"};
	if (!defined($customer_privacy)) { $customer_privacy = 'NONE'; }
	$GTOOLS::TAG{'<!-- CP_'.$customer_privacy.' -->'} = ' CHECKED ';


	$GTOOLS::TAG{'<!-- CHKOUT_ORDER_NOTES_CHECKED -->'} = ($webdbref->{"chkout_order_notes"})?'checked':'';
	$GTOOLS::TAG{'<!-- CHKOUT_SAVE_PAYMENT_DISABLED_CHECKED -->'} = ($webdbref->{'chkout_save_payment_disabled'})?'checked':'';

	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_0 -->"} = ''; 
	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_1 -->"} = ''; 
	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_2 -->"} = ''; 	
	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_3 -->"} = ''; 
	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_4 -->"} = ''; 
	$GTOOLS::TAG{"<!-- CART_QUOTESHIPPING_".int($webdbref->{"cart_quoteshipping"})." -->"} = 'checked'; 

	$GTOOLS::TAG{"<!-- CHKOUT_BILLSHIPSAME_CHECKED -->"} = ($webdbref->{"chkout_billshipsame"}) ? 'checked':'';

	$GTOOLS::TAG{'<!-- CHKOUT_ROI_DISPLAY -->'} = ($webdbref->{'chkout_roi_display'})?'checked':'';


	if ($LU->is_anycom()) { # different checkout preferences 
		$template_file = 'checkout-anycom.shtml';
		}
	else {
		$template_file = 'checkout-zoovy.shtml';
		my $DOMAIN = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
		$GTOOLS::TAG{'<!-- DOMAIN -->'} = $DOMAIN;
		$GTOOLS::TAG{'<!-- CHECKOUTLINK -->'} = sprintf("http://www.$DOMAIN/checkout");
		}
	$HELP = '#50305';
	}


if ($VERB eq 'CHECKFIELD') {
	$template_file = 'checkfield.shtml';
	}


my @TABS = ();
push @TABS, { selected=>($VERB eq 'GENERAL')?1:0, name=>'Checkout Config', link=>'/biz/setup/checkout', target=>'_top' };
push @TABS, { selected=>($VERB eq 'CUSTOMERADMIN')?1:0, name=>'Customer Admin Config', link=>'/biz/setup/checkout?MODE=CUSTOMERADMIN', target=>'_top' };
if ($FLAGS =~ /,WEB,/) {
	push @TABS, {  selected=>($VERB eq 'CHK-MESSAGES')?1:0, name=>'Checkout Msgs', link=>'/biz/setup/checkout/index.cgi?MODE=CHK-MESSAGES', target=>'_top' };
	push @TABS, {  selected=>($VERB eq 'SYS-MESSAGES')?1:0, name=>'System Msgs', link=>'/biz/setup/checkout/index.cgi?MODE=SYS-MESSAGES', target=>'_top' };
	push @TABS, {  selected=>($VERB eq 'PAY-MESSAGES')?1:0, name=>'Payment Msgs', link=>'/biz/setup/checkout/index.cgi?MODE=PAY-MESSAGES', target=>'_top' };
	push @TABS, {  selected=>($VERB eq 'PAGE-MESSAGES')?1:0, name=>'Special Page Msgs', link=>'/biz/setup/checkout/index.cgi?MODE=PAGE-MESSAGES', target=>'_top' };
	push @TABS, {  selected=>($VERB eq 'CC-MESSAGES')?1:0, name=>'CallCenter Msgs', link=>'/biz/setup/checkout/index.cgi?MODE=CC-MESSAGES', target=>'_top' };
	push @TABS, {  selected=>($VERB eq 'NEW-MESSAGE')?1:0, name=>'Create Message', link=>'/biz/setup/checkout/index.cgi?MODE=NEW-MESSAGE', target=>'_top' };
#	push @TABS, {  selected=>($VERB eq 'CHECKFIELD')?1:0, name=>'Checkout Fields', link=>'/biz/setup/checkout/index.cgi?MODE=CHECKFIELD', target=>'_top' };
	}

&GTOOLS::output(
   'title'=>'Setup : Checkout Properties',
   'file'=>$template_file,
   'header'=>'1',
	'jquery'=>'1',
   'help'=>$HELP,
   'tabs'=>\@TABS,
	'msgs'=>\@MSGS,
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Checkout Properties',link=>'http://www.zoovy.com/biz/setup/checkout','target'=>'_top', },
      ],
   );




exit;


