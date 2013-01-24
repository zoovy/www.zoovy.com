#!/usr/bin/perl

use strict;
use Data::Dumper;
use URI::Escape;
use lib "/httpd/modules";
require GTOOLS;
require DBINFO;
require LUSER;
require DOMAIN::TOOLS;
require DOMAIN;
require ZWEBSITE;

my $dbh = &DBINFO::db_zoovy_connect();

my @MSGS = ();
my ($LU) = LUSER->authenticate();
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @BC = ( { name=>"Sites", link=>"/biz/sites" } );

my $template_file = '';
my $VERB = uc($ZOOVY::cgiv->{'VERB'});

if ($VERB eq '') {
	$VERB = $LU->get('sites.focus','DOMAINS');
	}

if ($FLAGS =~ /,SCONLY,/) {
	$VERB = 'DENIED';
	$template_file = 'denied.shtml';
	}


my ($udbh) = &DBINFO::db_user_connect($USERNAME);

#if ($VERB =~ /^REAUTH\-(PARTITIONS|PROFILES|DOMAINS)$/) {
#	$VERB = $1;
#	## re-authenticate and change partition.
#	require AUTH;
#	my ($TOKEN) = AUTH::get_token_for_zjsid($ZOOVY::cookies->{'zjsid'});
#	my $TO_PRT = $ZOOVY::cgiv->{'PRT'};
#
#	if (not defined $TOKEN) {
#		push @MSGS, "ERROR|Could not lookup initial authentication token for your session";
#		}
#	else {
#		my ($ZJSID) = &AUTH::authorize_session($USERNAME,$LUSERNAME,$TOKEN,$TO_PRT);
#		push @MSGS, "SUCCESS|Successful authentication to partition # $TO_PRT";
#		$ZOOVY::PRT = $TO_PRT;
#		&AUTH::set_zjsid_cookie($ZJSID);
#		}
#	}

my @DIAGS = ();
if ($VERB eq 'FIX') {
	my $CMD = URI::Escape::uri_unescape($ZOOVY::cgiv->{'CMD'});
	$VERB = 'CHECKUP';

	my ($data,$action) = split(/\?/,$CMD,2);
	if ($data =~ /^profile:(.*?)$/) {
		my $NS = $1;
		my ($nsref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$NS);
		my ($k,$v) = split(/=/,$action,2);
		$nsref->{$k} = $v;
		&ZOOVY::savemerchantns_ref($USERNAME,$NS,$nsref);
		push @DIAGS, "FIX||$CMD ===> PROFILE[$NS] set $k=$v";
		}
	elsif ($data =~ /^webdb:([\d]+)$/) {
		my $PRT = int($1);
		my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
		my ($k,$v) = split(/=/,$action,2);
		$webdbref->{$k} = $v;
		&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
		push @DIAGS, "FIX||$CMD ===> WEBDB[$PRT] set $k=$v";
		}
	elsif ($data =~ /^domain:(.*?)$/) {
		my $DOMAIN = $1;
		my $d = DOMAIN->new($USERNAME,$DOMAIN);
		my ($k,$v) = split(/=/,$action,2);
		$d->set($k,$v);
		$d->save();
		push @DIAGS, "FIX||$CMD ===> DOMAIN[$DOMAIN] set $k=$v";
		}
	}


