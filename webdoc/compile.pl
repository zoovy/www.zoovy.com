#!/usr/bin/perl

use lib "/httpd/modules";
use WEBDOC;
use Storable qw (store);

use XML::Parser;
use XML::Parser::EasyTree;
use XML::RSS;
$XML::Parser::Easytree::Noempty=1;
use Data::Dumper;
use strict;
use DBI;
use Storable;
use POSIX;





##
##
##


my $wdbh = &WEBDOC::db_webdoc_connect();

&compileMenu($wdbh);

&WEBDOC::db_webdoc_close();

exit;

my $pstmt = "select ID from WEBDOC_FILES"; 
my $sth = $wdbh->prepare($pstmt);
$sth->execute();
while ( my ($ID) = $sth->fetchrow() ) {
	print "ID: $ID\n";
	&WEBDOC::reindex($ID);
	}

&WEBDOC::db_webdoc_close();



exit;







__DATA__



my $ROOTPATH = "/home/webdoc/www_public";

%::MODIFIED = ();		# key = area/path/file	value = modified timestamp
%::PRETTYNAMES = ();	# key = area/path/file	value = properly escaped name e.g. 'Some Topic' (with quotes)

%::AREAS = (
	'' => 'Webdoc Home',
	'dev' => 'Developer',
	'ordermgr' => 'Order Manager',
	'webmgr' => 'Website Manager',
	'zwm' => 'Warehouse Manager',
	'webmail' => 'ZoovyMail',
	'info' => 'Guides',
	'market' => 'Marketplace',
	'enterprise' => 'Enterprise',
	'pkg-ebay' => 'Auction Seller Edition',
	'pkg-store' => 'StoreFront Edition',
	'pkg-media' => 'Media Edition',
	'pkg-apparel' => 'Apparel Edition',
	);
(undef,undef,$::WEBDOC_UID,$::WEBDOC_GID) = getpwnam('webdoc');

use lib "/home/modules";
use $wdbh = &WEBDOC::db_webdoc_connect();

###########################
### related docs
($actual) = &SYNCTOOL::actual_ts($dbh,'select concat(MAX(ID),count(*)) from RELATED_DOCS limit 0,1');
if ($::FORCEALL) { $actual = time()%$$; }
print "ACTUAL: $actual - ".&SYNCTOOL::get_ts('RELATED')."\n";
if (1 && ($actual ne &SYNCTOOL::get_ts('RELATED'))) {
	foreach my $area (keys %::AREAS) {		
		&buildRelated($dbh,$area,'detail'); 
		&buildRelated($dbh,$area,'guide'); 
		&buildRelated($dbh,$area,'topic');
		}
	&SYNCTOOL::set_ts('RELATED',$actual);
	}

###########################
### faq
($actual) = &SYNCTOOL::actual_ts($dbh,'select concat(MAX(ID),count(*)) from QUESTIONS limit 0,1');
if ($::FORCEALL) { $actual = time()%$$; }
print "ACTUAL: $actual - ".&SYNCTOOL::get_ts('FAQ')."\n";
if (1 && ($actual ne &SYNCTOOL::get_ts('FAQ'))) {
	foreach my $area (keys %::AREAS) {
		&buildFAQ($dbh,$area,'detail'); 
		&buildFAQ($dbh,$area,'guide'); 
		&buildFAQ($dbh,$area,'topic');
		}
	&SYNCTOOL::set_ts('FAQ',$actual);
	}

