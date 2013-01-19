#!/usr/bin/perl

use lib "/httpd/modules"; 
use CGI;
use GTOOLS;
use ZOOVY;
use ZWEBSITE;	
use IMGLIB;	
use ZTOOLKIT;
use DBINFO;
use NAVCAT;
require WHOLESALE;
use strict;

my $dbh = &DBINFO::db_zoovy_connect();	
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $q = new CGI;
my $ACTION = $q->param('ACTION');

my $template_file = 'index.shtml';
if ($FLAGS !~ /,WS,/) {
	$template_file = 'deny.shtml';
	$ACTION = 'DENY';
	}

if ($ACTION eq 'SAVE') {
	my $ERROR = '';

	## need to add validation
	if ($q->param('ABOUT') eq '') { $ERROR .= "About is a required.<br>"; }
	if ($q->param('PHONE') eq '') { $ERROR .= "Phone is a required.<br>"; }
	if ($q->param('EMAIL') eq '') { $ERROR .= "Email is a required.<br>"; }

	if ($ERROR ne '') {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>$ERROR</font>";
		}
	else {
		my $pstmt = "select count(*) from BTC_FEEDS where MID=$MID /* $USERNAME */";
		my $sth = $dbh->prepare($pstmt);
		$sth->execute();
		my ($count) = $sth->fetchrow();
		$sth->finish();

		## insert into BTC_FEEDS as neccessary	
		if ($count == 0) { 
			my $pstmt = "insert into BTC_FEEDS (MID) values (?)";
			$dbh->do($pstmt, undef, $MID);
			}
	
#+----------+---------------------+------+-----+---------+-------+
#| Field    | Type                | Null | Key | Default | Extra |
#+----------+---------------------+------+-----+---------+-------+
#| MID      | int(10) unsigned    |      | PRI | 0       |       |
#| USERNAME | varchar(20)         |      |     |         |       |
#| COMPANY  | varchar(60)         |      |     |         |       |
#| LOGO     | varchar(40)         |      |     |         |       |
#| ABOUT    | varchar(255)        |      |     |         |       |
#| PHONE    | varchar(12)         |      |     |         |       |
#| EMAIL    | varchar(65)         |      |     |         |       |
#| PREMIUM  | tinyint(3) unsigned |      |     | 0       |       |
#+----------+---------------------+------+-----+---------+-------+
#8 rows in set (0.01 sec)

		## update data
		my $pstmt = "update BTC_FEEDS set USERNAME=?,COMPANY=?,LOGO=?,ABOUT=?,EMAIL=?,PHONE=? ".
						"where MID=$MID /* $USERNAME */";
		$dbh->do($pstmt, undef, $USERNAME,$q->param('COMPANY'),$q->param('LOGO'),$q->param('ABOUT'),
			$q->param('EMAIL'),$q->param('PHONE'));

		## update category/product info
		my $changed = 0;	
		my $NC = NAVCAT->new($USERNAME);
		foreach my $safe ($NC->paths()) {
			next if (not defined $q->param('navcat-'.$safe));
			# next if ($q->param('navcat-'.$safe) eq '');
			my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
			next if ($metaref->{'BIZRATE_CAT'} eq $q->param('navcat-'.$safe));
			$metaref->{'BIZRATE_CAT'} = $q->param('navcat-'.$safe);
			$NC->set($safe,metaref=>$metaref);
			}
		$NC->save();

		if ($changed) {
		
			}

		&ZWEBSITE::save_website_attrib($USERNAME,'buythecase',time());
		$ACTION = '';
		}
	}

####
if ($ACTION eq '') {
	my $hashref = {};
	my $pstmt = "select * from BTC_FEEDS where MID=$MID";
	my $sth = $dbh->prepare($pstmt);
	$sth->execute();
	my $BREF = $sth->fetchrow_array();
	
	## user hasn't saved this data
	if ($BREF->{'COMPANY'}  eq ''){ ## get user info 
		$GTOOLS::TAG{"<!-- COMPANY -->"} = ZOOVY::fetchmerchant_attrib($USERNAME,"zoovy:company_name");
		$GTOOLS::TAG{"<!-- LOGO -->"} = ZWEBSITE::nice_url_handler(&ZOOVY::fetchmerchant_attrib($MERCHANT,"zoovy:company_logo"));
		$GTOOLS::TAG{'<!-- ABOUT -->'} = 
		$GTOOLS::TAG{"<!-- EMAIL -->"} = ZOOVY::fetchmerchant_attrib($MERCHANT,"zoovy:email");
		$GTOOLS::TAG{"<!-- PHONE -->"} = ZOOVY::fetchmerchant_attrib($MERCHANT,"zoovy:phone");
		}
				
	$GTOOLS::TAG{'<!-- COMPANY -->'} = $BREF->{'COMPANY'}?$BREF->{'COMPANY'}:'';
	$GTOOLS::TAG{'<!-- LOGO -->'} = $BREF->{'LOGO'}?$BREF->{'LOGO'}:'';
	$GTOOLS::TAG{'<!-- ABOUT -->'} = $BREF->{'ABOUT'}?$BREF->{'ABOUT'}:'';
	$GTOOLS::TAG{'<!-- PHONE -->'} = $BREF->{'PHONE'}?$BREF->{'PHONE'}:'';
	$GTOOLS::TAG{'<!-- EMAIL -->'} = $BREF->{'EMAIL'}?$BREF->{'EMAIL'}:'';
	

	my $c = '<option value="">Not Set</option>';
	foreach my $s (@{&WHOLESALE::list_schedules($USERNAME)}) {
		$c .= "<option ".(($hashref->{'SCHEDULE'} eq $s)?'selected':'')." value=\"$s\">$s</option>\n";
		}
	$GTOOLS::TAG{'<!-- SCHEDULE -->'} = $c;

	my $c = '';
	use Data::Dumper;
	my $NC = NAVCAT->new($USERNAME);
	foreach my $safe (sort $NC->paths()) {
		next if (substr($safe,0,1) eq '*');
		next if ($safe eq '');
		my ($pretty, $children, $productstr, $sortby, $metaref) = $NC->get($safe);
		print STDERR "META: $meta\n";
		next if (substr($pretty,0,1) eq '!');

		my $name = ''; 
		if ($pretty eq '') { $pretty = "UN-NAMED: $safe"; }
		if (substr($safe,0,1) eq '.') {
			foreach (split(/\./,$safe)) { $name .= "&nbsp; - &nbsp; "; } $name .= $pretty;
			if ($safe eq '.') { $name = 'HOMEPAGE'; }
			}
		elsif (substr($safe,0,1) eq '$') {
			$name = "LIST: ".$pretty;
			}	
		my $val = $metaref->{'BIZRATE_CAT'};
		$c .= "<tr><td nowrap>$name</td><td><input type='textbox' size='10' name='navcat-$safe' value='$val'></td></tr>\n";
		}
	if ($c eq '') { $c = '<tr><td><i>No website categories exist??</i></td></tr>'; }
	$GTOOLS::TAG{'<!-- CATEGORIES -->'} = $c;
	undef $NC;
	}

&GTOOLS::output(
  	'title'=>'Buy the Case Syndication',
  	'file'=>$template_file,
  	'header'=>'1',
  	'help'=>'detail/setup-buythecase.php',
   'tabs'=>[
      ],
   'bc'=>[
      { name=>'Syndication',link=>'http://www.zoovy.com/biz/syndication','target'=>'_top', },
      { name=>'Buy the Case',link=>'http://www.zoovy.com/biz/syndication/buythecase','target'=>'_top', },
      ],
   );

&DBINFO::db_zoovy_close();

