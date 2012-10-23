#!/usr/bin/perl

use strict;
use CGI;
use lib "/httpd/modules";
use GTOOLS::Table;
use DBINFO;
use ZOOVY;

@::MSGS = ();

my %SKEYS = (
	'ebates'=>'EB',
	'bing'=>'BN',
	'upic'=>'UP',
	'razormouth'=>'RM',
	'buycom'=>'BY',
	'amazonpay'=>'AP',
	'veruta'=>'VR',
	'kount'=>'KT',
	);


print "Content-type: text/html\n\n";
print "<head>";
print qq~<link rel="STYLESHEET" type="text/css" onClick="JSgoTo();" href="/biz/standard.css">~;
print "</head>";

if ($ENV{'HTTPS'} ne 'on') {
	print "Please access this using https://\n\n";
	exit;
	}

#use Data::Dumper;
#print Dumper(\%ENV);
# print "Content-type: text/html\n\n";

my $header = '';
my $VERB = '';

my $q = CGI->new();

my $PARTNERUSER = ($q->param('partner_id'));
my $PARTNERPASS = ($q->param('partner_pass'));

if ($PARTNERUSER eq '') { $VERB = 'LOGIN'; }
elsif ($PARTNERPASS eq '') { $VERB = 'LOGIN'; }
elsif ($ZTOOLKIT::SECUREKEY::LOGINS{$PARTNERUSER} eq $PARTNERPASS) {
	$VERB = '';
	}
else { $VERB = 'LOGIN'; }
 

if ($VERB eq 'LOGIN') {

print qq~

<br>
<br>
<center>
<table border=1><tr><td>
<div class="zoovytableheader">Zoovy Partner Extranet</div>
<hr>
<form method="GET" action="index.cgi">
Papers please...:
<table>
	<tr>
		<td>Partner Login:</td>
		<td><input type="textbox" name="partner_id"></td>
	</tr>
	<tr>
		<td>Partner Password:</td>
		<td><input type="password" name="partner_pass"></td>
	</tr>
</table>
<input type="submit" value=" Login ">

</td></tr></table>

~;
	}
else {
	$VERB = $q->param('VERB');
	print qq~<form method=post ENCTYPE='multipart/form-data' id=thisFrm name=thisFrm action="index.cgi">
<center>
<table with=800><tr><td>
Logged in as $PARTNERUSER. 
<!-- Verb=$VERB --><hr>
<input type="hidden" value="$PARTNERUSER" name="partner_id">
<input type="hidden" value="$PARTNERPASS" name="partner_pass">
<input type="hidden" name="VERB">
~;
	}


if (($VERB eq 'KOUNT-ADD') && ($PARTNERUSER eq 'kount')) {
	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pass = $q->param('kountpass');
	my $kid = int($q->param('kountid'));
	$pass =~ s/^[\s]+//g;
	$pass =~ s/[\s]+$//g;
	my ($pstmt) = &DBINFO::insert($zdbh,'KOUNT_USERS',{
		KOUNT_ID=>$kid,
		KOUNT_PASS=>$pass,
		},sql=>1);
	print STDERR "$pstmt\n";
	if ($zdbh->do($pstmt)) {
		print "<div class='success'>Successfully added to db</div>";
		}
	$VERB = '';
	&DBINFO::db_zoovy_close();
	}



