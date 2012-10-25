#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use Data::Dumper;

require CUSTOMER;
require GTOOLS;
require LUSER;
require ZTOOLKIT;
require GIFTCARD;
require CUSTOMER::TICKET;
require CUSTOMER::BATCH;
require CART2;
require ZOOVY;
require SITE;

#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/manage",2,'_M&8');
#my ($LU) = LUSER->new($USERNAME,$LUSER);

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my @MSGS = ();

if ($MID<=0) { exit; }
$GTOOLS::TAG{"<!-- PRT -->"} = $PRT;
$GTOOLS::TAG{'<!-- GUID -->'} = time();
#if (not defined $LU) { warn "Auth"; exit; }

#my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
#if ($MID<=0) { warn "No auth"; exit; }

my @TABS = ();
my @BC = ();
push @BC, {'name'=>'Utilities', 'link'=>'/biz/utilities'};
push @BC, {'name'=>'Customer Manager','link'=>'/biz/utilities/customer'};

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $template_file = '';


if ($ZOOVY::cgiv->{'FROM_HEADER'}) {
	## this app is also run directly from the header and uses the variables below:
	$VERB='SEARCH-NOW';
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'customer:email') { $ZOOVY::cgiv->{'scope'} = 'email'; }
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'customer:lastname') {$ZOOVY::cgiv->{'scope'} = 'lastname'; }
	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'customer:orderid') {$ZOOVY::cgiv->{'scope'} = 'orderid'; }
	$ZOOVY::cgiv->{'searchfor'} = $ZOOVY::cgiv->{'HEADER_VALUE'};
	}



my $CID = -1; 	# THE CID WE're EDITING
if (defined $ZOOVY::cgiv->{'CID'}) { 
	$CID = int($ZOOVY::cgiv->{'CID'});
	$GTOOLS::TAG{'<!-- CID -->'} = $CID;
	}

if ($VERB eq '') { $VERB = 'SEARCH'; }
if ($VERB eq 'QUICKSEARCH') { $VERB = 'SEARCH-NOW'; }


##
##
##
if ($VERB eq 'DELETE') {
	$LU->log("CUSTOMER.DELETE","deleted customer $CID","INFO");
	&CUSTOMER::delete_customer($USERNAME,$CID);
	$VERB = 'SEARCH';
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>Customer $ZOOVY::cgiv->{'CUSTOMER'} successfully deleted!</font>";
	}



##
##
##
if ($VERB eq 'SEARCH-NOW') {
	my $history = $ZOOVY::cgiv->{'history'};
	my $searchfor = $ZOOVY::cgiv->{'searchfor'};

	## strip leading and trailing whitespace
	$searchfor =~ s/^[\s]+//g;
	$searchfor =~ s/[\s]+$//g;

	my $scope = $ZOOVY::cgiv->{'scope'};	 
	# note: scope may be email, name, full (includes billing/shipping/etc.)

	# use Data::Dumper; print STDERR Dumper('SEARCH-NOW',$searchfor);

	my ($result) = &CUSTOMER::BATCH::find_customers($USERNAME,$searchfor,$scope,$history);	
	if (scalar(@{$result})==0) {
		$GTOOLS::TAG{'<!-- RESULTS -->'} = "<i>No results found</i>";
		$VERB = 'SEARCH';
		}
	elsif (scalar(@{$result})==1) { 
		## we only found one result so lets go EDIT.
		($CID) = $result->[0]->{'CID'};
		$ZOOVY::cgiv->{'CID'} = $CID;
		$VERB = 'EDIT';

		if ($ZOOVY::cgiv->{'link'} ne '') {
			## hmm... the user requested we link the order to this customer record
			my ($C) = CUSTOMER->new($USERNAME,CID=>$CID);
			my ($CART2) = CART2->new_from_oid($USERNAME,$ZOOVY::cgiv->{'link'});
			$C->associate_order($CART2);
			}
		}
	else {
		my @rows = ();
		require GTOOLS::Table;

		foreach my $uref (@{$result}) {
			push @rows, [ 
				"&nbsp;<a href=\"index.cgi?VERB=EDIT&CID=$uref->{'CID'}\">[Edit]</a>", 
				$uref->{'FIRSTNAME'}.' '.$uref->{'LASTNAME'}, 
				&ZOOVY::incode($uref->{'EMAIL'}), 
				$uref->{'PHONE'},
				$uref->{'PRT'}
				];
			}

		$GTOOLS::TAG{'<!-- RESULTS -->'} = &GTOOLS::Table::buildTable([
				{ width=>50, title=>'Edit' },
				{ width=>200, title=>'Customer Name' },
				{ width=>200, title=>'Email' },
				{ width=>100, title=>'Phone' },
				{ width=>30, title=>'Prt' },

				], \@rows, width=>600);

		$VERB = 'SEARCH';
		}
	}


##
##
##
if ($VERB eq 'SEARCH') {

	if (not defined $ZOOVY::cgiv->{'scope'}) { 
		$ZOOVY::cgiv->{'scope'} = 'email';
		}
	$GTOOLS::TAG{'<!-- SCOPE_ORDERID -->'} = ($ZOOVY::cgiv->{'scope'} eq 'orderid')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_EMAIL -->'} = ($ZOOVY::cgiv->{'scope'} eq 'email')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_NAME -->'} = ($ZOOVY::cgiv->{'scope'} eq 'name')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_CID -->'} = ($ZOOVY::cgiv->{'scope'} eq 'cid')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_PHONE -->'} = ($ZOOVY::cgiv->{'scope'} eq 'phone')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_GIFTCARD -->'} = ($ZOOVY::cgiv->{'scope'} eq 'giftcard')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_EBAY -->'} = ($ZOOVY::cgiv->{'scope'} eq 'ebay')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_NOTES -->'} = ($ZOOVY::cgiv->{'scope'} eq 'notes')?' checked ':'';
	$GTOOLS::TAG{'<!-- SCOPE_ACCOUNT_MANAGER -->'} = ($ZOOVY::cgiv->{'scope'} eq 'account_manager')?' checked ':'';

	$GTOOLS::TAG{'<!-- HISTORY_0 -->'} = ($ZOOVY::cgiv->{'history'} eq '0')?' selected ':'';
	$GTOOLS::TAG{'<!-- HISTORY_90 -->'} = ($ZOOVY::cgiv->{'history'} eq '90')?' selected ':'';
	$GTOOLS::TAG{'<!-- HISTORY_365 -->'} = ($ZOOVY::cgiv->{'history'} eq '365')?' selected ':'';

	$GTOOLS::TAG{'<!-- SEARCHFOR -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'searchfor'});
	$template_file = 'index-search.shtml';
	}


##
##
##
if ($VERB eq 'REPORTS') {
	$template_file = 'index-reports.shtml';
	}


