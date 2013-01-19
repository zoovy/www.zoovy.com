#!/usr/bin/perl

##
## /biz/manage/newsletters/index.cgi
##
## allows user to CREATE/EDIT/DISABLE/DELETE newsletters (sub lists)
## and newsletter campaigns
## 
##  
##

use strict;

use Data::Dumper;
use JSON::Syck;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require ZTOOLKIT;
require CUSTOMER::NEWSLETTER;
require DOMAIN::TOOLS;
require SITE::MSGS;
require TOXML::UTIL;
require CUSTOMER;
require SITE;
use POSIX;
require TOXML;
require LUSER;
require ZSHIP::RULES;

my @MSGS = ();
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my $udbh = &DBINFO::db_user_connect($USERNAME);

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};
if (not defined $VERB) { $VERB = $ZOOVY::cgiv->{'ACTION'}; }
my $ID = int($ZOOVY::cgiv->{'ID'});

my @BC = ();
push @BC, { name=>'Utilities', link=>'/biz/manage', target=>'_top' };
push @BC, { name=>'Newsletter Management', link=>'/biz/manage/newsletters', target=>'_top' };
push @BC, { name=>"Partition: $PRT" };

## Delete CAMPAIGN from DB
##
if($VERB eq "CAMPAIGN-NUKE"){
	my $pstmt = "delete from CAMPAIGNS ".
					"where MID=$MID ".
					"and ID=".int($ID);
	$udbh->do($pstmt);
	
	push @MSGS, "SUCCESS|Deleted Campaign $ID";
	$LU->log('UTILITIES.NEWSLETTER',"Deleted Campaign $ID","SAVE");
	$VERB = '';
	}


## copy CAMPAIGN
##
if($VERB eq "CAMPAIGN-COPY"){
	my $PREVIOUS_ID = int($ID);
	my $pstmt = "select * from CAMPAIGNS where ID=$PREVIOUS_ID and MID=$MID /* $USERNAME */";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my ($CREF) = $sth->fetchrow_hashref();
	$sth->finish;


	$CREF->{'ID'} = 0;
	$CREF->{'STATUS'} = 'PENDING';

	$CREF->{'STAT_QUEUED'} = 0;
	$CREF->{'STAT_SENT'} = 0;
	$CREF->{'STAT_VIEWED'} = 0;
	$CREF->{'STAT_OPENED'} = 0;
	$CREF->{'STAT_BOUNCED'} = 0;
	$CREF->{'STAT_CLICKED'} = 0;
	$CREF->{'STAT_PURCHASED'} = 0;
	$CREF->{'STAT_TOTAL_SALES'} = 0;
	$CREF->{'STAT_UNSUBSCRIBED'} = 0;
	$pstmt = &DBINFO::insert($udbh,'CAMPAIGNS',$CREF,debug=>2);
	$udbh->do($pstmt);

  	$sth = $udbh->prepare("SELECT last_insert_id()");
	$sth->execute();
	($ID) = $sth->fetchrow();
	$sth->finish();

	if ($ID>0) {
		push @MSGS, "SUCCESS|Created campaign $ID from campaign $PREVIOUS_ID";
		}	

	$VERB = 'CAMPAIGN-EDIT';
	}	



if (($VERB eq 'CAMPAIGN-SAVE') || ($VERB eq 'CAMPAIGN-GENERATE')) {
	my $NAME = $ZOOVY::cgiv->{'NAME'};
	$NAME =~ s/\"//g;

	my $SUBJECT = $ZOOVY::cgiv->{'SUBJECT'};
	$SUBJECT =~ s/\"//g; $SUBJECT =~ s/\n$//;

	my $SENDER = $ZOOVY::cgiv->{'SENDER'};
	my $RECIPIENT = $ZOOVY::cgiv->{'RECIPIENT'};
	my $SCHEDULE = $ZOOVY::cgiv->{'SCHEDULE'};
	my $COUPON = $ZOOVY::cgiv->{'COUPON'};
	my $LAYOUT = $ZOOVY::cgiv->{'LAYOUT'};

   # input validation
   # if SENDER, SUBJECT, RECIPIENT must exist or bounce back to EDIT page
   if ((not defined($SENDER)) || ($SENDER eq '') ||
      (not defined($SUBJECT)) || ($SUBJECT eq '') ||
      (not defined($RECIPIENT)) || ($RECIPIENT eq '')) {

		$VERB = 'CAMPAIGN-EDIT';
		push @MSGS, "ERROR|Source Email, Subject and Recipients are required. Please fill out information completely before choosing your page layout.";
		}
	else {
		## we'll get which profile to use from the PRT
		# ($PROFILE) = &ZOOVY::prt_to_profile($USERNAME,$PRT);	## fuck, bad.
		# push @MSGS, "ERROR|$USERNAME,$SENDER";
		my ($PROFILE) = &DOMAIN::TOOLS::profileprt_for_domain($USERNAME,$SENDER);

		my $pstmt = &DBINFO::insert($udbh,'CAMPAIGNS',{
			'ID'=>int($ID), 'PRT'=>int($PRT),
			MID=>$MID, USERNAME=>$USERNAME,
			CPG_TYPE=>'NEWSLETTER',
			NAME=>$NAME,
			SENDER=>$ZOOVY::cgiv->{'SENDER'},
			SUBJECT=>$ZOOVY::cgiv->{'SUBJECT'},
			RECIPIENT=>$RECIPIENT,
			STATUS=>'PENDING',
			PROFILE=>$PROFILE,
			LAYOUT=>$LAYOUT,
			COUPON=>$COUPON,
			CREATED_GMT=>time(),
			PRT=>$PRT
			},key=>['ID','MID','PRT'],debug=>2);

		print STDERR $pstmt."\n";
		$udbh->do($pstmt);
		if ($ID<=0) {
		  	my $sth = $udbh->prepare("SELECT last_insert_id()");
			$sth->execute();
			($ID) = $sth->fetchrow();
			$sth->finish();
			}

		push @MSGS, "SUCCESS|Updated Campaign $ID (layout: $LAYOUT)";
		$LU->log('UTILITIES.NEWSLETTER',"Changed Newsletter $ID","SAVE");
		$GTOOLS::TAG{'<!-- ID -->'} = $ID;

		if ($VERB eq 'CAMPAIGN-GENERATE') {
			$VERB = 'CAMPAIGN-GENERATE';
			}
		else {
			$VERB = 'CAMPAIGN-EDIT';
			}
		}

	}

