#!/usr/bin/perl

use strict;

use lib "/httpd/modules"; 
use CGI;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;	
require ZTOOLKIT;
require DBINFO;
require NAVCAT;
require DOMAIN::TOOLS;
require SYNDICATION;


my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $qtUSERNAME = $dbh->quote($USERNAME);

my $template_file = 'index.shtml';
if ($FLAGS !~ /,XSELL,/) {
	$template_file = 'deny.shtml';
	}

my @TABS = ();
my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;
my $VERB = $ZOOVY::cgiv->{'VERB'};

my $so = undef;
my ($DOMAIN,$ROOTPATH) = (undef,undef);

if ($PROFILE ne '') {
	push @TABS, { name=>'Config',selected=>($VERB eq '')?1:0, link=>'index.cgi', };
	push @TABS, { name=>"Categories", selected=>($VERB eq 'CATEGORIES')?1:0, link=>"?VERB=CATEGORIES&PROFILE=$PROFILE", };
	push @TABS, { name=>"Logs", selected=>($VERB eq 'LOGS')?1:0, link=>"?VERB=LOGS&PROFILE=$PROFILE", };
	push @TABS, { name=>"Diagnostics", selected=>($VERB eq 'DEBUG')?1:0, link=>"?VERB=DEBUG&PROFILE=$PROFILE", };
	push @TABS, { name=>'Webdoc',selected=>($VERB eq 'WEBDOC')?1:0, link=>"?VERB=WEBDOC&DOC=50375&PROFILE=$PROFILE", };

	($so) = SYNDICATION->new($USERNAME,$PROFILE,'YST');
	($DOMAIN,$ROOTPATH) = $so->syn_info();
	}


my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Yahoo Shopping',link=>'http://www.zoovy.com/biz/syndication/yahooshop','target'=>'_top', },
		);


if ($VERB eq 'SAVE') {

	tie my %s, 'SYNDICATION', THIS=>$so;
	
	$s{'.ftp_user'} = $ZOOVY::cgiv->{'user'};
	$s{'.ftp_pass'} = $ZOOVY::cgiv->{'pass'};
	$s{'.ftp_server'} = $ZOOVY::cgiv->{'ftpserver'};
	$s{'.ftp_dir'} = $ZOOVY::cgiv->{'dir'};

	my $ERROR = '';
	if ($ERROR eq '' && $s{'.ftp_user'} eq '') { $ERROR = "Yahoo Shopping username is required"; }
	if ($ERROR eq '' && $s{'.ftp_pass'} eq '') { $ERROR = "Yahoo Shopping password is required"; }
	if ($ERROR eq '' && $s{'.ftp_server'} eq '') { $ERROR = "FTP Server is required, and will be given to you by Yahoo Shopping when you sign up (Hint: stop guessing and try reading the documentation)"; }
	if ($ERROR eq '' && $s{'.ftp_server'} =~ /[^A-Za-z0-9\.\-]+/) { $ERROR = "FTP Server contains invalid characters (perhaps you're sending a URI?)"; }
	if ($ERROR eq '' && $s{'.ftp_server'} !~ /yahoo\.com$/) { $ERROR = "FTP server does not end with .yahoo.com - it's probably not valid!"; }

	$s{'.include_ebay'} = 0;
	if (($ERROR eq '') && ($ZOOVY::cgiv->{'INCLUDE_EBAY'})) {
		if ($FLAGS =~ /,EBAY,/) { 	$s{'.include_ebay'} = 1; }
		else {
			$ERROR = "Sorry, you do not have the EBAY flag. <a href='http://www.zoovy.com/biz/configurator?VERB=VIEW&BUNDLE=EBAY'>Click here to Add</a>";
			}
		}

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		$so->save();
		}

	$VERB = 'EDIT';
	}


if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = time();
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</b><br>";
		$c .= "<a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a>";
		$c .= " | ";
		$c .= "<a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=SYNDICATION&DST=YST&PROFILE=$ns&GUID=$ts\">PUBLISH</a>";
		$c .= "</td>";
		$c .= "</tr>";
		my ($s) = SYNDICATION->new($USERNAME,$ns,'YST');
		$c .= "<tr><td class=\"$class\">Status: ".$s->statustxt()."<br><br></td></tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}


if ($VERB eq 'EDIT') {

	my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
	$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

	my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'YST');
	my ($DOMAIN,$ROOTPATH) = $so->syn_info();
	tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- USER -->'} = &ZOOVY::incode($s{'.ftp_user'});
	$GTOOLS::TAG{'<!-- DIR -->'} = &ZOOVY::incode($s{'.ftp_dir'});
	$GTOOLS::TAG{'<!-- PASS -->'} = &ZOOVY::incode($s{'.ftp_pass'});
	$GTOOLS::TAG{'<!-- FTPSERVER -->'} = &ZOOVY::incode($s{'.ftp_server'});
   $GTOOLS::TAG{'<!-- GUID -->'} = $so->guid();
   $GTOOLS::TAG{'<!-- VIEW_URL -->'} = $so->url_to_privatefile();
	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	$GTOOLS::TAG{'<!-- STATUS -->'} =~ s/\//<br>/g;

	#my $YMID = $hashref->{'YAHOO_FTPDIR'};
	#$YMID =~ s/[^\d]+//gs;
	#$GTOOLS::TAG{'<!-- YAHOO_SEARCH -->'} = "http://search.shopping.yahoo.com/search?p=mid:$YMID";
	$template_file = 'edit.shtml';
	}

if ($VERB eq 'DELETE') {
   my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
   my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'YST');
   $so->nuke();
   $VERB = '';
	
	$template_file = 'edit.shtml';
   }


if ($VERB eq 'SAVE-CATEGORIES') {
	my $changed = 0;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (not defined $ZOOVY::cgiv->{'navcat-'.$safe});
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if ($metaref->{'YSHOP_CAT'} eq $ZOOVY::cgiv->{'navcat-'.$safe});
		$metaref->{'YSHOP_CAT'} = $ZOOVY::cgiv->{'navcat-'.$safe};
		$NC->set($safe,metaref=>$metaref);
		}
	$NC->save(); undef $NC;

	$VERB = 'CATEGORIES';
	}	

if ($VERB eq 'CATEGORIES') {
	my @YAHOOCATS = ();
	open F, "<yahoocats.txt";
	while (<F>) {
		my $line = $_;
		$line =~ s/[\n\r]+//gs;
		$line =~ s/[ ]$//gs;
		next if ($line eq '');
		push @YAHOOCATS, $line;
		}
	close F;


	my $c = '';
	use Data::Dumper;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths($ROOTPATH)) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if (substr($pretty,0,1) eq '!');
	
		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,$safe)) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}
		my $val = $metaref->{'YSHOP_CAT'};
		$val =~ s/[\s]+$//;	# strip trailing whitespace on categories (bad Yahoo category update)
		$c .= "<tr><td nowrap>$name</td><td>";
		$c .= "<select name=\"navcat-$safe\">";
		$c .= "<option value=\"\">Do not submit category</option>";
		my $selected = '';
		foreach my $cat (@YAHOOCATS) {
			$selected = ($val eq $cat)?' selected ':''; 
			$c .= "<option $selected value=\"$cat\">$cat</a>";
			}
		$c .= "</td></tr>\n";
		}
	if ($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	
	$template_file = 'categories.shtml';
	}

if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
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


	

if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}



&GTOOLS::output(
   'title'=>'Yahoo Shopping Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50375',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

