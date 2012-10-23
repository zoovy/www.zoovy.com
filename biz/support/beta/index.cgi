#!/usr/bin/perl

use lib "/httpd/modules";
require ZTOOLKIT;
require GTOOLS;
require ZOOVY;
require CGI;

my @MSGS = ();
my $path = &ZOOVY::resolve_userpath('becky').'/IMAGES';

my $q = CGI->new();
my $VERB = uc($q->param('VERB'));



if ($VERB eq 'DOWNLOAD') {
	my $file = $q->param('file');
	$file =~ s/[\.]+/./gs;	# make sure they can't pass .
	$file =~ s/[^\w\.]//gs;
	$file = "$path/$file";
	if (! -f $file) {
		push @MSGS, "ERROR|File was not found";
		}
	elsif ($file =~ /(cab|CAB)$/) {
		print "Content-type: application/x-cab-compressed\n\n";
		open F, "<$file";
		while (<F>) { print $_; }
		close F;
		}	
	elsif ($file =~ /(msi|MSI)$/) {
		print "Content-type: application/x-ole-storage\n\n";
		open F, "<$file";
		while (<F>) { print $_; }
		close F;
		}	
	else {
		push @MSGS, "ERROR|Unknown file type";
		}

	if (scalar(@MSGS)>0) {
		$VERB = '';
		}
	}


if ($VERB eq '') {

	opendir($D,$path);
	$c ='';
	%sizehash = ();
	%ctimehash = ();
	while ( $file = readdir($D) ) {
		next if ($file !~ /\.(msi|cab|exe)$/i) ; 
	
		my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
	                      $atime,$mtime,$ctime,$blksize,$blocks)
	                          = stat("$path/$file");
	
		$ctimehash{$file} = $ctime;
		$sizehash{$file} = $size;
	
		}
	closedir($D);
	
	
	$GTOOLS::TAG{'<!-- SERVER -->'} = &ZOOVY::servername();
	
	foreach my $file (&ZTOOLKIT::value_sort(\%ctimehash,'numerically')) {
	
		$size = $sizehash{$file};
		$ctime = $ctimehash{$file};
	
		$release = '';
		$MAJOR = 0;
		$MINOR = 0;
		$url = $file;
		if ($file =~ /^zpm(.*?)$/) {
			($release,$MAJOR,$MINOR) = &release_version($1);
			$type = 'Product Manager';
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
		elsif ($file =~ /^zom(.*?)$/) {
			($release,$MAJOR,$MINOR) = &release_version($1);
			$type = 'Order Manager (6 series)';
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
		elsif ($file =~ /^zwm\_(.*?)$/) {
			($release,$MAJOR,$MINOR) = &release_version($1);
			$type = 'Warehouse Manager (6 series)';
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
		elsif ($file =~ /^zsm\_(.*?)$/) {
			($release,$MAJOR,$MINOR) = &release_version($1);
			$type = 'Enterprise Sync Manager (6 series)';
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
		elsif ($file =~ /^ZIDsetup\-v(.*?)\.(msi|exe)$/) {
			($MAJOR,$MINOR) = split(/\./,$1);
			$type = 'Integrated Desktop ';
			$type .= " v.$MAJOR.$MINOR";
			if (($MINOR % 2)==0) { $type .= 'BETA'; }
			if (($MINOR % 2)==1) { $type .= 'RELEASE CANDIDATE'; }
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
		elsif ($file =~ /\.(cab|CAB)$/) {
			$type = 'Mobile ';
			if (($MINOR % 2)==0) { $type .= 'BETA'; }
			if (($MINOR % 2)==1) { $type .= 'RELEASE CANDIDATE'; }
			$url = "http://www.zoovy.com/biz/support/beta/index.cgi/$file?VERB=DOWNLOAD&file=$file";
			}
		elsif ($file eq 'NETCFSetupv35.msi') {
			$type = "Microsoft.Net compact framework v3.5";
			$url = "http://www.zoovy.com/biz/support/beta/index.cgi/$file?VERB=DOWNLOAD&file=$file";
			}
		else {
			$type = 'Unknown';
			$url = "http://www.zoovy.com/biz/downloads/record.cgi?CODE=$file&URL=".CGI->escape('http://static.zoovy.com/merchant/becky/'.$file)."&MAJOR=$MAJOR&MINOR=$MINOR";
			}
	
		$c .= "<tr><td><a href=\"$url\">$file</a></td><td><b>$type $release</b></td><td>".$size." bytes</td><td>".&ZTOOLKIT::pretty_date($ctime,1)."</td></tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td>No Early Access releases currently available</td></tr>";
		}
	
	
	$GTOOLS::TAG{'<!-- FILES -->'} = $c;
	
	&GTOOLS::output(file=>'index.shtml',header=>1,msgs=>\@MSGS);
	}

sub release_version {
	my ($type) = @_;
	$release = '';
	$major=0;
	$minor=0;
		if ($type =~ /v([\d]+)rc([\d]+)/) {
			$release = 'version '.sprintf("%.2f",$1/100).' release candidate '.$2;
			($major,$minor) = split(/\./,sprintf("%.2f",$1/100));
			}
		elsif ($type =~ /v([\d]+)b([\d]+)/) {
			$release = 'version '.sprintf("%.2f",$1/100).' beta '.$2;
			($major,$minor) = split(/\./,sprintf("%.2f",$1/100));
			}
		elsif ($type =~ /v([\d]+)/) {
			$release = $1;
			if (length($release)==3) {
				$release = 'version '.sprintf("%.2f",$release/100);
				}
			elsif (length($release)==4) { 
				$release = 'version '.sprintf("%.3f",$release/1000);
				}
			($major,$minor) = split(/\./,sprintf("%.2f",$1/100));
			}
	return($release,$major,$minor);
}