if (($VERB eq 'CAMPAIGN-NEW') || ($VERB eq 'CAMPAIGN-EDIT')) {
	if ($VERB eq 'CAMPAIGN-NEW') { $ID = 0; }


   ## get campaign data from DB
	my $CREF = {};

	if ($ID>0) {
		my $PROFILE = '';
		$CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME, $ID); 
		
		

	   $GTOOLS::TAG{'<!-- ID -->'} = $ID;
		$GTOOLS::TAG{'<!-- EDITOR -->'} = qq~
<button class="button" 
	onClick="
jQuery('#setupContent').empty(); 
navigateTo('/biz/setup/builder/index.cgi?ACTION=INITEDIT&PG=\@CAMPAIGN:$ID&NS=$CREF->{'PROFILE'}&FORMAT=NEWSLETTER&FS=I&FL=$CREF->{'LAYOUT'}');
return false;
">
	Edit</button>
~;
		}

   push @BC, { name=> 'Campaign' };


   ## NAME
   $GTOOLS::TAG{'<!-- NAME -->'} = ($CREF->{'NAME'}?$CREF->{'NAME'}:$ZOOVY::cgiv->{'NAME'});

   ## SENDER
	my $c = '';
	my (@DOMAINS) = &DOMAIN::TOOLS::newsletter_domains($USERNAME,$PRT);
	if ($FLAGS =~ /,PKG=STAFF,/) { push @DOMAINS, "zoovymail.com"; }

	foreach my $domain (@DOMAINS) {
		my ($selected) = (($CREF->{'SENDER'} eq $domain)?'selected':'');
		 $c .= "<option $selected value=\"$domain\">newsletter.$domain</option>\n";
		}
	$GTOOLS::TAG{'<!-- SENDER -->'} = $c;

   ## SUBJECT
   $GTOOLS::TAG{'<!-- SUBJECT -->'} = ($CREF->{'SUBJECT'}?$CREF->{'SUBJECT'}:$ZOOVY::cgiv->{'SUBJECT'});


	$GTOOLS::TAG{'<!-- LAYOUT -->'} = '';


   ## RECIPIENTS
   ## get One Time Mailings (NEWSLETTERS)
   my @RESULTS = &CUSTOMER::NEWSLETTER::fetch_newsletter_detail($USERNAME,$PRT);
	unshift @RESULTS, { ID=>"All", MODE=>1, NAME=>"All Newsletter Subscribers" };
	# push @RESULTS, { ID=>"POST_SHIP_10", MODE=>10, NAME=>"Post 10 Day Shipping Notice" };

   ## set value for All Newsletter choice
	$c = '';
   foreach my $list (@RESULTS) {
      next unless ($list->{'MODE'}>=0);
		next if ($list->{'ID'} eq '');	# this ignores empty arrays

		my $selected = (
			($CREF->{'RECIPIENT'} eq "OT_".$list->{'ID'}) || ($ZOOVY::cgiv->{'RECIPIENT'} eq "OT_".$list->{'ID'})
			)?'selected':'';
		my $name = $list->{'NAME'};
		if ($name eq '') { $name = "<i>Name Not Initialized</i>"; }
		
		$c .= "<option $selected value=\"OT_$list->{'ID'}\"> $name<br>";
      }
	$GTOOLS::TAG{'<!-- RECIPIENTS -->'} = $c;


   ## get Reoccuring Mailings
   ##    should be switched to hash/array when list gets bigger
   #my $ro = '<input type="radio" name="RECIPIENT" '.
   #         (($CREF->{'RECIPIENT'} eq "RO_7d" ||
	#		  	  $ZOOVY::cgiv->{'RECIPIENT'} eq "RO_7d")?'checked=1':'').
   #         ' value="RO_7d"> New Customers - 7 days after purchase.<br>
   #         <input type="radio" name="RECIPIENT" '.
   #         (($CREF->{'RECIPIENT'} eq "RO_14d" ||
	#			  $ZOOVY::cgiv->{'RECIPIENT'} eq "RO_14d")?'checked=1':'').
   #         ' value="RO_14d"> New Customers - 14 days after purchase.<br>
   #         <input type="radio" name="RECIPIENT" '.
   #         (($CREF->{'RECIPIENT'} eq "RO_30d" ||
	#			  $ZOOVY::cgiv->{'RECIPIENT'} eq "RO_30d")?'checked=1':'').
   #         ' value="RO_30d"> New Customers - 30 days after purchase.<br>';
   # $GTOOLS::TAG{'<!-- RECIPIENTS_REOCCURING -->'} = $ro;

	## COUPONS
	my $out = "<option value=''>None</option>\n";
	require CART::COUPON;
	my $results = CART::COUPON::list($USERNAME,$PRT);
	foreach my $ref (@{$results}) {
		next if ($ref->{'disabled'}>0);
		next if ($ref->{'expires_gmt'}<$^T);

		my $selected = ($CREF->{'COUPON'} eq $ref->{'code'})?'selected':'';
		$out .= "<option $selected value='$ref->{'code'}'>$ref->{'code'}: $ref->{'title'}</option>";
      }
	$GTOOLS::TAG{'<!-- COUPONS -->'} = $out;

	my $selected = $ZOOVY::cgiv->{'LAYOUT'};
	my $arref = &TOXML::UTIL::listDocs($USERNAME,'LAYOUT',DETAIL=>1,SUBTYPE=>'I',SORT=>1,LU=>$LU,SELECTED=>$selected);
	#open F, ">/tmp/foo"; print F Dumper($arref); close F;
	# use Data::Dumper; print STDERR Dumper($FORMAT,$arref); die();

	$c = '';
	foreach my $layout (@{$arref}) {
		my ($selected) = ($layout->{"DOCID"} eq $CREF->{'LAYOUT'})?'selected':'';
		$c .= "<option $selected value='$layout->{'DOCID'}'>$layout->{'DOCID'}</option>\n";
		}
	$GTOOLS::TAG{'<!-- LAYOUTS -->'} = $c;

	# my $bgcolor = '';
	# my @rows = ();
	# $GTOOLS::JSON{'layouts'} = $arref;  ## LAYOUTS


	$template_file = 'campaign.shtml';
	}



