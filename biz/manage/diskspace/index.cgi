#!/usr/bin/perl

use CGI;
use lib "/httpd/modules";
require GTOOLS;
require MEDIA;
require MEDIA::ORPHANS;
require ZOOVY;
require LUSER;
use strict;

&ZOOVY::init();

my ($LU) = LUSER->authenticate(FLAGS=>'_M&2');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }



my $template_file = 'index.shtml';

my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
#if (1) {
#	$template_file = 'output.shtml';
#	$GTOOLS::TAG{'<!-- OUTPUT -->'} = qq~
#<table width=500><tr><td>
#<h2>Disk Space Tools</h1><br>
#<b>We apologize, this tool is currently offline for maintenance, it will be available again prior to 1/31/07.</b>
#
#</td></tr></table>
#	~;
#	}

if ($LU->is_zoovy()) {
	## support can run this anytime!
	}
elsif ((1) && (not ($hour < 7 || $hour > 18))) {
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = qq~
	<table width=500><tr><td>
	<h2>Disk Space Tools</h2><br>

	<b>Sorry this tool is not available right now</b><br>
	<br>
	Because of the high disk utilization caused by this tool, and the need to provide a fast and reliable platform for all our customers
	this feature is only available during off-peak hours between 8:00pm PST and 7:00am PST<br>
	<br>
	</td></tr></table>
	~;


	$template_file = 'output.shtml';
	}


if ($ZOOVY::cgiv->{'ACTION'} eq 'IMAGES') {
	require MEDIA;
	require MEDIA::ORPHANS;
	
	my %IMAGES = %{MEDIA::ORPHANS::find_orphans($USERNAME)};

	my $key_count = scalar(keys %IMAGES);
 
	my $OUTPUT = '';
	my $count = 0;
	my $msg = '';
	foreach my $i (sort keys %IMAGES) {
		$count++;
		$OUTPUT .= "<Tr><td><img src=\"".&GTOOLS::imageurl($USERNAME,$i,50,50,'FFFFFF',0,undef)."\" width=50 height=50 border=0></td>";
		$OUTPUT .= "<td valign='top'><input type='checkbox' id='checkGroup' name=\"*$i\"></td><td valign='top'>".$i."</td></tr>\n";

		## only show 500 images at a time
		if ($count >= 500) {
			$msg = "<font color=red><b>More than 500 ($key_count to be exact) orphan images were found!! Only the first 500 are shown. Please delete these and then find the next 500 images</b></font><br><br>";	
			last;
			}	
		}

	## added a check all button for checkboxes	
	$OUTPUT = "<hr>$msg<b>Found $count Orphaned Images</b><br>".
	 "<font size='2'>Check the box next to the images you wish to delete then press the \"Remove Selected Images\" button".
	 " to continue.<br>Note: Only remove images you are entirely sure you no longer need. A recovery charge will be ".
	 "applied to any image which must be recovered from tape.<br>\n<br>".
	 qq~<table><Tr><td></td><td valign='top'><input type="checkbox" name="all" onClick="checkAll(document.mylist.checkGroup,this)"></td>~.
	 qq~<td valign='top'>Check/Uncheck All<br><br></td></tr>~.
	 $OUTPUT."</table>";
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<b>Orphan Images</b><br><form name='mylist' action='index.cgi' method='POST'>".
	 "<input type='hidden' name='ACTION' value='NUKEIMG'>".$OUTPUT."<br>".
	 "<input type='submit' value='  Remove selected images  '></form>";
	$template_file = 'output.shtml';

	&DBINFO::db_zoovy_close();
	}

if ($ZOOVY::cgiv->{'ACTION'} eq 'NUKEIMG') {
	my $out = '<b>Deleted the following images:</b><br>';
	foreach my $p (%{$ZOOVY::cgiv}) {
		next if (substr($p,0,1) ne '*');
		#print STDERR "IMGS to delete $p\n";
		$out .= "$p<br>";
		$p = substr($p,1);
		&MEDIA::nuke($USERNAME,$p,instances=>1,original=>1);
		$LU->log('UTIL.DISKSPACE.NUKEIMG',"Deleted Image: $p","SAVE");
		}
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color=red>$out</font><br><br><br>";
	}

if ($ZOOVY::cgiv->{'ACTION'} eq 'COMPUTESPACE') {
	my $root = &ZOOVY::resolve_userpath($USERNAME);
	system("/usr/bin/du -kh $root > /tmp/$USERNAME.du.log");
	my $OUTPUT = '';
	open F, "</tmp/$USERNAME.du.log";
	my $len = length($root);
	my $total = 0;
	while (<F>) {
		my ($space,$path) = split(/[\t ]+/s,$_);

		$total += $space;
		$path = substr($path,$len);
		if (length($path)==1) { $path = '<b>TOTAL USAGE</b>'; }
		$OUTPUT .= "<tr><td>$path</td><td>$space</td></tr>";
		}
	close F;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = qq~
<b>Disk Space Usage: </b><br>
<table>$OUTPUT</table>
<br>
<br>NOTES:<br>
<li> /IMAGES also includes custom files (which are not stored in a separate sub directory).<br>
<li> K = 1024 bytes, M = 1048576 bytes.<br>
	~;

	$LU->log('UTIL.DISKSPACE.LOG',"Computed diskspace - total $total","STAT");
	}

&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,
   'title'=>'Diskspace',
	'header'=>1,
   'file'=>$template_file,
   'help'=>'#50330',
   'bc'=>[
      { name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
      { name=>'Diskspace',link=>'','target'=>'_top', },
      ],
   );




##
## parameters: 
##  virtual root 
sub dodir
{
	my ($root, $path) = @_;

	my $D = undef;
	opendir $D, $root.'/'.$path;
	my @dirs = ();
	while (my $sub = readdir($D)) { 
		next unless (substr($sub,0,1) ne '.');
		if (-d "$root/$path/$sub")
			{
			foreach my $e (&dodir($root,"$path/$sub")) { push @dirs, $e; }
			} else {
			push @dirs, $path.'/'.$sub; 
			}
		}
	closedir $D;

	return(@dirs);
}

sub classify
{
	my ($pathto, $filename) = @_;

	my $text = "Unknown File Type";
	if (substr($filename,-3) eq '.OG') { $text = 'Option Group'; }

	if (substr($filename,-1) eq '~') { $text = 'Zoovy Staff Recovery File'; }
	if (substr($filename,-3) eq '.bak') { $text = 'Zoovy Staff Recovery File'; }

	if (-d $pathto.'/'.$filename) { $text = 'DIR'; }

	if ($filename eq 'INVENTORY.db') { $text = 'Inventory Summary Database'; }
	if ($filename eq 'WEBSITE') { $text = 'Website configuration and setup'; }
	if ($filename eq 'products.zoovy') { $text = 'Product Namespace'; }
	if ($filename eq 'merchant.zoovy') { $text = 'Merchant Namespace'; }
	if ($filename eq 'navcats.db') { $text = 'Website Navigation database'; }
	
	my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($pathto.'/'.$filename);

	return($text,$mtime);
}