if ($VERB eq 'LOGIN') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID,INIT=>0x1);

	$LU->log("MANAGE.CUSTOMER","Logged into customer account: $CID","INFO");

	my $login = $C->email();
	my $pass = $C->get('INFO.PASSWORD');

	require DOMAIN::TOOLS;
	my $sdomain = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
	my $url = undef;

	# $SITE::SREF->{'+sdomain'} = $sdomain;
	if (not defined $sdomain) {
		$url = "#SORRY_NO_PRIMARY_DOMAIN_CONFIGURED_FOR_USERNAME=$USERNAME\_PRT=$PRT";
		print "Content-Type: text/plain\n\n";
		print "NO PRIMARY DOMAIN FOR USER:$USERNAME PRT:$PRT\n";
		}
	else {
		require SITE;
		($url) = SITE->new($USERNAME,'PRT'=>$PRT,'DOMAIN'=>"www.$sdomain")->URLENGINE()->get("login");
		#require SITE::URLS;
		#my $SITE_URLS = SITE::URLS->new($USERNAME,secure=>1,prt=>$PRT,sdomain=>"www.$sdomain");
		#$url = $SITE_URLS->get('login');
		print STDERR "SENDING TO: $url?login=$login&password=$pass\n";
		print "Location: $url?login=$login&password=$pass\n\n";
		}

	# print "Content-type: text/plain\n\n";
	exit;
	}




if ($VERB eq 'EMAIL') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID,INIT=>0x1);
	$GTOOLS::TAG{'<!-- CID -->'} = $CID;
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $C->email();

	#require DOMAIN::TOOLS;
	#my $sdomain = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
	my $PROFILE = &ZOOVY::prt_to_profile($USERNAME,$PRT);
	require SITE;
	my ($SITE) = SITE->new($USERNAME,'NS'=>$PROFILE,'PRT'=>$PRT);
	require SITE::EMAILS;
	my ($SE) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
	my $c = '';

	my $msgs = $SE->available("ACCOUNT");
	require JSON::XS;
	$GTOOLS::TAG{'<!-- JSON_EMAILS -->'} = JSON::XS::encode_json($msgs);

	foreach my $msgref (@{$msgs}) {
		$c .= "<tr>";
		$c .= qq~<td><input type='radio' onClick='load_email("$msgref->{'MSGID'}");' name='MSGID' value='$msgref->{'MSGID'}'></td>~;
		$c .= "<td>".&ZOOVY::incode($msgref->{'MSGID'})."</td>";
		$c .= "<td>".&ZOOVY::incode($msgref->{'MSGFORMAT'})."</td>";
		$c .= "<td>".&ZOOVY::incode($msgref->{'MSGSUBJECT'})."</td>";
		## $msgref->{'MSGBODY'};
		$c .= "</tr>";
		# $c .= Dumper($msgref);
		}
	$GTOOLS::TAG{'<!-- EMAILS -->'} = "<table>$c</table>";

	
	$template_file = 'email.shtml';
	}


if ($VERB eq 'EMAIL-SEND') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID,INIT=>0x1);

	$GTOOLS::TAG{'<!-- CID -->'} = $CID;
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $C->email();

	my $PROFILE = &ZOOVY::prt_to_profile($USERNAME,$PRT);
	require SITE;
	my ($SITE) = SITE->new($USERNAME,'PRT'=>$PRT,'PROFILE'=>$PROFILE);
	require SITE::EMAILS;
	my ($SE) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE);
	my ($MSGID) = $ZOOVY::cgiv->{'MSGID'};

	my ($ERR) = $SE->sendmail($MSGID,'PRT'=>$PRT,'RECIPIENT'=>$C->email(),'CUSTOMER'=>$C,
		MSGSUBJECT=>$ZOOVY::cgiv->{'MSGSUBJECT'},
		MSGBODY=>$ZOOVY::cgiv->{'MSGBODY'},
		);
	if (not $ERR) {
		$GTOOLS::TAG{'<!-- MSG -->'} = "<div class='success'>Your message was sent, you may now close this window.</div>";
		}
	else {
		$GTOOLS::TAG{'<!-- MSG -->'} = "<div class='error'>Error: ($ERR) $SITE::EMAILS::ERRORS{$ERR}</div>";
		}
	$template_file = 'window-close.shtml';
	}



