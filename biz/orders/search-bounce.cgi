#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use GTOOLS;

$q = new CGI;

$GTOOLS::TAG{'<!-- FIND_STATUS -->'} = $q->param('find_status');
$GTOOLS::TAG{'<!-- SEARCH_FIELD -->'} = $q->param('search_field');
$GTOOLS::TAG{'<!-- FIND_MONTH -->'} = $q->param('find_month');
$GTOOLS::TAG{'<!-- FIND_TEXT -->'} = CGI->escape($q->param('find_text'));

&GTOOLS::output(file=>'../search-results.shtml',header=>1);
