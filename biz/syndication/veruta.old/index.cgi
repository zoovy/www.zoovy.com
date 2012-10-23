#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
use strict;
use DOMAIN::TOOLS;
use SYNDICATION;
require PLUGIN::VERUTA;


my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$USERNAME = lc($USERNAME);
my $VERB = $ZOOVY::cgiv->{'VERB'};

my $template_file = 'index.shtml';

my @BC = (
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Veruta Remarketing',link=>'http://www.zoovy.com/biz/syndication/veruta','target'=>'_top', },
		);



my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
$GTOOLS::TAG{'<!-- PROFILE -->'} = $PROFILE;

my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'VRT');
my ($DOMAIN,$ROOTPATH) = $so->syn_info();
$DOMAIN =~ s/^www\.//g;
$GTOOLS::TAG{'<!-- DOMAIN -->'} = $DOMAIN;

if ($FLAGS =~ /,TRIAL,/) { $VERB = 'DENIED'; }
elsif ($FLAGS !~ /,WEB,/) { $VERB = 'DENIED'; }
elsif ($FLAGS !~ /,XSELL,/) { $VERB = 'DENIED'; }

if ($VERB eq 'DENIED') {
	$template_file = 'denied.shtml';
	}

if ($VERB eq 'WEBDOC') {
	$template_file = &GTOOLS::gimmewebdoc($LU,$ZOOVY::cgiv->{'DOC'});
	}

if ($VERB eq 'SETUP-NOW') {
	## don't let liz cheat anymore.
	# $so->set('.ticket',0);
	if ($so->get('.ticket')>0) { $VERB = 'EDIT'; }
	}

