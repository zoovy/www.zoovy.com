#!/usr/bin/perl

use lib "/httpd/modules";

##
## parameters:
##
##		attrib=zoovy:property -- set an attrib
##
##

use CGI;
use File::Basename;
require GTOOLS;
require ZTOOLKIT;
require ZOOVY;
require MEDIA;
use strict;

my $q = new CGI;

my $s = {};
if (not defined $q->param('s')) {
	exit;

	}

&ZOOVY::init();
&GTOOLS::init();
# print STDERR "S: ".$q->param('s')."\n";

$s = &ZTOOLKIT::fast_deserialize($q->param('s'),1);
my $USERNAME = $s->{'USERNAME'};
foreach my $p ($q->param()) { 
	next if ($p eq 'USERNAME');
	next if ($p eq 's');
	next if ($p eq 'upfile');
	$s->{$p} = $q->param($p); 
	}


## figure out the correct cancellation links
my $JS = 'top.close();';
if ($s->{'mode'} eq 'flow') {
	if ($s->{'PROD'} ne '') {
		## we're editing a product
		$JS = "parent.window.location='/biz/product/flow/preview.cgi?PROD=$s->{'PROD'}&FL=$s->{'FL'}&EL=$s->{'EL'}&FS=$s->{'FS'}&PG=".CGI->escape($s->{'PG'})."';\n\n";
		}
	else {
		## we're editing a webpage.
		$JS = "parent.window.location='/biz/setup/builder/preview.cgi?PROD=$s->{'PROD'}&FL=$s->{'FL'}&EL=$s->{'EL'}&FS=$s->{'FS'}&PG=".CGI->escape($s->{'PG'})."';\n\n";
		}
	}
$GTOOLS::TAG{'<!-- CANCELLINK -->'} = $JS;


## Upload command.
if ($s->{'ACTION'} eq 'UPLOAD') {
	my $fh = $q->param('upfile');
	
	use Data::Dumper;
	# print STDERR "[UPLOAD] ".Dumper($q);
	
	if ($fh eq '') { $fh = $q->param('furl'); }
	
	my $BUFFER = '';
	my $filename = $fh;
	# print STDERR "FILENAME: $filename\n";
	if (not defined $fh) {
		## Crap, not defined!
		}
	elsif ($filename =~ m/^http[s]?:\/\//i) {
		require ZURL;
		$BUFFER = &ZURL::snatch_url($filename.'');
		}
	elsif (defined $fh) {
		while (<$fh>) { $BUFFER .= $_; }
		}

	## convert S:\path\to\file.jpg to just file.jpg
	if (index($filename,'\\')>=0) { $filename = substr($filename,rindex($filename,'\\')+1); }
	## convert dir/file.jpg to just file.jpg
	if (index($filename,'/')>=0) { $filename = substr($filename,rindex($filename,'/')+1); }
	$filename = lc($filename);

	my ($name,$path,$suffix) = File::Basename::fileparse($filename,qr{\.jpeg|\.jpg|\.png|\.gif});
	if ($path eq './') { $path = ''; }	## this is not a valid path!

	## note: suffix has a .jpeg or .jpg (notice the leading period)
	$name = lc($name); 
	$name =~ s/[^a-z0-9\_]+/_/gs;
	$name =~ s/[_]+$//g;
	$filename = "$path$name$suffix";

	

	##
	## Sanity: at this point the image is uploaded!

	if ($BUFFER ne '') {
		if (($s->{'PWD'} eq '') || ($s->{'PWD'} eq '/')) {
			## auto-select directoyr
			}
		else {
			## save into a specific directory
			$filename = "$s->{'PWD'}/$filename";
			}
		# $f = "$PWD/$f";
		my ($iref) = &MEDIA::store($USERNAME,$filename,$BUFFER);
		# print STDERR "[IREF] ".Dumper($iref,$filename,$path,$name,$suffix);

		if ((defined $iref) && ($iref->{'err'}==0)) {
			$s->{'IMG'} = &MEDIA::iref_to_imgname($USERNAME,$iref);
			}
		elsif ($iref->{'err'}>0) {
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = &GTOOLS::errmsg("ERROR: $iref->{'err'} $iref->{'errmsg'}");
			}
		}
	}


my $img = $s->{'IMG'};
$GTOOLS::TAG{'<!-- PWD -->'} = $s->{'PWD'};

if ($s->{'IMG'} ne '') {
	$GTOOLS::TAG{'<!-- IMGSIZE -->'} = '';
	$GTOOLS::TAG{'<!-- IMG -->'} = $s->{'IMG'};
	require MEDIA;
	$GTOOLS::TAG{'<!-- PRETTY_IMGNAME -->'} = $s->{'IMG'};
	my $iref = &MEDIA::getinfo($USERNAME,$s->{'IMG'});
	if (not defined $iref) {
		$GTOOLS::TAG{'<!-- PRETTY_IMGNAME -->'} = '__UNDEFINED ERR__';
		}
	elsif ($iref->{'err'}>0) { 
		$GTOOLS::TAG{'<!-- PRETTY_IMGNAME -->'} = sprintf('IMAGE=%s | ERROR[%d]=%s',$s->{'IMG'},$iref->{'err'},$iref->{'errmsg'});
		}
	else {
		$GTOOLS::TAG{'<!-- IMGSIZE -->'} = sprintf("%.2f",$iref->{'MasterSize'}/1000).'k';
#		my $pretty = $s->{'PWD'}.'/'.$iref->{'ImgName'}.'.'.$iref->{'Format'};
#		$pretty =~ s/\/\.//gs;		## 1/1/1/./sunset.jpg
		my $pretty = &MEDIA::iref_to_imgname($USERNAME,$iref);
		$GTOOLS::TAG{'<!-- PRETTY_IMGNAME -->'} = $pretty;
		}
	}
else {
	$GTOOLS::TAG{'<!-- IMG -->'} = '';
	$GTOOLS::TAG{'<!-- PRETTY_IMG -->'} = '* Not Set *';
	$GTOOLS::TAG{'<!-- IMGSIZE -->'} = '0k';
	}


delete $s->{'ACTION'};
$GTOOLS::TAG{'<!-- SERIAL -->'} = &ZOOVY::incode(&ZTOOLKIT::fast_serialize($s,1));
$GTOOLS::TAG{'<!-- IMGURL -->'} = ($img)?&GTOOLS::imageurl($USERNAME,$img,110,110,'ffffff',undef):'/images/image_not_selected.gif';


&GTOOLS::output( file=>'popup-top.shtml', header=>1 );