##
## called from preview.shtml
if (($VERB eq 'DISPLAY_TXT') || ($VERB eq 'DISPLAY_HTML')) {

	my ($result,$warnings) = ();
#
#	## SUBJECT needs to be pulled from CAMPAIGN
#	## need alternative undef SUBJECT
#	my $out = '';
#	my $EMAIL = $ZOOVY::cgiv->{'EMAIL'};

	my $CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME,$ID);
	$GTOOLS::TAG{'<!-- HTML -->'} = $CREF->{'OUTPUT_HTML'};
	$template_file = 'display.shtml';	
	}

#
##	if ($VERB ne 'SEND_TEST_EMAIL') {
##		$out = &CUSTOMER::NEWSLETTER::format_newsletter($CREF,$out,'FOOTER_WILL_APPEAR_HERE',0,time());
##		}
#
#	if ($out eq '') {
#		$out = 'No Content';
#		}
#

#	## allow previews from admin.zoovy.com (a little less than secure)
#	if (not defined $FL) {  
#		require PAGE;
#		$USERNAME = $ZOOVY::cgiv->{'MERCHANT'}?$ZOOVY::cgiv->{'MERCHANT'}:$USERNAME;
#		$SITE::PAGE = PAGE->new($USERNAME,$PG,NS=>'');
#		$FL = $SITE::PAGE->get('FL');
#		}
#
#	my ($t) = TOXML->new('LAYOUT',$FL,USERNAME=>$USERNAME,FS=>'I');
#	my $out = 'No content';
#	if (defined $t) {
#		$SITE::PAGE = PAGE->new($USERNAME,$PG,NS=>'');
#		($out) = $t->render(USERNAME=>$USERNAME,PROFILE=>'',PG=>$PG);
#		}
#	

if ($VERB eq 'SEND_TEST_EMAIL') {

	my $CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME, $ID); 

	my $EMAIL = $ZOOVY::cgiv->{'EMAIL'};

	my $nsref = &ZOOVY::fetchmerchantns_ref($CREF->{'USERNAME'},&ZOOVY::prt_to_profile($CREF->{'USERNAME'},$CREF->{'PRT'}));

	my ($body) = &CUSTOMER::NEWSLETTER::rewrite_links($CREF->{'OUTPUT_HTML'},"meta=NEWSLETTER&cpg=$ID&cpn=0");
	my ($footer) = &CUSTOMER::NEWSLETTER::build_footer($CREF,$nsref);

	my $GUID = $CREF->{'PREVIEW_GUID'};

	$CREF->{'_BODY'} = $body.$footer.qq~
	Please carefully examine this email (both the html and text versions). 
	If you are fully satisfied with its layout and contents, press the APPROVE button. 
	This will take to your final Step, which will which allow you to set the 'Send Date' for this mailing Campaign.
	<br><br>
	<a href=\"http://www.zoovy.com/biz/manage/newsletters/approve.cgi?VERB=CAMPAIGN-APPROVE&USERNAME=$USERNAME&ID=$ID&GUID=$GUID\">APPROVE</a><br><hr><br><br><br>\n\n
	~;

	my ($result,$warnings) = &CUSTOMER::NEWSLETTER::send_newsletter($CREF,$EMAIL,0,0,'Test Customer');

	## test newsletter.. we should make sure this body doesn't have a line length issue.
	my $longest = 0;
	my $longcount = 0;
	foreach my $line (split(/[\n\r]+/,$CREF->{'OUTPUT_HTML'})) {
		if (length($line)>77) { 
			if (length($line)>$longest) { $longest = length($line); }
			$longcount++; 
			# push @{$warnings}, "<li> ".length($line)."=[".&ZOOVY::incode($line)."]";
			}
		}
	if (($longcount>0) && ($longest>300)) {
		if ($result>0) { $result = 0; }
		push @{$warnings}, "<div>ERROR: Message not formatted to RFC822 specifications.<div class='hint'>The body of your message has $longcount lines which exceed the RFC822 maximum of 77 characters. Your longest line is $longest bytes in length. Due to incompatibiles between HTML and Email lines which exceed the specification are known to cause transmission errors in rare circumstances. In some cases if image names, or links which exceed 77 characters are in use this issue may not be correctable. View the source of the HTML/Text iframes below to try and identify the issue.</div></div>\n";
		}

	## deal with errors/warnings
	if($result == -1){
		push @MSGS, "ERROR|Test email was not sent due to one or more serious errors.";
		}
	elsif($result == 0){
		push @MSGS, "WARNING|Test email was sent - but experienced one or more warnings.";
		}
	else{
		push @MSGS, "SUCCESS|Your Test email was successfully sent! Please throughly check the Newsletter test email. When you are completely satisfied with its contents/format, please click on the link to 'Step 5: Approve and Send Campaign' from the email. ";
		$LU->log('UTILITIES.NEWSLETTER',"Test email sent","INFO");
		}
	foreach my $msg (@{$warnings}){
		push @MSGS, "WARN|$msg";
		$LU->log('UTILITIES.NEWSLETTER',"$msg","WARN");
		}

	$VERB = 'CAMPAIGN-PREVIEW';
	# don't display header below
   }