if ($VERB eq 'SETUP-NOW') {
	require PLUGIN::VERUTA;
	require JSON::XS;
	require SUPPORT;


	my $JOBTYPE = $ZOOVY::cgiv->{'jobtype'};
	my $VUSER = undef;
	if ($so->get('.user') ne '') {
		## we already have a userid.
		$VUSER = $so->get('.user');
		}
	elsif ($DOMAIN eq "$USERNAME.zoovy.com") { 
		$VUSER = "$USERNAME\@veruta.zoovy.net";
		}
	else {
		$VUSER = "$DOMAIN\@veruta.zoovy.net";
		}

	#my ($result) = PLUGIN::VERUTA::doRequest("Merchant.Get",{
	#	"Username"=>"$VUSER",
	#	},output=>'simple');

	my $VPASS = &ZTOOLKIT::make_password();
	my ($result) = PLUGIN::VERUTA::doRequest("Merchant.Create",{
		"Username"=>"$VUSER",
		"Password"=>$VPASS,
		"MerchantName"=>"$USERNAME",
		"DomainName"=>"$DOMAIN",
		"JSONConfiguration"=>JSON::XS::encode_json({"mid"=>$MID, "username"=>"$USERNAME"}),
		},output=>'simple');

	if (($result =~ /^fail/) && ($result =~ /5025/)) {
		## user already exists error
		my ($VMID) = &PLUGIN::VERUTA::resolve_vmid($VUSER);
		($result) = PLUGIN::VERUTA::doRequest("Merchant.Get",{
			MerchantID=>$VMID
			},output=>'simple');
		}

	print STDERR "RESULT:$result\n";

	if ($result =~ /^win\?(.*?)$/) {
		my $vresult = &ZTOOLKIT::parseparams($1);
		my $VMID = $vresult->{'.MerchantInfo.MerchantID'};
		$so->set('.user',$VUSER);
		$so->set('.pass',$VPASS);
		$so->set('.vmid',$VMID);

		my ($TICKET) = SUPPORT::createticket($USERNAME,
			'ORIGIN'=>'PROJECT',
			'DISPOSITION'=>'ACTIVE',
			BODY=>qq~
This project has been created to track the progress of your Veruta integration.

job: $JOBTYPE
domain: $DOMAIN
profile: $PROFILE (PRT: #$PRT)
contact: $LUSERNAME
veruta-user: $VUSER
veruta-pass: $VPASS
veruta-vmid: $VMID

Please paste any special instructions, or attach any artwork. 
~,
			PUBLIC=>1,
			SUBJECT=>"Veruta $JOBTYPE $DOMAIN",
			'TECH'=>'',
			);

		$so->set('.ticket',$TICKET);
		$so->save();

		my $NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
		$NSREF->{'veruta:config'} = &ZTOOLKIT::buildparams($so->userdata());
		&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);	

		#	print "TICKET: $TICKET\n";
		&SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'PPM','jerryc', STAGE=>'NEED_REVIEW' );

		## go through each campaign type and create the invidivual jobs and TID's in VERUTA
		my @NOTES = ();
		foreach my $param (keys %{$ZOOVY::cgiv}) {
			print STDERR "PARAM:$param\n";
			next unless ($param =~ /cpg\|(.*?)$/);
			my $cpgtype = $1;

			if ($JOBTYPE eq "EXPRESS") {
				&SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'EXP_VERUTA','jerryc', STAGE=>'DESIGN' );
				}
			else {
				&SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'CSTM_VERUTA','jerryc', STAGE=>'DESIGN' );
				&SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'BLD_VERUTA','jt', STAGE=>'PENDING' );				
				}

			foreach my $dim ('728x90','300x250','160x600') {
				my ($TID) = &PLUGIN::VERUTA::create_template($USERNAME,$VMID);
				my ($NOTE) = "TID:$TID|DIM:$dim|TYPE:$cpgtype|PROFILE:$PROFILE";
				my ($TASKID) = &SUPPORT::add_task_to_ticket($USERNAME,$TICKET,'VERUTA_JOB','', STAGE=>'NEW', NOTE=>$NOTE);
				$NOTE = "$NOTE|TASK:$TASKID";
				push @NOTES, $NOTE;
				}
			}
		

		open MH, "|/usr/lib/sendmail -t";
		print MH "From: $USERNAME <ticket+$TICKET\@support.zoovy.com>\n";
		print MH "To: billing\@zoovy.com\n";
		print MH "Subject: $USERNAME veruta $DOMAIN $JOBTYPE\n\n";
		print MH "\n\nDOMAIN: $DOMAIN\nJOBTYPE: $JOBTYPE\n Peek URL:\n";
		print MH "https://admin.zoovy.com/support/index.cgi?ACTION=FINDTICKET&CUSTOMER=$USERNAME&TICKET=$TICKET\n";
		use Data::Dumper;
		print MH "\nVERUTA-USER: $VUSER\nVERUTA-PASS: $VPASS\nVERUTA-MID: $VMID\n";
		print MH "\nVERUTA-API-RESULT\n".Dumper()."\n";
		print MH join("\n",@NOTES);
		close MH;

		$VERB = 'EDIT';
		## created veruta account.
		}
	else {
		$VERB = 'SETUP';
		$result =~ s/^fail\?//g;
		my $msgref = &ZTOOLKIT::parseparams($result);
		$GTOOLS::TAG{'<!-- ERROR -->'} = $msgref->{'msg'};
		}
	}