if ($VERB eq 'CREATE-SAVE') {

	# validate the data
	my @ERRORS = ();
	if ($ZOOVY::cgiv->{'EMAIL'} eq '') {
		push @ERRORS, "Email is a required field.";
		}
	elsif (not &ZTOOLKIT::validate_email($ZOOVY::cgiv->{'EMAIL'})) {
		push @ERRORS, "Email address appears to be invalid, plesae double check";
		}


	# print STDERR Dumper(@ERRORS);

	# no errors, lets try to add. 
	if (scalar(@ERRORS)==0) {
		my $EMAIL = $ZOOVY::cgiv->{'EMAIL'};
		my $NEWS = (defined($ZOOVY::cgiv->{'NEWS'}))?1:0;
		my $ORDER = $ZOOVY::cgiv->{'ORDER'};
		srand(time());
		my $PASS = $ZOOVY::cgiv->{'PASS'};
		if (defined($ZOOVY::cgiv->{'PASS'})) { $PASS = reverse(sprintf("%x",(time()*rand())%1000000)); } else { $PASS = ''; }

		my $firstname = $ZOOVY::cgiv->{'FIRST'};
		my $lastname = $ZOOVY::cgiv->{'LAST'};
		my $CID = int($ZOOVY::cgiv->{'CID'});

		my $thisPRT = $PRT;
		if ($CID>0) {
			($thisPRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
			}

		my ($C) = CUSTOMER->new($USERNAME,PRT=>$thisPRT,CID=>$CID,
				EMAIL=>$EMAIL,
				CREATE=>3,
				DATA=>{
					'INFO.FIRSTNAME'=>$firstname,
					'INFO.LASTNAME'=>$lastname,
					'INFO.NEWSLETTER'=>$NEWS,
					},
				ORDER=>$ORDER);

		if (not defined $C) { 
			push @ERRORS, "Could not create customer.";
			}
		else {
			$CID = $C->cid();
			$ZOOVY::cgiv->{'CID'} = $C->cid();
			$LU->log("CUSTOMER.CREATE","Created customer $EMAIL","INFO");
			}
		}

	# now, lets proceed based on what happened earlier
	if (scalar(@ERRORS)>0) {
		# data didn't hold up to the rigid validation!
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font class='error'>".join("<br>",@ERRORS)."</font>";
		$VERB = 'CREATE';
		} 
	else {
		# No errors, lets create and move to the next step (whatever that may be)
		$VERB = 'EDIT';		
		}

	}

##
##
##
if ($VERB eq 'CREATE') {
	$GTOOLS::TAG{"<!-- EMAIL -->"} = &ZOOVY::incode($ZOOVY::cgiv->{'EMAIL'});
	$GTOOLS::TAG{"<!-- FIRST -->"} = &ZOOVY::incode($ZOOVY::cgiv->{'FIRST'});
	$GTOOLS::TAG{"<!-- LAST -->"} = &ZOOVY::incode($ZOOVY::cgiv->{'LAST'});
	$GTOOLS::TAG{"<!-- ORDER -->"} = &ZOOVY::incode((defined $ZOOVY::cgiv->{'ORDER'})?$ZOOVY::cgiv->{'ORDER'}:'');
		
	if ($ZOOVY::cgiv->{'VERB'} eq 'CREATE-SAVE') {
		$GTOOLS::TAG{'<!-- NEWS_CHECKED -->'} = (defined $ZOOVY::cgiv->{'NEWS'})?'checked':'';
		$GTOOLS::TAG{'<!-- PASS_CHECKED -->'} = (defined $ZOOVY::cgiv->{'PASS'})?'checked':'';
		$GTOOLS::TAG{'<!-- NOTIFY_CHECKED -->'} = (defined $ZOOVY::cgiv->{'NOTIFY'})?'checked':'';
		}
	else {	
		$GTOOLS::TAG{"<!-- NEWS_CHECKED -->"} = "CHECKED";
		$GTOOLS::TAG{"<!-- PASS_CHECKED -->"} = "CHECKED";
		$GTOOLS::TAG{"<!-- NOTIFY_CHECKED -->"} = "CHECKED";	
		}
	$template_file = 'create.shtml';
	}




##
## saves customer top level settings + schedule (wholesale only)
##
if ($VERB eq 'SAVE') {
	
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,int($ZOOVY::cgiv->{'CID'}));
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'CUSTOMER'},CID=>$ZOOVY::cgiv->{'CID'},INIT=>1);
	my $msg = '';

	if ($C->email() ne $ZOOVY::cgiv->{'email'}) { 
		my $email = $ZOOVY::cgiv->{'email'};
		my ($resultcid) = $C->change_email($email);
		if ($resultcid != $C->cid()) {
			$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>ERROR: The email address $email is already in use by customer #$resultcid</font>";
			}
		}
		
	my $changed = 0;	

	if ($ZOOVY::cgiv->{'reset_hint'}) {
		## makes it impossible to recover password using a hint
		$C->set_attrib('INFO.HINT_ANSWER','');
		$C->set_attrib('INFO.HINT_NUM',0);
		$changed++;
		}

	 if ($ZOOVY::cgiv->{'mirror_changes'}) {
			## hmm.. what is this supposed to do?
			}
		 
	$C->fetch_attrib('INFO');
	if ($C->fetch_attrib('INFO.FIRSTNAME') ne $ZOOVY::cgiv->{'firstname'}) {
		$changed++;
	   $C->set_attrib('INFO.FIRSTNAME',$ZOOVY::cgiv->{'firstname'});
		}
	
	my $IS_LOCKED = (defined $ZOOVY::cgiv->{'is_locked'})?1:0;
	if ($C->fetch_attrib('INFO.IS_LOCKED') != $IS_LOCKED) {
		$changed++;
		$C->set_attrib('INFO.IS_LOCKED',$IS_LOCKED);
		}

	if ($C->fetch_attrib('INFO.LASTNAME') ne $ZOOVY::cgiv->{'lastname'}) {
		$changed++;
	   $C->set_attrib('INFO.LASTNAME',$ZOOVY::cgiv->{'lastname'});
		}
		
	if ($C->fetch_attrib('INFO.PASSWORD') ne $ZOOVY::cgiv->{'pass'}) {
		print STDERR "Changing password to ".$ZOOVY::cgiv->{'pass'}."\n";
		$LU->log("MANAGE.CUSTOMER.PASSRESET",sprintf("Password was reset for customer %d",$C->cid()),"INFO");
		$C->initpassword(set=>$ZOOVY::cgiv->{'pass'});
		# &CUSTOMER::change_password($USERNAME,$C->{'_EMAIL'},$ZOOVY::cgiv->{'pass'});
		}
	
	## Handle Newsletter
	my $newsletter = 0;
	foreach my $i (1..15) {
		if (defined $ZOOVY::cgiv->{'newsletter_'.$i}) { $newsletter += (1<<($i-1)); }
		}	
	if ($C->fetch_attrib('INFO.NEWSLETTER') != $newsletter) {
		$C->set_attrib('INFO.NEWSLETTER',$newsletter); $changed++;
		}
	

	if (($ZOOVY::cgiv->{'NEW_NOTE'} ne '') && ($FLAGS =~ /,CRM,/)) {
		#$C->save_note($LUSERNAME,$ZOOVY::cgiv->{'NEW_NOTE'});
		$C->save_note($LUSERNAME,$ZOOVY::cgiv->{'NEW_NOTE'});
		}

	## Handle Wholesale
	if ($FLAGS =~ /,WS,/) {
		$changed++;
		$C->set_attrib('INFO.SCHEDULE',$ZOOVY::cgiv->{'SCHEDULE'}); 

		my $wsinfo = $C->fetch_attrib('WS');
		$wsinfo->{'ALLOW_PO'} = ($ZOOVY::cgiv->{'ALLOW_PO'})?1:0;
		$wsinfo->{'RESALE'} = ($ZOOVY::cgiv->{'RESALE'})?1:0;
		## NOTE: popup saves this data directly
		# $wsinfo->{'LOGO'} = $ZOOVY::cgiv->{'logoImg'};
		$wsinfo->{'RESALE_PERMIT'} = ($ZOOVY::cgiv->{'RESALE_PERMIT'})?$ZOOVY::cgiv->{'RESALE_PERMIT'}:'';
		$wsinfo->{'CREDIT_LIMIT'} = ($ZOOVY::cgiv->{'CREDIT_LIMIT'})?$ZOOVY::cgiv->{'CREDIT_LIMIT'}:'';
		$wsinfo->{'CREDIT_BALANCE'} = ($ZOOVY::cgiv->{'CREDIT_BALANCE'})?$ZOOVY::cgiv->{'CREDIT_BALANCE'}:'';
		$wsinfo->{'ACCOUNT_MANAGER'} = ($ZOOVY::cgiv->{'ACCOUNT_MANAGER'})?$ZOOVY::cgiv->{'ACCOUNT_MANAGER'}:'';
		$C->set_attrib('WS',$wsinfo);
		}
		
	print STDERR "CHANGED: $changed\n";
	if ($changed) {
		$C->save();
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>Saved changes</font>";
		}
		
	$VERB = 'EDIT';
	}

