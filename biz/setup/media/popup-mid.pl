#!/usr/bin/perl

use lib "/httpd/modules";
require ZOOVY;
require ZTOOLKIT;
use Data::Dumper;

##
## parameters:
##
##		attrib=zoovy:property -- set an attrib
##
##

use CGI;
require GTOOLS;
require MEDIA;

&GTOOLS::init();
&ZOOVY::init();

my $q = new CGI;
my $s = {};
if (not defined $q->param('s')) {
	exit;
	}

#print STDERR "S: ".$q->param('s')."\n";

$s = &ZTOOLKIT::fast_deserialize($q->param('s'),1);
my $USERNAME = $s->{'USERNAME'};
foreach my $p ($q->param()) { 
	next if ($p eq 'USERNAME');
	next if ($p eq 's');
	$s->{$p} = $q->param($p); 
	}

my $PWD = $s->{'PWD'};
if (not defined $PWD) {
	($PWD) = &MEDIA::parse_filename($s->{'IMG'});
	}

my $c = '';
my ($foldersref,$filesref) = &MEDIA::folders($USERNAME,$PWD);
if (($PWD eq '') || ($PWD eq '/')) { $filesref = {}; }

if (length($PWD) > 1) {
	if (rindex($PWD,'/')>0) { 
		$BACK = substr($PWD,0,rindex($PWD,'/'));
		}
	else {
		$BACK = '';
		}
	$GTOOLS::TAG{'<!-- BACK -->'} = "<a href=\"index.cgi?ACTION=LIST&PWD=$BACK\">[Back]</a>";
	}

##
## Display FOLDERS
##
if (defined $foldersref) {
	my $count = 0;
	$c = '<tr>';
	foreach my $f (sort keys %{$foldersref}) {
		# if (($PWD ne '') && ($PWD ne '/')) { $f = "$PWD/$f"; }
		$c .= "<td><a href=\"javascript:window.document.midFrm.PWD.value='$f'; window.document.midFrm.submit();\">";
		$c .= "<img src=\"/images/dir_icon_small.gif\" height=15 width=15 alt=\"$f\" border=0> $f</a></td>";
		if (++$count % 4 == 0) { $c .= "</tr><tr>\n<td colspan='4'><img width=100 height=5 src=\"/images/blank.gif\"></td></tr><tr>\n"; }
		}
	if ($count==0) { 
		$c .= "<tr><td>&nbsp;&nbsp;&nbsp; <i>no sub-folders exist.<br><br></i></td></tr>\n"; 
		}
	else {
		while ($count++%4!=0) { $c .= "<td width=25%>&nbsp;</td>\n"; }
		if ($count%4 != 0) { $c .= "</tr>"; } 
		}
	}
else {
	$c = "<tr><td><i>The folder you have requested no longer exists</i><br><a href=\"javascript:window.document.midFrm.PWD.value=''; window.document.midFrm.submit();\">[Return to Root Category]</a></td></tr>";
	}

$GTOOLS::TAG{'<!-- FOLDERS -->'} = $c;

delete $s->{'ACTION'};
#print STDERR 'serialize: '.Dumper($s);
$GTOOLS::TAG{'<!-- SERIAL -->'} = &ZOOVY::incode(&ZTOOLKIT::fast_serialize($s,1));
$GTOOLS::TAG{'<!-- PWD -->'} = $PWD;

my $BACKPWD = '';
if ($PWD ne '' && $PWD ne '/') {
   if (rindex($PWD,'/')>0) {
      $BACKPWD = substr($PWD,0,rindex($PWD,'/'));
      }
   else {
      $BACKPWD = '';
      }
 	# $BACKPWD = substr($PWD,0,rindex($PWD,'/'));
	$GTOOLS::TAG{'<!-- BACKPWD -->'} = "<a href=\"javascript:window.document.midFrm.PWD.value='$BACKPWD'; window.document.midFrm.submit();\"><img src=\"/images/up_dir_icon.gif\" border=0 height=15 width=15></a> <i>NOTE: Any images you upload will be saved in this directory</i>";
	}

##############################################################################################
##
## Lower Frame Control
## 
##	since this isn't obvious - a bit of commenting. 
##		first we'll generate a list of files in an html table
##		next we'll create an html document
##		finally we'll cut up the html document into document.write statements
##		then we'll add the javascript to the middle frame so it can rewrite the lower frame.
##

############## Generate HTML Table
if (defined $filesref) {
	$c = '<tr>';
	$count=0;
	foreach my $f (sort keys %{$filesref}) {
		my $imgurl = &GTOOLS::imageurl($USERNAME,"$PWD/$f",75,75,'ffffff',undef);
		$c .= qq~<td width=25% align="center"><a href="javascript:window.document.lowFrm.IMG.value='$PWD/$f'; window.document.lowFrm.submit();"><img border=0 class="table_stroke" src="$imgurl" width="75" height="75"><br><div style="font-family: sans-serif,arial; font-size: 8pt;">$f</div></a></td>~;
		if (++$count % 4 == 0) { $c .= "</tr><tr><td colspan='4'>&nbsp;</td></tr><tr>"; }
		}

	if (($count==0) && ($PWD eq '' || $PWD eq '/')) {
		$c = qq~
	<tr><td>
	<hr>
	To upload images into a specific folder, first navigate to the folder then upload the image.<br>
	To select an image which has already been uploaded, simply navigate to the appropriate folder.<br>
	<br>
	If you experience slow upload times: Many ISP's temporarily limit upload speeds after uploading 
	several large files - to avoid this try using warehouse manager.<br>
	Note: you may not upload files into the root directory. If you attempt to upload into the root directory 
	then the images will automatically be stored in a folder based on the first letter of the filename.<br>
	<br>
	</td></tr>
		~;
		}
	elsif ($count==0) { 
		$c = "<tr><td>&nbsp;&nbsp;&nbsp; <i>No images exist in this folder.<br><br></i></td></tr>"; 
		}
	else {
		while ($count++%4!=0) { $c .= "<td width=25%></td>"; }
		if ($count%4 != 0) { $c .= "</tr>"; } 
		}
	}
else {
	$c = "<tr><td><i>No files</i></td></tr>";
	}

############### Create HTML Document
my $t = time();
$c = qq~
<!-- begin lower frame -->
<head>
<link rel="stylesheet" type="text/css" href="/biz/standard.css">
</head>
<body>

<form name="lowFrm" action="popup-low.cgi">
<input type="hidden" name="s" value="$GTOOLS::TAG{'<!-- SERIAL -->'}">
<input type="hidden" name="IMG" value="">
<table class="zoovytable" border=0 cellspacing=2 cellpadding=2 width="100%">
$c 
</table>
</form>
</body>
~;

################ Cut Up HTML Document into Javascript
my $JS = '';
foreach my $line (split(/[\n\r]+/,$c)) {
	$line =~ s/'/\\'/gs;
	$line =~ s/\t//gs;
  	$JS .= "window.parent.LowFrame.document.write('$line');\n";
	}

################ Add Javascript to midForm
$GTOOLS::TAG{'<!-- LOWFRAME -->'} = $JS;
$c = ''; $JS = '';


&GTOOLS::output( file=>'popup-mid.shtml', header=>1 );
