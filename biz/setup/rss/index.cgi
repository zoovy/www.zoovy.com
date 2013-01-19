#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require LUSER;
use strict;


my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my @MSGS = ();

my $template_file = '';
my @BC = (
	{ link=>'/biz/setup', name=>'Setup' },
	{ link=>'/biz/setup/rss', name=>'RSS Feeds' },
	);


my $udbh = &DBINFO::db_user_connect($USERNAME);

my $VERB = $ZOOVY::cgiv->{'VERB'};
my $ID = $ZOOVY::cgiv->{'feed_code'};
if ($ID eq '') { $ID = $ZOOVY::cgiv->{'ID'}; }



#mysql> desc CAMPAIGNS;
#+--------------------+--------------------------------------------------------+------+-----+---------+----------------+
#| Field              | Type                                                   | Null | Key | Default | Extra          |
#+--------------------+--------------------------------------------------------+------+-----+---------+----------------+
#| ID                 | int(11)                                                | NO   | PRI | NULL    | auto_increment |
#| CPG_CODE           | varchar(6)                                             | NO   |     | NULL    |                |
#| CPG_TYPE           | enum('NEWSLETTER','RSS','PRINT','SMS','')              | NO   |     | NULL    |                |
#| MERCHANT           | varchar(20)                                            | NO   |     | NULL    |                |
#| MID                | int(10) unsigned                                       | NO   | MUL | 0       |                |
#| CREATED_GMT        | int(11)                                                | NO   |     | 0       |                |
#| NAME               | varchar(30)                                            | NO   |     | NULL    |                |
#| SUBJECT            | varchar(100)                                           | NO   |     | NULL    |                |
#| SENDER             | varchar(65)                                            | NO   |     | NULL    |                |
#| DATA               | mediumtext                                             | NO   |     | NULL    |                |
#| STATUS             | enum('PENDING','APPROVED','QUEUED','FINISHED','ERROR') | YES  | MUL | PENDING |                |
#| TESTED             | int(11)                                                | YES  |     | NULL    |                |
#| STARTS_GMT         | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_QUEUED        | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_SENT          | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_OPENED        | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_BOUNCED       | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_CLICKED       | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_PURCHASED     | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_TOTAL_SALES   | int(10) unsigned                                       | NO   |     | 0       |                |
#| STAT_UNSUBSCRIBED  | int(10) unsigned                                       | NO   |     | 0       |                |
#| RECIPIENT          | varchar(20)                                            | YES  |     | NULL    |                |
#| SCHEDULE           | varchar(10)                                            | NO   |     | NULL    |                |
#| SCHEDULE_COUNTDOWN | tinyint(4)                                             | NO   |     | 0       |                |
#| PROFILE            | varchar(10)                                            | NO   |     | NULL    |                |
#| PRT                | smallint(5) unsigned                                   | NO   |     | 0       |                |
#+--------------------+--------------------------------------------------------+------+-----+---------+----------------+
#26 rows in set (0.03 sec)

if ($VERB eq 'SAVE') {
	
	push @MSGS, "SUCCESS|+Changes have been saved";

	my $feed_code = uc($ZOOVY::cgiv->{'feed_code'});
	$feed_code =~ s/[^A-Z0-9]+//gs; 	# strip non-alpha num
	if ($feed_code eq '') {
		## cheaphack!
		$feed_code = substr(time(),-6);
		}
	
	my %info = ();
	$info{'title'} = $ZOOVY::cgiv->{'feed_title'};
	$info{'link'} = $ZOOVY::cgiv->{'feed_link'};
	$info{'link_override'} = (defined $ZOOVY::cgiv->{'feed_link_override'})?1:0;
	$info{'subject'} = $ZOOVY::cgiv->{'feed_subject'};
	$info{'max_products'} = $ZOOVY::cgiv->{'max_products'};
	$info{'cycle_interval'} = $ZOOVY::cgiv->{'cycle_interval'};
	$info{'schedule'} = $ZOOVY::cgiv->{'schedule'};
	$info{'profile'} = $ZOOVY::cgiv->{'profile'};
	$info{'list'} = $ZOOVY::cgiv->{'list'};
	$info{'image_h'} = $ZOOVY::cgiv->{'image_h'};
	$info{'image_w'} = $ZOOVY::cgiv->{'image_w'};
	$info{'translation'} = $ZOOVY::cgiv->{'translation'};

	my $COUPON = sprintf("%s",$ZOOVY::cgiv->{'coupon'});

	my $pstmt = &DBINFO::insert($udbh,'CAMPAIGNS',{
		USERNAME=>$USERNAME,
		MID=>$MID,
		CREATED_GMT=>time(),
		CPG_CODE=>$feed_code, CPG_TYPE=>'RSS',
		NAME=>$ZOOVY::cgiv->{'feed_title'},
		SUBJECT=>$ZOOVY::cgiv->{'feed_subject'},
		# SCHEDULE=>$ZOOVY::cgiv->{'schedule'},
		COUPON=>$COUPON,
		PROFILE=>$ZOOVY::cgiv->{'profile'},
		PRT=>$PRT,
		DATA=>&ZTOOLKIT::buildparams(\%info),
		},debug=>2,key=>['MID','CPG_CODE','CPG_TYPE']);
	print STDERR $pstmt."\n";
	$udbh->do($pstmt);

	$ZOOVY::cgiv->{'ID'} = $feed_code;

	$VERB = 'EDIT';
	}



