#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use ZOOVY;
use ZMAIL;


$DEBUG = 0;

$|++;
$q = new CGI;

$USERNAME = $q->param("USERNAME");
$PASSWORD = $q->param("PASSWORD");
$SUBJECT = $q->param("SUBJECT");
$MESSAGE = $q->param("MESSAGE");
$RECIPIENT = $q->param("RECIPIENT");

open F, ">>/tmp/sendmail.log";
print F "------------------------------------\n";
print F "USERNAME: $USERNAME\n";
print F "PASSWORD: $PASSWORD\n";
print F "RECIPIENT: $RECIPIENT\n";
print F "SUBJECT: $SUBJECT\n";
print F "MESSAGE: $MESSAGE\n";
close F;
	
if (!$USERNAME) 
   { 
   print $q->header(-type=>"text/error");
   print "ERROR: No username specified.\n"; exit(0); 
   }

if (!$PASSWORD) 
   { 
   print $q->header(-type=>"text/error");
   print "ERROR: No password for $USERNAME specified.\n"; exit(0); 
   }

if (!ZOOVY::verifypassword($USERNAME,$PASSWORD))
   { 
   print $q->header(-type=>"text/error");
   print "ERROR: Invalid Username/Password\n"; exit(0); 
   }

print "Content-type: text/html\n\n";
# we should do a quick check to make sure the user exists.

if ($DEBUG) { print "RECIPIENT: $RECIPIENT\n"; }
$SENDTO = "";
if (&ZOOVY::fetchmerchant_attrib($RECIPIENT,"zoovy:support_email") =~ /(^[\w|\.]\@[\w|\.])$/)
   { $SENDTO = "$1"; 
   } else { $SENDTO = &ZOOVY::fetchmerchant_attrib($RECIPIENT,"zoovy:email"); }
if ($SENDTO eq "") { $SENDTO = "support\@zoovy.com"; }

$SENDFROM = "";
if (&ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:email") =~ /(^[\w|\.]\@[\w|\.])$/)
   { $SENDFROM = "$1"; } 
if ($SENDFROM eq "") { $SENDFROM = "support\@zoovy.com"; }
#

if ($DEBUG) { print "SENDTO: $SENDTO\n USERNAME: $USERNAME\n"; }

if (!&ZMAIL::sendmail($USERNAME,$SENDTO,$SUBJECT,$MESSAGE,""))
  {
   print "SUCCESS: $SENDTO\n\n"; 
  } else {
   print "ERROR: Could not send mail!\n\n";
  }

