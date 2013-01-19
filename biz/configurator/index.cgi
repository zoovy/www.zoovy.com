#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use DBINFO;
use ZTOOLKIT;
require BILLING;

use strict;
use Data::Dumper;

my $dbh = &DBINFO::db_zoovy_connect();
require LUSER;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }


#my ($LU) = LUSER->authenticate(flags=>'_S&8',basic=>0);
#if (not defined $LU) { exit; }

#my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
#if ($MID<=0) { exit; }

my $PACKAGE_MONTHLY_BASE_FEE = 0;
my $BUNDLE = $ZOOVY::cgiv->{'PACKAGE'};
if (not defined $BUNDLE) { $BUNDLE = $ZOOVY::cgiv->{'BUNDLE'}; }		# shit, I should have passed BUNDLE= instead of PACKAGE=
$GTOOLS::TAG{'<!-- BUNDLE -->'} = $BUNDLE;
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
my $ERRORS = 0;
my %NEWSALE = ();

## if they don't have a basic flag, assume they're an expired trial!
if ($FLAGS !~ /,BASIC,/) { $FLAGS .= ',TRIAL,'; }

my $template_file = 'index.shtml';

if ($ZOOVY::cgiv->{'VERB'} eq 'PROCESS_SALE') {
	require ZPAY;

	my $PKG = 'BASIC'; 
	if ($FLAGS =~ /PKG=(.*?),/) { $PKG = $1; }

## A sale is just a quote with a different filename and some additional info
## A sale or quote is a storable file named username-xxxxx-quote.bin
## or username-xxxxx-sale.bin in /httpd/zoovy/quotes/ on app1

	my $pstmt = "select SALESPERSON from ZUSERS where USERNAME=".$dbh->quote($USERNAME);
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($SALESPERSON) = $sth->fetchrow();
	$sth->finish();

	$NEWSALE{'USERNAME'} = $USERNAME;
	$NEWSALE{'EMAIL'} = &ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:email');
	if ($NEWSALE{'EMAIL'} eq '') { &ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:support_email'); }
	if ($NEWSALE{'EMAIL'} eq '') {
		$ERRORS++; 
		$GTOOLS::TAG{'<!-- EMAIL_ERROR -->'} = "<font color='red'>You have no email address configured for this account. Cannot save.</font>";
		}

	$NEWSALE{'PACKAGE_ID'} = $PKG;
	$NEWSALE{'SALESPERSON'} = $SALESPERSON;
	$NEWSALE{'NOTES'} = 'Purchased online '.&ZTOOLKIT::pretty_date(time(),1);

	$NEWSALE{'CARD_NAME'} = $ZOOVY::cgiv->{'CARD_NAME'};
	$NEWSALE{'COMPANY_NAME'} = $ZOOVY::cgiv->{'COMPANY_NAME'};
	$NEWSALE{'COMPANY_PHONE'} = $ZOOVY::cgiv->{'COMPANY_PHONE'};
	$NEWSALE{'COMPANY_EMAIL'} = $ZOOVY::cgiv->{'COMPANY_EMAIL'};
	require ZTOOLKIT::SECUREKEY;
   $NEWSALE{'CC_NUM_SECRET'} = &ZTOOLKIT::SECUREKEY::encrypt($USERNAME,$ZOOVY::cgiv->{'CC_NUM'});
	$NEWSALE{'CC_EXP_MO'} = $ZOOVY::cgiv->{'CC_EXP_MO'};
	$NEWSALE{'CC_EXP_YR'} = $ZOOVY::cgiv->{'CC_EXP_YR'};
	my ($msg) = &ZPAY::verify_credit_card($ZOOVY::cgiv->{'CC_NUM'},$NEWSALE{'CC_EXP_MO'},$NEWSALE{'CC_EXP_YR'});
	if ($msg ne '') {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_CREDIT_CARD -->'} = "<tr><td colspan='2'><font color='red'>$msg</font></td></tr>";
		}

	my %BUNDLES = ();
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /upsell_(.*?)$/) {
			$BUNDLES{$1} = 1;
			}
		next unless ($k =~ /ship_/);
		$NEWSALE{uc($k)} = $ZOOVY::cgiv->{$k};
		$GTOOLS::TAG{'<!-- '.uc($k).' -->'} = &ZOOVY::incode($ZOOVY::cgiv->{$k});
		}
	my $str = '';
	foreach my $b (keys %BUNDLES) {
		$str .= sprintf("%b*%d,",$b,$BUNDLES{$b});
		}
	$NEWSALE{'BUNDLES'} = $str;
	

	$NEWSALE{'NEW_USERNAME'} = $ZOOVY::cgiv->{'NEW_USERNAME'};
	require ZSETUP;
	if (uc($NEWSALE{'NEW_USERNAME'}) eq uc($USERNAME)) {
		## this is okay
		}
	elsif (uc($NEWSALE{'NEW_USERNAME'}) =~ /[^A-Z0-9]/) {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_USERNAME -->'} = "<font color='red'>Username may only contain the characters A-Z and 0-9</font>";
		$NEWSALE{'NEW_USERNAME'} = $USERNAME;
		}
	elsif (uc($NEWSALE{'NEW_USERNAME'}) =~ /^[0-9]/) {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_USERNAME -->'} = "<font color='red'>Username may not start with a number.</font>";
		$NEWSALE{'NEW_USERNAME'} = $USERNAME;
		}
	elsif (length($NEWSALE{'NEW_USERNAME'})>20) {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_USERNAME -->'} = "<font color='red'>Username must not be more than 20 characters in length.</font>";
		$NEWSALE{'NEW_USERNAME'} = $USERNAME;
		}
	elsif (length($NEWSALE{'NEW_USERNAME'})<5) {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_USERNAME -->'} = "<font color='red'>Username must be longer than 5 characters.</font>";
		$NEWSALE{'NEW_USERNAME'} = $USERNAME;
		}
	elsif (&ZSETUP::userexists($NEWSALE{'NEW_USERNAME'})) {
		$ERRORS++;
		$GTOOLS::TAG{'<!-- ERROR_USERNAME -->'} = "<font color='red'>Username $NEWSALE{'NEW_USERNAME'} already exists - please try another.</font>";
		$NEWSALE{'NEW_USERNAME'} = $USERNAME;
		}
	$NEWSALE{'SALESNOTES'} = '';
	
	if ($ERRORS) {
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>$ERRORS errors occurred when trying to submit your request. please check below.</font>";
		$ZOOVY::cgiv->{'VERB'} = '';
		}
	else {
		require LUSER;
		$pstmt = "delete from BS_SETUP_TODO where MID=$MID /* $USERNAME */";
		$dbh->do($pstmt);

		my $qtIP = $dbh->quote($ENV{'REMOTE_ADDR'});
		$pstmt = "insert into BS_SETUP_TODO (MID,USERNAME,CREATED,DATA,IP) values ($MID,".$dbh->quote($USERNAME).',now(),'.$dbh->quote(LUSER::encodeini(\%NEWSALE)).','.$qtIP.')';
		$dbh->do($pstmt);

		require ZMAIL;
		ZMAIL::sendmail($USERNAME,"billing\@zoovy.com","ONLINE SIGNUP","please run bs_setup_todo - user $USERNAME has signed up online");

		$template_file = 'signup-thanks.shtml';
		}