#### OZMO -- make sure he's feeling healthy
($actual) = &SYNCTOOL::actual_ts($dbh,'select concat(MAX(ID),count(*)) from QUESTIONS limit 0,1');
if ($::FORCEALL) { $actual = time()%$$; }
print "ACTUAL: $actual - ".&SYNCTOOL::get_ts('OZMO')."\n";
if (1 && ($actual ne &SYNCTOOL::get_ts('OZMO'))) {

	my %killwords = ( 'where'=>'', 'when'=>'', 'does'=>'', 'site'=>'', 'support'=>'',
      'i'=>'', 'with'=>'', 'for'=>'', 'can'=>'', 'what'=>'', 'the'=>'', 'how'=>'', 'is'=>'',
      'your'=>'', 'do'=>'', 'from'=>'', 'you'=>'', 'are' => '', 'my'=>'', 'a'=>'',
      'to'=>'', 'are'=>'', 'an'=>'', 'in'=>'', 'and'=>'', 'you'=>'', 'about'=>'',
		'have'=>'','why'=>'','get'=>'','learn'=>'','that'=>'','this'=>'','on'=>'','of'=>'',
		'there'=>'','all'=>'','will'=>'','it'=>'','but'=>'','our'=>'','want'=>'','way'=>'',
		'mean'=>'',
	);
	
	foreach my $k (keys %killwords) {
		my $pstmt = "delete from QUESTION_KEYWORDS where KEYWORD=".$dbh->quote($k);
		print $pstmt."\n";
		$dbh->do($pstmt);
		}

	## kill dupes (always save the last copy)
	my $pstmt = "select QUESTION,count(*) X from QUESTIONS group by QUESTION order by X desc limit 0,1";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($q,$count) = $sth->fetchrow() ) {
		if ($count>1) {
			$pstmt = "select ID,RESPONSE from QUESTIONS where QUESTION=".$dbh->quote($q)." order by ID desc limit 1,$count";
			my $sth2 = $dbh->prepare($pstmt);
			$sth2->execute();
			print "Q: $q\n\n";
			while ( my ($id,$response) = $sth2->fetchrow() ) {
				print "ID: $id RESPONSE: $response\n";
				$pstmt = "delete from QUESTIONS where ID=$id";
				print $pstmt."\n";
				$dbh->do($pstmt);
				$pstmt = "delete from QUESTION_KEYWORDS where PARENT=$id";
				print $pstmt."\n";
				$dbh->do($pstmt);
				}
			}
		}
	$sth->finish();

	## This validates OZMO links
	my $pstmt = "select ID,AREA,PATH from QUESTIONS";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $errors = 0;
	while ( my ($ID,$AREA,$PATH) = $sth->fetchrow() ) {
		next if ($AREA eq '');
		if ($PATH eq '') { $PATH = '/body.php'; }
		if (! -f "$ROOTPATH/$AREA/$PATH") {
			$errors++;
			print "ERROR: $ID $AREA $PATH\n";
			}
		}
	$sth->finish();
	if ($errors ) { 
		print "Found errors in ozmo - exiting\n"; 
		}

	&SYNCTOOL::set_ts('OZMO',$actual);
	}


if (1) {
	## BUILD THE SEARCH INDEX
	foreach my $area ('ordermgr','pkg-ebay','pkg-store','pkg-media','zwm','webmail','info','webmgr','dev','enterprise','market') {		
		($actual) = &SYNCTOOL::files_changed("$ROOTPATH/$area/detail",0);
		($actual) = &SYNCTOOL::files_changed("$ROOTPATH/$area/guide",$actual);
		($actual) = &SYNCTOOL::files_changed("$ROOTPATH/$area/topic",$actual);
		$actual = int($actual/3600);	# we only care if stuff changed in the last hour

		if ($::FORCEALL) { $actual = time()%$$; }
		my $KEY = uc("SEARCH-$area");
		print "!! $KEY: ACTUAL: $actual - ".&SYNCTOOL::get_ts($KEY)."\n";
		if (1 && ($actual ne &SYNCTOOL::get_ts($KEY))) {
			&nukeSearch($dbh,$area);
			&buildSearch($dbh,$area,'detail');
			&buildSearch($dbh,$area,'guide');
			&buildSearch($dbh,$area,'topic');
			&finishSearch($dbh,$area);
			&SYNCTOOL::set_ts($KEY,$actual);
			}
		}
	}

&compileMenu($dbh,'pkg-ebay');
&compileMenu($dbh,'pkg-store');
&compileMenu($dbh,'pkg-media');
&compileMenu($dbh,'pkg-apparel');
&compileMenu($dbh,'ordermgr');
&compileMenu($dbh,'zwm');
&compileMenu($dbh,'webmail');
&compileMenu($dbh,'webmgr');
&compileMenu($dbh,'info');
&buildRecent($dbh,'');
&compileMenu($dbh,'dev');
&compileMenu($dbh,'enterprise');
&compileMenu($dbh,'market');

