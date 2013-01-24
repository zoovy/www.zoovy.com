#!/usr/bin/perl

use strict;

use CGI;
my $q = new CGI;

use lib "/httpd/modules";
use WEBDOC::SESSION;
use WEBDOC;
use GTOOLS;
use ZOOVY;
use SEARCH::GOOGLE;
use Data::Dumper;

my $wdbh = &DBINFO::db_zoovy_connect();
my $uri = $ENV{'REQUEST_URI'};
my $template_file = 'index.shtml';
my $DOCID = 0;
my $keywords = $q->param('keywords');
my $engine = $q->param('engine');
if (not defined $engine) { $engine = 'zoovy'; }

$GTOOLS::TAG{'<!-- engine_zoovy -->'} = ($engine eq 'zoovy')?'checked':'';
$GTOOLS::TAG{'<!-- engine_google -->'} = ($engine eq 'google')?'checked':'';

my $USERNAME = $q->param('USERNAME');
#if ($USERNAME eq '') { 
#	my ($userid) = split(/\@/,$q->cookie('session_id'));
#	($USERNAME,my $login) = split(/\*/,$userid);
#	}

print STDERR "USERNAME: $USERNAME\n";

my $VERB = '';
if (defined $q->param('VERB')) { $VERB = $q->param('VERB'); }
$VERB =~ s/[^A-Z0-9\-]//gs;	# this is output later, and this prevents XSS attack
my ($AREA,$FILE) = ('','');


my $SID = 0;
if (defined $q->param('SESSION')) { $SID = int($q->param('SESSION')); }
if (defined $q->cookie('webdoc_session')) { $SID = int($q->cookie('webdoc_session')); }

my ($ws) = WEBDOC::SESSION->new(ID=>$SID,USERNAME=>$USERNAME);

##
## SANITY: at this point session stuff is done.
##



if ($uri =~ /^(\/images\/.*)$/) {
	my $path = $1;
	$path =~ s/[.]+/./gs;		# converts .. into .
	$path =~ s/[\/]+/\//gs;		# converts // into /

	open F, "/httpd/webdoc/files/$path"; $/ = undef; my $buf = <F>; close F; $/ = "\n";
	if ($path =~ /\.gif$/) {
		print "Content-type: image/gif\n\n";
		}
	elsif ($path =~ /\.js$/) {
		print "Content-type: text/javascript\n\n";
		}
	elsif ($path =~ /\.css$/) {
		print "Content-type: text/css\n\n";
		}
	elsif ($path =~ /\.html$/) {
		print "Content-type: text/html\n\n";
		}
	print $buf;
	$template_file = '';
	$VERB = 'X';
	}