if ($VERB eq 'BILLING') {
#mysql> desc BS_VERUTA;
#+--------------------+------------------+------+-----+---------+----------------+
#| Field              | Type             | Null | Key | Default | Extra          |
#+--------------------+------------------+------+-----+---------+----------------+
#| ID                 | int(10) unsigned | NO   | PRI | NULL    | auto_increment |
#| USERNAME           | varchar(20)      | NO   |     | NULL    |                |
#| MID                | int(11)          | NO   | MUL | 0       |                |
#| DOMAIN             | varchar(65)      | NO   |     | NULL    |                |
#| VMID               | int(10) unsigned | NO   | MUL | 0       |                |
#| YEARMONWK          | decimal(8,0)     | NO   |     | 0       |                |
#| STARTYYYMMDD       | int(10) unsigned | NO   |     | 0       |                |
#| ENDYYYMMDD         | int(10) unsigned | NO   |     | 0       |                |
#| Page_Views         | int(10) unsigned | NO   |     | 0       |                |
#| Visits             | int(10) unsigned | NO   |     | 0       |                |
#| Impressions        | int(10) unsigned | NO   |     | 0       |                |
#| Conversions        | int(10) unsigned | NO   |     | 0       |                |
#| Engagements        | int(10) unsigned | NO   |     | 0       |                |
#| Clicks             | int(10) unsigned | NO   |     | 0       |                |
#| Banner_MouseOvers  | int(10) unsigned | NO   |     | 0       |                |
#| Product_MouseOvers | int(10) unsigned | NO   |     | 0       |                |
#| Scroll_MouseOvers  | int(10) unsigned | NO   |     | 0       |                |
#| CPE_Spend          | decimal(8,2)     | NO   |     | 0.00    |                |
#| CPM_Spend          | decimal(8,2)     | NO   |     | 0.00    |                |
#| Flat_Spend         | decimal(8,2)     | NO   |     | 0.00    |                |
#| ORDER_COUNT        | int(10) unsigned | NO   |     | 0       |                |
#| ORDER_SUBTOTAL     | decimal(10,2)    | NO   |     | 0.00    |                |
#| CPA_Spend          | decimal(8,2)     | NO   |     | 0.00    |                |
#| BS_TXN             | int(10) unsigned | NO   |     | 0       |                |
#+--------------------+------------------+------+-----+---------+----------------+
#24 rows in set (0.01 sec)

	my ($zdbh) = &DBINFO::db_zoovy_connect();
	my $pstmt = "select * from BS_VERUTA where MID=$MID /* $USERNAME */ order by YEARMONWK";
	my $sth = $zdbh->prepare($pstmt);
	$sth->execute();
	my $c = '';
	while ( my $vref = $sth->fetchrow_hashref() ) {
		$c .= '<tr>';
		$c .= "<td>$vref->{'STARTYYYMMDD'}</td>";
		$c .= "<td>$vref->{'ENDYYYMMDD'}</td>";
		$c .= "<td>$vref->{'Page_Views'}</td>";
		$c .= "<td>$vref->{'Visits'}</td>";
		$c .= "<td>$vref->{'Impressions'}</td>";
		$c .= "<td>$vref->{'Conversions'}</td>";
		$c .= "<td>$vref->{'Engagements'}</td>";
		$c .= "<td>$vref->{'Clicks'}</td>";
		$c .= "<td>$vref->{'Banner_MouseOvers'}</td>";
		$c .= "<td>$vref->{'Product_MouseOvers'}</td>";
		$c .= "<td>$vref->{'Scroll_MouseOvers'}</td>";
		$c .= "<td>$vref->{'CPE_Spend'}</td>";
		$c .= "<td>$vref->{'CPM_Spend'}</td>";
		$c .= "<td>$vref->{'Flat_Spend'}</td>";
		$c .= "<td>$vref->{'ORDER_COUNT'}</td>";
		$c .= "<td>$vref->{'ORDER_SUBTOTAL'}</td>";
		$c .= "<td>$vref->{'CPA_Spend'}</td>";
		$c .= '</tr>';
		}
	$sth->finish();

	$c = q~
<tr class='zoovysub1header'>
	<td>START YYYY-MM-DD</td>
	<td>END YYYY-MM-DD</td>
	<td>Page Views</td>
	<td>Visits</td>
	<td>Impressions</td>
	<td>Conversions</td>
	<td>Engagements</td>
	<td>Clicks</td>
	<td>Banner MouseOvers</td>
	<td>Product MouseOvers</td>
	<td>Scroll MouseOvers</td>
	<td>CPE Spend</td>
	<td>CPM Spend</td>
	<td>Flat Spend</td>
	<td>Order Count</td>
	<td>Order Subtotal</td>
	<td>CPA Spend</td>
</tr>
~.$c;

	$GTOOLS::TAG{'<!-- BILLING -->'} = $c;
	&DBINFO::db_zoovy_close();

	$template_file = 'billing.shtml';
	}



