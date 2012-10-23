#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use GT;
use CGI;

my ($USERNAME,$FLAGS) = &ZOOVY::authenticate('/biz/setup',1);
my $q = new CGI;

$GT::TAG{'<!-- TS -->'} = time();
my $path = &ZOOVY::resolve_userpath($USERNAME);

my $ACTION = $q->param('ACTION');

## remove a file
if ($ACTION eq 'DEL')
	{
	$filename = $q->param('FILE');
	if ((substr($filename,0,1) eq '/') || (substr($filename,0,1) eq '.'))
		{
		$GT::TAG{'<!-- MESSAGE -->'} = "invalid filename [$filename]";
		} else {
		unlink($path.'/IMAGES/'.$filename);			
		$GT::TAG{'<!-- MESSAGE -->'} = "removed $filename";
		}
	}

## upload a new file
if ($ACTION eq 'UPLOAD') {

	if ($FLAGS =~ /TRIAL/i) {
		$GT::TAG{'<!-- MESSAGE -->'} = 'Sorry - Trials cannot upload custom files.';
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
			$GT::TAG{'<!-- MESSAGE -->'} = "File was too large, must be less than 3,000,000 bytes.";
			} 
		elsif (length($BUFFER)>0) {
			my ($f,$e) = strip_filename($filename);
			if (! -d "$path/IMAGES") { mkdir (0777,"$path/IMAGES"); }
			open F, ">$path/IMAGES/$f.$e";
			print F $BUFFER;
			close F;
			} 
		else {
			$GT::TAG{'<!-- MESSAGE -->'} = 'File cannot be zero bytes'; 
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

	$c .= "<tr><td>[<a href='main.cgi?ACTION=DEL&FILE=$file'>DEL</a>]$ACTION</td><td>http://static.zoovy.com/merchant/$USERNAME/$file</td><td>$size</td></tr>";
	}
if ($c eq '') 
	{ $c .= '<tr><td><i>No Custom Files Exist Yet</i></td></tr>'; }
else
	{ $c = '<tr bgcolor="330099"><td><font color="white"><b>ACTION</b><td><font color="white"><b>URL</b></td><td><font color="white"><b>Size</b></td></tr>'.$c; }
$GT::TAG{'<!-- LIST -->'} = $c;
closedir($D);

&GT::print_form('','main.shtml',1);

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
		$name =~ s/[^\w\-]+/_/g;
		} else {
		# very bad filename!! ?? what should we do!
		}

	# we should probably do a bit more sanity on the filename right here

	print STDERR "upload.cgi:strip_filename says name=[$name] extension=[$ext]\n";
	return($name,$ext);
}
