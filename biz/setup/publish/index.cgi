#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
use ZOOVY;
use GT;
use ZWEBSITE;
use DBINFO;

$dbh = &DBINFO::db_zoovy_connect();
my ($USERNAME,$FLAGS) = &ZOOVY::authenticate();

$template_file = 'index.shtml';

%webdb = &ZWEBSITE::fetch_website_db($USERNAME);
$q = new CGI;
$ACTION = $q->param('ACTION');

if ($ACTION eq 'SAVE') {
	$webdb{'wwwpublish_username'} = $q->param('wwwpublish_username');
	$webdb{'wwwpublish_password'} = $q->param('wwwpublish_password');
	$webdb{'wwwpublish_rootdir'} = $q->param('wwwpublish_rootdir');
	$webdb{'wwwpublish_baseurl'} = $q->param('wwwpublish_baseurl');
	$webdb{'wwwpublish_remhost'} = $q->param('wwwpublish_remhost');
	&ZWEBSITE::save_website_db($USERNAME,\%webdb);
	}

if ($ACTION eq 'PUBLISH') {
	@urls = ();
	
	if ($q->param('HOMEPAGE')) {
		push @urls, 'http://'.$USERNAME.'.zoovy.com';
		}

	if ($q->param('CATEGORIES')) {
		require NAVCAT;
		@cats = &NAVCAT::fetch_navcat_fulllist($USERNAME,1);
		foreach $cat (@cats) {
			next if ($cat eq '.');
		   next if (substr($cat,0,1) eq '*');
		   $cat = substr($cat,1);
		   push @urls, "http://$USERNAME.zoovy.com/category/$cat";
   		}
		}


	if ($q->param('PRODUCTS')) {
		@prods = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
		foreach $prod (@prods) {
		   push @urls, "http://$USERNAME.zoovy.com/product/$prod";
   		}
		}

	$qtUSERNAME = $dbh->quote($USERNAME);
	$pstmt .= '';
	foreach $url (@urls) {
		$pstmt = "replace into PUBLISHER_TODO (ID,MERCHANT,CREATED,URL) values(0,$qtUSERNAME,now(),".$dbh->quote($url).")";
		$dbh->do($pstmt);
		print STDERR $pstmt."\n";
		}

	}


if ($ACTION eq 'DELETE') {
	$pstmt = "delete from PUBLISHER_TODO where MERCHANT=".$dbh->quote($USERNAME);
	if ($q->param('ID') ne '') { $pstmt .= " and ID=".$dbh->quote($q->param('ID')); }
	$sth = $dbh->prepare($pstmt);
	$sth->execute();	
	}


$pstmt = "select * from PUBLISHER_TODO where MERCHANT=".$dbh->quote($USERNAME);
$sth = $dbh->prepare($pstmt);
$sth->execute();

if ($sth->rows>0) {
	$c = '<tr><td colspan="2"><font face="arial" size="2"><a href="index.cgi?ACTION=DELETE">[Clear all Unpublished URLs]</a></td></tr>';
	while ( $hashref = $sth->fetchrow_hashref()) {
		$c .= "<tr><td><a href=\"index.cgi?ACTION=DELETE&ID=$hashref->{'ID'}\"><font face='arial' size='1'>[DEL]</a></td><td><font face='arial' size='1'>$hashref->{'URL'}</font></td></tr>\n";
		}
	$GT::TAG{'<!-- PENDING -->'} = $c;
	} 
else {
	$GT::TAG{'<!-- PENDING -->'} = '<tr><td><i><font face="arial">None scheduled.</i></font></td></tr>';	
	}


$GT::TAG{'<!-- wwwpublish_username -->'} = $webdb{'wwwpublish_username'};
$GT::TAG{'<!-- wwwpublish_password -->'} = $webdb{'wwwpublish_password'};
$GT::TAG{'<!-- wwwpublish_rootdir -->'} = $webdb{'wwwpublish_rootdir'};
$GT::TAG{'<!-- wwwpublish_baseurl -->'} = $webdb{'wwwpublish_baseurl'};
$GT::TAG{'<!-- wwwpublish_remhost -->'} = $webdb{'wwwpublish_remhost'};

&DBINFO::db_zoovy_close();

&GT::print_form('',$template_file,1);

