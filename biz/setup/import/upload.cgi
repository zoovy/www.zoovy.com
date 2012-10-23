#!/usr/bin/perl

use  strict;
	
use CGI;
use Data::Dumper;
my $q = new CGI;


use lib "/httpd/modules";
use LUSER;
use LUSER::FILES;
use ZCSV;


my ($LU) = LUSER->authenticate('zjsid'=>$q->param('ZJSID'),flags=>'_M&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT,$RESELLER) = $LU->authinfo();
if ($MID<=0) { exit; }


use Data::Dumper;
print STDERR Dumper($q);

my $ERROR = undef;
my $fh = $q->param('file');
my $filename = $fh;
print STDERR "FILENAME: $filename\n";
if (not defined $fh) {
   ## Crap, not defined!
	$ERROR = "File was not transmitted as 'file' param";
   }

my $VERB = $q->param('VERB');

## currently we pass all form variables in a serialized "thisFrm"
my $thisFrm = $q->param('thisFrm');
my $directives = {};
if ((not $ERROR) && ($thisFrm eq '')) {
	$ERROR = "serialize thisFrm is empty";
	}
else {
	$directives = &ZTOOLKIT::parseparams($thisFrm);
	delete $directives->{'hidFileID'};	## ignore this.
	delete $directives->{'btnSubmit'};	## ignore this.
	}

if (defined $directives->{'LOADTYPE'}) {
	## LOADTYPE is a deprecated parameter.
	$directives->{'TYPE'} = $directives->{'LOADTYPE'};
	delete $directives->{'LOADTYPE'};
	}

my $BUFFER = undef;

## eventually this could probably be merged into ZCSV:
if ($ERROR) {
	## shit already happened.
	}
elsif ($filename =~ /\.xls$/i) { 
	$ERROR = "Filename has an .xls extension - should be .csv"; 
	}
elsif (($directives->{'VERB'} eq 'UPLOAD-JEDI') && ($filename =~ /\.zip$/i)) {
	## JEDI files are special.
	if (defined $fh) {
		$/ = undef; $BUFFER = <$fh>; $/ = "\n"; # while (<$fh>) { $BUFFER .= $_; }
		}
	}
elsif ($filename =~ /\.zip$/i) { 
	my $zip = Archive::Zip->new();
	$zip->read($filename);
	# $zip->readFromFileHandle($fh);
	my @names = $zip->memberNames();
	foreach my $m (@names) {
		next unless (($m =~ /.txt$/i) || ($m =~ /.csv/i));
		$BUFFER = $zip->contents($m);
		}
	if ($BUFFER eq '') {
		$ERROR = "No valid .csv or .txt files found in zip.";
		}
	}
elsif ($filename =~ /(\.txt|\.csv)$/i) {
	## valid filename.
	if (defined $fh) {
		$/ = undef; $BUFFER = <$fh>; $/ = "\n"; # while (<$fh>) { $BUFFER .= $_; }
		}
	if (length($BUFFER)<10) {
		$BUFFER = undef;
		$ERROR = "File is too small to be valid";
		}
	}
else {
	$ERROR = "Unknown file type: $filename";
	}


## ZCSV::addFile does the heavy lifting. .. this lets us consolidate a bunch of logging/error handling routines.
my $FILETYPE = $directives->{'TYPE'};
my $JOBID = 0;
if (not defined $ERROR) {
	($JOBID,$ERROR) = &ZCSV::addFile(
		'*LU'=>$LU,
		SRC=>'USER',
		BUFFER=>$BUFFER,
		'TYPE'=>$directives->{'TYPE'},
		'%DIRECTIVES'=>$directives,
		FILETYPE=>(($directives->{'VERB'} eq 'UPLOAD-JEDI')?'JEDI':'CSV'),
		);
	}

print "Content-Type: text/plain\n\n";
if ($JOBID==0) {
	print STDERR "SENDING ERROR[$ERROR]\n";
	print "ERROR:$ERROR\n";
	}
else {
	print "JOBID:$JOBID\n";
	$LU->log("SETUP.IMPORT.$FILETYPE","$FILETYPE Import $ERROR (job:$JOBID)","INFO");
	}
print STDERR "UPLOADFILE[$USERNAME] JOB:$JOBID\n";
