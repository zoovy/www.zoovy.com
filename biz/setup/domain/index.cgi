#!/usr/bin/perl

use lib '/httpd/modules';
require ZOOVY;
require DOMAIN;
require DOMAIN::TOOLS;
require GTOOLS;
require LUSER;
#require JQUERY::PANELS;
require AJAX::PANELS;
require DOMAIN::QUERY;
require DOMAIN::REGISTER;
require DOMAIN::POOL;
require LISTING::MSGS;
use strict;

my $dbh = &DBINFO::db_zoovy_connect();

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my @BC = [
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Domain Hosting',link=>'http://www.zoovy.com/biz/setup/domain','target'=>'_top', },
      ];
my $help = "#50334";


my @MSGS = ();
#push @MSGS, "WARN|This area is currently offline until 12:30pm PST. Any changes made will be lost.";

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};
if ($VERB eq '') { $VERB = 'CONFIG'; }

print STDERR "VERB: $VERB\n";

if ($FLAGS =~ /,TRIAL,/) {
	$VERB = 'DENY';
   $template_file = "noperm.shtml";
   $GTOOLS::TAG{"<!-- ERROR_MSG -->"} = "Trial accounts don't have permission to use these tools. [$FLAGS]";
	}
#elsif ($FLAGS =~ /,PKG=STARTUP[AB],/) {
#	## STARTUPA/B gets SITE HOST
#	}
#elsif (index($FLAGS, ',SCONLY,')>0) {
#	$template_file = "noperm.shtml"; 
#	$GTOOLS::TAG{"<!-- ERROR_MSG -->"} = "Your account type does not include domain hosting.";
#	$VERB = 'DENY';	
#	}
#elsif (index($FLAGS, ',SITEHOST,') > 0) {
#	## SITEHOST ALSO OPENS UP DOMAIN ACCESS
#	}
#elsif (index($FLAGS, ',WEB,') == -1) {
#	if ($LUSERNAME eq 'SUPPORT') {
#		## support always gets access
#		push @MSGS, "WARN|ZOOVY SUPPORT NOTE: Customer does not have sufficient access (requires WEB bundle)";
#		}
#	else {
#		$template_file = "noperm.shtml"; 
#		push @MSGS, "ERROR|You don't have permission to use these tools. [$FLAGS] (requires WEB bundle)";
#		$VERB = 'DENY';
#		}
#	}


#push @MSGS, "WARN|Domain configuration is currently offline for maintenance";
#$VERB = 'DISABLED';


