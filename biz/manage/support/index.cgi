#!/usr/bin/perl

use strict;

use Data::Dumper;
use lib "/httpd/modules";
use GTOOLS;
use BATCHJOB;
use ZTOOLKIT;
use ZOOVY;


my $template_file = 'index.shtml';

require LUSER;
my ($LU) = LUSER->authenticate();
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }
if (index($FLAGS,'BASIC')==-1) { print "Location: /biz\n\n"; exit; }

my @MSGS = ();
use Data::Dumper;
print STDERR Dumper($ZOOVY::cgiv);
my ($VERB) = $ZOOVY::cgiv->{'VERB'};
print STDERR "VERB:'$VERB' xx\n";

$GTOOLS::TAG{'<!-- VERB -->'} = $VERB;
if ($VERB eq 'FUSESYNC') {
	require PLUGIN::FUSEMAIL;
	my $out = PLUGIN::FUSEMAIL::syncuser($USERNAME);
	my $c = '';
	foreach my $line (@{$out}) {
		$c .= "<li> $line\n";
		}
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'output.shtml';
	}


if ($VERB eq 'ADD-FAVORITE') {
	require TOXML::UTIL;
	&TOXML::UTIL::remember($USERNAME,$ZOOVY::cgiv->{'FORMAT'},$ZOOVY::cgiv->{'DOCID'},1);
	$VERB = 'MORE';
	}


if ($VERB eq 'CREATE-UTILITY-BATCH') {
	my ($bj) = BATCHJOB->new($USERNAME,0,
		PRT=>$PRT,
		EXEC=>'UTILITY',
		VARS=>&ZTOOLKIT::buildparams($ZOOVY::cgiv,1),
		'*LU'=>$LU,
		);
	push @MSGS, "SUCCESS|JOBTYPE: $ZOOVY::cgiv->{'APP'} JOBID: ".$bj->id();
	}



if ($VERB eq 'RESET-ORDER-CHANGED') {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);

	my $from = &ZTOOLKIT::mysql_to_unixtime($ZOOVY::cgiv->{'FROMYYYYMMDDHHMMSS'});
	my $till = &ZTOOLKIT::mysql_to_unixtime($ZOOVY::cgiv->{'TILLYYYYMMDDHHMMSS'});
	if ($from == 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>FROM time evaluated to zero</div>";
		}
	elsif ($till == 0) {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>TILL time evaluated to zero</div>";
		}
	else {
		require ORDER::BATCH;
		my @oids = ();
		my ($set) = ORDER::BATCH::report($USERNAME,'CREATED_GMT'=>$from,'CREATEDTILL_GMT'=>$till);
		foreach my $s (@{$set}) { push @oids, $s->{'ORDERID'}; }
		my ($tb) = &DBINFO::resolve_orders_tb($USERNAME);
		my $pstmt = "update $tb set SYNCED_GMT=0 where MID=$MID and ORDERID in ".&DBINFO::makeset($udbh,\@oids);
		print STDERR $pstmt."\n";
		if (not $udbh->do($pstmt)) {
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='error'>SQL ERROR<pre>".join(',',@oids)."</pre></div>";
			}
		else {
			$LU->log("UTILITIES.TECHTOOLS","Reset sync on orders from[$from] to[$till]","WARN");
			$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>SUCCESS ".join(', ',@oids)."</div>";
			}
		}

	&DBINFO::db_user_close();
	}


