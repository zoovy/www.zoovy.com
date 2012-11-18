#!/usr/bin/perl

use strict;
use POSIX qw (strftime);
use Date::Parse;
use YAML::Syck;
use Data::Dumper;


#if ($ENV{'HTTP_ORIGIN'} eq '') {
#	## this is for JT
#	}
#elsif ($ENV{'HTTP_REFERER'} !~ /^https?\:\/\/.*?\/biz\/app\/(admin|index)\.html/) {
#	print STDERR Dumper($ENV{'HTTP_REFERER'});
#	print "Location: /biz/app/admin.html\n\n";
#	exit;
#	}

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require DBINFO;
require ZTOOLKIT;
require ZTOOLKIT::SECUREKEY;
require ZWEBSITE;
require TODO;
require SUPPORT;

require LUSER;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT,$RESELLER) = $LU->authinfo();
if ($RESELLER eq '') { $RESELLER = 'ZOOVY'; }
if ($MID<=0) { exit; }
my @ERRORTASKS = ();

print STDERR "USERNAME:$USERNAME\n";
$GTOOLS::TAG{'<!-- MERCHANT -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- USERNAME -->'} = $LUSERNAME;

my $host = &ZOOVY::servername();

my $VERB = defined($ZOOVY::cgiv->{'VERB'}) ? $ZOOVY::cgiv->{'VERB'} : '';
my $template_file = ''; 


my ($cluster) = &ZOOVY::resolve_cluster($USERNAME);
my $NOUN = ($LU->is_anycom())?'anyCommerce':'Zoovy';
my $TITLE = "Logged in to $NOUN connected to server '$host' on cluster '$cluster'";

my $todo = TODO->new($USERNAME,LUSER=>$LUSERNAME);
if ($VERB eq 'DISMISS') {
	$todo->delete(int($ZOOVY::cgiv->{'ID'}));
	$VERB = '';
	}

if ($VERB eq 'DISABLE-TODO') {
	$LU->set('todo.setup',0);
	$LU->save();
	$VERB = '';
	}

if ($VERB eq 'DISABLE-TODO-TASK') {
	$todo->delete(0,class=>'SETUP',group=>$ZOOVY::cgiv->{'group'});
	$todo->save();
   $VERB = 'TODO';
	}



if ($VERB eq '') { 
	$VERB = 'NEWS'; 
	my $ts = $LU->get('todo.setup');
	if (not defined $ts) { $ts = 0; }
	if ($ts>0) { $VERB = 'TODO'; }
	elsif ($FLAGS =~ /,NEWBIE,/) { $VERB = 'WELCOME'; }
#		## MY TODO BOX
	}

my $HEAD = '';

if (($FLAGS eq '') || ($FLAGS =~ /TRIAL/) || ($FLAGS !~ /BASIC/)) {
	require ZACCOUNT;
	$FLAGS = &ZACCOUNT::BUILD_FLAG_CACHE($USERNAME);
	}


#if ($USERNAME eq 'brian') {
#	print "Location: trial.cgi\n\n"; exit;
#	}

my @BC = ();
my @TABS = ();

if (($FLAGS =~ /,TRIAL,/) || ($USERNAME eq 'brian')) {
	push @TABS, { selected=>($VERB eq 'WELCOME')?1:0, link=>"index.cgi?VERB=WELCOME", name=>"Welcome" };
	}
push @TABS, { selected=>($VERB eq 'NEWS')?1:0, link=>"index.cgi?VERB=NEWS", name=>"Recent News" };
#push @TABS, { selected=>($VERB eq 'TODO')?1:0, link=>"index.cgi?VERB=TODO", name=>"Tutorials" };
#push @TABS, { selected=>($VERB eq 'LIBRARY')?1:0, link=>"index.cgi?VERB=LIBRARY", name=>"Video Library" };

push @BC, { name=>'Home', };
push @BC, { name=>'Recent News', };


if ($VERB eq 'WELCOME') {
	$template_file = 'index-welcome.shtml';
#	$HEAD = q~
#<!--
#<script type="text/javascript" src="//e1h11.simplecdn.net/videosink.zoovy//msol-splash/swfobject.js"></script>
#<script type="text/javascript" src="//e1h11.simplecdn.net/videosink.zoovy//msol-splash/msol-splash.js"></script>
#-->
#~;
	}

