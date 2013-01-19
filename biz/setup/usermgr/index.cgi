#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use ZACCOUNT;
use DBINFO;
use strict;
use PLUGIN::FUSEMAIL;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_ADMIN');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSER,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

# $LU->log('PRODEDIT.NUKEIMG',"[PID:$PID] Nuking image $img ".$prodref->{'zoovy:prod_image'.$img},'INFO');

my @TABS = ();
my @MSGS = ();
my @BC = ();

push @BC, { name=>'Setup', link=>'/biz/setup/index.cgi', target=>'_top' };
push @BC, { name=>'User Manager', link=>'/biz/setup/usermgr/index.cgi' };


&ZOOVY::init();
&GTOOLS::init();
my $zdbh = &DBINFO::db_zoovy_connect();
if ($USERNAME eq '') { exit; }
$GTOOLS::TAG{'<!-- MERCHANT -->'} = $USERNAME;
my $VERB = $ZOOVY::cgiv->{'ACTION'};
if ($VERB eq '') { $VERB = $ZOOVY::cgiv->{'VERB'}; }

if ($FLAGS =~ /,BASIC,/) {
	if ($FLAGS !~ /,ZM,/) {
		## triple check we don't have a ,ZM, flag now.
		$FLAGS .= ",".&ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
		}
 	}
print STDERR "FLAGS: $FLAGS\n";

my $template_file = 'index.shtml';
my @ERRORS = ();




if ($VERB eq 'REGISTER-DEVICE') {

#mysql> desc ZUSER_DEVICES;
#+---------------+------------------+------+-----+---------------------+----------------+
#| Field         | Type             | Null | Key | Default             | Extra          |
#+---------------+------------------+------+-----+---------------------+----------------+
#| ID            | int(10) unsigned | NO   | PRI | NULL                | auto_increment |
#| USERNAME      | varchar(20)      | NO   |     | NULL                |                |
#| MID           | int(10) unsigned | NO   | MUL | 0                   |                |
#| HWADDR        | varchar(16)      | NO   |     | NULL                |                |
#| NAME          | varchar(25)      | NO   |     | NULL                |                |
#| TOKEN         | varchar(128)     | NO   |     | NULL                |                |
#| GEO     | varchar(3)       | NO   |     | NULL                |                |
#| REGISTERED_TS | timestamp        | NO   |     | 0000-00-00 00:00:00 |                |
#+---------------+------------------+------+-----+---------------------+----------------+
#8 rows in set (0.00 sec)

	my $hwaddr = uc($ZOOVY::cgiv->{'hwaddr'});
	$hwaddr =~ s/[^0-9A-Z]+//gs;	# take 01:23:45:67:89:ab to 0123456789ab
	my $name = $ZOOVY::cgiv->{'name'};
	$name =~ s/[^a-zA-Z0-9\.\s]+//gs;
	my $geo = uc($ZOOVY::cgiv->{'geo'});

	my $token = Data::GUID->new()->as_string();

	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pstmt = "delete from ZUSER_DEVICES where MID=".int($MID)." and HWADDR=".$zdbh->quote($hwaddr);
	$zdbh->do($pstmt);

	my $pstmt = &DBINFO::insert($zdbh,'ZUSER_DEVICES',{
		USERNAME=>$USERNAME,MID=>$MID,
		HWADDR=>$hwaddr,NAME=>$name,
		GEO=>$geo,
		TOKEN=>$token,
		'*REGISTERED_TS'=>'now()',
		},insert=>1,sql=>1);
	print STDERR "$pstmt\n";
	$zdbh->do($pstmt);

	&DBINFO::db_zoovy_close();
	push @MSGS, "SUCCESS|Device $hwaddr token was created, please add token into device to complete process.";

	$template_file = 'register-device.shtml';
	$VERB = 'VIEW-DEVICE';
	}