#########################################################################
##
##
##
if (($VERB eq 'CAMPAIGN-GENERATE') || ($VERB eq "CAMPAIGN-PREVIEW")) {
	$template_file = 'preview.shtml';

	my $CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME,$ID);
	push @MSGS, "SUCCESS|Sending domain is: $CREF->{'SENDER'}";

	if ($VERB eq 'CAMPAIGN-GENERATE') {
		($CREF) = &CUSTOMER::NEWSLETTER::generate($USERNAME,$CREF);
		push @MSGS, "SUCCESS|Campaign $CREF->{'ID'} was regenerated"; 
		}

	my $warnings = 0;
	my $validlinks = 0;
	foreach my $chunk (split(/\<.*?\>/,$CREF->{'OUTPUT_HTML'})) {
		if ($chunk =~ /%TRACKING%/) { $validlinks++; }
		next if ($chunk !~ /^<a/);
		if ($chunk !~ /%TRACKING%/) { $warnings++; push @MSGS, "WARN|Click Tracking for Link ".&ZOOVY::incode($chunk)." does not have %TRACKING%\n"; }
		}
	if ($warnings) {
		push @MSGS, "WARN|%TRACKING% must be embeded in links for click and sales tracking to function";
		}
	if (not $validlinks) {
		push @MSGS, "WARN|Did not detect any trackable HTML Links (please verify this is correct)";
		}


	# push @MSGS, "SUCCESS|".Dumper($CREF);

#	$CREF->{'OUTPUT_HTML'} = &CUSTOMER::NEWSLETTER::rewrite_links($CREF->{'OUTPUT_HTML'},"meta=NEWSLETTER&CPN=0&CPG=0");
#	$CREF->{'OUTPUT_TXT'} = &SITE::EMAILS::htmlStrip($CREF->{'OUTPUT_HTML'});

	$GTOOLS::TAG{'<!-- HTMLCONTENT -->'} = JSON::Syck::Dump($CREF->{'OUTPUT_HTML'});
	$GTOOLS::TAG{'<!-- TXTCONTENT -->'} = JSON::Syck::Dump($CREF->{'OUTPUT_TXT'});
#	$GTOOLS::JSON{'htmlcontent'} = $CREF->{'OUTPUT_HTML'};
#	if ($GTOOLS::JSON{'htmlcontent'} eq '') { $GTOOLS::JSON{'htmlcontent'} = 'ERROR - NO HTML PREVIEW'; }
#	$GTOOLS::JSON{'txtcontent'} = $CREF->{'OUTPUT_TXT'};
#	if ($GTOOLS::JSON{'txtcontent'} eq '') { $GTOOLS::JSON{'txtcontent'} = 'ERROR - NO TEXT PREVIEW'; }

	$GTOOLS::TAG{'<!-- ID -->'} = $ID;

	my ($EMAIL) = $ZOOVY::cgiv->{'EMAIL'};
	if ($EMAIL eq '') { $EMAIL = $LU->email(); }

	$GTOOLS::TAG{'<!-- EMAIL -->'} = $EMAIL;


	#if ($LU->is_zoovy() || ($USERNAME eq 'brian')) {
	#	$GTOOLS::TAG{'<!-- SUPPORT_APPROVE -->'} = qq~
#<form action="/biz/manage/newsletters/index.cgi">
#	<input type="hidden" name="ID" value="$CREF->{'ID'}">
#	<input type="hidden" name="VERB" value="CAMPAIGN-APPROVE">
#	<input type="hidden" name="GUID" value="$CREF->{'PREVIEW_GUID'}">
#	<input class="button" type="submit" value=" PROCEED AFTER REVIEWING IN EMAIL ">
#<form>
#~;
	#	}
	}


###########################################################################
##
##
##
if ($VERB eq "CAMPAIGN-START"){

	# format SEND_DATE to GMT format
   my $SEND_DATE = int($ZOOVY::cgiv->{'SEND_DATE'});
	if (int($ZOOVY::cgiv->{'SEND_TIME'})>0) {
		$SEND_DATE += (int($ZOOVY::cgiv->{'SEND_TIME'}))*3600;
		}
	if ($SEND_DATE<time()) { $SEND_DATE = time(); }

	$VERB = '';
	my $CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME,$ID);
	if (not defined $CREF) {
		push @MSGS, "WARN|Campaign $ID was not found";
		}
	else {
   	## The GMT bit is important here or else it'll assume PST/PDT

 		## only update PENDING CAMPAIGNS
		my ($udbh) = &DBINFO::db_user_connect($USERNAME);
   	my $pstmt = "update CAMPAIGNS set STARTS_GMT=$SEND_DATE,STATUS='APPROVED' where MID=$MID and ID=$ID and status='PENDING'";
   	print STDERR $pstmt."\n";
   	my $rows = $udbh->do($pstmt);
		$LU->log('UTILITIES.NEWSLETTER',"Approved Campaign $ID","SAVE");
		&DBINFO::db_user_close();

   	if ($rows == 1) {
			push @MSGS, "SUCCESS|Congratulations!! You have successfully approved and scheduled the mailing of your Newsletter Campaign.";
			}
		elsif ($CREF->{'STATUS'} eq 'APPROVED') {
			push @MSGS, "WARN|Your Campaign has already been APPROVED.";
			}
		else {
			push @MSGS, "ISE|Internal error campaign status:$CREF->{'STATUS'}";
			$VERB = 'CAMPAIGN-APPROVE';
			}
   	}
	}
	




