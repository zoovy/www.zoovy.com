#!/usr/bin/perl


use Data::Dumper;
use POSIX qw(strftime);
use lib '/httpd/modules';
use GTOOLS;
use ZOOVY;
use LUSER::FILES;
require LUSER;
require ZWEBSITE;
require BATCHJOB;

my ($LU) = LUSER->authenticate(flags=>'_S&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

# $LU->log('PRODEDIT.NUKEIMG',"[PID:$PID] Nuking image $img ".$prodref->{'zoovy:prod_image'.$img},'INFO');

my $VERB = $ZOOVY::cgiv->{'VERB'};
$GTOOLS::TAG{'<!-- SNAPSHOT -->'} = POSIX::strftime("SNAPSHOT-%Y%m%d_%H%M%S",localtime());

$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
$GTOOLS::TAG{'<!-- PROFILE -->'} = &ZWEBSITE::prt_get_profile($USERNAME,$PRT);
$GTOOLS::TAG{'<!-- GUID -->'} = BATCHJOB::make_guid();

my @BC = ();
push @BC, { name=>"Manage", link=>"/biz/manage/index.pl" };
push @BC, { name=>"Snapshots", link=>"/biz/manage/snapshots/index.cgi" };

my @TABS = ();
push @TABS, { name=>"Create", link=>"/biz/manage/snapshots/index.cgi?VERB=", selected=>($VERB eq '')?1:0,  };

my $c = '';
my ($lf) = LUSER::FILES->new($USERNAME);
foreach my $file (@{$lf->list("type"=>"SNAPSHOT",'active'=>0)}) {
	$c .= "<tr>";
		$c .= sprintf("<td><a target=\"file\" href=\"/biz/setup/private/index.cgi?VERB=VIEW&TYPE=%s&GUID=%s&ID=%s\">[View]</a></td>",$file->{'FILETYPE'},$file->{'GUID'},$file->{'ID'});
		$c .= sprintf("<td>%s</td>",$file->{'FILENAME'});
		$c .= sprintf("<td>%s</td>",&ZTOOLKIT::pretty_date($file->{'CREATED_GMT'}));
	$c .= "</tr>\n";
	}
if ($c eq '') { $c .= "<tr><td colspan=3><i>No files</i></td></tr>"; }
$GTOOLS::TAG{'<!-- FILES -->'} = $c;
my $template_file = 'index.shtml';

&GTOOLS::output(
	file=>$template_file,
	bc=>\@BC,
	tabs=>\@TABS,
	header=>1
	);