if ($VERB eq 'NEW-CONFIRMED') {
	my $DOMAINNAME = $ZOOVY::cgiv->{'DOMAINNAME'};
	my $ACTION = $ZOOVY::cgiv->{'ACTION'};
	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};	

	$VERB = 'NEW-CONFIRM';
	if ($PROFILE eq '') {
		## generate a new profile id.
		($PROFILE) = &DOMAIN::suggest_profilename($USERNAME,$DOMAINNAME);
		}

	if ($ACTION eq 'NEW-TRANSFER') {
		if (&DOMAIN::REGISTER::BelongsToRsp($DOMAINNAME)) {
			## already belongs to us
			my ($BILL_ID) = &DOMAIN::REGISTER::verify_billing($USERNAME,$DOMAINNAME);
			my ($D) = DOMAIN->create($USERNAME,$DOMAINNAME,'PROFILE'=>$PROFILE,'REG_TYPE'=>'ZOOVY','REG_STATUS'=>"Billing Record: $BILL_ID");
			push @MSGS, "SUCCESS|Successfully performed simulated transfer for domain:$DOMAINNAME";
			$VERB = 'CONFIG';
			}
		else {
			push @MSGS, "ERROR|We are no longer allowing non-registered domains to be transferred, please use delegate instead";
			}
		}
	elsif ($ACTION eq 'NEW-RESERVATION') {
		($DOMAINNAME) = &DOMAIN::POOL::reserve($USERNAME,$PRT,$PROFILE);
		if ($DOMAINNAME) {
			push @MSGS, "SUCCESS|Reserved domain: $DOMAINNAME";
			$VERB = 'CONFIG';
			}
		else {
			push @MSGS, "ERROR|Could not reserve a domain, unspecified error - please open a support ticket.";
			}
		}
	elsif ($ACTION eq 'NEW-REGISTER') {
		my $lm = LISTING::MSGS->new($USERNAME,logfile=>'domains.log');
		my ($RESULT) = DOMAIN::REGISTER::register($USERNAME,$DOMAINNAME,'*LM'=>$lm,'reg_type'=>'new');
		if (defined $RESULT) {
			my ($D) = DOMAIN->create($USERNAME,$DOMAINNAME,%{$RESULT},'PROFILE'=>$PROFILE);
			my ($BILL_ID) = DOMAIN::REGISTER::verify_billing($USERNAME,$DOMAINNAME);
			$lm->pooshmsg("INFO|DOMAIN:$DOMAINNAME|+billing id: $BILL_ID");
			if ($BILL_ID>0) { 
				push @MSGS, "SUCCESS|Billing ID:$BILL_ID was created"; 
				$VERB = 'CONFIG';
				}
			else {
				push @MSGS, "ISE|Recurring Billing ID could not be created (this domain is not properly linked)";
				}
			}

		foreach my $msg (@{$lm->msgs()}) {
			push @MSGS, $msg;
			}
		}
	elsif ($ACTION eq 'NEW-DELEGATE') {		
		my $lm = LISTING::MSGS->new($USERNAME,logfile=>'domains.log');
		my %RESULT = ();
		$RESULT{'REG_STATUS'} = 'External Registrar';
		$RESULT{'REG_TYPE'} = 'OTHER';
		$RESULT{'PROFILE'} = $PROFILE;

		# push @MSGS, "WARN|PROFILE:$RESULT{'PROFILE'}";

		my ($D) = DOMAIN->create($USERNAME,$DOMAINNAME,%RESULT);

		# use Data::Dumper; push @MSGS, "WARN|".Dumper($D);

		if ($D) {
			push @MSGS, "SUCCESS|Created entry in DOMAINS database (please allow 3-4 hours for changes to be visible)";
			$VERB = 'CONFIG';
			}
		}
	elsif ($ACTION eq 'NEW-SUBDOMAIN') {
		my $lm = LISTING::MSGS->new($USERNAME,logfile=>'domains.log');
		my %RESULT = ();
		$RESULT{'REG_STATUS'} = 'Subdomain';
		$RESULT{'REG_TYPE'} = 'SUBDOMAIN';
		$RESULT{'PROFILE'} = $PROFILE;

		my ($D) = DOMAIN->create($USERNAME,$DOMAINNAME,%RESULT);
		if ($D) {
			push @MSGS, "SUCCESS|Created entry in DOMAINS database (please allow 3-4 hours for changes to be visible)";
			$VERB = 'CONFIG';
			}
 
		}
	else {
		push @MSGS, "ERROR|Unsupported action:$ACTION";
		}

	if ($VERB eq 'CONFIG') {
		my ($nsref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
		$nsref->{'prt:id'} = $PRT;
		$nsref->{'zoovy:site_partition'} = $PRT;
		$nsref->{'this:domain'} = $DOMAINNAME;
		&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$nsref);
		}
	}