## page for setting APPROVAL and SEND_DATE 
## for CAMPAIGNS
##
if ($VERB eq "CAMPAIGN-APPROVE") {
	push @BC, { name=>'Campaign Setup' };
	$template_file = 'approve.shtml';

	# get values for SEND_DATE
   # next 7 days
   my @days = ();
	my $CREF = &CUSTOMER::NEWSLETTER::fetch_campaign($USERNAME,$ID);

   $GTOOLS::TAG{'<!-- NAME -->'} = $CREF->{'NAME'};

	print STDERR "TS: $ZOOVY::cgiv->{'TS'} TIMESTAMP: $CREF->{'TESTED'} USERNAME: $USERNAME ID: $ID\n";

	## check if newsletter has already been approved
	if (0) {
	#if ($CREF->{'PREVIEW_GUID'} ne $ZOOVY::cgiv->{'GUID'}){
	#	push @MSGS, "ERROR|Sorry you must click the link on the latest version (please retry)";
	#	$VERB = 'CAMPAIGN-PREVIEW';
		}
	## check if merchant is approving latest test mailing
	else {
		## get next 7 days (need to switch to Date::Parse func)
		my $ts = &ZTOOLKIT::mysql_to_unixtime(POSIX::strftime("%Y-%m-%d 00:00:00",localtime(time())));

		my $c = '';
   	for (my $cnt=1;$cnt <= 14;$cnt++){
      	$c .= "<option value=\"$ts\">".&ZTOOLKIT::pretty_date($ts)."</option>";
			$ts = $ts + 86400;
   		}
   	$c = "<select name=\"SEND_DATE\">$c</select>";
   	$GTOOLS::TAG{'<!-- SEND_DATE -->'} = $c;		

   	$GTOOLS::TAG{'<!-- APPROVE_BUTTON -->'} = qq~<button name="BUTTON" type="submit" class="button">Finish</button>~;
   	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
   	}
	}




## Move CAMPAIGN back to PENDING
##
if($VERB eq "CAMPAIGN-STOP"){

	my $udbh = &DBINFO::db_user_connect($USERNAME);

	my $pstmt = "update CAMPAIGNS set STATUS='PENDING' where MID=$MID and STATUS in ('PENDING','APPROVED') and ID=".int($ID);
	my $rv = $udbh->do($pstmt);
	
	if ($rv == 1) {
		$pstmt = "delete from CAMPAIGN_RECIPIENTS where CPG=".int($ID);
		$udbh->do($pstmt);

		$LU->log('UTILITIES.NEWSLETTER',"Stopped Campaign $ID","SAVE");

		push @MSGS, "SUCCESS|Stopped Campaign: $ID";
		}
	else {
		push @MSGS, "WARN|Could not stop campaign: $ID";
		}

	&DBINFO::db_user_close();

	$VERB = '';
	}




##
## Display the  
##
if ($VERB eq 'SUBSCRIBER-LISTS') {
	## get subscription count for all newsletters
	
	my $c = '';
	my $CREF = &CUSTOMER::NEWSLETTER::fetch_newsletter_sub_counts($USERNAME,$PRT);
   my @RESULTS = &CUSTOMER::NEWSLETTER::fetch_newsletter_detail($USERNAME,$PRT);
	my @sorted = ();

	my %modes = ();
	$modes{-1} = 'Not Configured';
	$modes{0} = 'Exclusive';
	$modes{1} = 'Default';
	$modes{2} = 'Targeted';

	my $count = 0;
	my $class = '';
	foreach my $list (@RESULTS) {
		my ($id, $name, $created, $mode) = ($list->{'ID'},$list->{'NAME'},$list->{'CREATED_GMT'},$modes{$list->{'MODE'}});
		next if ($id == 0);
		next if ($id >= 1000);	## this is an automated list.
		
		$class = ($class eq 'r0')?'r1':'r0';
		if ($name eq '') { $name = "<i>Not Initialized</i>"; }

		$c .= "<tr class=\"$class\">".
				"<td>$id</td>".
				"<td>". 
				"<a href=\"/biz/manage/newsletters/index.cgi?VERB=EDIT_SUBLIST&ID=$id\">[ Edit ]</a> ".
				"</td>".
				"<td>$name</td>\n".
				"<td>".&ZTOOLKIT::pretty_date($created, -1)."</td>\n".
				"<td>$mode</td>\n".
				"<td width=50>".(( defined $CREF->{$id} )?$CREF->{$id}:0)."</td>".
				"<td>".
				"<a href=\"/biz/manage/newsletters/index.cgi?VERB=EDIT_SUBLIST_RECIPIENTS&ID=$id\">[ View Subscribers ]</a> ".
				"<a href=\"/biz/manage/newsletters/index.cgi?VERB=EDIT_SUBLIST_BULK&ID=$id\">[ Bulk Add/Remove ]</a> ".
				"</td>\n".
				"\n</tr>\n";
		$count++;
		}	
	$GTOOLS::TAG{'<!-- REGULAR_NEWSLETTERS -->'} = $c;
	$template_file = 'index-lists.shtml';
	}