#######################################################################################
##
## Saves a billing/shipping or wholesale (WS) address
##
if ($VERB eq 'SAVEADDR') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,int($ZOOVY::cgiv->{'CID'}));

	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'CUSTOMER'},CID=>$ZOOVY::cgiv->{'CID'});
	print STDERR "CIDxxx: ".$C->cid()."\n";
	my $TYPE = lc($ZOOVY::cgiv->{'TYPE'});


	my $addr = undef;
	my $SHORTCUT = $ZOOVY::cgiv->{'SHORTCUT'};

	if (($SHORTCUT ne '') || (uc($TYPE) eq 'WS')) {
		$addr = $C->fetch_address(uc($TYPE),$SHORTCUT);
		}
	else {
		$SHORTCUT = $ZOOVY::cgiv->{'SET_SHORTCUT'};
		}
	if ($SHORTCUT eq '') { $SHORTCUT = $TYPE; } 	# a sane default
		
	$addr->{$TYPE.'_firstname'} = $ZOOVY::cgiv->{'firstname'};
	$addr->{$TYPE.'_lastname'} = $ZOOVY::cgiv->{'lastname'};
	$addr->{$TYPE.'_phone'} = $ZOOVY::cgiv->{'phone'};
	$addr->{$TYPE.'_company'} = $ZOOVY::cgiv->{'company'};
	$addr->{$TYPE.'_address1'} = $ZOOVY::cgiv->{'address1'};
	$addr->{$TYPE.'_address2'} = $ZOOVY::cgiv->{'address2'};
	$addr->{$TYPE.'_city'} = $ZOOVY::cgiv->{'city'};
	$addr->{$TYPE.'_state'} = $ZOOVY::cgiv->{'state'};
	
	if ($ZOOVY::cgiv->{'country'} ne '' && 
		 $ZOOVY::cgiv->{'country'} !~ m/US/i && 
		 $ZOOVY::cgiv->{'country'} !~ m/United States/i){
		$addr->{$TYPE.'_int_zip'} = $ZOOVY::cgiv->{'zip'};
		$addr->{$TYPE.'_zip'} = '';
		}
	else { 
		$addr->{$TYPE.'_int_zip'} = '';
		$addr->{$TYPE.'_zip'} = $ZOOVY::cgiv->{'zip'}; 
		}
	
	$addr->{$TYPE.'_country'} = $ZOOVY::cgiv->{'country'};
	$addr->{$TYPE.'_email'} = $ZOOVY::cgiv->{'email'};
	$addr->{$TYPE.'_province'} = $ZOOVY::cgiv->{'province'};
	
	if (uc($TYPE) eq 'WS') { 
		$addr->{'BILLING_CONTACT'} = $ZOOVY::cgiv->{'BILLING_CONTACT'};
		$addr->{'BILLING_PHONE'} = $ZOOVY::cgiv->{'BILLING_PHONE'};
		$C->set_attrib('WS',$addr);
		}
	else {
		$C->add_address($TYPE,$addr,'SHORTCUT'=>$SHORTCUT);
		}

	$C->save();

	$VERB = 'EDIT';
	}


#######################################################################################
##
## address editor
##
if ($VERB eq 'CREATEADDR') {
	$GTOOLS::TAG{'<!-- TYPE -->'} = $ZOOVY::cgiv->{'TYPE'};
	$GTOOLS::TAG{'<!-- CUSTOMER -->'} = '';
	$GTOOLS::TAG{'<!-- SHOW_SHORTCUT -->'} = qq~
	<input size=6 maxlength=6 type="textbox" name="SET_SHORTCUT" value="">
	<div class='hint'>Shortcut is a 6 digit code that will be used by the customer to refer to uniqely this address ex: "HOME" or "WORK"</div>
	~;
	$GTOOLS::TAG{'<!-- FIRSTNAME -->'} = $ZOOVY::cgiv->{'firstname'};
	$GTOOLS::TAG{'<!-- LASTNAME -->'} = $ZOOVY::cgiv->{'lastname'};
	$GTOOLS::TAG{'<!-- COMPANY -->'} = $ZOOVY::cgiv->{'company'};
	$GTOOLS::TAG{'<!-- ADDRESS1 -->'} = $ZOOVY::cgiv->{'address1'};
	$GTOOLS::TAG{'<!-- ADDRESS2 -->'} = $ZOOVY::cgiv->{'address2'};
	$GTOOLS::TAG{'<!-- CITY -->'} = $ZOOVY::cgiv->{'city'};
	$GTOOLS::TAG{'<!-- STATE -->'} = $ZOOVY::cgiv->{'state'};
	$GTOOLS::TAG{'<!-- PROVINCE -->'} = $ZOOVY::cgiv->{'province'};
	$GTOOLS::TAG{'<!-- ZIP -->'} = $ZOOVY::cgiv->{'zip'};
	$GTOOLS::TAG{'<!-- COUNTRY -->'} = $ZOOVY::cgiv->{'country'};
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $ZOOVY::cgiv->{'email'};
	$GTOOLS::TAG{'<!-- PHONE -->'} = $ZOOVY::cgiv->{'phone'};
	$GTOOLS::TAG{'<!-- CID -->'} = $CID;
	$GTOOLS::TAG{'<!-- CANCEL_URL -->'} = "document.location='index.cgi?POPUP=0&VERB=EDIT&CID=$CID';";
	$template_file = 'editaddr.shtml';
	}


if ($VERB eq 'NUKEADDR') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,int($ZOOVY::cgiv->{'CID'}));
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'CUSTOMER'},CID=>$ZOOVY::cgiv->{'CID'},INIT=>0xFF);
	my $TYPE = uc($ZOOVY::cgiv->{'TYPE'});	
	my $ADDR = uc($ZOOVY::cgiv->{'ADDR'});
	$C->nuke_addr($TYPE,$ADDR);
	$VERB = 'EDIT';	
	}

