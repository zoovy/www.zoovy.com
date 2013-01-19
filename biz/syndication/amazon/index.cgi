#!/usr/bin/perl

use strict;
use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use AMAZON3;
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use strict;
use SYNDICATION;

my ($zdbh) = &DBINFO::db_zoovy_connect();	

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

# my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/syndication",2,'_P&16');


my $q = new CGI;
my $qtUSERNAME = $zdbh->quote($USERNAME);
my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my $template_file = '';
my $help = '#50378';

my @MSGS = ();


my $VERB = $q->param('VERB');

print STDERR "VERB: $VERB\n";

my @BC = ();
push @BC, { name=>'Syndication',link=>'/biz/syndication','target'=>'_top', };
push @BC, { name=>'Amazon',link=>'/biz/syndication/amazon','target'=>'_top', };

#if (1) {
#	$template_file = 'maintenance.shtml';
#	$VERB = 'MAINTENANCE';
#	}

if ($LU->is_zoovy()) {
	## zoovy users never get denied.
	}
#elsif ($FLAGS !~ /,AMZ,/) {
#	$template_file = 'deny.shtml';
#	$VERB = 'DENY';
#	}

if ($VERB eq '') { 
	$VERB = 'CONFIG'; 
	}


if ($VERB eq 'CONFIG-SAVE') {
	## automatically create UPCs for products that do not have them defined 
	## and their category requires them
	my $upc_creation = ($q->param('upc_creation')==1)?1:0;
	## indicates that the merchant is exempt from the UPC requirement
	my $private_label = ($q->param('private_label')==1)?1:0;
	## Suppress Order creation emails, ie Amazon doesn't want our merchants to contact their customers

	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	tie my %s, 'SYNDICATION', THIS=>$so;
	$s{'.schedule'} = $q->param('pricing_schedule');
	#$s{'.shipping'} = $hashref->{'SHIPPING_MAP'};
	$s{'CREATED_GMT'} = time();
	## not sure what UPDATED is
	# $s{'.xmlorders'} = $hashref->{'XML_ORDERS'};
	$s{'IS_ACTIVE'} = 1;
	# $s{'.feedpermissions'} = $hashref->{'FEED_PERMISSIONS'};
	$s{'.emailconfirmations'} = 1; # suppress email?? wtf this is backwards!?!
	$s{'.upc_creation'} = $upc_creation;
	$s{'.private_label'} = $private_label; 
	$s{'ERRCOUNT'} = 0;
	$so->save();

   my $amz_merchantname = $ZOOVY::cgiv->{'amz_merchantname'};
	$amz_merchantname =~ s/[\s]+$//g;
	$amz_merchantname =~ s/^[\s]+//g;
	$s{'.amz_merchantname'} = $amz_merchantname;

   my $amz_userid = $ZOOVY::cgiv->{'amz_userid'};
	$amz_userid =~ s/[\s]+$//g;
	$amz_userid =~ s/^[\s]+//g;
	$s{'.amz_userid'} = $amz_userid;

   my $amz_password = $ZOOVY::cgiv->{'amz_password'};
	$amz_password =~ s/[\s]+$//g;
	$amz_password =~ s/^[\s]+//g;
	$s{'.amz_password'} = $amz_password;

   my $amz_merchanttoken = $ZOOVY::cgiv->{'amz_merchanttoken'};
	$amz_merchanttoken =~ s/[\s]+$//g;
	$amz_merchanttoken =~ s/^[\s]+//g;
	$s{'.amz_merchanttoken'} = $amz_merchanttoken;

   my $amz_merchantid = $ZOOVY::cgiv->{'amz_merchantid'};;
	$amz_merchantid =~ s/[^A-Z0-9]+//gs;
	$amz_merchantid =~ s/[\s]+$//g;
	$amz_merchantid =~ s/^[\s]+//g;
	$s{'.amz_merchantid'} = $amz_merchantid;

	my $amz_accesskey = $ZOOVY::cgiv->{'amz_accesskey'};
	$amz_accesskey =~ s/[\s]+$//g;
	$amz_accesskey =~ s/^[\s]+//g;
	$s{'.amz_accesskey'} = $amz_accesskey;

	my $amz_secretkey = $ZOOVY::cgiv->{'amz_secretkey'};
	$amz_secretkey =~ s/[\s]+$//g;
	$amz_secretkey =~ s/^[\s]+//g;
	$s{'.amz_secretkey'} = $amz_secretkey;

	$s{'.orderpermissions'} = (defined $ZOOVY::cgiv->{'ORDER_PERMS'})?1:0;
	$s{'.fbapermissions'} = (defined $ZOOVY::cgiv->{'FBA_PERMS'})?1:0;

   #if ($FLAGS !~ /,RP,/) {
   #   $panel_positions{'amzreprice'} = -1;
   #   }

	my ($FEED_PERMS) = 0;
	$FEED_PERMS |= (defined $ZOOVY::cgiv->{'FEED_PERMS_1'})?1:0;		## inventory
	$FEED_PERMS |= (defined $ZOOVY::cgiv->{'FEED_PERMS_2'})?2:0;		## prices/shipping
	$FEED_PERMS |= (defined $ZOOVY::cgiv->{'FEED_PERMS_4'})?4:0; 
	if ($FEED_PERMS==0) {
		}
	elsif ($FLAGS !~ /,AMZ,/) {
		$FEED_PERMS = 0;
		push @MSGS, "ERROR|Feed permissions were disabled due to missing AMAZON bundle";
		}
	elsif ($s{'.orderpermissions'}==0) {
		$FEED_PERMS = 0;
		push @MSGS, "ERROR|Products/Inventory/Pricing cannot be enabled without ORDER processing also enabled.";
		}
	# AMAZON_FEEDS CAN BE REMOVED
	$s{'.feedpermissions'} = $FEED_PERMS;
	

	if ($FEED_PERMS > 0) {
		my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
		if ((not defined $gref->{'amz_prt'}) || ($gref->{'amz_prt'} != $PRT)) {
			push @MSGS, "SUCCESS|Updated send partition to $PRT";
			$LU->log("SETUP.AMAZON","Configured amazon to send products from prt# $PRT");
			$gref->{'amz_prt'} = $PRT;
			&ZWEBSITE::save_globalref($USERNAME,$gref);
			}
		}

	$s{'ERRCOUNT'} = 0;
	if ((not $s{'.feedpermissions'}) && (not $s{'.orderpermissions'}) && (not $s{'.fbapermissions'})) {
		push @MSGS, "WARN|Due to current configuration - syndication has been disabled.";
		$s{'IS_ACTIVE'} = 0;
		}
	$so->save();

	push @MSGS, "SUCCESS|Updated settings";
	$LU->log("SETUP.AMAZON","Tokens updated","SAVE");
	$VERB = 'CONFIG';
	}

	