##
## Sale/Quote File Format:
## {
##      'USERNAME'      => 'username',
##      'EMAIL'         => 'user@domain.com',
##      'PACKAGE_ID'    => 'EBAY', ## package ID for the selected package
##      'BUNDLE_QTYS'   => {
##                              'WEB' => '3' ## bundle ID is key, number of that bundle is the value
##                              'DEV' => '1' ## Note that these are in addition to the included package bundles, do not put package-included bundles in this list
##                         },
##                         ],
##      'SALESPERSON'   => 'foo',    ## salesperson ID for the account
##      'NOTES'         => '',       ## Notes visible to the customer
##      'NEW_USERNAME'  => '',       ## username to change to during account setup
##      'SALENOTES'     => '',       ## Notes regarding the sale, not visible to customer
##      'CC_NUM'        => '',       ## credit card info
##      'CC_EXP_MO'     => '',
##      'CC_EXP_YR'     => '',
##      'SHIPTO'        => '',       ## where to ship any relevant information to
## };
##

	# use add_user_bundle 	
	#1. Create a sale bin file as per the previous email (you can do this by calling BILLING::new_quote if you want)
	#2. Run BILLING::process_sale() on that sale ID (username-number).  There is a wrapper file in /httpd/scripts/billing2/process_sale.pl to do this.  This will be triggered automagically when we're comfortable with the process.  process_sale will return a blank if all is well, or an error string if something barfed.		
	}



if ($ZOOVY::cgiv->{'VERB'} eq 'REMOVE') {
	$GTOOLS::TAG{'<!-- BUNDLE -->'} = $ZOOVY::cgiv->{'BUNDLE'};
	$template_file = 'removewarn.shtml';
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'CONFIRMREMOVE') {
	my $package_id = undef;
	if ($FLAGS =~ /,PKG=(.*?),/) { $package_id = $1; }

	my $result = '';	
	my $pstmt = "select count(*) from BS_ACTIONS where PROCESSED=0 and USERNAME=".$dbh->quote($USERNAME)." and PROC='KILLBUNDLE'";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();
	if ($count>0) {
		$result = 'Sorry, but you have an unprocessed REMOVE feature request pending - please wait for that to finish processing! (may take up to 24 hrs)';
		}
	
	$pstmt = "select count(*) from BS_BUNDLES where ID=".$dbh->quote($BUNDLE);
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	($count) = $sth->fetchrow();
	$sth->finish();
	
	if ($result ne '') {
		## we already had a fatal error
		}
	elsif ($count==0) {
		$result = "Sorry, I cannot find the package $BUNDLE on your account";
		}
	else {
		$result = &BILLING::remove_user_bundle($USERNAME,$BUNDLE);
		$LU->log("SETUP.KILLBUNDLE","Removed bundle $USERNAME","INFO");
		}

	if ($result eq '') {
		$GTOOLS::TAG{'<!-- ERRORS -->'} = '<font color="blue">'.$BUNDLE.' has been successfully removed from your account.</font>';
		}
	else {
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>ERROR: $result</font>";
		}

	require ZACCOUNT;
	&ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
	$ZOOVY::cgiv->{'VERB'} = '';
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'ADD') {
	my $package_id = undef;
	if ($FLAGS =~ /,PKG=(.*?),/) { $package_id = $1; }

	my $qty = int($ZOOVY::cgiv->{'QTY'});
	if ($qty==0) { $qty = 1; }

	my $pstmt = "select count(*) from BS_BUNDLES where ID=".$dbh->quote($BUNDLE);
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();
	
	my $result = '';	
	if ($count==0) {
		$result = "Sorry, I cannot verify the package $BUNDLE";
		}
	else {
		$result = &BILLING::set_user_bundle($USERNAME, $BUNDLE, 1, $LUSERNAME, 0, $package_id);
		$LU->log("SETUP.ADDBUNDLE","Requested add bundle $BUNDLE","INFO");		
		}

	if ($result eq '') {
		$GTOOLS::TAG{'<!-- RESULT -->'} = '<div class="success">Has been successfully added to your account. (You may need to logout/login for these changes to take effect)</font>';
		}
	else {
		$GTOOLS::TAG{'<!-- RESULT -->'} = qq~<div class="error">ERROR: $result</div>~;
		}

	require ZACCOUNT;
	&ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
	$template_file = 'add.shtml';
	}