if ($VERB eq 'EDITADDR') {
	my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,int($ZOOVY::cgiv->{'CID'}));
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'CUSTOMER'},CID=>$ZOOVY::cgiv->{'CID'},INIT=>0xFF);
	my $TYPE = uc($ZOOVY::cgiv->{'TYPE'});
	
	$GTOOLS::TAG{'<!-- CUSTOMER -->'} = $C->email();
	$GTOOLS::TAG{'<!-- TYPE -->'} = $ZOOVY::cgiv->{'TYPE'};
	$GTOOLS::TAG{'<!-- CID -->'} = $ZOOVY::cgiv->{'CID'};
	$GTOOLS::TAG{'<!-- SHORTCUT -->'} = $ZOOVY::cgiv->{'SHORTCUT'};
	$GTOOLS::TAG{'<!-- SHOW_SHORTCUT -->'} = $ZOOVY::cgiv->{'SHORTCUT'};
	
	my $addr = undef;
	if (($TYPE eq 'WS') || ($TYPE eq 'BILL') || ($TYPE eq 'SHIP')) {
		$addr = $C->fetch_address($TYPE,$ZOOVY::cgiv->{'SHORTCUT'});
		}
	else {
		die("UNKNOWN ADDRESS TYPE: $TYPE"); # never reached
		}
	
	$TYPE = lc($TYPE);
	if (not defined $addr) {
		push @MSGS, "ERROR|Address: $TYPE.$ZOOVY::cgiv->{'SHORTCUT'} could not be loaded";
		}
	else {
		$GTOOLS::TAG{'<!-- SHOW_SHORTCUT -->'} = sprintf("%s %s",$addr->shortcut(),($addr->is_default()?' (default)':''));
		$GTOOLS::TAG{'<!-- FIRSTNAME -->'} = $addr->{$TYPE.'_firstname'};
		$GTOOLS::TAG{'<!-- LASTNAME -->'} = $addr->{$TYPE.'_lastname'};
		$GTOOLS::TAG{'<!-- COMPANY -->'} = $addr->{$TYPE.'_company'};
		$GTOOLS::TAG{'<!-- ADDRESS1 -->'} = $addr->{$TYPE.'_address1'};
		$GTOOLS::TAG{'<!-- ADDRESS2 -->'} = $addr->{$TYPE.'_address2'};
		$GTOOLS::TAG{'<!-- CITY -->'} = $addr->{$TYPE.'_city'};
		$GTOOLS::TAG{'<!-- STATE -->'} = $addr->{$TYPE.'_state'};
		$GTOOLS::TAG{'<!-- PROVINCE -->'} = $addr->{$TYPE.'_province'};

		if ($addr->{$TYPE.'_country'} ne '' && 
			 $addr->{$TYPE.'_country'} ne 'USA' && 
			 $addr->{$TYPE.'_country'} ne 'US' &&
			 $addr->{$TYPE.'_country'} ne 'United States of America'){
			$GTOOLS::TAG{'<!-- ZIP -->'} = $addr->{$TYPE.'_int_zip'};
			}
		else { $GTOOLS::TAG{'<!-- ZIP -->'} = $addr->{$TYPE.'_zip'}; }
		$GTOOLS::TAG{'<!-- COUNTRY -->'} = $addr->{$TYPE.'_country'};
		$GTOOLS::TAG{'<!-- EMAIL -->'} = $addr->{$TYPE.'_email'};
		$GTOOLS::TAG{'<!-- PHONE -->'} = $addr->{$TYPE.'_phone'};
		if ($TYPE eq 'ship' || $TYPE eq 'ws') {
			$GTOOLS::TAG{'<!-- BEGIN_HIDE_SHIP -->'} = '<!--';
			$GTOOLS::TAG{'<!-- END_HIDE_SHIP -->'} = '-->';
			}

		if ($TYPE eq 'ws') {
			$GTOOLS::TAG{'<!-- WHOLESALE -->'} = qq~
			<tr>
				<td>Purchasing Contact:</td><td><input type="textbox" name="BILLING_CONTACT" value="~.&ZOOVY::incode($addr->{'BILLING_CONTACT'}).qq~"></td><td><i>(For your internal use only)</i></td>
			</tr>
			<tr>
				<td>Purchasing Phone:</td><td><input type="textbox" name="BILLING_PHONE" value="~.&ZOOVY::incode($addr->{'BILLING_PHONE'}).qq~"></td><td><i>(For your internal use only)</i></td>
			</tr>
			~;
			}
		}

	$GTOOLS::TAG{'<!-- CANCEL_URL -->'} = "document.location='index.cgi?POPUP=0&VERB=EDIT&CID=".$C->cid()."';";

	$template_file = "editaddr.shtml";
	}


if ($VERB eq 'WALLET-REMOVE') {
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID);
	$C->wallet_nuke(int($ZOOVY::cgiv->{'SECUREID'}));
	$VERB = 'EDIT';
	}

if ($VERB eq 'WALLET-DEFAULT') {
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID);
	$C->wallet_update(int($ZOOVY::cgiv->{'SECUREID'}),'default'=>1);
	$VERB = 'EDIT';
	}

if ($VERB eq 'WALLET-SAVE') {
	my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID);
	my %params = ();
	$params{'CC'} = $ZOOVY::cgiv->{'CC'};
	$params{'YY'} = $ZOOVY::cgiv->{'YY'};
	$params{'MM'} = $ZOOVY::cgiv->{'MM'};
	$C->wallet_store(\%params);
	$VERB = 'EDIT';
	}

if ($VERB eq 'WALLET-VIEW') {
	if ($LU->is_zoovy()) {
		## sorry but zoovy employees cannot view the contents of wallets
		$GTOOLS::TAG{'<!-- CC -->'} = '**ZOOVY-EMPLOYEE-NOT-ALLOWED**';
		$template_file = 'view-wallet.shtml';
		}
	elsif ($LU->is_admin()) {
		my $SECUREID = int($ZOOVY::cgiv->{'SECUREID'});
		my ($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,CID=>$CID);
		$GTOOLS::TAG{'<!-- CID -->'} = $CID;
		$GTOOLS::TAG{'<!-- SECUREID -->'} = $SECUREID;
		my ($wallet) = $C->wallet_retrieve($SECUREID);
		foreach my $k ('CC','YY','MM') {
			$GTOOLS::TAG{"<!-- $k -->"} = $wallet->{$k};	
			}
		$LU->log("WALLET.VIEW","INFO","Opened cid#$CID wallet#$SECUREID");
		$template_file = 'view-wallet.shtml';
		}
	
	}

if ($VERB eq 'WALLET-ADD') {
	$GTOOLS::TAG{'<!-- CID -->'} = $CID;
	foreach my $k ('CC','YY','MM') {
		$GTOOLS::TAG{"<!-- $k -->"} = '';
		}
	$template_file = 'add-wallet.shtml';
	}



