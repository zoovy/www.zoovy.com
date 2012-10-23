#!/usr/bin/perl

use CGI;
use URI::Escape;
use lib "/httpd/modules";
use ZTOOLKIT;

$q = new CGI;

# VL sty;e
# /webapi/aol/flexui.cgi?siteId=zoovy&mcCtx=pw&mcCtx2=verify&langLoc=en%2dus&siteState=OrigUrl%3dhttp%253a%252f%252faol%2ezoovy%2ecom%252fnerdgear%252flogin%2ecgis
# SNS style:
# /webapi/aol/flexui.cgi?siteId=zoovy&siteState=MERCHANT
#

$SITESTATE = $q->param('siteState');
$ORIGURL = URI::Escape::uri_unescape($SITESTATE);
$params = &ZTOOLKIT::parseparams($ORIGURL);
if (defined $params{'OrigUrl'}) {
	## VL style (where we obtain merchant id based on the return url)
	my $refer = $params->{'OrigUrl'};

	my $USERNAME = '';
	# strip out any embedded session ids
	$refer =~ s/\/c\=(.*?)\//\//gs;

	if ($refer =~ /\/aolsale\.cgi/) {
		$USERNAME = '*';
		}
	elsif ($refer =~ /zoovy\.com\/(.*?)\/login\.cgis/) {
		$USERNAME = $1;
		}
	else {
		$USERNAME = '*';
		}
	}
else {
	## SNS style - where we pass merchant id in siteState variable
	$USERNAME = $q->param('siteState');
	}

#$USERNAME = '*';
if ($USERNAME eq '*') {
	print "Content-type: text/html\n\n";
	print "<!-- refer: print $refer -->";
	print "<!-- AOL Classifieds Login -->";
	open F, "<flexui.html";
	my $buffer = '';
	$/ = undef; while (<F>) { $buffer .= $_; } $/ = "\n";
	close F;
	print $buffer;
	}
else {
	require ZOOVY;
	require ZWEBSITE;
	require IMGLIB;
	# require SITE;

	$ENV{'merchant_id'} = $USERNAME;
	$ENV{'merchant_dir'} = &ZOOVY::resolve_userpath($USERNAME);	

	# my $out;
	# &SITE::init('flexui','dbopen'=>'0');
	# print "Content-type: text/html\n\n";	
	# $out .= &SITE::wrapper_top(); 
	# $out .= "<LINK rel=stylesheet href=\"http://classifieds.aol.com/cblib/css/header.css\">";
	# $out .= "<!--SNSmodule-->";
	# $out .= &SITE::wrapper_bottom(); 

	# $out =~ s/<script.*?<\/script>//igs;
	# $out =~ s/<\!DOCTYPE.*?>//igs;
	# $out =~ s/<title>.*?<\/title>/<TITLE>SNSLogin<\/TITLE>/igs;
	# $out =~ s/<map(.*?)<\/map>//igs;
	
	## <IMG src="<!-- LOGOURL -->" alt=Main width=315 height=54 border=0>
	my $logo = &ZWEBSITE::fetch_website_attrib($USERNAME,"company_logo");
	my ($actual_width,$actual_height) = &IMGLIB::minimal_size($USERNAME, $logo, 315, 54);
	print STDERR "MINIMAL: w=$actual_width actual_height=$actual_height\n";
	$logo = &IMGLIB::url_to_image($USERNAME,$logo,$actual_width,$actual_height,'ffffff');
	$logo = "<img align=\"right\" border=0 src=\"$logo\">";
	
	my $greeting = '&nbsp;'.&ZWEBSITE::fetch_website_attrib($USERNAME,'website_name')."<br>";
	$greeting .= '&nbsp;'.&ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:website_url');

	print "Content-type: text/html\n\n";
	print "<!-- Merchant: $USERNAME login -->"; 

	open F, "<merchant.html";
	my $buffer = '';
	$/ = undef; while (<F>) { $buffer .= $_; } $/ = "\n";
	close F;
	$buffer =~ s/<!-- WEBSITE -->/http\:\/\/$USERNAME\.zoovy\.com/gs;
	$buffer =~ s/<!-- LOGO -->/$logo/gs;
	$buffer =~ s/<!-- GREETING -->/$greeting/gs;
	print $buffer;

	open F, ">/tmp/aol";
	print F $buffer;
	close F;
	
	}