if ($VERB eq 'CONFIG') {
	my $hashref = {};

	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	tie my %s, 'SYNDICATION', THIS=>$so;

	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;

	$GTOOLS::TAG{'<!-- AMZ_MERCHANTNAME -->'} = &ZOOVY::incode($s{'.amz_merchantname'});
	$GTOOLS::TAG{'<!-- AMZ_USERID -->'} = &ZOOVY::incode($s{'.amz_userid'});
	$GTOOLS::TAG{'<!-- AMZ_PASSWORD -->'} = &ZOOVY::incode($s{'.amz_password'});
	$GTOOLS::TAG{'<!-- AMZ_MERCHANTTOKEN -->'} = &ZOOVY::incode($s{'.amz_merchanttoken'});
	$GTOOLS::TAG{'<!-- AMZ_MERCHANTID -->'} = &ZOOVY::incode($s{'.amz_merchantid'});
	$GTOOLS::TAG{'<!-- AMZ_ACCESSKEY -->'} = &ZOOVY::incode($s{'.amz_accesskey'});
	$GTOOLS::TAG{'<!-- AMZ_SECRETKEY -->'} = &ZOOVY::incode($s{'.amz_secretkey'});

	my $feedpermissions = $so->get('.feedpermissions');
	$GTOOLS::TAG{'<!-- FEED_PERMS_1 -->'} = ($feedpermissions&1)?'checked':'';
	$GTOOLS::TAG{'<!-- FEED_PERMS_2 -->'} = ($feedpermissions&2)?'checked':'';
	$GTOOLS::TAG{'<!-- FEED_PERMS_4 -->'} = ($feedpermissions&4)?'checked':'';

	## FBA Settings, added 2011-06-10 - patti
	## - check if merchant wants us to import FBA Order and Tracking
	##	- Tracking includes orders that originate from Amazon 
	##		and those that are manually put into FBA via the merchant (ie manual FWS)
	$GTOOLS::TAG{'<!-- FBA_PERMS -->'} = ($so->get('.fbapermissions'))?'checked':'';
	$GTOOLS::TAG{'<!-- ORDER_PERMS -->'} = ($so->get('.orderpermissions'))?'checked':'';
	
	## check to make sure they only have one profile enabled for syndication!
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select PROFILE from SYNDICATION where MID=$MID /* $USERNAME */ and DSTCODE='AMZ'";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ACTIVE = ();
	while ( my ($profile) = $sth->fetchrow() ) { 
		my ($so) = SYNDICATION->new($USERNAME,$profile,"AMZ");
		if ( ($so->get('.feedpermissions')&7)>0) {
			push @ACTIVE, $profile; 
			}
		}
	$sth->finish();
	&DBINFO::db_user_close();
	if (scalar(@ACTIVE)>1) {
		push @MSGS, "WARN|You must only have one partition setup to transmit products/inventory currently partitions: ".join(',',@ACTIVE)." have products configured to syndicate.";
		}
	if ($FLAGS !~ /,AMZ,/) {
		push @MSGS, "WARN|You will not be able to send products (only receive orders) without the Amazon bundle.";
		}

	my ($userref) = AMAZON3::fetch_userprt($USERNAME,$PRT);
	#print STDERR Dumper($hashref);
	## if Product Syndication has been turned, ALERT merchant
	if ($s{'IS_ACTIVE'}==0) {
		push @MSGS, "WARN|all syndication has been turned off";
		}

	$GTOOLS::TAG{'<!-- MERCHANT -->'} = $userref->{'AMAZON_MERCHANT'};
	$GTOOLS::TAG{'<!-- MERCHANTID -->'} = $userref->{'AMAZON_MERCHANTID'};
	$GTOOLS::TAG{'<!-- USERID -->'} = $userref->{'USERID'};
	$GTOOLS::TAG{'<!-- PASSWORD -->'} = $userref->{'PASSWORD'};
	$GTOOLS::TAG{'<!-- TOKEN -->'} = $userref->{'AMAZON_TOKEN'};

	$GTOOLS::TAG{'<!-- PRIVATE_LABEL -->'} = ($s{'.private_label'}>0)?'checked':'';
	$GTOOLS::TAG{'<!-- UPC_CREATION -->'} = ($s{'.upc_creation'}>0)?'checked':'';

	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
	$GTOOLS::TAG{'<!-- MWSTOKEN_STATUS -->'} = '<font color="red">Not Set</font>';
   if ($userref->{'AMAZON_MWSTOKEN'} ne '') {
      $GTOOLS::TAG{'<!-- MWSTOKEN_STATUS -->'} = "Token: ($userref->{'AMAZON_MWSTOKEN'})";
      }

	my $out = qq~<select  name="pricing_schedule"><option value="">None</option>~;
	require WHOLESALE;
	foreach my $sid (@{&WHOLESALE::list_schedules($USERNAME)}) {
		my ($S) = &WHOLESALE::load_schedule($USERNAME,$sid);
		if ($S->{'TITLE'} eq '') { $S->{'TITLE'} = "Untitled Schedule"; }
		my $selected = ($s{'.schedule'} eq $sid)?'selected':'';
		$out .= "<option $selected value=\"$sid\">$sid - $S->{'TITLE'}</option>\n";
		}
	$out .= "</select>";

	$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $out;
	$GTOOLS::TAG{'<!-- STATUS -->'} = $userref->{'STATUS'};
	if ($userref->{'IS_ERROR'} > 0) { 
		push @MSGS, "WARN|Error(s) found on last syndication, please check Logs.";
		}
	elsif ($s{'PRODUCTS_LASTRUN_GMT'} == 0) {
		$GTOOLS::TAG{'<!-- LAST_UPDATE -->'} = 'Pending - next 24 hours, all Products have been reset';
		}
	else {
		$GTOOLS::TAG{'<!-- LAST_UPDATE -->'} = &ZTOOLKIT::pretty_date($s{'PRODUCTS_LASTRUN_GMT'},1);
		}
	
	## link for webdoc
	my ($helplink, $helphtml) = GTOOLS::help_link('Amazon Merchant Feed Webdoc', 50378);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;

	push @BC, { 'name'=>'Config' };
	$template_file = 'config.shtml';
	}


