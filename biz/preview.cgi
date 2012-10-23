#!/usr/bin/perl -w

use lib "/httpd/modules";
use CGI;
use ZOOVY;

my ($USERNAME,$FLAGS) = &ZOOVY::authenticate("/biz",1);
if (not defined $FLAGS) { $FLAGS = ''; }

my $q = new CGI;

my $url = $q->param('url');
if (($url eq '') || (!defined($url))) {
	$url = "http://".$USERNAME.".zoovy.com";
	}

# try to figure out if we passed a theme/layout
#my $theme = '';  if ($url =~ m/theme=(\w+)/)  { $theme = $1; }
#my $layout = ''; if ($url =~ m/layout=(\w+)/) { $layout = $1; }
#my $sendto = $url.(($url =~ m/\?/)?'&':'?').$USERNAME.'-nocache=1';
if ($url !~ /^http\:\/\//) {
	$url = "http://$url";
	}
my $sendto = $url.(($url =~ m/\?/)?'&':'?').$USERNAME.'-nocache=1&ts='.time();
my $cgiurl = CGI::escape($url);
my $cleanurl = $url; $cleanurl =~ s/\?.*$//;
my $header = $q->param('header'); if (not defined $header) { $header = 0; }
my $t = time();

print "Content-type: text/html\n";
print "Pragma: no-cache\n"; # HTTP 1.0 non-caching specification
print "Cache-Control: no-cache\n"; # HTTP 1.1 non-caching specification
print "Expires: 0\n\n"; # HTTP 1.0 way of saying "expire now"

if ($header)
{

print <<"EOF";
<html>
<head><title>Previewing </title></head>
<body bgcolor="#CCCC99" marginwidth="3" marginheight="3" topmargin="3" leftmargin="3">
<table width="100%">
	<tr>
		<td align="left">
			<font face="arial, helvetica" size="2" color="black">
			Previewing: <b><a href="$sendto" target="main"><font color="#000066">$cleanurl</font></a></b><br>
			</font>
		</td>
		<td align="right">
			<font face="arial, helvetica" size="2" color="black">
			<a href="javascript:parent.close();"><font color="#000066">Exit</font></a> | <a href="javascript:openWindow('preview-help.shtml');"><font color="#000066">Help</font></a>
			</font>
		</td>
	</tr>
</table>
</body>
</html>
EOF
	
}
else
{

print <<"EOF";
<html>
	<frameset rows="40,*" frameborder="0" framespacing="2" border="2">
		<frame src="/biz/preview.cgi?header=1&url=$cgiurl" name="title" frameborder="0" border="0" noresize scrolling="no">
		<frame src="$sendto" name="main" frameborder="0" border="0" scrolling="yes">
		<noframes>You need to support Frames</noframes>
	</frameset>
</html>
EOF

}

# Stuff past here isn't used any more...  It will go away when I have preview.merchant.zoovy.com set up properly.  -AK
# The END line tells perl to stop processing the file
__END__
<body onLoad="bakecookies();" onUnload="scrubcookies();"  bgcolor="CCCC99" marginwidth="3" marginheight="3" topmargin="3" leftmargin="3">
<script Lanugage="Javascript"">
<!--//
function openWindow(url) {
	popupWin = window.open(url, 'popup','status=yes,resizable=yes,width=638,height=450,menubar=yes,scrollbars=yes');
	popupWin.focus(true);
}
	
function setCookie(cookiename, cookievalue) {
	var argv = setCookie.arguments;
	var argc = setCookie.arguments.length;
	var expires = (argc > 2) ? argv[2] : null;
	var path =    (argc > 3) ? argv[3] : null;
	var domain =  (argc > 4) ? argv[4] : null;
	var secure =  (argc > 5) ? argv[5] : false;
	document.cookie = cookiename + "=" + escape(cookievalue) +
	((expires == null) ? "" 	    : ("; expires=" + expires.toGMTString())) +
	((path    == null) ? ""	    : ("; path="    + path                 )) +
	((domain  == null) ? "" 	    : ("; domain="  + domain               )) +
	((secure  == true) ? "; secure" : "");
	return;
}

function bakecookies() {
	setCookie('theme','$theme',null,'/','.zoovy.com');
	setCookie('layout','$layout',null,'/','.zoovy.com');
	window.focus();
}

function scrubcookies() {
	setCookie('theme','',null,'/','.zoovy.com');
	setCookie('layout','',null,'/','.zoovy.com');
}
//-->
</script>

