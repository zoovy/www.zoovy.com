#!/usr/bin/perl

use Storable;

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use SYNDICATION;
use GTOOLS;
use NAVCAT;
use strict;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
$GTOOLS::TAG{'<!-- GUID -->'} = time();

my $q = new CGI;
my $qtUSERNAME = $dbh->quote($USERNAME);
my $VERB = $q->param('VERB');

my $template_file = 'index.shtml';
if (($FLAGS !~ /,XSELL,/) && ($FLAGS !~ /,EBAY,/)) { 
	$template_file = 'deny.shtml'; $VERB = 'xx'; 
	}


my ($so) = SYNDICATION->new($USERNAME,"#$PRT",'OAS','AUTOCREATE'=>0);
if (defined $so) {
	$GTOOLS::TAG{'<!-- OS_USERID -->'} = $so->get('.os_userid');
	$GTOOLS::TAG{'<!-- OS_SCREENNAME -->'} = $so->get('.os_screenname');
	$GTOOLS::TAG{'<!-- STATUS_MSG -->'} = $so->statustxt();
	}

#my $USERREF = undef;
#my $pstmt = "select * from OVERSTOCK_USERS where MERCHANT=$qtUSERNAME";
#my $sth = $dbh->prepare($pstmt);
#$sth->execute();
#if ($sth->rows()>0) {
#  ($USERREF) = $sth->fetchrow_hashref();
#  if ($USERREF->{'OS_USERID'}==0) { $USERREF = undef; }
#  if ($USERREF->{'OS_SCREENNAME'} eq '') { $USERREF = undef; }
#  }
#$sth->finish();


##
##
##
if ((not defined $so) || ($VERB eq 'SIGNUP')) {
	## if they've changed usernames, then delete their old record.
#	$pstmt = "delete from OVERSTOCK_USERS where MID=$MID limit 1";
#	$dbh->do($pstmt);
	$VERB = 'SIGNUP';
	$template_file = 'signup.shtml'; 
	}
  
if ($VERB eq 'SAVE-CATEGORY') {
	my $changed = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths()) {
		next if (not defined $q->param('os-'.$safe));
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
      print STDERR "PRETTY: $pretty\n";
		$metaref->{'OS_CAT'} = $q->param('os-'.$safe);
      $NC->set($safe,metaref=>$metaref);
		}
	$NC->save();
	undef $NC;

	$VERB = 'CATEGORY';
	}




if ($VERB eq 'CATEGORY') {
	require DEFINITION::LIST;
	$template_file = 'category.shtml';

	my $catref = &DEFINITION::LIST::load_list('CATEGORIES','overstock','listing','TEXT');
	my %categories = ();
	$categories{''} = 'Not Set';
	## reverse the categories
	foreach my $k (keys %{$catref}) {
		$categories{$catref->{$k}} = $k;
		}

	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	my $bgcolor = '';
	my $c = '';
	foreach my $safe (sort $NC->paths()) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');

		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		# print STDERR "META: $meta\n";
		# next if (substr($pretty,0,1) eq '!'); 		# why not let them use hidden categories

		if ($bgcolor eq 'FFFFFF') { $bgcolor='DEDEDE'; } else { $bgcolor = 'FFFFFF'; }

		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,$safe)) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}
		$c .= "<tr bgcolor='$bgcolor'>";
		$c .= "<td nowrap>$name</td>";

		my $val = $metaref->{'OS_CAT'};
		$c .= "<td valign='top'><input name=\"os-$safe\" type=\"textbox\" size=\"6\" value=\"$val\"></td>";
		$c .= "<td valign='top'><a href=\"javascript:openWindow('/biz/syndication/overstock/catchooser.cgi?FQ=overstock.listing.CATEGORIES&V=os-$safe');\">[Choose]</a></td>";
		$c .= "<td valign='top'>".$categories{$val}."</td>";
		$c .= "</tr>\n";
		}
	undef $NC;
	if ($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	}


