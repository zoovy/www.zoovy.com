#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use DBINFO;
use YAML::Syck;
use Data::Dumper;



my ($ref) = YAML::Syck::LoadFile("default-graphs.yaml");
#print  Dumper($ref); die();

foreach my $CLUSTER (@{$ZOOVY::CLUSTERS}) {
	my $udbh = &DBINFO::db_user_connect($CLUSTER);
	my $pstmt = "select USERNAME from KPI_USER_GRAPHS";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @USERS = ();
	while ( my ($USERNAME) = $sth->fetchrow() ) {
		push @USERS, $USERNAME;
		}
	$sth->finish();

	foreach my $USERNAME (@USERS) {
		my ($MID) = &ZOOVY::resolve_mid($USERNAME);
		my $pstmt = "delete from KPI_USER_GRAPHS where IS_SYSTEM=1 and MID=$MID";
		print "$pstmt\n";
		$udbh->do($pstmt);
		foreach my $guid (keys %{$ref}) {
			$pstmt = "delete from KPI_USER_GRAPHS where MID=$MID and UUID=".$udbh->quote($guid);
			print $pstmt."\n";
			$udbh->do($pstmt);

			my $db = $ref->{$guid};
			$db->{'USERNAME'} = $USERNAME;
			$db->{'MID'} = &ZOOVY::resolve_mid($USERNAME);
			$db->{'IS_SYSTEM'} = 1;
			my $pstmt = &DBINFO::insert($udbh,'KPI_USER_GRAPHS',$db,sql=>1);
			print $pstmt."\n";
			$udbh->do($pstmt);
			} 
		}
	&DBINFO::db_user_close();
	}

