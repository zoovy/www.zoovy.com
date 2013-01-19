#!/usr/bin/perl -w

use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require MEDIA;
require ZTOOLKIT;
require ZWEBSITE;
use strict;

##
## HEY - this function is called by the following programs:
##		channel editor
##		product option chooser
##		html editor (called as "image.[pl|cgi]/HTMLAREA" since we have to track vars a little different )
##

&ZOOVY::init();
&ZWEBSITE::init();
&GTOOLS::init();

my ($USERNAME,$FLAGS) = &ZOOVY::authenticate('/biz',1);
my $c = ''; 
my $d = '';

my $template_file = '';

my $LASTDIR = 0;
my $NEXTDIR = 0;
my $SRC = '';
my $ACTION = $ZOOVY::cgiv->{'ACTION'};
my $ATTRIB = '';
my $ERROR = '';

if ((!defined($SRC)) || $SRC eq '') { $SRC = "/images/blank.gif"; }
my $DIR = $ZOOVY::cgiv->{'DIR'};

print STDERR "ACTION: $ACTION\n";
use Data::Dumper;

my $cgi = CGI->new();

if ($ACTION eq 'UPLOAD_NOW') {
	my $q = new CGI;

   my $fh = $q->param('FILENAME');
   my $filename = $fh;

	my $BUFFER = '';
   print STDERR "FILENAME: $filename\n";
   if (not defined $fh) {
      ## Crap, not defined!
      }
   elsif (defined $fh) {
      while (<$fh>) { $BUFFER .= $_; }
      }

	# at this point $BUFFER has the contents.
	print STDERR "LENGTH: ".length($BUFFER)."\n";
	my ($iref) = &MEDIA::store($USERNAME,"$filename",$BUFFER); 

	if ($iref->{'err'}>0) {
		$ERROR = "($iref->{'err'}) ERROR: $iref->{'errmsg'}";
		$GTOOLS::TAG{'<!-- IMAGESELECT -->'} = qq~
		<font color='red'>Upload Error: $ERROR</font><br>
		~;
		}
	else {

		my $IMGURL = &GTOOLS::imageurl($USERNAME,$iref->{'ImgName'},0,0,'FFFFFF',0);
		my $THUMBURL = &GTOOLS::imageurl($USERNAME,$iref->{'ImgName'},75,75,'FFFFFF',0);

		$GTOOLS::TAG{'<!-- IMAGESELECT -->'} = qq~
		<font color='blue'>Successfully uploaded image $iref->{'ImgName'}</font><br>
		<table><td><td><img src="$THUMBURL" width=75 height=75> 
		</td><td><input type="button" value=" use image $iref->{'ImgName'} " onClick="thisFrm.url.value='$IMGURL'; onPreview();"></td></tr></table>
		~;
		} 
	}


# quick upload is the same thing but doesn't return to the preview page.
if ($ACTION eq 'UPLOAD' || $ACTION eq 'QUICKUPLOAD') {
	$GTOOLS::TAG{'<!-- IMAGESELECT -->'} = qq~
	<input type="hidden" name="ACTION" value="UPLOAD_NOW">
	Upload: <input name="FILENAME" type="file"><input type="button" value="Upload" onClick="thisFrm.submit();"><br>
	~;
	}

