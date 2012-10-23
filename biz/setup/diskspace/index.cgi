#!/usr/bin/perl

use lib "/httpd/modules";
use GT;
use CGI;
use ZOOVY;



$q = new CGI;
($USERNAME) = &ZOOVY::authenticate('/biz');

$c = 'Directory Listing:';

$root = &ZOOVY::resolve_userpath($USERNAME);
my @dirs = dodir($root,'');
foreach $sub (sort @dirs)
	{
	if (substr($sub,0,1) ne '.')
		{
		($type,$size) = &classify($path,$sub);
		$c .= "<tr><td>$sub</td><td>$size</td><td>$type</td></tr>";
		}
	}

$GT::TAG{'<!-- DIRLIST -->'} = $c;

print "Content-type: text/html\n\n";
&GT::print_form('','index.shtml',0);


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
			foreach $e (&dodir($root,"$path/$sub")) { push @dirs, $e; }
			} else {
			push @dirs, $path.'/'.$sub; 
			}
		}
	closedir $D;

	return(@dirs);
}

sub classify
{
	($pathto, $filename) = @_;

	$text = "Unknown File Type";
	if (substr($filename,-3) eq '.OG') { $text = 'Option Group'; }

	if (substr($filename,-1) eq '~') { $text = 'Zoovy Staff Recovery File'; }
	if (substr($filename,-3) eq '.bak') { $text = 'Zoovy Staff Recovery File'; }

	if (-d $pathto.'/'.$filename) { $text = 'DIR'; }

	if ($filename eq 'INVENTORY.db') { $text = 'Inventory Summary Database'; }
	if ($filename eq 'WEBSITE') { $text = 'Website configuration and setup'; }
	if ($filename eq 'products.zoovy') { $text = 'Product Namespace'; }
	if ($filename eq 'merchant.zoovy') { $text = 'Merchant Namespace'; }
	if ($filename eq 'navcats.db') { $text = 'Website Navigation database'; }
	
	($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($pathto.'/'.$filename);

	return($text,$mtime);
}