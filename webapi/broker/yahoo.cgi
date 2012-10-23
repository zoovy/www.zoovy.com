#!/usr/bin/perl

use lib "/httpd/modules";
use lib "/httpd/servers/modules";
use CGI;
use ZAUTH;
use ZOOVY;
use ZOOVYLITE;
use GT;
use lib ".";


$|++;
$q = new CGI;

#$USERNAME = $q->param("USERNAME");
#$PASSWORD = $q->param("PASSWORD");
#if (!$USERNAME && !$PASSWORD) 
#   { 
#   # if they didn't pass username, then lets try cookie authentication
#   ($SESSION_STATUS, $USERNAME) = ZAUTH::verify_cookie();
#   if (!$USERNAME || $SESSION_STATUS != 0) 
#      {
#      print $q->header(-type=>"text/plain");
#      print "ERROR: Invalid Username/Password or not specified! ($SESSION_STATUS -> $USERNAME)\n";
#      exit; 
#      }
#   } else {
#   if (!ZOOVY::verifypassword($USERNAME,$PASSWORD,1))
#      { 
 #     print $q->header(-type=>"text/plain");
#      print "ERROR: Invalid Username/Password\n"; 
#      exit(0); 
#      }
#   }
#
$ZOOVY = $q->unescape($q->param('ZOOVY'));

print $q->header;

# print STDERR "ZOOVY is=[$ZOOVY]\n";
%vars = ZOOVYLITE::safe_attrib_handler($ZOOVY);
#foreach (keys %vars) { $c .= "[$_]=>[".$vars{$_}."]\n"; }
$img = &GT::imageurl($USERNAME,$vars{'zoovy:prod_image1'},200,200,'FFFFFF');

# yahoo doesn't support bgcolor, or backgrounds
$vars{'zoovy:html'} =~ s/bgcolor=/nobgcolor=/igs;
$vars{'zoovy:html'} =~ s/background=/nobackground=/igs;


$c .= "<center><b>".$vars{'yahoo:title'}."</b></center><br>";
$c .= "<hr>".$vars{'zoovy:html'}."<br><br>\n\n";

$GT::TAG{"<!-- FOO -->"} = $c;
&GT::print_form("","yahoo.shtml");

exit(0);