if ($VERB eq 'SAVE') {
	tie my %s, 'SYNDICATION', THIS=>$so;

#	$s{'.ftp_user'} = $ZOOVY::cgiv->{'user'};	
#	$s{'.ftp_pass'} = $ZOOVY::cgiv->{'pass'};	
#	$s{'.ftp_server'} = $ZOOVY::cgiv->{'ftpserver'};	
#	$s{'.ftp_server'} =~ s/^ftp\:\/\///igs;
	$s{'.tag_products'} = (defined $ZOOVY::cgiv->{'veruta:tag_products'})?1:0;
	$s{'.tag_category'} = (defined $ZOOVY::cgiv->{'veruta:tag_category'})?1:0;
	$s{'.tag_cart'} = (defined $ZOOVY::cgiv->{'veruta:tag_cart'})?1:0;
	$s{'.tag_checkout'} = (defined $ZOOVY::cgiv->{'veruta:tag_checkout'})?1:0;
	$s{'.stop_checkout'} = (defined $ZOOVY::cgiv->{'veruta:stop_checkout'})?1:0;
	$s{'.stop_login'} = (defined $ZOOVY::cgiv->{'veruta:stop_login'})?1:0;
	$s{'.probability'} = int($ZOOVY::cgiv->{'veruta:probability'});
	$s{'.minevents'} = int($ZOOVY::cgiv->{'veruta:minevents'});
	$s{'.scheduleperiod'} = $ZOOVY::cgiv->{'scheduleperiod'};


	if ($s{'.vmid'} eq '') {
		$LU->log("SETUP.PLUGIN","Nuked VERUTA for profile $PROFILE","SAVE");
	   $so->nuke();
		}
	else {
		$LU->log("SETUP.PLUGIN","Enabled VERUTA for profile $PROFILE","SAVE");
		$so->set('IS_ACTIVE',1);
		$so->save();
		}

	$s{'.schedule'} = undef;
   if ($FLAGS =~ /,WS,/) {
		$s{'.schedule'} = $ZOOVY::cgiv->{'schedule'};
      }

	my $ERROR = '';

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		$s{'IS_ACTIVE'} = 1;
		$so->save();
		}

	my $NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);
	if ($s{'IS_ACTIVE'}) {
		$NSREF->{'veruta:config'} = &ZTOOLKIT::buildparams($so->userdata());
		}
	else {
		delete $NSREF->{'veruta:config'};
		}
	&ZOOVY::savemerchantns_ref($USERNAME,$PROFILE,$NSREF);

	$VERB = 'EDIT';
	}


if ($VERB eq 'DELETE') {
   my $PROFILE = $ZOOVY::cgiv->{'PROFILE'};
   my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'VRT');
   $so->nuke();
   $VERB = '';
   }