if ($VERB eq 'NEW-CONFIRM') {
	my $DOMAINNAME = $ZOOVY::cgiv->{'DOMAINNAME'};
	my $ACTION = $ZOOVY::cgiv->{'ACTION'};
	$GTOOLS::TAG{'<!-- DOMAINNAME -->'} = $DOMAINNAME;
	$GTOOLS::TAG{'<!-- ACTION -->'} = $ACTION;
	$GTOOLS::TAG{'<!-- PRT -->'} =  int($PRT);

	my @ERRORS = ();

	if ($ACTION eq 'NEW-RESERVATION') {
		}
	elsif ($DOMAINNAME eq '') {
		push @ERRORS, "Domain name is required for all types except 'Reserve'";
		}
	elsif ($DOMAINNAME =~ /^www\./) {
		push @ERRORS, "The leading www. is part of the hostname, not the domain name. Please remove the www. and try again.";
		}
	elsif ($DOMAINNAME =~ /^app\./) {
		push @ERRORS, "The leading app. is part of the hostname, not the domain name. Please remove the www. and try again.";
		}
	elsif ($DOMAINNAME =~ /^m\./) {
		push @ERRORS, "The leading m. is part of the hostname, not the domain name. Please remove the www. and try again.";
		}
	elsif ($DOMAINNAME !~ /\./) {
		push @ERRORS, "Domain names must have at least one . in them";
		}
	elsif (length($DOMAINNAME)>50) {
		push @ERRORS, "Domain name may not exceed 50 characters total";
		}
	
	if ($ACTION eq '') {
		push @ERRORS, "Err: Crystal ball is broken, you must select what you're trying to do, sorry but we refuse to guess.";
		}
	elsif (scalar(@ERRORS)>0) {
		}
	elsif ($ACTION eq 'NEW-REGISTER') {
		$GTOOLS::TAG{'<!-- ACTION_PRETTY -->'} = 'New Registration';
		if (not $LU->is_admin()) {
			push @ERRORS, "You must have admin priviledges to access this tool";
			}
		elsif (not DOMAIN::REGISTER::DomainAvailable($DOMAINNAME)) {
			push @ERRORS, "Domain appears to already be registered, please try again.";
			}
		else {
			}
		# push @ERRORS, "Sorry, but this functionality is currently offline - please check back later today.";

		}
	elsif ($ACTION eq 'NEW-SUBDOMAIN') {
		$GTOOLS::TAG{'<!-- ACTION_PRETTY -->'} = 'Add Subdomain';
		my ($SUB,$DOMAIN) = split(/\./,$DOMAINNAME,2);
		my ($D) = DOMAIN->new($USERNAME,$DOMAIN);
		if (not $D) {
			push @ERRORS, "Domain $DOMAIN is not currently setup in your account, please register,transfer,delegate it first.";
			}
		# push @ERRORS, "Sorry, but this functionality is currently offline - please check back later today.";
		}
	elsif ($ACTION eq 'NEW-TRANSFER') {
		$GTOOLS::TAG{'<!-- ACTION_PRETTY -->'} = 'Transfer Domain';
		my $DOMAIN = $DOMAINNAME;

		if (DOMAIN::REGISTER::DomainAvailable($DOMAIN)) {
			push @ERRORS, "Sorry, but domain $DOMAIN is not registered [cannot be transferred], use REGISTER instead";
			}
		elsif (&DOMAIN::REGISTER::BelongsToRsp($DOMAINNAME)) {
			## already belongs to us
			}
		elsif (DOMAIN::REGISTER::is_locked($DOMAINNAME)) {
			push @ERRORS, "Domain is currently locked and cannot be transferred, please ask your current register to unlock it.";
			}
		else {
			push @ERRORS, "Sorry, but this functionality is no longer available.";
			}
		}
	elsif ($ACTION eq 'NEW-DELEGATE') {
		$GTOOLS::TAG{'<!-- ACTION_PRETTY -->'} = 'Delegate Domain';
		my (@NSMSGS) = &DOMAIN::REGISTER::verify_ns($DOMAINNAME);
		if (scalar(@NSMSGS)>0) {
			push @MSGS, "WARN|Nameservers *MUST* be configured as 'ns.zoovy.com' and 'ns2.zoovy.com'";
			foreach my $msg (@NSMSGS) { push @MSGS, "WARN|NS Verify Error - $msg"; }
			}
		elsif (&DOMAIN::REGISTER::BelongsToRsp($DOMAINNAME)) {
			push @ERRORS, "This domain appears to be registered with us - please use TRANSFER instead to make changes";
			}
		# push @ERRORS, "Sorry, but this functionality is currently offline  - please check back later today.";
		}
	elsif ($ACTION eq 'NEW-RESERVATION') {
		$GTOOLS::TAG{'<!-- ACTION_PRETTY -->'} = 'Reserve Random Domain';
		if ($DOMAINNAME ne '') {
			push @ERRORS, "Please leave domain name blank to reserve one"; 
			}
		}


	my ($AVAILABLE_PROFILESREF) = undef;
	if (scalar(@ERRORS)>0){
		}
	elsif ($ACTION ne '') {
		$AVAILABLE_PROFILESREF = &ZOOVY::fetchprofiles($USERNAME,'FILTER'=>'NO_DOMAIN_MAPPED');
		if (scalar(@{$AVAILABLE_PROFILESREF})==0) {
			my ($SUGGESTEDPROFILE) = &DOMAIN::suggest_profilename($USERNAME,$DOMAINNAME);
			$AVAILABLE_PROFILESREF = [ $SUGGESTEDPROFILE ];
			push @MSGS, "WARN|No profiles are available for the requested action profile (profile:$SUGGESTEDPROFILE will be autogenerated)";
			}
		}

	push @MSGS, "WARN|ACTION IS:$ACTION";

	if (scalar(@ERRORS)>0) {
		foreach my $err (@ERRORS) {
			push @MSGS, "ERROR|$err";
			}
		$VERB = 'NEW';
		}
	elsif ($ACTION =~ /^(NEW-RESERVATION|NEW-REGISTER|NEW-SUBDOMAIN|NEW-DELEGATE|NEW-TRANSFER)$/) {
		$GTOOLS::TAG{'<!-- DOMAINNAME -->'} = $DOMAINNAME;
		my $c = '';
		foreach my $NS (@{$AVAILABLE_PROFILESREF}) {
			$c .= "<option value=\"$NS\">$NS</option>";
			}
		if ($c eq '') {
			$c .= "<option value=\"\"></option>";
			}
		$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
		$template_file = 'new-confirm.shtml';
		}
	else {
		push @MSGS, "ERROR|UNKNOWN ACTION:$ACTION";
		}
	}