if ($VERB eq 'SHOW-USER-EVENT-QUEUE') {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);

	my $pstmt = "select count(*) from USER_EVENTS where MID=$MID and PROCESSED_GMT=0";
	my ($user_count) = $udbh->selectrow_array($pstmt);

	$pstmt = "select count(*) from USER_EVENTS where PROCESSED_GMT=0";
	my ($system_count) = $udbh->selectrow_array($pstmt);

	$pstmt = "select ID,CREATED_GMT,PRT,PID,EVENT,ORDERID,ATTEMPTS,PROCESSED_GMT,YAML from USER_EVENTS where 
		MID=$MID 
		and CREATED_GMT>unix_timestamp(date_format(now(),'%Y%m%d000000'))
		and (PROCESSED_GMT<=1 or PROCESSED_GMT>unix_timestamp(date_format(now(),'%Y%m%d000000'))) 
		order by ID;";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $displaycount = 0;
	require YAML::Syck;
	while ( my ($ID,$CREATED,$PRT,$PID,$EVENT,$ORDERID,$ATTEMPTS,$PROCESSED_GMT,$YAML) = $sth->fetchrow() ) {
		my $YREF = YAML::Syck::Load($YAML);
		if (defined $YREF->{'SKU'}) { $PID = $YREF->{'SKU'}; }
		my $data = '';
		foreach my $k (sort keys %{$YREF}) { $data .= " $k=$YREF->{$k} "; }

		if ($ORDERID eq '') { $ORDERID = 'N/A'; }
		if ($PROCESSED_GMT<=1) {
			$c .= "<tr class='rs'>";
			}
		else {
			$c .= "<tr>";
			}
		$c .= "<td>$ID</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($CREATED,1)."</td>";
		$c .= "<td>$PRT</td>";
		$c .= "<td>$PID</td>";
		$c .= "<td>$EVENT</td>";
		$c .= "<td>$ORDERID</td>";
		$c .= "<td>$ATTEMPTS</td>";
		if ($PROCESSED_GMT==0) {
			$c .= "<td>--PENDING--</td>";
			}
		elsif ($PROCESSED_GMT==1) {
			$c .= "<td>ERROR</td>";
			}
		else {
			$c .= "<td>".&ZTOOLKIT::pretty_date($PROCESSED_GMT,3)."</td>";
			}
		$c .= "<td><div class='hint'>$data</div></td>";
		$c .= "</tr>";
		$displaycount++;
		}
	$sth->finish();
	&DBINFO::db_user_close();

	if ($c eq '') {
		$c .= "<tr><td><i>No user events since midnight or pending.</td></tr>";
		}
	else {
		$c = qq~
	<tr>
		<td><b>ID</b></td>
		<td><b>POSTED</b></td>
		<td><b>PRT</b></td>
		<td><b>PID</b></td>
		<td><b>EVENT</b></td>
		<td><b>SRC/ORDERID</b></td>
		<td><b>ATTEMPTS</b></td>
		<td><b>PROCESSED</b></td>
		<td><b>ADDITIONAL DATA</b></td>
	</tr>
	~.$c;
		}

	$c = qq~
	<b>User Total Pending Events: $user_count</b><br>
	<b>Cluster Total Pending Events: $system_count</b><br>
	<hr>
	Next $displaycount events:
	<table>$c</table>
	<br>
	<i>Note: If you don't see an event, it may not have been queued for firing yet - check the inventory finalization table.</i>
	<i>A normal service time of 4 hours is expected, however on busy days this could easily reach 12 hours. Events are considered a low priority
	service and so are shutdown/queued for later when system load is high or running events could impact performance.</i>
	~;

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'output.shtml';
	$VERB = '';
	}


if ($VERB eq 'SESSION-DEBUG') {
	my $c = '';
	
	my $CARTID = $ZOOVY::cgiv->{'session'};
	#use CART; $CARTID = CART::generate_cart_id();

	$c .= "<b>Cart ID: $CARTID</b><br>";
	$c .= "RANDOM PREFIX: ".substr($CARTID,0,6)."<br>"; 
	$CARTID = substr($CARTID,6);
	## time
	my $ts = &ZTOOLKIT::unbase62(substr($CARTID,0,4))*600;
	if ($ts<1306510000) {
		$c .= "TIME: not available<br>";
		}
	elsif ($ts<1306510000+(86400*365)) {
		$c .= "TIME: ".substr($CARTID,0,4)." : $ts : ".&ZTOOLKIT::pretty_date($ts,4)."<br>"; 
		}
	else {
		$c .= "TIME $ts (too old)<br>";
		}
	$CARTID = substr($CARTID,4);
	## ip address
	if (($ts < 1306518289) || ($ts > 1306518289+(86400*365))) {
		$c .= "IP: not available<br>";
		}
	elsif (substr($CARTID,0,1) eq 'X') {
		$c .= "IP: internal - not remote";
		}
	else {
		my $ip = &ZTOOLKIT::int_to_ip(&ZTOOLKIT::unbase62(substr($CARTID,0,6)));
		$c .= "IP: ".substr($CARTID,0,6)." : $ip<br>";
		}
	$CARTID = substr($CARTID,6);
	$c .= "RANDOM SUFFIX: ".$CARTID."<br>";

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'output.shtml';
	}



if ($VERB eq 'SHOW-INVENTORY-EVENT-QUEUE') {
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);

