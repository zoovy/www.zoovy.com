#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use CHANNEL;
use CHANNEL::MERCHANT;
use CHANNEL::SCHEDULER;
use GTOOLS;
use DBINFO;
use ZTOOLKIT;
use Data::Dumper;

($USERNAME,$FLAGS) = &ZOOVY::authenticate('','/biz',1);


$ref = &CHANNEL::SCHEDULER::fetch_schedulers($USERNAME,3);
%products = ();
foreach $channel (keys %{$ref}) {
	$products{$ref->{$channel}->{'PRODUCT'}}++;
	}

my @ar = keys %products;
my $hashref = &ZOOVY::fetchproducts_into_hashref($USERNAME,\@ar);


$GTOOLS::TAG{'<!-- FOO -->'} = "<pre>".Dumper($ref)."</pre>";

$c = '<tr><td>CHANNEL</td><Td colspan="2">Created</td><td colspan="2">Interval</td><td colspan="2">Last Launch</td><td colspan="2">Next Launch</td></tr>';
foreach $channel (reverse sort keys %{$ref}) {	
	$c .= "<tr><td>$channel</td>";
	$c .= "<td>".&ZTOOLKIT::pretty_date($ref->{$channel}->{'CREATED'},1)."</td>";
	$c .= "<td>&nbsp;</td>";
	$c .= "<td>".&ZTOOLKIT::pretty_time_since(1,$ref->{$channel}->{'LAUNCH_INTERVAL'}+1)."</td>";
	$c .= "<td>&nbsp;</td>";
	$c .= "<td>".&ZTOOLKIT::pretty_date($ref->{$channel}->{'LASTLAUNCH'},1)."</td>";
	$c .= "<td>&nbsp;</td>";
	$c .= "<td>".&ZTOOLKIT::pretty_date($ref->{$channel}->{'NEXTLAUNCH'},1)."</td>";
	$c .= "<td>&nbsp;</td>";
	$c .= "<td>$ref->{$channel}->{'PRODUCT'}</td>";
	$c .= "<td>$ref->{$channel}->{'MARKET'}.$ref->{$channel}->{'DEFINITION'}</td>";
	$c .= "</tr>\n";
	}
$GTOOLS::TAG{'<!-- LIST -->'} = $c;

&GTOOLS::output(file=>'index.shtml',header=>1);