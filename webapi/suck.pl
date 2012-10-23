#!/usr/bin/perl
## suck.pl

## called from app5:/home/autofile/process.pl
## pulls messages from "bounced" newsletters
## that need to be processed

use strict;
use Fcntl qw(:flock);
use POSIX ();
POSIX::nice(10);

# This is how many files we process at a time.
my $BATCHSIZE="1000";
my $MAXLOAD="20.0";
my $TAR="/bin/tar";

## LOCK 
# Make sure more than one copy of this script is not running.
open(LOCK, ">LOCK") or die "open LOCK: $!\n";
flock(LOCK, LOCK_EX|LOCK_NB) or die "flock: $!\n";

## CHECK LOAD
# Make sure we aren't contributing to the demise of a system.
open(LOAD, "/proc/loadavg");
my $load=<LOAD>;
close(LOAD);
$load =~ s/ .*//;
die "CPU load $load > $MAXLOAD.  Try again later.\n" if $load > $MAXLOAD;
use POSIX ();
POSIX::nice(10);
print "got past init\n";

my $PATH = "/home/autofile/Maildir/new";

# Move a batch of files into "Mailbox/cur"
chdir "$PATH" or die "cd Maildir/new: $!\n";
opendir (D, ".") or die "read Maildir: $!\n";
my $count=0;
my $list='';
my $entry='';
my @files=();
while (my $entry = readdir(D)) {
  next if (substr($entry,0,1) eq '.');
  if (($entry =~ /^msg-/) || ($entry =~ /([^Tt][^Xx][^Tt])$/i)) {
    print "REMOVING ENTRY: $entry\n";
    unlink "/home/autofile/Maildir/new/$entry";
    }
  next unless($entry =~ /^[1-9]/);
  push @files, $entry;

#  rename("$entry", "../cur/$entry") or die "move $entry: $!\n";
  last if $count++ > $BATCHSIZE;
  }
closedir(D);
print "$count entries\n$list";
exit 0 unless $count;

use Data::Dumper;

use MIME::Entity;
use MIME::Parser;
use LWP::UserAgent;
   
my $ua = LWP::UserAgent->new();
$ua->timeout(10);
                                                                                                
                                                                                                
$/ = undef;
my $parser = new MIME::Parser;
 
foreach my $file (@files) {
  print $file."\n";
  
  my $ent = $parser->parse(new IO::File "$PATH/$file", "r");
  my $head = $ent->head();
  $head->unfold();

  # print Dumper($ent);
  
  my ($TO) = $head->get('To', 0); $TO =~ s/[\n\r]+//g;
  my ($FROM) = $head->get('From', 0); $FROM =~ s/[\n\r]+//g;
  my ($SUBJECT) = $head->get('Subject', 0); $SUBJECT =~ s/[\n\r]+//g;

  my ($CPNID,$CPG,$USERNAME,$DOMAIN) = ();

  my @parts = ();
  foreach my $part ($ent->parts()) {
    push @parts, $part;
    foreach my $part2 ($part->parts()) {
      push @parts, $part2;
      foreach my $part3 ($part2->parts()) {
        push @parts, $part3; 
        }
      }
    }
  
  foreach my $part (@parts) {
     my $head = $part->head();
     my $DESC = $head->get('Content-Description',0); $DESC =~ s/[\n\r]+//g;
     my $TYPE = $head->get('Content-Type',0); $TYPE =~ s/[\n\r]+//gs;
     my $TYPE = $head->get('Content-Type',0); $TYPE =~ s/[\n\r]+//gs;
        
     #print "TYPE: $TYPE ($DESC)\n";
     #print $part->as_string();

     foreach my $line (split(/[\n\r]+/,$part->as_string() )) {
       if ($line =~ /^X-Postfix-Sender: rfc822; (.*?)$/io) { $TO = $1; } 
       elsif ($line =~ /^Final-Recipient: rfc822; (.*?)$/io) { $FROM = $1; } 
       # elsif ($line =~ /^X-Actual-Recipient: RFC822; (.*?)$/io) { $FROM = $1; }

       if ($line =~ /webbug\.cgi\/CPG=(3D)?\@CAMPAIGN:([\d]+)\/CPN=(3D)?([\d]+)\/([A-Za-z0-9]+)\.gif/iso) {
          ($CPG,$CPNID,$USERNAME) = ($2,$4,$6);
          }
       elsif ($line =~ /cpg\=(3D)?\@CAMPAIGN\:([\d]+)\&cpn\=(3D)?([\d]+)/iso) {
          ($CPG,$CPNID) = ($2,$4);
          }
       else {
  #        print "\nLINE: $line\n";
  #      die('xyz');
          }
       }
  
     print "--[$TYPE]------------------------------------------\n";
  
  #   print "TO: ".$head->get('To',0)."\n";
  #   print Dumper($part);
     }
     
  ## convert "bob <bob@domain.com>" to simply bob@domain.com  
  $TO =~ s/^.*<(.*?)>.*$/$1/;
  if (($DOMAIN eq '') && ($TO =~ /@(.*?)$/)) { $DOMAIN = $1; }
  
  $FROM =~ s/^.*<(.*?)>.*$/$1/;
  if ($FROM =~ /MAILER-DAEMON@/i) { $TO = ''; }
  
  print "To: $TO\n";
  print "From: $FROM\n";
  print "Subject: $SUBJECT\n";
  print "CPG=$CPG CPNID=$CPNID USER=$USERNAME\n\n";

  if (($TO ne '') || ($CPG ne '') || ($CPNID ne '')) {
    my $response = $ua->get("http://webapi.zoovy.com/webapi/newsletter/bounce.pl?USERNAME=$USERNAME&DOMAIN=$DOMAIN&EMAIL=$FROM&CPG=$CPG&CPNID=$CPNID");
    if ($response->is_success) {
      print $response->content;  # or whatever
    
      if ($response->content =~ /Recorded-Bounce/) { unlink("$PATH/$file"); } 
      elsif ($response->content =~ /Found-Customer/) { unlink("$PATH/$file"); } 
      }
    else {
      die $response->status_line;
      }
   }
  
  
  # if ($ARGV[0] eq '1') { die();  }
  unlink("$PATH/$file");
  
   
  # print "$buf\n";
  # die();
  
  }
$/ = "\n";

exit;


# Create a batch and print it to STDOUT

chdir("../cur") or die "chdir cur: $!\n";
my $tmp="/tmp/suck.$^T.$$";
open(LIST, ">$tmp") or die "write list $tmp: $!\n";
print LIST $list;
close(LIST) or die "write list $tmp: $!\n";
my $cmd="$TAR -T $tmp -cpzf /var/tmp/suck.tar";
system($cmd) == 0
  or die "system exit $?: $!\ncommand: $cmd\n";
sleep 2;

# Clean up
unlink $tmp || warn "unlink $list: $!\n";
