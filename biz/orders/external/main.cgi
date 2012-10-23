#!/usr/bin/perl -w

use lib "/httpd/modules";
use GTOOLS;
use EXTERNAL;
use ZOOVY;
use CGI;
use ZTOOLKIT;
use strict;
use LUSER;

my $q = new CGI;
my $template_file = '';	


my ($LU) = LUSER->authenticate(flags=>'_O&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $dbh = &DBINFO::db_user_connect($USERNAME);

my $CMD = uc($q->param('XCMD'));
if (!defined($CMD) || ($CMD) eq '') { $CMD = $q->param('CMD'); }
if (!defined($CMD) || ($CMD) eq '') { $CMD = 'WAITING'; }
$GTOOLS::TAG{"<!-- CMD -->"} = $CMD;
my $ORDERBY = uc($q->param('ORDERBY'));
print STDERR $ORDERBY."\n";
if ($ORDERBY eq 'A') { $GTOOLS::TAG{"<!-- ORDERBY -->"} = 'D'; } else { $GTOOLS::TAG{"<!-- ORDERBY -->"} = 'A'; }
my $EXIDS = $q->param('EXIDS');
if (!defined($EXIDS)) { $EXIDS = ''; }

my $pstmt = "select count(*) from EXTERNAL_ITEMS where MID=$MID";
my $sth = $dbh->prepare($pstmt);
$sth->execute();
my ($totalcount) = $sth->fetchrow();
$sth->finish;

my $PAGE = undef;
if ($totalcount<200000) {
	$PAGE = undef;
	$GTOOLS::TAG{'<!-- PAGE -->'} = '';
	} 
else {
	my $c = '';
	$PAGE = $q->param('PAGE');
	if (!defined($PAGE)) { $PAGE = 0; }
	my $begrange = $PAGE * 100;
	my $endrange = $begrange + 100;
	if ($endrange>$totalcount) { $endrange = $totalcount; }
	$c .= "Showing $begrange-$endrange of $totalcount total";
	if ($endrange<$totalcount) { 
		$c .= " [<a href='main.cgi?PAGE=".($PAGE+1)."'>Next</a>] ";
		}
	if ($begrange > 0) {
		$c .= " [<a href='main.cgi?PAGE=".($PAGE-1)."'>Last</a>] ";
		}
	$GTOOLS::TAG{'<!-- BREAKOUT_PAGES -->'} = $c;
	# href="main.cgi?SORTBY=<!-- SORTBY -->&XCMD=<!-- CMD -->&PAGE=<!-- PAGE -->&ORDERBY=<!-- ORDERBY -->">Next</a>]
	}

$template_file = 'main.shtml';

my $SORTBY = $q->param('SORTBY');
if (!defined($SORTBY)) { $SORTBY = 'ID'; }
$GTOOLS::TAG{'<!-- SORTBY -->'} = $SORTBY;


print STDERR "CMD IS: $CMD\n";

if ($CMD eq 'SAVE')
	{
	my $STAGE = $q->param('STAGE');

	if (!defined($EXIDS)) {	
		## in some cases this script will redirect to itself in those cases we need this code, otherwise 
		## body.cgi will combine all the selected orders into a single GET and pass it into the frame	
		foreach my $key ($q->param()) {
			if ($key =~ /^\*ID\-(.*?)$/) {
				my $ID = $1;
				print STDERR "Key is: $ID\n"; 
				my $STATUS = undef;
				if ($STAGE eq 'C') { $STATUS = 'G'; }
				$LU->log('ORDERS.INCOMPLETE',"Set Incomplete $ID to STAGE:$STAGE","INFO");
				&EXTERNAL::update_stage($USERNAME,$ID,$STAGE,$STATUS);
				$EXIDS .= "$ID,";
				}
			}
		}
	else {
		foreach my $key (split(',',$EXIDS)) {
			if ($key ne '') {
				my $STATUS = undef;
				if ($STAGE eq 'C') { $STATUS = 'G'; } 
				$LU->log('ORDERS.INCOMPLETE',"Set Incomplete $key to STAGE:$STAGE","INFO");
				&EXTERNAL::update_stage($USERNAME,$key,$STAGE,$STATUS);
				}
			}	
		}
	

	$CMD = 'WAITING';
	if ($STAGE eq 'P' || $STAGE eq 'C') { $CMD = 'COMPLETED'; }
	}

if ($CMD eq 'SEARCH') {
	my $arref = &EXTERNAL::fetch_external_list($USERNAME,'ID','ID','SEARCH',$q->param('TEXT'));
	my $checked = undef;
	if (scalar(@{$arref})==1) { 
		$checked = 1;
		} else {
		$checked = 0;
		}
	$GTOOLS::TAG{"<!-- CONTENT -->"} = ${&build_list($arref,$checked)};
	}

if ($CMD eq 'COMPLETED')
	{
	$GTOOLS::TAG{'<!-- WHICH -->'} = 'Processed';
	my $arref = &EXTERNAL::fetch_external_list($USERNAME,$SORTBY,$ORDERBY,'HPCN',undef,$PAGE); 
	$GTOOLS::TAG{"<!-- CONTENT -->"} = ${&build_list($arref)};
	}	

if ($CMD eq 'WAITING')
	{ 	
	$GTOOLS::TAG{'<!-- WHICH -->'} = 'Not Yet Processed';
	my $arref = &EXTERNAL::fetch_external_list($USERNAME,$SORTBY,$ORDERBY,'AIVW',undef,$PAGE);
	$GTOOLS::TAG{"<!-- CONTENT -->"} = ${&build_list($arref)};
	}

if ($CMD eq 'ALL')
	{
	$GTOOLS::TAG{'<!-- WHICH -->'} = 'All Incomplete Items';
	my $arref = &EXTERNAL::fetch_external_list($USERNAME,$SORTBY,$ORDERBY,'',undef,$PAGE);
	$GTOOLS::TAG{"<!-- CONTENT -->"} = ${&build_list($arref)};
	}


&GTOOLS::output(title=>'',file=>$template_file,header=>1);

&DBINFO::db_user_close();
exit;


sub build_list
{
	my ($arref,$checkall) = @_;

	if (!defined($checkall)) { $checkall = 0; }
	my $counter = 1;
	my $c = '';

	print STDERR "EXIDS:=> [$EXIDS]\n";
	foreach my  $el (@{$arref}) {
		my $class = undef;
		if ($counter++%2 == 0) { $class='item_on'; } else { $class='item_off'; }
		$c .= "<tr class='$class'>";
		my $id = $el->{'ID'};
		
		$c .= '<td align="center">&nbsp; <a href="edit.cgi?ID='.$el->{'ID'}.'">'.$el->{'ID'}.'</a>';
		if ($el->{'ZOOVY_ORDERID'} ne '') {
			$c .= "<br><a href=\"/biz/orders/view.cgi?ID=$el->{'ZOOVY_ORDERID'}\">".$el->{'ZOOVY_ORDERID'}."</a>";
			}
		$c .= '</td>';

		my $checked = undef;
		if ((index($EXIDS,"$id,")>=0) || $checkall) { $checked = ' checked '; } else { $checked = ''; }	
		$c .= '<td nowrap>&nbsp; <input '.$checked.' type="checkbox" name="*ID-'.$el->{'ID'}.'"> &nbsp;</td>';	

		my $market = '';
		if ($el->{'MKT_LISTINGID'} ne '') { 
			$market = $el->{'MKT_LISTINGID'}; 
			my $url = &EXTERNAL::linkto($el);
			if ($url ne '#') {
				$market = "<a href=\"$url\" target=\"_blank\">".$market.'</a>';
				}
			if ($el->{'MKT_TRANSACTIONID'}>0) {
				$market .= '-'.$el->{'MKT_TRANSACTIONID'};
				}
			if ($el->{'MKT'} eq '') {
				$market = 'none';
				}
			}
		
		$c .= '<td>&nbsp;'.$el->{'MKT'}.$market.'</td>';

		$c .= '<td><b>'.$el->{'SKU'}.'</b>&nbsp; '.$el->{'PROD_NAME'}.'</td>';
		$c .= '<td>$'.sprintf("%.2f",$el->{'PRICE'})." </td>";
		$c .= '<td> &nbsp;'.$el->{'BUYER_EMAIL'}.' ('.$el->{'BUYER_USERID'}.')</td>';
		$c .= '<td>'.&ZTOOLKIT::pretty_time_since($el->{'CREATED_GMT'})."</td>";
		my %infohash = ();
		if ($el->{'STAGE'} ne 'W') {
			$c .= '<td>'.$EXTERNAL::STAGE{$el->{'STAGE'}}.'</td>';
			}
		else {
			$infohash{'UPDATED'} = $infohash{'MODIFIED_GMT'};
			$c .= '<td><font color="red">Warned: </font>'.&ZTOOLKIT::pretty_time_since($el->{'SENTEMAIL_GMT'},time())."</td>";
			
			}
		

		$c .= '</tr>'."\n";
		}

	if ($counter == 0) { $c = "<tr><td colspan='6'><font color='red'>You don't have any incomplete items yet. Try sell some auctions first. (If you want to test then click \"Create New\" below)</font></td></tr>"; }

	return(\$c);
}








