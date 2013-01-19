#!/usr/bin/perl

use lib "/httpd/modules";
use IMGLIB;
use GT;
use CGI;
use ZOOVY;

$q = new CGI;
($USERNAME) = &ZOOVY::authenticate();
$image = $q->param('IMAGE');
$width = $q->param('WIDTH');
$height = $q->param('HEIGHT');
if (defined($q->param('ZOOM'))) { $zoom = 1; } else { $zoom = 0; }

my $src = &GT::imageurl($USERNAME,$image,$height,$width);
my $zoomsrc = &GT::imageurl($USERNAME,$image,0,0);
if ($width ne '') { $width = "width=\"$width\" "; } else { $width = ''; }
if ($height ne '') { $height = "height=\"$height\" "; } else { $height = ''; }

print "Content-type: text/html\n\n";
print "<html>";
print "<head><link REL='STYLESHEET' TYPE='text/css' HREF='/standard.css'></head><body>";
print "HTML CODE (copy and paste this into any HTML document):<br>";
print "<form><textarea cols='100' rows='3'>";
# if ($zoom) { print "<a href=\"http://$USERNAME.zoovy.com/view.cgis?IMG=$image\" target=\"_blank\" border=\"0\">"; }

if ($zoom) { $c .= "&lt;a href=\"$zoomsrc\" target=\"_blank\" border=\"0\"&gt;\n"; }
$c .= "&lt;img src=\"$src\" ${width}${height}border=\"0\"&gt;\n";
if ($zoom) { $c .= "&lt;/a&gt;\n"; }
print $c;

print "</textarea>\n";
print "<br><br>";
print "<br><b>Preview:</b><br>";
print &ZOOVY::dcode($c);
print "<br>";
print "Note: You can easily adjust the Width and Height by altering the W and H parameters in the image URL.<br>\n";
print "<hr><center><a href='properties.cgi?COLLECTION=$image'><img src='/images/bizbuttons/exit.gif' border='0'></a></center><br>";

print "</body>";
print "</html>\n";