##
##
##
#if ($VERB eq 'LIBRARY') {
#	$template_file = 'index-library.shtml';
#
#	my @rows = ();
#	my $zdbh = &DBINFO::db_zoovy_connect();
#	my $pstmt = "select * from WEBDOC_VIDEOS where APPROVED_GMT>0 order by ID";
#	my $sth = $zdbh->prepare($pstmt);
#	$sth->execute();
#	my %VIDEOS = ();
#	while ( my $vidref = $sth->fetchrow_hashref() ) {
#		# http://upload.wikimedia.org/wikipedia/commons/3/32/Video_icon_2.png
#		my $html = '';
#		$html .= "<tr><td>";
#		$html .= qq~<b><a target="_video" href="http://e1h11.simplecdn.net/videosink.zoovy/$vidref->{'FILENAME'}/index.html">~;
#		$html .= qq~$vidref->{'TITLE'}</a><b><br>~;
#		my $created = &ZTOOLKIT::pretty_date(&ZTOOLKIT::mysql_to_unixtime($vidref->{'CREATED'}),-1);
#		$html .= qq~<div class='hint'>Created: $created</div>~;
#		$html .= "</td></tr>";
#
#		if ($vidref->{'LEVEL'} eq 'BEGINNER') {
#			$GTOOLS::TAG{'<!-- BEGINNER -->'} .= $html;
#			}
#		elsif ($vidref->{'LEVEL'} eq 'INTERMEDIATE') {
#			$GTOOLS::TAG{'<!-- INTERMEDIATE -->'} .= $html;
#			}
#		else {
#			$GTOOLS::TAG{'<!-- ADVANCED -->'} .= $html;
#			}
#		
#		push @rows, [ 
#				# qq~&nbsp;<a target="_video" href="http://videosink-s3.simplecdn.net/$video/index.html">[View]</a>~, 
#				];
#		}
#	$sth->finish();
#	&DBINFO::db_zoovy_close();
#
#	require GTOOLS::Table;
#	$GTOOLS::TAG{'<!-- LIBRARY -->'} = &GTOOLS::Table::buildTable([
#		{ 'width'=>50, title=>' ' },
#		{ 'width'=>100, title=>'Level' },
#		{ 'width'=>500, title=>'Description' },
#		{ 'width'=>100, title=>'Created' },
#		], \@rows,
#		height=>150
#		);
#	
#	}
#
##
## No more TODO panels
##
if ($VERB eq 'TODO') { $VERB = 'NEWS'; }

##
##
##
if ($VERB eq 'NEWS') {

	my $c = '';
	foreach my $task (@{$todo->list()}) {
		next if ($task->{'COMPLETED_GMT'});

		if (($task->{'PRIORITY'}==1) && ($task->{'CLASS'} ne 'TODO')) {
			## always show any PRIORITY 1 non TODO task as an error/priority message
			push @ERRORTASKS, $task;
			}
		elsif ($task->{'CLASS'} eq 'ERROR') {
			## any errors, regardless of priority.
			push @ERRORTASKS, $task;
			}
		else {
			$c .= "<tr><td>";
			if ($task->{'LINK'} ne '') { $c .= "<a target=\"_top\" href=\"$task->{'LINK'}\">"; }
			$c .= "<div>$task->{'TITLE'}</div>";
			if ($task->{'LINK'} eq '') { $c .= "<div class='hint'>$task->{'DETAIL'}</div>"; }
			if ($task->{'LINK'} ne '') { $c .= "</a>"; }
			$c .= "</td></tr>";
			}
		}
	if ($c eq '') { $c .= "<tr><td><i>Empty</i></td></tr>"; }
	$GTOOLS::TAG{'<!-- TODOLIST -->'} = $c;
	}