elsif ($ZOOVY::cgiv->{'VERB'} eq 'VIEW') {
	#+-------------+---------------------+------+-----+---------------------+-------+
	#| Field       | Type                | Null | Key | Default             | Extra |
	#+-------------+---------------------+------+-----+---------------------+-------+
	#| ID          | varchar(6)          |      | PRI |                     |       |
	#| NAME        | varchar(50)         |      |     |                     |       |	
	#| DESCRIPTION | varchar(255)        |      |     |                     |       |
	#| URL         | varchar(255)        |      |     |                     |       |
	#| ACTIVE      | tinyint(1) unsigned |      |     | 0                   |       |
	#| PUBLIC      | tinyint(1) unsigned |      |     | 0                   |       |
	#| MULTI       | tinyint(1) unsigned |      |     | 0                   |       |
	#| RESELLER    | varchar(12)         |      |     |                     |       |
	#| CREATED     | datetime            |      |     | 0000-00-00 00:00:00 |       |
	#| RETIRED     | datetime            | YES  |     | NULL                |       |
	#| FLAGS       | varchar(255)        |      |     |                     |       |
	#| PREREQ      | varchar(6)          |      |     |                     |       |
	#| AMOUNT      | decimal(8,2)        |      |     | 0.00                |       |
	#+-------------+---------------------+------+-----+---------------------+-------+
	$template_file = 'view.shtml'; 

	my $pstmt = "select NAME,SHORT_DESC,DESCRIPTION,WEBDOC,ACTIVE,AMOUNT,AMOUNT_ADD,MULTI from BS_BUNDLES where ID=".$dbh->quote($BUNDLE);
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($NAME,$SHORT,$DESCRIPTION,$WEBDOC,$ACTIVE,$AMOUNT,$AMOUNT_ADD,$MULTI) = $sth->fetchrow();
	$sth->finish();
	if (not defined $ACTIVE) { $ACTIVE = 0; }
	if ($MULTI) {
		$GTOOLS::TAG{'<!-- QUANTITY -->'} = '<b>This feature has per-seat licensing.<br>Clicking "Add Feature Now" will add 1 additional license.</b><br>';
		}
	$GTOOLS::TAG{'<!-- QUANTITY -->'} .= '<input type="hidden" name="QTY" value="1">';

	my $package_id = undef;
	if ($FLAGS =~ /,PKG=(.*?),/) { $package_id = $1; }

	$pstmt = "select FREE_BUNDLES from BS_PACKAGES where ID=".$dbh->quote($package_id);
	my ($FREE_BUNDLES) = $dbh->selectrow_array($pstmt);
	my %FREE = ();
	foreach my $bundle (split(/,/,$FREE_BUNDLES)) { $FREE{$bundle}++; }
	if ($FREE{$BUNDLE}) { $AMOUNT = 0; }

	if ($ACTIVE>0) {	
		$GTOOLS::TAG{'<!-- NAME -->'} = $NAME;
		$SHORT =~ s/\n/<br>/gs;
		$DESCRIPTION =~ s/\n/<br>/gs;
		$GTOOLS::TAG{'<!-- SHORT -->'} = $SHORT;
		if ($DESCRIPTION) {
			$GTOOLS::TAG{'<!-- DESCRIPTION -->'} = 
				'<br><br><div>'.
				'<div class="zoovytableheader">Billing Details:</div>'.
				$DESCRIPTION.
				'</div>';
			}
		if ($WEBDOC>0) {
			$GTOOLS::TAG{'<!-- URL -->'} = '<div>'.&GTOOLS::help_link("Webdoc #$WEBDOC",$WEBDOC).'</div>';
			}

		$GTOOLS::TAG{'<!-- AMOUNT -->'} = sprintf("%.2f",$AMOUNT);
		if ($MULTI>0) {
			$GTOOLS::TAG{'<!-- AMOUNT_ADD -->'} = sprintf("<b>Additional Seats: \$%.2f (each)</b><br>",$AMOUNT_ADD);
			}
		}
	else {
		$template_file = 'view-denied.shtml';
		$GTOOLS::TAG{'<!-- DESCRIPTION -->'} = 'No description available.';
		$GTOOLS::TAG{'<!-- AMOUNT -->'} = 'Unknown';
		}

	if ($FLAGS =~ /,TRIAL,/) {	
		$GTOOLS::TAG{'<!-- TRIAL_DENIED -->'} = "<font color='red'>Sorry, but as a trial you must first sign up before being allowed to add additional features.</font><br><br>";
		$template_file = 'view-denied.shtml';
		}

	}
#######################################################
elsif ( (index($FLAGS,',TRIAL,',)>=0) && (lc($ENV{'HTTPS'}) ne 'on')) {
	##
	## this isn't a secure page, we should redirect (this will pass through the other modules and no form will be printed)
	## trial signups can't be done in non-secure mode.
	##
	print "Location: https://www.zoovy.com/biz/configurator\n\n";
	$template_file = '';
	$ZOOVY::cgiv->{'VERB'} = 'TRIAL';
	}
