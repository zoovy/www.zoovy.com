#!/usr/bin/perl

use Archive::Zip;
use lib "/httpd/modules";
require GTOOLS;
require MEDIA;
require ZOOVY;
require LUSER;
require ZURL;
require ZTOOLKIT;
use strict;
use Data::Dumper;

&GTOOLS::init();
&ZOOVY::init();


my $template_file = 'index.shtml';

my $q = new CGI;

my ($LU) = LUSER->authenticate(flags=>'_S&4|_P&1');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

#my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&4|_P&1');
#if ($USERNAME eq '') { exit; }

%GTOOLS::TAG = ();

my $ACTION = $ZOOVY::cgiv->{'ACTION'};
if ($ACTION eq '') { $ACTION = 'LIST'; }
my $PWD = $ZOOVY::cgiv->{'PWD'};
if ($PWD eq '') { $PWD = '/'; }
$PWD =~ s/[^\w\/]+/_/gs;		# clear out unpleasant characters
$PWD =~ s/[\/]+/\//gs;		# make sure we don't have any //
$PWD =~ s/[\.]+/\./gs;		# replace .. with .

if (substr($PWD,0,1) eq '/') { $PWD = substr($PWD,1); }		# strip leading / slash

my $PATH = &ZOOVY::resolve_userpath_zfs1($USERNAME).'/IMAGES/';

print STDERR "ACTION IS: $ACTION\n";

##
## deletes an image, and all it's instances
##
if ($ACTION eq 'DELETE') {
	my $FILE = $ZOOVY::cgiv->{'FILE'};
	&MEDIA::nuke($USERNAME,"$PWD/$FILE");
	$LU->log("SETUP.MEDIA.NUKEIMG","Deleting image $PWD/$FILE","SAVE");
	$ACTION = 'LIST';
	}

##
## generates the HTML at the top of the preview
##
if ($ACTION eq 'HTML') {
	my $image = $ZOOVY::cgiv->{'PWD'}.'/'.$ZOOVY::cgiv->{'FILE'};
	my $width = $ZOOVY::cgiv->{'WIDTH'};
	my $height = $ZOOVY::cgiv->{'HEIGHT'};
	my ($zoom);
	if (defined($ZOOVY::cgiv->{'ZOOM'})) { $zoom = 1; } else { $zoom = 0; }
	my $src = &GTOOLS::imageurl($USERNAME,$image,$height,$width);
	my $zoomsrc = &GTOOLS::imageurl($USERNAME,$image,0,0);
	if ($width ne '') { $width = "width=\"$width\" "; } else { $width = ''; }
	if ($height ne '') { $height = "height=\"$height\" "; } else { $height = ''; }

	my $HTML = '';
	if ($zoom) { $HTML .= "&lt;a href=\"$zoomsrc\" target=\"_blank\" border=\"0\"&gt;\n"; }
	$HTML .= "&lt;img src=\"$src\" ${width}${height}border=\"0\"&gt;\n";
	if ($zoom) { $HTML .= "&lt;/a&gt;\n"; }

	$GTOOLS::TAG{'<!-- HTML -->'} = qq~
	<table border='1'><tr><td>
	HTML CODE (copy and paste this into any HTML document):<br>
	<form><textarea cols='100' rows='3'>$HTML</textarea></form><br>
	<br><b>Preview:</b><br>
	~.&ZOOVY::dcode($HTML).qq~
	<br>
	Note: You can easily adjust the Width and Height by altering the W and H parameters in the image URL.<br>
	</td></tr></table>	
	~;
	$ACTION = 'FILE';
	}


