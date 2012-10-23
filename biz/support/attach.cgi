#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use CGI;
use SUPPORT;

my $q = new CGI;
my $TICKET = $q->param('TICKET');
if ($TICKET eq '') { $TICKET = -1; } else { $TICKET = int($TICKET); }
$GTOOLS::TAG{'<!-- TICKET -->'} = $TICKET;

&ZOOVY::init();
my ($USERNAME) = '';

use Data::Dumper;
print STDERR Dumper($q);
print STDERR Dumper(%ENV);

if ($ENV{'REMOTE_USER'} ne '') {
	## this is being accessed from https://admin.zoovy.com/support/attach.cgi
	# note: i'm not sure if this is a symlink, or where it exists, but this is how we should check to see if a person
	# is allowed to access this script without needing an auth token from the ticket queue.
	($USERNAME) = $q->param('CUSTOMER');
	}
else {
	($USERNAME) = &ZOOVY::authenticate("http://support.zoovy.com");
	}
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
my ($MID) = &ZOOVY::resolve_mid($USERNAME);



exit if $USERNAME eq '';
$GTOOLS::TAG{'<!-- CUSTOMER -->'} = $USERNAME;

my $path = &ZOOVY::resolve_userpath($USERNAME);
print STDERR "Gone into attachments for $USERNAME ticket $TICKET using path : $path\n";


my $dbh = &SUPPORT::db_support_connect();
if ($q->param('ACTION') eq 'DONE' || $TICKET < 0) {
	if ($TICKET>0) {
		print "Content-type: text/html\n\n<body onLoad=\"opener.location = opener.location; window.close();\"></body>";
		}
	else {
		print "Content-type: text/html\n\n<body onLoad=\"window.close();\"></body>";
		}
	exit;
	}

if ($q->param('ACTION') eq 'NUKE') {
	my $pstmt = "select ID,STORED_NAME from TICKET_ATTACHED_FILES where MID=$MID /* $USERNAME */ and ID=".$dbh->quote($q->param('ID'));
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	if ($sth->rows) {
		my ($ID,$FILE) = $sth->fetchrow();
		unlink($path."/".$FILE);
		my $pstmt = "delete from TICKET_ATTACHED_FILES where ID=".$dbh->quote($ID);
		print STDERR $pstmt."\n";
		$dbh->do($pstmt);
		}
	$sth->finish();
	}

if ($q->param('ACTION') eq 'UPLOAD') {
	my $F = $q->param('thisfile');
	$/ = undef;
	my $buf = <$F>;
	$/ = "\n";

	print STDERR "LENGTH: ".length($buf)."\n";
	if (length($buf)>0) {
		my ($f,$e) = strip_filename($F);
		if (! -d "$path/IMAGES") { mkdir (0777,"$path/IMAGES"); }
		open F, ">$path/IMAGES/TICKET_$TICKET-$f.$e";
		print F $buf;
		close F;
		print STDERR "Saving file to $path/IMAGES/TICKET_$TICKET-$f.$e\n";
	
		my $localfile = "IMAGES/TICKET_$TICKET-$f.$e";
		my ($pstmt) = &DBINFO::insert($dbh,'TICKET_ATTACHED_FILES',{
			USERNAME=>$USERNAME,
			MID=>$MID,
			TICKET=>$TICKET,
			TASK=>0,
			'*CREATED'=>'now()',
			UPLOAD_FILENAME=>$q->param('thisfile'),
			STORED_NAME=>$localfile,
			},debug=>1+2);
	#	my $pstmt = "insert into TICKET_ATTACHED_FILES (MERCHANT,TICKET,CREATED,UPLOAD_FILENAME,STORED_NAME) values ";
	#	$pstmt .= "(".$dbh->quote($USERNAME).",".$dbh->quote($TICKET).",now(),".$dbh->quote($q->param('thisfile')).",".$dbh->quote($localfile).")";
		print STDERR $pstmt."\n";	
		$dbh->do($pstmt);
		}
	else {
		$GTOOLS::TAG{'<!-- ERROR -->'} = '<font color="red">Received zero byte file - cannot save.</font>';
		}
	
	}

my $pstmt = "select ID,UPLOAD_FILENAME,STORED_NAME from TICKET_ATTACHED_FILES where MID=$MID /* $USERNAME */ and TICKET=".$dbh->quote($TICKET);
print STDERR $pstmt."\n";
my $sth = $dbh->prepare($pstmt);
$sth->execute();
my $c = '';
my $counter=0;
my $class = '';
while ( my ($ID,$ORIG,$REMOTE) = $sth->fetchrow() ) {		
	$class = ($class eq 'r1')?'r0':'r1';
	
	my $REMOTE = $path."/".$REMOTE;
	my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($REMOTE);
	print STDERR "REMOTE: $REMOTE\n";
	next if ($size == 0);
	$size = sprintf("%.1f",$size/1024);

	$c .= qq~
	<tr>
		<td class='$class'><a href="/support/attach.cgi?ACTION=NUKE&ID=$ID&TICKET=$TICKET&CUSTOMER=$USERNAME">[Del]</a></td>
		<td class='$class'>$ORIG</td>
		<td class='$class'>$size</td>
	</tr>
	~;
	}
$sth->finish();

if ($c eq '') {
	$c = qq~
		<tr>
	       <td class="r0">&nbsp;</td>
	       <td class="r0">- No Files Selected -</td>
	       <td class="r0">&nbsp;</td>
		</tr>
	~;
	}
$GTOOLS::TAG{'<!-- RESULT -->'} = $c;


&GTOOLS::output(file=>'attach.shtml',header=>1,popup=>1);
&SUPPORT::db_support_close();

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
		$name =~ s/\W+/_/g;
		} else {
		# very bad filename!! ?? what should we do!
		}

	# we should probably do a bit more sanity on the filename right here

	print STDERR "upload.cgi:strip_filename says name=[$name] extension=[$ext]\n";
	return($name,$ext);
}