##
##
##
if (($VERB eq 'ADD_SUBLIST_RECIPIENT') || ($VERB eq 'REMOVE_SUBLIST_RECIPIENT')) {
	require CUSTOMER;
	my $EMAILS = $ZOOVY::cgiv->{'EMAILS'};
	if (not defined $EMAILS) { $EMAILS = $ZOOVY::cgiv->{'EMAIL'}; }
		
	my @RESULTS = ();
	foreach my $EMAIL ( split(/[\s,\n\r;]+/,$EMAILS) ) {
		$EMAIL =~ s/^[\s]+//g;	# strip leading whitespace
		$EMAIL =~ s/[\s]$+//g;  # strip trailing whitepsace

		if ($EMAIL =~ /^[\d\-]+$/) {
			## EMAIL is a phone #!?
			}
		elsif (not &ZTOOLKIT::validate_email($EMAIL)) {
			push @RESULTS, "<font color='red'>$EMAIL does not appear to be valid</font>";
			$EMAIL = '';
			}

		next if ($EMAIL eq '');

		my $changed = 0;
		my ($C) = CUSTOMER->new($USERNAME,EMAIL=>$EMAIL,PRT=>$PRT,INIT=>0x1,CREATE=>2);
		my ($newsletter) = $C->fetch_attrib('INFO.NEWSLETTER');
		my $BITMASK = 1 << ($ID-1);
		if ($VERB eq 'ADD_SUBLIST_RECIPIENT') {
			if (($newsletter & $BITMASK)>0) {
				push @RESULTS, "$EMAIL is already subscribed.";
				}
			else {
				$newsletter |= $BITMASK; $changed++;
				push @RESULTS, "$EMAIL was added.";
				}
			}
		elsif ($VERB eq 'REMOVE_SUBLIST_RECIPIENT') {
			if (($newsletter & $BITMASK)==0) {
				push @RESULTS, "$EMAIL was already removed.";
				}
			else {
				$newsletter = $newsletter & (0xFFFF-$BITMASK); $changed++;
				push @RESULTS, "$EMAIL was removed.";
				}
			}
		if ($changed) {
			$C->set_attrib('INFO.NEWSLETTER',$newsletter);
			$C->save();
			}

		}

	foreach my $txt (@RESULTS) {
		push @MSGS, "SUCCESS|$txt";
		}
	$GTOOLS::TAG{'<!-- RESULTS -->'} .= "<br>";

	$VERB = 'EDIT_SUBLIST_RECIPIENTS';
	}

if ($VERB eq 'EDIT_SUBLIST_BULK') {	
	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
	$template_file = 'edit-sublist-bulk.shtml';	
	}


if ($VERB eq 'EDIT_SUBLIST_RECIPIENTS') {
	
	my $c = '';
	my $BITMASK = 1 << ($ID-1);
	require CUSTOMER::BATCH;
	my (%ref) = &CUSTOMER::BATCH::list_customers($USERNAME,$PRT,NEWSLETTERMASK=>$BITMASK);
	
	use Data::Dumper;
	# $c = Dumper($ref);
	foreach my $email (sort keys %ref) {
		$c .= "<tr>";
		$c .= "<td>";
		$c .= "<a href='/biz/manage/newsletters/index.cgi?VERB=REMOVE_SUBLIST_RECIPIENT&ID=$ID&EMAIL=$email'>[Remove]</a></td>";
		$c .= "<td>$email</td>";
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td><i>No subscribers currently found</i></td></tr>";
		}

	$GTOOLS::TAG{'<!-- SUBSCRIBERS -->'} = $c;
	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
	$template_file = 'edit-sublist-recipients.shtml';	
	}


##
## checks if ID exists, then
## updates/inserts user input into NEWSLETTER table as appropriate
## 
if($VERB eq "SAVE_SUBLIST"){
	if(defined $ZOOVY::cgiv->{'NAME'} && $ZOOVY::cgiv->{'NAME'} ne ''){

		my $pstmt = "select count(*) ".
						"from NEWSLETTERS ".
						"where MID=$MID and PRT=$PRT ".
						"and ID=".int($ID);
		print STDERR $pstmt."\n";
		my ($count) = $udbh->selectrow_array($pstmt);

		# strip out html and quotes, then
		# quote for DB update/insert
		### switched from AUTOEMAIL::htmlStrip to ZTOOLKIT::htmlstrip
		### patti - 2008-03-17
		$ZOOVY::cgiv->{'NAME'} =~ s/\n$//;
		my $qtNAME = $udbh->quote(&ZTOOLKIT::htmlstrip($ZOOVY::cgiv->{'NAME'}));
		my $qtMODE = $udbh->quote(int($ZOOVY::cgiv->{'mode'}));
		my $qtES = $udbh->quote(&ZTOOLKIT::htmlstrip($ZOOVY::cgiv->{'desc'}));

		if ($count>0) {
			my $pstmt = "update NEWSLETTERS ".
							"set NAME=$qtNAME,".
							"MODE=$qtMODE,".
							"EXEC_SUMMARY=$qtES ".
							"where MID=$MID and PRT=$PRT and ID=$ID";
			$udbh->do($pstmt);
			}
		else {
			my $pstmt = "insert into NEWSLETTERS ".
						"(ID,MID,USERNAME,PRT,NAME,MODE,EXEC_SUMMARY,CREATED_GMT) values ";
			$pstmt .= "($ID,$MID,".$udbh->quote($USERNAME).",$PRT,$qtNAME,$qtMODE,$qtES,".time().')';
			$udbh->do($pstmt);
			}
			
		$LU->log('UTILITIES.NEWSLETTER',"Changed Subscriber List $ID","SAVE");
		$VERB = 'SUBSCRIBER-LISTS';
		}
	else{
		push @MSGS, "ERROR|Please be sure to fill out the name of the Subscription List.";
   	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
		$VERB = 'EDIT_SUBLIST';
		}
	}