#######################################################################################
##
## 
##
if (($VERB eq 'EDIT') || ($VERB eq 'NUKENOTE')) {

	my ($C) = undef;
	if (defined $ZOOVY::cgiv->{'CID'}) {
		## got passed CID implicitly.
		my $CID = int($ZOOVY::cgiv->{'CID'});
		my ($PRT) = &CUSTOMER::cid_to_prt($USERNAME,$CID);
		($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'EMAIL'},CID=>$CID);
		}
	elsif (defined $ZOOVY::cgiv->{'EMAIL'}) {
		## got passed EMAIL
		($C) = CUSTOMER->new($USERNAME,PRT=>$PRT,EMAIL=>$ZOOVY::cgiv->{'EMAIL'});
		}
	else {
		die();
		}

	my $CID = $C->cid();

	if ($C->prt() != $PRT) {
		push @MSGS, sprintf("WARN|This customer exists on partition %d, you are logged into partition %d",$C->prt(),$PRT);
		}
	
	if ($VERB eq 'NUKENOTE') {
		$C->nuke_note( $ZOOVY::cgiv->{'NID'} );
		$VERB = 'EDIT';
		}

	if ($ZOOVY::cgiv->{'O'}) {
		## a order # was passed, make sure it's associated to this customer.
		&CUSTOMER::save_order_for_customer($USERNAME,$ZOOVY::cgiv->{'O'},$C->email());
		}

	$GTOOLS::TAG{'<!-- ORIGIN -->'} = $C->fetch_attrib('INFO.ORIGIN');
	if ($GTOOLS::TAG{'<!-- ORIGIN -->'} == 0) { $GTOOLS::TAG{'<!-- ORIGIN -->'} = 'CSV'; }
	elsif ($GTOOLS::TAG{'<!-- ORIGIN -->'} == 1) { $GTOOLS::TAG{'<!-- ORIGIN -->'} = 'Checkout'; }
	elsif ($GTOOLS::TAG{'<!-- ORIGIN -->'} == 2) { $GTOOLS::TAG{'<!-- ORIGIN -->'} = 'MailList'; }

	$GTOOLS::TAG{'<!-- IP -->'} = $C->fetch_attrib('INFO.IP');
	$GTOOLS::TAG{'<!-- CREATED_GMT -->'} = $C->fetch_attrib('INFO.CREATED_GMT');

	$GTOOLS::TAG{'<!-- CID -->'} = $C->cid();
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $C->email();
	$GTOOLS::TAG{'<!-- CREATED -->'} = &ZTOOLKIT::pretty_date($C->fetch_attrib('INFO.CREATED_GMT'),1);
	$GTOOLS::TAG{'<!-- FIRSTNAME -->'} = $C->fetch_attrib('INFO.FIRSTNAME');
	$GTOOLS::TAG{'<!-- LASTNAME -->'} = $C->fetch_attrib('INFO.LASTNAME');
	$GTOOLS::TAG{'<!-- PASSWORD -->'} = $C->fetch_attrib('INFO.PASSWORD')?$C->fetch_attrib('INFO.PASSWORD'):'';
	$GTOOLS::TAG{'<!-- CHK_IS_LOCKED -->'} = ($C->fetch_attrib('INFO.IS_LOCKED')?'checked':'');

	my $newsletter = $C->fetch_attrib('INFO.NEWSLETTER');
	$GTOOLS::TAG{'<!-- CHK_NEWSLETTER_1 -->'} = ($newsletter & 1)==1?'CHECKED':'';
	if ($FLAGS =~ /,CRM,/) {
		require CUSTOMER::NEWSLETTER;
		my @RESULTS = CUSTOMER::NEWSLETTER::fetch_newsletter_detail($USERNAME,$C->prt());
		my $c = '';
		foreach my $i (2..16) {
			next if (not defined $RESULTS[$i]);
			next if ($RESULTS[$i]->{'MODE'} == -1);	## not initialized!

			$c .= "<tr><td><input name=\"newsletter_$i\" ";
			if (($newsletter & (1<<($i-1)))>0) { $c .= " CHECKED "; }
			$c .= " type=\"checkbox\">&nbsp;";
			$c .= $RESULTS[$i]->{'NAME'}."</td></tr>";
			}	
		$GTOOLS::TAG{"<!-- NEWSLETTERS -->"} = $c;
		}
	
	

	$GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} = '';
	foreach my $addr (@{$C->fetch_addresses('BILL')}) {
		if ($GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} ne '') { $GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} .= "<hr>\n"; }
		$GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} .= $addr->as_html();
		$GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} .= 
			sprintf("<a href=\"index.cgi?POPUP=1&VERB=EDITADDR&CID=%d&SHORTCUT=%s&TYPE=%s\"><b>[Edit]</b></a>\n",$C->cid(),$addr->shortcut(),$addr->type());
		$GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} .= 
			sprintf("<a href=\"index.cgi?POPUP=1&VERB=NUKEADDR&CID=%d&SHORTCUT=%s&TYPE=%s\"><b>[Remove]</b></a> \n",$C->cid(),$addr->shortcut(),$addr->type());
		}
	$GTOOLS::TAG{'<!-- BILLING_ADDRESS -->'} .= 
		sprintf("<br><a href=\"index.cgi?POPUP=1&VERB=CREATEADDR&TYPE=BILL&CID=%d&SHORTCUT=*NEW*\"><b>[Add New]</b></a><br>\n",$C->cid());


	$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} = '';
	foreach my $addr (@{$C->fetch_addresses('SHIP')}) {
		if ($GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} ne '') { $GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} .= "<hr>\n"; }
		$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} .= $addr->as_html();
		$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} .= 
			sprintf("<a href=\"index.cgi?POPUP=1&VERB=EDITADDR&CID=%d&SHORTCUT=%s&TYPE=%s\"><b>[Edit]</b></a>\n",$C->cid(),$addr->shortcut(),$addr->type());
		$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} .= 
			sprintf("<a href=\"index.cgi?POPUP=1&VERB=NUKEADDR&CID=%d&SHORTCUT=%s&TYPE=%s\"><b>[Remove]</b></a> \n",$C->cid(),$addr->shortcut(),$addr->type());
		}
	$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} .= 
		sprintf("<br><a href=\"index.cgi?POPUP=1&VERB=CREATEADDR&TYPE=SHIP&CID=%d&SHORTCUT=*NEW*\"><b>[Add New]</b></a><br>\n",$C->cid());