elsif ($FLAGS =~ /,TRIAL,/) {
#| ID              | varchar(6)              |      | PRI |                     |       |
#| NAME            | varchar(50)             |      | MUL |                     |       |
#| DESCRIPTION     | mediumtext              |      |     |                     |       |
#| URL             | varchar(255)            |      |     |                     |       |
#| ACTIVE          | tinyint(1) unsigned     |      |     | 0                   |       |
#| PUBLIC          | tinyint(1) unsigned     |      |     | 0                   |       |
#| RATE_0          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| RATE_1          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| RATE_2          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| RATE_3          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| RATE_4          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| RATE_5          | decimal(11,10) unsigned |      |     | 0.0000000000        |       |
#| CUTOFF_1        | bigint(20) unsigned     |      |     | 0                   |       |
#| CUTOFF_2        | bigint(20) unsigned     |      |     | 0                   |       |
#| CUTOFF_3        | bigint(20) unsigned     |      |     | 0                   |       |
#| CUTOFF_4        | bigint(20) unsigned     |      |     | 0                   |       |
#| CUTOFF_5        | bigint(20) unsigned     |      |     | 0                   |       |
#| BUNDLES         | varchar(255)            |      |     |                     |       |
#| DENY_BUNDLES    | varchar(255)            |      |     |                     |       |
#| AMOUNT          | decimal(8,2)            |      |     | 0.00                |       |
#| SETUP           | decimal(8,2)            |      |     | 0.00                |       |
#| RESELLER        | varchar(12)             |      |     |                     |       |
#| CREATED         | datetime                |      |     | 0000-00-00 00:00:00 |       |
#| RETIRED         | datetime                | YES  |     | NULL                |       |
#| PREPAID_HOURS   | tinyint(4)              |      |     | 0                   |       |
#| SKIPBILLDAYS    | int(11)                 |      |     | 0                   |       |
#| PRORATE_PACKAGE | tinyint(4)              |      |     | 0                   |       |

	## this is a new trial.
	$template_file = 'signup.shtml';
	$ZOOVY::cgiv->{'VERB'} = 'TRIAL';
	
#	$GTOOLS::TAG{'<!-- SHIP_NAME -->'} = &ZOOVY::incode($NEWSALE{'SHIP_NAME'});
#	$GTOOLS::TAG{'<!-- SHIP_ADDRESS1 -->'} = &ZOOVY::incode($NEWSALE{'SHIP_ADDRESS1'});
#	$GTOOLS::TAG{'<!-- SHIP_ADDRESS2 -->'} = &ZOOVY::incode($NEWSALE{'SHIP_ADDRESS2'});
#	$GTOOLS::TAG{'<!-- SHIP_CITY -->'} = &ZOOVY::incode($NEWSALE{'SHIP_CITY'});
#	$GTOOLS::TAG{'<!-- SHIP_STATE -->'} = &ZOOVY::incode($NEWSALE{'SHIP_STATE'});
#	$GTOOLS::TAG{'<!-- SHIP_ZIP -->'} = &ZOOVY::incode($NEWSALE{'SHIP_ZIP'});

	my $PKG = 'BASIC'; 
	if ($FLAGS =~ /PKG=(.*?),/) { $PKG = $1; }

	### BEGIN BUILD THE CHANGE PACKAGE MATRIX
	my $pstmt = "select ID,NAME,DESCRIPTION,SETUP,AMOUNT,BUNDLES,SKIPBILLDAYS,PREPAID_HOURS,UPSELL_BUNDLES from BS_PACKAGES where ID=".$dbh->quote($PKG)." and ACTIVE=1 ";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my ($PACKAGE_id,$PACKAGE_name,$PACKAGE_description,$PACKAGE_setup,$PACKAGE_monthly,$PACKAGE_bundles,$PACKAGE_skipbilldays,$PACKAGE_prepaidhours,$PACKAGE_upsellbundles) = $sth->fetchrow();
	$PACKAGE_MONTHLY_BASE_FEE = $PACKAGE_monthly;
	$sth->finish();

	$PACKAGE_id = uc($PACKAGE_id);
	$PACKAGE_bundles = ",$PACKAGE_bundles,";
	$GTOOLS::TAG{'<!-- PACKAGE_DESC -->'} = $PACKAGE_description;
	$GTOOLS::TAG{'<!-- PACKAGE_ID -->'} = $PACKAGE_id;
	$GTOOLS::TAG{'<!-- PACKAGE_NAME -->'} = $PACKAGE_name;
	$GTOOLS::TAG{"<!-- PACKAGE_IMAGE -->"} = "<img src=\"/biz/configurator/images/package_".$PACKAGE_id."_white.jpg\" width=\"116\" height=\"88\" alt=\"\" border=\"0\">";
	if ($PACKAGE_id eq 'SHOPCART') {
		$GTOOLS::TAG{"<!-- PACKAGE_IMAGE -->"} = '';
		}
	$GTOOLS::TAG{"<!-- PACKAGE_SETUPFEE -->"} = $PACKAGE_setup;
	$GTOOLS::TAG{"<!-- PACKAGE_MONTHLYFEE -->"} = $PACKAGE_monthly;
	$GTOOLS::TAG{"<!-- PACKAGE_SKIPBILLDAYS -->"} = $PACKAGE_skipbilldays;
	$GTOOLS::TAG{"<!-- PACKAGE_PREPAIDHOURS -->"} = $PACKAGE_prepaidhours;

	$GTOOLS::TAG{'<!-- CC_NUM -->'} = $NEWSALE{'CC_NUM'};
	$GTOOLS::TAG{'<!-- CARD_NAME -->'} = $NEWSALE{'CARD_NAME'};
	$GTOOLS::TAG{'<!-- COMPANY_NAME -->'} = $NEWSALE{'COMPANY_NAME'};
	$GTOOLS::TAG{'<!-- COMPANY_EMAIL -->'} = $NEWSALE{'COMPANY_EMAIL'};
	$GTOOLS::TAG{'<!-- COMPANY_PHONE -->'} = $NEWSALE{'COMPANY_PHONE'};
	$GTOOLS::TAG{'<!-- NEW_USERNAME -->'} = $NEWSALE{'NEW_USERNAME'};
	if (not defined $NEWSALE{'NEW_USERNAME'}) { $NEWSALE{'NEW_USERNAME'} = $USERNAME; }
	### END THE CHANGE PACKAGE MATRIX


	my $UPSELL = $PACKAGE_bundles.','.$PACKAGE_upsellbundles;
	$pstmt = '';
	foreach my $p (split(/,/,$UPSELL)) { $pstmt .= $dbh->quote($p).','; } chop($pstmt);
	$pstmt = "select ID,NAME,SHORT_DESC,URL,AMOUNT from BS_BUNDLES where ID in ($pstmt) and ACTIVE>0";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $row = 0; my $col = 0; 
	my $color = '';
	my %BUNDLES = ();
	while ( my @foo  = $sth->fetchrow() ) {	
		$BUNDLES{$foo[0]} = \@foo;
		}
	
	foreach my $id (split(/,/,$UPSELL)) {
		next if (not defined $BUNDLES{$id});
		next if ($id eq 'BASIC');
		next if ($id eq 'BILLHELP');
		my ($id,$name,$description,$url,$amount) = @{$BUNDLES{$id}};
		if ($col % 2 == 0) { 
			if ($row % 2 == 0) { $c .= "<tr class='row1'>"; $color = '_purple'; } else { $c .= "<tr class='row2'>"; $color = '_white'; }
			$row++;
			} 

		if ($PACKAGE_bundles =~ /,$id,/) {
			$c .= "<td valign=top width='50' align=\"center\"><img src=\"/biz/configurator/images/green_check.gif\"></td>";
			}
		else {
			$c .= "<td valign=top width='50' align=\"center\"><input onClick=\"sumIt();\" ";
			if (defined $ZOOVY::cgiv->{'upsell_'.$id}) { $c .= "checked"; }
			$c .= " type=\"checkbox\" name=\"upsell_$id\">";
			$c .= "<input type=\"hidden\" name=\"price_$id\" value=\"$amount\"></td>";
			}
	
		$c .= "<td width='70' valign=top align=\"center\"><input type=\"image\" onClick=\"document.signupFrm.upsell_$id.checked = !document.signupFrm.upsell_$id.checked; sumIt(); return false;\" src=\"/biz/configurator/images/bundle_".$id.$color.".gif\" width=\"57\" height=\"58\" alt=\"\" border=\"0\"></td>";
		$c .= "<td width='200' valign=\"top\"><p style=\"margin: 2px;\"><strong>$name</strong><br>";
		$c .= "$description";
		$c .= "<br>\$".sprintf("%.2f",$amount)."/mo.<br>";
#		$c .= "<input type=\"image\" onClick=\"document.signupFrm.upsell_$id.checked = !document.signupFrm.upsell_$id.checked; sumIt(); return false;\" src=\"$imagename\" width=\"57\" height=\"58\" alt=\"\" border=\"0\">";

#		$c .= " [ <a href=\"http://www.zoovy.net/features/bundles.php?bundle=$id\" target=\"features\">Features</a> ]";
		$c .= "</p></td>";

		if ($col % 2 == 1) {
			$c .= "</tr>";
			}
		$col++;
		}

	my $jscell = qq~
	<td colspan='3' align='center'>
		<table cellpadding='0' cellspacing='2' width='100%' border='0'>
			<tr>
				<td>One Time Setup Fee:</td>
				<td>\$$PACKAGE_setup</td>
			</tr>
			<tr>
				<td colspan='2'><i>Setup Fees include the first $PACKAGE_skipbilldays days of access<br> and $PACKAGE_prepaidhours hours of pre-paid LIVE support time.<br><br></td>
			<tr>
				<td>Package Monthly Price:</td>
				<td>\$$PACKAGE_monthly</td>
			<tr>
				<td>Additional Features:</td>
				<td>\$<input size='5' type="textbox" name="ADDAMOUNT"></td>
			</tr>
			<tr>
				<td>Total Monthly Price:</td>
				<td>\$<input size='5' type="textbox" name="GRANDTOTAL"></td>
			</tr>
			<tr>
				<td colspan='2'><i>NOTE: You will only be billed the setup charge at this time. You will not be invoiced for any monthly fees for $PACKAGE_skipbilldays days</i></td>
			</tr>
		</table>
	</td>
	~;

	## this means the next one would have been a </tr>
	if (($col % 2) == 1) { 
		## ended odd.
		$c .= $jscell;
		$c .= "</tr>"; 
		} 
	else { 
		## ended even - add a blank WHITE row. (even if it ought to be purple, it's going to be white!)
		$c .= "<tr class='row2'>";
		$c .= "<td colspan='3'></td>";
		$c .= $jscell;
		$c .= "</tr>";
		}

	$sth->finish();
	$GTOOLS::TAG{'<!-- PACKAGE_UPSELL -->'} = $c;

	
	$pstmt = "select NAME,DESCRIPTION,URL,BUNDLES,DENY_BUNDLES,AMOUNT,SETUP,PREPAID_HOURS,SKIPBILLDAYS from BS_PACKAGES where ID=".$dbh->quote($PKG);
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($name,$desc,$url,$bundles,$amount,$setup,$prepaid,$skipbill) = $sth->fetchrow();
	$sth->finish();
	$GTOOLS::TAG{'<!-- PKG -->'} = $PKG;

	$pstmt = "select count(*) from BS_SETUP_TODO where USERNAME=".$dbh->quote($USERNAME);
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();
	if ($count) {
		$template_file = 'signup-thanks.shtml';
		}


	}