##
##
##
if ($VERB eq 'TODO') {
	$template_file = 'index-todo.shtml';
	my $c = '';	


	my @PANELS = ();

	my @TASKS = @{$todo->list(sort=>'PRIORITY',class=>'SETUP',sorttype=>'numerically')};
	foreach my $task (@TASKS) {
		use Storable;
		if ($task->{'PANEL'} ne '') {
			## check out the panels files in /httpd/static/todo/xxxx.bin
			my $panel = undef;
			eval { $panel = retrieve "/httpd/static/todo/$task->{'PANEL'}.bin"; };
			if (not defined $panel) {
				$panel = { id=>$task->{'PANEL'}, txt=>"error: $task->{'PANEL'}", detail=>"Could not load panel $task->{'PANEL'}" };
				}
			$panel->{'%TASK'} = $task;
			push @PANELS, $panel;
			}
		}


	if (scalar(@PANELS)==0) {
		push @PANELS, { id=>'nothing', txt=>'.......', disable_remove=>1, title=>'Nothing Available', detail=>'You have no tutorial oriented tasks that need to be completed.', };
		}

	if (scalar(@PANELS)>0) {
		my $focus = $ZOOVY::cgiv->{'focus'};
		if ($focus ne '') {
			## handle focuson .. (sometimes the panel id doesn't match the focus 
			my $found = 0;
			foreach my $task (@PANELS) {
				next if ($found);
				if ($focus eq $task->{'id'}) { $found++; }
				elsif ($focus eq $task->{'focuson'}) { $focus = $task->{'id'}; $found++; }
				}
			if (not $found) { $focus = ''; }
			}
		elsif ($ZOOVY::cgiv->{'focusfrom'} ne '') {
			## handle "coming from" situations
			my $i = 0;
			foreach my $task (@PANELS) {
				## if we are receiving 'focusfrom' a specific id, then go to the next id.
				if ($task->{'id'} eq $ZOOVY::cgiv->{'focusfrom'}) { $focus = $PANELS[$i+1]->{'id'}; }
				$i++;
				}
			}
		if ($focus eq '') { $focus = $PANELS[0]->{'id'}; }  ## default to welcome!
		my $i = 1;
		my $c = '';
		$GTOOLS::TAG{'<!-- NEXT_BUTTON -->'} = '';
		my $allow_remove = ($LU->get('todo.setup')==0)?1:0;
		# $allow_remove = 1;
		foreach my $task (@PANELS) {
			if ($focus ne $task->{'id'}) {
				## Non-Focused
				$c .= qq~<a href="/biz/index.pl?VERB=TODO&focus=$task->{'id'}" id="tab_button">$i.  $task->{'txt'}</a>~;
				}
			else {
				## Active/Focused Tab
				$c .= qq~<div class="active_tab">$i. $task->{'txt'}</div>~;
				$GTOOLS::TAG{'<!-- TODO_TITLE -->'} = $task->{'title'};
				$GTOOLS::TAG{'<!-- TODO_DETAIL -->'} = $task->{'detail'};
				$GTOOLS::TAG{'<!-- NEXT_BUTTON -->'} = '';
				if (($ZOOVY::cgiv->{'splash'}) && ($task->{'splash'} ne '') && ($ENV{'REMOTE_ADDR'} =~ /^192\.168\./)) {
					## on newdev just shoot the splash.
					# $GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = "http://videosink-s3.simplecdn.net/$task->{'splash'}";
					$GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = "http://e1h11.simplecdn.net/videosink.zoovy/$task->{'splash'}";
					}
				elsif ($task->{'iframesrc'} ne '') {
					## this will load and override video
					$GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = $task->{'iframesrc'};
					}
				elsif ($task->{'video'} ne '') {
					# $GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = "http://videosink-s3.simplecdn.net/$task->{'video'}/index.html";
					$GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = "http://e1h11.simplecdn.net/videosink.zoovy/$task->{'video'}/index.html";
					}
				else {
					$GTOOLS::TAG{'<!-- VIDEO_LINK -->'} = "/biz/todo/no_video.html";
					}
				$GTOOLS::TAG{'<!-- REMOVE_BUTTON -->'} = '';
				if ($task->{'disable_remove'}) {
					## flag that turns off the remove feature.
					}
				elsif ($allow_remove) {
					$GTOOLS::TAG{'<!-- REMOVE_BUTTON -->'} = qq~<a href="/biz/index.cgi?VERB=DISABLE-TODO-TASK&group=$task->{'id'}" id="remove_button"></a>~;
					}		

				my $nexttask = undef;
				if ($i != scalar(@PANELS)) { 
					$nexttask = $PANELS[$i]; 
					}

				if ($task->{'doit'} ne '') {
					## do it button
					$GTOOLS::TAG{'<!-- DOIT_BUTTON -->'} = qq~<a href="$task->{'doit'}" id="do_it_now_button"></a>~;
					if (defined $nexttask) {
						$GTOOLS::TAG{'<!-- NEXT_BUTTON -->'} = qq~<a href="/biz/index.pl?VERB=TODO&focus=$nexttask->{'id'}" id="skip_button">~;
						}
					}
				else {
					if (defined $nexttask) {
						$GTOOLS::TAG{'<!-- NEXT_BUTTON -->'} = qq~<a href="/biz/index.pl?VERB=TODO&focus=$nexttask->{'id'}" id="next_button">~;				
						}
					}
				}
			
			$i++;
			}
		$GTOOLS::TAG{'<!-- PANELS -->'} = $c;
		}
	}


