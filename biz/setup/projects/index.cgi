#!/usr/bin/perl

use Archive::Zip;
use URI::Escape;
use Data::Dumper;
use Data::GUID;
use lib "/httpd/modules";
require  ZOOVY;
require GTOOLS;
require PROJECT;
use strict;

my @MSGS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};

my ($udbh) = &DBINFO::db_user_connect($USERNAME);
my @BC = ();
push @BC, { name=>'Setup', link=>'/biz/setup/index.cgi', };
push @BC, { name=>'Projects', link=>'/biz/setup/projects/index.cgi', };

my ($q) = CGI->new();


if ($VERB eq 'PROJECT-DELETE') { 
	my ($ID) = int($ZOOVY::cgiv->{'ID'});
	my ($P) = PROJECT->new($USERNAME,'ID'=>$ID);
	$P->delete();
	push @MSGS, "SUCCESS|Deleted project $ID";
	$VERB = '';
	}

if ($VERB eq 'PROJECT-COPY') {
	my ($project) = $q->param('PROJECT');
	my ($P) = PROJECT->create($USERNAME,$project);
	my ($ERROR) = $P->copyfrom($project);
	if ($ERROR) {
		push @MSGS, "ERROR|$ERROR";
		$VERB = 'PROJECT-BROWSE';
		}
	else {
		push @MSGS, sprintf("SUCCESS|Copy to project %s",$P->uuid());
		$VERB = '';
		}
	}

if ($VERB eq 'PROJECT-BROWSE') {
	$template_file = 'project-browse.shtml';

	my $c = '';
	opendir my $D, "/httpd/static/apps";
	while ( my $file = readdir($D) ) {
		next if (substr($file,0,1) eq '.');
		next if (substr($file,0,1) eq '_');	# hidden
		$c .= qq~
<div>
<input type="button" class="button" value=" Select " onClick="document.thisFrm.PROJECT.value='$file'; document.thisFrm.submit();"> $file
</div>
~;
		}
	closedir $D;
	$GTOOLS::TAG{'<!-- PROJECTS -->'} = $c;
	}


#if ($VERB eq 'PROJECT-UPLOAD') {
#	my ($ID) = int($ZOOVY::cgiv->{'ID'});
#	my $fh = $q->param('upfile');
#	my $BUFFER = '';
#	my $filename = $fh;
#	my $ERROR = '';
#
#	print STDERR "FILENAME: $filename\n";
#	if ($filename =~ /\.zip$/i) {
#		$VERB = 'PROJECT-UPLOADZIP';
#		}
#
#	if ($ID<=0) {
#		push @MSGS, "PROJECT ID is not defined!";
#		}
#	elsif (not defined $fh) {
#		## crap not defined
#		push @MSGS, "ERROR|Invalid file handle";
#		}
#	elsif (defined $fh) {
#		while (<$fh>) { $BUFFER .= $_; }
#		}
#
#
#	my ($P) = PROJECT->new($USERNAME,ID=>$ID);
#	my ($UUID) = $P->uuid();
#	push @MSGS, "WARN|UUID:$UUID";
#	
#	my $USERPATH = &ZOOVY::resolve_userpath($USERNAME);
#	if (! -d "$USERPATH/PROJECTS") {
#		mkdir("$USERPATH/PROJECTS");
#		chmod(0777, "$USERPATH/PROJECTS");
#		}
#	if (! -d "$USERPATH/PROJECTS/$UUID") {
#		mkdir("$USERPATH/PROJECTS/$UUID");
#		chmod(0777, "$USERPATH/PROJECTS/$UUID");
#		}
#
#	if ($VERB eq 'PROJECT-UPLOAD') {
#		## convert S:\path\to\file.jpg to just file.jpg
#		if (index($filename,'\\')>=0) { $filename = substr($filename,rindex($filename,'\\')+1); }
#		## convert dir/file.jpg to just file.jpg
#		if (index($filename,'/')>=0) { $filename = substr($filename,rindex($filename,'/')+1); }
#		$filename = lc($filename);
#
#		open F, ">$USERPATH/PROJECTS/$UUID/$filename";
#		print F $BUFFER;
#		close F;
#
#		push @MSGS, "SUCCESS|wrote file /$filename";
#		}	
#	elsif ($VERB eq 'PROJECT-UPLOADZIP') {
#		open F, ">/tmp/zipupload.$$.zip";
#		print F $BUFFER;
#		close F;
#
#		my $zip = Archive::Zip->new();
#		die 'read error' if $zip->read( "/tmp/zipupload.$$.zip" ) != $Archive::Zip::AZ_OK;
#
#		my $ROOT = '';
#		my $filenamewithoutzip = $filename;
#		$filenamewithoutzip =~ s/\.zip$//gsi;
#		foreach my $member ($zip->members()) {
#			next if ($ROOT ne '');
#			if ($member->fileName() =~ /^$filenamewithoutzip\//) { $ROOT = $filenamewithoutzip; }
#			}
#		if ($ROOT ne '') {
#			push @MSGS, "WARN|Guessed ROOT directory in Zip: $ROOT"; 
#			}
#
#		my ($r) = $zip->extractTree( $ROOT, "$USERPATH/PROJECTS/$UUID/" );
#
#		my $c = '';
#		foreach my $member ($zip->members()) {
#			# print Dumper($member);
#
#			# my $BUF = $zip->contents( $member ); 
#			# print $member->fileName()." length: ".length($foo)." []\n";
#			my ($filename) = $member->fileName();
#			if ($ROOT ne '') { $filename =~ s/^$ROOT\//\//s; }
#			push @MSGS, "SUCCESS|Decompressed $filename";
#			}
#		$GTOOLS::TAG{'<!-- MESSAGE -->'} = $c;
#		}
#	else {
#		push @MSGS, "ERROR|Sorry, your files were not uploaded";
#		}
#
#	$VERB = 'PROJECT-EDIT';
#	}
#
#