else {
	$ZOOVY::cgiv->{'VERB'} = '';
	}


if ($ZOOVY::cgiv->{'VERB'} eq '') {
	#+-------------+-------------+------+-----+---------------------+-------+
	#| Field       | Type        | Null | Key | Default             | Extra |
	#+-------------+-------------+------+-----+---------------------+-------+
	#| MID         | int(11)     |      | PRI | 0                   |       |
	#| USERNAME    | varchar(20) |      | MUL |                     |       |
	#| BILL_DAY    | tinyint(2)  | YES  |     | 1                   |       |
	#| SALESPERSON | varchar(20) |      |     |                     |       |
	#| PACKAGE_ID  | varchar(6)  |      |     |                     |       |
	#| CREATED     | datetime    |      |     | 0000-00-00 00:00:00 |       |
	#| BEGINS      | datetime    |      |     | 0000-00-00 00:00:00 |       |
	#| LAST_EXEC   | datetime    |      |     | 0000-00-00 00:00:00 |       |
	#+-------------+-------------+------+-----+---------------------+-------+

	my $pstmt = "select BILL_PACKAGE,BILL_PROVISIONED,BILL_DAY from ZUSERS where MID=".$dbh->quote($MID)." and USERNAME=".$dbh->quote($USERNAME);
	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($PACKAGE_ID,$CREATED,$BILL_DAY) = $sth->fetchrow();
	$sth->finish();

	$GTOOLS::TAG{'<!-- PACKAGE_ID -->'} = $PACKAGE_ID;


	$pstmt = "select ID,NAME,BUNDLES,UPSELL_BUNDLES,FREE_BUNDLES,AMOUNT from BS_PACKAGES where ID=".$dbh->quote($PACKAGE_ID)." and ACTIVE=1 ";
	my ($PACKAGE_id,$PACKAGE_name,$PACKAGE_bundles,$PACKAGE_upsellbundles,$PACKAGE_freebundles,$PACKAGE_monthly) = $dbh->selectrow_array($pstmt);

	

	my $c = '';
	$sth->finish();
	$PACKAGE_id = uc($PACKAGE_id);
	$PACKAGE_bundles = ",$PACKAGE_bundles,";
	$GTOOLS::TAG{'<!-- PACKAGE_NAME -->'} = $PACKAGE_name;
	$GTOOLS::TAG{"<!-- PACKAGE_IMAGE -->"} = '';

	my @SHOW_BUNDLES = ();
	my %FREE_BUNDLES = ();
	foreach my $bundle (split(/,/,$PACKAGE_bundles)) { push @SHOW_BUNDLES, $bundle; }
	foreach my $bundle (split(/,/,$PACKAGE_upsellbundles)) { push @SHOW_BUNDLES, $bundle; }
	foreach my $bundle (split(/,/,$PACKAGE_freebundles)) { 
		$FREE_BUNDLES{$bundle}++; 
		push @SHOW_BUNDLES, $bundle;
		}

	## always show the bundles this current user has
	$pstmt = "select BAB.BUNDLE_ID from BS_ACCOUNT_BUNDLES as BAB where BAB.MID=$MID";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($bundle)  = $sth->fetchrow() ) {	
		push @SHOW_BUNDLES, $bundle;
		}