if (($VERB eq 'NEWS') || ($VERB eq 'WELCOME')) {
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	$year+=2000; $mon+=1;


	my %TOPICS = (
      'enhance'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/enhancements.gif',
      'feature'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/new_feature.gif',
      'general'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/general.gif',
      'outage'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/outage.gif',
      'aol'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/aol.gif',
      'ebay'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/ebay.gif',
		# 'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/ebay_manager.gif',
		'mpo'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/mpo.gif',
      'video'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/video.gif',
      'zoovy'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/zoovy.gif',
      'pr'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/zoovy.gif',
      'zid'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/zoovy.gif',
      'amz'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/amazon.gif',
      'ebaystore'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/ebaystores.gif',
      'overstock'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/overstock.gif',
      'google'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/google.gif',
      'bing'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/bing.gif',
      'newsletter'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/newsletter.gif',
      'sc'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/supplychain.gif',
      'pricegrab'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/pricegrabber.gif',
      'dealtime'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/dealtime.gif',
      'nextag'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/nextag.gif',
      'image'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/image.gif',
      'design'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/design.gif',
      'html'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/html.gif',
      'fedex'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/fedex.gif',
      'paypal'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/paypal.gif',
      'ups'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/ups.gif',
      'proshop'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/newsicons/proshop.gif',
      'twitter'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/twitter.gif',
      'facebook'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/facebook.gif',
		'wishpot'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/wishpot.gif',
		'veruta'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/logos/veruta.gif',
		'pirate'=>'https://static.zoovy.com/img/proshop/W64-H64-Bffffff/zoovy/funny/pirateflag.gif',
	   );
	

	my $dbh = &DBINFO::db_zoovy_connect();
	my $pstmt = "select * from RECENT_NEWS where EXPIRES>now() and CREATED<now() order by ID desc limit 0,30";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my @results = ();
	my $CLUSTER = uc('@'.&ZOOVY::resolve_cluster($USERNAME));

	while ( my $hashref = $sth->fetchrow_hashref() ) {
		next if (($hashref->{'TOPIC'} =~ /^ebay/) && ($FLAGS !~ /,EBAY,/)); 
		next if (($hashref->{'TOPIC'} eq 'outage') && ($FLAGS =~ /,TRIAL,/));
		next if ((not $hashref->{'PUBLIC'}) && ($FLAGS =~ /,TRIAL,/));
		next if ((substr($hashref->{'TOPIC'},0,1) eq '@') && ($hashref->{'TOPIC'} ne $CLUSTER));
		next if ($hashref->{'TITLE'} eq '');
		next if ($hashref->{'MESSAGE'} eq '');
		next if (($hashref->{'RESELLER'} ne '') && ($hashref->{'RESELLER'} ne $RESELLER));
		next if ($hashref->{'PUBLIC'} & 8);	# never show SEO FODDER on the recent news
		next if ($hashref->{'PUBLIC'} & 16); # never show PRESS RELEASES on the recent news
		push @results, $hashref;
		}
	$sth->finish();

	if (scalar(@results)==0) {
		push @results, { 
			CREATED=>&ZTOOLKIT::mysql_from_unixtime(time()),
			TOPIC=>'',
			TITLE=>'No Recent News',
			MESSAGE=>'The system is running normally, there are no recent changes to report.',
			};
		}

	foreach my $hashref (@results) {
		my $created = strftime("%D<br>",localtime(&ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'})));
		my $URL = $TOPICS{$hashref->{'TOPIC'}};
		if ($URL eq '') { $URL = $TOPICS{'general'}; }
	
		if ($hashref->{'MESSAGE'} =~ /<.*?>/) {
			## already formatted
			}
		else {
			$hashref->{'MESSAGE'} =~ s/[\n\n]/\<\/p><p>/gs;
			}

		if ($hashref->{'SUBTITLE'} =~ /^http/i) {
			$hashref->{'SUBTITLE'} = qq~<a target="link" href="$hashref->{'SUBTITLE'}">$hashref->{'SUBTITLE'}</a>~;
			}

		$c .= qq~
		<tr>
		<td bgcolor='FFFFFF' valign='top'>
			<img src="$URL" width=64 height=64><br>
			<font face='verdana, helvetica, arial' size='1'>$created</font>	
		</td>
		<td bgcolor='FFFFFF' valign='top'>
		<h2 class="recentnews">$hashref->{'TITLE'}</h2>
		<h3 class="recentnews">$hashref->{'SUBTITLE'}</h3>
		<p class="recentnews">$hashref->{'MESSAGE'}</p>
		</td>
		</tr>
		~;
		}

	$GTOOLS::TAG{"<!-- RECENT_NEWS -->"} = $c;
	$c = '';

	open F, ">>/tmp/login.log";
	print F "$mon/$mday/$year - $hour:$min:$sec ".$ENV{"REMOTE_ADDR"}." -> ".$USERNAME."\n";
	close F;

	}


my @MSGS = ();

##
##
##
if ($VERB eq 'NEWS') {
	##
	## Main User Login
	##
	$template_file = 'index-main.shtml'; 

	if (not defined $todo) {
		$todo = TODO->new($USERNAME,LUSER=>$LUSERNAME);
		}
	$todo->verify();
	my ($count) = $todo->count();

	if ($count>100) {
		push @ERRORTASKS, {
			TITLE=>"Wow, you have a lot of items on your TO DO list",
			DETAIL=>"You are seeing this message because your TODO list contains more than 100 items in it. This is a very severe issue. Please remove items from your TODO list.",
			};
		}
	elsif ($count>20) {
		push @ERRORTASKS, {
			TITLE=>"Wow, you have a lot of items on your TO DO list",
			DETAIL=>"You are seeing this message because your TODO list contains $count items in it. Please take a moment to clear out some of the items to improve the performance of the Zoovy interface.",
			};
		}

	if ($PRT>0) {
		push @ERRORTASKS, {
			TITLE=>'PARTITIONED ACCESS',
			DETAIL=>"You are currently logged into partition $PRT",
			};
		}

	require SITE;
	my ($DESIGNATION) = &SITE::whatis($ENV{'REMOTE_ADDR'});
	if ($DESIGNATION eq '') {}
	elsif ($DESIGNATION eq 'SAFE') {}
	else {
		push @ERRORTASKS, {
			'TITLE'=>sprintf("Your IP Address: %s is designated as %s (please contact Zoovy support to resolve)",$ENV{'REMOTE_ADDR'},$DESIGNATION),
			'DETAIL'=>"This was most likely caused by some type of non-standard usage of the system. Chances are your site is not working properly for this IP address"
			};
		}

	if ($FLAGS =~ /,TRIAL,/) {
		}
	elsif (($LUSERNAME eq '') || ($LUSERNAME eq 'ADMIN')) {
		## WARN USER ABOUT ACCESSING ACCOUNT.
		my ($helplink,$helphtml) = GTOOLS::help_link('Manage User Logins', 50292);
		push @ERRORTASKS, {
			TITLE=>"ADMIN ACCOUNT LOGIN",
			DETAIL=>qq~You are currently logged into the administrative account "ADMIN".
You should go to Setup / User Manager and create unique logins for each person who has access to this account.~,
			};
		}


	$GTOOLS::TAG{'<!-- RSS_SECUREKEY -->'} = &ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'RS');
	$GTOOLS::TAG{'<!-- TESTCODE -->'} = &ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'XX');
	$GTOOLS::TAG{'<!-- SPONSOR_CODE -->'} = &ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'ZR');