if ($VERB eq 'PROJECT-EDIT') {
	my ($ID) = $ZOOVY::cgiv->{'ID'};
	$GTOOLS::TAG{'<!-- ID -->'} = $ID;
	$template_file = 'project-edit.shtml';
	push @BC, { name=>'Edit' };

	my ($P) = PROJECT->new($USERNAME,'ID'=>$ID);
	my $filesref = $P->allFiles();
	if (scalar(@{$filesref})==0) {
		}
	else {
		my $found_index = 0;
		foreach my $file (@{$filesref}) {
			# push @MSGS, "WARN|$file->[1]|$file->[2]|$file->[3]";
			if (($file->[2] eq 'index.html') && ($file->[1] eq '/')) {
				$found_index++;
				}
			}
		if (not $found_index) {
			push @MSGS, "WARN|Missing index.html file, this project will not work.";
			}
		}
	my $c = '';
	foreach my $file (@{$filesref}) {
		next if ($file->[0] ne 'F');
		$c .= "<tr><td>$file->[1]</td><td>$file->[2]</td><td>$file->[3]</td><td>".&ZTOOLKIT::pretty_date($file->[4],-3)."</td></tr>\n";
		}
	if ($c eq '') {
		$c .= "<tr><td><div class='warning'>No files found in project</td></tr>";
		}
	$GTOOLS::TAG{'<!-- FILES -->'} = $c;
	}

##
##
##