if ($VERB eq 'EDIT') {
	my $pstmt = "select * from CAMPAIGNS where CPG_TYPE='RSS' and MID=$MID and CPG_CODE=".$udbh->quote($ID);
	my $sth = $udbh->prepare($pstmt);	
	$sth->execute();
	my ($dbinfo) = $sth->fetchrow_hashref();
	$sth->finish();

	my ($info) = &ZTOOLKIT::parseparams($dbinfo->{'DATA'});

	$ZOOVY::cgiv->{'image_h'} = $info->{'image_h'};
	$ZOOVY::cgiv->{'image_w'} = $info->{'image_w'};
	$ZOOVY::cgiv->{'feed_code'} = $ID;
	$ZOOVY::cgiv->{'feed_title'} = $info->{'title'};
	$ZOOVY::cgiv->{'feed_link'} = $info->{'link'};
	$ZOOVY::cgiv->{'feed_link_override'} = $info->{'link_override'};
	$ZOOVY::cgiv->{'feed_subject'} = $info->{'subject'};
	$ZOOVY::cgiv->{'max_products'} = $info->{'max_products'};
	$ZOOVY::cgiv->{'cycle_interval'} = $info->{'cycle_interval'};
	$ZOOVY::cgiv->{'schedule'} = $dbinfo->{'SCHEDULE'};
	$ZOOVY::cgiv->{'coupon'} = $dbinfo->{'COUPON'};
	$ZOOVY::cgiv->{'profile'} = $dbinfo->{'PROFILE'};
	$ZOOVY::cgiv->{'list'} = $info->{'list'};
	$ZOOVY::cgiv->{'translation'} = $info->{'translation'};

	$LU->log('SETUP.RSS',"Edited Campaign $ID","INFO");
	}


if ($VERB eq 'NUKE') {
	print STDERR "VERB:$VERB ID:$ID\n";
	my $pstmt = "delete from CAMPAIGNS where CPG_TYPE='RSS' and MID=$MID and PRT=$PRT and CPG_CODE=".$udbh->quote($ID);
	print STDERR "pstmt:$pstmt\n";
	$udbh->do($pstmt);
	$LU->log('SETUP.RSS',"Deleted Campaign $ID","INFO");
	$VERB = '';
	}

if ($VERB eq '') {
	my $pstmt = "select * from CAMPAIGNS where CPG_TYPE='RSS' and MID=$MID and PRT=$PRT order by CREATED_GMT";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $r = '';
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class='$r'>";
		$c .= "<td>#$hashref->{'ID'}</td>";
		$c .= "<td>$hashref->{'CPG_CODE'}</td>";
		$c .= "<td>$hashref->{'TITLE'}</td>";
		$c .= "<td>";
		$c .= " <a href=\"/biz/setup/rss/index.cgi?VERB=EDIT&ID=$hashref->{'CPG_CODE'}\">[Edit]</a> ";
		# $c .= " <a href=\"index.cgi?VERB=NUKE&ID=$hashref->{'CPG_CODE'}\">[Delete]</a> ";
		$c .= "</td>";
		$c .= "<td><a target=\"_rss\" href=\"http://static.zoovy.com/rss/$USERNAME/$hashref->{'CPG_CODE'}.xml\">[Link]</a></td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($hashref->{'CREATED_GMT'},1)."</td>";
		$c .= "</tr>";
		$c .= "<tr class='$r'>";
		$c .= "<td colspan=5>Clicks: $hashref->{'STAT_CLICKED'} Orders: $hashref->{'STAT_PURCHASED'}  Gross Subtotals: $hashref->{'STAT_TOTAL_SALES'}</td>";
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td><i>No Feeds currently configured - proceed to the Create Feed tab</i></td></tr>";
		}
	$sth->finish();	
	$GTOOLS::TAG{'<!-- EXISTING_FEEDS -->'} = $c;

	$template_file = 'index.shtml';
	}