if ($VERB eq 'NEW') {
	$GTOOLS::TAG{'<!-- DOMAINNAME -->'} = sprintf("%s",$ZOOVY::cgiv->{'DOMAINNNAME'});
	$template_file = 'new.shtml';
	}



##
##
##
if ($VERB eq 'PROFILE-CREATE') {
   my $CODE = $ZOOVY::cgiv->{'CODE'};
   $CODE =~ s/[\W_]+//gs;
	$CODE = uc($CODE);
   if (length($CODE)<3) {
		push @MSGS, "ERROR|Profile must be at least 3 characters log";
		}
   else {
      my $ref = {};
      $ref->{'prt:id'} = int($PRT);
      $ref->{'zoovy:site_partition'} = $PRT;
      &ZOOVY::savemerchantns_ref($USERNAME,$CODE,$ref);
		push @MSGS, "SUCCESS|Created profile $CODE on partition #$PRT";
      }
	$VERB = 'PROFILES';

   }




if ($VERB eq 'PROFILES') {
	if (not $LU->is_admin()) {
		push @MSGS, "ERROR|Cannot access profiles - reason: not admin";
		$VERB = '';
		}
	}

if ($VERB eq 'PROFILES') {
	my (@domains) = &DOMAIN::QUERY::domains($USERNAME);
	my $c = '';
	my $r = '';
	my $PRT_PRIMARY = undef;
	foreach my $domain (@domains) {		## don't sort alphabetically because prt,is_prt_primary
		($r) = ($r eq 'r0')?'r1':'r0';
		my ($D) = DOMAIN->new($USERNAME,$domain);
		if ($D->{'IS_PRT_PRIMARY'}) { $PRT_PRIMARY = $domain; $r = 'rs'; }
		$c .= sprintf("<tr class='$r'><td>%s</td><td>%s</td><td>%s</td><td>%s</td<</tr>\n",
				$domain,$D->profile(),$D->prt(),(($D->{'IS_PRT_PRIMARY'})?'Yes':'No'));
		}
	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $c;
	if (not defined $PRT_PRIMARY) {
		push @MSGS, "WARN|There is no primary domain for this partition. Please configure a domain as primary.";
		}
	$template_file = 'profiles.shtml';
	}