if ($VERB eq '') {

	foreach my $msg (@::MSGS) {
		my ($class,$txt) = split(/\|/,$msg);
		$class = lc($class);
		print qq~<div class=\"$class\">$txt</div>\n~;
		}

	if (1) {
	print qq~
<div class="zoovytableheader">User Security Key:</div><br>
Username: <input type="textbox" name="skey_username">
<input type="button" value=" Lookup SecureKey " onClick="thisFrm.VERB.value='SKEY'; thisFrm.submit();"><br>
<a href="http://www.zoovy.com/webdoc/?VERB=DOC&DOCID=50639"><i>[Learn more]</i></a><br>
<br>~;
		}

#	if ($PARTNERUSER eq 'buycom') {
#	print qq~
#<hr>
#<br>
#<b>Import NEWSKU Batch</b><br>
#Zoovy Username: <input type="textbox" name="ZOOVYUSER"><br>
#File: <input type="file" name="BATCHFILE"><br>
#<input type="button" value=" Upload " onClick="thisFrm.VERB.value='BUYCOM-UPLOADBATCH'; thisFrm.submit();"><br>
#REMINDER: Please make sure to use the header:<br>
#%SKU,buycom:listingid<br>
#<br>
#~;
#		}

	if ($PARTNERUSER eq 'kount') {

		my $zdbh = &DBINFO::db_zoovy_connect();
		my $pstmt = "select count(*) from KOUNT_USERS where PROVISIONED_GMT=0";
		my ($count) = $zdbh->selectrow_array($pstmt);
		&DBINFO::db_zoovy_close();
		if ($count<3) {
			print qq~<div class='warning'>WARNING: $count accounts available for provisioning, please add some.</div>~;
			}
		else {
			print qq~<div><b>$count accounts available for provisioning</b></div>~;
			}

		print qq~
		<div class="zoovytableheader">Kount Buttons!</div>
		<input type="button" value=" Display Existing Users " onClick="thisFrm.VERB.value='KOUNT-USERS'; thisFrm.submit();">
		<br><br>
		~;
		print qq~
		<div class="zoovytableheader">Add Unprovisioned Account</div>
		<table>
		<tr><td>Kount Merchant ID #</td><td><input type="textbox" name="kountid"></td></tr>
		<tr><td>Kount AWC Password</td><td><input type="textbox" name="kountpass"></td></tr>
		</table>
		<input type="button" value=" Add User " onClick="thisFrm.VERB.value='KOUNT-ADD'; thisFrm.submit();">
		~;	

		
		}
	


	if ($PARTNERUSER eq 'razormouth') {
	print qq~
<hr>
<br>
<div class="zoovytableheader">Verify Code</div><br>
Zoovy Username/Domain: <input type="textbox" name="RM_USER" value="">
<input type="button" value=" Display Code " onClick="thisFrm.VERB.value='RM-VERIFY'; thisFrm.submit();">

~;
		}

	if ($PARTNERUSER eq 'bing') {
	print qq~
<hr>
<br>
<div class="zoovytableheader">Pixel Lookup:</div><br>
Domain: <input type="textbox" name="BING_DOMAIN"><br>
Order ID: <input type="textbox" name="BING_ORDERID"><br>
<input type="checkbox" name="BING_FLAG-AS-PAID"> Flag order as paid (will auto dispatch notification)<br>
<input type="button" value=" Verify " onClick="thisFrm.VERB.value='BING-VERIFY'; thisFrm.submit();">
~;
		}


	if ($PARTNERUSER eq 'ebates') {
	print qq~
<div class="zoovytableheader">Sales Report:</div><Br>
<table>
	<tr>
	<td>Start:</td>
	<td><input size=8 type="textbox" name="txn_date_start"> (YYYYMMDD)</td>
	</tr>
	<tr>
	<td>End</td>
	<td><input size=8 type="textbox" name="txn_date_end"> (YYYYMMDD)</td>
	</tr>
</table>
<input type="button" value=" Transactions " onClick="thisFrm.VERB.value='TXN'; thisFrm.submit();">
<br>
<br>~;
		}


	if ($PARTNERUSER eq 'upic') {
	print qq~
<hr>
UPic Area:
Zoovy Username: <input type="textbox" name="UPIC_USERNAME"><br>
<input type="button" value=" Last 60 Days " onClick="thisFrm.VERB.value='UPIC-LAST60'; thisFrm.submit();">
<input type="button" value=" UPIC Packages " onClick="thisFrm.VERB.value='UPIC-PACKAGES'; thisFrm.submit();">
		~;
		}

	}





