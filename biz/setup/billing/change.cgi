#!/usr/bin/perl

use lib "/httpd/modules";
use DBINFO;
use ZOOVY;
use GTOOLS;
use CGI;
use ZACCOUNT;
use strict;

my @PAYMETHODS = (
	[ 'CREDIT', 'Credit Card' ],
	[ 'ECHECK', 'eCheck' ],
	[ 'PAYPAL', 'Paypal' ],
	[ 'PREPAID', 'PrePaid' ],
	);

my $dbh = &DBINFO::db_zoovy_connect();
#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&1');
#if ($USERNAME eq '') { &DBINFO::db_zoovy_close(); exit; }

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&1');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


my $q = new CGI;
my $ACTION = $q->param('ACTION');
my $error = '';
my $template_file = '';

if ($ACTION eq 'DELETE') {
	my $qtUSERNAME = $dbh->quote($USERNAME);
	my $qtID = $dbh->quote($q->param('ID'));

	my $pstmt = "delete from ZUSER_PAYMENT where MID=$MID /* $qtUSERNAME */ and ID=$qtID";
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);	
	$ACTION = '';
	}

if ($ACTION eq 'INC' || $ACTION eq 'DEC') {
	my $qtUSERNAME = $dbh->quote($USERNAME);
	my $qtID = $dbh->quote($q->param('ID'));

	my $pstmt = "update ZUSER_PAYMENT ";
	if ($ACTION eq 'INC') { $pstmt .= " set PAYORDER=PAYORDER+1 "; }
	elsif ($ACTION eq 'DEC') { $pstmt .= " set PAYORDER=PAYORDER-1 "; }
	$pstmt .= " where MID=$MID /* $qtUSERNAME */ and ID=$qtID";
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);	

	$LU->log("SETUP.BILLING.CHANGE-PAY","Changed payment information order","INFO");

	$ACTION = '';
	}

