#!/usr/bin/perl

#
#
#

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use DOMAIN::TOOLS;
use SYNDICATION;

use strict;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my @TABS = ();



my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'buySAFE bonded shopping',link=>'http://www.zoovy.com/biz/syndication/buysafeshopping','target'=>'_top', },
		);


if ($VERB eq 'ENABLE') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
	$so->set('.bsstoken',$ZOOVY::cgiv->{'TOKEN'});
	$so->set('.domain',$ZOOVY::cgiv->{'DOMAIN'});
	$so->set('IS_ACTIVE',time());
	$so->save();
	$VERB = 'EDIT';
	}


if ($VERB eq 'SAVE') {

	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
	tie my %s, 'SYNDICATION', THIS=>$so;

	$s{'IS_ACTIVE'} = (defined $ZOOVY::cgiv->{'IS_ACTIVE'})?time():0;
	$s{'.schedule'} = undef;
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'SCHEDULE'};
      }

	my $ERROR = '';
	#if ($s{'.host'} eq '') { $ERROR = "FTP Server is required.<br>"; }
	#if ($s{'.user'} eq '') { $ERROR .= "FTP Username is required.<br>"; }
	#if ($s{'.pass'} eq '') { $ERROR .= "FTP Password is required.<br>"; }

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$so->save();
		#&ZOOVY::savemerchantns_attrib($USERNAME,$PROFILE,"buysafe:enable",${'.enable'});
		&ZOOVY::savemerchantns_attrib($USERNAME,$PROFILE,"buysafe:enable",1);
		# &ZWEBSITE::save_website_attrib($USERNAME,'buysafe',$^T);
		}

	$VERB  = 'EDIT';
	}





if ($VERB eq 'SAVE-CATEGORIES') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);

		$metaref->{'BSS'} = (defined $ZOOVY::cgiv->{'navcat-'.$safe})?1:0;
		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save();
	undef $NC;
	$GTOOLS::TAG{'<!-- MSG -->'} = "<font color='blue'>Successfully saved buySAFE bonded shopping categories.</font><br>";
	$VERB = 'CATEGORIES';
	}


if ($VERB eq '') {
	my $dbh = &DBINFO::db_zoovy_connect();
	my $pstmt = "select HOST_TYPE, PROFILE, DOMAIN, BUYSAFE_TOKEN from DOMAINS where MID=$MID /* $USERNAME */ and PRT=$PRT order by PROFILE";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $cnt = 0;
	my %PROFILES = ();
	while ( my ($HOST_TYPE,$PROFILE,$DOMAIN,$TOKEN) = $sth->fetchrow() ) {
		next if (($HOST_TYPE ne 'SPECIALTY') && ($HOST_TYPE ne 'PRIMARY'));
		next if ($TOKEN eq '');
		if ($PROFILE eq '') { $PROFILE = 'DEFAULT'; }
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		my ($s) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
		
		my $link = "<a href=\"/biz/syndication/buysafeshopping/index.cgi?VERB=EDIT&PROFILE=$PROFILE\">EDIT</a>";
		my $status = '';
		if (($s->get('.bsstoken') ne $TOKEN) || (not $s->get('IS_ACTIVE'))) {
			$status = "Not Enabled";
			$link = "<a href=\"/biz/syndication/buysafeshopping/index.cgi?VERB=ENABLE&PROFILE=$PROFILE&TOKEN=$TOKEN&DOMAIN=$DOMAIN\">ENABLE</a>";
			}
		else {
			$status = $s->statustxt();
			}
		$c .= "<td class=\"$class\">";
		$c .= "<b>$PROFILE =&gt; $DOMAIN ($link)</b><br>";
		$c .= "&nbsp;&nbsp;&nbsp; $status<br>";
		if (defined $PROFILES{$PROFILE}) {
			$c .= "&nbsp;&nbsp&nbsp; <font color='red'>WARNING: PROFILE $PROFILE is shared with DOMAIN $PROFILES{$PROFILE} -- please correct.</font><br>";
			}
		$PROFILES{$PROFILE} = $DOMAIN;
		$c .= "</td>";		
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td><i>Sorry but you have no buySAFE enabled domains on this partition.</i></td></tr>";
		}
	$sth->finish();
	&DBINFO::db_zoovy_close();


#	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME);
#	my $c = '';
#	my $cnt = 0;
#	foreach my $ns (sort keys %{$profref}) {
#		my $class = ($cnt++%2)?'r0':'r1';
#		$c .= "<tr><td class=\"$class\"><b>$ns =&gt; $profref->{$ns} (<a href=\"/biz/syndication/buysafeshopping/index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>)</td></tr>";		
#		my ($s) = SYNDICATION->new($USERNAME,$ns,'BSS');
#		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
#		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}


if ($PROFILE ne '') {
	push @TABS, { selected=>($VERB eq 'EDIT')?1:0, 'name'=>'Config', 'link'=>'/biz/syndication/buysafeshopping/index.cgi?VERB=EDIT&PROFILE='.$PROFILE };
	push @TABS, { selected=>($VERB eq 'CATEGORIES')?1:0, 'name'=>'Categories', 'link'=>'/biz/syndication/buysafeshopping/index.cgi?VERB=CATEGORIES&PROFILE='.$PROFILE };
	push @BC, { name=>'Profile: '.$PROFILE };
	push @BC, { name=>($VERB eq 'EDIT')?'Config':'Categories' };
	}


if ($VERB eq 'EDIT') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
	tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- BSSTOKEN -->'} = $s{'.bsstoken'};
	$GTOOLS::TAG{'<!-- DOMAIN -->'} = $s{'.domain'};
	$GTOOLS::TAG{'<!-- CHK_IS_ACTIVE -->'} = ($s{'IS_ACTIVE'})?'checked':'';
	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	$GTOOLS::TAG{'<!-- FILENAME -->'} = "http://static.zoovy.com/merchant/$USERNAME/$PROFILE-bss.txt";

	if ($FLAGS =~ /,WS,/) {
  		my $c = '<option value="">Not Set</option>';
	   require WHOLESALE;
		foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
   	   $c .= "<option ".(($s{'.schedule'} eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
	      }
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;
		}
	else {
		$s{'.schedule'} = '';
 		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = '<option value="">Not Available</option>';
	   }

	$template_file = 'edit.shtml';
	}


if ($VERB eq 'LOGS') {
	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }


if ($VERB eq 'CATEGORIES') {

	require SYNDICATION::CATEGORIES;
	my ($CDS) = SYNDICATION::CATEGORIES::CDSLoad('BSS');

	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'BSS');
	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();

	my $c = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);

	my ($cdsflat) = SYNDICATION::CATEGORIES::CDSFlatten($CDS);

	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (substr($pretty,0,1) eq '!');
	
		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,substr($safe,1))) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}

		my $val = $metaref->{'BSS'};
		if ((not defined $val) || ($val == 0)) { $val = 0; }
		$c .= "<tr>";

		my $checked = ($val)?'checked':'';
		$c .= qq~<td nowrap><input $checked type="checkbox" name="navcat-$safe"></td>~;
		$c .= "<td nowrap>$name</td>";


		$c .= qq~<td nowrap><span id="txt!navcat-$safe">$pretty</span></td>~;
		$c .= "</tr>\n";
		}
	if	($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;

	$template_file = 'categories.shtml';
	}

&GTOOLS::output(
   'title'=>'buySAFE bonded shopping Product Syndication',
   'file'=>$template_file,
	'head'=>qq~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>~,
   'header'=>'1',
	'js'=>1+2,
   'help'=>'#51002',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

