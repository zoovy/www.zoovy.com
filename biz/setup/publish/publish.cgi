#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use ZNAVCAT;
use ZWEBSITE;
use Net::FTP;
use LWP::UserAgent;

$ua = LWP::UserAgent->new(keep_alive => 1,timeout => 60,);
$ua->proxy(['http', 'ftp'], 'http://63.108.93.10:8080/');

%IMG_MAPPING = ();

my ($USERNAME, $FLAGS) = &ZOOVY::authenticate('',1);
if ($FLAGS =~ /PUBLISH/) {
	
	}


$USERNAME = 'donstoys';
$webdb{'wwwpublish_remhost'} = 'www.kilna.com';
$webdb{'wwwpublish_username'} = 'zoovy';
$webdb{'wwwpublish_password'} = 'foo|';
$webdb{'wwwpublish_rootdir'} = '/www/foo.kilna.com';
$webdb{'wwwpublish_baseurl'} = 'http://foo.kilna.com';


$ZOOVYURL = 'http://'.$USERNAME.'.zoovy.com';	## the URL to the users Zoovy Website
$TMPFILE = '/tmp/'.$USERNAME.'.xfer';				## the Path to a safe file, which you can use to read/write
$CWD = '/';													## the current working directory (not used)

# derived constants
$safe_wwwpublish_baseurl = quotemeta($webdb{'wwwpublish_baseurl'});
$safe_zoovyurl = quotemeta($ZOOVYURL);


print "Content-type: text/html\n\n";
print "<html>\n";
print "<head><title>Zoovy Import</title></head>\n";
print "<body>\n";
print "<font face='arial'><center>\n";


## prepare a list of all products (we'll use it later)
@ALLPRODS = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
@CATEGORIES = &ZNAVCAT::fetch_navcat_fulllist($USERNAME,0);
use Data::Dumper;
print Dumper(\@CATEGORIES);

#%webdb = &ZWEBSITE::fetch_website_db($USERNAME);


&divout("Connecting to ".$webdb{'wwwpublish_remhost'}.'..');
$ftp = Net::FTP->new($webdb{'wwwpublish_remhost'}, Debug => 1);
$ftp->login($webdb{'wwwpublish_username'},$webdb{'wwwpublish_password'});
$ftp->pasv();
$ftp->cwd($webdb{'wwwpublish_rootdir'});
$ftp->binary();
$ftp->mkdir('images');
$ftp->mkdir('product');

## Do the index.html file
$request = HTTP::Request->new('GET', $ZOOVYURL);
$result = $ua->request($request);
$html = $result->content();
($html) = &suckimages($html);
($html) = &temp_sub_paths($html);
open F, ">$TMPFILE"; print F $html; close F;
$ftp->put($TMPFILE,'index.html');


foreach my $foocat (@CATEGORIES)
	{
	next if ($foocat eq '');
	next if ($foocat eq ' ');

	$tmpcat = &ZNAVCAT::navcat_to_url($foocat);
	print "CATEGORY: [$tmpcat]\n";
	my $safeurl = $tmpcat;
	$safeurl =~ s/\W+//g;
	$safeurl = lc($safeurl);
	print "\n\n\n------------------------------------------\nREQUESTING CATEGORY [$foocat] SAVING TO: [$safeurl.html]\n------------------------------------------\n";
	
	$request = HTTP::Request->new('GET', $ZOOVYURL.$tmpcat);
	$result = $ua->request($request);
	$html = $result->content();
	($html) = &suckimages($html);
	($html) = &temp_sub_paths($html);

	open F, ">$TMPFILE"; print F $html; close F;
	$ftp->put($TMPFILE,$safeurl.'.html');
	}

## Now Lets do all the products
foreach $prod (@ALLPRODS)
	{
	$request = HTTP::Request->new('GET', $ZOOVYURL.'/product/'.$prod);
	$result = $ua->request($request);
	$html = $result->content();
	($html) = &suckimages($html);
	($html) = &temp_sub_paths($html);

	open F, ">$TMPFILE"; print F $html; close F;
	$ftp->put($TMPFILE,'product/'.$prod.'.html');
	}

$ftp->quit;