########################################################
if ($VERB eq 'CATEGORIES-SAVE') {
	my $changed = 0;
   my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
   foreach my $safe (sort $NC->paths()) {
		next if (not defined $q->param('navcat-'.$safe));
		#next if ($q->param('navcat-'.$safe) eq '');
      my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		next if ($metaref->{'AMAZON_THE'} eq $q->param('navcat-'.$safe));
		$metaref->{'AMAZON_THE'} = $q->param('navcat-'.$safe);
      $NC->set($safe,metaref=>$metaref);
		}
	$NC->save();
	undef $NC;
	$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<font color='blue'>Updated categories</font><br><br>";
	$VERB = 'CATEGORIES';
	}

if ($VERB eq 'CATEGORIES') {
	my $c = '';
	use Data::Dumper;
   my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	my $theref = &AMAZON3::fetch_thesaurus($USERNAME);
   foreach my $safe (sort $NC->paths()) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
      my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);

		# commented out 9/13/2005 patti, per customer
		#next if (substr($pretty,0,1) eq '!');
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		my $name = ''; foreach (split(/\./,$safe)) { $name .= "&nbsp;"; } $name .= $pretty;
		if ($safe eq '.') { $name = 'HOMEPAGE'; }
		my $val = $metaref->{'AMAZON_THE'};
		$c .= '<tr><td>'.$name.'</td><td><select name="navcat-'.$safe.'"><option value="">Not Set</option>';
		my @values = ZTOOLKIT::value_sort($theref);
		foreach my $id (@values) {
			$c .= "<option ".(($id==$val)?'selected':'')." value='$id'>$theref->{$id}</a>";
			}
		$c .= '</select></td></tr>';
		}

	if	($c eq '') { $c = '<tr><td><i>Uh-oh! No website categories exist??</i></td></tr>'; }
	else { $c = "<tr><td><b>Category</b></td><td><b>Thesaurus</b></td></tr>".$c; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	push @BC, { 'name'=>'Categories' };
	$template_file = 'categories.shtml';
	$help = '#50391';

	}

## 
if ($VERB eq 'UNCONFIRMED') {
	require CART2;

	$template_file = 'unconfirmed.shtml';
	push @BC, { 'name'=>'Unconfirmed Orders' };
	my $out = '<table><tr><th></th><th>Created</th><th>Amazon Order ID</th><th>Zoovy Order ID</th></tr>';

	my $PATH = ZOOVY::resolve_userpath($USERNAME);

	## only select from the last 50 days
	my $pstmt = "select CREATED_GMT,AMAZON_ORDERID,OUR_ORDERID from AMAZON_ORDERS ".
					"where CREATED_GMT >unix_timestamp(now())-(50*86400) and FULFILLMENT_ACK_REQUESTED_GMT>0 and FULFILLMENT_ACK_PROCESSED_GMT=0 and MID=".$udbh->quote($MID).
					" and PRT=$PRT /* $USERNAME */ and OUR_ORDERID <> '' order by ID desc";
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute;
	my $ctr =0;
	while(my ($CREATED_GMT,$AMAZON_ORDERID,$OUR_ORDERID) = $sth->fetchrow()) {

		
		my $created = ZTOOLKIT::pretty_date($CREATED_GMT,1);

		my $cancelled = 0;
		my ($O2) = CART2->new_from_oid($USERNAME,$OUR_ORDERID);
		if (not defined $O2) {
			$cancelled = 1;
			}
		elsif (defined $O2->in_get('flow/cancelled_ts') && $O2->in_get('flow/cancelled_ts') > 0) {
			$cancelled = 1;
			}
		$ctr++;
		$out .= qq~<tr>~.
				   qq~<td width=30>$ctr</td>~.
					qq~<td width="200">$created</td>~.
				   qq~<td width="200">$AMAZON_ORDERID</td>~.
				   qq~<td width="200"><a href="/biz/orders/index.cgi?VERB=QUICKSEARCH&find_text=$OUR_ORDERID&find_status=ANY&x=13&y=5">$OUR_ORDERID~;
		if ($cancelled) { $out .= "**"; }
		$out .= "</a></td></tr>";
		}		
 	$sth->finish;
	$GTOOLS::TAG{'<!-- UNCONFIRMED_DATA -->'} = $out."</table><br><br><br><br>** Indicates cancelled orders.";

	if ($ctr==0) { $GTOOLS::TAG{'<!-- UNCONFIRMED_DATA -->'} = "<font color=red>No data available at this time</font><br><br>"; }
	}


