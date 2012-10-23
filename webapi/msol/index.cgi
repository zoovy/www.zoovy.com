#!/usr/bin/perl

use CGI;
use lib "/httpd/modules";


my $q = new CGI;
my %v = ();
# Signature=([a-zA-Z0-9]+)\&UUID=([a-z0-9\-])\&Timestamp=(.*)\&ordercalculations-request=(.*)/) {
foreach my $p ($q->param()) {
#  $v{'Signature'} = $1;
#  $v{'UUID'} = $2;
#  $v{'Timestamp'} = $3;
#  $v{'REQUEST'} = $4;          ## see __DATA__ below for REQUEST XML example
   $v{"$p"} = $q->param($p);
   }

## REQUEST
## will need to modify per CBA specs
## https://webapi.zoovy.com/webapi/amazon/callback.cgi?
##      Signature=[Signature_value]&UUID=[UUID_value]&Timestamp=[Timestamp_value]&ordercalculations-request=[request_v
##
## values need to be decoded
foreach my $str (split(/\//,$ENV{'REQUEST_URI'})) {
  next unless ($str =~ /\=/);
  my ($k1,$v1) = split(/=/,$str);
  $v{"_$k1"} = $v1;
  }



print "Content-type: text/javascript\n\n";
print "document.write('hello world');\n";