if (($VERB eq 'FUSEMAIL') || ($VERB eq 'FUSEMAIL-SYNC')) {
	require PLUGIN::FUSEMAIL;
	my @fmusers = &PLUGIN::FUSEMAIL::report($USERNAME);	
	push @BC, { name=>'ZoovyMail' };
	$help = "#50268";

	## make sure we've got the latest version of the flags!
	my $count = 0; 
	if ((scalar(@fmusers)==0) && ($FLAGS !~ /,ZM,/)) {
		my $dbh = &DBINFO::db_zoovy_connect();
		my $pstmt = "select count(*) from BS_ACTIONS where USERNAME=".$dbh->quote($USERNAME)." and PROC='ADDBUNDLE' and PARAMETER1='ZM' and (PROCESSED=0 or PROCESSED>".(time()-600).')';
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		($count) = $sth->fetchrow();
		$sth->finish();
		&DBINFO::db_zoovy_close();
		if ($count>0) {
			require ZACCOUNT;
			&ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
			}
		}


	print STDERR "COUNT: $count\n";
	if (not $LU->is_level(5)) {
		push @MSGS, "ERROR|Sorry, but the Zoovy Mail feature is not available to accounts at your level.";
		}
	elsif (($FLAGS =~ /,PKG\=(NOTLIVE|TRIAL),/) && (not $LU->is_zoovy())) {
		$GTOOLS::TAG{'<!-- FUSEMAIL -->'} = 
		push @MSGS, qq~ERROR|ZoovyMail cannot be provisioned on the "NOTLIVE" package, you will need to convert this account to a LIVE package to provision it.~;
		}
	elsif (($count>0) || (($FLAGS =~ /,ZM,/) && (scalar(@fmusers)==0))) {
		push @MSGS, qq~ERROR|Your ZoovyMail account has been requested, but has not been provisioned yet.~;
		}
	elsif (($FLAGS !~ /,ZM,/) && (scalar(@fmusers)==0)) {
		push @MSGS, qq~WARN|You have not yet enabled ZoovyMail on your account.~;
		}
	else {
		require PLUGIN::FUSEMAIL;

		my $c = qq~ZoovyMail features are currently available for this account.<br>~;
		if ($VERB eq 'FUSEMAIL-SYNC') {
			$c .= "<font color='blue'>Verified Account Settings</font>";
			PLUGIN::FUSEMAIL::syncuser($USERNAME);		
			}

		$c .= qq~<br><b>Users:</b><table>~;
		foreach my $userref (@fmusers) {
			$c .= "<tr><td width=70>$userref->{'email'}</td>";
			if ($LU->is_admin() || $LU->is_zoovy()) {
				my $url = &PLUGIN::FUSEMAIL::loginurl($userref->{'email'});
				$c .= "<td><a href=\"$url\">[Inbox Login]</a></td>";
				}
			$c .= "</tr>";
			}
		$c .= "</table>";

		if ($LU->is_admin() || $LU->is_zoovy()) {
			$c .= "
<div class=\"warning\">
Password/login urls are displayed because you are an Admin user
</div>"; 
			}

		if (scalar(@fmusers)==1) {
			$c .= qq~<br><b>You still need to go setup additional email inboxes for each employee by going to Setup / Manage Users</b><br>~;
			}

		my $emailout = '';
		require Text::CSV_XS;
		my $csv = Text::CSV_XS->new();          # create a new object

		# require FUSEMAIL;
		my ($code,$csvtxt) = &PLUGIN::FUSEMAIL::Request("reportmail",{user=>"admin\@$USERNAME.zoovy.com",group_subaccount=>"yes",type=>"all"});
		my @lines = split(/[\n\r]+/,$csvtxt);
		shift @lines; 	## remove the "Success" header line.
		$emailout .= "<table>";
		my $r = '';
		foreach my $line (@lines) {
			next if ($line eq '');
			my $status  = $csv->parse($line);       # parse a CSV string into fields
			my @columns = $csv->fields();           # get the parsed fields
			$emailout .= "<tr class=\"".($r = (($r eq 'r0')?'r1':'r0'))."\">";
			$emailout .= "<td>$columns[0]</td>";
			$emailout .= "<td>$columns[2]</td>";
			$emailout .= "<td>$columns[3]</td>";
			$emailout .= "</tr>";
			}
		if ($r eq '') {
			$emailout .= "<tr><td><i>Sorry but there are no Aliases, Forwarders</i></td></tr>";
			}
		# $emailout .= "<tr><td>".Dumper(\@lines)."</td>";
		$emailout .= "</table>";
		
		$c .= "<hr><b>Email Aliases/Forwarders</b><br>$emailout";


		$c .= qq~
<br>
<form action="index.cgi">
<input type="hidden" name="VERB" value="FUSEMAIL-SYNC">
<input class="button" type="submit" value="Verify Settings">
</form>
<div class="hint">
Verify Settings will attempt to update all fusemail accounts so they are in-sync.
</div>
~;
		$GTOOLS::TAG{'<!-- FUSEMAIL -->'} = $c;
		}

	$template_file = 'fusemail.shtml';
	}

