#!/usr/bin/perl

use lib "/httpd/modules";
require GTOOLS;
require ZWEBSITE;

use strict;

use Data::Dumper;
use GTOOLS;
use ZOOVY;
use LUSER;
use WATCHER;
use Text::CSV_XS;


my ($LU) = LUSER->authenticate(flags=>'_M&16');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my ($gref) = ZWEBSITE::fetch_globalref($USERNAME);
my $DST = 'AMZ';
my ($w) = WATCHER->new($USERNAME,$DST);

my $VERB = uc($ZOOVY::cgiv->{'VERB'});
if ($VERB eq '') { 
	$VERB = 'GLOBAL'; 
	if ($gref->{'amz_merchantname'} ne '') {
		$VERB = 'STRATEGIES';
		}
	}

my @MSGS = ();
my @BC = ();
push @BC, { name=>'Setup',link=>'https://www.zoovy.com/biz/setup','target'=>'_top', };
push @BC, { name=>'Repricing',link=>'https://www.zoovy.com/biz/setup/repricing','target'=>'_top', };
push @BC, { name=>'Amazon',link=>'https://www.zoovy.com/biz/setup/repricing','target'=>'_top', };

my $template_file = '';

if ($gref->{'cached_flags'} !~ /,(AMZRP|RP|MKO),/) {
   $template_file = 'deny.shtml';
   $VERB = 'DENY';
   }

##
##
##
if ($VERB eq 'STRATEGY-SAVE') {
	my ($STRATEGY_ID) = uc($ZOOVY::cgiv->{'STRATEGY_ID'});
	$STRATEGY_ID =~ s/[^A-Z0-9\-]+//gs; # we only allow URI safe characters in strategy id's
	my %config = ();
	$config{'seller'} = $gref->{'amz_merchantname'};
	$config{'sellerid'} = $gref->{'amz_sellerid'};
	$config{'ignore_sellers'} = $ZOOVY::cgiv->{'ignore_sellers'};
	$config{'bully_sellers'} = $ZOOVY::cgiv->{'bully_sellers'};

	$config{'lower_amount'} = sprintf("%.2f",$ZOOVY::cgiv->{'lower_amount'});
	if ($config{'lower_amount'}==0) { $config{'lower_amount'} = 0.01; }

	use Data::Dumper;
	print STDERR Dumper($ZOOVY::cgiv);

	print STDERR "STRATEGY_ID: $STRATEGY_ID\n";
	my ($err) = $w->add_strategy($STRATEGY_ID,\%config,\@MSGS);
	if ($err) {
		$VERB = 'STRATEGY-EDIT';
		}
	else {
		## we should really add some check and give a success message or something.
		push @MSGS, "SUCCESS|Saved strategy $STRATEGY_ID";
		$VERB = 'STRATEGIES';
		}
	}

if ($VERB eq 'STRATEGIES') {
	my $c = '';
	my ($strats) = $w->list_strategies($USERNAME);
	my $r = '';
	foreach my $stratref (@{$strats}) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class=\"$r\">";
		$c .= "<td><a href=\"index.cgi?VERB=STRATEGY-EDIT&STRATEGY_ID=$stratref->{'STRATEGY_ID'}\">[EDIT]</a></td>";
		$c .= "<td>$stratref->{'STRATEGY_ID'}</td>";
		# $c .= "<td>".Dumper($stratref->{'%'})."</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($stratref->{'MODIFIED_GMT'},2)."</td>";
		$c .= "</tr>";
		}
	if (scalar(@{$strats})==0) {
		$c .= qq~<tr><td colspan=5><div class="warning">No strategies configured. Click "Add Strategy" to create one.</td></tr>~;
		}
	$GTOOLS::TAG{'<!-- STRATEGIES -->'} = $c;
	$template_file = 'strategies.shtml';
	}