$dbh->disconnect();

print "Finished!\n";



sub summarize_doc {
	my ($area,$file) = @_;


	my $buf = '';
	open Fzzz1, "<$ROOTPATH/$area/$file"; $/ = undef; $buf = <Fzzz1>; close Fzzz1;
	my $len = length($buf);
	
	$buf =~ s/<.*?>//gs;
	$buf =~ s/<//gs;
	$buf =~ s/>//gs;
	$buf = substr($buf,0,256);
	$buf .= "... ($len bytes total)";

	return($buf);
	}

sub buildRecent {
	my ($dbh,$area) = @_;

	my $pstmt = "select AREA,FILE,TITLE,MODIFIED_GMT from FILE_TITLES ";
	if ($area ne '') { 
		%::MODIFIED = ();
		%::PRETTYNAMES = ();
		$pstmt .= 'where AREA='.$dbh->quote($area); 
		}
	$pstmt .= " order by MODIFIED_GMT";
	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $latestts = 0;
	while ( my ($area,$file,$title,$mtime) = $sth->fetchrow() ) {
		if ($mtime>$latestts) { $latestts = $mtime; }
		$::MODIFIED{"$area/$file"} = $mtime;
		$::PRETTYNAMES{"$area/$file"} = $title;
		}
	$sth->finish();

	my $filename = "$ROOTPATH/$area/lastmodified";
	if ($area eq '') { $filename = "$ROOTPATH/lastmodified"; }
	my $count = 0;
	open Fp, ">$filename.php";
	open Fx, ">$filename.xml";

	my $rss = new XML::RSS (version => '1.0');
   $rss->channel(
      title        => ($area ne '')?("Webdoc Updates: ".$::AREAS{$area}):("Webdoc Updates - recent 25"),
      link         => "http://www.zoovy-ecommerce-docs.com/$area",
      description  => "The most recently updated documents in the Zoovy Online Documentation $::AREAS{$area} area.",
      dc => {
         date       => strftime("%Y-%m-%dT07:00+00:00",localtime($latestts)),
         subject    => "Zoovy Webdoc - ",
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

	foreach my $f (reverse &ZTOOLKIT::value_sort(\%::MODIFIED) ) {
		## F= pkg-ebay/detail/foo.php
		print STDERR "F: $f\n";
		my $skip = 0;
		if ($f !~ /^$area/) {
			if ($area =~ /^pkg-/) { 
				if ($f =~ /^ordermgr/) { }
				elsif ($f =~ /^zwm/) { }
				elsif ($f =~ /^webmail/) { }
				elsif ($f =~ /^webmgr/) { }
				elsif ($f =~ /^info/) { }
				else { $skip++; }
				}
			else {
				$skip++;
				}
			};
		next if ($skip);

		my $pretty = unPHPescape($::PRETTYNAMES{$f});
		next if (not defined $pretty);
		my $fpath = $f;
		my $thisAREA = '';
		my $file = '';
		if ($area ne '') {
			$fpath =~ s/^$area\///;
			$file = $fpath; 
			$fpath = "$area/index.php?GOTO=$fpath";
			$thisAREA = $area;
			}
		else {
			$thisAREA = substr($fpath,0,index($fpath,'/'));
			$fpath = substr($fpath,index($fpath,'/')+1);
			$file = $fpath;
			$pretty = $::AREAS{$thisAREA}.": $pretty";
			$fpath = "/$thisAREA/index.php?GOTO=$fpath";
			}

		print "AREA: $thisAREA [$count]\n";
		my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($::MODIFIED{$f});
		$mon += 1;

		if ($count<=25) {
      	$rss->add_item(
				title       => $pretty,
         	link        => "http://webdoc.zoovy.com/$fpath",
         	description => $::AREAS{$thisAREA}.": ".&summarize_doc($thisAREA,$file),
         	dc => {
           		date => strftime("%Y-%m-%dT07:%H+%M:%S",localtime($::MODIFIED{$f})),
            	subject  => "$pretty",
            	creator  => "Support (support\@zoovy.com)",
            	},
				taxo => [
					"http://webdoc.zoovy.com/$area/",
					"http://webdoc.zoovy.com/$area/$fpath",
					'http://dmoz.org/Computers/Software/Business/E-Commerce/'
	            ]
				);
			}

		if ($count<=5) {
			my $icon = "/images/blank.gif";
			my $playerfile = "$ROOTPATH/".substr("$f",0,-4).'.player';
			$playerfile =~ s/[\/]+/\//gs;		# removes www_public//area
			if (-f $playerfile) { $icon = "/images/tv_icon.jpg"; }
			print "PLAYERFILE: $playerfile [$icon]\n";
			
			my $date = sprintf("%02d-%02d-%02d",$mon,$mday,$year%100);
			print Fp qq~
				<tr>
				<td><a href="http://webdoc.zoovy.com/$fpath"><img border=0 width=25 height=25 src='$icon'></a></td>
				<td><a target="_top" href="http://webdoc.zoovy.com/$fpath">$pretty</a></td><td nowrap valign='top'>$date</td>
				</tr>~;
			}

		$count++;
		}

   print Fx $rss->as_string;

	close Fx;
	close Fp;
	chown($::WEBDOC_UID,"$filename.xml");
	chmod(0755,"$filename.xml");
	chown($::WEBDOC_UID,"$filename.php");
	chmod(0755,"$filename.php");
	
#	print Dumper(\%::MODIFIED);
	}


sub finishSearch {
	my ($dbh,$area) = @_;

	my $filename = "$ROOTPATH/$area/sitemap.html";
	open F, ">>$filename";
	print F "</td></tr></table></center></body>";
	close F;
	chown($::WEBDOC_UID,$filename);
	chmod(0664,$filename);
	}

sub nukeSearch {
	my ($dbh,$area) = @_;

	my $filename = "$ROOTPATH/$area/sitemap.html";
	unlink($filename);
	open F, ">$filename";
	print F "<head><link rel=\"STYLESHEET\" type=\"text/css\" href=\"http://webdoc.zoovy.com/webdoc.css\"><meta name=\"description\" content=\"$area\">\n<meta name=\"keywords\" content=\"$area\">\n<title>List of ".uc($area)." documents</title></head><body><center><table width='500'><tr><td><a href=\"/sitemap.html\">general sitemap!</a><br>\n";

	print F "<h1>".uc($area)."</h1><hr>\n";
	print F "<a href=\"/search.php?map=$area\">Detailed Search</a><br>\n";
	close F;
	chown($::WEBDOC_UID,$filename);
	chmod(0664,$filename);

	my $qtAREA = $dbh->quote($area);
	my $pstmt = "delete from FILE_TITLES where AREA=".$qtAREA;
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);

	my $pstmt = "delete from KEYWORDS where AREA=".$qtAREA;
	print STDERR $pstmt."\n";
	$dbh->do($pstmt);
	}

##
## indexes all the files in the directory
## 	dbh should be a valid database handle
##		sub should be a subtype e.g. detail,guide
##		area should be a topic level category e.g. info,zwm,ordermgr


################################### MENU FUNCTIONS

## root function, pass this:
##	path (e.g. ordermgr), pretty name of menu (e.g. Order Manager)
	}