#+--------------+------------------------+------+-----+---------------------+-------+
#| Field        | Type                   | Null | Key | Default             | Extra |
#+--------------+------------------------+------+-----+---------------------+-------+
#| ID           | varchar(8)             | NO   | PRI | NULL                |       |
#| NAME         | varchar(50)            | NO   |     | NULL                |       |
#| SHORT_DESC   | varchar(255)           | NO   |     | NULL                |       |
#| DESCRIPTION  | mediumtext             | NO   |     | NULL                |       |
#| URL          | varchar(255)           | NO   |     | NULL                |       |
#| ACTIVE       | tinyint(1) unsigned    | NO   |     | 0                   |       |
#| MULTI        | tinyint(1) unsigned    | NO   |     | 0                   |       |
#| RESELLER     | varchar(12)            | NO   |     | NULL                |       |
#| CREATED      | datetime               | NO   |     | 0000-00-00 00:00:00 |       |
#| FLAGS        | varchar(255)           | NO   |     | NULL                |       |
#| AMOUNT       | decimal(8,2)           | NO   |     | 0.00                |       |
#| AMOUNT_ADD   | decimal(8,2)           | NO   |     | 0.00                |       |
#| PERIOD       | enum('MON','QTR','YR') | YES  |     | MON                 |       |
#| ALLOW_REMOVE | tinyint(4)             | NO   |     | 1                   |       |
#+--------------+------------------------+------+-----+---------------------+-------+

	my %BUNDLES = ();
	$pstmt = '';
	$pstmt = "select * from BS_BUNDLES where ID in ".&DBINFO::makeset($dbh,\@SHOW_BUNDLES);
	print STDERR $pstmt."\n";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my $ref = $sth->fetchrow_hashref() ) {	
		$BUNDLES{ $ref->{'ID'} } = $ref;

		if ($FREE_BUNDLES{$ref->{'ID'}}) {
			$ref->{'AMOUNT'} = 0;
			}
		}
	$sth->finish();

