#!/usr/bin/perl

#
# this application exports the default set of graphs from a users account.
#
#


use Data::Dumper;
use YAML::Syck;
use lib "/httpd/modules";
use ZOOVY;
use ZTOOLKIT;
use DBINFO;
use KPIBI;

my %SYSTEM_COLLECTIONS = ();
open F, "</httpd/htdocs/biz/kpi/collections.txt";
while (<F>) {
	chomp($_);
	my ($ID,$COLLECTION) = split(/\|/,$_);
	## create a two way lookup of collection=>id and id=>collection
	$SYSTEM_COLLECTIONS{$COLLECTION} = $ID;	
	$SYSTEM_COLLECTIONS{$ID} = $COLLECTION;
	}
close F;
print Dumper(\%SYSTEM_COLLECTIONS);

my $USERNAME = 'toynk'; my $PRT = 0;
my $MID = &ZOOVY::resolve_mid($USERNAME);
my ($udbh) = &DBINFO::db_user_connect($USERNAME);

#   open F, "</httpd/htdocs/biz/kpi/collections.txt";
#   while (<F>) {
#      chomp();
#      next if ($_ eq '');
#      next if (substr($_,0,1) eq '#'); # skip lines that start with a #
#      my ($id,$title) = split(/\|/,$_,2);
#      my $pstmt = &DBINFO::insert($udbh,'KPI_USER_COLLECTIONS',{
#         ID=>0,IS_SYSTEM=>$id,MID=>$MID,PRT=>$PRT,TITLE=>$title,'*CREATED'=>'now()'
#         },sql=>1);
#      $udbh->do($pstmt);
#      }
#   close F;
my %USER_COLLECTIONS = ();
my $pstmt = "select ID,TITLE,IS_SYSTEM from KPI_USER_COLLECTIONS where MID=$MID";
my $sth = $udbh->prepare($pstmt);
$sth->execute();
while ( my ($ID,$TITLE,$IS_SYSTEM) = $sth->fetchrow() ) {
	$USER_COLLECTIONS{ $ID } = $TITLE;
	$USER_COLLECTIONS{ $TITLE } = $ID;
	#if ($SYSTEM_COLLECTIONS{$TITLE}) {
	#	$pstmt = "update KPI_USER_GRAPHS set COLLECTION=$ID where MID=$MID and COLLECTION=$SYSTEM_COLLECTIONS{$TITLE}";
	#	print $pstmt."\n";
	#	$udbh->do($pstmt);
	#	}
	}
$sth->finish();

my $pstmt = "select * from KPI_USER_GRAPHS where MID=$MID /* $USERNAME */";
my $sth = $udbh->prepare($pstmt);
$sth->execute();
my %GUIDS = ();
while ( my $hashref = $sth->fetchrow_hashref() ) {
	delete $hashref->{'USERNAME'};
	delete $hashref->{'MID'};
	$hashref->{'IS_SYSTEM'} = $SYSTEM_COLLECTIONS{ $USER_COLLECTIONS{ $hashref->{'COLLECTION'} }};

	my $y = YAML::Syck::Load($hashref->{'CONFIG'});
	foreach $i (1..10) {
		next if ($y->{"dataset-$i"} eq '');
		my ($dsid,$dsp) = &ZTOOLKIT::dsnparams($y->{"dataset-$i"});
		if ($dsp->{'fmt'} eq '') {
			$dsp->{'fmt'} = $y->{"format-$i"};
			delete $y->{"format-$i"};
			}
		if ($dsp->{'f'}) { 
			$dsp->{'ctype'} = $dsp->{'f'};
			delete $dsp->{'f'};
			}
		$y->{"dataset-$i"} = &ZTOOLKIT::builddsn($dsid,$dsp);
		}
	if ($y->{'ddataset'}) {
		my ($dsid,$dsp) = &ZTOOLKIT::dsnparams($y->{"ddataset"});
      if ($dsp->{'fmt'} eq '') {
         $dsp->{'fmt'} = $y->{"dformat"};
         delete $y->{"dformat"};
         }
      if ($dsp->{'f'}) {
         $dsp->{'ctype'} = $dsp->{'f'};
         delete $dsp->{'f'};
         }
		$y->{"ddataset"} = &ZTOOLKIT::builddsn($dsid,$dsp);
		}

	$hashref->{'CONFIG'} = YAML::Syck::Dump($y);

	delete $hashref->{'COLLECTION'};
	$GUIDS{ $hashref->{'UUID'} } = $hashref;
	}
$sth->finish();
&DBINFO::db_user_close();

my $yyyymmdd = ZTOOLKIT::pretty_date(time(),-2);
my $file = "/httpd/htdocs/biz/kpi/$USERNAME-$yyyymmdd.yaml";
YAML::Syck::DumpFile($file,\%GUIDS);
chmod(0666,$file);
chown(65534,65534,$file);

print "File: $file was written, if you want to use this file then you need to symlink it:\n";
print "ln -sf $file /httpd/htdocs/biz/kpi/default-graphs.yaml\n\n";