## BEGIN DEBUGGER
if ($VERB eq 'GOGO-DEBUG') {
	$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = $so->runDebug(type=>'product',TRACEPID=>$ZOOVY::cgiv->{'PID'});
	$VERB = 'DEBUG';
		}
if ($VERB eq 'DEBUG') {
	if ($GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} eq '') { 
		$GTOOLS::TAG{'<!-- DEBUG-OUTPUT -->'} = '<i>Please specify a product</i>'; 
		}
	$GTOOLS::TAG{'<!-- PID -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'PID'});
	$template_file = '_/syndication-debug.shtml';
	}
## END DEBUGGER


##
##
if ($VERB eq 'SAVE-CONFIG') {
	my $options = 0; 
	my $mode = int($q->param('MODE'));

	tie my %s, 'SYNDICATION', THIS=>$so;
	# $s{'.userid'} = $hashref->{'OS_USERID'};
	# $s{'.screenname'} = $hashref->{'OS_SCREENNAME'};
	# $s{'.is_dev'} = $hashref->{'DEV'};
	# $s{'.authkey'} = $hashref->{'AUTHKEY'};
	$s{'.syn_mode'} = $mode;
	$s{'.cfg_startbid'} = $q->param('STARTBID');
	$s{'.cfg_maxlistings'} = $q->param('MAXLISTINGS');
	$s{'.cfg_base_to_makeitmine'} = ($q->param('cfg_base_to_makeitmine'))?1:0;
	$s{'.cfg_send_shipping'} = ($q->param('cfg_send_shipping'))?1:0;
	untie(%s);
	$so->save();

#  $pstmt = "update OVERSTOCK_USERS set ERRORS=0,FEED_PROCESSED_GMT=0,CLOSED_PROCESSED_GMT=0,STATUS_MSG='Syndication settings updated',";
#  $pstmt .= "SYNDICATION_STARTBID=".$dbh->quote($q->param('STARTBID')).',';
#  $pstmt .= "SYNDICATION_OPTIONS=$options,SYNDICATION_MODE=$mode,";
#  $pstmt .= "SYNDICATION_MAXLISTINGS=".$dbh->quote($q->param('MAXLISTINGS')).',';
#  $pstmt .= "SYNDICATION_HTMLWIZ=".$dbh->quote('').' ';
#  $pstmt .= "where MID=$MID and MERCHANT=$qtUSERNAME";
#  print STDERR $pstmt."\n";
#  $dbh->do($pstmt);
  
#  $pstmt = "select * from OVERSTOCK_USERS where MERCHANT=$qtUSERNAME";
#  $sth = $dbh->prepare($pstmt);
#  $sth->execute();
#  if ($sth->rows()>0) { ($USERREF) = $sth->fetchrow_hashref(); } 
#  $sth->finish();

  $VERB = '';
  }


if ($VERB eq '') {

  $template_file = 'index.shtml';
	tie my %s, 'SYNDICATION', THIS=>$so;

	foreach my $i (0..5) { 
		$GTOOLS::TAG{'<!-- CHK_MODE_'.$i.' -->'} = ($s{'.syn_mode'}==$i)?'CHECKED':'';  
		}
	
	$GTOOLS::TAG{'<!-- CFG_BASE_TO_MAKEITMINE -->'} = ($s{'.cfg_base_to_makeitmine'})?'checked':'';
	$GTOOLS::TAG{'<!-- CFG_SEND_SHIPPING -->'} = ($s{'.cfg_send_shipping'})?'checked':'';
	$GTOOLS::TAG{'<!-- CFG_USE_EBAY -->'} = ($s{'.cfg_use_ebay'})?'checked':'';
	$GTOOLS::TAG{'<!-- MAXLISTINGS -->'} = $s{'.cfg_maxlistings'};   
	$GTOOLS::TAG{'<!-- STARTBID -->'} = $s{'.cfg_startbid'};
	untie(%s); 

  # $GTOOLS::TAG{'<!-- LAST_PROCESSED -->'} = &ZTOOLKIT::pretty_date($USERREF->{'FEED_PROCESSED_GMT'},1);   
  # $GTOOLS::TAG{'<!-- STATUS_MSG -->'} = $USERREF->{'STATUS_MSG'};
    
  #if ($USERREF->{'SYNDICATION_MODE'} == 0) {
  #  $GTOOLS::TAG{'<!-- WARNINGS -->'} = "<font color='red'>WARNING: Syndication is currently disabled.</font><br>";
  #  }
  # elsif ($USERREF->{'ERRORS'}>0) {
  #  $GTOOLS::TAG{'<!-- WARNINGS -->'} = "<font color='red'>WARNING: There have been $USERREF->{'ERRORS'} errors logged on your account.</font><br>";
  #  }
  #elsif ($USERREF->{'SYNDICATION_MAXLISTINGS'}==0) {
  #  $GTOOLS::TAG{'<!-- WARNINGS -->'} = "<font color='red'>WARNING: Syndication is not active because Max Listings is set to zero.</font><br>";
  #  }
  
  #$GTOOLS::TAG{'<!-- DEV -->'} = ($USERREF->{'DEV'})?'<font color="red">SANDBOX</font>':'';
#	my $selected = '';
#	$GTOOLS::TAG{'<!-- HTML_WIZARDS -->'} = "<option value=\"\">Use Profile</option>\n";
  }