#	if (($FLAGS !~ /,BPP,/) && ($LUSERNAME eq 'ADMIN')) {
#		$GTOOLS::TAG{'<!-- MASTER_LOGIN -->'} .= qq~
#<tr><td colspan='3'><center><table border=0 cellpadding=3 width=95% class="table_stroke"><tr><td>
#<span class="alert">WARNING: Your Zoovy experience can be optimized.</span>
#<br>
#You are not currently enrolled in our Best Partner Practices (BPP) program. <br>
#Your account is now eligible for this program, please visit:
#<a href="http://webdoc.zoovy.com/doc/50849">
#http://webdoc.zoovy.com/doc/50849
#</a> to learn more. 
#
#</font>
#</td></tr></table>
#</center>
#</td></tr>
#		~;
#		}




	my $MIDNIGHT_TS = Date::Parse::str2time(strftime("%Y-%m-%d 00:00:00", localtime(time())));

	my $d = 0;
	if ($FLAGS =~ /\,_O\=([\d]+)\,/) { $d = $1; }
	if ($d>0) {
		#require ORDER::STATS;
		#my ($count,$sum) = &ORDER::STATS::quick_stats($USERNAME,$MID,$MIDNIGHT_TS);

		require KPIBI;		
		my ($gms,$count,$units) = KPIBI::quick_stats($USERNAME,'OGMS');

	$gms = sprintf("%.2f",$gms);
	$GTOOLS::TAG{'<!-- RECENT_ORDERS -->'} = qq~
	<tr><td><u>Since Midnight:</u></td></tr>
	<tr><td>Total Orders</td><td>$count</td></tr>
	<tr><td>Gross Sales</td><td>\$$gms</td></tr>
	<tr><td>Items Sold</td><td>$units</td></tr>
	~;
		}
	else {
		$GTOOLS::TAG{'<!-- RECENT_ORDERS -->'} = qq~<tr><td colspan=2><i>Not Available<br></i></td></tr>~;
		}
	