if (($VERB eq 'KOUNT-USERS') && ($PARTNERUSER eq 'kount')) {

	require ZWEBSITE;
	require DOMAIN::TOOLS;
	require LUSER;
	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pstmt = "select USERNAME,PRT,KOUNT_ID,PROVISIONED_GMT from KOUNT_USERS order by ID";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my $users = '';
	my $r = '';
	while ( my ($USERNAME,$PRT,$KOUNT_ID,$PROVISIONED_GMT) = $sth->fetchrow() ) {
		$r = ($r eq 'r0')?'r1':'r0';
		my $webdbref = {};
		if ($PROVISIONED_GMT>0) {
			($webdbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
			}

		if ($PROVISIONED_GMT == 0) { 
			$PROVISIONED_GMT = '--'; 
			}
		else {
			$PROVISIONED_GMT = &ZTOOLKIT::pretty_date($PROVISIONED_GMT,-2);
			}
		$users .= "<tr>";
		$users .= "<td valign=top>$KOUNT_ID</td><td valign=top>$USERNAME</td><td valign=top>$PRT</td>";
		$users .= "<td valign=top>$PROVISIONED_GMT</td>";


		my $deployed = '';
		if ($webdbref->{'kount'} eq '') {
			$deployed = 'not config.';
			}
		elsif ($webdbref->{'kount'} == 0) {
			$deployed = 'disabled'; 
			}
		elsif ($webdbref->{'kount'} == 1) {
			$deployed = 'test';
			}
		elsif ($webdbref->{'kount'} == 2) {	
			$deployed = 'live';
			}
		$users .= "<td valign=top>$deployed</td>";

		my $PKG = '?';
		my ($LU) = undef;
		if ($USERNAME ne '') {
			($LU) = LUSER->new($USERNAME,'');
			if (not defined $LU) { $PKG = '?'; }
			}

		if ((defined $LU) && (ref($LU) eq 'LUSER')) {
			if ($LU->flags() =~ /PKG\=(.*?),/) { $PKG = $1; }
			if ($LU->flags() =~ /,CANCEL,/) { $PKG = 'CANCEL'; }
			}
		
		$users .= sprintf("<td valign=top>%s</td>",$PKG);
		if ($PKG eq 'STAFF') {
			}
		elsif ($PKG eq 'CANCEL') {
			}
		elsif ($PKG eq '?') {
			}
		else {
			my ($DOMAIN) = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$PRT);
			$users .= "<td valign=top>$DOMAIN</td>";
			$users .= sprintf("<td valign=top>%s %s</td>",$LU->get('zoovy:firstname'),$LU->get('zoovy:lastname'));
			$users .= sprintf("<td valign=top>%s</td>",$LU->get('zoovy:phone'));
			$users .= sprintf("<td valign=top>%s</td>",
				$LU->get('zoovy:address1').
				(($LU->get('zoovy:address2') ne '')?"<br>".$LU->get('zoovy:address2'):'').
				"<br>".
				sprintf("%s, %s. %s %s",$LU->get('zoovy:city'),$LU->get('zoovy:state'),$LU->get('zoovy:zip'),$LU->get('zoovy:country'))
				);
				

			$users .= sprintf("<td valign=top>%s</td>",$LU->get(''));
			$users .= sprintf("<td valign=top>%s</td>",$LU->get(''));
			}
		$users .= "</tr>";
		}
	$sth->finish();
	&DBINFO::db_user_close();

	print qq~
<div class="zoovytableheader">Active Users</div><br>
<table>
<tr class='zoovysub1header'>
	<td class='zoovysub1header'>KOUNT ID</td>
	<td class='zoovysub1header'>USERNAME</td>
	<td class='zoovysub1header'>PRT</td>
	<td class='zoovysub1header'>PROVISIONED</td>
	<td class='zoovysub1header'>STATUS</td>
	<td class='zoovysub1header'>PKG</td>
	<td class='zoovysub1header'>PRIMARY DOMAIN</td>
	<td class='zoovysub1header'>CONTACT NAME</td>
	<td class='zoovysub1header'>PHONE</td>
	<td class='zoovysub1header'>ADDRESS</td>
	<td class='zoovysub1header'>TXN 30 DAY</td>
</tr>
$users
</table>
~;
	}


if ($VERB eq 'BUYCOM-UPLOADBATCH') {
	die();		## does not appear to be used.
#	require ZCSV;
#	require ZCSV::PRODUCT;
#	require LUSER;
#	my $fh = $q->upload('BATCHFILE');
#	my ($USERNAME) = $q->param('ZOOVYUSER');
#	my $BUFFER = '';
#	while (<$fh>) { $BUFFER .= $_; }
#
#	my ($LU) = LUSER->new($USERNAME,'SUPPORT');
#	my ($fieldref,$lineref,$optionsref) = &ZCSV::readHeaders($BUFFER,header=>1,ALLOW_CRLF=>0,SEP_CHAR=>',');
#	$optionsref->{'NONDESTRUCTIVE'}++;
#	$optionsref->{'PRODNAVCAT'} = 0;
#	&ZCSV::logImport($USERNAME,'*BUYCOM',$fieldref,$lineref,$optionsref);
#	&ZCSV::PRODUCT::parseproduct($LU,$fieldref,$lineref,$optionsref);	
	$VERB = '';
	}