sub temp_sub_paths
{
	my ($html) = @_;

	foreach $prod (@ALLPRODS) {
		$safeurl = quotemeta($ZOOVYURL).'/product/'.$prod;
		$desturl = $webdb{'wwwpublish_baseurl'}."/product/".$prod.".html";
		print "REPLACING: $safeurl with $desturl\n";
		$html =~ s/$safeurl([\'\" ])/$desturl$1/gsi;
		}

#	use Data::Dumper;
#	print Dumper(\@CATEGORIES);

	@FOO = @CATEGORIES;
	foreach my $tmpcat (@FOO) {	
		next if ($tmpcat eq ' ');
		next if ($tmpcat eq '');
		$tmpcat = &ZNAVCAT::navcat_to_url($tmpcat);
#		print "AFTER: [$tmpcat]\n";
		$safename = $tmpcat;
		$safename =~ s/\W+//g;
		$safename = lc($safename);
		$safeurl = quotemeta($ZOOVYURL).$tmpcat;
		$desturl = $webdb{'wwwpublish_baseurl'}.'/'.$safename.".html";
		print "REPLACING: $safeurl with $desturl\n";
		$html =~ s/$safeurl[\/]?([\'\" ])/$desturl$1/gsi;
		}

	$safeurl = quotemeta($ZOOVYURL);
	$html =~ s/$safe_zoovyurl[\/]?([\"\' ]+)/$webdb{'wwwpublish_baseurl'}$1/gs;
	
	return($html);
}


sub suck_product
{
	my ($PRODUCT) = @_;

	$request = HTTP::Request->new('GET', $ZOOVYURL.'/product/'.$PRODUCT);
	$result = $ua->request($request);
	$html = $result->content();

	($html) = &suckimages($html);
	($html) = &tmp_sub_products($html);

	open F, ">$TMPFILE"; print F $html; close F;

	$ftp->put($TMPFILE,"product/$PRODUCT.html");
	$ftp->quit;

}



sub divout
{
	# Removed the divs and un-ended center tags. Neither are needed to make this update realtime.
	print "<table width='600' cellpadding='3' align='center'><tr><td>\n";
	foreach (@_) { print $_ . "<br>\n"; }
	print "</td></tr></table>\n\r";
}


##
## Note: $subref is a reference to a hash which will contain 
## urls - keyed by value, mapped to local imagelib collections 
## for future substitution.
##
sub suckimages
{
  my ($html) = @_;

	foreach my $tag (split(/(<*?>)/is,$html))
		{
		$missed = 1;

		# look in <img src= tags
		if ($tag =~ /src=[\"\']?(.*?)[\"\' ]+/is)	{
			$tag = $1; $missed = 0;
			}

		# download table backgrounds as well background=
		if ($tag =~ /background=[\"\']?(.*?)[\"\' ]+/is) {
			$tag = $1; $missed = 0;
			}

		# if we've already done this IMG then skip it
		if (defined($IMG_MAPPING{quotemeta($tag)})) { 
			$missed = 1;
			# print "SKIPPING $tag (already exists)\n";
			} 
		
		# if the tag already contains the base url, then no need to continue.
		if ($tag =~ /$safe_wwwpublish_baseurl/) {
			$missed = 1;
			}

		if ($tag eq '') { $missed = 1; }

		if (!$missed) {

#			use Data::Dumper;
#			print "TAG IS: [$tag]\n";
#			print Dumper(\%IMG_MAPPING)."\n";


			my $origtag = $tag;
			$origtag = quotemeta($origtag);

			## If the Graphic URL is in a relative directory add the CWD to make it fully qualified
			## if it has an HTTP then ignore it.
			if (substr($tag,0,1) ne '/' && uc(substr($tag,0,4)) ne 'HTTP') { $tag = $CWD.$tag; }

			## If the Graphic URL is missing the HTTP:// then assume is the path http://username.zoovy.com
			if (uc(substr($tag,0,4)) ne 'HTTP') { $tag = $ZOOVYURL.$tag; }

			if ($echodebug) { &IMPORT::divout("REMOTE COPYING: $tag\n"); }
			my ($newimg) = &remote_image_copy($tag);
				
			# print "REPLACING $tag \-\> $newimg\n";

			$IMG_MAPPING{$origtag} = $newimg;
			}

		} # end of foreach

	foreach my $tag (keys %IMG_MAPPING) {
		$html =~ s/$tag/$IMG_MAPPING{$tag}/g;
		}

	return($html);
}

sub remote_image_copy
{
	($SRC) = @_;

	# print "Retreiving $SRC\n";
	$request = HTTP::Request->new('GET', $SRC);
	$result = $ua->request($request);
	$img = $result->content();
	open F, ">$TMPFILE";
	print F $img; 
	close F;

	# print "Writing $FILENAME\n";

	if ($SRC =~ /static\.zoovy\.com\/img\/(.*?)\/(.*?)\/(.*?)$/) { 
		$FILENAME = $2.'-'.$3;
		} else {
		# Default Filename grabber
		$FILENAME = substr($SRC,rindex($SRC,'/')+1);
		}

	# if the file is missing a . then lets assume it's an imagelib file
	if (index($FILENAME,'.')==-1)
		{
		if ($result->content_type() eq 'image/gif') { $FILENAME .= '.gif'; }
		elsif ($result->content_type() eq 'image/jpg') { $FILENAME .= '.jpg'; }
		elsif ($result->content_type() eq 'image/jpeg') { $FILENAME .= '.jpg'; }
		elsif ($result->content_type() eq 'image/png') { $FILENAME .= '.png'; }
		else { 
			print "Unknown File Type: ".$result->content_type()."\n";
			$FILENAME .= '.'.substr($result->content_type(),index($result->content_type(),'/')+1); 
			}
		}
	# Strip out bad filenames ..
	$FILENAME =~ s/\%//g;
	
	$ftp->put($TMPFILE,'images/'.$FILENAME);
	
	$DEST = $webdb{'wwwpublish_baseurl'}.'/images/'.$FILENAME;
	# print "New URL is $DEST\n";

	return($DEST);
}