if (defined $q->param('GOTO')) {
	$VERB = 'LOAD';
	my ($AREA,$FILE) = split(/\//,$q->param('GOTO'),2);
	my $pstmt = "select ID from WEBDOC_FILES where AREA=".$wdbh->quote($AREA)." and FILE=".$wdbh->quote($FILE);
	print STDERR $pstmt."\n";
	my $sth = $wdbh->prepare($pstmt);
	$sth->execute();
	($DOCID) = $sth->fetchrow();
	$sth->finish();

	if (($DOCID == 0) && ($FILE =~ /[\/]?myzoovy\/(.*?)$/)) {
		## create a new user webdoc
		my ($USERNAME) = $1;
		my ($w) = WEBDOC->new(0,FILE=>$FILE,BODY=>qq~
[[FILENAME]$FILE]
[[TITLE]Webdoc Homepage for $USERNAME]

[[SECTION]Welcome $USERNAME]
This page will contain custom notes for your account.
It is only visible to you and support.
[[/SECTION]]
~);
		($DOCID) = $w->docid();
		print STDERR "DOCID: $DOCID\n";
		$w->save();
		}


	$VERB = 'LOAD';
	if ($DOCID == 0) { $VERB = ''; }
	}


if ($uri =~ /^\/sitemap$/) { $VERB = 'SITEMAP'; }
elsif ($uri =~ /^\/search/) { $VERB = 'SEARCH'; }
elsif ($uri =~ /^\/tag\/(.*?)$/) { $VERB = 'SEARCH'; $keywords = $1; }


if ($uri =~ /^\/doc[\/-]([\d]+)/) { $VERB = 'LOAD'; $DOCID = int($1); } 
if ($VERB eq 'DOC') { $VERB = 'LOAD'; $DOCID = int($q->param('DOCID'));  } 

## receiving from gtools::output header (webdoc search)
if ($q->param('FROM_HEADER') eq 'help:webdoc') {
	$VERB = 'SEARCH';
	$keywords = $q->param('HEADER_VALUE');
	}
# print STDERR Dumper($q);



if ($VERB eq 'DOCHEADER') {
	$VERB = 'SHOW';
	$template_file = 'frame-header.shtml';
	}

if ($VERB eq 'DOCNAV') {
	$DOCID = int($q->param('DOCID')); 
	$VERB = 'SHOW';
	## this displays the navigation (used in the left frame)
	my ($w) = WEBDOC->new($DOCID);
	($GTOOLS::TAG{'<!-- TOC -->'}) = buildToc($w,keywords=>$keywords,ws=>$ws);
	$GTOOLS::TAG{'<!-- KEYWORDS -->'} = $keywords;
	$w = undef;
	$template_file = 'frame-nav.shtml';
	}

if ($VERB eq 'DOCBODY') {
	$DOCID = $q->param('DOCID');
	$VERB = 'SHOW';
	## this displays the (used in the left frame)
	my ($w) = WEBDOC->new($DOCID);

	my $okay_to_show = 1;
	if ($w->filename() =~ /^myzoovy\/(.*?)$/) {
		## authenticated documents
		my ($tryusername) = $1;	

		if (&ZOOVY::is_zoovy_ip($ENV{'REMOTE_ADDR'})) {
			$okay_to_show++;
			$USERNAME = $tryusername;
			}
		else {
			require LUSER;
			my ($LU) = LUSER->authenticate();
			if (defined $LU) {
				my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
				if (lc($USERNAME) eq lc($tryusername)) { $USERNAME = $tryusername; }
				}
			}
		}
	else {
		## unauthenticated documents
		$USERNAME = '';
		$okay_to_show++;
		}

	if (not $okay_to_show) {
		$GTOOLS::TAG{'<!-- BODY -->'} = sprintf("<i>Document %s is restricted -- please login to access this page.</i>\n",$w->filename());
		}
	elsif (($USERNAME ne '') && (not defined $ENV{'HTTPS'})) {
		## force reload to secure!
		$GTOOLS::TAG{'<!-- BODY -->'} = qq~
<body>

<i>Please hold on while we upgrade to a secure connection!</i><br>

<script language="javascript">

if (document.location.protocol != "https:")
{
	document.location.href = "https://www.zoovy.com/$ENV{'REQUEST_URI'}";
};
</script>

</body>
~;
		}
	elsif ($USERNAME ne '') {
		$GTOOLS::TAG{'<!-- BODY -->'} = "<font color='red'>DOCUMENT IS RESTRICTED TO: $USERNAME</font><hr>".
			$w->wiki2html(keywords=>$keywords,USERNAME=>$USERNAME);
		}
	else {
		## just to be safe, we don't pass document here.
		$GTOOLS::TAG{'<!-- BODY -->'} = '<!-- no authentication required -->'.
			$w->wiki2html(keywords=>$keywords);
		}


	
	$GTOOLS::TAG{'<!-- KEYWORDS -->'} = $keywords;
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Zoovy eCommerce - ".$w->{'TITLE'};
	$GTOOLS::TAG{'<!-- TS -->'} = time();
	$w = undef;
	$template_file = 'frame-body.shtml';
	}

if ($VERB eq '') { $VERB = 'SEARCH'; }



sub buildToc {
	my ($w,%options) = @_;
	##
	## generate the table of contents
	##

	my $toc = '';
	my ($ws) = $options{'ws'};
	if (not defined $ws) { $ws = WEBDOC::SESSION->new(); }

	## SANITY: at this point $ws is initialized to the current session.

	if (defined $w->{'@FAQS'}) {
		my $has_faqs = 0;
		foreach my $faqref (@{$w->{'@FAQS'}}) {
			# $toc .= Dumper($faqref);
			if ($faqref->{'IS_FAQ'}) { $has_faqs++; }
			}
		if ($has_faqs) {
			$toc .= qq~<h2 style="color:#777777;">Frequently Asked Questions</h2><ol>~;
			foreach my $faqref (@{$w->{'@FAQS'}}) {
				next unless ($faqref->{'IS_FAQ'});
				my $txt = &WEBDOC::jsescape($faqref->{'QUESTION'});
				$toc .= qq~<li> $txt\n~;
				}
			$toc .= qq~</ol><br>~;
			}
		
		}



	$toc .= qq~
	<h2 style="color:#777777;">Related Documents</h2>
<!--
	<p><a href="javascript: d.openAll();">open all</a> | <a href="javascript: d.closeAll();">close all</a></p>
-->
	<script type="text/javascript">
		<!--

		d = new dTree('d');
	~;
		

#//		d.add(1,0,'Node 1','example01.html');
#//		d.add(2,0,'Node 2','example01.html');
#//		d.add(3,1,'Node 1.1','example01.html');
#//		d.add(4,0,'Node 3','example01.html');
#//		d.add(5,3,'Node 1.1.1','example01.html');
#//		d.add(6,5,'Node 1.1.1.1','example01.html');
#//		d.add(7,0,'Node 4','example01.html');
#//		d.add(8,1,'Node 1.2','example01.html');
#//		d.add(9,0,'My Pictures','example01.html','Pictures I taken over the years','','','img/imgfolder.gif');

	##
	## this builds the list of documents.
	##

	if (1) {
		my $wdbh = &DBINFO::db_zoovy_connect();
		my $pstmt = "select TOPICID from WEBDOC_TOPIC_LINKS where DOCID=".int($w->docid());
		my $sth = $wdbh->prepare($pstmt);
		$sth->execute();
		while ( my ($TOPICID) = $sth->fetchrow() ) {
			$pstmt = "select ID,PARENT,ROOT,TITLE from WEBDOC_TOPICS where ID=".int($TOPICID);
			my $sthx = $wdbh->prepare($pstmt);
			$sthx->execute();
			while ( my ($topicid,$p,$root,$title) = $sthx->fetchrow() ) {
				my $txt = &WEBDOC::jsescape($title);
				$toc .= qq~ d.add($topicid,0,'$txt'); ~;
				$toc .= WEBDOC::buildNav($root,int($w->docid()));
				}
			$sthx->finish();
			}
		$sth->finish();
		&DBINFO::db_zoovy_close();
		}


	$toc .= qq~ 
		d.add(0,-1,'Zoovy WebDocs');
		document.write(d);

//-->
</script>
	~;

	my @s = $ws->recentSearch();
	if (scalar(@s)>0) {
		## only show recent searches if there are some!
		$toc .= qq~
		<br>
		<h2 style="color:#777777;">Your Recent Searches</h2>
		~;
		foreach my $s (@s) {
			$toc .= qq~<li> <a target=\"_top\" href=\"//www.zoovy.com/webdoc/index.cgi?VERB=SEARCH&keywords=$s\">$s</a><br>~;
			}
		}

	if (1) {
		my @d = $ws->recentDocs();
		my $wdbh = &DBINFO::db_zoovy_connect();
		my $c = '';
		my $wdocid = $w->docid();
		foreach my $DOCID (@d) {
			next if ($DOCID == $wdocid);	# skip the current document!
			my $pstmt = "select TITLE from WEBDOC_FILES where ID=".int($DOCID);
			my $sth = $wdbh->prepare($pstmt);
			$sth->execute();
			my ($TITLE) = $sth->fetchrow();
			$sth->finish();
			next if ($TITLE eq '');

			$c .= qq~<li> <a target=\"_top\" href=\"//www.zoovy.com/webdoc/doc-$DOCID\">$TITLE (#$DOCID)</a><br>~;
			}
		&DBINFO::db_zoovy_close();
		if ($c ne '') {
			$toc .= qq~
			<br>
			<h2 style="color:#777777;">Your Recently Viewed</h2>$c
			~;
			}
		}


	return($toc);
	}


##
## AT THIS POINT THE URI HAS BEEN PROCESSED AND A VERB HAS BEEN SELECTED.
##


if ($VERB eq 'SEARCH') {
	require URI::Escape;
	my $escKeywords = URI::Escape::uri_escape($keywords);

	require WEBDOC::OZMO;
	my $resultsref = &WEBDOC::OZMO::ask_question($keywords);
	if ((defined $resultsref) && (scalar(@{$resultsref})>0)) { 
        #    {
        #      'FILE' => '',
        #      'ID' => '1660',
        #      'QUESTION' => 'What if I have a lot of products? How can I get them into Zoovy quickly?',
        #      'DOCID' => '50788',
        #      'SCORE_HURTFUL' => '0',
        #      'RESPONSE' => 'If you have a spreadsheet of product data, we can import your products via CSV. It is best to have tech support handle the actual import or learn the details of how to do it through a scheduled appointment. If you do not have a spreadsheet and would rather create your products offline you might consider Zoovy Warehouse Manager.',
        #      'CREATED_GMT' => '1164922436',
        #      'MODIFIED_GMT' => '1164922436',
        #      'IS_FAQ' => '1',
        #      'AREA' => '',
        #      'TECH' => 'jmiewald',
        #      'SCORE_HELPFUL' => '100'
        #    }

		$ws->addSearch($keywords);

		my $c = '';
		my $i = 0; 
		foreach my $faqref (@{$resultsref}) {
			$c .= "<tr><td>";
			$c .= $faqref->{'QUESTION'}."<br>";
			if ($faqref->{'RESPONSE'} ne '') { $c .= "<div class=\"hint\">".$faqref->{'RESPONSE'}."</div>"; }
			if ($faqref->{'DOCID'}>0) {
				$c .= sprintf("<div class=\"hint\"><a href=\"//www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=%d\">Read WebDoc #%d</a></div>",$faqref->{'DOCID'},$faqref->{'DOCID'});
				}
			$c .= "</td></tr>";
	
			}
		
		if ($c ne '') {
			$c = qq~
<table align="center"><tr><td>
	<!-- main section of copy in a doc. displays the headline of the section, subhead, and copy block -->
<div class="sectional">
<h3>Related FAQ's</h3>
<div class="navcat_5 subsectional">
<table width="100%">
	$c
</table>
</div>
</td></tr></table>
~;
			}

		$GTOOLS::TAG{'<!-- FAQ_RESULTS -->'} = $c;
		}


	## 
	## Keyword Results
	## 


	my ($keysref,$docsref) = ();

	if ($engine eq 'zoovy') {
		($keysref,$docsref) = &WEBDOC::search($keywords);
		}
	elsif ($engine eq 'google') {
#$VAR1 = {
#          'S' => 'CORRECTED: If <b>shipping</b> to international ground for <b>Fedex</b> Labels, the province <br>  <b>.....</b> Highlights: Quickbooks 2004 support, <b>FedEx Ship</b> Manager Support (imports <b>...</b>',
#          'RK' => '0',
#          'HAS' => [
#                   {}
#                 ],
#          'T' => 'Zoovy Webdoc - Order Manager 5.xxx Release Notes',
#          'HAS.C' => undef,
#          'HAS.~SZ' => '2k',
#          'HAS.RT' => undef,
#          'HAS.~CID' => 'O22bM5g-SUYJ',
#          'Label' => '_cse_bts1i2nyxpm',
#          'UE' => 'http://webdoc.zoovy.com/doc-50499/Order%2520Manager%25205.xxx%2520Release%2520Notes',
#          'HAS.L' => undef,
#          'LANG' => 'en',
#          'U' => 'http://webdoc.zoovy.com/doc-50499/Order%20Manager%205.xxx%20Release%20Notes'
#        };

		
		my $results = SEARCH::GOOGLE::search(CGI->unescape('017949788311019015841%3Abts1i2nyxpm'),$keywords);

		foreach my $ref (@{$results}) {
			push @{$docsref}, {
				'title'=>$ref->{'T'},
				'link'=>$ref->{'U'},
				'score'=>'',
				'summary'=>$ref->{'S'},	
				};
			}
#		$docsref = [
#			{ 'title'=>'title', file=>'file', score=>'score', summary=>'summary', }
#			];
		}


	my $c = '';
	my $i = 0; 
	foreach my $docref (@{$docsref}) {
		next if ($i++>25);
		if ($docref->{'title'} eq '') { $docref->{'title'} = $docref->{'file'}; }
		if (not defined $docref->{'link'}) {
			$docref->{'link'} = "//www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=$docref->{'docid'}&keywords=$escKeywords";
			}
		my $video_icon = '<!-- no video -->';
		if ($docref->{'has_video'}) { $video_icon = qq~<a href="//www.zoovy.com/webdoc/index.cgi?VERB=DOC&DOCID=$docref->{'docid'}&i_want_video_please=1"><img border=0 width=50 height=20 src="http://www.zoovy.com/webdoc/images/icon_youtube.png"/></a>~; }

		$c .= qq~<tr>
				<td valign=top><a href="$docref->{'link'}">$docref->{'title'}</a></td>
				<td valign=bottom>$docref->{'score'}</td>
				<td>$video_icon</td>
				</tr>~;
		$c .= qq~<tr><td>$docref->{'summary'}</td></tr>~;
		}

	if ($c ne '') {

		my %params = ();
		foreach my $p ($q->param()) { $params{$p} = $q->param($p); }
		$params{'engine'} = ($params{'engine'} eq 'google')?'zoovy':'google';
		my $retryurl = '//webdoc.zoovy.com?'.ZTOOLKIT::buildparams(\%params);		

		$c = qq~
	<table align="center"><tr><td>
		<!-- main section of copy in a doc. displays the headline of the section, subhead, and copy block -->
	<div class="sectional">
	<h3>Documents Matching: $keywords</h3>
	<!--
	<i>Results provided by ~.uc($engine).qq~, try again with <a href="$retryurl">~.uc( ($engine eq 'google')?'zoovy':'google' ).qq~</i>
	-->
	<div class="navcat_5 subsectional">
	<table width="100%">
		$c
	</table>
	</div>
	</td></tr></table>
	~;
		$GTOOLS::TAG{'<!-- SEARCH_RESULTS -->'} = $c;
		}
	elsif ($keywords eq '') {
		## don't do shit, no keywords were specified.
		}		
	else {
		$GTOOLS::TAG{'<!-- SEARCH_RESULTS -->'} = "<br><table align=\"center\"><tr><td><i>Sorry, no results were found matching: $keywords</i></td></tr></table>";
		}

#<h3>Frequently asked questions</h3>
#<div class="navcat_5 subsectional">
#	<a href="">File Match</a><br />
#	<a href="">File Match</a><br />
#	<a href="">File Match</a><br />
#</div>
#<br>
#<h3>Matching pages</h3>
#<div class="navcat_5 subsectional">
#	<a href="">File Match</a><br />
#	<a href="">File Match</a><br />
#	<a href="">File Match</a><br />
#</div>
#</div>



	#  . '<pre>'.&ZOOVY::incode(Dumper($docsref)).'</pre>';
	$GTOOLS::TAG{'<!-- KEYWORDS -->'} = &ZOOVY::incode($keywords);	

	$template_file = 'index.shtml';
	}


if ($VERB eq 'LOAD') {
	$ws->addDoc($DOCID);
	my ($w) = WEBDOC->new($DOCID);
	$GTOOLS::TAG{'<!-- TITLE -->'} = "Zoovy Webdoc - ".$w->{'TITLE'};
	$GTOOLS::TAG{'<!-- DOCID -->'} = $DOCID;
	$template_file = 'frames.shtml';
	}


if ($VERB eq 'SITEMAP') {
	my $pstmt = "select ID,AREA,FILE,substring(BODY,1,1024),TITLE,MODIFIED_GMT from WEBDOC_FILES order by MODIFIED_GMT desc";
	print STDERR $pstmt."\n";
	my $sth = $wdbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $i = 0;
	while ( my ($id,$area,$file,$body,$title,$mgmt) = $sth->fetchrow() ) {
		## skip if title is blank
		next if ($title eq '');

		next if ($file =~ /^myzoovy/);
		next if ($area =~ /^myzoovy/);

		$i++;
		## staff notes should never be disclosed.
		$body =~ s/(\[\[STAFF\]\].*?\[\[\/STAFF\]\])//igs;
		$body =~ s/(\[\[POLICY\]\].*?\[\[\/POLICY\]\])//igs;

		$body =~ s/\[\[.*?\].*?\]//gs; 
		$body =~ s/\<.*?\>//gs;
		$body =~ s/\&/\& /gs;
		$body =~ s/<!--.*?-->//gs;
		$body =~ s/<!--.*//gs;
		

		if (substr($body,-25) =~ /</) {
			$body =~ s/<.*$//gs;	# sometimes html tags are cut off in the middle.
			}
		if (substr($body,-25) =~ /\[/) {
			$body =~ s/\[.*$//gs;	# sometimes webdoc markup tags are cut off in the middle.
			}
		my $modified = &ZTOOLKIT::pretty_date($mgmt,1);
		$c .= qq~
<tr>
	<td align="left"><a href="//webdoc.zoovy.com/doc-$id/$title">[$id] $area: <b>$title</b></a></td>
	<td align="right"><i>Last Modified: $modified</i><br></td>
</tr>
<tr>
	<td colspan=2>
	<br><div style="font-size: 8pt;">$body</div><br>
	</td>
</tr>~; 
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- RESULTS -->'} = "<table width=700><tr><td colspan=2><h1>SiteMap</h1></td></tr>".
												"$c</table><br><b>$i documents total.</b>";
	$template_file = 'sitemap.shtml';
	}


if ($template_file ne '') {
	($SID) = $ws->save();
	$GTOOLS::TAG{'<!-- SESSION -->'} = $SID;
	

	my ($cookie) = $q->cookie( -name=>'webdoc_session', -value=>$SID, -domain=>'webdoc.zoovy.com', -secure=>0, -expires=>'+1d');
#	print $q->header(-cookie=>$cookie,charset=>'utf8');

	if (&ZOOVY::is_zoovy_ip($ENV{'REMOTE_ADDR'})) {
		$GTOOLS::TAG{'<!-- EDIT_LINK -->'} = "URI:[$uri] [VERB: $VERB] [<a target=\"_top\" href=\"https://admin.zoovy.com/webdoc/index.cgi?VERB=EDIT&docid=$DOCID\">EDIT</a>] $ENV{'REMOTE_ADDR'}\n";
		}

	&GTOOLS::output(file=>$template_file,header=>1);
	if ($template_file ne 'frame-body.shtml') {
		}
	print $WEBDOC::ANALYTICS_CODE;
	print "<!-- IP:$ENV{'REMOTE_ADDR'} VERB[$VERB] FILE[$FILE] SESSION[$SID] -->";
	# use Data::Dumper; print STDERR Dumper(\%ENV);
	#print STDERR "REMOTE_ADDR: ".$ENV{'REMOTE_ADDR'}. " template_file: $template_file\n";
	}

&DBINFO::db_zoovy_close();