#	my %SUBSCRIBED_BUNDLES = ();
#	$pstmt = "select * from BS_ACCOUNT_BUNDLES where  BUNDLE_ID in ".&DBINFO::makeset($dbh,\@SHOW_BUNDLES);
#	print STDERR $pstmt."\n";
#	$sth = $dbh->prepare($pstmt);
#	$sth->execute();
#	while ( my $ref = $sth->fetchrow_hashref() ) {	
#		$BUNDLES{ $ref->{'BUNDLE_ID'} }->{'USER_CUSTOM_PRICE'} = $ref->{'CUSTOM_PRICE'};
#		$BUNDLES{ $ref->{'BUNDLE_ID'} }->{'USER_CUSTOM_NAME'} = $ref->{'CUSTOM_NAME'};
#		$BUNDLES{ $ref->{'BUNDLE_ID'} }->{'USER_CREATOR'} = $ref->{'CREATOR'};
#		$BUNDLES{ $ref->{'BUNDLE_ID'} }->{'USER_CREATED'} = $ref->{'CREATED'};
#		}
#	$sth->finish();
	
	
	my $row = 0; my $col = 0; 
	my $color = '';
	foreach my $id (@SHOW_BUNDLES) {
	
		next if (not defined $BUNDLES{$id});
		next if ($id eq 'BASIC');
		next if ($id eq 'BILLHELP');
		# my ($id,$BREF->{'NAME'},$BREF->{'SHORT_DESC'},$url,$BREF->{'AMOUNT'},$BREF->{'MULTI'},$BREF->{'DESCRIPTION'},$BREF->{'ALLOW_REMOVE'}) = @{$BUNDLES{$id}};
		my $BREF = $BUNDLES{$id};
		delete $BUNDLES{$id};		## this makes sure we never show the same bundle twice.
		if ($col % 2 == 0) { 
			if ($row % 2 == 0) { $c .= "<tr class='row1'>"; $color = '_purple'; } else { $c .= "<tr class='row2'>"; $color = '_white'; }
			$row++;
			} 

		$c .= "<td width='70' valign='top' align=\"center\"><br><br>";
		my $imagename = "/biz/configurator/images/bundle_".$id.$color.".gif";
		if (! -f "../../$imagename") { $imagename = '/images/blank.gif'; }
		$c .= "<input type=\"image\" onClick=\"document.signupFrm.upsell_$id.checked = !document.signupFrm.upsell_$id.checked; sumIt(); return false;\" src=\"$imagename\" width=\"57\" height=\"58\" alt=\"\" border=\"0\">";
		# $c .= "<br><br><a href=\"http://www.zoovy.net/features/bundles.php?bundle=$id\" target=\"features\">detail</a><br>";

		$c .= "</td>";
		$c .= "<td width='250' valign=\"top\"><p style=\"margin: 2px;\"><strong>$BREF->{'NAME'}</strong><br>";
		$c .= "$BREF->{'SHORT_DESC'} <br>";

		if (length($BREF->{'DESCRIPTION'})>10) {
			$c .= "<a href=\"#detail!$id\" onClick=\"if (Element.visible('detail!$id')) { new Effect.SlideUp('detail!$id'); \$('moreorless!$id').innerHTML = '[More]'; } else { \$('moreorless!$id').innerHTML = '[Less]'; new Effect.SlideDown('detail!$id'); }\"><div id=\"moreorless!$id\">[More]</div></a><a name=\"#detail!$id\"></a><br>";
			$c .= qq~<div id="detail!$id" style="display: none;"><div class="hint">$BREF->{'DESCRIPTION'}<br></div></div>~;
			}
		# $c .= "<img src='/images/blank.gif' width='100%' height='5'><br>";
		$c .= "<br>";


		$pstmt = "select count(*) from BS_ACCOUNT_BUNDLES where BUNDLE_ID=".$dbh->quote($id)." and MID=$MID";
		$sth = $dbh->prepare($pstmt);
		$sth->execute();
		my ($count) = $sth->fetchrow();
		$sth->finish();
		if ($BREF->{'MULTI'}) {
			$c .= "<font color='330066'><b>Price: \$$BREF->{'AMOUNT'}/mo ".(($BREF->{'MULTI'})?' per seat':'')."</b></font><br>\n";
		 	my $qty = 0;
			if ($FLAGS =~ /,$id,/) { $qty = 1; }
			if ($FLAGS =~ /,$id\*[\d]+,/) { $qty = $1; }
			my $included = $qty - $count;		# take the qty available - subtract the qty purchased
			
			if ($included>0) { 
				$c .= "<b>[$included seat".(($included==1)?'':'s')." included FREE with account]</b><br>";
				}

			if ($count>0) {
				$c .= "<b>[$count additional seat".(($count==1)?'':'s')." purchased]</b><br>";
				}

			if ($included==0 && $count==0) {
				$c .= "<b>[0 seats currently available]</b><br>";
				}

			$c .= "<input type='button' class='button' value='Add' onClick=\"navigateTo('/biz/configurator?VERB=VIEW&BUNDLE=$id');\"> ";
			if (not $BREF->{'ALLOW_REMOVE'}) {
				$c .= "<i>Please contact billing\@zoovy.com to remove</i>";
				}
			elsif ($count > 0) {
				$c .= "<input type='button' class='button' value='Remove' onClick=\"navigateTo('/biz/configurator?VERB=REMOVE&BUNDLE=$id');\"> ";
				}
			}
		elsif ($PACKAGE_bundles =~ /,$id,/) {
			## included with package (cannot be removed)
			$c .= "<font color='330066'><b>Price: FREE</b></font><br>\n";
			$c .= "<b>[Included w/account]</b>";
			}
		else {
			## purchased separately, figure out if it's a multi.
			# if ($count>0) { $ZOOVY::cgiv->{'upsell_'.$id} = 1; }
			$c .= "<font color='330066'><b>Price: \$$BREF->{'AMOUNT'}/mo ".(($BREF->{'MULTI'})?' per seat':'')."</b></font><br>\n";

			if (($count>0) && (not $BREF->{'ALLOW_REMOVE'})) {
				$c .= "<b>[Currently added to account]</b><br>";
				$c .= "<i>Please contact billing\@zoovy.com to have this removed</i>";
				}
			elsif ($count>0) {
				$c .= "<b>[Currently added to account]</b><br>";
				$c .= "<input type='button' class='button' value='Remove' onClick=\"navigateTo('/biz/configurator?VERB=REMOVE&BUNDLE=$id');\"> ";
				}
			else {
				$c .= "<b>[Please add to enable]</b><br>";
				$c .= "<input type='button' class='button' value='Add' onClick=\"navigateTo('/biz/configurator?VERB=VIEW&BUNDLE=$id');\"> ";
				}

#			$c .= "<td width='50' align=\"center\"><input onClick=\"sumIt();\" ";
#			if (defined $ZOOVY::cgiv->{'upsell_'.$id}) { $c .= "checked"; }
#			$c .= " type=\"checkbox\" name=\"upsell_$id\">";
			$c .= "<input type=\"hidden\" name=\"price_$id\" value=\"$BREF->{'AMOUNT'}\">";
			}
		
		$c .= "<br><br>";
		$c .= "</p></td>";

		if ($col % 2 == 1) {
			$c .= "</tr>";
			}
		$col++;
		}

	$GTOOLS::TAG{'<!-- PACKAGE_MONTHLYFEE -->'} = $PACKAGE_monthly;
	my $jscell = qq~
	<td colspan='3' align='center' bgcolor='FFEEEE'>
		<table cellpadding='0' cellspacing='2' width='100%' border='0'>
			<tr>
				<td>Package Monthly Price:</td>
				<td>\$$PACKAGE_monthly</td>
			<tr>
				<td>Additional Features:</td>
				<td>\$<input size='5' type="textbox" name="ADDAMOUNT"></td>
			</tr>
			<tr>
				<td>Total Monthly Price:</td>
				<td>\$<input size='5' type="textbox" name="GRANDTOTAL"></td>
			</tr>
		</table>
	</td>
	~;
	$jscell = '';

	## this means the next one would have been a </tr>
	if (($col % 2) == 1) { 
		## ended odd.
		$c .= $jscell;
		$c .= "</tr>"; 
		} 
	else { 
		## ended even - add a blank WHITE row. (even if it ought to be purple, it's going to be white!)
		$c .= "<tr class='row2'>";
		$c .= "<td colspan='3'></td>";
		$c .= $jscell;
		$c .= "</tr>";
		}

	$sth->finish();
	$GTOOLS::TAG{'<!-- PACKAGE_UPSELL -->'} = "<!-- PACKAGE_UPSELL -->$c<!-- /PACKAGE_UPSELL -->";
	}