#if ($VERB eq 'BING-VERIFY') {
#	my $ERROR = undef;
#	my ($DOMAIN) = $q->param('BING_DOMAIN');
#	my ($ORDERID) = $q->param('BING_ORDERID');
#	my ($FAP) = $q->param('BING_FLAG-AS-PAID');
#
#	if ((not defined $ERROR) && ($DOMAIN eq '')) { $ERROR = "Domain not specified"; }
#	if ((not defined $ERROR) && ($ORDERID eq '')) { $ERROR = "OrderId not specified"; }
#
#		
#	## This allows them to pass a domain.
#	my $USERNAME = '';
#	if (not defined $ERROR) {
#		require DOMAIN::TOOLS;
#		($USERNAME) = &DOMAIN::TOOLS::domain_to_user($DOMAIN);
#		if ($USERNAME eq '') {
#			$ERROR = "Could not find Zoovy account for domain $DOMAIN";
#			}
#		else {
#			print "FOUND ZOOVY USER: $USERNAME<br>\n";
#			}
#		}
#
#
#	my ($o) = undef;
#	if (not defined $ERROR) {
#		require ORDER;
#		($o,my $err) = ORDER->new($USERNAME,$ORDERID);
#		if ($err) { 
#			$ERROR = "ORDER-ERROR!$err"; 
#			}
#		else {
#			print "FOUND ORDER: $ORDERID<br>\n";
#			}
#		}
#	
#	if (not defined $ERROR) {
#		if (int($o->{'data'}->{'mkt'}) & 32768) {
#			require ZTOOLKIT;
#			## it's good
#			}
#		else {
#			$ERROR = "Zoovy does not believe BING is a party to this transaction";
#			}
#		}
#
#	if (not defined $ERROR) {
#		require PLUGIN::BING;
#		my ($url) = PLUGIN::BING::pixel_for_order($o);
#		print "SUCCESS PIXEL URL: $url\n";
#		}
#
#	if ((not defined $ERROR) && ($FAP)) {
#		$o->set_payment_status('076','bing-did-it',["Bing flagged this order as paid as part of their testing."]);
#		$o->save();
#		}
#	
#	if ($ERROR) {
#		print "FATAL ERROR: $ERROR\n";
#		}
#	else {
#			print "<hr>";
#			print "<b>Order Event Detail</b><br><table>";
#			foreach my $e (@{$O2->history()}) {
#				print "<tr><td valign=top nowrap>".&ZTOOLKIT::pretty_date($e->{'ts'},1)."</td><td>$e->{'content'}</td></tr>";
#				# print "EVENT: ".&ZTOOLKIT::buildparams($e)."<br>\n";
#				}
#			print "</table>";
#
#		}
#
#	}
#

if ($VERB eq 'RM-VERIFY') {
	my ($USERNAME) = $q->param('RM_USER');
		
	## This allows them to pass a domain.
	if ($USERNAME =~ /\./) {
		require DOMAIN::TOOLS;
		($USERNAME) = &DOMAIN::TOOLS::domain_to_user($USERNAME);
		}

	if ($USERNAME ne '') {
		my @PROFILES = @{&ZOOVY::fetchprofiles($USERNAME)};
		foreach my $PROFILE (@PROFILES) {
			print "<hr><b>PROFILE: $PROFILE</b><br>";
			my ($val) = &ZOOVY::fetchmerchantns_attrib($USERNAME,$PROFILE,'razormo:chkoutjs');
			if ((not defined $val) || ($val eq '')) {
				print "<i>RazorMouth Code Not Set</i><br>";
				}
			else {
				print "<b>RazorMouth HTML Code:</b><br><pre>".&ZOOVY::incode($val)."</pre>";
				}
			}
		}
	else {
		print "User/Domain not found: $USERNAME<br>\n";
		}
	}