##
##
##
if ($VERB eq 'STRATEGY-NEW-CREATE') {
	my $err = '';

	my ($err) = $w->add_strategy($ZOOVY::cgiv->{'STRATEGY_ID'});
	if ($err eq '') {
		push @MSGS, "SUCCESS|Created strategy: $ZOOVY::cgiv->{'STRATEGY_ID'}";
		$VERB = 'STRATEGY-EDIT';
		}
	else {
		push @MSGS, "ERROR|$err";
		$VERB = 'STRATEGY-NEW';
		}
	}

if ($VERB eq 'STRATEGY-NEW') {
	$template_file = 'strategy-new.shtml';
	}

if ($VERB eq 'STRATEGY-EDIT') {
	my $stratref = {};
	($stratref) = $w->get_strategy($ZOOVY::cgiv->{'STRATEGY_ID'});
	if (not defined $stratref) { 
		push @MSGS, "ERROR|Could not load strategy: $ZOOVY::cgiv->{'STRATEGY_ID'}";
		$stratref = {}; 
		}
	else {
		$GTOOLS::TAG{'<!-- STRATEGY_ID -->'} = $ZOOVY::cgiv->{'STRATEGY_ID'};
		}
	
	$GTOOLS::TAG{'<!-- SELLER -->'} = $gref->{'amz_merchantname'};
	$GTOOLS::TAG{'<!-- STRATEGY_ID -->'} = $stratref->{'STRATEGY_ID'};
	my $c = '';
	foreach my $l ('0.01','0.02','0.03','0.04','0.05','0.25','0.35','0.50','0.75','0.90','1.00') {
		my ($selected) = ($stratref->{'%'}->{'lower_amount'} eq $l)?'selected':'';
		$c .= "<option $selected value=\"$l\">$l</option>\n";
		}
	$GTOOLS::TAG{'<!-- LOWER_AMOUNTS -->'} = $c;
	$GTOOLS::TAG{'<!-- BULLY_SELLERS -->'} = $stratref->{'%'}->{'bully_sellers'};
	$GTOOLS::TAG{'<!-- IGNORE_SELLERS -->'} = $stratref->{'%'}->{'ignore_sellers'};

	$template_file = 'strategy-amazon.shtml';
	}

if ($VERB eq 'EDIT') {	
	$template_file = 'profile.shtml';
	}

##
##
##
if ($VERB eq 'GLOBAL-SAVE') {
	$gref->{'amz_merchantname'} = '';
	if ($ZOOVY::cgiv->{'enable'}) {
		$gref->{'amz_merchantname'} = $ZOOVY::cgiv->{'amz_merchantname'};	
		$gref->{'amz_sellerid'} = $ZOOVY::cgiv->{'amz_sellerid'};
		}
	&ZWEBSITE::save_globalref($USERNAME,$gref);
	if ($gref->{'amz_merchantname'} eq '') {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~<div class="error">Need a Amazon Merchant name</div>~;
		}
	else {
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = qq~<div class="success">Saved settings</div>~;
		}
	$VERB = 'GLOBAL';
	}

##
##
##
if ($VERB eq 'GLOBAL') {
	my ($gref) = ZWEBSITE::fetch_globalref($USERNAME);
	$GTOOLS::TAG{'<!-- AMZ_MERCHANTNAME -->'} = $gref->{'amz_merchantname'};
	$GTOOLS::TAG{'<!-- AMZ_SELLERID -->'} = $gref->{'amz_sellerid'};
	$GTOOLS::TAG{'<!-- CHK_ENABLED -->'} = ($gref->{'amz_merchantname'} ne '')?'checked':'';
	$template_file = 'global.shtml';
	if ($gref->{'amz_merchantname'} eq '') {
		$VERB = 'RESTRICT-TO-GLOBAL';
		}
	}


