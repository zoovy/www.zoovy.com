#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use CGI;

($USERNAME) = &ZOOVY::authenticate();

print "Content-Type: text/html\n\n";
print "<html>";
print "<frameset rows=\"120,*\" frameborder=0 framespacing=0 border=0>";
print "<frame src=\"title.cgi\" name=\"title\" frameborder=0 border=0 scrolling='no' noresize>";
print "<frame src=\"main.shtml\" name=\"main\" frameborder=0 border=0>";
print "</frameset>";
print "</html>";