if ($VERB eq 'ADD-DEVICE') {
	$GTOOLS::TAG{'<!-- HWADDR -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'hwaddr'});
	$GTOOLS::TAG{'<!-- NAME -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'name'});
	$GTOOLS::TAG{'<!-- GEO -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'geo'});
	$template_file = 'add-device.shtml';
	}

if ($VERB eq 'DELETE-DEVICE') {
	my $hwaddr = uc($ZOOVY::cgiv->{'hwaddr'});
	$hwaddr =~ s/[^0-9A-Z]+//gs;	# take 01:23:45:67:89:ab to 0123456789ab
	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pstmt = "delete from ZUSER_DEVICES where MID=".int($MID)." and HWADDR=".$zdbh->quote($hwaddr);
	$zdbh->do($pstmt);
	$VERB = '';
	push @MSGS, "SUCCESS|Device $hwaddr removed";
	}

if ($VERB eq 'VIEW-DEVICE') {
	my $hwaddr = uc($ZOOVY::cgiv->{'hwaddr'});
	$hwaddr =~ s/[^0-9A-Z]+//gs;	# take 01:23:45:67:89:ab to 0123456789ab

	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pstmt = "select * from ZUSER_DEVICES where MID=".int($MID)." and HWADDR=".$zdbh->quote($hwaddr);
	my ($hashref) = $zdbh->selectrow_hashref($pstmt);
	&DBINFO::db_zoovy_close();

	$GTOOLS::TAG{'<!-- HWADDR -->'} = $hashref->{'HWADDR'};
	$GTOOLS::TAG{'<!-- GEO -->'} = $hashref->{'GEO'};
	$GTOOLS::TAG{'<!-- NAME -->'} = $hashref->{'NAME'};
	$GTOOLS::TAG{'<!-- TOKEN -->'} = $hashref->{'TOKEN'};

	require ZTOOLKIT::BARCODE;
	$GTOOLS::TAG{'<!-- BARCODE -->'} = sprintf("<img src=\"%s\">",ZTOOLKIT::BARCODE::code128_url($hashref->{'TOKEN'}));
	# $GTOOLS::TAG{'<!-- BARCODE -->'} = qq~<img src="https://www.barcodesinc.com/generator/image.php?code=$hashref->{'TOKEN'}&style=197&type=C128B&width=600&height=50&xres=1&font=3">~;
	
	$template_file = 'view-device.shtml';
	}


##
##
##

if ($VERB eq 'NUKE') {
	$template_file = 'nukewarn.shtml';
	$GTOOLS::TAG{'<!-- UID -->'} = $ZOOVY::cgiv->{'UID'};
	$GTOOLS::TAG{'<!-- LUSER -->'} = $ZOOVY::cgiv->{'LUSER'};
	}

if ($VERB eq 'NUKECONFIRM') {	
	my $UID = int($ZOOVY::cgiv->{'UID'});
	my $pstmt = "select LUSER from ZUSER_LOGIN where MID=$MID and UID=$UID limit 0,1";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my ($LUSER) = $sth->fetchrow();
	$sth->finish();
	$LU->log('SETUP.USERMGR',"CONFIRM_DELETE on $LUSER UID: $UID",'INFO');

	if ($LUSER ne 'admin') {
		&PLUGIN::FUSEMAIL::account_terminate($USERNAME,$LUSER);
		}

	$pstmt = "delete from ZUSER_LOGIN where MID=$MID and UID=$UID limit 1";
	print STDERR $pstmt."\n";
	$zdbh->do($pstmt);
	$VERB = '';
	}



if (($LUSER eq 'ADMIN') || ($LUSER eq 'SUPPORT')) {
	if ($VERB eq 'CHANGE-ADMIN-ZOOVYMAIL-PASS') {
		require PLUGIN::FUSEMAIL;
		&PLUGIN::FUSEMAIL::resetpassword("admin\@$USERNAME.zoovy.com",$ZOOVY::cgiv->{'FUSEMAIL-PASSWORD'});
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<div class='success'>Successfully updated password</div>";
		$VERB = 'ADMINEDIT';
		}
	}

if ($VERB eq 'ADMINEDIT') {
	if (($LUSER eq 'ADMIN') || ($LUSER eq 'SUPPORT')) {
		$template_file = 'adminedit.shtml';
		}
	else {
		$GTOOLS::TAG{'<!-- LUSER -->'} = $LUSER;
		$template_file = 'admindeny.shtml';
		}
	}


my $UREF = {};
if ($VERB eq 'SAVE') {
	my $LUSER = lc($ZOOVY::cgiv->{'username'});
	if ($LUSER eq '') { push @ERRORS, 'Username is blank!'; }
	if ($LUSER =~ /^support/) { push @ERRORS, 'Usernames containing the word "support" are not valid, please choose a different name.'; }
	if ($LUSER =~ /^admin$/) { push @ERRORS, 'Username "admin" is not valid, please choose a different name.'; }
	if ($LUSER =~ /^zoovy/) { push @ERRORS, 'Usernames containing the word "zoovy" are not valid, please choose a different name.'; }
	if (($UREF->{'CREATED_GMT'}>0) && (length($LUSER)<3)) { push @ERRORS, 'Usernames must have at least 3 characters'; }

	if ($LUSER =~ /[^\w]/) { push @ERRORS, 'Username contains invalid characters (allowed: A-Z 0-9)'; }
	if ($LUSER =~ /^[0-9]+/) { push @ERRORS, 'Username may not start with a number'; }
	if ($LUSER eq 'grant') { push @ERRORS, 'Username "grant" conflicts with SQL reserved word.'; }
	$UREF->{'LUSER'} = $LUSER;

	$LU->log('SETUP.USERMGR',"ACTION: SAVE SUB-USER: $LUSER",'INFO');

	my $PASSWORD = $ZOOVY::cgiv->{'password'};
	$UREF->{'PASSWORD'} = $PASSWORD;
	$UREF->{'*PASSWORD_CHANGED'} = 'now()';

	my $qtPHONE = $zdbh->quote($ZOOVY::cgiv->{'phone'});
	$UREF->{'PHONE'} = $ZOOVY::cgiv->{'phone'};
	my $qtTITLE = $zdbh->quote($ZOOVY::cgiv->{'title'});
	$UREF->{'JOBTITLE'} = $ZOOVY::cgiv->{'title'};
	my $qtFULLNAME = $zdbh->quote($ZOOVY::cgiv->{'fullname'});
	$UREF->{'FULLNAME'} = $ZOOVY::cgiv->{'fullname'};
	my $qtEMAIL = $zdbh->quote($ZOOVY::cgiv->{'email'});
	$UREF->{'EMAIL'} = $ZOOVY::cgiv->{'email'};

	$UREF->{'IS_ADMIN'} = "N"; if ($ZOOVY::cgiv->{'IS_ADMIN'}) { $UREF->{'IS_ADMIN'} = "Y"; }
	$UREF->{'ALLOW_FORUMS'} = "N"; if ($ZOOVY::cgiv->{'ALLOW_FORUMS'}) { $UREF->{'ALLOW_FORUMS'} = "Y"; }
	$UREF->{'IS_CUSTOMERSERVICE'} = "N"; if ($ZOOVY::cgiv->{'IS_CUSTOMERSERVICE'}) { $UREF->{'IS_CUSTOMERSERVICE'} = "Y"; }
	$UREF->{'IS_BILLING'} = "N"; if ($ZOOVY::cgiv->{'IS_BILLING'}) { $UREF->{'IS_BILLING'} = "Y"; }

	my $expires = 0;
	$UREF->{'EXPIRES_GMT'} = 0;
	if ($ZOOVY::cgiv->{'expires'} ne '') {
		require Date::Parse;
		$expires = Date::Parse::str2time($ZOOVY::cgiv->{'expires'});
		if ($expires eq '') { push @ERRORS, "Expires data was not valid try MM/DD/YY format"; }
		$UREF->{'EXPIRES_GMT'} = $expires;
		}
	
	
	my $i = 0;
	$UREF->{'FLAG_SETUP'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'setup_'.$i}) { $UREF->{'FLAG_SETUP'} += $i; } $i *= 2; }
	$UREF->{'FLAG_PRODUCTS'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'product_'.$i}) { $UREF->{'FLAG_PRODUCTS'} += $i; } $i *= 2; }
	$UREF->{'FLAG_ORDERS'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'order_'.$i}) { $UREF->{'FLAG_ORDERS'} += $i } $i *= 2; }
	$UREF->{'FLAG_MANAGE'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'manage_'.$i}) { $UREF->{'FLAG_MANAGE'} += $i; } $i *= 2; }
	$UREF->{'FLAG_ZOM'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'zom_'.$i}) { $UREF->{'FLAG_ZOM'} += $i; } $i *= 2; }
	$UREF->{'FLAG_CRM'} = 0; $i = 1; while ($i<16384) { if ($ZOOVY::cgiv->{'crm_'.$i}) { $UREF->{'FLAG_CRM'} += $i; } $i *= 2; }

	if (not defined $UREF->{'HAS_EMAIL'}) {
		$UREF->{'HAS_EMAIL'} = 'N';
		}

	if (scalar(@ERRORS)>0) {
		}
	elsif (not $LU->is_level(5)) {
		$UREF->{'HAS_EMAIL'} = 'N';
		}
	elsif ($FLAGS =~ /,ZM,/) {
		if ($ZOOVY::cgiv->{'ADD-ZOOVYMAIL'} eq 'on') {
			## they want us to add ZOOVYMAIL
			$GTOOLS::TAG{'<!-- WARNING -->'} = "<font color='error'>Submitted email account creation request. (Please wait 5-10 minutes)</font>";
			$LU->log('SETUP.USERMGR',"Requested Fusemail account for $LUSER",'INFO');
			my ($success,$detail) = &PLUGIN::FUSEMAIL::account_order($USERNAME,$LUSER);
			if ($success!=1) {
				push @ERRORS, "Fusemail error:$detail";
				}
			$UREF->{'HAS_EMAIL'} = 'WAIT';
			}
		else {
			my $ZEMAIL = "$UREF->{'LUSER'}\@$USERNAME.zoovy.com";
			my ($pass) = &PLUGIN::FUSEMAIL::getpassword($ZEMAIL);
			if ($UREF->{'HAS_EMAIL'} eq 'ERR') {
				# hmm..
				}
			elsif ($UREF->{'HAS_EMAIL'} eq 'WAIT') {
				if ($pass ne '') { $UREF->{'HAS_EMAIL'} = 'Y'; }
				}
			else {
				$UREF->{'HAS_EMAIL'} = (defined $pass)?'Y':'N';
				}
			}
		}

	if (scalar(@ERRORS)==0) {
		my $pstmt = '';
		if ((not defined $ZOOVY::cgiv->{'UID'}) || ($ZOOVY::cgiv->{'UID'} eq '') || ($ZOOVY::cgiv->{'UID'} eq '0')) {
			$UREF->{'CREATED_GMT'} = $^T;
			$UREF->{'MID'} = $MID;
			$UREF->{'USERNAME'} = $USERNAME;
			$UREF->{'LUSER'} = $LUSER;

			$pstmt = &DBINFO::insert($zdbh,'ZUSER_LOGIN',$UREF,debug=>2);
			}
		else {
			$pstmt = "update ZUSER_LOGIN set FULLNAME=$qtFULLNAME,JOBTITLE=$qtTITLE,EMAIL=$qtEMAIL,PHONE=$qtPHONE,";

			$pstmt .= "IS_CUSTOMERSERVICE='$UREF->{'IS_CUSTOMERSERVICE'}',";
			$pstmt .= "IS_ADMIN='$UREF->{'IS_ADMIN'}',";
			$pstmt .= "IS_BILLING='$UREF->{'IS_BILLING'}',";
			my ($wms_device_pin) = sprintf("%s",$ZOOVY::cgiv->{'wms_device_pin'});
			$wms_device_pin =~ s/[^A-Z0-9]//gs;
			if ($wms_device_pin eq '') { $wms_device_pin = undef; }
			if (defined $wms_device_pin) {
				## we should check for duplicate pins here, but i don't have time right now.
				}

			$pstmt .= "WMS_DEVICE_PIN=".$zdbh->quote($wms_device_pin).',';

			$pstmt .= "EXPIRES_GMT=$UREF->{'EXPIRES_GMT'},";
			if ($PASSWORD ne '') { $pstmt .= "PASSWORD=".$zdbh->quote($UREF->{'PASSWORD'}).","; }
			$pstmt .= "FLAG_SETUP=$UREF->{'FLAG_SETUP'},";
			$pstmt .= "FLAG_PRODUCTS=$UREF->{'FLAG_PRODUCTS'},";
			$pstmt .= "FLAG_ORDERS=$UREF->{'FLAG_ORDERS'},";
			$pstmt .= "FLAG_MANAGE=$UREF->{'FLAG_MANAGE'},";
			$pstmt .= "FLAG_ZOM=$UREF->{'FLAG_ZOM'},";
			$pstmt .= "FLAG_CRM=$UREF->{'FLAG_CRM'},";
			
			$pstmt .= "ALLOW_FORUMS='$UREF->{'ALLOW_FORUMS'}',";
			$pstmt .= "HAS_EMAIL='$UREF->{'HAS_EMAIL'}'";
			$pstmt .= " where MID=$MID and UID=".$zdbh->quote(int($ZOOVY::cgiv->{'UID'}));
			}
		print STDERR $pstmt."\n";
		$zdbh->do($pstmt);

		## need to remove entry from COOKIE_CACHE so permissions get changed immediately
		my $pstmt = "delete from COOKIE_CACHE where mid = ".$zdbh->quote($MID). " /* $USERNAME */ ".
						"and LUSER = ".$zdbh->quote($LUSER);
		#print STDERR $pstmt."\n";
		$zdbh->do($pstmt);

		## note: we need to provision the fusemail account *AFTER* we add the ZUSER_LOGIN
		if ($UREF->{'HAS_EMAIL'} eq 'Y')  {
			my $EMAIL = "$UREF->{'LUSER'}\@$USERNAME.zoovy.com";
			my ($pass) = &PLUGIN::FUSEMAIL::getpassword($EMAIL);
			if (not defined $pass) { 
				}
			elsif ($ZOOVY::cgiv->{'FUSEMAIL-PASSWORD'} ne '') {
				# riascrazy965
				require PLUGIN::FUSEMAIL;
				require Digest::MD5;
				my $digest = Digest::MD5::md5_hex($ZOOVY::cgiv->{'FUSEMAIL-PASSWORD'});
				&PLUGIN::FUSEMAIL::resetpassword($EMAIL,$ZOOVY::cgiv->{'FUSEMAIL-PASSWORD'});
				$LU->log("FUSEMAIL.PASSWORD","Reset $EMAIL to digest: $digest");
				}
			}


		$VERB = '';
		}
	else {
		$VERB = 'ADD-USER';
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>The following errors were encountered:<br>".join('<li>',@ERRORS)."</font><br>";
		}
	}