## now called SETTLEMENTS
if ($VERB eq 'REPORTS') {
	my $URL = "http://static.zoovy.com/merchant/".$USERNAME."/amz_settlement_report_";
	
	$template_file = 'reports.shtml';
	push @BC, { 'name'=>'Settlements' };
	my $out = '<table><tr><th>Start Date</th><th>End Date</th><th>Rows</th></tr>';

	my $PATH = ZOOVY::resolve_userpath($USERNAME);
	my $pstmt = "select DOCID,REPORTID,START_DATE,END_DATE,ROWS from AMAZON_REPORTS ".
					"where type = 'Settlement' and mid = $MID".
					" and PRT=$PRT order by START_DATE desc";
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute;
	my $ctr =0;
	while(my ($DOCID,$REPORTID,$START_DATE,$END_DATE,$ROWS) = $sth->fetchrow()) {
		my $start = $START_DATE;
		$start =~ s/(\d\d\d\d)(\d\d)(\d\d)/$1-$2-$3/;
		my $end = $END_DATE;
		$end =~ s/(\d\d\d\d)(\d\d)(\d\d)/$1-$2-$3/;
		
		## implemented ROWS at the same time as the addition of start_date in the URL
		if ($ROWS > 0) {
		  $out .= qq~<tr><td width="300">$start</td>~.
				  qq~<td width="300"><a href="~.$URL.$START_DATE."_".$END_DATE.qq~.csv">$end</a></td><td>$ROWS</td></tr>~;
		  }
      else {
        $out .= qq~<tr><td width="300">$start</td>~.
				  qq~<td width="300"><a href="~.$URL.$END_DATE.qq~.csv">$end</a></td><td>NA</td></tr>~;
		  }
		$ctr++;
		}		
 	$sth->finish;
	$GTOOLS::TAG{'<!-- REPORT_DATA -->'} = $out."</table><br><br>";

	if ($ctr==0) { $GTOOLS::TAG{'<!-- REPORT_DATA -->'} = "<font color=red>No data available at this time</font><br><br>"; }
	}

#################################################################################################
##
##	
##

my $thesaurusinfo = undef;

if ($VERB eq 'THESAURUS-CONFIRM-DELETE') {
	$template_file = "confirm-delete.shtml";	
	$GTOOLS::TAG{'<!-- ID -->'} = $ZOOVY::cgiv->{'ID'};
	$GTOOLS::TAG{'<!-- THESAURUS -->'} = $ZOOVY::cgiv->{'THESAURUS'};
	$help = '#50390';
	}

if ($VERB eq 'THESAURUS-DELETE') {
	
	$VERB = 'THESAURUS';
	my $pstmt = "delete from AMAZON_THESAURUS where MID=$MID and ID=".int($ZOOVY::cgiv->{'ID'});
	print STDERR $pstmt."\n";
	$udbh->do($pstmt);
	}

