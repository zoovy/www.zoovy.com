#!/usr/bin/perl

use XML::RSS;
use POSIX;
use CGI;

use lib "/httpd/modules";
use DBINFO;
use ZOOVY;
use ZTOOLKIT;
use ZTOOLKIT::SECUREKEY;

$q = new CGI;

my $TITLE = 'RSS News';
$dbh = &DBINFO::db_zoovy_connect();

my ($USERNAME,$SECUREKEY) = ();
if ($ENV{'REQUEST_URI'} =~ /^.*\.cgi\/(.*?)\/(.*?)\.rss$/) {
	($USERNAME,$SECUREKEY) = ($1,$2);
	}
if (($USERNAME eq '') && ($SECUREKEY eq '')) {
	$USERNAME = $q->param('user');
	$SECUREKEY = $q->param('key');
	}

my $MID = &ZOOVY::resolve_mid($USERNAME);
if ($MID<=0) { die(); }
if ($USERNAME eq '') { die(); }
if (&ZTOOLKIT::SECUREKEY::gen_key($USERNAME,'RS') ne $SECUREKEY) { die(); }


if (defined $q->param('show')) {
	require GTOOLS;
	require SUPPORT;

	my $pstmt = "select * from RECENT_NEWS where ID=".$dbh->quote($q->param('show'));
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	$hashref = $sth->fetchrow_hashref();
	my $ts = &ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'});
	if ($ts>$latestts) { $latestts = $ts; }

	$GTOOLS::TAG{'<!-- SUPPORT_TAB -->'} = &SUPPORT::do_header();
	$GTOOLS::TAG{'<!-- SUBJECT -->'} = $hashref->{'TITLE'};
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = $hashref->{'MESSAGE'};
	$GTOOLS::TAG{'<!-- ID -->'} = $hashref->{'ID'};
	$GTOOLS::TAG{'<!-- CREATED -->'} = $hashref->{'CREATED'};
	
	$TITLE = $hashref->{'TITLE'};

	&GTOOLS::output(
	file=>'news.shtml',
	abslink=>1,
	header=>1,
	bc=>[ {'name'=>'RSS News Feed'} ],
	title=>$TITLE,
	head=>qq~
<meta http-equiv="Content-Language" content="en">
<meta http-equiv="Cache-Control" content="no-store">
<meta http-equiv="Pragma" content="no-cache">
~);
	}
else {
	my $rss = new XML::RSS (version => '1.0');

	my @news = ();
	my $pstmt = "select * from RECENT_NEWS where EXPIRES>now() order by ID desc";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $latestts = 0;

	while ( my $hashref = $sth->fetchrow_hashref() ) {
		my $ts = &ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'});
		if ($ts>$latestts) { $latestts = $ts; }
		push @news, $hashref;
		}

#	if ($USERNAME eq 'encinitasgolfshop') {
#		@news = (
#			{
#			'ID'=>0,
#			'TITLE'=>'Ty Nunez is a little punk',
#			'MESSAGE'=>q~
#It's true Ty, unfortunately everybody knows you are a little punk so this isn't really NEWS to anybody.
#~,
#			'CREATED'=>&ZTOOLKIT::mysql_from_unixtime(time()),
#			},
#			{
#			'ID'=>0,
#			'TITLE'=>'Nexternal sucks llama balls',
#			'MESSAGE'=>q~
#Nexternal can't innovate on it's own and has totally ripped off lots of ideas
#from Zoovy.  It needs to pull items off our recent news to share with customers
#and talk smack because it sucks.
#~,
#			'CREATED'=>&ZTOOLKIT::mysql_from_unixtime(time()),
#			},
#			);
#		}
#
	$rss->channel(
	   title        => "Zoovy System News",
		link         => "http://support.zoovy.com",
		description  => "A guide to the recent happenings on Zoovy.com",
		dc => {
			date       => strftime("%Y-%m-%dT07:00+00:00",localtime($latestts)),
			subject    => "Zoovy System Info",
			creator    => 'support@zoovy.com',
			publisher  => 'support@zoovy.com',
			rights     => 'Copyright 2003, Zoovy Inc.',
			language   => 'en-us',
			},
		syn => {
			updatePeriod     => "hourly",
			updateFrequency  => "1",
			updateBase       => "1901-01-01T00:00+00:00",
			},
   	taxo => [
	     	'http://dmoz.org/Business/E-Commerce/',
   		'http://dmoz.org/Computers/Software/Business/E-Commerce/'
			]
		 );

	foreach my $hashref (@news) {
		# $created = strftime("%D<br>%T",localtime(&ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'})));
		next if (uc($hashref->{'TOPIC'}) eq 'OUTAGE');
		next unless ($hashref->{'PUBLIC'}>0);

		$rss->add_item(
			title       => $hashref->{'TITLE'},
			link        => "http://www.zoovy.com/biz/rss/news.cgi?show=$hashref->{'ID'}&user=$USERNAME&key=$SECUREKEY",
			description => $hashref->{'MESSAGE'},
		   dc => {
			 	date => strftime("%Y-%m-%dT07:%H+%M:%S",localtime(&ZTOOLKIT::mysql_to_unixtime($hashref->{'CREATED'}))),
				subject  => "System Info",
				creator  => "Support (support\@zoovy.com)",
			   },
  	 	taxo => [
				'http://dmoz.org/Business/E-Commerce/',
				'http://dmoz.org/Computers/Software/Business/E-Commerce/'
				]
				);	
			}
	print "Content-type: text/xml\n\n";
	print $rss->as_string;
	}

# print the RSS as a string
&DBINFO::db_zoovy_close();