if ($VERB eq 'CHECKUP') {

	my $c = '';
	my $FIX = ($ZOOVY::cgiv->{'FIX'})?1:0;


	if ($ZOOVY::cgiv->{'CHECK-GLOBAL'}) {
		my ($globalref) = &ZWEBSITE::fetch_globalref($USERNAME);
		my $i = 0;
		push @DIAGS, "INFO||Evaulating ".scalar(@{$globalref->{'@partitions'}})." partitions";
		my %USED = ();
		foreach my $prt ( @{$globalref->{'@partitions'}} ) {
			if ($prt->{'profile'} eq '') { $prt->{'profile'} = 'DEFAULT'; }
			if (not defined $prt->{'p_navcats'}) { $prt->{'p_navcats'}=0; }
			if (not defined $prt->{'p_customers'}) { $prt->{'p_customers'}=$i; }

			push @DIAGS, "INFO||PRT#$i PROFILE($prt->{'profile'}) CATEGORIES($prt->{'p_navcats'}) CUSTOMERS($prt->{'p_customers'})";

			if (defined $USED{$prt->{'profile'}}) {
				push @DIAGS, "ERR||WARNING: prt $USED{$prt->{'profile'}} and prt $i are both mapped to $prt->{'profile'}<br>== reminder: Profiles should never be shared by partition";
				}
			else {
				push @DIAGS, "INFO||Partition $i uses profile $prt->{'profile'}";
				$USED{$prt->{'profile'}} = $i;
				}

			my ($dbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$i);
			if ($dbref->{'profile'} ne $prt->{'profile'}) {
				push @DIAGS, "ERR|webdb:$i?profile=$prt->{'profile'}|Global partition says profile[$prt->{'profile'}] but webdb has profile=[$dbref->{'profile'}]*";
				if ($FIX) {
					$dbref->{'profile'} = $prt->{'profile'};
					&ZWEBSITE::save_website_dbref($USERNAME,$dbref,$i);
					push @DIAGS, "FIX||Set webdb(partition settings) for prt[$i] to profile $prt->{'profile'}";
					}
				}

			## some profile checks.
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$prt->{'profile'});
			if (int($nsref->{'prt:id'}) != int($i)) {
				push @DIAGS, "ERR|profile:$prt->{'profile'}?prt:id=$i|Profile[$prt->{'profile'}] has prt:id field set to: $nsref->{'prt:id'} (should be *$i)";
				if ($FIX) {
					$nsref->{'prt:id'} = $i;
					&ZOOVY::savemerchantns_ref($USERNAME,$prt->{'profile'},$nsref);
					push @DIAGS, "FIX||Profile[$prt->{'profile'} set prt:id=$i";
					}
				}
			if ($nsref->{'zoovy:site_partition'} != int($i)) {
				push @DIAGS, "ERR|profile:$prt->{'profile'}?zoovy:site_partition=$i|Profile[$prt->{'profile'}] has specialty site partition (zoovy:site_partition)=$nsref->{'zoovy:site_partition'} (should be *$i)"; 
				if ($FIX) {
					push @DIAGS, "FIX||Profile[$prt->{'profile'} set specialty site partition(zoovy:site_partition) was=$nsref->{'zoovy:site_partition'} [[we do this just to be safe]]";				
					$nsref->{'zoovy:site_partition'} = int($i);
					&ZOOVY::savemerchantns_ref($USERNAME,$prt->{'profile'},$nsref);
					}
				}

			if ($prt->{'p_navcats'} == $i) {
				push @DIAGS, "INFO||Partition[$i] has federated navigation - so we'll check that too.";
				if ($nsref->{'zoovy:site_rootcat'} ne '.') {
					push @DIAGS, "ERR|profile:$prt->{'profile'}?zoovy:site_rootcat=.|Profile[$prt->{'profile'}] has specialty rootcat(zoovy:site_rootcat)='$nsref->{'zoovy:site_rootcat'}'  should be (*)'.'";
					if ($FIX) {
						push @DIAGS, "FIX||Profile[$prt->{'profile'}] set rootcat for prt $i to . (was: $nsref->{'zoovy:site_rootcat'})";
		         	$nsref->{'zoovy:site_rootcat'} = '.';
						&ZOOVY::savemerchantns_ref($USERNAME,$prt->{'profile'},$nsref);
						}
					}
				}

			## we should probably eventually add some domain checks here.
			my ($udbh) = &DBINFO::db_user_connect($USERNAME);
			my $pstmt = "select DOMAIN from DOMAINS where IS_PRT_PRIMARY>0 and PRT=$PRT and MID=$MID";
			my @DOMAINS = ();
			my $sth = $udbh->prepare($pstmt);
			$sth->execute();
			while ( my ($domain) = $sth->fetchrow() ) { 
				push @DOMAINS, $domain; 
				}
			$sth->finish();
			if (scalar(@DOMAINS)==0) {
				push @DIAGS, "ERR||Partition[$i] needs at least one domain designated as primary";
				}
			elsif (scalar(@DOMAINS)==1) {
				push @DIAGS, "INFO||Partition[$i] has one primary domain '$DOMAINS[0]' (good)";
				}
			else {
				push @DIAGS, "ERR||Partition[$i] has more than one primary domain (confusing) - ".join(",",@DOMAINS);
				}

			&DBINFO::db_user_close();

			$i++;
			}	
		}



	if ($ZOOVY::cgiv->{'CHECK-DOMAINS'}) {
		my @domains = DOMAIN::TOOLS::domains($USERNAME);
		my %USED_PROFILES = ();
		my %USED_PRIMARY = ();
		foreach my $domainname (@domains) {
			my ($d) = DOMAIN->new($USERNAME,$domainname);
			my $PRT = $d->prt();
			my $PROFILE = $d->profile();
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);

			my $SKIP = 0;
			if ($d->{'HOST_TYPE'} eq 'REDIR') {
				push @DIAGS, "INFO||DOMAIN: $domainname is type REDIRECT, nothing to check";
				$SKIP++;
				}
			if ($d->{'HOST_TYPE'} eq 'MINISITE') {
				push @DIAGS, "INFO||DOMAIN: $domainname is type MINISITE, nothing to check";
				$SKIP++;
				}

			next if ($SKIP);
			
			#elsif ($d->{'HOST_TYPE'} eq 'NEWSLETTER') {
			#	}
			#elsif ($d->{'HOST_TYPE'} eq 'PRIMARY') {
			#	## primary domain .. should share same profile as partition.
			#	push @DIAGS, "INFO||DOMAIN: $domainname is type PRIMARY, profile=$d->profile() prt=$PRT";
			#	my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$d->profile());				
			#	my $prt = &ZOOVY::fetchprt($USERNAME,$PRT);

			if ($USED_PROFILES{$PROFILE}) {
				push @DIAGS, "ERR||DOMAIN: $domainname has same profile[$PROFILE] as domain $USED_PROFILES{$PROFILE} -- these should not be shared.";
				if ($FIX) {
					push @DIAGS, "FAIL||Cannot resolve which domain $domainname or $USED_PROFILES{$PROFILE} should be using profile $PROFILE";
					}
				}
			else {
				$USED_PROFILES{$PROFILE} = $domainname;
				}

			if ($USED_PRIMARY{$PRT}) {
				push @DIAGS, "ERR||DOMAIN: $domainname is primary for partition $PRT, but domain $USED_PRIMARY{$PRT} claims to be primary for same partition.";
				if ($FIX) {
					push @DIAGS, "FAIL||I'm sorry, but I will not conduct a domain deathmatch between $domainname and $USED_PRIMARY{$PRT} for partition $PRT, please work it out yourself.";
					}
				}
			else {
				$USED_PRIMARY{$PRT} = $domainname;
				}

			if ($nsref->{'prt:id'} != $PRT) {
				push @DIAGS, "ERR||DOMAIN: $domainname has profile($PROFILE) which says prt:id=$nsref->{'prt:id'}) .. but domain says PRT=$PRT";
				if ($FIX) {
					push @DIAGS, "FAIL||Cannot resolve PRT/prt:id discrepancy automatically! .. I have no idea who to trust here.";
					}					
				}
			if ($PRT != $nsref->{'prt:id'}) {
				push @DIAGS, "ERR||DOMAIN: $domainname has partition=$PRT but also profile[$PROFILE] which has prt:id=$nsref->{'prt:id'}";				
				if ($FIX) {
					push @DIAGS, "FIX||DOMAIN: $domainname set partition=$nsref->{'prt:id'} .. was partition=$PRT";
					$PRT = $nsref->{'prt:id'};
					$d->save();
					}
				}
			if ($PRT != $nsref->{'zoovy:site_partition'}) {
				push @DIAGS, "ERR||DOMAIN: $domainname has profile($PROFILE) which has specialty site partition(zoovy:site_partition)=$nsref->{'zoovy:site_partition'} (should be *$PRT)";
				if ($FIX) {
					push @DIAGS, "FIX||DOMAIN: removed zoovy:site_partition from profile was=$nsref->{'zoovy:site_partition'}";
					$nsref->{'zoovy:site_partition'} = $PRT;
					&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$nsref);
					}
				}

			#	}
			#elsif ($d->{'HOST_TYPE'} eq 'SPECIALTY') {
			#	## specialty site. -- 
			#	##		zoovy:site_rootcat
			#	##		zoovy:site_partition
			#	push @DIAGS, "INFO||DOMAIN: $domainname is type SPECIALTY, profile=$PROFILE prt=$PRT";
			#	my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);				

			#	if ($USED_PROFILES{$PROFILE}) {
			#		push @DIAGS, "ERR||DOMAIN: $domainname has same profile as domain $USED_PROFILES{$PROFILE} -- these should not be shared.";
			#		if ($FIX) {
			#			push @DIAGS, "FAIL||Cannot resolve which domain $domainname or $USED_PROFILES{$PROFILE} should be using profile $PROFILE";
			#			}
			#		}
			#	else {
			#		$USED_PROFILES{$PROFILE} = $domainname;
			#		}
	
			## $PRT is assumed to be correct.
			if ($PRT != $nsref->{'zoovy:site_partition'}) {
				push @DIAGS, "ERR||DOMAIN: $domainname *prt=$PRT found issue w/profile($PROFILE) has zoovy:site_partition=$nsref->{'zoovy:site_partition'} (should be same as domain *$PRT)";	
				if ($FIX) {
					push @DIAGS, "FIX||DOMAIN: $domainname setting profile($PROFILE zoovy:site_partition=$PRT (was $nsref->{'zoovy:site_partition'})";
					$nsref->{'zoovy:site_partition'} = $PRT;
					&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$nsref);
					}
				}
			## $PRT is assumed to be correct.
			if ($PRT != $nsref->{'prt:id'}) {
				push @DIAGS, "ERR||DOMAIN: $domainname found issue w/profile($PROFILE) has prt:id=$nsref->{'prt:id'}) but (should be same as domain *$PRT)";	
				if ($FIX) {
					push @DIAGS, "FIX||DOMAIN: $domainname profile($PROFILE) setting prt:id=$PRT (was $nsref->{'prt:id'})";
					$nsref->{'prt:id'} = $PRT;
					&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$nsref);
					}
				}
			}
		}


	if ($ZOOVY::cgiv->{'CHECK-PROFILE'}) {
		my %USED = ();
		foreach my $p (@{&ZOOVY::fetchprofiles($USERNAME)}) {
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$p);

			push @DIAGS, "INFO||Checking Profile $p";
			if ($nsref->{'prt:id'} ne '') {
				push @DIAGS, "INFO||Profile:$p will checkout through partition prt:id=$nsref->{'prt:id'}";
				}

			if ($nsref->{'zoovy:site_partition'} ne '') {
				push @DIAGS, "INFO||Profile:$p is a specialty site for partition zoovy:site_partition=$nsref->{'zoovy:site_partition'}";
				}

			if ($nsref->{'prt:id'} != $nsref->{'zoovy:site_partition'}) {
				push @DIAGS, "ERR||Profile:$p has *zoovy:site_partition=$nsref->{'zoovy:site_partition'} and prt:id=$nsref->{'prt:id'}";
				if ($FIX) {
					push @DIAGS, "FIX||Profile: $p setting prt:id=$nsref->{'zoovy:site_partition'} (was $nsref->{'prt:id'})";
					$nsref->{'prt:id'} = $nsref->{'zoovy:site_partition'};
					&ZOOVY::savemerchantns_ref($USERNAME,$p,$nsref);
					}
				}

			## lets look at what domains are mapped.
			my @domains = DOMAIN::TOOLS::domains($USERNAME,PROFILE=>$p,HOST_TYPE=>['PRIMARY','SPECIALTY'],SKIP_VSTORE=>1);
			if (scalar(@domains)==0) {
				push @DIAGS, "INFO||Profile $p -- no domains believe they are mapped (that might be okay)";
				}
			elsif (scalar(@domains)==1) {
				push @DIAGS, "INFO||Profile: $p -- only one domain ($domains[0]) is mapped to profile (that's good)";
				my $d = DOMAIN->new($USERNAME,$domains[0]);
				if ($d->{'PRT'} != $nsref->{'prt:id'}) {
					push @DIAGS, "ERR|domain:$domains[0]?PRT=$nsref->{'prt:id'}|Profile $p says *prt:id=$nsref->{'prt:id'} but domain $domains[0] thinks has PRT=$d->{'PRT'} (HOST_TYPE=$d->{'HOST_TYPE'}) ";
					if ($FIX) {
						push @DIAGS, "FIX||Profile $p set domain to PRT=$nsref->{'prt:id'} (was $d->{'PRT'})";
						$d->{'PRT'} = $nsref->{'prt:id'};
						$d->save();
						}
					}
				else {
					push @DIAGS, "INFO||Profile: $p -- domain ($domains[0]) PRT=$d->{'PRT'} is mapped to same value as profile prt:id=$nsref->{'prt:id'} (that's very good)";
					}	
				}
			else {
				foreach my $domain (@domains) {
					push @DIAGS, "ERR||Profile:$p has more than one domain ($domain) -- this can't be corrected automatically. ";
					if ($FIX) {
						push @DIAGS, "FAIL||Profile: $p, cowardly refusing to unmap domain $domain from profile. Too many choices (".scalar(@domains).").";
						}
					}
				}
			
			}
		}

	if (scalar(@DIAGS)==0) {
		push @DIAGS, "INFO||No checks conducted.";
		}

	foreach my $msg (@DIAGS) {
		my ($type,$cmd,$txt) = split(/\|/,$msg,3);
		# $LU->log("SETUP.GLOBAL.FIX",$ERR,"WARN");
		if ($type eq 'INFO') {
			$c .= "<tr><td valign=top>INFO:</td><td valign=top>$txt</td></tr>";
			}
		elsif ($type eq 'FIX') {
			$c .= "<tr><td valign=top><b><font color='green'>FIX:</font></b></td><td valign=top><font color='green'>$txt</font></td></tr>";
			}
		elsif ($type eq 'ERR') {
			my $fixlink = '';
			if ($cmd ne '') {
				$cmd = URI::Escape::uri_escape($cmd);
				$fixlink .= "<br><a href=\"index.cgi?VERB=FIX&CMD=$cmd";
				foreach my $i ('CHECK-GLOBAL','CHECK-DOMAINS','CHECK-PROFILE') {
					next if (not defined $ZOOVY::cgiv->{$i});
					$fixlink .= "&$i=".$ZOOVY::cgiv->{$i};
					}
				$fixlink .= "\">[FIX THIS]</a>";
				}
			$c .= "<tr><td valign=top><font color='red'>ERROR:</font></td><td valign=top>$txt$fixlink</td></tr>";
			}
		elsif ($type eq 'FAIL') {
			$c .= "<tr><td valign=top><b><font color='red'>FAIL:</font></b></td><td valign=top><font color='red'>$txt</font></td></tr>";
			}
	
		if ($type ne 'INFO') {
			$LU->log("SITES.CHECKUP.$type",$txt);
			}
		}