##
## this displays the files detail page
if ($ACTION eq 'FILE') {
	my $FILE = $ZOOVY::cgiv->{'FILE'};

	$GTOOLS::TAG{'<!-- FULLFILE -->'} = "$PWD/$FILE";
	$GTOOLS::TAG{'<!-- FILE -->'} = "$FILE"; 
	$GTOOLS::TAG{'<!-- IMAGETHUMB -->'} = &GTOOLS::imageurl($USERNAME,"$PWD/$FILE",120,120,'ffffff',undef);
	$GTOOLS::TAG{'<!-- ORIGURL -->'} = &GTOOLS::imageurl($USERNAME,"$PWD/$FILE",0,0,undef,undef);

	# my $iref = &IMGLIB::load_collection_info($USERNAME,"$PWD/$FILE");
	my $iref = &MEDIA::getinfo($USERNAME,"$PWD/$FILE",DETAIL=>1);
	# print STDERR Dumper($iref);
	#$VAR1 = {
   #       'orig_timestamp' => '1093846550',
   #       'original' => '2lesfuck.jpg',
   #       'ver' => '1.3',
   #       'orig_height' => 352,
   #       'orig_width' => 637,
   #       'created' => '1093907239',
   #       'subs' => {},
   #       'orig_filesize' => 41938
   #     };


	$GTOOLS::TAG{'<!-- FILESIZE -->'} = sprintf("%.1f",$iref->{'MasterSize'} / 1000).'k';
	$GTOOLS::TAG{'<!-- DIMENSIONS -->'} = $iref->{'W'}.' x '.$iref->{'H'};
	$GTOOLS::TAG{'<!-- FORMAT -->'} = uc( $iref->{'Format'} );
	$GTOOLS::TAG{'<!-- MODIFIED -->'} = &ZTOOLKIT::pretty_date($iref->{'TS'},1);

	$template_file = 'detail.shtml';
	}




if ($ACTION eq 'UPLOADFILE') {

	my $fh = $q->param('upfile');
	my $BUFFER = '';
	my $filename = $fh;
	my $ERROR = '';

	print STDERR "FILENAME: $filename\n";
	if ($filename =~ /\.zip$/i) {
		$ACTION = 'UPLOADZIP';
		}
	elsif (not defined $fh) {
		## crap not defined
		}
	elsif ($filename =~ m/^http[s]?:\/\//i) {
		$BUFFER = &ZURL::snatch_url($filename.'');
		}
	elsif (defined $fh) {
		while (<$fh>) { $BUFFER .= $_; }
		}

	if ($ACTION eq 'UPLOADFILE') {
		## convert S:\path\to\file.jpg to just file.jpg
		if (index($filename,'\\')>=0) { $filename = substr($filename,rindex($filename,'\\')+1); }
		## convert dir/file.jpg to just file.jpg
		if (index($filename,'/')>=0) { $filename = substr($filename,rindex($filename,'/')+1); }
		$filename = lc($filename);
	
		(my $pwd,$filename,my $ext) = &MEDIA::parse_filename($filename);	
		if ($BUFFER ne '') {
			$filename =~ s/[_\s]+$//g;		# strip any underscores at the end of the filename (e.g. image___)
			my $f = "$PWD/$filename.$ext";
			my ($resultref) = &MEDIA::store($USERNAME, $f, $BUFFER); 
			if ($resultref->{'err'}>0) {
				$GTOOLS::TAG{'<!-- MESSAGE -->'} = &GTOOLS::errmsg("[ERROR $resultref->{'err'}] $resultref->{'errmsg'}");
				}
			}
		$ACTION = 'LIST';
		}

	}



if ($ACTION eq 'UPLOADZIP') {
	my $fh = $q->upload("upfile");
	my $BUFFER = "";
	my $ERROR = '';
	my $filename = $fh;
	if (not defined $fh) {
		## crap
		}
	elsif ($filename =~ m/^http[s]:\/\//i) {
		$BUFFER = &ZURL::snatch_url($filename);
		}
	elsif (defined($fh))
		{ while (<$fh>) { $BUFFER .= $_; } } 
	else 
		{ $ERROR = 'Empty file!'; }

	# at this point $BUFFER has the contents.
	if ($LUSERNAME eq 'SUPPORT') {
		## no filesize limit on support
		}
	elsif ($LU->is_level(7)) {
		if (length($BUFFER)>=100000000) {
			$ERROR = "File was too large, must be less than 100,000,000 bytes.";
			}
		}
	elsif (length($BUFFER)>=10000000) {
		$ERROR = "File was too large, must be less than 10,000,000 bytes.";
		} 

	if ($ERROR) {
		}
	elsif (length($BUFFER)>0) {

		open F, ">/tmp/zipupload.$$.zip";
		print F $BUFFER;
		close F;

		my $zip = Archive::Zip->new();
		die 'read error' if $zip->read( "/tmp/zipupload.$$.zip" ) != $Archive::Zip::AZ_OK;

		my $c = '';
		foreach my $member ($zip->members()) {
			# print Dumper($member);

			my $BUF = $zip->contents( $member ); 
			# print $member->fileName()." length: ".length($foo)." []\n";
			my ($filename) = $member->fileName();
	
			## convert S:\path\to\file.jpg to just file.jpg
			if (index($filename,'\\')>=0) { $filename = substr($filename,rindex($filename,'\\')+1); }
			## convert dir/file.jpg to just file.jpg
			if (index($filename,'/')>=0) { $filename = substr($filename,rindex($filename,'/')+1); }
			$filename = lc($filename);

			(my $pwd,$filename,my $ext) = &MEDIA::parse_filename($filename);	
			my $f = "$PWD/$filename.$ext";
			
			my ($CODE,$NAME) = &MEDIA::store($USERNAME,$f,$BUF);

			if ($CODE == 0) { 
				$c .= "<b>Created $NAME</b><br>";
				$c .= "<font size='1'>Folder: ".uc(substr($NAME,0,1))."</font><br>";
				$c .= "<img width=\"75\" height=\"75\"  border=\"0\" src=\"//static.zoovy.com/img/$USERNAME/W75-H75/$NAME\">"."<hr>";
				}
			}
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = $c;
		}
	
	if ($ERROR eq '') {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color=\"red\">$ERROR</font><br>";
		}

	$ACTION = 'LIST';
	}