if ($VERB eq 'REALLY-NUKE') {
	my $domain= $ZOOVY::cgiv->{'DOMAIN'};
	my ($d) = DOMAIN->new($USERNAME,$domain);
	$d->nuke('*LU'=>$LU);	
	
	$VERB = 'CONFIG';
	}


## PREFLIGHT REGISTER-SAVE - see if we're registering a new domain, or a subdomain -- since the
##		actions are *really* different, but the same field can be used for both.
##			
if ($VERB eq 'REGISTER-SAVE') {
	## check for subdomain
	my $domain = $ZOOVY::cgiv->{'DOMAIN'};
	$domain =~ s/^[\s]+//g;	 # strip leading whitespace
	$domain =~ s/[\s]$+//g;	 # strip trailing whitespace.
	#$domain =~ s/^[\d]+//g;	 # domains may not start iwth a number.

	## subdomain.domain.com
	##	domain.com
	##	somedomain.co.uk
	my @parts = split(/\./,$ZOOVY::cgiv->{'DOMAIN'});
	my $subdomain = shift @parts;
	$domain = join(".",@parts);

	my $count = 0;
	if (scalar(@parts)>1) {
		## we gotta have *AT LEAST* two parts e.g. domain.com to even bother with a lookup
		my $zdbh = &DBINFO::db_zoovy_connect();
		my $pstmt = "select count(*) from DOMAINS where MID=$MID /* $USERNAME */ and DOMAIN=".$dbh->quote($domain);
		print STDERR $pstmt."\n";
		my ($count) = $zdbh->selectrow_array($pstmt);
		&DBINFO::db_zoovy_close();
		}
	
	if ($count>0) {
		## okay we're trying to register a subdomain for a domain we've already got.
		$VERB = 'SUBDOMAIN-SAVE';
		$ZOOVY::cgiv->{'SUBDOMAIN'} = $subdomain;
		$ZOOVY::cgiv->{'DOMAIN'} = $domain;
		}
	else {
		## okie dokie, so we're not registering a subdomain and we'll pass through to VERB=REGISTER-SAVE
		$VERB = 'REGISTER-SAVE';
		}
	}


## REGISTER A NEW DOMAIN
if ($VERB eq 'REGISTER-SAVE') {
	my $domain = $ZOOVY::cgiv->{'DOMAIN'};
	$domain =~ s/^[\s]+//g;	 # strip leading whitespace
	$domain =~ s/[\s]$+//g;	 # strip trailing whitespace.
	# $domain =~ s/^[\d]+//g;	 # domains may not start iwth a number.
	my @errors = &DOMAIN::TOOLS::valid_domain($domain);

#	use Data::Dumper;
#	print STDERR "ERRORS: ".Dumper(@errors);
	if (scalar(@errors)==0) {
		require DOMAIN::REGISTER;
		if (not &DOMAIN::REGISTER::DomainAvailable($domain)) {
			push @errors, "Sorry, the domain [$domain] is not available and has already been registered by somebody else, (if you are the owner perhaps you meant to do a transfer)";
			}
				
		}

	if (scalar(@errors)>0) {
		$VERB = 'REGISTER';
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>ERRORS:<br>".join("<br>",@errors)."<br></font>";
		}
	else {
		my ($d) = DOMAIN->new($USERNAME,$domain,register=>1);
		$d->{'PRT'} = $PRT;
		$d->gen_dkim_keys('save'=>0);
		$d->save();
		$VERB = 'CONFIG';
		$LU->log("SETUP.DOMAIN","Domain $domain registered","SAVE");
		}
	}

if ($VERB eq 'REGISTER') {
	push @BC, { name=>'Register' };
	$GTOOLS::TAG{'<!-- DOMAIN -->'} = $ZOOVY::cgiv->{'DOMAIN'};
	$template_file = 'register.shtml';
	}


