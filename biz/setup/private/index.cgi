#!/usr/bin/perl


use strict;

use Data::Dumper;
use lib "/httpd/modules";
use GTOOLS;
use LUSER;
use LUSER::FILES;
use TODO;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }
my $template_file = '';

#use Data::Dumper;
#print STDERR Dumper($LU);

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my $c = '';
my ($lf) = LUSER::FILES->new($USERNAME);

my @MSGS = ();
my @BC = ();
push @BC, { name=>'Setup',link=>'/biz/setup/index.cgi' };
push @BC, { name=>'Private Files',link=>'/biz/setup/private/index.cgi' };

my $VERB = $ZOOVY::cgiv->{'VERB'};
my @FILES = ();
foreach my $k (keys %{$ZOOVY::cgiv}) {
	next unless ($k =~ /^FILE:(.*?)$/);
	push @FILES, $1;
	}	


if (($VERB eq 'VIEW') || ($VERB eq 'DOWNLOAD')) {
	## view different types of files.
	$template_file = 'view.shtml';

	my ($FILETYPE, $FILENAME, $GUID) = ();
	if ($ZOOVY::cgiv->{'GUID'} ne '') {
		($FILETYPE, $FILENAME, $GUID) = $lf->lookup(GUID=>$ZOOVY::cgiv->{'GUID'});
		}
	elsif ($ZOOVY::cgiv->{'FILENAME'} ne '') {
		($FILETYPE, $FILENAME, $GUID) = $lf->lookup(FILENAME=>$ZOOVY::cgiv->{'FILENAME'});
		print STDERR "FILENAME: $ZOOVY::cgiv->{'FILENAME'} FILE: $FILENAME\n";
		}

	if ($FILENAME eq '') {
		$GTOOLS::TAG{'<!-- OUTPUT -->'} = "Sorry, but the requested file does not appear to have been created.";
		# die("file doesn't exist.. and i'm not writing a handler right now because i've got a billion other things to do.");
		}
	elsif (($VERB eq 'VIEW') && ($FILETYPE eq 'SYNDICATION')) {	
		## NOTE: we can't show the raw file because stupid firefox auto detects (and mangles) things like the googlebase feed.
		##			since we don't want the people downloading the file, etc. this probably makes more sense anyway.. we can
		##			always make a "view raw file"
		my ($created,$sizex) = $lf->file_detail($FILENAME);
		$sizex = int($sizex);

		require ZTOOLKIT;

		my $out = qq~<b>File Name:</b> 
		<a href="#" onClick="return linkOffSite('https://www.zoovy.com/biz/setup/private/download.cgi/$FILENAME?VERB=DOWNLOAD&'+app.ext.admin.u.uiCompatAuthKVP()+'&FILENAME=$FILENAME');">
		$FILENAME</a><br><b>File Created:</b> ~.&ZTOOLKIT::pretty_date($created,1).qq~<br><b>File Length:</b> $sizex<br><hr>~;

		if ($sizex>100000) {
			$out .= "<i>File too big, please click to download</i>";
			}
		else {
			my $contents = $lf->file_contents($FILENAME);
			$contents = &ZOOVY::incode($contents);
			$contents = &ZTOOLKIT::htmlify($contents);
			$out .= $contents;
			}

		$GTOOLS::TAG{'<!-- OUTPUT -->'} = $out;
		#if (($FILETYPE eq 'CSV') || ($FILETYPE eq 'SYNDICATION')) {
		#	# print "Content-type: text/plain\n\n";	
		#	}
		}
	else {
		print "Content-type: binary/file\n\n";
		print $lf->file_contents($FILENAME);
		exit;
		}
	}



if ($VERB eq 'EXPIRE') {
	foreach my $fileid (@FILES) {
		$lf->expire($fileid);
		}
	$VERB = '';
	}

if ($VERB eq 'PRESERVE') {
	foreach my $fileid (@FILES) {
		$lf->preserve($fileid);
		}
	$VERB = '';
	}





