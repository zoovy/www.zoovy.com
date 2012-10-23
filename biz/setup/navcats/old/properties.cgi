#!/usr/bin/perl

use lib "/httpd/modules";
use GT;

use CGI;

$q = new CGI;

$navcat = $q->param('navcat');

$GT::TAG{"<!-- NAVCAT -->"} = $navcat;
$template_file = "properties.shtml";


print $q->header();
GT::print_form("",$template_file);