if ($VERB eq 'SUBDOMAIN-SAVE') {
	my $domain = lc($ZOOVY::cgiv->{'SUBDOMAIN'});
	$domain =~ s/^[\s]+//g;	 # strip leading whitespace
	$domain =~ s/[\s]$+//g;	 # strip trailing whitespace.
	$domain =~ s/^[\d]+//g;	 # sub-domains may not start iwth a number.
	$domain =~ s/[^a-z0-9]+//g;	 # sub-domains may not have dashes, or other funny characters
	$domain = $domain.'.'.$ZOOVY::cgiv->{'DOMAIN'};

	my ($d) = DOMAIN->new($USERNAME,$domain,subdomain=>1);
	$d->{'EMAIL_TYPE'} = 'NONE';
	$d->{'REG_TYPE'} = 'SUBDOMAIN';
	$d->{'PRT'} = $PRT;
	$d->gen_dkim_keys('save'=>0);
	$d->save();

	$LU->log("SETUP.DOMAIN","Subdomain $ZOOVY::cgiv->{'SUBDOMAIN'} updated","INFO");
	$VERB = 'CONFIG';
	}

if ($VERB eq 'SUBDOMAIN') {
	push @BC, { name=>'Add Subdomain' };
	$GTOOLS::TAG{'<!-- DOMAIN -->'} = $ZOOVY::cgiv->{'DOMAIN'};
	$template_file = 'subdomain.shtml';
	}



## TRANSFER AN EXISTING DOMAIN
if ($VERB eq 'TRANSFER-SAVE') {
	my $domain = $ZOOVY::cgiv->{'DOMAIN'};
	my @errors = &DOMAIN::TOOLS::valid_domain($domain);

	require DOMAIN::REGISTER;

	if (scalar(@errors)==0) {
		if (&DOMAIN::REGISTER::BelongsToRsp($domain)) {
			push @errors, "Domain currently registered thru Zoovy, domain registration status updated.";
			my ($d) = DOMAIN->new($USERNAME,$domain,transfer=>1);
			$d->{'STATUSMSG'} = 'Live';
			$d->{'REG_TYPE'} = 'ZOOVY';
			$d->{'REG_STATE'} = 'VERIFY';
			$d->{'PRT'} = $PRT;
			$d->gen_dkim_keys('save'=>0);
			$d->save();
			}
		}

	if (scalar(@errors)==0) {
		require DOMAIN::REGISTER;
		if (&DOMAIN::REGISTER::is_locked($domain)) {
			push @errors, "Domain [$domain] is locked, please login at the current registrar and unlock it prior to transfer.";
			}
		}

	if (scalar(@errors)==0) {
		my ($d) = DOMAIN->new($USERNAME,$domain,transfer=>1);
		my ($VERIFIED,$STATUS) = &DOMAIN::REGISTER::check_ns($d);
		if ($VERIFIED<2) {
			push @errors, "Nameservers do not point at Zoovy, please point your nameservers at Zoovy prior to transfer.";
			}
		}

	if ($USERNAME eq 'brian') {
		@errors = ();
		}

	if (scalar(@errors)>0) {
		$VERB = 'TRANSFER';
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>ERRORS:<br>".join("<br>",@errors)."<br></font>";
		}
	else {
		my ($d) = DOMAIN->new($USERNAME,$domain,transfer=>1);
		$d->{'REG_TYPE'} = 'ZOOVY';
		$d->{'PRT'} = $PRT;
		$d->gen_dkim_keys('save'=>0);
		$d->save();
		$VERB = 'CONFIG';
		$LU->log("SETUP.DOMAIN","Domain $domain transfer requested.","SAVE");
		}
	}

if ($VERB eq 'TRANSFER') {
	push @BC, { name=>'Transfer' };

	require DOMAIN::REGISTER;
	my $DOMAIN = $ZOOVY::cgiv->{'DOMAIN'};

	$GTOOLS::TAG{'<!-- DOMAIN -->'} = $ZOOVY::cgiv->{'DOMAIN'};
	$template_file = 'transfer.shtml';
	}