#if ($VERB eq 'UPIC-LAST60') {
#	require ZWEBSITE;
#	require Net::FTP;
#	require ORDER::BATCH;
#	require ORDER;
#
#	my ($USERNAME) = $q->param('UPIC_USERNAME');
#	my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,0);
##	my $TMPFILE = "/tmp/$USERNAME.tsv";
##	open F, ">$TMPFILE\n";
#	my ($ts) = &ORDER::BATCH::report($USERNAME,'CREATED_GMT'=>time()-(86400*60));
#	print "<pre>";
#	print "ORDER\tSHIP-DATE\tDST-COUNTRY\tSUBTOTAL\tCREATED\tCARRIER\tTRACKING\tDECLAREDVAL\n";
#	foreach my $oidref (@{$ts}) {
#		my $oid = $oidref->{'ORDERID'};
##		print STDERR "OID: $oid\n";
#		next if ($oid eq '');
#		my ($o) = ORDER->new($USERNAME,$oid);
#		my $total = sprintf("%.2f",$o->get_attrib('order_subtotal'));
#
#		foreach my $trk (@{$o->tracking()}) {
#			# print Dumper($trk);
#			$trk->{'dv'} = sprintf("%.2f",$trk->{'dv'});
#			my $shipdate = POSIX::strftime("%Y%m%d%H%M%S",localtime($trk->{'created'}));
#			my $country = $o->get_attrib('ship_country');
#			if ($country eq '') { $country = 'USA'; }
#		
#			print "$oid\t$shipdate\t$country\t$total\t$trk->{'carrier'}\t$trk->{'track'}\t$trk->{'dv'}\n";
#			}	
#		}
#	print "</pre>";
#
##	my $ftpuser = 'zoovy';
##	my $ftppass = 'z0ovY!nc';
##	my $ftphost = 'delta.u-pic.com';
##	my $ftp = Net::FTP->new($ftphost, Debug => 1);
##	if (not defined $ftp) {
##		my $rc = $ftp->login($ftpuser,$ftppass);
##		print "RC: $rc\n";
##
##		my $FILENAME = strftime("shiplog-%Y%m%d_$USERNAME.csv",localtime());
##
##		# $ftp->pasv();
##		$ftp->binary();
##		$ftp->put($TMPFILE,$FILENAME);
##		$ftp->quit;
##		print "FTP File: $FILENAME has been created on FTP SITE host:$ftphost u:$ftpuser p:$ftppass\n";
##		}
##	else {
##		print "FTP Login error!\n";
##		}
#	}


if ($VERB eq 'UPIC-PACKAGES') {

#+-------------+------------------+------+-----+---------+----------------+
#| Field       | Type             | Null | Key | Default | Extra          |
#+-------------+------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| MID         | int(10) unsigned | NO   | MUL | 0       |                |
#| USERNAME    | varchar(20)      | NO   |     | NULL    |                |
#| ORDERID     | varchar(12)      | NO   |     | NULL    |                |
#| CARRIER     | varchar(4)       | NO   |     | NULL    |                |
#| TRACK       | varchar(20)      | NO   |     | NULL    |                |
#| DVALUE      | decimal(6,2)     | NO   |     | 0.00    |                |
#| CREATED_GMT | int(10) unsigned | NO   |     | 0       |                |
#| VOID_GMT    | int(10) unsigned | NO   |     | 0       |                |
#+-------------+------------------+------+-----+---------+
	my ($USERNAME) = $q->param('UPIC_USERNAME');
	my ($odbh) = &DBINFO::db_user_connect($USERNAME);
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	my $pstmt = "select ORDERID,CARRIER,TRACK,DVALUE,CREATED_GMT,VOID_GMT from UPIC where MID=$MID";
	my $sth = $odbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my ($ORDERID,$CARRIER,$TRACK,$DVALUE,$C_GMT,$V_GMT) = $sth->fetchrow() ) {
		}
	if ($c eq '') {
		print "<i>No Transactions</i>";
		}
	else {
		print qq~
<table>
	<tr>
	<td>ORDERID</td>
	<td>CARERIER</td>
	<td>TRACK</td>
	<td>DVALUE</td>
	<td>CREATED</td>
	<td>VOID</td>
	</tr>
	$c
</table>~;
		}
	$sth->finish();
	&DBINFO::db_user_close();
	}


if ($VERB eq 'SKEY') {
	my $username = $q->param('skey_username');
	my ($MID) = &ZOOVY::resolve_mid($username);
	if ($MID==-1) { print "WARN: No user: $username found<br>\n"; }
	my ($partnerid) = $SKEYS{$PARTNERUSER};
	if ($partnerid eq '') { print "WARN: No code found for partner $PARTNERUSER\n"; }
	use ZTOOLKIT::SECUREKEY;
	my ($key) = &ZTOOLKIT::SECUREKEY::gen_key($username,$partnerid);

	if ($MID>0) {
		require LUSER;
		my ($LU) = LUSER->new($username);
	   my $email = $LU->get('zoovy:email');
	
   	my $phone = $LU->get('zoovy:phone');
	   my $address = $LU->get('zoovy:address1');
	   my $city = $LU->get('zoovy:city');
	   my $state = $LU->get('zoovy:state');
	   my $zip = $LU->get('zoovy:zip');
	   my $country = $LU->get('zoovy:country');
		
		print "Contact: ".$LU->get('zoovy:firstname').' '.$LU->get('zoovy:lastname')."<br>\n";
		print "Phone: $phone<br>\n";
		print "Email: $email<br>\n";
		print "Address: $address<br>\n";
		print "City: $city<br>\n";
		print "State: $state<br>\n";
		print "Zip: $zip<br>\n";
		print "Country: $country<br>\n";
		print "SECURE KEY: \"$key\"<br>\n";
		}
	}