##
## get data from DB on NEWSLETTER (subscription list), display for user
## 
print STDERR "VERB: $VERB\n";
if ($VERB eq "EDIT_SUBLIST"){
   push @BC, { name=>'Configure Subscription List' };

   $GTOOLS::TAG{'<!-- ID -->'} = $ID;

   my @RESULTS = &CUSTOMER::NEWSLETTER::fetch_newsletter_detail($USERNAME,$PRT);
   my $x = $RESULTS[$ID];

	my $NAME = ($x->{'NAME'} eq '' && $ID == 1)?"Default Store Newsletter":$x->{'NAME'};
	#if($NAME eq '' && $ID == 1){ $NAME = "Default Store Newsletter"; }
	
	my $MODE = defined($x->{'MODE'})?$x->{'MODE'}:-1;
	my $EXEC_SUMMARY = (defined $ZOOVY::cgiv->{'desc'})?$ZOOVY::cgiv->{'desc'}:$x->{'EXEC_SUMMARY'};

   $GTOOLS::TAG{'<!-- NAME -->'} = $NAME;
   $GTOOLS::TAG{'<!-- EXEC_SUMMARY -->'} = $EXEC_SUMMARY;
   
	#####
	## MODE=1 => Default
	## MODE=2 => Targeted
	## MODE=0 => Exclusive
	#####
	$GTOOLS::TAG{'<!-- MODE_-1 -->'} = $MODE==0?'checked':'';
	$GTOOLS::TAG{'<!-- MODE_0 -->'} = $MODE==0?'checked':'';
   $GTOOLS::TAG{'<!-- MODE_1 -->'} = $MODE==1?'checked':'';
   $GTOOLS::TAG{'<!-- MODE_2 -->'} = $MODE==2?'checked':'';

   $template_file = 'edit-sublist.shtml';
   }