if (($VERB eq '') || ($VERB eq 'SEARCH')) {
	my %params = ();

	$GTOOLS::TAG{'<!-- KEYWORD -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'keyword'});
	$GTOOLS::TAG{'<!-- CHK_FILETYPE -->'} = ($ZOOVY::cgiv->{'filetype'} eq '')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_FILETYPE_AMZ -->'} = ($ZOOVY::cgiv->{'filetype'} eq 'amz')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_FILETYPE_REPORT -->'} = ($ZOOVY::cgiv->{'filetype'} eq 'report')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_FILETYPE_SYNDICATION -->'} = ($ZOOVY::cgiv->{'filetype'} eq 'syndication')?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_FILETYPE_CSV -->'} = ($ZOOVY::cgiv->{'filetype'} eq 'csv')?'checked':'';

	if ($VERB eq '') {
		$GTOOLS::TAG{'<!-- RESULT_TITLE -->'} = "Recently added Private Files";
		$params{'active'} = 1;
		$params{'limit'} = 50;
		}
	elsif ($VERB eq 'SEARCH') {
		$GTOOLS::TAG{'<!-- RESULT_TITLE -->'} = "Search Results";
		if ($ZOOVY::cgiv->{'filetype'} ne '') { $params{'type'} = $ZOOVY::cgiv->{'filetype'}; }
		$params{'active'} = ($ZOOVY::cgiv->{'expired'})?1:0;
		$params{'keyword'} = $ZOOVY::cgiv->{'keyword'};
		}

	my ($results) = $lf->list(%params);

	#mysql> desc PRIVATE_FILES;
	#+-----------+-----------------------------------------+------+-----+---------+----------------+
	#| Field     | Type                                    | Null | Key | Default | Extra          |
	#+-----------+-----------------------------------------+------+-----+---------+----------------+
	#| ID        | int(10) unsigned                        | NO   | PRI | NULL    | auto_increment |
	#| USERNAME  | varchar(20)                             | NO   |     | NULL    |                |
	#| MID       | int(10) unsigned                        | NO   | MUL | 0       |                |
	#| CREATEDBY | varchar(10)                             | NO   |     | NULL    |                |
	#| CREATED   | datetime                                | YES  |     | NULL    |                |
	#| EXPIRES   | datetime                                | YES  |     | NULL    |                |
	#| TITLE     | varchar(50)                             | NO   |     | NULL    |                |
	#| FILENAME  | varchar(50)                             | NO   |     | NULL    |                |
	#| FILETYPE  | enum('TICKET','REPORT','DEBUG','OTHER') | YES  |     | OTHER   |                |
	#| META      | tinytext                                | NO   |     | NULL    |                |
	#+-----------+-----------------------------------------+------+-----+---------+----------------+
	#10 rows in set (0.01 sec)
	
	my @results = @{$results};
	if ($ZOOVY::cgiv->{'SORTBY'}) {
		## 
		
		}
	
	
	foreach my $fref (@results) {
		$c .= "<tr>";
	
		$c .= qq~<td valign=top><input type='checkbox' name="FILE:$fref->{'ID'}"></td>~;
		$c .= "<td valign=top>";
		
		if ($fref->{'FILETYPE'} eq 'REPORT') {
			## report viewer should ONLY used to be able types of FILES
			$c .= "<a href=\"/biz/reports/view.cgi?TYPE=$fref->{'FILETYPE'}&GUID=$fref->{'GUID'}\">View</a>";
			}
		else {
			$c .= "<a href=\"/biz/setup/private/index.cgi?VERB=VIEW&TYPE=$fref->{'FILETYPE'}&GUID=$fref->{'GUID'}&ID=$fref->{'ID'}\">View</a>";
			}
		$c .= "</td>";
	
	
		$c .= "<td nowrap valign=top>".&ZTOOLKIT::pretty_date($fref->{'CREATED_GMT'},4)."</td>";
		# FILENAME
		$c .= "<td valign=top>";
			$c .= $fref->{'TITLE'};
			$c .= "<div><font class='hint'>".$fref->{'%META'}->{'subtitle'}."</font></div>";
		$c .= "</td>";
		$c .= "<td valign=top>".$fref->{'FILETYPE'}."</td>";
		$c .= "<td valign=top>".$fref->{'SIZE'}."</td>";
		$c .= "<td valign=top>".$fref->{'EXPIRES'}."</td>";
		$c .= "<td valign=top>".$fref->{'CREATEDBY'}."</td>";
		$c .= "</tr>";
		}
	
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No private files found</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- FILES -->'} = $c;
	$template_file = 'index.shtml';
	}
	
&GTOOLS::output('*LU'=>$LU,bc=>\@BC,msgs=>\@MSGS,,file=>$template_file,header=>1);