if ($VERB eq 'PROJECT-ADD-SAVE') {
	my $TITLE = $ZOOVY::cgiv->{'title'};


	my $ERROR = undef;	
	my $REPO = $ZOOVY::cgiv->{'repo'};
	if ($REPO ne '') {
		if ($REPO !~ /^http\:/) { $ERROR = "ERROR|+REPO must be http:"; }
		if ($REPO !~ /^http\:\/\/[a-z0-9A-Z\-\_\:\/\.]+$/) { $ERROR = "ERROR|+REPO contains prohibited characters"; }
		}

	my $domain = ($ZOOVY::cgiv->{'domain'})?1:0;
	my $TYPE = $ZOOVY::cgiv->{'type'};
	if ($TYPE eq '') {
		$ERROR = "ERROR|+PROJECT TYPE is required";
		}

	if ($domain) {
		if ($TYPE eq 'DSS') { $ERROR = "ERROR|+DSS Projects do not require a domain"; }
		}

	if ($TITLE eq '') {
		$ERROR = "ERROR|+TITLE is required";
		}

	my $UUID = Data::GUID->new()->as_string();
	$UUID = substr($UUID,0,32); ## restrict to 32 characters for db length
	if ($TYPE eq 'DSS') {	$UUID = "dss"; }

	my $BRANCH = uc(sprintf("%s",$ZOOVY::cgiv->{'branch'}));
	if (($ERROR eq '') && ($BRANCH ne '')) {
		if ($BRANCH =~ /^[^A-Z0-9]/) { $ERROR = "ERROR|+invalid characters in start of branch name"; }
		if ($BRANCH =~ /[^A-Z0-9\-\_]/) { $ERROR = "ERROR|+invalid characters in branch name '$BRANCH' (allowed A-Z 0-9 - _)"; }
		}

	if (defined $ERROR) {
		push @MSGS, "$ERROR";
		}
	elsif (scalar(@MSGS)==0) {	
		if ($REPO ne '') {
			my $path = sprintf("%s/PROJECTS/%s",&ZOOVY::resolve_userpath($USERNAME),$UUID);
			## /usr/local/bin/git clone http://github.com/brianhorakh/linktest.git /remote/snap/users/b/brian/PROJECTS/e8b9f059-a695-11e1-9cc4-1560a415
			my $BRANCH_PARAM = '';
			if ($BRANCH) { $BRANCH_PARAM = " -b $BRANCH "; }
			my $CMD = "/usr/local/bin/git clone $BRANCH_PARAM $REPO $path  > /dev/null";
			print STDERR "$CMD\n";
			system("$CMD");
			## chmod 777 -R /remote/crackle/users/e/erich/PROJECTS/7C62B56A-101C-11E2-9284-F4273A9C/.git/FETCH_HEAD
			if (-d $path) {
				push @MSGS, "SUCCESS|REPO was cloned";
				}
			else {
				push @MSGS, $ERROR = "ERROR|+REPO could not be created, please try again";
				}
			}
		else {
			push @MSGS, "SUCCESS|Added project $UUID";
			}
		}

	if ($TITLE eq '') { 
		$TITLE = "Untitled Project ".&ZTOOLKIT::pretty_date(time()); 
		}

	if (not defined $ERROR) {
		my ($pstmt) = &DBINFO::insert($udbh,'PROJECTS',{
			MID=>&ZOOVY::resolve_mid($USERNAME),
			USERNAME=>$USERNAME,
			TITLE=>$TITLE,
			UUID=>"$UUID",
			SECRET=>'secret',
			GITHUB_REPO=>$REPO,
			GITHUB_BRANCH=>$BRANCH,
			TYPE=>$TYPE,
			},sql=>1);
		print STDERR $pstmt."\n";
		$udbh->do($pstmt);
		$VERB = '';

		if ($domain) {
			my %options = ();
			$options{'WWW_HOST_TYPE'} = $TYPE;
			$options{'%WWW_CONFIG'} = { 'PROJECT'=>$UUID };
			$options{'M_HOST_TYPE'} = $TYPE;
			$options{'%M_CONFIG'} = { 'PROJECT'=>$UUID };
			$options{'APP_HOST_TYPE'} = $TYPE;
			$options{'%APP_CONFIG'} = { 'PROJECT'=>$UUID };			
			require DOMAIN::POOL;
			my ($DOMAINNAME) = &DOMAIN::POOL::reserve($USERNAME,$PRT,%options);
			push @MSGS, "SUCCESS|+DOMAIN '$DOMAINNAME' was reserved for project $UUID";
			}
		}


	if ($ERROR) {
		$VERB = 'PROJECT-ADD';
		}
	}

if ($VERB eq 'PROJECT-ADD') {
	$template_file = 'project-add.shtml';
	}