##
## Removes images from a folder
##
if ($ACTION eq 'DELETEIMAGES') {
	my %nuke = ();
	foreach my $p (keys %{$ZOOVY::cgiv}) {
		if ($p =~ /img-(.*?)$/) {
			$nuke{$1}++; 
			}
		}

	my $D = undef;
	opendir($D,$PATH.$PWD);
	while (my $file = readdir($D)) {
		next if (substr($file,0,1) eq '.');
		my $basefile = &MEDIA::filespec($file);
		if (defined $nuke{$basefile}) {
			unlink($PATH.$PWD.'/'.$file);
			$nuke{$basefile}--;	# we'll only remove items which are 0 or lower from the database!
			}
		}
	closedir($D);

	## maintain the media library database!
	foreach my $p (keys %nuke) {
		next if ($nuke{$p}>0);	# don't delete stuff that didn't actually get unlinked!
		&MEDIA::delimage($USERNAME,$PWD,$p);
		$LU->log("SETUP.MEDIA.DELIMG","Deleting image $PWD/$p","SAVE");
		}

	$ACTION = 'LIST';
	}

##
## Creates a new folder
##
if ($ACTION eq 'CREATEFOLDER') {
	my $newfolder = $ZOOVY::cgiv->{'NEWFOLDER'};
	$newfolder =~ s/ /_/gs;
	$newfolder =~ s/\W+//gs;
	$newfolder =~ s/[\.]+//gs;
	$newfolder = lc($newfolder);
	$newfolder = $PWD.'/'.$newfolder;

	if (length($newfolder)>65) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='red'>Total length of folders may not exceed 65 characters</font>";
		$newfolder = '';
		}

	if ($newfolder ne '') {
		&MEDIA::mkfolder($USERNAME,$newfolder);
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='red'>Created folder $newfolder</font><br>";
		}
	$ACTION = 'LIST';
	}


##
## Delete a folder
##
if ($ACTION eq 'DELETEFOLDER') {
	$ACTION = 'LIST';
	$PWD = &MEDIA::rmfolder($USERNAME,$PWD);
	}

