#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use CGI;
use GTOOLS;
use DBINFO;
use LUSER;

my ($dbh) = &DBINFO::db_zoovy_connect();

# this will fetch the remote username from the environment

my ($LU) = LUSER->authenticate(flags=>'_ADMIN',nocache=>1);
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


my ($LUADMIN) = LUSER->new($USERNAME,'ADMIN');
my $VERB = uc($ZOOVY::cgiv->{'ACTION'});
if ($VERB eq '') { $VERB = $ZOOVY::cgiv->{'VERB'}; }

my $template_file = "error.shtml";


if ($VERB eq 'PAYPAL-THANKYOU') {
	$template_file = 'paypal-thankyou.shtml';
	}

if ($VERB eq 'PAYPAL-CANCEL') {
	$template_file = 'paypal-cancel.shtml';
	}

my $ID = 0;
if ($VERB eq 'VIEW') {
	$ID = $ZOOVY::cgiv->{'ID'};
	$GTOOLS::TAG{'<!-- ID -->'} = $ID;

	require BILLING;
	my ($html) = &BILLING::build_invoice_html($USERNAME,$ID);

#	$pstmt = "select DETAIL_TXT from BS_SETTLEMENTS where MID=$MID and USERNAME=".$dbh->quote($USERNAME)." and ID=".$dbh->quote($ID);
#	print STDERR $pstmt."\n";
#	my $sth = $dbh->prepare($pstmt);
#	my $rv = $sth->execute;
#	($TXT) = $sth->fetchrow();
#	$sth->finish();

	$GTOOLS::TAG{"<!-- INVOICECOPY -->"} = $html;
	$template_file = 'view.shtml';
	}



if ($VERB eq 'SAVECOMPANY') {
	my $ERRORS = '';

	# handle general parameters.
	$LUADMIN->set("zoovy:company_name",$ZOOVY::cgiv->{"zoovy:company_name"});
	$LUADMIN->set("zoovy:firstname",$ZOOVY::cgiv->{"zoovy:firstname"});
	$LUADMIN->set("zoovy:middlename",$ZOOVY::cgiv->{"zoovy:middlename"});
	$LUADMIN->set("zoovy:lastname",$ZOOVY::cgiv->{"zoovy:lastname"});

	if (&ZTOOLKIT::validate_email($ZOOVY::cgiv->{"zoovy:email"})) {
		$LUADMIN->set("zoovy:email",$ZOOVY::cgiv->{"zoovy:email"});
		}
	else { $ERRORS .= "Invalid Account Contact Email!!<br>"; }

	if (&ZTOOLKIT::validate_email($ZOOVY::cgiv->{"zoovy:bill_email"})) {
		$LUADMIN->set("zoovy:bill_email",$ZOOVY::cgiv->{"zoovy:bill_email"});
		}
	else { $ERRORS .= "Invalid Billing Contact Email!!<br>"; }

	$LUADMIN->set("zoovy:phone",$ZOOVY::cgiv->{"zoovy:phone"});
	$LUADMIN->set("zoovy:address1",$ZOOVY::cgiv->{"zoovy:address1"});
	$LUADMIN->set("zoovy:address2",$ZOOVY::cgiv->{"zoovy:address2"});
	$LUADMIN->set("zoovy:city",$ZOOVY::cgiv->{"zoovy:city"});
	$LUADMIN->set("zoovy:state",$ZOOVY::cgiv->{"zoovy:state"});
	$LUADMIN->set("zoovy:country",$ZOOVY::cgiv->{"zoovy:country"});
	$LUADMIN->set("zoovy:zip",$ZOOVY::cgiv->{"zoovy:zip"});
	$LUADMIN->set("zoovy:phone",$ZOOVY::cgiv->{"zoovy:phone"});
	$LUADMIN->set("zoovy:facsimile",$ZOOVY::cgiv->{"zoovy:facsimile"});
	$LUADMIN->set("zoovy:newsletter", (defined $ZOOVY::cgiv->{'newsletter'})?1:0);

	$LUADMIN->log('SETUP.BILLING',"Updated billing settings","SAVE");
	$LUADMIN->save();
	$VERB = '';

	if ($ERRORS ne '') {
		$GTOOLS::TAG{'<!-- MSG -->'} = "<font color=red>$ERRORS</font><br><br>";
		}
	else { 
		$GTOOLS::TAG{'<!-- MSG -->'} = "<font color=red>Your changes have been successfully saved.</font><br><br>";
		}
	}