## POINT NAMESERVERS AT ZOOVY
if ($VERB eq 'LINK-SAVE') {
	my $domain = $ZOOVY::cgiv->{'DOMAINNAME'};
	my @errors = &DOMAIN::TOOLS::valid_domain($domain);

	if (scalar(@errors)>0) {
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "<font color='red'>ERRORS for $domain:<br>".join("<br>",@errors)."<br></font>";
		}
	else {
		my ($d) = DOMAIN->new($USERNAME,$domain);
		$d->{'EMAIL_TYPE'} = $ZOOVY::cgiv->{'EMAIL_TYPE'};
		if (not defined $d->{'EMAIL_TYPE'}) { $d->{'EMAIL_TYPE'} = 'NONE'; }
		$d->{'EXTERNAL_MX1'} = $ZOOVY::cgiv->{'EXTERNAL_MX1'};
		$d->{'EXTERNAL_MX2'} = $ZOOVY::cgiv->{'EXTERNAL_MX1'};
		$d->{'PRT'} = $PRT;
		$d->gen_dkim_keys('save'=>0);
		$d->save();
		$LU->log("SETUP.DOMAIN","Domain $domain configured w/external nameservers","SAVE");
		}
	$VERB = 'CONFIG';		
	}

if ($VERB eq 'LINK') {
	push @BC, { name=>'Link Domain' };
	$GTOOLS::TAG{'<!-- DOMAINNAME -->'} = $ZOOVY::cgiv->{'DOMAIN'};
	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- MXMODE_ZM -->'} = 'selected';
	$GTOOLS::TAG{'<!-- MXMODE_MX -->'} = '';
	$GTOOLS::TAG{'<!-- EXTERNAL_MX1 -->'} = '';
	$GTOOLS::TAG{'<!-- EXTERNAL_MX2 -->'} = '';
	$template_file = 'link.shtml';
	}


if ($VERB eq 'CONFIG') {
	push @BC, { name=>'Domain Config' };
	require AJAX::PANELS;
	require DOMAIN::PANELS;

	my $buf     = '';                         # temporarily garbage variable.
	my $class = 'r1';
	my $PRT_PRIMARY = undef;
	my @domains = &DOMAIN::TOOLS::domains($USERNAME,PRT=>$PRT);
	foreach my $domain (@domains) {
		my ($d) = DOMAIN->new($USERNAME,$domain);
		if ($d->{'IS_PRT_PRIMARY'}) { $PRT_PRIMARY = $domain; }
		if ($class eq 'r0') { $class = 'r1'; } else { $class = 'r0'; }

		my $panel = 'DOMAIN:'.$d->{'DOMAIN'};

		my ($content,$state) = ('',0);
		if (defined $LU) { ($state) = $LU->get('domain.'.$panel,0); }

		$content = ($state)?&DOMAIN::PANELS::panel_domain($LU,'','LOAD',$d,{VERB=>''}):'';
		# if ($state) { $content = 'test'; }
		my $warnings = '';

		$buf .= &AJAX::PANELS::render_panel($panel,$d->{'DOMAIN'}.'<br><font size=1>'.$d->{'STATUSMSG'}.'</font>'.$warnings,$state,$content);
		} ## end foreach my $line (sort @ar)

	if ($buf eq '') {
		$buf .= "<tr><td>No domains exist yet - use \"Domain Setup\" to get started.</td></tr>";
		}
	if (not defined $PRT_PRIMARY) {
		push @MSGS, "WARN|No domain is configured as Primary for this partition";
		}

	$template_file = 'config.shtml';
	$GTOOLS::TAG{"<!-- EXISTING_DOMAINS -->"} = $buf;
	}


my @TABS = ();
push @TABS, { name=>'Add Domains', link=>'index.cgi?VERB=NEW', selected=>($VERB eq 'NEW')?1:0 };
push @TABS, { name=>'Domain Config', link=>'index.cgi?VERB=CONFIG', selected=>($VERB eq 'CONFIG')?1:0 };
if ($FLAGS =~ /,ZM,/) {
	push @TABS, { name=>'FuseMail', link=>'index.cgi?VERB=FUSEMAIL', selected=>($VERB eq 'FUSEMAIL')?1:0 };
	}
if ($LU->is_admin()) {
	push @TABS, { name=>'Profiles &amp; Partitions', link=>'index.cgi?VERB=PROFILES', selected=>($VERB eq 'PROFILES')?1:0 };
	}

&GTOOLS::output(
   'title'=>'Setup : Domain Hosting',
   'file'=>$template_file,
	'head'=>&AJAX::PANELS::header('DOMAINEDIT','','index.cgi'),
   'header'=>'1',
   'help'=>$help,
	'jquery'=>1,
   'tabs'=>\@TABS,
	'msgs'=>\@MSGS,
   'bc'=>@BC,
   );

&DBINFO::db_zoovy_close();