###########################################################################################
##
## Manage
##
###########################################################################################
if ($VERB eq 'LOG') {
	$template_file = 'log.shtml';

#Tmysql> desc OVERSTOCK_LOGS;
#+-------------+------------------+------+-----+---------+----------------+
#| Field       | Type             | Null | Key | Default | Extra          |
#+-------------+------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned |      | PRI | NULL    | auto_increment |
#| MID         | int(11)          |      | MUL | 0       |                |
#| PRODUCT     | varchar(45)      |      |     |         |                |
#| OSID        | int(10) unsigned |      |     | 0       |                |
#| CREATED_GMT | int(10) unsigned |      |     | 0       |                |
#| MESSAGE     | varchar(60)      |      |     |         |                |
#+-------------+------------------+------+-----+---------+----------------+
#6 rows in set (0.01 sec)

	my $dbh = &DBINFO::db_zoovy_connect();
	my $pstmt = "select PRODUCT,OSID,MESSAGE from OVERSTOCK_LOGS where MID=$MID order by ID desc limit 0,1000";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my ($prod,$ebayid,$message) = $sth->fetchrow() ) {
		$c = "<tr><td><a target=_new href=\"http://www.zoovy.com/biz/product/index.cgi?VERB=QUICKSEARCH&VALUE=$prod\">$prod</a></td><td>$ebayid</td><td>$message</td></tr>\n".$c;
		}
	$GTOOLS::TAG{'<!-- LOG -->'} = "<tr><td><b>PRODUCT</b><td><b>OVERSTOCK ID</b></td><td><b>MESSAGE</b></td></tr>$c";
	$sth->finish();

	&DBINFO::db_zoovy_close();
	}

if ($VERB eq 'REPORTS') {
	$template_file = 'reports.shtml';
	}


##
##
##
&GTOOLS::output(
  title=>'Overstock Syndication',
  file=>$template_file,
  header=>1,
   'help'=>'#50592',
   'tabs'=>[
		{ name=>'Configuration',link=>'http://www.zoovy.com/biz/syndication/overstock','target'=>'_top', },
		{ name=>'Categories',link=>'http://www.zoovy.com/biz/syndication/overstock?VERB=CATEGORY','target'=>'_top', },
		{ name=>'Log',link=>'http://www.zoovy.com/biz/syndication/overstock?VERB=LOG','target'=>'_top', },
		{ name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"?VERB=DEBUG&PROFILE=#$PRT", },
#		{ name=>'Reports',link=>'http://www.zoovy.com/biz/syndication/overstock?VERB=REPORTS','target'=>'_top', },
      ],
   'bc'=>[
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Overstock Feeds',link=>'http://www.zoovy.com/biz/syndication/overstock','target'=>'_top', },
      ],
  );

&DBINFO::db_zoovy_close();