#+-----------+--------------------------+------+-----+---------+----------------+
#| Field     | Type                     | Null | Key | Default | Extra          |
#+-----------+--------------------------+------+-----+---------+----------------+
#| ID        | int(11)                  | NO   | PRI | NULL    | auto_increment |
#| MID       | int(10) unsigned         | NO   |     | 0       |                |
#| USERNAME  | varchar(20)              | YES  | MUL | NULL    |                |
#| LUSER     | varchar(20)              | NO   |     | NULL    |                |
#| TIMESTAMP | datetime                 | YES  |     | NULL    |                |
#| TYPE      | enum('U','I','R','J','') | YES  |     | NULL    |                |
#| PRODUCT   | varchar(20)              | NO   |     | NULL    |                |
#| SKU       | varchar(35)              | NO   |     | NULL    |                |
#| QUANTITY  | int(11)                  | YES  |     | NULL    |                |
#| APPID     | varchar(10)              | NO   |     | NULL    |                |
#| ORDERID   | varchar(16)              | NO   |     | NULL    |                |
#+-----------+--------------------------+------+-----+---------+----------------+
#11 rows in set (0.01 sec)


	my $pstmt = "select count(*) from INVENTORY_UPDATES where MID=$MID /* $USERNAME */";
	my ($count) = $udbh->selectrow_array($pstmt);

	$pstmt = "select LUSER,TIMESTAMP,TYPE,SKU,QUANTITY,APPID,ORDERID from INVENTORY_UPDATES where MID=$MID order by ID desc limit 0,200";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $displaycount = 0;
	while ( my ($LUSER,$WHEN,$TYPE,$SKU,$QTY,$APPID,$ORDERID) = $sth->fetchrow() ) {
		if ($ORDERID eq '') { $ORDERID = 'N/A'; }
		$c .= "<tr>";
		$c .= "<td>LUSER</td>";
		$c .= "<td>WHEN</td>";
		$c .= "<td>TYPE</td>";
		$c .= "<td>SKU</td>";
		$c .= "<td>QTY</td>";
		$c .= "<td>APPID</td>";
		$c .= "<td>ORDERID</td>";
		$c .= "</tr>";
		$displaycount++;
		}
	$sth->finish();
	&DBINFO::db_user_close();

	if ($c eq '') {
		$c .= "<tr><td><i>No inventory finalization events currently pending.</td></tr>";
		}
	else {
		$c = qq~
	<tr>
		<td><b>LUSER</b></td>
		<td><b>WHEN</b></td>
		<td><b>TYPE</b></td>
		<td><b>SKU</b></td>
		<td><b>QTY</b></td>
		<td><b>APPID</b></td>
		<td><b>ORDERID</b></td>
	</tr>
	~.$c;
		}

	$c = qq~
	<b>Total Pending Events: $count</b><br>
	<hr>
	Next $displaycount events:
	<table>$c</table>
	<br>
	<i>Note: If you don't see an event, it may have already fired.</i>
	<i>A normal service time of 4 hours is expected, however on busy days this could easily reach 12 hours. Events are considered a low priority
	service and so are shutdown/queued for later when system load is high or running events could impact performance.</i>
	~;

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'output.shtml';
	$VERB = '';
	}


## Disassociate product from SUPPLIER
## (this doesn't remove product from Zoovy Store)
if ($VERB eq 'DISASSOCIATE') {
	my @prods = ();
	foreach my $var (keys %{$ZOOVY::cgiv}){
		next unless ($var =~ /^SKU_/);
		push @prods, $ZOOVY::cgiv->{$var};
		}

	if (scalar(@prods) > 0) {
		SUPPLIER::disassociate_products($USERNAME, $ZOOVY::cgiv->{'CODE'}, \@prods);
		}

	$VERB = 'PRODUCTS';
	}



if ($VERB eq 'DUMP-ORDER') {
	my ($OID) = $ZOOVY::cgiv->{'ORDERID'};

	#require ORDER;
	#my ($o,$err) = ORDER->new($USERNAME,$OID,new=>0);
	#if (not defined $o) { $o = $err; }
	require CART2;
	my ($CART2) = CART2->new_from_oid($USERNAME,$OID);
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<pre>".&ZOOVY::incode(Dumper($CART2))."</pre>";

	$template_file = 'output.shtml';
	$VERB = '';
	}


if ($VERB eq 'ACCESSLOG') {
	my $FILE = $ZOOVY::cgiv->{'FILE'};
	# $FILE =~ s/[^access\-[\d]//g;
	my ($path) = &ZOOVY::resolve_userpath($USERNAME);
	my $buffer = undef;
	if ($FILE =~ /^[a-z].*?(\.log|\.log\.gz)$/) {
		open F, "<$path/$FILE"; $/ = undef; $buffer = <F>; $/ = "\n"; close F;
		if ($FILE =~ /\.log\.gz$/) {
			require Compress::Zlib;
			$buffer = Compress::Zlib::memGunzip($buffer);
			}
		}
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<pre>FILE: $FILE\n".$buffer."</pre>"; 

	$template_file = 'output.shtml';
	$VERB = '';
	}