if ($ACTION eq 'SAVE') {
	my $CARDNUM = $q->param('cc_num');
	$CARDNUM =~ s/[^0-9]//gs;	# remove non-numeric cards

	my $CCEXPMO = $q->param('exp_mo');
	my $CCEXPYR = $q->param('exp_yr');

	my $mref = &ZOOVY::fetchmerchant_ref($USERNAME);
	$mref->{'zoovy:company_name'} = $q->param("zoovy:company_name");
	$mref->{'zoovy:firstname'} = $q->param("zoovy:firstname");
	$mref->{'zoovy:lastname'} = $q->param("zoovy:lastname");
	$mref->{'zoovy:email'} = $q->param("zoovy:email");
	$mref->{'zoovy:phone'} = $q->param("zoovy:phone");
	$mref->{'zoovy:bill_email'} = $q->param("zoovy:bill_email");
	&ZOOVY::savemerchant_ref($USERNAME,$mref);


	if ($q->param('PAYMETHOD') eq 'CREDIT') {
		require ZPAY;
		$error = &ZPAY::verify_credit_card($CARDNUM,$CCEXPMO,$CCEXPYR);
		if (
			($q->param('cc_num') eq '4111111111111111') || 
			($q->param('cc_num') eq '4242424242424242') || 
			($q->param('cc_num') eq '5105105105105100') || 
			($q->param('cc_num') eq '6011111111111117') || 
			($q->param('cc_num') eq '4444444444444448') || 
			($q->param('cc_num') eq '4444444411111111') || 
			($q->param('cc_num') eq '5555555555555557') || 
			($q->param('cc_num') eq '5555555533333333') || 
			($q->param('cc_num') eq '6011701170117011') || 
			($q->param('cc_num') eq '6011621162116211') || 
			($q->param('cc_num') eq '6011608860886088') || 
			($q->param('cc_num') eq '6011333333333333') || 
			($q->param('cc_num') eq '378282246310005') || 
			($q->param('cc_num') eq '370370370370370') || 
			($q->param('cc_num') eq '377777777777770') || 
			($q->param('cc_num') eq '343434343434343') || 
			($q->param('cc_num') eq '341111111111111') || 
			($q->param('cc_num') eq '341341341341341') || 
			($q->param('cc_num') eq '8888888888888888')
			) { 
			$error = 'Please enter a real credit card number.'; 
			}

		if (substr($q->param('cc_num'),0,1) eq '6') {
			$error = 'Sorry, but Zoovy does not accept Discover card.';
			}
		}

	my $pstmt = "select count(*) from ZUSER_PAYMENT where MID=$MID /* $USERNAME */";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($count) = $sth->fetchrow();
	$sth->finish();

	my $BANK = $q->param('ECHECK_BANK');
	my $CHECKING = $q->param('ECHECK_CHECKING');
	my $ROUTING = $q->param('ECHECK_ROUTING');

	#use Data::Dumper;
	#print STDERR Dumper($q);

	my $MASKCARD = &ZTOOLKIT::cardmask($CARDNUM);
	## perl code to mask all cards in db - run 11/30/11
	## perl -e 'use lib "/httpd/modules"; use ZTOOLKIT; use DBINFO; my ($zdbh) = &DBINFO::db_zoovy_connect(); my $pstmt = "select ID,CARDNUM from ZUSER_PAYMENT"; my $sth = $zdbh->prepare($pstmt); $sth->execute(); while ( my ($ID,$CARD) = $sth->fetchrow()) { print "ID: $ID\n"; $pstmt = "update ZUSER_PAYMENT set CARDNUM=".$zdbh->quote(&ZTOOLKIT::cardmask($CARD))." where ID=$ID"; print "$pstmt\n"; $zdbh->do($pstmt); } $sth->finish();'

	if (not $error) {
		require ZTOOLKIT::SECUREKEY;
		my $pstmt = &DBINFO::insert($dbh,'ZUSER_PAYMENT',{
			MID=>$MID, 
			USERNAME=>$USERNAME,
			PAYMETHOD=>$q->param('PAYMETHOD'),
			CARDNUM=>$MASKCARD,
			CARDNUM_SECRET=>&ZTOOLKIT::SECUREKEY::encrypt($USERNAME,$CARDNUM),
			EXP_MO=>$CCEXPMO,
			EXP_YR=>$CCEXPYR,
			BANK=>$BANK,
			CHECKING=>$CHECKING,
			ROUTING=>$ROUTING,
			'*CREATED'=>'now()',
			PAYORDER=>$count+1,			
			},debug=>1+2);

	#	$pstmt = "insert into ZUSER_PAYMENT (MID,USERNAME,PAYMETHOD,CARDNUM,EXP_MO,EXP_YR,BANK,CHECKING,ROUTING,CREATED,PAYORDER) values(";
	#	$pstmt .= "$MID,$qtUSERNAME,";
	#	$pstmt .= $dbh->quote($q->param('PAYMETHOD')).',';
	#	$pstmt .= "$qtCARDNUM,$qtCCEXPMO,$qtCCEXPYR,";
	#	$pstmt .= "$qtBANK,$qtCHECKING,$qtROUTING,";
	#	$pstmt .= "now(),$count+1)";
		print STDERR $pstmt."\n";
		my $rv = $dbh->do($pstmt);

		$pstmt = "delete from EXCEPTION_FLAGS where MID=$MID /* $USERNAME */ and FLAGS='DISABLE'";
		print STDERR $pstmt."\n";
		$dbh->do($pstmt);

		$pstmt = "update BS_SETTLEMENTS set STATUS='PENDING' where STATUS='DENIED' and MID=$MID /* $USERNAME */";
		print STDERR $pstmt."\n";
		$dbh->do($pstmt);

		&ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
		}

	if (not $error) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "Done!";	
		$template_file = "success.shtml";	

		open MH, "|/usr/sbin/sendmail -t";
		print MH "From: billing\@zoovy.com\n";
		print MH "To: billing\@zoovy.com\n";
		print MH "Subject: $USERNAME modified payment information\n\n";
		print MH "Just thought you'd like to know..\n";
		close MH;
		$LU->log("SETUP.BILLING.MODIFIED-PAY","Modified payment information order","INFO");
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = 'Error: '.$error;
		$ACTION = '';
		}

	}

