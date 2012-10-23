#!/usr/bin/perl

use lib "/httpd/modules";

use CGI;
use TODO;

$q = new CGI;


my ($USERNAME) = $q->param('USERNAME');

if (($USERNAME eq '') && ($ENV{'REQUEST_URI'} =~ /\/([a-z0-9A-Z]+)\.xml$/)) {
	## /biz/todo/xml.cgi/username.xml
	$USERNAME = $1; 
	}

print "Content-type: text/xml\n\n";

my ($todo) = TODO->new($USERNAME);

$todo->verify();

if (not defined $todo) {	
	print "<ToDo><Error>USERNAME: $USERNAME had undefined todo list.</Error></Todo>";
	}
else {
	print $todo->as_xml();
	}