my @TABS = ();
if ($FLAGS =~ /,TRIAL,/) {
   push @TABS, { 'name'=>'Introduction', 'link'=>'/biz/', 'target'=>'_top' };
#   push @TABS, { 'name'=>'Pricing', 'link'=>'/biz/configurator', 'target'=>'_top' };
	}

if ($template_file ne '') {
	&GTOOLS::output('*LU'=>$LU,
   'title'=>'Setup : Account Configurator',
   'file'=>$template_file,
   'header'=>'1',
	'js'=>6,
   'help'=>'#50764',
	'head'=>qq~
<STYLE TYPE="text/css">
.tablehead	{font-family: verdana,arial, sans serif; color: #ffffff; font-size: 12px; font-weight: bold;}
.tablebox	{background-color: #3366CC;}
.row1	{background-color: #E1D9F0;}
.row2	{background-color: #FFFFFF;}
</style>

<script name="JavaScript"><!--

function cent(amount) {
	// returns the amount in the .50 format (instead of .5)
	amount = amount-0;
	// return(amount==Math.floor(amount))?amount+'.00':((amount*10==Math.floor(amount*10))?amount+'0':amount);
	amount = (Math.round(amount*100))/100;
		return(amount==Math.floor(amount))?amount+'.00':((amount*10==Math.floor(amount*10))?amount+'0':amount);
	}

function sumIt() {
	var total = 0;
	
	for (var i = 0; i<document.signupFrm.elements.length; i++) {
		if (document.signupFrm.elements[i].name.indexOf('upsell_')==0)	{
			if (document.signupFrm.elements[i].checked) {
				var pkg = document.signupFrm.elements[i].name.substring(7);
				total = total-0 + (document.signupFrm.elements[ 'price_'+pkg ].value-0);
				// alert(document.signupFrm.elements[i].name.substring(7));
				}
			}
		}
	document.signupFrm.elements['ADDAMOUNT'].value = cent(total);
	document.signupFrm.elements['GRANDTOTAL'].value = cent(total + ($PACKAGE_MONTHLY_BASE_FEE-0));

	}

//-->
</script>


~,
   'tabs'=>\@TABS,
   'bc'=>[
      { name=>'Account Configurator',link=>'/biz/configurator','target'=>'_top', },
      ],
   );
	}

&DBINFO::db_zoovy_close();