#	require STATS;
#	$GTOOLS::TAG{'<!-- RECENT_VISITORS -->'} = "<tr><td>Page Views:</td><td>".&STATS::quick_stats($USERNAME,$MID,$MIDNIGHT_TS)."</td></tr>";

	&DBINFO::db_zoovy_close();

	$HEAD .= qq~<link rel="alternate" title="Zoovy News RSS" href="https://www.zoovy.com/biz/rss/news.cgi/$USERNAME.rss" type="application/rss+xml">~;
	}

## 
## NON-TODO LIST (CLASSIC VIEW)
##
if (scalar(@ERRORTASKS)>0) {
	my $c = '';
	foreach my $errtask (@ERRORTASKS) {
		my $prettydate = &ZTOOLKIT::pretty_date($errtask->{'CREATED_GMT'},1);
		my $link = $errtask->{'LINK'};
		if (not defined $link) { $link = ''; }
		if ($link ne '') { $link = "<span class='hint'><a href='$link'>[LINK]</a></span>"; }
		$c .= qq~
<tr><td align=center colspan='3'>
<table border=0 cellpadding=3 width=95% class="table_stroke"><tr><td>
<div class="alert">$prettydate ...  $errtask->{'TITLE'}</div>
<div class="hint">$errtask->{'DETAIL'}</div>
~;
		if (not defined $errtask->{'ID'}) { $errtask->{'ID'} = 0; }
		if ($errtask->{'ID'}>0) {
			$c .= qq~<span class="hint"><a href="index.cgi?VERB=DISMISS&ID=$errtask->{'ID'}">[CLEAR]</a> </span>~;
			}
		$c .= qq~
$link
</td></tr></table>
</td></tr>~;
		}
	$GTOOLS::TAG{'<!-- MESSAGES -->'} = $c;
	}

if ($VERB eq 'BLANK') {
	$VERB = 'xyz';
	$template_file = 'index-blank.shtml';
	}



if ($LUSERNAME eq 'SUPPORT') {
	my $TIER = 'Z';
	if ($FLAGS =~ /TIER\=(.*?),/) { $TIER = $1; }
	elsif ($FLAGS =~ /TRIAL/) { $TIER = 'T'; }
	elsif ($FLAGS =~ /NEWBIE/) { $TIER = 'N'; }
	$HEAD .= qq~

<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost +
"google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try{
var pageTracker = _gat._getTracker("UA-885015-3");
pageTracker._setCustomVar(1,"Tier","$TIER",1);
pageTracker._trackPageview();
} catch(err) {}</script>

~;
	}

&GTOOLS::output(
	header=>1,
	bc=>\@BC,
	'msgs'=>\@MSGS,
	tabs=>\@TABS,
	head=>$HEAD,
	title=>$TITLE,
	help=>"#50727",
	file=>$template_file,
	js=>1+2+4,
	todo=>1
	);

exit();