if ($VERB eq 'THESAURUS-SAVE') {
	$VERB = 'THESAURUS-EDIT';
	
	my $name = $ZOOVY::cgiv->{'name'};
	$name = uc($name);
	$name =~ s/[^\w]+/_/gs;

	$ZOOVY::cgiv->{'search_terms'} =~ s/\s+/ /g;
	$ZOOVY::cgiv->{'search_terms'} =~ s/, /,/g;
	$ZOOVY::cgiv->{'search_terms'} = substr($ZOOVY::cgiv->{'search_terms'},0,250);

	my ($pstmt) = &DBINFO::insert($udbh,'AMAZON_THESAURUS',{
		ID=>int($ZOOVY::cgiv->{'ID'}),
		MID=>$MID, USERNAME=>$USERNAME,
		PROFILE=>$name,
		ITEMTYPE=>$ZOOVY::cgiv->{'itemtype'},
		USEDFOR=>$ZOOVY::cgiv->{'usedfor'},
		SEARCH_TERMS=>$ZOOVY::cgiv->{'search_terms'},
		OTHERITEM=>$ZOOVY::cgiv->{'otherattribs'},
		SUBJECTCONTENT=>$ZOOVY::cgiv->{'subjectcontent'},
		TARGETAUDIENCE=>$ZOOVY::cgiv->{'targetaudience'},
		ISGIFTWRAPAVAILABLE=>$ZOOVY::cgiv->{'isgiftwrapavailable'},
		ISGIFTMESSAGEAVAILABLE=>$ZOOVY::cgiv->{'isgiftmessageavailable'},
		ADDITIONALATTRIBS=>$ZOOVY::cgiv->{'additionalattribs'}
		},
		sql=>1,
		update=>(($ZOOVY::cgiv->{'ID'}==0)?0:2),
		key=>['MID','ID']
		);
	print STDERR "$pstmt\n";
	$udbh->do($pstmt);

	#if (int($ZOOVY::cgiv->{'ID'})>0) {
	#	my $pstmt = "update AMAZON_THESAURUS set PROFILE=".$udbh->quote($name);
	#	$pstmt .= ",ITEMTYPE=".$udbh->quote($ZOOVY::cgiv->{'itemtype'});
	#	$pstmt .= ",USEDFOR=".$udbh->quote($ZOOVY::cgiv->{'usedfor'});
	#	#$pstmt .= ",SEARCH_TERMS_1=".$udbh->quote($ZOOVY::cgiv->{'search_terms_1'});
	#	#$pstmt .= ",SEARCH_TERMS_2=".$udbh->quote($ZOOVY::cgiv->{'search_terms_2'});
	#	#$pstmt .= ",SEARCH_TERMS_3=".$udbh->quote($ZOOVY::cgiv->{'search_terms_3'});
	#	#$pstmt .= ",SEARCH_TERMS_4=".$udbh->quote($ZOOVY::cgiv->{'search_terms_4'});
	#	#$pstmt .= ",SEARCH_TERMS_5=".$udbh->quote($ZOOVY::cgiv->{'search_terms_5'});
	#	$pstmt .= ",SEARCH_TERMS=".$udbh->quote($ZOOVY::cgiv->{'search_terms'});
	#	$pstmt .= ",OTHERITEM=".$udbh->quote($ZOOVY::cgiv->{'otherattribs'});
	#	$pstmt .= ",SUBJECTCONTENT=".$udbh->quote($ZOOVY::cgiv->{'subjectcontent'});
	#	$pstmt .= ",TARGETAUDIENCE=".$udbh->quote($ZOOVY::cgiv->{'targetaudience'});
	#	$pstmt .= ",ISGIFTWRAPAVAILABLE=".$udbh->quote($ZOOVY::cgiv->{'isgiftwrapavailable'});
	#	$pstmt .= ",ISGIFTMESSAGEAVAILABLE=".$udbh->quote($ZOOVY::cgiv->{'isgiftmessageavailable'});
	#	$pstmt .= ",ADDITIONALATTRIBS=".$udbh->quote($ZOOVY::cgiv->{'additionalattribs'});
	#	$pstmt .= " where MID=$MID and ID=".int($ZOOVY::cgiv->{'ID'})." limit 1";
	#	$udbh->do($pstmt);
	#	}
	#else {
	#	## insert		
	#	my $pstmt = "insert into AMAZON_THESAURUS ".
	#					"(MID,CREATED_GMT,PROFILE,ITEMTYPE,USEDFOR,OTHERITEM,SUBJECTCONTENT,TARGETAUDIENCE,ISGIFTWRAPAVAILABLE,".
	#					"ISGIFTMESSAGEAVAILABLE,ADDITIONALATTRIBS,".
	#					#"SEARCH_TERMS_1,SEARCH_TERMS_2,SEARCH_TERMS_3,SEARCH_TERMS_4,SEARCH_TERMS_5) ".
	#					"SEARCH_TERMS) ".
	#					"values(?,?,?,?,?,?,?,?,?,?,?,?)";
	#	my $sth = $udbh->prepare($pstmt);
	#	$sth->execute($MID,time(),$name,$ZOOVY::cgiv->{'itemtype'},$ZOOVY::cgiv->{'usedfor'},
	#	 $ZOOVY::cgiv->{'otherattribs'},$ZOOVY::cgiv->{'subjectcontent'},$ZOOVY::cgiv->{'targetaudience'},
	#	 $ZOOVY::cgiv->{'isgiftwrapavailable'}, $ZOOVY::cgiv->{'isgiftmessageavailable'},
	#	 $ZOOVY::cgiv->{'additionalattribs'},$ZOOVY::cgiv->{'search_terms'});
#$Z#OOVY::cgiv->{'search_terms_1'},$ZOOVY::cgiv->{'search_terms_2'},,$ZOOVY::cgiv->{'search_terms_3'},$ZOOVY::cgiv->{'search_terms_4'},$ZOOVY::cgiv->{'search_terms_5'});
	#	$sth->finish();
	#	}

	push @MSGS, "SUCCESS|Changes saved";
	}

if ($VERB eq 'THESAURUS-EDIT') {
	$VERB = 'THESAURUS';
	my $pstmt = "select * from AMAZON_THESAURUS where MID=$MID and ID=".int($ZOOVY::cgiv->{'ID'});
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	$thesaurusinfo = $sth->fetchrow_hashref();
	$sth->finish();

	}