elsif ($VERB eq 'TXN') {
	my $dbh = &DBINFO::db_zoovy_connect();
	my $start = int($q->param('txn_date_start')).'000000';
	my $end = int($q->param('txn_date_end')).'000000';

#mysql> desc BS_TRANSACTIONS;
#+-----------------+--------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| Field           | Type                                                                                 | Null | Key | Default             | Extra          |
#+-----------------+--------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#| ID              | int(11)                                                                              | NO   | PRI | NULL                | auto_increment |
#| USERNAME        | varchar(20)                                                                          | NO   |     | NULL                |                |
#| MID             | int(11)                                                                              | NO   | MUL | 0                   |                |
#| AMOUNT          | decimal(10,2)                                                                        | NO   |     | 0.00                |                |
#| CREATED         | datetime                                                                             | NO   |     | 0000-00-00 00:00:00 |                |
#| MESSAGE         | varchar(80)                                                                          | NO   |     | NULL                |                |
#| BILLGROUP       | enum('SETUP','MONTHLY','SUCCESS','DESIGN','SERVICES','PARTNER','PAYMENT','OTHER','') | YES  |     | NULL                |                |
#| BILLCLASS       | enum('BILL','CREDIT','TBD','HOLD','WAIVED','')                                       | NO   |     | NULL                |                |
#| PAID_GMT        | int(10) unsigned                                                                     | NO   | MUL | 0                   |                |
#| PARTNER         | enum('','EBATES','DNS')                                                              | NO   |     | NULL                |                |
#| PARTNER_TXN     | int(10) unsigned                                                                     | YES  |     | NULL                |                |
#| BUNDLE          | varchar(8)                                                                           | NO   |     | NULL                |                |
#| SETTLED         | int(11)                                                                              | NO   |     | 0                   |                |
#| SETTLEMENT      | int(11)                                                                              | NO   | MUL | 0                   |                |
#| LOCK_ID         | int(11)                                                                              | NO   |     | 0                   |                |
#| NO_COMMISSION   | tinyint(4)                                                                           | NO   |     | 0                   |                |
#| COMMISSION_RATE | decimal(4,2)                                                                         | NO   |     | 0.00                |                |
#| DISCOUNT_RATE   | tinyint(3) unsigned                                                                  | NO   |     | 0                   |                |
#| SALESPERSON     | varchar(10)                                                                          | NO   |     | NULL                |                |
#+-----------------+--------------------------------------------------------------------------------------+------+-----+---------------------+----------------+
#19 rows in set (0.01 sec)


	my $pstmt = "select ID,USERNAME,AMOUNT,date_format(CREATED,'%Y/%m/%d'),MESSAGE,PARTNER_TXN from BS_TRANSACTIONS where PARTNER='ebates' and CREATED>=$start and CREATED<$end order by CREATED";
	# print $pstmt;
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	print "Transaction report between: $start and $end<br>";
	print "<table>";
	print qq~
<tr>
	<td><div class="zoovytableheader">AMOUNT</td>
	<td><div class="zoovytableheader">USER</td>
	<td><div class="zoovytableheader">CREATED</td>
	<td><div class="zoovytableheader">MESSAGE</td>
	<td><div class="zoovytableheader">PARTNER-TXN</td>
	<td><div class="zoovytableheader">ZOOVY-TXN</td>
</tr>
~;
	my $total = 0; my $count = 0;
	while ( my ($id,$user,$amount,$created,$message,$ptxn) = $sth->fetchrow() ) {
		print "<tr>";
		print "<td>$amount</td>\n";
		print "<td>$user</td>\n";
		print "<td>$created</td>\n";
		print "<td>$message</td>\n";
		print "<td>$ptxn</td>\n";
		print "<td>$id</td>\n";
		print "</tr>";
		$total += $amount;
		$count++;
		}
	$sth->finish();
	&DBINFO::db_zoovy_close();
	
	print "<tr><td colspan=2 align=right>Total \$:</td><td>$total</td><td align=right>Total Txn:</td><td>$count</td></tr>";
	print "</table>";
	print "--end--\n";
	}


print "</form>";
print "</td></tr></table>";
