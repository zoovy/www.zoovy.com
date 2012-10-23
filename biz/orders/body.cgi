#!/usr/bin/perl

use strict;

use CGI;
my ($q) = new CGI;

my $CMD = $q->param('CMD');
my $ORDERIDS = $q->param('ORDERIDS');
my $SORTBY = $q->param('SORTBY');

print "Content-type: text/html\n\n";
print qq~
<html>
<frameset rows="*,50" frameborder="0" framespacing="0" border="0">
	<frame src="main.cgi?CMD=$CMD&ORDERIDS=$ORDERIDS&SORTBY=$SORTBY" name="main" frameborder="0" border="0"></frame>
	<frame src="footer.pl?CMD=$CMD" name="footer" frameborder="0" border="0" nowrap noresize scrolling="no"></frame>
</frameset>
</html>
~;