#	$c = Dumper($ZOOVY::cgiv);

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	

	$GTOOLS::TAG{'<!-- CB_FIX -->'} = ($FIX)?'checked':'';
	$GTOOLS::TAG{'<!-- CB_CHECK-DOMAINS -->'} = (defined $ZOOVY::cgiv->{'CHECK-DOMAINS'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_CHECK-PROFILE -->'} = (defined $ZOOVY::cgiv->{'CHECK-PROFILE'})?'checked':'';
	$GTOOLS::TAG{'<!-- CB_CHECK-GLOBAL -->'} = (defined $ZOOVY::cgiv->{'CHECK-GLOBAL'})?'checked':'';

	$template_file = 'checkup.shtml';
	}

if ($VERB eq 'ADD-RESERVE-DOMAIN') {
	my ($PRT) = $ZOOVY::cgiv->{'PRT'};
	require DOMAIN::POOL;
 	my ($DOMAINNAME) = &DOMAIN::POOL::reserve($USERNAME,$PRT);
	if ($DOMAINNAME) {
		push @MSGS, "SUCCESS|Reserved domain: $DOMAINNAME";
		$VERB = 'DOMAINS';
		}
	else {
		push @MSGS, "ERROR|Could not find a free domain to reserve";
		$VERB = 'PARTITIONS';
		}
	}


if ($VERB eq 'DOMAINS') {
	$LU->set('sites.focus','DOMAINS'); $LU->save();
	my @domains = &DOMAIN::TOOLS::domains($USERNAME);
	my %PROFILES = ();
	my $c = '';
	my $out = '';
	my $class = 'r1';
	my $i = 0;
	foreach my $dname (sort @domains) {
		my ($d) = DOMAIN->new($USERNAME,$dname);
		my $ns = $d->profile();
		my $prt = int($d->prt());
		my $domainname = $d->domainname();

		## don't show redirect domains in the list.
		## next if ($d->{'HOST_TYPE'} eq 'REDIR');

		my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$ns);
		if ($class eq 'r0') { $class = 'r1'; } else { $class = 'r0'; }
		# $c .= "<tr><td>".Dumper($nsref)."</td></tr>";
		$c .= "<tr class=\"$class\">";
		$c .= "<td valign=top>
<img width=100 height=50 src=\"".&GTOOLS::imageurl($USERNAME,$nsref->{'zoovy:logo_website'},50,100,'FFFFFF')."\">
</td>";
		$c .= "<td valign=top>$ns</td>";
		$c .= "<td valign=top>$domainname</td>";
		$c .= qq~<td valign=top><button class="minibutton" onClick="changeDomain('$domainname',$prt); return false;">Use Domain</button></td>~;
		$c .= "<td>";
		my $ALLOW_EDIT = 0;
		foreach my $host ('WWW','M','APP') {
			if ($d->{"$host\_HOST_TYPE"} eq 'APP') {
				$c .= "<a target=\"_blank\" href=\"http://$host.$domainname\">$host</a> (app)<br>";
				}
			elsif ($d->{"$host\_HOST_TYPE"} eq 'VSTORE') {
				$c .= "<a target=\"_blank\" href=\"http://$host.$domainname?multivarsite=A&_sandbox=0\">$host Site-A</a> (vstore)<br>";
				$c .= "<a target=\"_blank\" href=\"http://$host.$domainname?multivarsite=B&_sandbox=0\">$host Site-B</a> (vstore)<br>";
				$ALLOW_EDIT++;
				}
			elsif ($d->{"$host\_HOST_TYPE"} eq 'REDIRECT') {
				my $params = &ZTOOLKIT::parseparams($d->{"$host\_CONFIG"});
				$c .= sprintf("<i>$host redirect to: %s/%s</i><br>",$params->{'REDIR'},$params->{'URI'});
				}
			else {
				$c .= "<i>$host.$dname not configured</i><br>";
				}
			}
		if ($ALLOW_EDIT) {
			$c .= "<a href=\"/biz/setup/builder/index.cgi?PROFILE=$ns\">Edit $ns</a><br>";
			}
		$c .= "</td>";


#		$c .= "<td>$d->{'HOST_TYPE'}</td>";
#		$c .= "<td align=center>";
#		$c .= "<a target=\"_blank\" href=\"http://$domainname?_sandbox=1\">STAGING</a> | ";
#		if ($LU->is_zoovy()) {
#			$c .= " | <a target=\"_blank\" href=\"http://www.$domainname?sbverb=login&code=$d->{'SANDBOX_PASSWORD'}\">sandbox</a>";
#			}
#		$c .= "</td>";
		$c .= "<td valign=top align=center>$prt</td>";
		$c .= "</tr>";

		$i++;
		}
	$GTOOLS::TAG{'<!-- DOMAINS -->'} = $c;
	$template_file = 'domains.shtml';
	}