if ($VERB eq 'DISPOSITION') {
	#mysql> desc REPRICE_PRODUCTS;
	#+--------------------+------------------+------+-----+---------+----------------+
	#| Field              | Type             | Null | Key | Default | Extra          |
	#+--------------------+------------------+------+-----+---------+----------------+
	#| ID                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
	#| USERNAME           | varchar(20)      | NO   |     | NULL    |                |
	#| MID                | int(10) unsigned | NO   | MUL | 0       |                |
	#| CREATED_GMT        | int(10) unsigned | NO   |     | 0       |                |
	#| MODIFIED_GMT       | int(10) unsigned | NO   |     | 0       |                |
	#| SKU                | varchar(45)      | NO   |     | NULL    |                |
	#| ASIN               | varchar(20)      | NO   |     | NULL    |                |
	#| IS_SUSPENDED       | tinyint(4)       | NO   |     | 0       |                |
	#| STRATEGY_ID        | varchar(10)      | NO   |     | NULL    |                |
	#| VAR_MIN_PRICE      | decimal(10,2)    | NO   |     | 0.00    |                |
	#| VAR_MIN_SHIP       | decimal(10,2)    | NO   |     | 0.00    |                |
	#| VAR_MAX_PRICE      | decimal(10,2)    | YES  |     | 0.00    |                |
	#| LAST_PRICE         | decimal(10,2)    | NO   |     | 0.00    |                |
	#| LAST_SHIP          | decimal(10,2)    | NO   |     | 0.00    |                |
	#| LAST_UPDATE_GMT    | int(10) unsigned | NO   |     | 0       |                |
	#| LAST_STATUS        | tinytext         | NO   |     | NULL    |                |
	#| CURRENT_PRICE      | decimal(10,2)    | NO   |     | 0.00    |                |
	#| CURRENT_SHIP       | decimal(10,2)    | NO   |     | 0.00    |                |
	#| LOCK_ID            | int(10) unsigned | YES  |     | 0       |                |
	#| LOCK_GMT           | int(10) unsigned | YES  |     | 0       |                |
	#| NEEDS_PRICE_UPDATE | tinyint(4)       | NO   |     | 0       |                |
	#+--------------------+------------------+------+-----+---------+----------------+
	#21 rows in set (0.17 sec)

	$template_file = 'disposition.shtml';
	my $udbh = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select SKU,ASIN,
		AMZRP_HAS_ERROR,AMZRP_STATUS_MSG,
		AMZRP_STRATEGY,AMZRP_MIN_SHIP_I,AMZRP_MIN_PRICE_I,AMZRP_MAX_PRICE_I,AMZRP_LAST_PRICE_I,AMZRP_LAST_SHIP_I,
		AMZRP_LAST_POLL_TS,AMZRP_SET_PRICE_I,AMZRP_SET_SHIP_I,AMZRP_STATUS,AMZRP_NEXT_POLL_TS
		from AMAZON_PID_UPCS where MID=$MID and AMZRP_IS_ENABLED>0 order by SKU";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	my $r = '';
	while ( my $row = $sth->fetchrow_hashref() ) {
		# $r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr>";
		$c .= "<td>$row->{'SKU'}></td>";
		$c .= "<td>$row->{'ASIN'}></td>";
		$c .= "<td>$row->{'AMZRP_STRATEGY'}</td>";
		$c .= "<td>$row->{'AMZRP_HAS_ERROR'}</td>";
		$c .= "<td>".&ZTOOLKIT::iprice($row->{'AMZRP_MIN_PRICE_I'})."</td>";
		$c .= "<td>".&ZTOOLKIT::iprice($row->{'AMZRP_MIN_SHIP_I'})."</td>";
		$c .= "<td>".&ZTOOLKIT::iprice($row->{'AMZRP_MAX_PRICE_I'})."</td>";
		$c .= "<td>".&ZTOOLKIT::iprice($row->{'AMZRP_SET_PRICE_I'})."</td>";
		$c .= "<td>".&ZTOOLKIT::iprice($row->{'AMZRP_SET_SHIP_I'})."</td>";
		$c .= "<td>$row->{'AMZRP_LAST_POLL_TS'}</td>";
		$c .= "<td>$row->{'AMZRP_NEXT_POLL_TS'}</td>";
		$c .= "<td>$row->{'AMZRP_STATUS_MSG'}</td>";
		$c .= "</tr>";		
		}
	if ($c eq '') {
		$c .= "<tr><td colspan=5><div class='warning'>No products have been configured yet.</div></td></tr>";
		}
	else {
		}
	$GTOOLS::TAG{'<!-- LOGS -->'} = $c;
	
	$sth->finish();
	&DBINFO::db_user_close();
	}



