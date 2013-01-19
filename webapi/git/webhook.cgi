#!/usr/bin/perl


use strict;
print "Content: text/plain\n\n";

use Data::Dumper;
use CGI;
use Digest::MD5;
use lib "/httpd/modules";
require DBINFO;


my $q = CGI->new();
#my $payload = '{"pusher":{"name":"none"},"repository":{"name":"linktest","created_at":"2012-10-06T16:11:58-07:00","size":0,"has_wiki":true,"private":false,"watchers":0,"url":"https://github.com/brianhorakh/linktest","fork":false,"id":6107642,"pushed_at":"2012-10-06T16:11:58-07:00","open_issues":0,"has_downloads":true,"has_issues":true,"description":"linktest","stargazers":0,"forks":0,"owner":{"name":"brianhorakh","email":"brianh@zoovy.com"}},"forced":false,"after":"29ebef452b38b1bda426daa722381d57566dcd4e","head_commit":{"added":["README.md"],"modified":[],"timestamp":"2012-10-06T16:11:58-07:00","author":{"name":"brianhorakh","username":"brianhorakh","email":"brianh@zoovy.com"},"removed":[],"url":"https://github.com/brianhorakh/linktest/commit/29ebef452b38b1bda426daa722381d57566dcd4e","id":"29ebef452b38b1bda426daa722381d57566dcd4e","distinct":true,"message":"Initial commit","committer":{"name":"brianhorakh","username":"brianhorakh","email":"brianh@zoovy.com"}},"deleted":false,"ref":"refs/heads/master","commits":[],"before":"29ebef452b38b1bda426daa722381d57566dcd4e","compare":"https://github.com/brianhorakh/linktest/compare/29ebef452b38...29ebef452b38","created":false}';
#my $payload = '{"pusher":{"name":"brianhorakh","email":"brianh@zoovy.com"},"repository":{"name":"linktest","created_at":"2012-10-06T16:11:58-07:00","size":128,"has_wiki":true,"private":false,"watchers":0,"url":"https://github.com/brianhorakh/linktest","fork":false,"id":6107642,"pushed_at":"2012-10-06T17:04:37-07:00","open_issues":0,"has_downloads":true,"has_issues":true,"description":"linktest","stargazers":0,"forks":0,"owner":{"name":"brianhorakh","email":"brianh@zoovy.com"}},"forced":false,"after":"f43ce1b5c2a42a6e2966d41079c8098ef9ac669e","head_commit":{"added":["index.html"],"modified":[],"timestamp":"2012-10-06T17:04:19-07:00","author":{"name":"Brian Horakh","username":"brianhorakh","email":"brianh@zoovy.com"},"removed":[],"url":"https://github.com/brianhorakh/linktest/commit/f43ce1b5c2a42a6e2966d41079c8098ef9ac669e","id":"f43ce1b5c2a42a6e2966d41079c8098ef9ac669e","distinct":true,"message":"commit1","committer":{"name":"Brian Horakh","username":"brianhorakh","email":"brianh@zoovy.com"}},"deleted":false,"ref":"refs/heads/master","commits":[{"added":["index.html"],"modified":[],"timestamp":"2012-10-06T17:04:19-07:00","author":{"name":"Brian Horakh","username":"brianhorakh","email":"brianh@zoovy.com"},"removed":[],"url":"https://github.com/brianhorakh/linktest/commit/f43ce1b5c2a42a6e2966d41079c8098ef9ac669e","id":"f43ce1b5c2a42a6e2966d41079c8098ef9ac669e","distinct":true,"message":"commit1","committer":{"name":"Brian Horakh","username":"brianhorakh","email":"brianh@zoovy.com"}}],"before":"29ebef452b38b1bda426daa722381d57566dcd4e","compare":"https://github.com/brianhorakh/linktest/compare/29ebef452b38...f43ce1b5c2a4","created":false}';
use JSON::XS;

