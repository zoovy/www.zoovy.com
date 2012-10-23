use lib "/httpd/modules";
use ZAUTH;

my $cgi = new CGI;

my $rows = ZAUTH::delete_session_db($cgi->param('login'));

print "Content-type: text/plain\n\n";
print "Rows deleted: $rows\n";