##
## 
## 
if ($VERB eq 'EDIT') {
	tie my %s, 'SYNDICATION', THIS=>$so;

	my $NSREF = &ZOOVY::fetchmerchantns_ref($USERNAME,$PROFILE);

	$GTOOLS::TAG{'<!-- VERUTA_MERCHANTID -->'} = $s{'.vmid'};
	$GTOOLS::TAG{'<!-- CHK_VERUTA_TAG_PRODUCTS -->'} = &ZOOVY::incode($s{'.tag_products'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_VERUTA_TAG_CATEGORY -->'} = &ZOOVY::incode($s{'.tag_category'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_VERUTA_TAG_CART -->'} = &ZOOVY::incode($s{'.tag_cart'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_VERUTA_TAG_CHECKOUT -->'} = &ZOOVY::incode($s{'.tag_checkout'}?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_STOP_CHECKOUT -->'} = int($s{'.stop_checkout'})?'checked':'';
	$GTOOLS::TAG{'<!-- CHK_STOP_LOGIN -->'} = int($s{'.stop_login'})?'checked':'';

	$GTOOLS::TAG{'<!-- FEED_STATUS -->'} = $so->statustxt();

	my $c = '<option value="">Not Set</option>';
   require WHOLESALE;
	foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
  	   $c .= "<option ".(($s{'.schedule'} eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
      }
	$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;

	my @PERIODS = ();
	push @PERIODS, "0|No Expiration";
	push @PERIODS, "30|30 Minutes";
	push @PERIODS, "59|59 Minutes";
	push @PERIODS, "60|1 Hour";
	push @PERIODS, "120|2 Hours";
	push @PERIODS, "180|3 Hours";
	push @PERIODS, "240|4 Hours";
	push @PERIODS, "300|5 Hours";
	push @PERIODS, "360|6 Hours";
	push @PERIODS, "480|8 Hours";
	push @PERIODS, "600|10 Hours";
	push @PERIODS, "720|12 Hours";
	foreach my $p (@PERIODS) {
		my ($min,$txt) = split(/\|/,$p);
		my $selected = ($s{'.scheduleperiod'} == $min)?'selected':'';
		$GTOOLS::TAG{'<!-- PERIOD -->'} .= "<option $selected value=\"$min\">$txt</option>";
		}

	
	my @PROBABILITIES = (100,50,33,25,20,10,5,1,0);
	foreach my $p (@PROBABILITIES) {
		$GTOOLS::TAG{"<!-- OPT_PROBABILITY_$p -->"} = ($s{'.probability'} eq $p)?'selected':'';
		}	

	my @MINEVENTS = (1,2,3,4,5);
	foreach my $p (@MINEVENTS) {
		$GTOOLS::TAG{"<!-- OPT_MINEVENTS_$p -->"} = ($s{'.minevents'} eq $p)?'selected':'';
		}	


	$GTOOLS::TAG{'<!-- VERUTA_LOGIN -->'} = &ZOOVY::incode($s{'.user'});
	$GTOOLS::TAG{'<!-- VERUTA_PASSWORD -->'} = &ZOOVY::incode($s{'.pass'});
	$GTOOLS::TAG{'<!-- VERUTA_MERCHANTID -->'} = &ZOOVY::incode($s{'.vmid'});

	

	$GTOOLS::TAG{'<!-- STATUS -->'} = $so->statustxt();
	if ($s{'IS_ACTIVE'}==0) {
		$GTOOLS::TAG{'<!-- STATUS -->'} = qq~<div class="error">Inactive Feed / None-Submitted. Campaigns will not operate properly (no products or navigation will appear, no updates to product database will be performed).</div>~;
		}
	$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
	$GTOOLS::TAG{'<!-- FILENAME -->'} = $so->filename();

#	my ($result) = PLUGIN::VERUTA::doRequest("Password.Get",{
#		MerchantID=>$s{'.vmid'}
#		},output=>'raw');
#	$GTOOLS::TAG{'<!-- STATUS -->'} = Dumper($result);
#	open F, ">/tmp/foo2";
#	print F Dumper($s{'.vmid'}, $result);
# 	close F;

	if ($FLAGS =~ /,WS,/) {
		my $c = '';
		require WHOLESALE;
		$c = "<option value=\"\">None</option>";
		foreach my $sch (@{&WHOLESALE::list_schedules($USERNAME)}) {
			$c .= "<option ".(($s{'.schedule'} eq $sch)?'selected':'')." value=\"$sch\">$sch</option>\n";
			}
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;
		}
	else { 
		$s{'.schedule'} = '';
		$GTOOLS::TAG{'<!-- SCHEDULE -->'} = '<option value="">Not Available</option>'; 
		}

	push @BC, { name=>'Profile: '.$PROFILE };
	$template_file = 'edit.shtml';
	}



if ($VERB eq 'LOGS') {
   $GTOOLS::TAG{'<!-- LOGS -->'} = $so->summarylog();
   $template_file = '_/syndication-logs.shtml';
   }



if ($VERB eq 'NEW_BANNER') {
	## where VERUTA will send a person when they need to setup a new campaign.
	$VERB = 'SETUP';
	}



if ($VERB eq 'SETUP') {
	($GTOOLS::TAG{'<!-- IS_STAFF -->'}, $GTOOLS::TAG{'<!-- END_STAFF -->'}) = ('<!--','-->');
	if ($LU->is_zoovy()) {
		($GTOOLS::TAG{'<!-- IS_STAFF -->'}, $GTOOLS::TAG{'<!-- END_STAFF -->'}) = ('','');
		}
	$template_file = 'setup.shtml';
	}


if ($VERB eq 'LEARN') {
	$template_file = 'learn.shtml';
	}


if ($VERB eq '') {
	my $profref = &DOMAIN::TOOLS::syndication_profiles($USERNAME,PRT=>$PRT);
	my $c = '';
	my $cnt = 0;
	my $ts = time();
	foreach my $ns (sort keys %{$profref}) {
		my $class = ($cnt++%2)?'r0':'r1';
		$c .= "<tr>";
		$c .= "<td class=\"$class\"><b>$ns =&gt; $profref->{$ns}</b><br>";

		my ($s) = SYNDICATION->new($USERNAME,$ns,'VRT');
		if ($s->get('.user') eq '') {
			$c .= "<i>No veruta account found.</i><br>";
			$c .= "&#187; <a href=\"index.cgi?VERB=LEARN&PROFILE=$ns\">LEARN MORE</a><br>";
			$c .= "&#187; <a href=\"index.cgi?VERB=SETUP&PROFILE=$ns\">SETUP ACCOUNT</a><br>";
			$c .= "<br>";
			}
		else {
			$c .= "<i>Username: ".$s->get('.user')."</i><br>";
			$c .= "&#187; <a href=\"index.cgi?VERB=EDIT&PROFILE=$ns\">EDIT</a><br>";
			$c .= "&#187; <a href=\"/biz/batch/index.cgi?VERB=ADD&EXEC=SYNDICATION&DST=VRT&PROFILE=$ns&GUID=$ts\">PUBLISH</a><br>";
			$c .= "&#187; Status: ".$s->statustxt()."<br>";
			}
		$c .= "</td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- PROFILES -->'} = $c;
	$template_file = 'index.shtml';
	}


if ($VERB eq 'CATEGORIES') {
	}

if ($VERB eq 'CAMPAIGNS') {
	require PLUGIN::VERUTA;

	$template_file = 'campaigns.shtml';	
	}


my @TABS = ();
push @TABS, { name=>"Profiles", selected=>($VERB eq '')?1:0, link=>"?VERB=", };
if ($PROFILE ne '') {
	push @TABS, { name=>"Config", selected=>($VERB eq 'EDIT')?1:0, link=>"?VERB=EDIT&PROFILE=".$PROFILE, };
	push @TABS, { name=>"Campaigns", selected=>($VERB eq 'CAMPAIGNS')?1:0, link=>"?VERB=CAMPAIGNS&PROFILE=".$PROFILE, };
	push @TABS, { selected=>($VERB eq 'LOGS')?1:0, 'name'=>'Logs', 'link'=>'index.cgi?VERB=LOGS&PROFILE='.$PROFILE };
	push @TABS, { selected=>($VERB eq 'BILLING')?1:0, 'name'=>'Billing', 'link'=>'index.cgi?VERB=BILLING&PROFILE='.$PROFILE };
	push @TABS, { name=>"Webdoc", selected=>($VERB eq 'WEBDOC')?1:0, link=>"?VERB=WEBDOC&DOC=51420&PROFILE=".$PROFILE, };
	}

&GTOOLS::output(
   'title'=>'Veruta Syndication',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#51420',
   'tabs'=>\@TABS,
   'bc'=>\@BC,
   );

&DBINFO::db_zoovy_close();

