#!/usr/bin/perl

use lib "/httpd/modules";
use POGS;

my $json = q~[{"global":"0","v":"2","sog":"A1","@options":[{"w":"77","p":"77","v":"02","prompt":"3"},{"w":"","p":"","v":"00","prompt":"1"},{"w":"55","p":"55","v":"01","prompt":"2"}],"prompt":"BOXinMAN","amz":"FOOD: Color","inv":"1","goo":"Color","type":"select","id":"A1","ghint":""}]~;
use Data::Dumper;
print Dumper(&POGS::from_json($json));

__DATA__
<pog id="20" prompt="Simple Colors" inv="0" global="0" type="select" sog="20-colors_simple" cols="1" zoom="on">
<option v="AK" m="w=|p=">Blue<option>
<option v="BK" m="w=|p=">Coral<option>
<pog>