#&CUSTOMER::OUTPUT::addr_list($C,'BILL',0);
#	$GTOOLS::TAG{'<!-- SHIPPING_ADDRESS -->'} = &CUSTOMER::OUTPUT::addr_list($C,'SHIP',0);

	if (1) {
		my $c = '';
		foreach my $payref (@{$C->wallet_list()}) {
			my ($DEFAULT,$DEFAULTBUTTON);
			if ($payref->{'IS_DEFAULT'}) {
				$DEFAULT = '(DEFAULT)';
				$DEFAULTBUTTON = '';
				}
			else {
				$DEFAULT = '';
				$DEFAULTBUTTON = qq~<input type="button" class="minibutton" onClick="document.location='index.cgi?VERB=WALLET-DEFAULT&CID=$CID&SECUREID=$payref->{'ID'}';" value="Default">~;
				}

			$c .= qq~<tr>
			<td>
			~;
			$c .= qq~<input type="button" class="minibutton" onClick="document.location='index.cgi?VERB=WALLET-REMOVE&CID=$CID&SECUREID=$payref->{'ID'}';" value="Remove">~;
			if ($LU->is_admin()) {
				$c .= qq~<input type="button" class="minibutton" onClick="document.location='index.cgi?VERB=WALLET-VIEW&CID=$CID&SECUREID=$payref->{'ID'}';" value="View">~;
				}
			$c .= qq~
			$DEFAULTBUTTON
			</td>
			<td>$payref->{'DESCRIPTION'} $DEFAULT</td>
			<td>$payref->{'CREATED'}</td>
			<td>$payref->{'EXPIRES'}</td>
			</tr>~;
			}
		
		if ($c eq '') { 
			$c = "<tr><td colspan=3><i>No Payment Methods on File</i></td></tr>"; 
			}
		else {
			$c = "<tr class=\"zoovysub1header\">
					<td></td>
					<td>Description</td>
					<td>Created</td>
					<td>Store Until</td>
					</tr>\n$c";
			}
		$c .= "<tr><td colspan=3><a href=\"index.cgi?VERB=WALLET-ADD&CID=$CID\">[Add New Payment Method]</a></td></tr>";
		$GTOOLS::TAG{'<!-- PAYMENT_METHODS -->'} = $c;
		}


	if ($FLAGS =~ /,WS,/) {
		require WHOLESALE;
		my $out = qq~<tr><td nowrap colspan='2'>Wholesale Schedule: <select name="SCHEDULE"><option value="">None</option>~;
		my $schedule = $C->fetch_attrib('INFO.SCHEDULE');
		my $found = 0;
		foreach my $sid (@{&WHOLESALE::list_schedules($USERNAME)}) {
			my ($S) = &WHOLESALE::load_schedule($USERNAME,$sid);
			if ($S->{'TITLE'} eq '') { $S->{'TITLE'} = "Untitled Schedule"; }
			my $selected = '';
			if ($schedule eq $sid) { 
				$found++;
				$selected = 'selected';
				}
			$out .= "<option $selected value=\"$sid\">$sid - $S->{'TITLE'}</option>\n";
			}
		if ((not $found) && ($schedule ne '')) {
			$out .= "<option selected value=\"$schedule\">$schedule **INVALID**</option>\n";
			}
		$out .= qq~</select></td></tr>~;
		
	#	print STDERR Dumper($C->{'_STATE'},$C->fetch_attrib('WS'));
	#	die();

		print STDERR "SCHEDULE: $schedule\n";
		my $wsaddr = undef;
		if ($schedule ne '') {
			$wsaddr = $C->fetch_address('WS');
			}

		if (defined $wsaddr) {
			# print STDERR 'WSINFO: '.Dumper($wsaddr);
			my $chk_allow_po = ($wsaddr->{'ALLOW_PO'}>0)?'checked':'';
			my $chk_resale	= ($wsaddr->{'RESALE'}>0)?'checked':'';
			$out .= qq~
			<tr><td nowrap colspan=3>
			<table width=100%>
				<tr>
					<td nowrap><input type="checkbox" $chk_allow_po name="ALLOW_PO"> Enable/Accept Purchase Orders</td>
					<td>&nbsp;</td>
					<td nowrap><input type="checkbox" $chk_resale name="RESALE"> Do not charge sales tax</td>
				</tr>
				<tr>
					<td>Credit Limit: \$<input size=10 type="textbox" value="$wsaddr->{'CREDIT_LIMIT'}" name="CREDIT_LIMIT"></td>
					<td></td>
					<td>Credit Balance: \$<input size=10 type="textbox" value="$wsaddr->{'CREDIT_BALANCE'}" name="CREDIT_BALANCE"><br></td>
				</tr>
				<tr>
					<td>Resale #: <input size=15 type="textbox" value="$wsaddr->{'RESALE_PERMIT'}" name="RESALE_PERMIT"></td>
					<td></td>
					<td>Account Manager: <input size=10 type="textbox" value="$wsaddr->{'ACCOUNT_MANAGER'}" name="ACCOUNT_MANAGER"><br></td>
				</tr>
			</table>
			</td></tr>
				~;

			$GTOOLS::TAG{'<!-- DROPSHIP -->'} = qq~
			<tr>
				<td colspan='1' class="table_top" style="height: 22px;"><span class="white">DropShip Address+Info</span></td>
				<td colspan='1' class="table_top" style="height: 22px;"><span class="white">DropShip Company Logo</span></td>
			</tr>
			<tr>
				<td bgcolor="#ffffff">
					~.
		$wsaddr->as_html().
		sprintf("<a href=\"index.cgi?POPUP=1&VERB=EDITADDR&CID=%d&TYPE=WS\"><b>[Edit]</b></a>\n",$C->cid()).
				qq~
				</td>
				<td bgcolor="#ffffff">
					<img name="logoImg" src="~.(($wsaddr->{'LOGO'})?&GTOOLS::imageurl($USERNAME,$wsaddr->{'LOGO'},70,200,'FFFFFF',0):'/images/blank.gif').qq~" width=200 height=70>
					<br><a href='#' onClick="openWindow('/biz/setup/media/popup.cgi?mode=customerlogo&CID=$C->{'_CID'}');"><b>[Edit]</b></a></td>
			</tr>	
			~;
			}
		$GTOOLS::TAG{'<!-- WHOLESALE -->'} = $out;
		}

	if ($FLAGS =~ /,CRM,/) {
		my $points = int($C->get('INFO.REWARD_BALANCE'));

		my $out .= qq~
		<table cellspacing="1" cellpadding="2" border="0" width="100%">
			<tr class="zoovysub2header" style="height: 22px;">
				<td width=100%>
				Rewards/Loyalty Program
				</td>
			</tr>
			<tr>
				<td>
				Current Point Balance: $points
				</td>
			</tr>
		</table>
		~;
		$GTOOLS::TAG{'<!-- REWARDS -->'} = $out;
		}


	if ($FLAGS =~ /,CRM,/) {
		my $out = '';


		$out .= qq~
		<table cellspacing="1" cellpadding="2" border="0" width="100%">
			<tr class="zoovysub2header" style="height: 22px;">
				<td width="100%">
				<a href="/biz/utilities/giftcard/index.cgi?VERB=CREATE&CID=$CID"><b>[+]</b></a> 
				Gift Cards
				</td>
			</tr>
			<tr>
				<td>
			~;

		my $giftcardsref = &GIFTCARD::list($USERNAME,CID=>$CID);
		if (scalar(@{$giftcardsref})==0) {
			$out .= "<i>No Giftcards</i>";
			}
		else {
			$out .= qq~<tr>
				<td bgcolor="#ffffff" valign="top">
				<table width=100%>
				~;

			foreach my $gcref (@{$giftcardsref}) {
				$out .= "<tr>";
				$out .= "<td><a href=\"/biz/utilities/giftcard/index.cgi?VERB=EDIT&GCID=$gcref->{'ID'}\"><img border=0 src=\"/biz/images/arrows/v_edit-15x20.gif\"></a></td>";
				$out .= "<td>".&GIFTCARD::obfuscateCode($gcref->{'CODE'})."</td>";
				$out .= "<td>$gcref->{'NOTE'}</td>";
				$out .= "<td>".sprintf("%.2f",$gcref->{'BALANCE'})."</td></tr>";
				}
			$out .= qq~</table>~;
			}
		
		$out .= qq~
				</td>
			</tr>
		</table>
		~;

		
      my $tickets = &CUSTOMER::TICKET::getTickets($USERNAME,CID=>$C->cid());

		$out .= qq~
		<table cellspacing="1" cellpadding="2" border="0" width="100%">
			<tr class="zoovysub2header" style="height: 22px;">
				<td width="100%"><a href="/biz/crm/index.cgi?VERB=CREATE&CID=$CID"><b>[+]</b></a> Customer Tickets/RMAs</td>
			</tr><tr>
				<td bgcolor="#ffffff" valign="top">~;

		if (@{$tickets}==0) {
			$out .= "<i>No Tickets</i><br>";
			}
		else {
			$out .= qq~
<table width=100% border=0 cellspacing=1 cellpadding=1 class="ztable_head">
   <tr class="ztable_head">
      <td>TICKET</td><td>SUBJECT</td><td>ORDER #</td><td>UPDATED</td>
   </tr>
~;
      my $i = 0;
      foreach my $t (@{$tickets}) {
         $i = ($i==0)?1:0;
         $out .= "<tr class=\"ztable_row$i\"><td><a href=\"/biz/crm/index.cgi?verb=view&code=$t->{'RMACODE'}\">$t->{'RMACODE'}</a></td><td>$t->{'SUBJECT'}</td><td>$t->{'ORDERID'}</td><td>".&ZTOOLKIT::pretty_date($t->{'UPDATED_GMT'})."</td></tr>";
         }
      $out .= qq~</table>~;
		}

		$out .= qq~

				
				</td>
			</tr>
		</table>
		~;


		

		
		$out .= qq~

		<div class="zoovysub2header" width="100%">Customer Notes</div>
		<table>
		~;

		my $c = '';
		print STDERR "HAS_NOTES: ".$C->fetch_attrib('INFO.HAS_NOTES')."\n";
		if ($C->fetch_attrib('INFO.HAS_NOTES')>0) {
			my $EMAIL = $C->email();
			foreach my $noteref (sort @{$C->fetch_notes()}) {
				my $remove = '';
				if (1) {
					$remove = "<td><a href=\"?VERB=NUKENOTE&NID=$noteref->{'ID'}&CID=$CID&EMAIL=$EMAIL\">[Remove]</a></td>";
					}

				my $pretty_date = ZTOOLKIT::pretty_date($noteref->{'CREATED_GMT'});
				$c .= qq~
				<tr>
					$remove
					<td>$pretty_date</td>
					<td>$noteref->{'LUSER'}</td>
					<td>$noteref->{'NOTE'}</td>
				</tr>
				~;
				}
			}
		if ($c eq '') { $c .= "<tr><td><i>None</i><br></td></tr>"; }

		my $eventref = $C->fetch_events();
		if (scalar(@{$eventref})>0) {
			foreach my $e (sort @{$eventref}) {
				next if ($e->{'*PRETTY'} eq '');
				$c .= qq~
				<tr>
					<td></td><td>*user</td><td>~.$e->{'*PRETTY'}.qq~</td>
				</tr>
				~;
				}
			}

		$out .= qq~
				$c
			<tr>
				<td colspan=3>
				<table>
					<td nowrap>New Note:</td>
					<td nowrap><input type="textbox" maxlength="80" size="60" name="NEW_NOTE"></td>
					<td nowrap><input type="submit" value=" Add "></td>
				</table>
				</td>
			</tr>
		</table>
		~;
		$GTOOLS::TAG{'<!-- CRM -->'} = $out;
		}

