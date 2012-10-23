#!/usr/bin/perl

use lib "/httpd/modules";
use strict;
require GTOOLS;
require ZOOVY;
require ZWEBSITE;
require LUSER;
require SITE;
require SITE::EMAILS;

#use URI::Escape;
use Data::Dumper;

my ($LU) = LUSER->authenticate();
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }

my ($VERB) = $ZOOVY::cgiv->{'VERB'};
if ($VERB eq '') { $VERB = 'EDIT'; }

my ($NS) = $ZOOVY::cgiv->{'NS'};
$GTOOLS::TAG{'<!-- NS -->'} = $NS;
my @TABS = ();

my $template_file = '';
my ($SITE) = SITE->new($USERNAME,'PROFILE'=>$NS,'PRT'=>$PRT);
my ($SE) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE,RAW=>1);

if ($VERB eq 'MSGNUKE') {
	my $MSGID = $ZOOVY::cgiv->{'MSGID'};
	$SE->save($MSGID,"NUKE"=>1);
	$VERB = 'EDIT';
	}

##
##
##
if ($VERB eq 'MSGTEST') {
	my $MSGID = $ZOOVY::cgiv->{'MSGID'};
	my ($err) = $SE->send($MSGID,TEST=>1,TO=>$ZOOVY::cgiv->{'MSGFROM'});
	$VERB = 'MSGEDIT';

	if ($err) {
		my $errmsg = $SITE::EMAILS::ERRORS{$err};
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<font color='red'>ERROR[$err] $errmsg</font><br>";
		}
	else {
		$GTOOLS::TAG{'<!-- ERROR -->'} = '<font color="blue">Successfully sent test email.</font>';
		}
	}

##
##
##
if ($VERB eq 'MSGSAVE') {
	## 
	my $MSGID = $ZOOVY::cgiv->{'MSGID'};

	my %options = ();
	$options{'SUBJECT'} = $ZOOVY::cgiv->{'MSGSUBJECT'};
	$options{'BODY'} = $ZOOVY::cgiv->{'MSGBODY'};
	if (defined $ZOOVY::cgiv->{'MSGTYPE'}) {
		$options{'TYPE'} = $ZOOVY::cgiv->{'MSGTYPE'};
		}
	if (defined $ZOOVY::cgiv->{'MSGBCC'}) {
		$options{'BCC'} = $ZOOVY::cgiv->{'MSGBCC'};
		}
	if (defined $ZOOVY::cgiv->{'MSGFROM'}) {
		$options{'FROM'} = $ZOOVY::cgiv->{'MSGFROM'};
		}

	$options{'FORMAT'} = 'HTML';
	if (defined $ZOOVY::cgiv->{'MSGFORMAT'}) {
		$options{'FORMAT'} = $ZOOVY::cgiv->{'MSGFORMAT'};
		}
	
	$GTOOLS::TAG{'<!-- ERROR -->'} = '<font color="blue">Successfully saved.</font>';
	
	$SE->save($MSGID, %options);
	$VERB = 'MSGEDIT';
	}

##
##
##
if ($VERB eq 'MSGEDIT') {
	my $MSGID = $ZOOVY::cgiv->{'MSGID'};
	my $msgref = $SE->getref($MSGID);
	
	$GTOOLS::TAG{'<!-- MSGTYPE -->'} = $msgref->{'MSGTYPE'};
	$GTOOLS::TAG{'<!-- MSGID -->'} = uc($MSGID);
	$GTOOLS::TAG{'<!-- MSGSUBJECT -->'} = &ZOOVY::incode($msgref->{'MSGSUBJECT'});

	$GTOOLS::TAG{'<!-- MSGFORMAT_HTML -->'} = ($msgref->{'MSGFORMAT'} eq 'HTML')?'checked':'';
	$GTOOLS::TAG{'<!-- MSGFORMAT_WIKI -->'} = ($msgref->{'MSGFORMAT'} eq 'WIKI')?'checked':'';
	$GTOOLS::TAG{'<!-- MSGFORMAT_TEXT -->'} = ($msgref->{'MSGFORMAT'} eq 'TEXT')?'checked':'';

	$GTOOLS::TAG{'<!-- MSGBODY -->'} = &ZOOVY::incode($msgref->{'MSGBODY'});
	$GTOOLS::TAG{'<!-- MSGFROM -->'} = &ZOOVY::incode($msgref->{'MSGFROM'});
	$GTOOLS::TAG{'<!-- MSGBCC -->'} = &ZOOVY::incode($msgref->{'MSGBCC'});
	$GTOOLS::TAG{'<!-- CREATED -->'} = &ZTOOLKIT::pretty_date($msgref->{'CREATED_GMT'},1);

	foreach my $mline (@SITE::EMAILS::MACRO_HELP) {
		my $show = 0;
		if ($mline->[0] eq $msgref->{'MSGTYPE'}) { $show |= 1; }
		elsif (($msgref->{'MSGTYPE'} eq 'TICKET') && ($mline->[0] eq 'CUSTOMER')) { $show |= 1; }
		elsif (($msgref->{'MSGTYPE'} eq 'TICKET') && ($mline->[0] eq 'ORDER')) { $show |= 2; } # 2 = selective availability

		if ($show) {
		$GTOOLS::TAG{'<!-- MACROHELP -->'} .= 
			sprintf(q~<tr>
			<td class="av" valign="top">%s</td>
			<td class="av" valign="top">%s%s</td>
			</tr>~,
			&ZOOVY::incode($mline->[1]), 
			$mline->[2],
			((($show&2)==2)?'<div class="hint">Note: will only appear when properly associated.</div>':'')
			 );
			}
		}

	$template_file = 'msgedit.shtml';	
	}