if ($VERB eq 'PARTITIONS') {
	$LU->set('sites.focus','PARTITIONS'); $LU->save();
	my ($globalref) = &ZWEBSITE::fetch_globalref($USERNAME);

	my $i = 0;
	my $c = '';
	foreach my $prt ( @{$globalref->{'@partitions'}} ) {

		my $domain = &DOMAIN::TOOLS::domain_for_prt($USERNAME,$i);
		$c .= qq~<tr>~;
		if ($domain eq '') {
			$c .= qq~<td><div class="warning">No domain</div></td>~;
			$c .= qq~<td>$i</td><td><button style="width: 150px;" class="button" onClick=\"navigateTo('/biz/sites/index.cgi?VERB=ADD-RESERVE-DOMAIN&PRT=$i');\">Add Reserve Domain</a></td>~;
			}
		else {
			$c .= qq~<td><button class="button" onClick="changeDomain('$domain',$i); return false;">Use Partition</button></td>~;
			$c .= qq~<td>$i</td><td>$domain</td>~;
			}
		
		$c .= qq~<td><b>$prt->{'name'}</b>~;
		$c .= qq~</td></tr>~;
		$i++;
		}
	$GTOOLS::TAG{'<!-- PARTITIONS -->'} = $c;
	$template_file = 'partitions.shtml';
	}