## turns a name into a javascript safe variable
sub make_js_safevar {
	my ($name) = @_;
	$name =~ s/\W+//g;
	$name = 'Z'.$name;
	return($name);
}

############################################################
## adds the javascript for a guide
sub parseGuide {
	my ($path,$menuname,$node) = @_;

	my $name = $node->{'attrib'}->{'name'};
	my $file = $node->{'attrib'}->{'file'};
	if (substr($file,0,1) eq '/') {
		## this one changes areas
		## interesting!
		}
	else {
		## this is a relative topic
		## e.g. type/doc.php - do nothing
		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat("$path/$file");
		$::MODIFIED{"$path/$file"} = $mtime;
		$/ = undef; open F, "$ROOTPATH/$path/$file"; my $BUF = <F>; close F; $/ = "\n";
		if ($BUF =~ /webdoc_guide_header\((.*?)\)/s) {
			$::PRETTYNAMES{"$path/$file"} = $1;
			}
		}

	if ($file eq '') {
		$file = "/blank.php?type=guide&name=$name";
		}

	print "Adding guide $name [$file]\n";
	return("$menuname.addItem(\"$name\",\"$file\");\n");
}

###############################################################
## adds the javascript for a topic
sub parseDetail {
	my ($path,$menuname,$node) = @_;

	my $name = $node->{'attrib'}->{'name'};
	my $file = $node->{'attrib'}->{'file'};

	if (substr($file,0,1) eq '/') {
		## this one changes areas
		## interesting!
		}
	else {
		## this is a relative topic
		## e.g. type/doc.php - do nothing

		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat("$path/$file");
		$::MODIFIED{"$path/$file"} = $mtime;
		$/ = undef; open F, "$ROOTPATH/$path/$file"; my $BUF = <F>; close F; $/ = "\n";
		if ($BUF =~ /webdoc_detail_header\((.*?)\)/s) {
			$::PRETTYNAMES{"$path/$file"} = $1;
			}
		}

	if ($file eq '') {
		$file = "/blank.php?type=detail&name=$name";
		}
		
	print "Adding TOPIC $name [$file]\n";
	return("$menuname.addItem(\"$name\",\"$file\");\n");
	
}

