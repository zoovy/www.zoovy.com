#!/usr/bin/perl

use lib "/httpd/modules";

use CGI;

$/ = undef;
my $xml = <STDIN>;
$/ = "\n";



my $METHOD = $ENV{'REQUEST_METHOD'};


if ($METHOD eq 'OPTIONS') {
	print "DAV: 1\n";
	print qq~Content-type: text/xml; charset="utf8"\n\n~;
	}
elsif ($METHOD eq 'PROPFIND') {

	# <?xml version="1.0" encoding="utf-8" ?><propfind xmlns="DAV:"><prop><resourcetype/><lockdiscovery/></prop></propfind>
	print qq~HTTP/1.1 207 Multi-Status\n~;
	print qq~Content-type: text/xml; charset="utf8"\n\n~;
	## <?xml version="1.0" encoding="utf-8" ?><propfind xmlns="DAV:"><prop><resourcetype/><lockdiscovery/></prop></propfind>
#	print qq~<?xml version="1.0" encoding="utf-8" ?><D:propfind xmlns:D="DAV:" xmlns:E="http://www.foo.bar/standards/props/"></D:propfind>~;
	print qq~<?xml version="1.0" encoding="utf-8" ?>
<multistatus xmlns="DAV:">
     <response>
          <href>http://www.zoovy.com/webapi/jt</href>
          <propstat>
               <prop>
						<lockdiscovery/>
						<resourcetype/>
					</prop>
               <status>HTTP/1.1 200 OK</status>
          </propstat>
     </response>
</multistatus>~;


	}

use Data::Dumper;
print STDERR Dumper(\%ENV,$xml);