my $ERROR = undef;
my ($V,$USERNAME,$PROJECT,$KEY) = (); # ('erich','7C62B56A-101C-11E2-9284-F4273A9C');
if ($ENV{'REQUEST_URI'} =~ /\/webapi\/git\/webhook\.cgi\/v=([\d]+)\/u\=([a-zA-Z0-9\-]+)\/p=([a-zA-z0-9\-]+)\/k=([0-9A-Fa-f]+)$/) {
	($V,$USERNAME,$PROJECT,$KEY) = ($1,$2,$3,$4);
	}
else {
	$ERROR = 'INVALID WEBHOOK URL FORMAT';
	}

print STDERR "V:$V USERNAME:$USERNAME PROJECT:$PROJECT KEY:$KEY\n";

#my $var = JSON::XS->new()->decode($payload);
#use Data::Dumper;
#print Dumper($var);

if (defined $ERROR) {
	}
elsif ($USERNAME eq '') {
	$ERROR = 'USERNAME NOT SET';
	}
elsif ($PROJECT eq '') {
	$ERROR = 'PROJECT NOT SET';
	}
elsif ($KEY eq '') {
	$ERROR = 'SECURITY KEY NOT';
	}
else {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my ($MID) = &ZOOVY::resolve_mid($USERNAME);
	my $pstmt = "select ID,SECRET from PROJECTS where MID=$MID and UUID=".$udbh->quote($PROJECT);
	my ($ID,$SECRET) = $udbh->selectrow_array($pstmt);
	if (not defined $ID) { 
		$ERROR = "COULD NOT FIND PROJECT "; 
		}
	else {
		my ($realkey) = Digest::MD5::md5_hex($SECRET.$PROJECT);	
		if ($realkey ne $KEY) { $ERROR = "SECURITY KEY IN CALLBACK URL IS INVALID"; }
		}

	if (not $ERROR) {
		my $userpath = &ZOOVY::resolve_userpath($USERNAME);
		# print Dumper($ID,$SECRET);
	
		if (-d "$userpath/PROJECTS/$PROJECT") {
			my $CMD = "cd $userpath/PROJECTS/$PROJECT; /usr/local/bin/git --git-dir=$userpath/PROJECTS/$PROJECT/.git pull";
			print STDERR "$CMD\n";
			system("$CMD >> /dev/null");

			my ($memd) = &ZOOVY::getMemd($USERNAME);
			if (defined $memd) {
				## no timestamp in memcache, so we load one, and we set 
				my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat("$userpath/PROJECTS/$PROJECT");
				$memd->set("$USERNAME.$PROJECT",$mtime);
				}
			}
	
		open F, ">/tmp/git.$USERNAME";
		print F Dumper(\%ENV,$q);
		close F;
		}

	

	&DBINFO::db_user_close();
	}

if ($ERROR) {
	print "ERROR:$ERROR\n\n";
	}
else {
	print "HAPPY\n\n";
	}


__DATA__


#{"pusher":{"name":"none"},"repository":{"name":"linktest","created_at":"2012-10-06T16:11:58-07:00","size":0,"has_wiki":true,"private":false,"watchers":0,"url":"https://github.com/brianhorakh/linktest","fork":false,"id":6107642,"pushed_at":"2012-10-06T16:11:58-07:00","open_issues":0,"has_downloads":true,"has_issues":true,"description":"linktest","stargazers":0,"forks":0,"owner":{"name":"brianhorakh","email":"brianh@zoovy.com"}},"forced":false,"after":"29ebef452b38b1bda426daa722381d57566dcd4e","head_commit":{"added":["README.md"],"modified":[],"timestamp":"2012-10-06T16:11:58-07:00","author":{"name":"brianhorakh","username":"brianhorakh","email":"brianh@zoovy.com"},"removed":[],"url":"https://github.com/brianhorakh/linktest/commit/29ebef452b38b1bda426daa722381d57566dcd4e","id":"29ebef452b38b1bda426daa722381d57566dcd4e","distinct":true,"message":"Initial commit","committer":{"name":"brianhorakh","username":"brianhorakh","email":"brianh@zoovy.com"}},"deleted":false,"ref":"refs/heads/master","commits":[],"before":"29ebef452b38b1bda426daa722381d57566dcd4e","compare":"https://github.com/brianhorakh/linktest/compare/29ebef452b38...29ebef452b38","created":false}