if ($VERB eq '') {

	my %PROJECTS = ();
	my $pstmt = "select DOMAIN,WWW_HOST_TYPE,WWW_CONFIG,M_HOST_TYPE,M_CONFIG,APP_HOST_TYPE,APP_CONFIG from DOMAINS where MID=$MID";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ( $DOMAIN,$WWW,$WWW_CONFIG,$M,$M_CONFIG,$APP,$APP_CONFIG ) = $sth->fetchrow() ) {
		my $wwwcfg = &ZTOOLKIT::parseparams($WWW_CONFIG);
		my $mcfg = &ZTOOLKIT::parseparams($M_CONFIG);
		my $appcfg = &ZTOOLKIT::parseparams($APP_CONFIG);
		if ($wwwcfg->{'PROJECT'}) { push @{$PROJECTS{$wwwcfg->{'PROJECT'}}}, "www.$DOMAIN"; }
		if ($mcfg->{'PROJECT'}) { push @{$PROJECTS{$mcfg->{'PROJECT'}}}, "m.$DOMAIN"; }
		if ($appcfg->{'PROJECT'}) { push @{$PROJECTS{$appcfg->{'PROJECT'}}}, "app.$DOMAIN"; }
		}
	$sth->finish();

	my $pstmt = "select * from PROJECTS where MID=$MID /* $USERNAME */ order by ID";
	my ($sth) = $udbh->prepare($pstmt);
	my @ROWS = ();
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		push @ROWS, $hashref;
		if (not defined $PROJECTS{ $hashref->{'UUID'} }) { 
			# $PROJECTS{$hashref->{'UUID'}} = [];
			}
		}
	$sth->finish();

	if (scalar(@ROWS)==0) {
		$GTOOLS::TAG{'<!-- PROJECTS -->'} = '<tr><td><i>No projects, please add one</i></td></tr>';
		}
	else {
		my $c = '';
		foreach my $row (@ROWS) {
			my $link = '';
			if ($row->{'GITHUB_REPO'}) {
				my ($key) = Digest::MD5::md5_hex($row->{'SECRET'}.$row->{'UUID'});
				$link = "https://webapi.zoovy.com/webapi/git/webhook.cgi/v=1/u=$USERNAME/p=$row->{'UUID'}/k=$key";
				}
			else {
				$link = '<i>No Repo Linked</i>';
				}

			my $branch = $row->{'GITHUB_BRANCH'};
			if ($branch eq '') { $branch = 'master'; }

			my $BUTTONS = '';
			$BUTTONS .= "<a href='/biz/setup/projects/index.cgi?VERB=PROJECT-EDIT&ID=$row->{'ID'}'>[EDIT]</a><br>";
			$BUTTONS .= "<a href='/biz/setup/projects/index.cgi?VERB=PROJECT-DELETE&ID=$row->{'ID'}'>[DELETE]</a><br>";
			
			my $domains = '';
			if (not defined $PROJECTS{ $row->{'UUID'} }) {
				## 
				}
			elsif (scalar(@{$PROJECTS{ $row->{'UUID'} }} )>0) {
				foreach my $domain (@{$PROJECTS{$row->{'UUID'}}}) {
					$domains .= "<li>$domain</li>";
					}
				}
			else {
				$domains .= "<i>None</i>";
				}

			my $ID = $row->{'ID'};
			$c .= "<tr>
<td valign=top>$BUTTONS</td>
<td valign=top>$row->{'TYPE'} : $row->{'TITLE'}</td>
<td valign=top>$row->{'UUID'}</td>
<td valign=top>$row->{'UPDATED_TS'}</td>
<td valign=top>
	<div>Branch: $branch</div>
	<div>Domains: $domains</div>
	<div>Callback URL: <a href=\"#\" onClick=\"jQuery('#callback$ID').removeClass('displayNone'); jQuery(this).hide();\">Show</a>
<div id=\"callback$ID\" class=\"displayNone\">$link</div></div>
	</td>
</tr>\n";
			}

		# $c .= Dumper(\%PROJECTS);
		$GTOOLS::TAG{'<!-- PROJECTS -->'} = $c;
		}


	$template_file = 'index.shtml';
	}


my @TABS = ();
push @TABS, { name=>'Projects', link=>'/biz/setup/projects/index.cgi', selected=>($VERB eq '')?1:0 };
#push @TABS, { name=>'Browse Samples', link=>'/biz/setup/projects?VERB=PROJECT-BROWSE', selected=>($VERB eq 'PROJECT-BROWSE')?1:0 };
push @TABS, { name=>'Add New', link=>'/biz/setup/projects/index.cgi?VERB=PROJECT-ADD', selected=>($VERB eq 'PROJECT-ADD')?1:0 };




&GTOOLS::output('*LU'=>$LU,file=>$template_file,header=>1,
	tabs=>\@TABS,
	msgs=>\@MSGS,
	'jquery'=>'1',
	bc=>\@BC,
	'zmvc'=>1,
	todo=>1
	);

&DBINFO::db_user_close(); 