sub unPHPescape {
	my ($t) = @_;
	# yeah, I know i need to do more here
	$t =~ s/"//g;
	$t =~ s/'//g;
	return($t);
	}


sub buildRelated {
	my ($dbh,$area,$type) = @_;

	if (! -d "$ROOTPATH/$area/related") {
		mkdir("$ROOTPATH/$area/related");
		}

	if (! -d "$ROOTPATH/$area/related/$type") {
		mkdir("$ROOTPATH/$area/related/$type");
		}

	## read in the files which have already been created (make sure we don't have any which should be deleted)
	my %EXISTING = ();
	my %SAVE = ();
	opendir my $d, "$ROOTPATH/$area/related/$type";
	while ( my $file = readdir($d) ) {
		next if (substr($file,0,1) eq '.');
		$EXISTING{"$type/$file"}++;
		}
	closedir($d);

	my $qtarea = $dbh->quote($area);
	my $pstmt = "select SRC_FILE from RELATED_DOCS where SRC_AREA=".$qtarea." group by SRC_FILE";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($src_file) = $sth->fetchrow() ) {
		next if ($src_file !~ /^$type/);
		delete $EXISTING{$src_file};
		print "AREA: $area SRC: $src_file\n";
		$pstmt = "select DEST_AREA,DEST_FILE from RELATED_DOCS where SRC_AREA=".$qtarea." and SRC_FILE=".$dbh->quote($src_file);
		my $sth2 = $dbh->prepare($pstmt);
		$sth2->execute();
		print "UPDATING: $ROOTPATH/$area/related/$src_file\n";
		unlink("$ROOTPATH/$area/related/$src_file");
		$SAVE{"$area/$src_file"}++;
		my $filename = "$ROOTPATH/$area/related/$src_file";
		open F, ">$filename";
		while ( my ($dest_area,$dest_file) = $sth2->fetchrow() ) {
			next if (! -f "$ROOTPATH/$dest_area/$dest_file");
			print "DEST FILE: $dest_area $dest_file\n";
			my $title = &resolve_pathname($dbh,$dest_area,$dest_file);		
			print F "<a target=\"_top\" href=\"/$dest_area/index.php?GOTO=$dest_file\">$title</a><br>\n";
			}
		close F;
		chown($::WEBDOC_UID,$filename);
		chmod(0664,$filename);
		$sth2->finish();
		}

	my $qtarea = $dbh->quote($area);
	my $pstmt = "select DEST_FILE from RELATED_DOCS where DEST_AREA=".$qtarea." and LINKBACK=1 group by DEST_FILE";
	print STDERR $pstmt."\n";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($src_file) = $sth->fetchrow() ) {
		next if ($src_file !~ /^$type/);
		delete $EXISTING{$src_file};
		print "LINKBACK AREA: $area SRC: $src_file\n";
		$pstmt = "select SRC_AREA,SRC_FILE from RELATED_DOCS where LINKBACK=1 and DEST_AREA=".$qtarea." and DEST_FILE=".$dbh->quote($src_file);
		my $sth2 = $dbh->prepare($pstmt);
		$sth2->execute();
		my $filename = "$ROOTPATH/$area/related/$src_file";
		if (not $SAVE{"$area/$src_file"}) {
			unlink("$filename");
			}
		open F, ">>$filename";
		while ( my ($dest_area,$dest_file) = $sth2->fetchrow() ) {
			next if (! -f "$ROOTPATH/$dest_area/$dest_file");
			print "DEST FILE: $dest_area $dest_file\n";
			my $title = &resolve_pathname($dbh,$dest_area,$dest_file);		
			print F "<a target=\"_top\" href=\"/$dest_area/index.php?GOTO=$dest_file\">$title</a><br>\n";
			}
		close F;
		chown($::WEBDOC_UID,$filename);
		chmod(0664,$filename);
		$sth2->finish();
		}
	
	## nuke any which are no longer needed
	foreach my $file (keys %EXISTING) {
		print "NUKE FILE: $file\n";
		}
		
	}