if ($ACTION eq '') {


	$GTOOLS::TAG{'<!-- YEAR_01 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_02 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_03 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_04 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_05 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_06 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_07 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_08 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_09 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_10 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_11 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_12 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_13 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_14 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_15 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_16 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_17 -->'} = '';
	$GTOOLS::TAG{'<!-- YEAR_18 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_01 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_02 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_03 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_04 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_05 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_06 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_07 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_08 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_09 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_10 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_11 -->'} = '';
	$GTOOLS::TAG{'<!-- MON_12 -->'} = '';
	$GTOOLS::TAG{'<!-- CC_NUM -->'} = $q->param('cc_num');
	$GTOOLS::TAG{'<!-- MON_'.$q->param('exp_mo').' -->'} = 'selected';
	$GTOOLS::TAG{'<!-- YEAR_'.$q->param('exp_yr').' -->'} = 'selected';
	$GTOOLS::TAG{'<!-- ECHECK_BANK -->'} = '';
	$GTOOLS::TAG{'<!-- ECHECK_ROUTING -->'} = '';
	$GTOOLS::TAG{'<!-- ECHECK_CHECKING -->'} = '';

	my $hashref;
	my $paypref;
	my $backuppref;
	
	my $out = '';
	my $pstmt = "select * from ZUSER_PAYMENT where MID=$MID /* $USERNAME */ order by ID desc";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $rowcount = $sth->rows();
	my $counter = 1;
	while ( $hashref = $sth->fetchrow_hashref() ) {
		$out .= "<tr>";
#		if ($rowcount>$counter) { $out .= "<td><a href=\"change.cgi?ACTION=INC&ID=$hashref->{'ID'}\">[Move Up]</a></td>"; } else { $out .= "<td></td>"; }
#		if ($counter>1) { $out .= "<td><a href=\"change.cgi?ACTION=DEC&ID=$hashref->{'ID'}\">[Move Down]</a></td>"; } else { $out .= "<td></td>"; }
		$counter++;

		$out .= "<td><a href=\"change.cgi?ACTION=DELETE&ID=$hashref->{'ID'}\">[Remove]</a></td>";
		$out .= "<td>$hashref->{'PAYMETHOD'}</td>";
		
		if ($hashref->{'PAYMETHOD'} eq 'CREDIT') {
			# my $currently = substr($hashref->{'CARDNUM'},0,4);
			# for (my $x = 4; $x<length($hashref->{'CARDNUM'}); $x++) { $currently .= 'x'; }
			my $currently = sprintf("%s expires %d/%d",$hashref->{'CARDNUM'},$hashref->{"EXP_MO"},$hashref->{'EXP_YR'});
			$out .= "<td>$currently</td>";
			}
		elsif ($hashref->{'PAYMETHOD'} eq 'ECHECK') {
			$out .= "<td>$hashref->{'BANK'} $hashref->{'ROUTING'}:$hashref->{'CHECKING'}</td>";
			}
		elsif ($hashref->{'PAYMETHOD'} eq 'PREPAID') {
			$out .= sprintf("<td>Initial Balance: \$%.2f / Remaining Balance: \$%.2f</td>",$hashref->{'PREPAID_AMOUNT_TOTAL'},$hashref->{'PREPAID_AMOUNT_REMAINING'});
			}
		else {
			$out .= "<td></td>";
			}
		$out .= "</tr>";
		} 

	if ($out eq '') { 
		$out = "<tr><td><i>You currently have no payment methods configured - please add one.</I></td></tr>";
		}
	else {
		$out = "<tr><td colspan='1'>&nbsp;</td><td><b>Method</b></td><td><b>Description</b></td></tr>".$out;
		}
	$sth->finish;
	$GTOOLS::TAG{'<!-- METHODS -->'} = $out;
	

	$GTOOLS::TAG{"<!-- COMPANY_NAME -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:company_name");
	$GTOOLS::TAG{"<!-- ZOOVY_FIRSTNAME -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:firstname");
	$GTOOLS::TAG{"<!-- ZOOVY_MI -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:middlename");
	$GTOOLS::TAG{"<!-- ZOOVY_LASTNAME -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:lastname");
	$GTOOLS::TAG{"<!-- ZOOVY_EMAIL -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:email");
	$GTOOLS::TAG{"<!-- ZOOVY_PHONE -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:phone");
	$GTOOLS::TAG{"<!-- ZOOVY_BILLEMAIL -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:bill_email");

	my $c = '';
	foreach my $pp (@PAYMETHODS) {
		next if (($pp->[0] eq 'PAYPAL') && ($FLAGS =~ /NOPAYPAL/));
		my $selected = ($pp->[0] eq $paypref)?'selected':'';
		$c .= "<option $selected value=\"$pp->[0]\">$pp->[1]</option>";
		}
	$GTOOLS::TAG{'<!-- PAYMETHODS -->'} = $c;

	$template_file = 'change.shtml';
	} 


&GTOOLS::output(
   'title'=>'Setup : Billing / Change Payment',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Change Payment',link=>'http://www.zoovy.com/biz/setup/','target'=>'_top', },
      ],
   );

&DBINFO::db_zoovy_close();