##
##
##
if ($VERB eq 'EDIT') {
	$template_file = 'edit.shtml';

	my ($SE) = SITE::EMAILS->new($USERNAME,'*SITE'=>$SITE,RAW=>1);
	my $result = $SE->available("");	
	foreach my $TYPE ('ORDER','ACCOUNT','INCOMPLETE','PRODUCT','TICKET') {
		my $c = '';
		my $r = 0;
		my %MSGIDS = ();
		foreach my $msgref (@{$result}) {
			next if ($TYPE ne $msgref->{'MSGTYPE'});
			$MSGIDS{ $msgref->{'MSGID'} } = $msgref;
			}

		## we sort by MSGID
		foreach my $k (sort keys %MSGIDS) {
			my $msgref = $MSGIDS{$k};
			my $title = "SUBJECT: $msgref->{'MSGSUBJECT'}";
			if ($msgref->{'MSGTITLE'} ne '') { $title = "TITLE: $msgref->{'MSGTITLE'}"; }

			if (not defined $msgref->{'MSGFORMAT'}) { $msgref->{'MSGFORMAT'} = 'HTML'; }

			$r = ($r eq 'r0')?'r1':'r0';
			$c .= "<tr class='$r'>";
			$c .= "<td width='50px'><input type='button' class='button' value=' Edit ' onClick=\"document.location='index.cgi?NS=$NS&VERB=MSGEDIT&MSGID=".$msgref->{'MSGID'}."'\"></td>";
			$c .= "<td width='100px'>".&ZOOVY::incode($msgref->{'MSGID'})."</td>";
			$c .= "<td>".&ZOOVY::incode($title)."</td>";
			if (not defined $msgref->{'CREATED_GMT'}) { $msgref->{'CREATED_GMT'} = 0; }
			$c .= "<td width='100px'>".&ZTOOLKIT::pretty_date($msgref->{'CREATED_GMT'})."</td>";
			$c .= "<td width='100px'>".$msgref->{'MSGFORMAT'}."</td>";
			$c .= "</tr>";
			}
		$GTOOLS::TAG{"<!-- $TYPE -->"} .= $c;
		}
	# $GTOOLS::TAG{'<!-- ORDER -->'} = Dumper($result);

	}

if ($VERB eq 'ADD') {
	$GTOOLS::TAG{'<!-- NS -->'} = $NS;
	$template_file = 'add.shtml';
	}


push @TABS, { name=>'Select', link=>"/biz/setup/builder/themes/index.cgi?SUBTYPE=E&NS=$NS", selected=>(($VERB eq 'SELECT')?1:0) };
push @TABS, { name=>'Edit', link=>"/biz/setup/builder/emails/index.cgi?VERB=EDIT&NS=$NS", selected=>(($VERB eq 'EDIT')?1:0)  };
push @TABS, { name=>'Add', link=>"/biz/setup/builder/emails/index.cgi?VERB=ADD&NS=$NS", selected=>(($VERB eq 'ADD')?1:0)  };

my @BC = ();
push @BC, { name=>"Setup", link=>'/biz/setup' };
push @BC, { name=>"Builder", link=>'/biz/setup/builder' };
push @BC, { name=>"Emails", link=>'/biz/setup/builder/emails' };

&GTOOLS::output(file=>$template_file,header=>1,tabs=>\@TABS, bc=>\@BC);