my %collections = ();
if (1) {
	my $found = 0;
	my $count = 0;
	my ($folders) = &MEDIA::folders($USERNAME,''); 
	%collections = %{$folders};

	if (scalar(keys %collections)==0) {
		# has zero directories.
		$c .= "<font class='NOTFOLDER'><b>None Created</b>.</font>";
		}

	if (not defined $DIR) { $DIR = ''; }

	foreach my $d (sort keys %collections) {
		# don't show dirs that have zero files
		if ((defined $collections{$d}) && ($collections{$d} =~ m/\w/)) {
			if ($d eq $DIR) {
				print STDERR "Matched [$d] eq [$DIR]\n";
				## we're in the selected dir
				my @images = split /,/, $collections{$d};
				$count = scalar @images;
				$found=1;
				$c .= "<font color='333333' face='arial' size='2'>&nbsp;<b>$d <font size='2'>($count images)</font></b>&nbsp;</font>\n";
				$c .= "<font color='AAAADD' size='2'><b>|</b></font>\n";
				} else {
				if ($found) { $NEXTDIR = $d; $found=0; }
				$c .= "&nbsp;<a href='image.pl?ACTION=VIEWDIR\&DIR=$d'><b>$d</b></a>&nbsp;\n";
				$c .= "<font color='AAAADD' size='2'><b>|</b></font>\n";
				}

			# if we don't have a next, then set the LAST
			if (!$found && $NEXTDIR eq "") { $LASTDIR = $d; }
			} # end of don't show dirs with 0 files
		}

	$c .= "<font color='AAAADD' size='2'><b>|</b></font>\n";
	$c .= "&nbsp;<a href='image.pl?ACTION=UPLOAD'><b>UPLOAD</b></a>&nbsp;\n";

	$GTOOLS::TAG{'<!-- IMGLIB -->'} = $c;
	if ($NEXTDIR)
		{ $GTOOLS::TAG{"<!-- NEXTDIR -->"} = "<td><a class='FOLDER' href=\"main.cgi?ACTION=VIEWDIR&src=$NEXTDIR\">&gt&gt</a></td>\n"; }
	if ($LASTDIR)
		{ $GTOOLS::TAG{"<!-- LASTDIR -->"} = "<td><a class='FOLDER' href=\"main.cgi?ACTION=VIEWDIR&src=$LASTDIR\">&lt&lt</a></td>\n"; }

	}	# end ACTION eq ''



if ($ACTION eq 'VIEWDIR')
	{
	$c = "<hr><b>HINT: Click The Image You Wish To Use.</b><br><table width='95%'>";
	$d = '';
	my $counter = 0;
	# images per row
	my $images_per_row = 4;
	my $t = time();
	foreach my $img (sort split(',',$collections{$DIR})) {
		if ($counter % $images_per_row == 0) { $c .= "<tr>"; }
		$c .= "<td><center>";
		$c .= "<font class=\"norm\">";

		my $VALUE = &GTOOLS::imageurl($USERNAME,"$DIR/$img",0,0,'FFFFFF',0);
		$c .= "<a href=\"javascript:setImage('$img','$VALUE','$t');\">";
		$c .= "<img border=\"0\" width=\"75\" height=\"75\" src=\"$VALUE\"><br>";		
		$c .= "$img</a></center></font></td>";
		if ($counter % $images_per_row == ($images_per_row - 1)) { $c .= "</tr>"; }
		$counter++;
		$d .= "<option value=\"$VALUE\">$img</option>";
		}
	$c .= "</table>";
	$GTOOLS::TAG{'<!-- IMAGESELECT -->'} = "Image: <select onChange=\"setImage(this);\" name=\"IMAGE\">$d</select> (series $DIR)<br>";
	$template_file = "image.shtml";
	}

$GTOOLS::TAG{'<!-- SRC -->'} = $SRC;
$GTOOLS::TAG{'<!-- ATTRIB -->'} = $ATTRIB;
$GTOOLS::TAG{'<!-- IMAGENAME -->'} = $ATTRIB;

$template_file = 'image.shtml';

&GTOOLS::output(file=>$template_file,header=>1);

## Free up some memory
%collections = (); 		
exit;

##
## purpose: takes a filename, returns the extension and the name (pretty formatted)
##
sub strip_filename
{
	my ($filename) = @_;

	my $ext = "";
	my $name = "";
	print STDERR "upload.cgi:strip-filename says filename is: $filename\n";
	my $pos = rindex($filename,'.');
	print STDERR "upload.cgi:strip_filename says pos is: $pos\n";
	if ($pos>0)
		{
		$name = substr($filename,0,$pos);
		$ext = substr($filename,$pos+1);
		
		# lets strip name at the first / or \
		$name =~ s/.*[\/|\\](.*?)$/$1/;
		$name =~ s/\W+/_/g;
		} else {
		# very bad filename!! ?? what should we do!
		}

	# we should probably do a bit more sanity on the filename right here

	print STDERR "upload.cgi:strip_filename says name=[$name] extension=[$ext]\n";
	return($name,$ext);
}