if ($VERB eq 'ADD-USER' || $VERB eq 'EDIT-USER') {
	$LU->log('SETUP.USERMGR',"ACTION: $VERB UID #".int($ZOOVY::cgiv->{'UID'}),'INFO');

	$GTOOLS::TAG{'<!-- LUSER_EDIT -->'} = qq~<input type="textbox" name="username" maxlength="10" size="10" value="">~;
	if ($VERB eq 'EDIT-USER') {		
		my $pstmt = "select * from ZUSER_LOGIN where MID=$MID and UID=".int($ZOOVY::cgiv->{'UID'});
		my $sth = $zdbh->prepare($pstmt);
		$sth->execute();
		($UREF) = $sth->fetchrow_hashref();
		$sth->finish();
		$GTOOLS::TAG{'<!-- LUSER_EDIT -->'} = qq~<input type="hidden" name="username" value="$UREF->{'LUSER'}">$UREF->{'LUSER'}~;
		}

	if (not $LU->is_level(5)) {
		$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2><i>Email hosting not available at this level.</i></tr></tr>~;
		}
	elsif ($FLAGS =~ /,ZM,/) {

		if ($ZOOVY::cgiv->{'ADD-ZOOVYMAIL'} eq 'on') {
			$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2>Email Account is being provisioned.<br></td></tr>~;
			}
		elsif ($UREF->{'HAS_EMAIL'} eq 'WAIT') {
			$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2><i>Email account provision request issued (please check back in 5-10 minutes from opening.)</td></tr>~;
			}


		if ($VERB eq 'ADD-USER') {
			$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2><input type="checkbox" checked name="ADD-ZOOVYMAIL"> Create individual ZoovyMail Inbox for this User (Recommended)<br></td></tr>~;
			}
		elsif ($VERB eq 'EDIT-USER') {
			my $EMAIL = "$UREF->{'LUSER'}\@$USERNAME.zoovy.com";
			my ($pass) = &PLUGIN::FUSEMAIL::getpassword($EMAIL);
			print STDERR "trying to edit ZoovyMail for: ".$UREF->{'LUSER'}." with password: ".$pass."\n";
			if ($UREF->{'HAS_EMAIL'} eq 'ERR') {
				## error..
				$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2>Internal FuseMail Error<br></td></tr>~;
				}
			elsif ((not defined $pass) && ($UREF->{'HAS_EMAIL'} eq 'WAIT')) {
				## no user exists??
				$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2>Email: Waiting for Fusemail to Provision.</td></tr>~;
				}
			elsif ((not defined $pass) && ($UREF->{'HAS_EMAIL'} eq 'N')) {
				## no user exists, none has been created.
				$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2><input type="checkbox" name="ADD-ZOOVYMAIL"> Create individual ZoovyMail Inbox for this User<br></td></tr>~;
				}
			elsif ((not defined $pass) && ($UREF->{'HAS_EMAIL'} eq 'Y')) {
				## no user exists??
				$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2>Email: Could not retrieve account info from fusemail. (please wait 5-10 min. for new accounts)<br></td></tr>~;
				}
			else {
				## no-encrypted password
				my $URL = &PLUGIN::FUSEMAIL::loginurl($EMAIL);
				$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~
	<tr>
		<td colspan=2><a target="fusemail" href="$URL">ZoovyMail Login</a><br>
		Change ZoovyMail Password: <input type="password" name="FUSEMAIL-PASSWORD"><br>
	</td>
	</tr>~;
				}

			#else {
			#	## decrypt password -- why show passwords ??
			#	$GTOOLS::TAG{'<!-- ZOOVYMAIL -->'} = qq~<tr><td colspan=2><input type="hidden" name="ZOOVYMAIL" value="on"> ZoovyMail Login: $UREF->{'LUSER'}\@$USERNAME.zoovy.com Pass: $pass<br></td></tr>~;
			#	}
			}
		}

	$GTOOLS::TAG{'<!-- WMS_DEVICE_PIN -->'} = $UREF->{'WMS_DEVICE_PIN'};
	$GTOOLS::TAG{'<!-- UID -->'} = $UREF->{'UID'};
	$GTOOLS::TAG{'<!-- LUSER -->'} = $UREF->{'LUSER'};
	$GTOOLS::TAG{'<!-- PASSWORD -->'} = $UREF->{'PASSWORD'};
	$GTOOLS::TAG{'<!-- PHONE -->'} = $UREF->{'PHONE'};
	$GTOOLS::TAG{'<!-- TITLE -->'} = $UREF->{'JOBTITLE'};
	$GTOOLS::TAG{'<!-- FULLNAME -->'} = $UREF->{'FULLNAME'};
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $UREF->{'EMAIL'};
	$GTOOLS::TAG{'<!-- EXPIRES -->'} = '';
	if ($UREF->{'EXPIRES_GMT'}>0) {
		my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($UREF->{'EXPIRES_GMT'});
		$year = $year % 100; $mon += 1;
		$GTOOLS::TAG{'<!-- EXPIRES -->'} = sprintf("%02d/%02d/%02d",$mon,$mday,$year);
		}
	$GTOOLS::TAG{'<!-- CHK_IS_ADMIN -->'} = ($UREF->{'IS_ADMIN'} eq 'Y')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_ALLOW_FORUMS -->'} = ($UREF->{'ALLOW_FORUMS'} eq 'Y')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_IS_CUSTOMERSERVICE -->'} = ($UREF->{'IS_CUSTOMERSERVICE'} eq 'Y')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_IS_BILLING -->'} = ($UREF->{'IS_BILLING'} eq 'Y')?'checked':'';

	my $i = 1; 
	while ($i<16384) { 
		$GTOOLS::TAG{'<!-- CHK_SETUP_'.$i.' -->'} = (($UREF->{'FLAG_SETUP'} & $i)==$i)?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_PRODUCT_'.$i.' -->'} = (($UREF->{'FLAG_PRODUCTS'} & $i)==$i)?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_ORDER_'.$i.' -->'} = (($UREF->{'FLAG_ORDERS'} & $i)==$i)?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_MANAGE_'.$i.' -->'} = (($UREF->{'FLAG_MANAGE'} & $i)==$i)?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_ZOM_'.$i.' -->'} = (($UREF->{'FLAG_ZOM'} & $i)==$i)?'checked':'';
		$GTOOLS::TAG{'<!-- CHK_CRM_'.$i.' -->'} = (($UREF->{'FLAG_CRM'} & $i)==$i)?'checked':'';
		$i *= 2;
		}

	if ($VERB eq 'EDIT-USER') {
		$GTOOLS::TAG{'<!-- REMOVE_BUTTON -->'} = qq~<td><button form="setupUserFrm" type="submit" onClick="navigateTo('/biz/setup/usermgr/index.cgi?ACTION=NUKE&LUSER=$UREF->{'LUSER'}&UID=$UREF->{'UID'}');">Remove</button></td>~;		
		}
	
	$template_file = 'useredit.shtml';
	}