if ($VERB eq 'PROFILES') {
	$LU->set('sites.focus','PROFILES'); $LU->save();
	my @domains = &DOMAIN::TOOLS::domains($USERNAME);
	my %PROFILES = ();
	my %DOMAIN_TO_PROFILE = ();
	foreach my $dname (@domains) {
		my ($d) = DOMAIN->new($USERNAME,$dname);
		my $ns = $d->{'PROFILE'};

		## skip domains that don't have a profile selected
		next if ($ns eq '');
		if (not defined $PROFILES{$ns}) { $PROFILES{$ns} = []; }
		push @{$PROFILES{$ns}}, [ $d->domainname(), $d->prt() ];
		}

	my $c = '';

	my $out = '';
	my $class = 'r1';
	my $i = 0;
	foreach my $ns (sort keys %PROFILES) {
		my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$ns);
		if (not defined $nsref->{'prt:id'}) { $nsref->{'prt:id'} = 0; }
	
		my $imgurl = &GTOOLS::imageurl($USERNAME,$nsref->{'zoovy:logo_website'},50,100,'FFFFFF');
		if ($imgurl  eq '') { $imgurl = '/biz/images/blank.gif'; }

		if ($class eq 'r0') { $class = 'r1'; } else { $class = 'r0'; }
		# $c .= "<tr><td>".Dumper($nsref)."</td></tr>";
		$c .= "<tr class=\"$class\">";
		$c .= "<td valign=top><img width=100 height=50 src=\"$imgurl\"></td>";
		$c .= "<td valign=top>$ns</td>";
#		$c .= "<a target=\"_blank\" href=\"http://$PROFILES{$ns}->[0]?_sandbox=1\">STAGING</a> |";
#		$c .= "<a target=\"_blank\" href=\"http://$PROFILES{$ns}->[0]?multivarsite=A&_sandbox=0\">Site-A</a>";
#		$c .= " | ";
#		$c .= "<a target=\"_blank\" href=\"http://$PROFILES{$ns}->[0]?multivarsite=B&_sandbox=0\">Site-B</a>";
#		$c .= "</td>";
#		if ($ALLOW_EDIT) {
#			$c .= "<td align=center><a href=\"/biz/setup/builder?PROFILE=$ns\">EDIT</a></td>";
#			}
#		else {
#			$c .= "<td>-</td>";
#			}
		$c .= "<td valign=top>";
		foreach my $set (@{$PROFILES{$ns}}) {
			my ($domainname,$prt) = @{$set};
			$c .= qq~<div><button class="minibutton" onClick="changeDomain('$domainname',$prt); return false;">Use Domain: $domainname ($prt)</button></div>~;
			}
		$c .= "</td>";
		# $c .= "<td align=center><a href=\"/biz/sites/index.cgi?VERB=REAUTH-PROFILES&PRT=$nsref->{'prt:id'}\">$nsref->{'prt:id'}</a></td>";
		$c .= "</tr>";

		$i++;
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'profiles.shtml';
	}