##
##
##
##
##
if ($VERB eq 'DEBUG-RUN') {
	my ($SKU) = $ZOOVY::cgiv->{'SKU'};
	$VERB = 'DEBUG';
	require LISTING::MSGS;

	my ($lm) = LISTING::MSGS->new($USERNAME);
	$w->set('*LM'=>$lm);

	my ($SKUREF) = $w->get_skuref($SKU);
	if (not defined $SKUREF) {
		$lm->pooshmsg("ERROR|+Could not load SKU:$SKU");
		}
	else {
		$lm->pooshmsg("INFO|+ASIN: $SKUREF->{'ASIN'}");
		$lm->pooshmsg("INFO|+CURRENT STRATEGY: $SKUREF->{'AMZRP_STRATEGY'}");

		if ($ZOOVY::cgiv->{'strategy'} eq $SKUREF->{'AMZRP_STRATEGY'}) {
			## we're going to try the current strategy!
			}
		elsif ($ZOOVY::cgiv->{'strategy'} ne '') {
			$SKUREF->{'AMZRP_STRATEGY'} = $ZOOVY::cgiv->{'strategy'};
			$lm->pooshmsg("HINT|+WE ARE GOING TO TRY STRATEGY: $SKUREF->{'AMZRP_STRATEGY'}");

			if (not $ZOOVY::cgiv->{'use_strategy'}) {
				## we are just temporarily using this strategy.
				}
			elsif ($w->dst() eq 'AMZ') {
				my ($udbh) = &DBINFO::db_user_connect($USERNAME);
				$lm->pooshmsg("SUCCESS|+Updating strategy in AMZRP database");
				my $qtSTRATEGY = $udbh->quote($ZOOVY::cgiv->{'strategy'});
				my $pstmt = "update AMAZON_PID_UPCS set AMZRP_STRATEGY=$qtSTRATEGY where MID=".int($MID)." and SKU=".$udbh->quote($SKU);
				print STDERR "$pstmt\n";
				$udbh->do($pstmt);
				&DBINFO::db_user_close();
				}

			}

		$w->verify($SKUREF);	
		}

	my $out = '';
	foreach my $msg (@{$lm->msgs()}) {
		my ($d) = LISTING::MSGS::msg_to_disposition($msg);

		my $type = $d->{'_'};
		my $style = '';
		if ($type eq 'HINT') { 
			$style = 'style="color: green; border: thin dashed;"'; 
			}
		elsif (($type eq 'GOOD') || ($type eq 'SUCCESS') || ($type eq 'PAUSE')) { 
			$style = 'style="color: blue"'; 
			}
		elsif (($type eq 'FAIL') || ($type eq 'STOP') || ($type eq 'PRODUCT-ERROR')) { 
			$style = 'style="color: red"'; 
			}
		elsif (($type eq 'WARN')) { 
			$style = 'style="color: orange; border: thin dashed;"'; 
			}
		elsif ($type eq 'DEBUG') {
			$style = 'style="color: gray;"';
			}
		elsif ($type eq 'INFO') { 
			$style = 'style="font-size: 8pt; color: CCCCCC;"'; 
			}
		else {
			}
		$out .= "<div $style>$type: $d->{'+'}</div>";
		}

	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = $out;
	}

