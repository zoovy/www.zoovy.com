#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use GTOOLS;
use DBINFO;
use ZOOVY;
use ZTOOLKIT;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_O&2|_M&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
my $VERB = $ZOOVY::cgiv->{'VERB'};

my $dbh = &DBINFO::db_zoovy_connect();

my $template_file = 'index.shtml';

#+-------------+------------------+------+-----+---------+----------------+
#| Field       | Type             | Null | Key | Default | Extra          |
#+-------------+------------------+------+-----+---------+----------------+
#| ID          | int(11)          |      | PRI | NULL    | auto_increment |
#| PAYPAL_ID   | varchar(20)      |      |     |         |                |
#| USERNAME    | varchar(20)      |      |     |         |                |
#| MID         | int(11)          |      | MUL | 0       |                |
#| CREATED     | int(11)          |      |     | 0       |                |
#| PROCESSED   | int(11)          |      | MUL | 0       |                |
#| LOCKED      | int(11)          |      |     | 0       |                |
#| LOCK_ID     | varchar(20)      |      |     |         |                |
#| ITEM_NUMBER | varchar(127)     |      |     |         |                |
#| INVOICE     | varchar(127)     |      |     |         |                |
#| DATA        | mediumtext       |      |     |         |                |
#| SRC         | varchar(10)      |      |     |         |                |
#| ATTEMPTS    | tinyint(4)       |      |     | 0       |                |
#| NEXTATTEMPT | int(10) unsigned |      |     | 0       |                |
#+-------------+------------------+------+-----+---------+----------------+
#14 rows in set (0.02 sec)


##
##
##
if ($VERB eq 'RESEARCH') {
	my $TXN = $ZOOVY::cgiv->{'PAYPALTXN'};	
	
	my $pstmt = "select * from PAYPAL_QUEUE where MID=$MID and PAYPAL_ID=".$dbh->quote($TXN);
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my ($inforef) = $sth->fetchrow_hashref();
	$sth->finish();

	$GTOOLS::TAG{'<!-- TXN -->'} = $TXN;
	use Data::Dumper;
	$GTOOLS::TAG{'<!-- DUMP -->'} = '<pre>'.&ZOOVY::incode(Dumper($inforef)).'</pre>';

	my $c = '';
	$pstmt = "select ID,CREATED,DESCRIPTION from PAYPAL_LOG where PAYPAL_ID=".$dbh->quote($TXN)." and USERNAME=".$dbh->quote($USERNAME)." order by ID";
	print STDERR $pstmt."\n";
	$sth = $dbh->prepare($pstmt);
	$sth->execute();
	while ( my ($ID,$CREATED,$DESC) = $sth->fetchrow() ) {
		$c .= "<tr><td>$CREATED</td><td>$DESC</td></tr>";
		}
	$sth->finish();
	if ($c eq '') { $c = "<tr><td><i>No events recorded or has not been processed.</i></td></tr>"; }
	$GTOOLS::TAG{'<!-- PROCESS_LOG -->'} = $c;
	
	$template_file = 'research.shtml';
	}


##
##
##
if ($VERB eq '') {

my $pstmt = "select PAYPAL_ID,CREATED,PROCESSED,ITEM_NUMBER,INVOICE,SRC,ATTEMPTS,NEXTATTEMPT from PAYPAL_QUEUE where MID=$MID /* $USERNAME */ order by ID desc limit 0,250";
print STDERR $pstmt."\n";
my $sth = $dbh->prepare($pstmt);
$sth->execute();
my $c = '';
my $r = '';
while ( my ($paypal_id,$created,$processed,$item,$invoice,$src,$attempts,$nextattempt) = $sth->fetchrow() ) {
	$r = ($r eq 'r0')?'r1':'r0';

	$c .= "<tr class='$r'>";
	$c .= "<td valign=top><a href=\"index.cgi?VERB=RESEARCH&PAYPALTNX=$paypal_id\">$paypal_id</a></td>";
	$c .= "<td valign=top>".&ZTOOLKIT::pretty_date($created,1)."</td>";
	if ($processed) {
		$c .= "<td valign=top>Processed: ".&ZTOOLKIT::pretty_date($processed,1);
		if ($invoice ne '') { $c .= " - Invoice: $invoice"; }
		if ($item ne '') { $c .= " - Item: $item"; }
		$c .= "</td>";
		}
	elsif ($nextattempt == 0) {
		$c .= "<td valign=top>Just received.</td>"; 
		}
	else {
		$c .= "<td valign=top>";
		if ($nextattempt>time()) { $c .= " Try again after: ".&ZTOOLKIT::pretty_date($nextattempt,1); } else { $c .= " Processing Imminent! "; }
		if ($attempts) { $c .= "Attempts: ".$attempts; }
		$c .= "</td>";
		}
	}
$sth->finish();
if ($c eq '') { $c .= "<tr><td valign=top>No Paypal Payments have been received.</td></tr>"; }
else {
	$c = qq~
	<tr>
		<td valign=top><b>Paypal Id</b></td>
		<td valign=top><b>Received</b></td>
		<td valign=top><b>Status</b></td>
	</tr>
	~.$c;
	}

$GTOOLS::TAG{'<!-- PAYPAL -->'} = $c;
}

&DBINFO::db_zoovy_close();



&GTOOLS::output('*LU'=>$LU,
   'title'=>'Paypal IPN Report',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'',
   'bc'=>[
      { name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
      { name=>'Paypal IPN Report',link=>'','target'=>'_top', },
      ],
   );