## 
## shows the folders
##
if ($ACTION eq 'LIST') {
	my ($foldersref,$filesref) = &MEDIA::folders($USERNAME,$PWD);

	if (substr($PWD,0,1) ne '/') { $PWD = "/$PWD"; }

	if (length($PWD) > 1) {
		my $BACK = '/';
		if (index($PWD,'/')>=0) { $BACK = substr($PWD,0,rindex($PWD,'/')); } 
		$GTOOLS::TAG{'<!-- BACK -->'} = "<a href=\"index.cgi?ACTION=LIST&PWD=$BACK\"><img src=\"/images/up_dir_icon.gif\" border=0 height=15 width=15></a>";
		}

	## Display FOLDERS
	my $count = 0;
	my $c = '<tr>';
	foreach my $f (sort keys %{$foldersref}) {

		my $cwdonly = $f;

		$c .= "<td width=25% valign='top' align=\"center\"><a href=\"index.cgi?ACTION=LIST&PWD=$f\"><img border=0  src=\"/biz/images/tabs/graphics/folder.gif\" width=\"41\" height=\"42\"></a>";
		$c .= "<br><a href=\"index.cgi?ACTION=LIST&PWD=$f\">$cwdonly</a> ($foldersref->{$f})</td>";
		if (++$count % 4 == 0) { $c .= "</tr><tr>\n<td colspan='4'>&nbsp;</td></tr><tr>\n"; }
		}
	if ($count==0) { 
		$c .= "<tr><td>&nbsp;&nbsp;&nbsp; <i>no sub-folders exist.<br><br></i></td></tr>\n"; 
		}
	else {
		while ($count++%4!=0) { $c .= "<td width=25%>&nbsp;</td>\n"; }
		if ($count%4 != 0) { $c .= "</tr>"; } 
		}
	$GTOOLS::TAG{'<!-- FOLDERS -->'} = $c;
	
	## Display FILES
	if ($PWD ne '' && $PWD ne '/') {
		$GTOOLS::TAG{'<!-- ACTIONS -->'} = '';
		$GTOOLS::TAG{'<!-- ACTIONS -->'} .= qq~
			<tr><td>
				<b>Upload Image</b>
				<input class="file" type="file" size=10 name="upfile">
				<input type="button" onClick="document.thisFrm.ACTION.value='UPLOADFILE'; document.thisFrm.submit();" value=" Upload File ">
				<br>
				<br>
			</td></tr>
		~;

		$c = '<tr>';
		$count=0;
		foreach my $f (sort keys %{$filesref}) {
			my $imgurl = &GTOOLS::imageurl($USERNAME,"$PWD/$f",75,75,'ffffff',undef);
			$c .= "<td valign='top' width=25% align=\"center\"><a href=\"index.cgi?ACTION=FILE&PWD=$PWD&FILE=$f\"><img border=0  src=\"$imgurl\" width=\"75\" height=\"75\"></a>";
			$c .= "<br><a href=\"index.cgi?ACTION=FILE&PWD=$PWD&FILE=$f\">$f</a> ($filesref->{$f})<br><input type=\"checkbox\" name=\"img-$f\"></td>";
			if (++$count % 4 == 0) { $c .= "</tr><tr><td colspan='4'>&nbsp;</td></tr><tr>"; }
			}

		if ($count==0) { 
			$c .= "<tr><td>&nbsp;&nbsp;&nbsp; <i>no images exist.<br><br></i></td></tr>"; 
			## No Images
			$GTOOLS::TAG{'<!-- ACTIONS -->'} .= qq~
				<tr><td>
				<b>Remove Folder $PWD</b>
				<input type="button" onClick="document.thisFrm.ACTION.value='DELETEFOLDER'; document.thisFrm.submit();" value=" Remove Folder "><br><br>
			</td></tr>
			~;
			}
		else {
			while ($count++%4!=0) { $c .= "<td width=25%></td>"; }
			if ($count%4 != 0) { $c .= "</tr>"; } 
			$GTOOLS::TAG{'<!-- ACTIONS -->'} .= qq~
				<tr><td>
				<b>Remove Images</b><br>
				<input type="button" onClick="document.thisFrm.ACTION.value='DELETEIMAGES'; document.thisFrm.submit();" value=" Delete Images"><br><br>
				</td></tr>
			~;
			}

		}
	else {
		$c = '<tr><td><i>Note: You may not store image files in the root directory.</i></td>';
		}
	$GTOOLS::TAG{'<!-- FOLDER_FILES -->'} = $c;


	## Add "Create Folder" to Actions
	$GTOOLS::TAG{'<!-- ACTIONS -->'} .= qq~
		<tr><td>
			<b>Create New Folder:</b><br>
			<input type="textbox" size="15" name="NEWFOLDER">
			<input type="button" onClick="document.thisFrm.ACTION.value='CREATEFOLDER'; document.thisFrm.submit();" value=" Create ">
		</td></tr>
		~;

	}


$GTOOLS::TAG{'<!-- PWD -->'} = $PWD;

&GTOOLS::output(
   'title'=>'Setup : Media Library',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50404',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'//www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Media',link=>'//www.zoovy.com/biz/setup/media','target'=>'_top', },
      ],
   );



