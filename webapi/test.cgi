#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;

$q = new CGI;

print "Content-type: text/plain\n\n";

print "List of Parameters Received:\n";
foreach $param ($q->param)
  {
   print "$param=".$q->param($param)."\n";
  }