if ($VERB eq "") {	
	$GTOOLS::TAG{"<!-- USERNAME -->"} = $USERNAME;

	$GTOOLS::TAG{'<!-- NEWSLETTER -->'} = 'checked';

	$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = $LUADMIN->get("zoovy:company_name");
	$GTOOLS::TAG{"<!-- ZOOVY_FIRSTNAME -->"} = $LUADMIN->get("zoovy:firstname");
	$GTOOLS::TAG{"<!-- ZOOVY_MI -->"} = $LUADMIN->get("zoovy:middlename");
	$GTOOLS::TAG{"<!-- ZOOVY_LASTNAME -->"} = $LUADMIN->get("zoovy:lastname");
	$GTOOLS::TAG{"<!-- ZOOVY_EMAIL -->"} = $LUADMIN->get("zoovy:email");
	$GTOOLS::TAG{"<!-- ZOOVY_BILL_EMAIL -->"} = $LUADMIN->get("zoovy:bill_email");
	if (not &ZTOOLKIT::validate_email($GTOOLS::TAG{'<!-- ZOOVY_EMAIL -->'})) {
		$GTOOLS::TAG{'<!-- WARN_EMAIL -->'} = "<font color='red'>warning: if you do not have a contact email, you may miss important messages from zoovy.</font>";
		}
	if (not &ZTOOLKIT::validate_email($GTOOLS::TAG{'<!-- ZOOVY_BILL_EMAIL -->'})) {
		$GTOOLS::TAG{'<!-- WARN_BILL_EMAIL -->'} = "<font color='red'>warning: if you do not have a contact email, you may miss important messages from zoovy.</font>";
		}
	$GTOOLS::TAG{"<!-- ZOOVY_PHONE -->"} = $LUADMIN->get("zoovy:phone");
	$GTOOLS::TAG{"<!-- ZOOVY_ADDRESS1 -->"} = $LUADMIN->get("zoovy:address1");
	$GTOOLS::TAG{"<!-- ZOOVY_ADDRESS2 -->"} = $LUADMIN->get("zoovy:address2");
	$GTOOLS::TAG{"<!-- ZOOVY_CITY -->"} = $LUADMIN->get("zoovy:city");	
	$GTOOLS::TAG{"<!-- ZOOVY_STATE -->"} = $LUADMIN->get("zoovy:state");
	$GTOOLS::TAG{"<!-- ZOOVY_COUNTRY -->"} = $LUADMIN->get("zoovy:country");
	$GTOOLS::TAG{"<!-- ZOOVY_ZIP -->"} = $LUADMIN->get("zoovy:zip");
	$GTOOLS::TAG{"<!-- ZOOVY_FAX -->"} = $LUADMIN->get("zoovy:facsimile");

	## determine the account typ
	my $acct = '';
	if ($FLAGS =~ /TRIAL/) {
		$acct = 'Trial';
		$GTOOLS::TAG{'<!-- ACCOUNT_TYPE -->'} = "TRIAL";
		$GTOOLS::TAG{'<!-- BILLING_DAY -->'} = '<i>Not Set</i>';
		$GTOOLS::TAG{'<!-- PACKAGE_DETAIL -->'} = '<i>This is an evaluation account.</i>';
		} 
	else {
		## determine account type and billing day
		$GTOOLS::TAG{'<!-- FLAGS -->'} = $FLAGS;
		my $pstmt = "select BILL_DAY, BILL_PACKAGE, BPP_MEMBER, BILL_PRICING_REVISION, BILL_CUSTOMRATES from ZUSERS where MID=$MID /* USERNAME=".$dbh->quote($USERNAME)." */";
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		my ($billday,$billpackage,$is_bpp, $billrev,$bill_customrates) = $sth->fetchrow();
		$sth->finish();
		$GTOOLS::TAG{"<!-- ACCOUNT_TYPE -->"} = $billpackage;
		$GTOOLS::TAG{"<!-- BILLING_DAY -->"} = $billday;
		require BILLING;
		my ($pkgref) = &BILLING::get_packageref($billpackage);
		if (substr($bill_customrates,0,1) eq '~') {
			## if the first character is a ~ then we fully override all rates from package
			$bill_customrates = substr($bill_customrates,1);
			}
		else {
			## merge custom rates with package rates.
			$bill_customrates = "$pkgref->{'RATES'},$bill_customrates";
			}
		if ($is_bpp) {
			$bill_customrates = "BPP=$is_bpp,$bill_customrates";
			}

		$GTOOLS::TAG{'<!-- PACKAGE_DETAIL -->'} = qq~
<b>Name: $pkgref->{'NAME'}</b><br>
<br>
<b>Description:</b>
<div>$pkgref->{'DESCRIPTION'}</div>
<br>
<b>Support Policy:</b>
<div>$pkgref->{'POLICY_SUPPORT'}</div>
~;

		my $txt;

		if ($is_bpp==0) {
			## not bpp
			}
		elsif ($is_bpp==1) {
			$txt .= "Account participates in BPP program, and will receive a 12.5% discount on all fees listed below.<br>";
			}
		elsif ($is_bpp==2) {
			$txt .= "Account participates in BPP preferred tier, and will receive a 25% discount on all fees listed below.<br>";
			}
		else {
			$txt .= "UNKNOWN BPP DISPOSITION - PLEASE CONTACT BILLING.<br>";
			}

		$txt .= sprintf("Package Monthly Fee: \$%.2f<br>",$pkgref->{'AMOUNT'});
		my $RATES = &BILLING::parse_rates($bill_customrates,partial=>1);
		if ($LUSERNAME eq 'SUPPORT') {
			## zoovy employees can see this.
			use Data::Dumper; 
			$txt .= "<hr><font color='red'>**** ZOOVY EMPLOYEES ONLY ****<br>custom_rates: $bill_customrates<br>".Dumper($RATES)."<br>FLAGS: $FLAGS<br></font><hr>";
			}

		if ($RATES->{'MIN'}>0) {
			$txt .= "Monthly Minimum Fee: \$$RATES->{'MIN'} -- <span class=\"hint\">(Monthly invoices will never be less than this)</span><br>";
			}
		if ($RATES->{'CAP'}>0) {
			$txt .= "Capped Order Rate: \$$RATES->{'CAP'} -- <span class=\"hint\">(Regardless of amount you will never pay more than this for an order.)</span><br>";
			}

		## display R1 .. R5 rates.
		for (my $i=1; $i<5; $i++) {
			my $Rx = 'R'.$i;		## R1, R2, R3, R4, R5
			my $Tx = 'T'.$i;		## T1, T2, T3, T4, T5
			my $Lx = 'L'.$i;		## L1, L2, L3, L4, L5
			if ($RATES->{$Rx}>0) {
				$txt .= sprintf("Tier $i Rate Success Fee: %.3f%", $RATES->{$Rx} * 100);
				if ($is_bpp) { 
					## no discount for you!
					if ($RATES->{$Tx}==0) { $RATES->{$Tx} = $RATES->{$Rx} * ((100 - $RATES->{'BPPSDR'})/100); }
					## woot, tx is set.. show them their effective rate.
					$txt .= sprintf(" -- but w/BPP effectively %.3f%",$RATES->{$Tx}*100); 
					}
				if ($RATES->{$Lx}>0) { $txt .= sprintf(" -- up to \$%.02f in sales",$RATES->{$Lx}); }
				$txt .= "<br>";
				}
			}
		
		if ($RATES->{'DFOF'} ne '') {
			## DFOF: discounted flat order fee
			$txt .= "This account has special negotiated flat fee per order pricing listed below:<br>";
			# if ($is_bpp) { $txt .= "(negotiated discount pricing reflects bpp discounts)<br>"; }
			my @TIERS = split(/,/,$RATES->{'DFOF-TIERS'});	## ex: 0,500,2500,10000,50000
			push @TIERS, '*';
			my $i = 0;
			my $lasttier = shift(@TIERS);
			while (scalar(@TIERS)>0) {
				my $tier = shift(@TIERS);
				$i++;
				if ($tier eq '*') {
					$txt .= sprintf("Tier $i: orders %d+ = \$%.2f per order.<br>",
						$lasttier,$RATES->{"DFOF-TIER-$lasttier"});
					}
				else {
					$txt .= sprintf("Tier $i: orders %d-%d = \$%0.2f per order.<br>",
						(($lasttier==0)?1:$lasttier),
						$tier-1,
						$RATES->{"DFOF-TIER-$lasttier"}
						);
					}
				$lasttier = $tier;
				}

			if ($i==1) {
				## special handlers if there are only one rate (not tiered)
				if ($RATES->{"DFOF-TIER-0"}==0) {
					$txt .= "*NOTE: No per-order fees will *ever* be applied.<br>";
					}				
				}
			}

		## pricing revision info  /httpd/modules/BILLING/PRODSK.pm
		if ($billrev==1) { 
			$txt .= "Pricing Rev.$billrev - no charge for products or disk space.<br>";
		#	$txt .= "Additional partitions:  users: <br>";
			}
		elsif ($billrev==2) { 
			$txt .= "Pricing Rev.$billrev - 1000 products and 100mb included, each additional 1000 products OR 100mb (whichever is greater) is \$20<br>";
			$txt .= "Additional partitions: \$50 users: \$10 <br>";
			}
		elsif ($billrev==3) { 
			$txt .= "Pricing Rev.$billrev - 5000 skus and 2gb. included, each additional 2500 skus OR 1gb (whichever is greater) is \$25<br>";
			$txt .= "Additional partitions: \$50 users: \$25<br>";
			}
		elsif ($billrev==4) { 
			$txt .= "Pricing Rev.$billrev - 5000 skus and 2gb. included, each additional 2500 skus OR 1gb (whichever is greater) <br>";
			$txt .= "Additional partitions:\$50 users:\$25 <br>";
			}
		elsif ($billrev==5) {
			$txt .= "STAFF2 - unlimited skus, partitions, users - no charge.<br>";
			}
		elsif ($billrev==6) {
			$txt .= "Pricing Rev.$billrev (COMPLETE) accounts include 10gb of space and 100,000 SKU included, with 10 sub-users, no charge on feature bundles.";			
			$txt .= "additional 5k SKU + 1gb of space are \$10, additional users: \$10 ea.<br>";
			}
		else {
			$txt .= "Pricing Rev.$billrev - rates unknown.<br>";
			}

		if ($RATES->{'PRT'}>0) {
			$txt .= sprintf("You receive a negotiated discounted fee \$%.2f per partition.<br>",$RATES->{'PRT'});
			}
		if ($RATES->{'BLK'}>0) {
			$txt .= sprintf("You receive a negotiated discounted fee \$%.2f per disk/sku block.<br>",$RATES->{'BLK'});
			}
		if ($RATES->{'USR'}>0) {
			$txt .= sprintf("You receive a negotiated discounted fee \$%.2f per additional user.<br>",$RATES->{'USR'});
			}

		## now lets talk about support charges.
		if ($FLAGS =~ /,BILLHELP,/) {
			$txt .= qq~You will be charged for any live or electronic technical support but will receive a credit for any issue determined to be a software defect (bug).<br>~;
			}
		elsif ($is_bpp) {
			$txt .= qq~As a BPP client you will receive 1 hour of prepaid implementation for every $100 you spend. In addition any implementation fees are applied against your monthly minimum.~;
			}
		else {
			$txt .= qq~You receive 1 hour of prepaid time each month. In addition any implementation fees are applied to your monthly minimum and will be covered by success fees.~;
			} 
		$txt .= qq~Zoovy rounds down to the minute.~;

		$GTOOLS::TAG{'<!-- FEES -->'} = $txt;

		}


	## determine payment preferences
	my $pstmt = "select * from ZUSER_PAYMENT where MID=$MID /* USERNAME=".$dbh->quote($USERNAME)." */";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $paym = undef;
	if ($sth->rows>0)
		{
		my $hashref = $sth->fetchrow_hashref();
		$paym = $hashref->{'PAYMETHOD'};
		} else {
		$paym = 'Not Configured.';
		}
	$GTOOLS::TAG{'<!-- PAYMENT_METHOD -->'} = $paym;


#+------------+-------------------------------------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| Field		| Type																																						  | Null | Key | Default				 | Extra			 |
#+------------+-------------------------------------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| ID			| int(11)																																		           |      | PRI | NULL                | auto_increment |
#| USERNAME   | varchar(20)                                                                                                             |      |     |                     |                |
#| MID        | int(11)                                                                                                                 |      |     | 0                   |                |
#| AMOUNT     | decimal(10,2)                                                                                                           |      |     | 0.00                |                |
#| CREATED    | datetime                                                                                                                |      |     | 0000-00-00 00:00:00 |                |
#| ACTION     | enum('C','D','')                                                                                                        |      |     |                     |                |
#| MESSAGE    | varchar(80)                                                                                                             |      |     |                     |                |
#| BILLABLE   | enum('SETUP_TBD','FEE_TBD','FVF_TBD','SETUP_WAIVED','SETUP_BILLED','FEE_WAIVED','FEE_BILLED','FVF_WAIVED','FVF_BILLED') | YES  |     | NULL                |                |
#| BUNDLE     | varchar(6)                                                                                                              |      |     |                     |                |
#| SETTLED    | int(11)                                                                                                                 |      |     | 0                   |                |
#| SETTLEMENT | int(11)                                                                                                                 |      |     | 0                   |                |
#+------------+-------------------------------------------------------------------------------------------------------------------------+------+-----+---------------------+----------------+

   # gets the payment history of the CUSTOMER
	$pstmt = "select ID, CREATED, BILLGROUP, BILLCLASS, MESSAGE, SETTLEMENT, AMOUNT from BS_TRANSACTIONS where MID=$MID and USERNAME=".$dbh->quote($USERNAME)." and SETTLEMENT=0";
	print STDERR $pstmt."\n";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
   
   my $RETURNSTRING = "";
	my $r = '';
	my $TOTAL = 0;
	while ( my ($ID,$WHEN,$BILLCLASS,$BILLGROUP,$MESSAGE,$SETTLEMENT,$AMOUNT,$ACCOUNT) = $sth->fetchrow() ) {
			if ($BILLGROUP eq 'WAIVED') { $AMOUNT = 0; }
			$TOTAL += $AMOUNT;
			$r = ($r eq 'r0')?'r1':'r0';
			$RETURNSTRING .= "<tr class='$r'>";
			$RETURNSTRING .= "<td valign=top>$WHEN</td>";
			$RETURNSTRING .= "<td valign=top>$BILLGROUP</td>";
			$RETURNSTRING .= "<td valign=top>$BILLCLASS</td>";
			$RETURNSTRING .= "<td valign=top>$MESSAGE</td>";

			# next get the amount 
			$RETURNSTRING .= "<td nowrap valign=top>\$".$AMOUNT."</td>";
			# if settlment is  empty then settlement is pending otherwise			
			# print the settlement number
			$RETURNSTRING .= "</tr>";
			} # end of the for 
	$GTOOLS::TAG{'<!-- AMOUNT -->'} = sprintf("%.2f",$TOTAL);

	if ($RETURNSTRING eq '') {
		#if ID is not in OPEN_TICKETS then its tells not id found
		$RETURNSTRING .= "<tr bgcolor='white'><td colspan='5'>No Pending Transactions Found</td></tr>";
		}

	# shows all the information in the table
	$GTOOLS::TAG{"<!-- TRANSACTIONS -->"} = $RETURNSTRING;  
	

	my $c = '';
	$pstmt = "select ID,SUBJECT,CREATED,AMOUNT,STATUS,PAID_DATE,ATTEMPTS from BS_SETTLEMENTS where MID=$MID and USERNAME=".$dbh->quote($USERNAME)." order by CREATED desc";
	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	my $rv = $sth->execute;

	while (my ($ID,$SUBJECT,$CREATED,$AMOUNT,$STATUS,$PAID,$ATTEMPTS) = $sth->fetchrow) {
		$c .= '<tr bgcolor="white"><td valign=top>'.$ID.' - '.$SUBJECT.'</td>';
		$c .= '<td valign=top>'.$CREATED.'</td>';
		if ($STATUS eq 'PAID') {
			$c .= "<td valign=top>$STATUS - $PAID</td>";
			}
		elsif ($STATUS eq 'PENDING') {
			$c .= '<td valign=top>PENDING</td>';
			}
		elsif ($STATUS eq 'DENIED') {
			$c .= "<td valign=top><font color=\"red\">DENIED</font> - $ATTEMPTS attempts</td>";
			}
		else {
			$c .= "<td valign=top><font color=\"red\">$STATUS</font></td>";
			}
		$c .= '<td valign=top><a href="index.cgi?ACTION=view&ID='.$ID.'">View Detail</a></td>';
		$c .= "<td valign=top>\$".sprintf("%.2f",$AMOUNT)."</td>";
		$c .= "</tr>\n";
		}
	$sth->finish;
	if ($c eq '') { $c .= "<tr bgcolor='white'><td colspan='5'>No billing has occured yet.</td></tr>"; }
	$GTOOLS::TAG{"<!-- INVOICES -->"} = $c;

	# loads the template 
	$template_file = "index.shtml";
}

&GTOOLS::output(
	'title'=>'Setup : Billing History',
	'file'=>$template_file,
	'header'=>'1',
	'help'=>'#50341',
	'tabs'=>[
		],
	'bc'=>[
		{ name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
		{ name=>'Billing History',link=>'http://www.zoovy.com/biz/setup/billing','target'=>'_top', },
		],
	);



&DBINFO::db_zoovy_close();