if ($VERB eq 'THESAURUS') {

	my $pstmt = "select ID,PROFILE,ITEMTYPE,USEDFOR from AMAZON_THESAURUS where MID=$MID";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my ($id,$profile,$itemtype,$usedfor) = $sth->fetchrow()) {
		$c .= "<tr><td><a href=\"/biz/syndication/amazon/index.cgi?VERB=THESAURUS-CONFIRM-DELETE&ID=$id&THESAURUS=$profile\">[Del]</a> <a href=\"/biz/syndication/amazon/index.cgi?VERB=THESAURUS-EDIT&ID=$id\">[Edit]</a></td><td>$profile</td><td>$itemtype: $usedfor</td></tr>\n";
		}
	if ($c eq '') { $c .= "<i>No profiles defined - you will NOT be able to transmit products to Amazon</i>"; }
	else { $c = "<tr><td></td><td><b>Profile</b></td><td><b>Item Type: Used For</b></td></tr>".$c; }
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;

	$GTOOLS::TAG{'<!-- TITLE -->'} = ($thesaurusinfo->{'PROFILE'} eq '')?'Add New Thesaurus Profile':'Edit Thesaurus Profile '.$thesaurusinfo->{'PROFILE'};
	$GTOOLS::TAG{'<!-- ID -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'ID'}:'0';
	$GTOOLS::TAG{'<!-- NAME -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'PROFILE'}:'';
	$GTOOLS::TAG{'<!-- ITEMTYPE -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'ITEMTYPE'}:'';
	$GTOOLS::TAG{'<!-- SEARCH_TERMS -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS'}:'';
	#$GTOOLS::TAG{'<!-- SEARCH_TERMS_1 -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS_1'}:'';
	#$GTOOLS::TAG{'<!-- SEARCH_TERMS_2 -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS_2'}:'';
	#$GTOOLS::TAG{'<!-- SEARCH_TERMS_3 -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS_3'}:'';
	#$GTOOLS::TAG{'<!-- SEARCH_TERMS_4 -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS_4'}:'';
	#$GTOOLS::TAG{'<!-- SEARCH_TERMS_5 -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SEARCH_TERMS_5'}:'';

	$GTOOLS::TAG{'<!-- USEDFOR -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'USEDFOR'}:'';
	$GTOOLS::TAG{'<!-- SUBJECTCONTENT -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'SUBJECTCONTENT'}:'';
	
	$GTOOLS::TAG{'<!-- ISGIFTWRAPAVAILABLE -->'} = qq~<select form="syndicationAmazonFrm" name="isgiftwrapavailable">~;
	if ($thesaurusinfo->{'ISGIFTWRAPAVAILABLE'} == 1) {
		$GTOOLS::TAG{'<!-- ISGIFTWRAPAVAILABLE -->'} .= qq~<option value=0>No</option>~.
																		qq~<option selected value=1>Yes</option>~;
		}
	else { 
		$GTOOLS::TAG{'<!-- ISGIFTWRAPAVAILABLE -->'} .= qq~<option select value=0>No</option>~.
                                                      qq~<option value=1>Yes</option>~;
		}
	$GTOOLS::TAG{'<!-- ISGIFTWRAPAVAILABLE -->'} .= "</select>";
	
	$GTOOLS::TAG{'<!-- ISGIFTMESSAGEAVAILABLE -->'} = qq~<select form="syndicationAmazonFrm" name="isgiftmessageavailable">~;
	if ($thesaurusinfo->{'ISGIFTMESSAGEAVAILABLE'} == 1) {
		$GTOOLS::TAG{'<!-- ISGIFTMESSAGEAVAILABLE -->'} .= qq~<option value=0>No</option>~.
																		qq~<option selected value=1>Yes</option>~;
		}
	else { 
		$GTOOLS::TAG{'<!-- ISGIFTMESSAGEAVAILABLE -->'} .= qq~<option select value=0>No</option>~.
                                                      qq~<option value=1>Yes</option>~;
		}
	$GTOOLS::TAG{'<!-- ISGIFTMESSAGEAVAILABLE -->'} .= "</select>";


	
	$GTOOLS::TAG{'<!-- OTHERATTRIBS -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'OTHERITEM'}:'';
	$GTOOLS::TAG{'<!-- TARGETAUDIENCE -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'TARGETAUDIENCE'}:'';
	$GTOOLS::TAG{'<!-- ADDITIONALATTRIBS -->'} = (defined $thesaurusinfo)?$thesaurusinfo->{'ADDITIONALATTRIBS'}:'';

	## link for webdoc
	my ($helplink, $helphtml) = GTOOLS::help_link('Amazon Thesaurus Profiles Webdoc', 50390);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;


	$help = '#50390';
	$template_file = 'thesaurus.shtml';
	push @BC, { 'name'=>'Thesaurus / Item Classification' };
	}


#################################################################################################
##
##	SHIPPING MAP
##

if ($VERB eq 'SHIPPING-SAVE') {
	print STDERR "VERB: $VERB\n";

	$VERB = 'SHIPPING';
		

	print STDERR "VERB: $VERB\n";
	my $mapref = ();
	foreach my $method ("Standard", "Expedited","Scheduled","NextDay","SecondDay") {
		$mapref->{$method}=$ZOOVY::cgiv->{$method};
		}

	my $map = ZTOOLKIT::buildparams($mapref);

	## old database location:
	#my $pstmt = "update AMAZON_FEEDS set SHIPPING_MAP = ".$udbh->quote($map);
	#$pstmt .= " where MID=$MID";
	#print STDERR $pstmt."\n";

	## new syndication object (where we load from)
	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	$so->set('.shipping',$map);
	$so->save();

	# $udbh->do($pstmt);
	}

if ($VERB eq 'SHIPPING') {

	print STDERR "VERB: $VERB\n";

	my ($so) = SYNDICATION->new($USERNAME,"#$PRT","AMZ");
	my $MAP = $so->get('.shipping');
	my $MAPREF = ZTOOLKIT::parseparams($MAP);

	# my $MAPREF = AMAZON3::fetch_shippingmap($USERNAME);
	## add FEDEX shipping methods
	#require ZSHIP::FEDEXAPI;
	#foreach my $value (values %ZSHIP::FEDEXAPI::DOM_NAMES) {
	#	my ($code, $pretty) = split(/\|/,$value);
	#	$shp_methods->{$code} = $pretty;
	#	}
	### add UPS shipping methods
	#require ZSHIP::UPSAPI;
	#foreach my $value (values %ZSHIP::UPSAPI::CODES) {
	#	my ($code, $pretty) = split(/\|/,$value);
	#	## skip intl methods for now
	#	next if ($pretty =~ /Canada/ || $pretty =~ /Worldwide/);
	#	$shp_methods->{$code} = $pretty;
	#	}
	### add USPS shipping methods
	#$shp_methods->{'ESPP'} = "U.S.P.S Standard Mail";
	#$shp_methods->{'EXPR'} = "U.S.P.S Express Mail";
	#$shp_methods->{'EPRI'} = "U.S.P.S Priority Mail";
	#
	#
	#print STDERR "SHP_METHODS: ".Dumper($shp_methods)."\n\n";

	$GTOOLS::TAG{'<!-- TITLE -->'} = 'Edit Shipping Map';

	my $c = '<table>';
	foreach my $amzshiptype ("Standard", "Expedited","Scheduled","NextDay","SecondDay") {
		$c .= "<tr><td>$amzshiptype</td><td><select name=$amzshiptype><option value=''>";
		require ZSHIP;
		foreach my $carrier (sort keys %ZSHIP::SHIPCODES) {
			my $method = $ZSHIP::SHIPCODES{$carrier}->{'method'};
			my $expedited = ($ZSHIP::SHIPCODES{$carrier}->{'expedited'})?'/expedited/':'';
			my $is_selected = ($carrier eq $MAPREF->{$amzshiptype})?'selected':'';
			$c .= qq~<option value="$carrier" $is_selected>[$carrier] $method $expedited</option>~;
			}
		$c .= "</select></td></tr>";
		}
	$c .= "</table>";

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;

	## link for webdoc
	my ($helplink, $helphtml) = GTOOLS::help_link('Amazon Shipping Map Webdoc', 50392);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;

	$help = '#50392';
	$template_file = 'shipping.shtml';
	push @BC, { 'name'=>'Shipping Map' };
	}





#################################################################################################
##
##
##

if ($VERB eq 'BROWSEPROFILES') {

	$template_file = 'browseprofiles.shtml';
	push @BC, { 'name'=>'Browse Tree Profiles' };
	}

#################################################################################################
##
##
##

if ($VERB eq 'ORDERS') {
	$template_file = 'orders.shtml';
	push @BC, { 'name'=>'Orders' };
	}

#################################################################################################
##
##
##

if ($VERB eq 'SELLERCENTRAL') {
	$template_file = 'sellercentral.shtml';
	push @BC, { 'name'=>'Seller Central' };
	}


#################################################################################################
##
##
## now called UPLOADS
if ($VERB eq 'PRODUCTS') {
	$template_file = 'products.shtml';
	
	my $pstmt = "select AMZ_MERCHANT_ID from AMAZON_FEEDS where PRT=$PRT and mid = ".$udbh->quote($MID);
	my $sth = $udbh->prepare($pstmt);
   $sth->execute();
	my ($amz_merchant_id) = $sth->fetchrow();
	$sth->finish;

	if ($amz_merchant_id eq '') {
		$GTOOLS::TAG{'<!-- MSG -->'} = "Unfortunately you do not currently have your 'Amazon Merchant ID' configured.".
				"This means this Upload report will not automatically update on a nightly basis. Please reference the ".
				"webdoc for instructions on finding and configuring this value.";
		}
	else {
		$GTOOLS::TAG{'<!-- MSG -->'} = "This Uploads report runs on a nightly basis. It is as accurate as possible, ie".
				" there have been reports of some categories not returning ASINs as they should. Please submit a ticket with ".
				"'Amazon Uploads report' in your subject if you need to report an issue.";
		}

	$pstmt = "select STATUS, PID, ASIN, from_unixtime(UPLOADED_GMT) DATE ".
					"from PID_UPCS where mid = ".$udbh->quote($MID).
					" order by substring(from_unixtime(UPLOADED_GMT), 1, 10) desc, PID";
	print STDERR $pstmt."\n";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();

	my $ctr = 1;
	my $removals = 0;
	my $errors = 0;
	my $c = "** Removed SKUs<br><br><center><table border=1 width=650 cellspacing=1><tr><th></th><th>SKU</th>".
	        "<th>Inv</th><th>ASIN</th><th>Update Time</th></tr>";

	my %skus = ();
	my @orders = ();
	while (my $hashref = $sth->fetchrow_hashref()) {
		$skus{$hashref->{'PID'}} = $hashref;
		push @orders, $hashref->{'DATE'}."|".$hashref->{'PID'};
		}

   my @pids = keys %skus;
   use INVENTORY;
	my ($invref,$reserveref,$locref) = INVENTORY::fetch_qty($USERNAME,\@pids);


	foreach my $order (reverse sort @orders) {
		my ($date, $pid) = split(/\|/,$order);
		my $hashref = $skus{$pid}; 
		my $qty = $invref->{$pid} - $reserveref->{$pid};

		my $note = '';
		if ($hashref->{'STATUS'} < 0) { 
			$note = '** '; 
			$hashref->{'ASIN'} = "removed"; 
			$removals++; 
			}

		$c .= qq~<tr><td>~.$ctr++.qq~</td>~.
				qq~<td>$note<a target="_new" href="/biz/product/edit.cgi?PID=$hashref->{'PID'}">$hashref->{'PID'}</a></td>~.
				qq~<td>$qty</td><td>~;
		if ($hashref->{'ASIN'} =~ /^[B|7]/) { $c .= qq~<a target="_new" href="http://www.amazon.com/o/ASIN/$hashref->{'ASIN'}">~; }
		elsif ($hashref->{'STATUS'} >= 0) { $errors++; }
		$c .=	qq~$hashref->{'ASIN'}</a></td><td>$date</td></tr>~;

		}
	$sth->finish;
	$c .= "</table></center>";

	$c .= "<br>Total Errors: $errors<br>"; 
	$c .= "<br>Total Removals: $removals<br>";
	$c .= "<br>Total Live: ".($ctr-$errors-$removals-1)."<br>";
	  
	$help = '#50393';
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	push @BC, { 'name'=>'Uploads' };
	}
	

#################################################################################################
##
##
##
if ($VERB eq 'LOGS') {

#mysql> desc SYNDICATION_PID_ERRORS;
#+-------------+----------------------+------+-----+---------+----------------+
#| Field       | Type                 | Null | Key | Default | Extra          |
#+-------------+----------------------+------+-----+---------+----------------+
#| ID          | int(10) unsigned     | NO   | PRI | NULL    | auto_increment |
#| CREATED_GMT | int(10) unsigned     | NO   |     | 0       |                |
#| ARCHIVE_GMT | int(10) unsigned     | NO   |     | 0       |                |
#| MID         | int(10) unsigned     | NO   | MUL | 0       |                |
#| DSTCODE     | varchar(3)           | NO   |     | NULL    |                |
#| PID         | varchar(20)          | NO   |     | NULL    |                |
#| SKU         | varchar(35)          | NO   |     | NULL    |                |
#| FEED        | smallint(5) unsigned | NO   |     | 0       |                |
#| ERRCODE     | int(10) unsigned     | NO   |     | 0       |                |
#| ERRMSG      | text                 | YES  |     | NULL    |                |
#| BATCHID     | bigint(20)           | NO   |     | 0       |                |
#+-------------+----------------------+------+-----+---------+----------------+
#11 rows in set (0.01 sec)

	$GTOOLS::TAG{'<!-- GUID -->'} = time();

#	my $pstmt = "select count(1),DOCID,CREATED_GMT,TYPE,MESSAGE,PRODUCT,MSGTYPE from SYNDICATION_ where MID=$MID /* $USERNAME */ and PRT=$PRT and CREATED_GMT>(unix_timestamp(now())-(86400*30)) and (type = 'ERR' or type = 'WARN') group by DOCID,CREATED_GMT,TYPE,MESSAGE order by created_gmt desc limit 0,500";
	require AMAZON3;

	my ($TB) = &ZOOVY::resolve_lookup_tb($USERNAME,$MID);
	my $pstmt = "select PID,SKU,AMZ_FEEDS_ERROR,AMZ_FEEDS_TODO,AMZ_ERROR from $TB where MID=$MID /* $USERNAME */ and AMZ_FEEDS_ERROR>0  order by AMZ_PRODUCTDB_GMT  desc limit 0,1000";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	
	my $c = '';
#	$c .= $pstmt;
	my $r = '';
	require TXLOG;
	while ( my ($product,$sku,$feed_error,$feed_todo,$errmsg) = $sth->fetchrow() ) {
		$r = ($r eq 'r0')?'r1':'r0';
		
		my $txmsgs = '';
		my $tx = TXLOG->new($errmsg);

		# $c .= "<tr><td>".Dumper($product,$sku,$feed_error,$feed_todo,$errmsg)."</td></tr>";

		foreach my $feed (split(/,/,&AMAZON3::describe_bw($feed_error))) {
			if ($feed eq 'init') { $feed = 'products'; }	## there are no errors for init per se.
			my ($UNI,$TS,$PARAMSREF) = $tx->get($feed);	
			my $txmsg = '';
			my $txmsgtype = '?';
			if (not defined $UNI) {
				$TS = 0;
				}
			else {
				$txmsg = $PARAMSREF->{'+'};
				if ($txmsg eq '') { $txmsg = 'No error message was provided'; }
				$txmsgtype = $PARAMSREF->{'_'};
				}
			$c .= "<tr class='$r'>".
				"<td nowrap valign=top>$product</td>".
				"<td nowrap valign=top>$sku</td>".
				"<td nowrap valign=top>".$feed."</td>".
				"<td nowrap valign=top>".(($TS==0)?'':&ZTOOLKIT::pretty_date($TS,2))."</td>".
				"<td valign=top>".$txmsgtype."</td>".
				"<td valign=top>".$txmsg."</td>".
				"</tr>";
			}
		}
	$sth->finish();

	if ($c eq '') { 
		$c .= "<tr><td colspan='6'><i>No log entries have been recorded in the last 30 days</i></td></tr>"; 
		}
	$c = qq~
<tr class="zoovytableheader">
	<th>PRODUCT</th>
	<th>SKU</th>
	<th>FEED</th>
	<th>DATE</th>
	<th>MSGTYPE</th>
	<th>MSG</th>
</tr>
$c
~;

	# $c = "<tr><td colspan=6>$pstmt</td></tr>$c";
	$GTOOLS::TAG{'<!-- LOGS -->'} = $c;
	
	$help = '#50393';
	$template_file = 'logs.shtml';	
	push @BC, { 'name'=>'Logs' };
	}

&GTOOLS::output('*LU'=>$LU,
   'title'=>'Amazon @Merchant Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>$help,
	'msgs'=>\@MSGS,
   'tabs'=>[
		{ name=>'Config', selected=>($VERB eq 'CONFIG')?1:0, link=>'/biz/syndication/amazon/index.cgi?VERB=CONFIG' },
#		{ name=>'Browse Profiles', link=>'index.cgi?VERB=BROWSEPROFILES' },
		{ name=>'Thesaurus', selected=>($VERB eq 'THESAURUS')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=THESAURUS' },
		{ name=>'Categories', selected=>($VERB eq 'CATEGORIES')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=CATEGORIES' },
		{ name=>'Logs', selected=>($VERB eq 'LOGS')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=LOGS', },
#		{ name=>'Uploads', link=>'index.cgi?VERB=PRODUCTS', },
#		{ name=>'Uploads',selected=>($VERB eq 'UPLOADS')?1:0,  link=>'/biz/batch/index.cgi?VERB=NEW&EXEC=REPORT&REPORT=AMAZON_UPLOADS&GUID='.time(), },
#		{ name=>'Orders', link=>'index.cgi?VERB=ORDERS', },
		{ name=>'Settlements', selected=>($VERB eq 'SETTLEMENTS')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=REPORTS', },
		{ name=>'Unconfirmed Orders',  selected=>($VERB eq 'UNCONFIRMED')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=UNCONFIRMED', },
		{ name=>'Shipping Map',  selected=>($VERB eq 'SHIPPING')?1:0,  link=>'/biz/syndication/amazon/index.cgi?VERB=SHIPPING', },
		{ name=>'Seller Central', link=>'/biz/syndication/amazon/index.cgi?VERB=SELLERCENTRAL', },
      ],
   'bc'=>\@BC,
   );


&DBINFO::db_zoovy_close();
&DBINFO::db_user_close();

