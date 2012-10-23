#!/usr/bin/perl

use POSIX qw (strftime);
use lib "/httpd/modules";
use DBINFO;
use ZOOVY;

open F, ">/httpd/htdocs/sitemap.xml";

print F q~<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"	xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
~;


## homepage.
print F q~
<url><loc>http://www.zoovy.com/index.html</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
~;

## woot pdfs!
print F "<!-- pdfs -->\n";
opendir $D, "/httpd/htdocs/pdfs";
while ( my $file = readdir($D) ) {
	next if (substr($file,0,1) eq '.');
	next unless ($file =~ /pdf$/);
	next unless (-l "/httpd/htdocs/pdfs/$file");
	print F qq~<url><loc>http://www.zoovy.com/pdfs/$file</loc></url>\n~;
	}
closedir $D;

## all pages
print F "<!-- all pages -->\n";
use HTML::Mason::Interp;
my $outbuf;
my $i = HTML::Mason::Interp->new(data_dir=>'/tmp',comp_root=>'/httpd/htdocs/',out_method => \$outbuf);
$i->exec('/includes/sitemap.html',xml=>1);
print F $outbuf;

## press releases
print F "<!-- press releases -->\n";
$outbuf = '';
$i->exec('/includes/pressreleases.html',xml=>1);
print F $outbuf;

## tasty webdoc pages... yum.
print F "<!-- webdoc -->\n";
my $dbh = &DBINFO::db_zoovy_connect();
$pstmt = "select ID,AREA,FILE,MODIFIED_GMT from WEBDOC_FILES";
my $sth = $dbh->prepare($pstmt);
$sth->execute();
while ( my ($ID,$AREA,$FILE,$MODIFIED_GMT) = $sth->fetchrow() ) {
	next if ($FILE =~ /^myzoovy/);
	next if ($FILE =~ /^hide/);
	$FILE =~ s/[\/_\s]/+/g;

	my ($modified) = POSIX::strftime("%Y-%m-%d",localtime($MODIFIED_GMT));
	my $link = &ZOOVY::incode("http://www.zoovy.com/webdoc/?VERB=DOC&DOCID=$ID&KEYWORDS=$FILE");
	print F qq~<url><loc>$link</loc><lastmod>$modified</lastmod><priority>0.7</priority></url>~;
	}
$sth->finish();
&DBINFO::db_zoovy_close();

print F q~
</urlset>
~;
