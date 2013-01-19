#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use ZOOVY;

$q = new CGI;
($USERNAME) = &ZOOVY::authenticate();

$file = $q->param('file');
print "Content-type: text/html\n\n";
print "<html>";
print "<head><link REL='STYLESHEET' TYPE='text/css' HREF='/standard.css'></head><body>";
print "HTML CODE (copy and paste this into any HTML document):<br>";

$file = 'http://static.zoovy.com/merchant/'.$USERNAME.'/'.$file;
print "<pre>";
print "&lt;img src=\"$file\" border=\"0\"&gt;\n";
print "</pre>";
print "<br><br>";
print "<br><b>Preview:</b><br>";
print "<img src=\"$file\">";
print "</body>";
print "</html>\n";