if ($VERB eq 'DEBUG') {
	## debugger
	$GTOOLS::TAG{'<!-- MARKETPLACE -->'} = '';
	if ($DST eq 'AMZ') { $GTOOLS::TAG{'<!-- MARKETPLACE -->'} = 'Amazon'; }

	$GTOOLS::TAG{'<!-- SKU -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'SKU'});
	$GTOOLS::TAG{'<!-- CHK_USE_STRATEGY -->'} = (defined $ZOOVY::cgiv->{'use_strategy'})?'checked':'';
	my ($strats) = $w->list_strategies($USERNAME);
	my $c = '';
	$c .= "<option value=\"\">--</option>";
	foreach my $stratref (@{$strats}) {
		my $selected = ($ZOOVY::cgiv->{'strategy'} eq $stratref->{'STRATEGY_ID'})?'selected':'';
		$c .= "<option $selected value=\"$stratref->{'STRATEGY_ID'}\">$stratref->{'STRATEGY_ID'}</option>";
		}
	$GTOOLS::TAG{'<!-- STRATEGIES -->'} = $c;

	if (not defined $GTOOLS::TAG{'<!-- DEBUG_OUT -->'}) {
		$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = "<i>Please press RUN to see output</i>";
		}

	$template_file = 'debug.shtml';
	}



#if ($VERB eq 'LOGS') {
#	$template_file = 'logs.shtml';
#
#	my $udbh = &DBINFO::db_user_connect($USERNAME);
#	my $pstmt = "select * from WATCHER_HISTORY where MID=$MID and DST=$qtDST order by CREATED_GMT";
#	my $sth = $rdbh->prepare($pstmt);
#	$sth->execute();
#	my $c = '';
#	my $r = '';
#	while ( my $row = $sth->fetchrow_hashref() ) {
#		$r = ($r eq 'r0')?'r1':'r0';
#		$c .= "<tr class=\"$r\">".
#				"<td nowrap valign=top>".&ZTOOLKIT::pretty_date($row->{'CREATED_GMT'},2	)."</td>".
#				"<td nowrap valign=top><b>".$row->{'SKU'}."</b></td>".
#				"<td nowrap valign=top>".$row->{'ASIN'}."</td>".
#				"<td nowrap valign=top>".$row->{'VERB'}."</td>".
#				"<td nowrap valign=top>".$row->{'PRICE_WAS'}."</td>".
#				"<td nowrap valign=top>".$row->{'PRICE_IS'}."</td>".
#				"<td>".$row->{'NOTE'}."</td>".
#				"</tr>";
#		}
#	if ($c eq '') {
#		$c .= "<tr><td><div class='warning'>No actions have been taken yet.</div></td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- LOGS -->'} = $c;
#	
#	$sth->finish();
#	&DBINFO::db_user_close();
#	}


my @TABS = ();
push @TABS, { name=>'Strategies', selected=>($VERB eq 'STRATEGIES')?1:0, link=>'index.cgi?VERB=STRATEGIES' };
if ($VERB ne 'RESTRICT-TO-GLOBAL') {
	## if they don't have the service enabled, then don't show other tabs.
	push @TABS, { name=>'Add Strategy', selected=>($VERB eq 'ADD')?1:0, link=>'index.cgi?VERB=STRATEGY-NEW' };
	push @TABS, { name=>'Amazon Global Config', selected=>($VERB eq 'GLOBAL')?1:0, link=>'index.cgi?VERB=GLOBAL' };
	push @TABS, { name=>'Diagnostics', selected=>($VERB eq 'DEBUG')?1:0, link=>'index.cgi?VERB=DEBUG' };
	push @TABS, { name=>'Disposition', selected=>($VERB eq 'LOGS')?1:0, link=>'index.cgi?VERB=DISPOSITION' };
#	push @TABS, { name=>'Event Logs', selected=>($VERB eq 'LOGS')?1:0, link=>'index.cgi?VERB=LOGS' };
	}

&GTOOLS::output(
	header=>1,
	bc=>\@BC,
	file=>$template_file,
	msgs=>\@MSGS,
	tabs=>\@TABS,
	jquery=>1,
	);

