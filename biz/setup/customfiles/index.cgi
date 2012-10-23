#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GTOOLS;
use CGI;


my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_S&4');
if ($USERNAME eq '') { exit; }

my $q = new CGI;
my $MODE = $q->param('MODE');

$GTOOLS::TAG{'<!-- TS -->'} = time();
my $path = &ZOOVY::resolve_userpath_zfs1($USERNAME);

my $ACTION = $q->param('ACTION');

if ($FLAGS !~ /,WEB,/) {
	$ACTION = '';
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = 'Sorry - your account does not have access to this functionality. <br><a target="_top" href="/biz/configurator?VERB=VIEW&BUNDLE=WEB">Click here to upgrade</a>';
	}

## remove a file
if ($ACTION eq 'DEL') {
	$filename = $q->param('FILE');
	## error anything which begins with a period, or begins with a slash
	if ((substr($filename,0,1) eq '/') || (substr($filename,0,1) eq '.'))
		{
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "invalid filename [$filename]";
		} else {
		unlink($path.'/IMAGES/'.$filename);			
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "removed $filename";
		}
	}

## upload a new file
if ($ACTION eq 'UPLOAD') {

	if ($FLAGS =~ /TRIAL/i) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = 'Sorry - Trials cannot host custom files.<br><a target="_top" href="/biz/configurator">Click here to upgrade</a>';
		}
	else {

		$BUFFER = "";
		$filename = $q->param("FILENAME").'';
		$fh = $q->upload("FILENAME");

		if (defined $fh) {
			if (!defined($filename)) { $filename = time(); }
	   	while (<$fh>) { $BUFFER .= $_; }
			}


		if (length($BUFFER)==0) {
			## check for a URL
			if ($filename =~ /http/i) {
				require ZURL;
				$BUFFER = &ZURL::snatch_url($filename);
				}
			}

		# at this point $BUFFER has the contents.
		if (length($BUFFER)>=3000000) {
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = "File was too large, must be less than 3,000,000 bytes.";
			} 
		elsif (length($BUFFER)>0) {
			my ($f,$e) = strip_filename($filename);
			if (! -d "$path/IMAGES") { mkdir (0777,"$path/IMAGES"); }
			open F, ">$path/IMAGES/$f.$e";
			print F $BUFFER;
			close F;
			} 
		else {
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = 'File cannot be zero bytes'; 
			}
		}

	}


opendir($D,$path.'/IMAGES');
$c = '';
while ($file = readdir($D)) {
	next if ($file =~ /^\./);
	next if (-d $path.'/IMAGES/'.$file);

	my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($path.'/IMAGES/'.$file);
	$ACTION = '';
	if ($file =~ /\.gif$/i){ $ACTION = "[<a href=\"javascript:openWindow('img.cgi?file=$file');\">HTML</a>]"; }
	if ($file =~ /\.jpg$/i){ $ACTION = "[<a href=\"javascript:openWindow('img.cgi?file=$file');\">HTML</a>]"; }
	if ($file =~ /\.png$/i){ $ACTION = "[<a href=\"javascript:openWindow('img.cgi?file=$file');\">HTML</a>]"; }

	next if (($MODE eq 'THEMES') && ($file !~ /\.zhtml$/));

	$c .= "<tr><td>[<a href='index.cgi?ACTION=DEL&FILE=$file'>DEL</a>]$ACTION</td><td>http://static.zoovy.com/merchant/$USERNAME/$file</td><td>$size</td></tr>";
	}

if (($c eq '') && ($MODE eq 'THEMES')) {
	$c .= "<tr><td><i>No custom themes (.zhtml files) have been uploaded yet.</i></td></tr>";
	}
elsif ($c eq '') { 
	$c .= '<tr><td><i>No Custom Files Exist Yet</i></td></tr>'; 
	}
else
	{ $c = '<tr bgcolor="3366CC"><td><font color="white"><b>ACTION</b><td><font color="white"><b>URL</b></td><td><font color="white"><b>Size</b></td></tr>'.$c; }

$GTOOLS::TAG{'<!-- LIST -->'} = $c;
closedir($D);


&GTOOLS::output(
   'title'=>'Setup : Custom Files',
   'file'=>'index.shtml',
   'header'=>'1',
   'help'=>'#50278',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Custom Files',link=>'http://www.zoovy.com/biz/setup/customfiles','target'=>'_top', },
      ],
   );




sub strip_filename {
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
		
		# lets strip name at the first / or \ e.g. C:\program files\zoovy\foo.gif becomes "foo.gif"
		$name =~ s/.*[\/|\\](.*?)$/$1/;
		# allow periods, alphanum, and dashes to pass through, kill any other special characters
		$name =~ s/[^\w\-\.]+/_/g;
		# now, remove duplicate periods
		$name =~ s/[\.]+/\./g;
		
		} else {
		# very bad filename!! ?? what should we do!
		}

	# we should probably do a bit more sanity on the filename right here

	print STDERR "upload.cgi:strip_filename says name=[$name] extension=[$ext]\n";
	return($name,$ext);
	}