#	if ($POPUP==0) {
#		$GTOOLS::TAG{'<!-- DELETE_BUTTON -->'} = qq~<td><a href='index.cgi?POPUP=$POPUP&ACTION=DELETE&CID=$C->{'_CID'}&EMAIL=$C->{'_EMAIL'}'><img border="0" src="/images/bizbuttons/delete.gif"></a></td>~;
#		}

	##
	## BUILD AN ORDER LIST
	##
	my $out = '';
	my @orders = &CUSTOMER::BATCH::customer_orders($C->{'_USERNAME'},$C->cid());
	# use Data::Dumper; print STDERR Dumper(\@orders);
	my $count = 0;
	my $sum = 0;
	foreach my $order (@orders) {
		next if ($order eq '');
		my ($O2) = CART2->new_from_oid($C->{'_USERNAME'},$order,new=>0);
		next if (not defined $O2);

		$out .= "<tr bgcolor='".(($count%2==0)?'EEEEEE':'FFFFFF')."'>";
		$out .= "<td class='order'><a target='_blank' href='https://www.zoovy.com/biz/orders/view.cgi?ID=".$O2->oid()."'>".$O2->oid()."</a></td>";
		$out .= "<td class='order'>".($O2->pool())."</td>";
		$out .= "<td class='order'>".($O2->in_get('sum/order_total'))."</td>";
		$out .= "<td class='order'>".($O2->payment_method())."</td>";
		$out .= "</tr>";
			
		$sum += $O2->in_get('sum/order_total');
		$count++;
		}
		
	if ($out ne '') {
		$sum = sprintf("%.2f",$sum);
		$out .= qq~<tr class="warning"><td colspan="2"><strong>Total</strong></td><Td colspan="2">\$$sum</Td></tr>~;
		}	
	else {
		$out = qq~<tr class='warning'><td colspan='4'><i>Sorry, there have been no orders placed by this customer.</td></tr>~;
		}	
	$GTOOLS::TAG{'<!-- ORDER_TABLE -->'} = $out;
	$GTOOLS::TAG{'<!-- PRT -->'} = $C->prt();

#	use Data::Dumper;
#	print STDERR Dumper($C);

	push @BC, {'name'=>'Edit: '.$C->email(),link=>'/biz/utilities/customer/index.cgi?VERB=EDIT&CID='.$C->{'_CID'}, };	


	$template_file = 'edit.shtml';
	}





push @TABS, { 'name'=>'Search', link=>'index.cgi?VERB=SEARCH', selected=>($VERB eq 'SEARCH')?1:0 };
push @TABS, { 'name'=>'Reports', link=>'index.cgi?VERB=REPORTS', selected=>($VERB eq 'REPORTS')?1:0 };
push @TABS, { 'name'=>'Create', link=>'index.cgi?VERB=CREATE', selected=>($VERB eq 'CREATE')?1:0 };


&GTOOLS::output(file=>$template_file,header=>1,msgs=>\@MSGS,tabs=>\@TABS,bc=>\@BC,js=>1);
&DBINFO::db_user_close();