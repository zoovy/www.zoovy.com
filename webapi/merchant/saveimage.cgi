#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
require ZOOVY;
require IMGLIB;
use strict;

$|++;
my $q = new CGI;

my $USERNAME = lc($q->param("USERNAME"));
if ($USERNAME eq "") { $USERNAME = lc($q->param('REMOTE_USER')); }	 # legacy

my $VERSION = $q->param('VERSION');
if (!defined($VERSION)) { $VERSION = 1; }

my $PASSWORD = $q->param("PASSWORD");

print STDERR "/webapi/client/imagelib.cgi USERNAME=[$USERNAME] PASSWORD=[$PASSWORD] VERSION=[$VERSION]\n";

if (!$USERNAME) 
   { 
   print $q->header(-type=>"text/error");
   print "ERROR: No username specified.\n"; exit(0); 
   }

my $filename = $q->param('IMAGE_FILE');
if ( (!defined($filename)) && ($VERSION<3) && (!defined($q->param('DELETE_COLLECTION'))) && (!defined($q->param('DELETE_URL'))) ) {
	print $q->header("text/error");
	print "ERROR: IMAGE_FILE or DELETE_COLLECTION or DELETE_URL not specified [what am I supposed to do??].\n";
	exit(0);
	} 


# We always read the contents of $filename into BUFFER
my $BUFFER = undef;
if (defined $q->param('CONTENTS')) {
	$BUFFER = $q->param('CONTENTS');
	}
elsif (defined $q->param('IMAGE_FILE')) {
	while (<$filename>) { $BUFFER .= $_; }
	}


if (($VERSION < 3) || (defined $PASSWORD)) {
	if (!$PASSWORD) { 
	   print $q->header(-type=>"text/error");
		print "ERROR: No password for $USERNAME specified.\n"; exit(0); 
		}

	if (! &ZOOVY::verifypassword($USERNAME,$PASSWORD,1)) {
		print $q->header(-type=>"text/error");
		print "ERROR: Invalid Username/Password\n"; exit(0);
		}
	}
else {
	if (!&ZOOVY::verify_md5pass($USERNAME,$PASSWORD,$q->param('NAME').$BUFFER)) {
		print "Content-type: text/error\n\n";
		print "ERROR: Invalid MD5 password.\n"; exit(0);
		}
	}






if ($VERSION==1)
	{
	my ($STATUS,$URL) = ();
	if ($q->param('DELETE_URL')) { IMGLIB::delete_image($USERNAME, $q->param('DELETE_URL')); $STATUS = 0; }
	if ($filename) { ($STATUS, $URL) = IMGLIB::store_image($USERNAME, $filename, $BUFFER); }

	if (!$STATUS) 
		{ 
		print "Content-type: text/plain\n\n<url>$URL</url>\n"; 
		} else { 
		print "Content-type: text/error\n\nERROR: Could not save/delete file\n"; 
		}
	}	 

elsif ($VERSION == 2 || $VERSION == 3)
	{
	my $STATUS = 0;
	my $COLLECTION = '';
	# NOTE: $filename (as a scalar) should contain the name of the file.
	
	if (defined($BUFFER))
		{		
		my $ext = 'PNG'; ## default

		# see if we can get an extension from filename, otherwise assume it's a PNG
		if (index($filename,'.')>=0) { $ext = substr($filename,rindex($filename,'.')+1); } else { $ext = 'PNG'; }

		# if they have a preferred name, lets use that.
		if (defined($q->param('NAME'))) { $filename = $q->param('NAME'); }

		print STDERR "Assuming Filename is [$filename]\n";
		if (index($filename,'.')>=0)
			{
			# has file extension
			$ext = substr($filename,rindex($filename,'.')+1);
			$filename = substr($filename,0,rindex($filename,'.'));
			print STDERR "overwriting defaults with best guess [$ext] [$filename]\n";
			} else {
			# no extension?? Hmm..
			}

		if ($filename)
			{
			# Quick sanity
			print STDERR "Calling IMGLIB::create_collection($USERNAME,$filename,$ext,buffref)\n";		
			($STATUS, $COLLECTION) = &IMGLIB::create_collection($USERNAME,$q->param('NAME'),$ext,\$BUFFER);
			&IMGLIB::nuke_instances($USERNAME,$COLLECTION);
			}
		}

	if (($STATUS == 0) && ($q->param('DELETE_COLLECTION'))) {

		if (uc($USERNAME) ne 'SHOEBACCA') {
			&IMGLIB::nuke_instances($USERNAME,$q->param('DELETE_COLLECTION'));
			&IMGLIB::nuke_collection($USERNAME,$q->param('DELETE_COLLECTION'));
			}
		else {
			&IMGLIB::quick_nuke($USERNAME,$q->param('DELETE_COLLECTION'));
			}
		print STDERR "Deleted ".$q->param('DELETE_COLLECTION')."\n";
		}

	if ($STATUS==0)
		{
		print "Content-type: text/success\n\n<collection>$COLLECTION</collection>\n\n";
		} else {
		print "Content-type: text/error\n\nERROR: $COLLECTION\n\n";
		}

	}



exit(0);