##
##
##
if ($VERB eq '') {
	## CAMPAIGNS
	## Build 3 separate tables:
	##  PENDING, APPROVED, FINISHED
	## where the header may be different for all
	my $pstmt = "select * ".
					"from CAMPAIGNS ".
					"where MID=$MID ".
					" /* $USERNAME */ and PRT=$PRT and CPG_TYPE='NEWSLETTER' order by STATUS,FINISHED_GMT desc,ID desc";

	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	

	my @UNSENT = ();
	my @ACTIVE = ();
	my @FINISHED = ();

	while ( my $CREF = $sth->fetchrow_hashref() ) {
		# my $CREATE_DATE = &ZTOOLKIT::pretty_date($CREF->{'CREATED_GMT'}, -1);
		$CREF->{'CREATE_DATE'} = &ZTOOLKIT::pretty_date($CREF->{'CREATED_GMT'}, -1);

		# my $START_DATE = &ZTOOLKIT::pretty_date($CREF->{'STARTS_GMT'}, -1);
		$CREF->{'START_DATE'} = &ZTOOLKIT::pretty_date($CREF->{'FINISHED_GMT'}, 1);

		# $START_DATE = &ZTOOLKIT::pretty_date($CREF->{'QUEUED_GMT'}, 1);


		#$CREATE_DATE = &ZTOOLKIT::pretty_date($CREF->{'STARTS_GMT'}, 1);
		#$START_DATE = &ZTOOLKIT::pretty_date($CREF->{'FINISHED_GMT'}, 1);
		# my $CAMPAIGN_ID = $CREF->{'ID'};
	
		## BEGIN assigning column values for types
		## values for pending
		## CAMPAIGN, CREATE DATE, ACTIONS
		## may switch hrefs to images
		## actions for pending
		if ($CREF->{'STATUS'} eq 'PENDING') {
			push @UNSENT, $CREF;
			}
		elsif ($CREF->{'STATUS'} eq 'APPROVED') {
			push @ACTIVE, $CREF;
			}
		elsif ($CREF->{'STATUS'} eq 'QUEUED') {
			push @ACTIVE, $CREF;
			}
		elsif ($CREF->{'STATUS'} eq 'FINISHED') {
			push @FINISHED, $CREF;
			}
		else {
			$CREF->{'STATUS'} = "UNKNOWN-$CREF->{'STATUS'}";
			push @FINISHED, $CREF;
			}
		}
	$sth->finish();
			
	my $r = '';
	my $c = '';


	$c = '';
	foreach my $CREF ( @UNSENT ) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= qq~<tr class='$r'>
		<td>
		<input class='minibutton' value='Preview' type="button" onClick="navigateTo('/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-PREVIEW&ID=$CREF->{'ID'}');">
		<input class='minibutton' value='Copy' type="button" onClick="navigateTo('/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-COPY&ID=$CREF->{'ID'}');">
		<input class='minibutton' value='Edit' type="button" onClick="navigateTo('/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-EDIT&ID=$CREF->{'ID'}');">
		<input class='minibutton' value='Delete' type="button" onClick="navigateTo('/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-NUKE&ID=$CREF->{'ID'}');">
		</td>
		<td valign='top'>$CREF->{'NAME'}</td>
		<td valign='top'>$CREF->{'CREATE_DATE'}</td>
		</tr>~;
		}
	if (scalar(@UNSENT)==0) {
		$c .= '<tr><td colspan=3><i>No unsent newsletters</td></tr>';
		}
	$GTOOLS::TAG{'<!-- UNSENT -->'} = $c;

	## send date for approved
	## CAMPAIGN, CREATE DATE, START DATE
	$c = '';
	foreach my $CREF ( @ACTIVE ) {

		$c .= 
		"<tr>
		<td valign='top'>$CREF->{'NAME'}</td>
        <td valign='top'>$CREF->{'CREATE_DATE'}</td>
		<td valign='top'>".&ZTOOLKIT::pretty_date($CREF->{'STARTS_GMT'}, 1).
			(($CREF->{'STARTS_GMT'}<time())?'<br><font color="red">OVERDUE: WILL START SHORTLY</font>':'' ).
		"</td>
		<td valign='top'><a target=_new href=\"/biz/manage/newsletters/index.cgi?VERB=DISPLAY_HTML&ID=$CREF->{'ID'}\">[ View ]</a>
		<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-COPY&ID=$CREF->{'ID'}\">[ Copy ]</a><br>
		<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-STOP&ID=$CREF->{'ID'}\">[ Stop Send ]</a> </td>
		</tr>";

#		my $PUBLIC_URL = &CUSTOMER::NEWSLETTER::cref_to_public_url($CREF);
#		$c .= 
#		"<tr>
#		<td valign='top'>$CREF->{'NAME'}</td>
#		<td valign='top'>$CREF->{'START_DATE'}</td>
#		<td valign='top'>
#			<a target=_new href=\"/biz/manage/newsletters/index.cgi?VERB=DISPLAY_HTML&ID=$CREF->{'ID'}\">[ View ]</a>
#			<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-COP&ID=$CREF->{'ID'}\">[ Copy ]</a><br>
#			<a href=\"$PUBLIC_URL\">[Public URL]</a><br>
#			<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-STOP&ID=$CREF->{'ID'}\">[ Stop Send ]</a>
#		</td>
#		<td valign='top'>
#			Total Recipients: $CREF->{'STAT_QUEUED'}<br>
#			Emails Sent So Far: $CREF->{'STAT_SENT'}<br>
#		</td>
#		</tr>";
		}
	if (scalar(@ACTIVE)==0) {
		$c .= '<tr><td colspan=3><i>No active newsletters</td></tr>';
		}
	$GTOOLS::TAG{'<!-- ACTIVE -->'} = $c;

	## report data for finished
	## CAMPAIGN, CREATE DATE, START DATE, TRANSMISSION, RESULTS
	$c = '';
	foreach my $CREF ( @FINISHED ) {
		my $PUBLIC_URL = &CUSTOMER::NEWSLETTER::cref_to_public_url($CREF);
		$c .= 
		"<tr>
		<td valign='top'>
			$CREF->{'NAME'}<br>
		</td>
        <td nowrap valign='top'>
			Subject: $CREF->{'SUBJECT'}<br>
			Campaign ID: $CREF->{'ID'}<br>
			".(($CREF->{'SCHEDULE'} ne '')?"Schedule: ".$CREF->{'SCHEDULE'}."<br>":'')."
			First Message Sent: $CREF->{'CREATE_DATE'}<br>
			Last Message Sent: $CREF->{'START_DATE'}<br>
		</td>
		<td nowrap valign='top'>
			<a target=_new href=\"/biz/manage/newsletters/index.cgi?VERB=DISPLAY_HTML&ID=$CREF->{'ID'}\">[ View ]</a><br>
			<a href=\"$PUBLIC_URL\">[Public URL]</a><br>
				<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-COPY&ID=$CREF->{'ID'}\">[ Copy ]</a><br>
		<a href=\"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-NUKE&ID=$CREF->{'ID'}\">[ Delete ]</a>
		</td>
		<td nowrap valign='top'>
			Emails Sent: $CREF->{'STAT_SENT'}<br>
			Emails Opened: $CREF->{'STAT_OPENED'}<br>
			Emails Viewed: $CREF->{'STAT_VIEWED'}<br>
			Emails Bounced: $CREF->{'STAT_BOUNCED'}<br>
			Emails Unknown: ".($CREF->{'STAT_SENT'}-($CREF->{'STAT_BOUNCED'}+$CREF->{'STAT_OPENED'}))."<br>
		</td>

		<td nowrap valign='top'>
			Unique Clicks: $CREF->{'STAT_CLICKED'}<br>
			Sale Counter: $CREF->{'STAT_PURCHASED'}<br>
			Sale Total: $CREF->{'STAT_TOTAL_SALES'}<br>
			Unsubscribes: $CREF->{'STAT_UNSUBSCRIBED'}<br>
		</td>

		</tr>";
		}

	## after getting all CAMPAIGNS
	$GTOOLS::TAG{'<!-- FINISHED -->'} = $c;

	$template_file = 'index.shtml';
	}

my @TABS = ();
push @TABS, { name=>"Status", link=>"/biz/manage/newsletters/index.cgi?VERB=", selected=>($VERB eq '')?1:0, };
push @TABS, { name=>"Subscriber Lists", link=>"/biz/manage/newsletters/index.cgi?VERB=SUBSCRIBER-LISTS", selected=>($VERB eq 'SUBSCRIBER-LISTS')?1:0, };
push @TABS, { name=>"Create Campaign", link=>"/biz/manage/newsletters/index.cgi?VERB=CAMPAIGN-NEW", selected=>($VERB eq 'CAMPAIGN-NEW')?1:0, };

# push @MSGS, "ERROR|Newsletters are offline until further notice, please check the recent news";


## all VERBS use this output except the "Step 2: Choose a Page Layout",
## which is using frames
&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,
	jquery=>1,
	title=>"Utilities: Newsletter Management",
	bc=>\@BC,	
	msgs=>\@MSGS,
	tabs=>\@TABS,
	help=>"#50394",
	file=>$template_file,	
	header=>1,
	);

&DBINFO::db_user_close();





__DATA__




