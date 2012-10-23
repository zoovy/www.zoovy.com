#!/usr/bin/perl -w

$debug = 0;

use lib '/httpd/modules';
use ZOOVY;
ZOOVY::authenticate('/biz/reports/index.cgi');

use ZWEBSITE;
use GTOOLS;
use ZTOOLKIT;
use Time::Local;
use Time::Zone;

my @months = ('January','February','March','April','May','June','July','August','September','October','November','December');

$ts = &ZTOOLKIT::timetohash(time);
$now_month = $ts->{'mon'};
$now_year = $ts->{'year'} + 1900;
$year = 2000;
$month = $now_month -1;
if ($month == -1) {
	$month = 11;
	$year = $now_year - 2;
}

my $count = 1;
$c = '';
for (@months) {
	if ($count == ($now_month + 1)) {
		$c .= "<option value=\"$count\" selected>$_\n";
	}
	else {
		$c .= "<option value=\"$count\">$_\n";
	}
	$count++;
}
$GTOOLS::TAG{'<!-- MONTHS -->'} = $c;

$c = '';
while ($year <= $now_year) {
	if ($year == $now_year) {
		$c .= "<option value=\"$year\" selected>$year\n";
	}
	else {
		$c .= "<option value=\"$year\">$year\n";
	}
	$year++;
}
$GTOOLS::TAG{'<!-- YEARS -->'} = $c;
&GTOOLS::print_form('Sales Report','index.shtml',1);
exit;

