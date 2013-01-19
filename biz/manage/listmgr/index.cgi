#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use DBINFO;

require LUSER;
my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my $template_file = 'index.shtml';

my ($udbh) = &DBINFO::db_user_connect($USERNAME);
my $pstmt = "select %s from LISTING_EVENTS where MID=$MID /* $USERNAME */";
my ($count) = $udbh->selectrow_array(sprintf($pstmt,"count(*)"));

if ($count==0) {
	$GTOOLS::TAG{'<!-- STATUS -->'} = "<div><i>Sorry, but you have no listing events to manage. Please create some</i></div>";
	}
elsif ($count>5000) {
	$GTOOLS::TAG{'<!-- STATUS -->'} = "<div><i>Sorry, but you cannot manage more than 5,000 listing events at one time, please use a more specific filter criteria.</i></div>";
	}
else {
	my $sth = $udbh->prepare(sprintf($pstmt,"*"));
	$sth->execute();
	my $c = '';
	while ( my $ref = $sth->fetchrow_hashref() ) {
		$c .= "<tr>";
		$c .= "<td>$ref->{'ID'}</td>";
		$c .= "<td>$ref->{'SKU'}</td>";
		$c .= "<td>$ref->{'TARGET'}</td>";
		$c .= "<td>$ref->{'REQUEST_APP'}:$ref->{'REQUEST_BATCHID'}</td>";
		$c .= "<td>$ref->{'RESULT'}</td>";
		if ($ref->{'RESULT'} =~ /FAIL/) {
			$c .= "<td>$ref->{'RESULT_ERR_SRC'}</td>";
			$c .= "<td>$ref->{'RESULT_ERR_CODE'}:$ref->{'RESULT_ERR_MSG'}</td>";
			}
		elsif ($ref->{'RESULT'} eq 'SUCCESS-WARNING') {
			$c .= "<td>$ref->{'RESULT_ERR_SRC'}</td>";
			$c .= "<td>$ref->{'RESULT_ERR_CODE'}:$ref->{'RESULT_ERR_MSG'}</td>";
			}
		elsif ($ref->{'RESULT'} eq 'SUCCESS') {
			$c .= "<td colspan=2></td>";
			}
		elsif ($ref->{'RESULT'} eq 'RUNNING') {
			$c .= "<td colspan=2><i>currently being processed.</i></td>";
			}
		elsif ($ref->{'RESULT'} eq 'PENDING') {
			if ($ref->{'LOCK_ID'}>0) {
				$c .= "<td colspan=2><i>being processed by lock:$ref->{'LOCK_ID'} (please check back in a moment)</i></td>";			
				}
			elsif ($ref->{'LAUNCH_GMT'}<$^T) {
				$c .= "<td colspan=2><i>event is ready for processing (please check back in a few moments)</i></td>";
				}
			else {
				$c .= sprintf("<td colspan=2><i>Waiting till %s</i></td>",&ZTOOLKIT::pretty_date($ref->{'LAUNCH_GMT'},1));
				}
			}
		$c .= "</tr>";
		}	
	$sth->finish();
	$GTOOLS::TAG{'<!-- ROWS -->'} = $c;
	}

&DBINFO::db_user_close();

&GTOOLS::output(file=>$template_file,header=>1);