if ($VERB eq '') {
	my ($path) = &ZOOVY::resolve_userpath($USERNAME);
	my $D;
	opendir $D, $path;
	my %ACCESS_LOGS = ();
	while ( my $file = readdir($D) ) {
		next if (substr($file,0,1) eq '.');
		if ($file =~ /^(.*?[\d]+)\.log$/) {
			$ACCESS_LOGS{$1} = [ $1, $file ];
			}
		elsif ($file =~ /^(.*?)(\.log\.gz)$/) {
			$ACCESS_LOGS{$1} = [ "$1 (Compressed)", $file ];
			}
		}
	closedir $D;

	my $c = '';
	foreach my $k (sort keys %ACCESS_LOGS) {
		my ($pretty,$filename) = @{$ACCESS_LOGS{$k}};
		$c .= "<li><a href=\"/biz/manage/support/index.cgi?VERB=ACCESSLOG&FILE=$filename\">$pretty</a>";
		}
	$GTOOLS::TAG{'<!-- ACCESS_LOGS -->'} = $c;

	require ZWEBSITE;
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	if ($gref->{'%tuning'}) {
		my $c = '';
		foreach my $param (keys %{$gref->{'%tuning'}}) {
			$c .= "<li> $param<br>";
			}
		$GTOOLS::TAG{'<!-- TUNING -->'} = $c;
		}
	else {
		$GTOOLS::TAG{'<!-- TUNING -->'} = "<i>No special tuned settings</i>";
		}

	}

if ($VERB eq 'FLEXEDIT-SAVE') {
	require ZWEBSITE;
	require JSON::XS;
	require PRODUCT::FLEXEDIT;

	my $coder = JSON::XS->new->ascii->pretty->allow_nonref;
	my $fref = $coder->decode($ZOOVY::cgiv->{'FLEXEDIT'});

	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	
	#forach my $id (@{$fref}) {
	#	if ($fref->{$id}->{'COPY'}) {
	##		foreach my $attrib (keys %{$fref->{$id}}) {
	#			next if ($attrib eq 'id');
	#			delete $fref->{$id}->{$attrib};
	#			}
	#		}
	#	}

	foreach my $id (sort keys %PRODUCT::FLEXEDIT::fields) {
		if (defined $ZOOVY::cgiv->{$id}) {
			push @{$fref}, { id=>"$id" };
			}
		}

	$gref->{'@flexedit'} = $fref;

	&ZWEBSITE::save_globalref($USERNAME,$gref);
	
	## nuke flexedit in webdb.
	my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME,0);
	delete $webdb->{'flexedit'};
	&ZWEBSITE::save_website_dbref($USERNAME,$webdb,0);

	$VERB = 'FLEXEDIT';
	}

if ($VERB eq 'FLEXEDIT') {
	require ZWEBSITE;
	require PRODUCT::FLEXEDIT;
	require JSON::XS;

	my %SET = ();
	my $fref = &PRODUCT::FLEXEDIT::userfields($USERNAME,undef);

	foreach my $id (@{$fref}) {
		$SET{$id}++;
		}

	my $coder = JSON::XS->new->ascii->pretty->allow_nonref;
	$GTOOLS::TAG{'<!-- FLEXEDIT -->'} = $coder->encode($fref);

	my $c = '';
	foreach my $id (sort keys %PRODUCT::FLEXEDIT::fields) {
		next if ($SET{$id});
		my ($title) = $PRODUCT::FLEXEDIT::fields{$id}->{'title'};
		my ($type) = $PRODUCT::FLEXEDIT::fields{$id}->{'type'};
		$c .= qq~<input type="checkbox" name="$id"> $id $type $title<br>~;
		}
	$GTOOLS::TAG{'<!-- STANDARD -->'} = $c;

	$template_file = 'flexedit.shtml';
	}


if ($VERB eq 'LOGS') {
	$template_file = 'logs.shtml';
	}

if ($VERB eq 'MORE') {
	$template_file = 'more.shtml';
	}

my @TABS = ();
push @TABS, { name=>"Less", link=>"/biz/manage/support/index.cgi?VERB=", selected=>($VERB eq '')?1:0 };
push @TABS, { name=>"More", link=>"/biz/manage/support/index.cgi?VERB=MORE", selected=>($VERB eq 'MORE')?1:0 };
push @TABS, { name=>"Flexedit", link=>"/biz/manage/support/index.cgi?VERB=FLEXEDIT", selected=>($VERB eq 'FLEXEDIT')?1:0 };

push @TABS, { name=>"Logs", link=>"/biz/manage/support/index.cgi?VERB=LOGS",  selected=>($VERB eq 'LOGS')?1:0 };

$GTOOLS::TAG{'<!-- GUID -->'} = &BATCHJOB::make_guid();

&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,msgs=>\@MSGS,tabs=>\@TABS,file=>$template_file,header=>1);