#if ($VERB eq 'SNAPSHOT-USE') {
#	my ($focusPRT) = $ZOOVY::cgiv->{'PRT'};
#
#	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$focusPRT);
#	$webdb->{'snapshot'} = $ZOOVY::cgiv->{'FILE'};
#	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$focusPRT);
#
#	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
#	&DBINFO::insert($udbh,'SNAPSHOT_SITES',{
#		USERNAME=>$USERNAME,
#		MID=>$MID,
#		PRT=>$focusPRT,
#		SNAPSHOT_FILE=>$ZOOVY::cgiv->{'FILE'},
#		CREATED_GMT=>time(),
#		},key=>['MID','PRT'],update=>1);
#	&DBINFO::db_user_close();
#	$VERB = 'SNAPSHOTS';
#	}
#
#if ($VERB eq 'SNAPSHOT-UNDO') {
#	my ($focusPRT) = $ZOOVY::cgiv->{'PRT'};
#	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,$focusPRT);
#	$webdb->{'snapshot'} = '';
#	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,$focusPRT);
#
#	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
#	my $pstmt = "delete from SNAPSHOT_SITES where MID=$MID and PRT=".int($focusPRT);
#	print STDERR $pstmt."\n";
#	$udbh->do($pstmt);
#	&DBINFO::db_user_close();
#	$VERB = 'SNAPSHOTS';
#	}
#
#
#
#if ($VERB eq 'SNAPSHOTS') {
#	$template_file = 'snapshots.shtml';
#
#	## Build a list of available files.
#	require LUSER::FILES;
#	my ($lf) = LUSER::FILES->new($USERNAME);
#	my $files = $lf->list('type'=>'SNAPSHOT');
#	my %prts = ();
#	foreach my $fileref (@{$files}) {
#		my $PRT = $fileref->{'%META'}->{'prt'};
#		if (not defined $prts{ $PRT }) {
#			$prts{ $PRT } = [];
#			}
#		push @{$prts{ $PRT }}, [ $fileref->{'TITLE'}, $fileref->{'FILENAME'}, $fileref->{'CREATED'}, $fileref->{'SIZE'} ];
#		}
#	
#	## Grab a list of active snapshots
##mysql> desc SNAPSHOT_SITES;
##+---------------+------------------+------+-----+---------+----------------+
##| Field         | Type             | Null | Key | Default | Extra          |
##+---------------+------------------+------+-----+---------+----------------+
##| ID            | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
##| USERNAME      | varchar(20)      | NO   |     | NULL    |                |
##| MID           | int(10) unsigned | NO   | MUL | 0       |                |
##| PRT           | int(10) unsigned | NO   |     | 0       |                |
##| SNAPSHOT_FILE | varchar(45)      | NO   |     | NULL    |                |
##| CREATED_GMT   | int(10) unsigned | NO   |     | 0       |                |
##+---------------+------------------+------+-----+---------+----------------+
##6 rows in set (0.00 sec)
#
#	my $udbh = &DBINFO::db_user_connect($USERNAME);
#	my @ACTIVEFILE = ();
#	my $pstmt = "select PRT,SNAPSHOT_FILE,CREATED_GMT from SNAPSHOT_SITES where MID=$MID";
#	my $sth = $udbh->prepare($pstmt);
#	$sth->execute();
#	while ( my ($PRT,$FILE,$CREATED) = $sth->fetchrow() ) {
#		$ACTIVEFILE[ $PRT ] = $FILE;
#		}
#	$sth->finish();
#	&DBINFO::db_user_close();
#
#	my $c = '';
#	foreach my $prttxt (@{ZWEBSITE::list_partitions($USERNAME)}) {
#		my ($PRT) = split(/:/,$prttxt);
#
#		$c .= "<tr class=\"zoovysub1header\"><td>Partition: $prttxt</td></tr>";
#		$c .= "<tr><td>";
#			
#		if (not defined $prts{$PRT}) {
#			$c .= "<i>There are no snapshots available for this partition.</i>";
#			}
#		else {
#			$c .= "<table>";
#			$c .= "<tr class=\"zoovysub2header\">";
#			$c .= "<td width=100></td>\n";
#			$c .= "<td width=300>File Title</td>\n";
#			$c .= "<td width=150>Created</td>\n";
#			$c .= "<td width=100>Size</td>\n";
#			$c .= "</tr>";
#			my $r = '';
#			my $found = 0;
#			foreach my $prtinfo (@{$prts{$PRT}}) {
#				my ($title,$filename,$created,$size) = @{$prtinfo};
#				$r = ($r eq 'r0')?'r1':'r0';
#				my $active = '';
#				if ($filename eq $ACTIVEFILE[$PRT]) { 
#					$r = 'rs'; $active = 'Active';  $found++;
#					}
#				else {
#					$active = qq~<input type="button" class="button" value=" Select " onClick="
#document.thisFrm.VERB.value='SNAPSHOT-USE';
#document.thisFrm.PRT.value='$PRT'; 
#document.thisFrm.FILE.value='$filename';
#document.thisFrm.submit();
#">~;
#					}
#				$c .= "<tr class=\"$r\"><td>$active</td><td>$title</td><td>$created</td><td>$size</td></tr>";
#				# $c .= "<tr><td colspan=3>".Dumper($prtinfo)."</td></tr>";
#				}
#
#			if ($found) {
#				## alls good.
#				$c .= qq~<tr><td><input type="button" class="button" value=" Remove Snapshot " onClick="
#document.thisFrm.VERB.value='SNAPSHOT-UNDO'; 
#document.thisFrm.PRT.value='$PRT'; 
#document.thisFrm.submit();
#"></td></tr>~;
#				}
#			elsif ((not $found) && ($ACTIVEFILE[$PRT] ne '')) {
#				$c .= "<tr><td colspan=4>OH NO! SELECTED SNAPSHOT FILE: $ACTIVEFILE[$PRT] COULD NOT BE LOCATED IN PRIVATE FILES!</td></tr>";
#				}
#			elsif (not $found) {
#				$c .= "<tr><td colspan=4>No active snapshot has been selected.</td></tr>";
#				}
#			
#
#			$c .= "</table>";
#			}
#
#		# $c .= '<pre>'.Dumper($prts{$prt}).'</pre>';
#
#		$c .= "</td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- PARTITIONS -->'} = $c;
#
#	}




my @TABS = (
	{ selected=>($VERB eq 'PROFILES')?1:0, name=>"Profiles", link=>"/biz/sites/index.cgi?VERB=PROFILES" },
	{ selected=>($VERB eq 'DOMAINS')?1:0, name=>"Domains", link=>"/biz/sites/index.cgi?VERB=DOMAINS" },
	{ selected=>($VERB eq 'PARTITIONS')?1:0, name=>"Partitions", link=>"/biz/sites/index.cgi?VERB=PARTITIONS" },
# 	{ selected=>($VERB eq 'SNAPSHOTS')?1:0, name=>"Snapshots", link=>"index.cgi?VERB=SNAPSHOTS" },
	{ selected=>($VERB eq 'CHECKUP')?1:0, name=>"Diagnostics", link=>"/biz/sites/index.cgi?VERB=CHECKUP" },
	);



&GTOOLS::output('*LU'=>$LU, msgs=>\@MSGS, bc=>\@BC, tabs=>\@TABS, file=>$template_file,header=>1 );
&DBINFO::db_zoovy_close();

&DBINFO::db_user_close();
