#!/usr/bin/perl

use strict;
print "Content-type: text/html\n\n";

open F, "</proc/sys/kernel/hostname"; $/ = undef; my ($server) = <F>; close F;

print "<body>\n";
print "<b>Server: $server</b><hr>";
opendir my $D, "/httpd/htdocs/pdf";

my %DATE_FILES = ();
my %ACTUAL_FILES = ();
while ( my $file = readdir($D) ) {
	next if (substr($file,0,1) eq '.');
	next if ($file !~ /^20/);

	## ignore files that start with an x.
	if ($file =~ /^([\d]+)[_\-](.*)\.pdf$/) {
		my ($x,$y) = ($1,$2);
		$y =~ s/\-web$//;
#		print "<li> $file  - - - - $x - - - - - $y<br>\n";
		if (not defined $DATE_FILES{$y}) { $DATE_FILES{$y} = 0; }
		if ($DATE_FILES{$y}<$x) { 
			$DATE_FILES{$y} = $x;
			$ACTUAL_FILES{$y} = $file;
			}
		}
	else {
		print "<li> SKIP: $file<br>\n";
		}
	
	}
closedir $D;

print "<table>";
foreach my $symfile (sort keys %DATE_FILES) {
	my $date = $DATE_FILES{$symfile};
	my $origfile = $ACTUAL_FILES{$symfile};
	if (-z $origfile) {
		print "<!-- zero bytes: $symfile -->";
		unlink("$symfile.pdf");
		}
	else {
		print "<tr><td>$date</td><td><a href='$symfile.pdf'>$symfile.pdf</a></td><td>$origfile</td></tr>\n";
		symlink($origfile,"$symfile.pdf");
		chmod 0666, "$symfile";
		}
	}
print "</table>";
print "</body>";