##
## Blah.. 
##
if (($VERB eq 'CREATE') || ($VERB eq 'EDIT')) {

	$GTOOLS::TAG{'<!-- BUTTON -->'} = '';
	if ($VERB eq 'CREATE') {
		$GTOOLS::TAG{'<!-- BUTTON -->'} .= q~<input type="submit" value=" Create " class="button">~;
		}
	else {
		$GTOOLS::TAG{'<!-- BUTTON -->'} .= q~<input type="submit" value=" Save " class="button">~;
		$GTOOLS::TAG{'<!-- BUTTON -->'} .= qq~&nbsp; <button class="button" onClick="navigateTo('/biz/setup/rss/index.cgi?VERB=NUKE&ID=$ID');">Delete</button>~;
		}

	my $c = '';	
	$GTOOLS::TAG{'<!-- image_h -->'} = ($ZOOVY::cgiv->{'image_h'})?&ZOOVY::incode($ZOOVY::cgiv->{'image_h'}):'75';
	$GTOOLS::TAG{'<!-- image_w -->'} = ($ZOOVY::cgiv->{'image_w'})?&ZOOVY::incode($ZOOVY::cgiv->{'image_w'}):'75';
	$GTOOLS::TAG{'<!-- FEED_CODE -->'} = ($ZOOVY::cgiv->{'feed_code'})?&ZOOVY::incode($ZOOVY::cgiv->{'feed_code'}):'';
	$GTOOLS::TAG{'<!-- FEED_TITLE -->'} = ($ZOOVY::cgiv->{'feed_title'})?&ZOOVY::incode($ZOOVY::cgiv->{'feed_title'}):'';
	$GTOOLS::TAG{'<!-- FEED_LINK -->'} = ($ZOOVY::cgiv->{'feed_link'})?&ZOOVY::incode($ZOOVY::cgiv->{'feed_link'}):'';
	$GTOOLS::TAG{'<!-- CHK_FEED_LINK_OVERRIDE -->'} = ($ZOOVY::cgiv->{'feed_link_override'})?'checked':'';
	$GTOOLS::TAG{'<!-- FEED_SUBJECT -->'} = ($ZOOVY::cgiv->{'feed_subject'})?&ZOOVY::incode($ZOOVY::cgiv->{'feed_subject'}):'';

	my $translation = ($ZOOVY::cgiv->{'translation'})?&ZOOVY::incode($ZOOVY::cgiv->{'translation'}):'';
	foreach my $t ('RAW','HTMLSTRIP','WIKISTRIP','WIKI2HTML','WIKI2HTMLIMG','LEGACYV1') {
		$GTOOLS::TAG{"<!-- TRANSLATION_$t -->"} = ($translation eq $t)?'selected':'';
		}
	# $GTOOLS::TAG{'<!-- MESSAGE -->'} = "Translation is: $translation";

	$c = '';
	for my $i (-1,1,2,3,4,5,10,15,20,25) { 
		my $selected = (int($ZOOVY::cgiv->{'max_products'}) ==$i)?' selected ':'';
		$c .= "<option $selected value=\"$i\">".(($i==-1)?'unlimited':$i)."</option>\n"; 
		}
	$GTOOLS::TAG{'<!-- MAX_PRODUCTS -->'} = $c;


	$c = '';
	for my $i (-1,1,2,3,4,5,6,7,8,9,10,15,20,25,30,60,120,360,1440) { 
		my $selected = ($ZOOVY::cgiv->{'cycle_interval'}==$i)?' selected ':'';
		$c .= "<option $selected value=\"$i\">".(($i==-1)?'Never':$i)."</option>\n"; 
		}
	$GTOOLS::TAG{'<!-- CYCLE_INTERVAL -->'} = $c;

	require WHOLESALE;
	$c = '';
	for my $s ('',@{&WHOLESALE::list_schedules($USERNAME)}) { 
		my $selected = ($ZOOVY::cgiv->{'schedule'} eq $s)?' selected ':'';
		$c .= "<option $selected value=\"$s\">".(($s eq '')?'-- None --':$s)."</option>\n"; 
		}
	$GTOOLS::TAG{'<!-- SCHEDULES -->'} = $c;
	$GTOOLS::TAG{'<!-- COUPON -->'} = ($ZOOVY::cgiv->{'COUPON'})?&ZOOVY::incode($ZOOVY::cgiv->{'COUPON'}):'';


	$c = '';
	require DOMAIN::TOOLS;
	my ($profiles) = DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	foreach my $k (sort keys %{$profiles}) {
		my $selected = ($ZOOVY::cgiv->{'profile'} eq $k)?' selected ':'';
		$c .= "<option $selected value=\"$k\">$k $profiles->{$k}</option>\n"; 
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;

	$c = '';
	require NAVCAT;
	my ($nc) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $nc->paths()) {
		next if (substr($safe,0,1) ne '$');	
		my ($pretty) = $nc->get($safe);
		if ($pretty eq '') { $pretty = "Untitled $safe"; }
		my $selected = ($ZOOVY::cgiv->{'list'} eq $safe)?' selected ':'';
		$c .= "<option $selected value=\"$safe\">$pretty</option>\n";
		}

	if ($c eq '') {
		$c .= "<option value=\"\">-- no lists configured --</option>";
		}

	$GTOOLS::TAG{'<!-- LISTS -->'} = $c;
	$template_file = 'create.shtml';
	}

my @TABS = (
	{ link=>'/biz/setup/rss/index.cgi?VERB=', name=>'RSS Feeds', selected=>($VERB eq '')?1:0, },
	{ link=>'/biz/setup/rss/index.cgi?VERB=CREATE', name=>'Create New', selected=>($VERB eq 'CREATE')?1:0, },
	);


$GTOOLS::TAG{'<!-- ID -->'} = $ID;

&GTOOLS::output('*LU'=>$LU, msgs=>\@MSGS, file=>$template_file, header=>1, tabs=>\@TABS, bc=>\@BC );
&DBINFO::db_user_close();


1;
