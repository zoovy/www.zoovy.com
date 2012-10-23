#!/usr/bin/perl

use lib "/httpd/modules";
use Data::Dumper;
require GTOOLS;
require LUSER;
require ZOOVY;
require DBINFO;
require CUSTOMER::BATCH;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my ($CPRT) = &CUSTOMER::remap_customer_prt($USERNAME,$PRT);

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'VERB'};


if ($VERB eq 'ENROLL-SAVE') {
	my ($EMAIL) = $ZOOVY::cgiv->{'EMAIL'};
	my ($c) = CUSTOMER->new($USERNAME,EMAIL=>$EMAIL,PRT=>$CPRT,CREATE=>3,INIT=>0x1);
	$c->set_attrib('INFO.IS_AFFILIATE',int($ZOOVY::cgiv->{'PACKAGE'}));
	$c->save();
	$VERB = 'ENROLL';
	}

if ($VERB eq 'ENROLL') {
	my $c = '';
	my $pstmt = "select ID,OFFER_TITLE from AFFILIATE_PACKAGES where MID=$MID /* $USERNAME */ and PRT=$CPRT order by ID desc";
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($ID,$TITLE) = $sth->fetchrow() ) {
		$c .= "<option value=\"$ID\">$TITLE</option>";
		}
	$sth->finish();
	$GTOOLS::TAG{'<!-- PACKAGES -->'} = $c;
	$template_file = 'enroll.shtml';
	}


if ($VERB eq 'PACKAGE-NUKE') {
	my $pstmt = "delete from AFFILIATE_PACKAGES where MID=$MID /* $USERNAME */ and PRT=$CPRT and ID=".int($ZOOVY::cgiv->{'ID'});
	print STDERR $pstmt."\n";
	$udbh->do($pstmt);
	$VERB = '';
	}

if ($VERB eq 'PACKAGE-SAVE') {
	&DBINFO::insert($udbh,'AFFILIATE_PACKAGES',{
		MID=>$MID,USERNAME=>$USERNAME,PRT=>$CPRT,
		OFFER_TITLE=>$ZOOVY::cgiv->{'TITLE'},
		ORDER_BOUNTY_FEE=>sprintf("%.2f",$ZOOVY::cgiv->{'ORDER_BOUNTY_FEE'}),
		ORDER_BOUNTY_PCT=>sprintf("%.2f",$ZOOVY::cgiv->{'ORDER_BOUNTY_PCT'}),
		});
	$VERB = '';
	}

if ($VERB eq 'PACKAGE-NEW') {
	$template_file = 'new.shtml';
	}

if ($VERB eq '') {
	$template_file = 'index.shtml';

	my (%cids) = CUSTOMER::BATCH::list_customers($USERNAME,$CPRT,IS_AFFILIATE=>1,HASHKEY=>'CID');
	print STDERR Dumper(\%cids);
	my %PROGRAM_COUNTS = ();
	foreach my $cid (keys %cids) {
		$PROGRAM_COUNTS{ $cids{$cid}->{'IS_AFFILIATE'} }++;
		}

	my $c = '';
	my $pstmt = "select * from AFFILIATE_PACKAGES where MID=$MID /* $USERNAME */ and PRT=$CPRT";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		$c .= "<tr>";
		$c .= "<td>";

		if ($PROGRAM_COUNTS{ $hashref->{'ID'} }==0) {
			## only show delete if no participants.
			$c .= qq~<a href="index.cgi?VERB=PACKAGE-NUKE&ID=$hashref->{'ID'}">[Delete]</a>~;
			}

		$c .= "</td>";
		$c .= "<td>".&ZOOVY::incode($hashref->{'OFFER_TITLE'})."</td>";
		$c .= "<td>\$$hashref->{'ORDER_BOUNTY_FEE'}</td>";
		$c .= "<td>$hashref->{'ORDER_BOUNTY_PCT'}%</td>";
		$c .= "<td>".int($PROGRAM_COUNTS{ $hashref->{'ID'} })."</td>";
		$c .= "</tr>";
		}
	$sth->finish();
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No affiliate packages have been defined. Please add one</td></tr>";
		}
	else {
		$c = qq~
<tr class='zoovysub1header'>
	<td></td>
	<td>Title</td>
	<td>Order-\$</td>
	<td>Order-\%</td>
	<td># Enrolled</td>
</tr>
$c
~;
		}
	$GTOOLS::TAG{'<!-- PACKAGES -->'} = $c;


	$c = '';
	foreach my $cid (keys %cids) {
		$c .= "<tr>";
		$c .= "<td>".$cids{$cid}->{'EMAIL'}."</td>";
		$c .= "<td>".$cids{$cid}->{'IS_AFFILIATE'}."</td>";
		$c .= "</tr>";
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=5><i>No affiliates enrolled at this time.</td></tr>";
		}
	else {
		$c = qq~
<tr class="zoovysub1header">
	<td>Customer Email</td>
	<td>Program</td>
</tr>
</tr>
$c
~;
		}
	$GTOOLS::TAG{'<!-- AFFILIATES -->'} = $c;

	}

my @TABS = ();
push @TABS, { name=>'Current Programs', link=>"index.cgi", selected=>(($VERB eq '')?1:0) };
push @TABS, { name=>'New Program', link=>"index.cgi?VERB=PACKAGE-NEW", selected=>(($VERB eq 'PACKAGE-NEW')?1:0) };
push @TABS, { name=>'Enroll Affiliates', link=>"index.cgi?VERB=ENROLL", selected=>(($VERB eq 'ENROLL')?1:0) };

&DBINFO::db_user_close();
&GTOOLS::output(header=>1,file=>$template_file,tabs=>\@TABS);