if ($VERB eq '') {
	$LU->log('SETUP.USERMGR',"Viewed User+Device List/Preferences",'LOG');

	my @ROWS = ();
	my $pstmt = "select * from ZUSER_LOGIN where MID=$MID order by LUSER";
	print STDERR $pstmt."\n";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	push @ROWS, { UID=>0, LUSER=>'ADMIN', FULLNAME=>'Administrator', JOBTITLE=>'Master Account', HAS_EMAIL=>(($FLAGS =~ /,ZM,/)?'Y':'N') };
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		push @ROWS, $hashref; 
		}
	$sth->finish();
	
	my $c = '';
	foreach my $hashref (@ROWS) {
		$c .= "<tr>";	
		if ($hashref->{'UID'}==0) {
			$c .= qq~<td><input type="button" class="button" value=" Edit " onClick="navigateTo('/biz/setup/usermgr/index.cgi?ACTION=ADMINEDIT&UID=$hashref->{'UID'}');"></td>~;
			}
		else {
			$c .= qq~<td><input type="button" class="button" value=" Edit " onClick="navigateTo('/biz/setup/usermgr/index.cgi?ACTION=EDIT-USER&UID=$hashref->{'UID'}');"></td>~;
			}
		$c .= "<td>$USERNAME*$hashref->{'LUSER'}</td>";
		$c .= "<td>$hashref->{'FULLNAME'} / $hashref->{'JOBTITLE'}</td>";
		$c .= "<td>$hashref->{'HAS_EMAIL'}</td>";
		$c .= "</tr>";
		}
	if ($c eq '') { 
		$c = "<tr><td><div class=\"warning\">No users currently exist</div></td></tr>"; 
		}
	else { 
		$c = qq~
	<tr class="zoovytableheader">
		<td><b>Edit</b></td>
		<td><b>Login</b></td>
		<td><b>Name/Title</b></td>
		<td><b>Email</b></td>
	</tr>~.$c; 
		}
	$GTOOLS::TAG{'<!-- CURRENT_USERS -->'} = $c;

	
	$c = '';
	$pstmt = "select HWADDR,NAME,GEO,REGISTERED_TS from ZUSER_DEVICES where MID=$MID order by REGISTERED_TS";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		$c .= "<tr>";
		$c .= "<td><input type='button' onClick=\"navigateTo('/biz/setup/usermgr/index.cgi?VERB=VIEW-DEVICE&hwaddr=$hashref->{'HWADDR'}');\" value='View'></td>";
		$c .= "<td>$hashref->{'HWADDR'}</td>";
		$c .= "<td>$hashref->{'NAME'}</td>";
		$c .= "<td>$hashref->{'GEO'}</td>";
		$c .= "<td>$hashref->{'REGISTERED_TS'}</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	if ($c eq '') {
		$c .= "<tr><td><div class=\"warning\">No mobile devices have been registered.</div></td></tr>";
		}
	else {
		$c = qq~<tr class='zoovytableheader'>
<td></td>
<td>Hw Address</td>
<td>Device Name</td>
<td>Geo/Location</td>
<td>Registered</td>
</tr>
~.$c;
		}
	$GTOOLS::TAG{'<!-- CURRENT_DEVICES -->'} = $c;
	}

if ($FLAGS !~ /,BASIC,/) {
	$template_file = 'deny.shtml';
	}

push @TABS, { name=>'User/Device Manager', link=>'/biz/setup/usermgr/index.cgi?VERB=', 'selected'=>($VERB eq '')?1:0, };

&GTOOLS::output(
	title=>'Setup: User Manager',
	file=>$template_file,
	header=>1,
	help=>'#50292',
	tabs=>\@TABS,
	msgs=>\@MSGS,
	bc=>\@BC,
	);

&DBINFO::db_zoovy_close();