sub buildFAQ {
	my ($dbh,$area,$type) = @_;

	if (! -d "$ROOTPATH/$area/faq") {
		mkdir("$ROOTPATH/$area/faq");
		}

	if (! -d "$ROOTPATH/$area/faq/$type") {
		mkdir("$ROOTPATH/$area/faq/$type");
		}

	## read in the files which have already been created (make sure we don't have any which should be deleted)
	my %EXISTING = ();
	opendir my $d, "$ROOTPATH/$area/faq/$type";
	while ( my $file = readdir($d) ) {
		next if (substr($file,0,1) eq '.');
		$EXISTING{"$type/$file"}++;
		}
	closedir($d);

	my $qtarea = $dbh->quote($area);
	my $pstmt = "select PATH from QUESTIONS where FAQ>0 and AREA=".$qtarea." group by PATH";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($path) = $sth->fetchrow() ) {
		next if ($path !~ /^$type/);
		delete $EXISTING{$path};
		print "AREA: $area SRC: $path\n";
		$pstmt = "select ID,QUESTION,RESPONSE from QUESTIONS where AREA=$qtarea and PATH=".$dbh->quote($path)." and FAQ>0 order by SCORE_HELPFUL desc";
		my $sth2 = $dbh->prepare($pstmt);
		$sth2->execute();
		my $filename = "$ROOTPATH/$area/faq/$path";
		unlink($filename);
		open F, ">$filename";
		print F "<table>\n";
		while ( my ($id,$question,$response) = $sth2->fetchrow() ) {
			print F "<tr><td><font size=1>FAQ #$id:</font><br>";
			print F "<b>$question?</b>\n<br>";
			print F "$response<br>\n</td></tr><tr><td><img src='/images/blank.gif' height=3 width=100%></td></tr>\n\n";
			}
		print F "</table>";
		close F;
		chown($::WEBDOC_UID,$filename);
		chmod(0664,$filename);
		$sth2->finish();
		}
	
	## nuke any which are no longer needed
	foreach my $file (keys %EXISTING) {
		print "NUKE FILE: $file\n";
		unlink("$ROOTPATH/$area/faq/$file");
		}
		
	}







sub resolve_pathname {
   my ($dbh,$area,$path) = @_;
  my $pstmt = "select TITLE from FILE_TITLES where AREA=".$dbh->quote($area)." and FILE=".$dbh->quote($path);
   my $sth = $dbh->prepare($pstmt);
   $sth->execute();
   my $title = '';
   if ($sth->rows()) {
      ($title) = $sth->fetchrow();
      if (defined $::AREAS{$area}) {
         $title = "$::AREAS{$area} : $title";
         }
      }
   else {
      $title = "Webdoc $area/$path";
      }
   $sth->finish();
   return($title);
}

