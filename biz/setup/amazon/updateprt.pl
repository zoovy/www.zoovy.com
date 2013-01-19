#!/usr/bin/perl

use lib "/httpd/modules";
use ZWEBSITE;
use SYNDICATION;
use ZOOVY;
use DBINFO;

foreach my $CLUSTER (@{&ZOOVY::return_all_clusters()}) {
	print "CLUSTER: $CLUSTER\n";
	my ($udbh) = &DBINFO::db_user_connect($CLUSTER);
	
	my $pstmt = "select USERNAME,PROFILE from SYNDICATION where DSTCODE='AMZ' and IS_ACTIVE>0 order by LASTSAVE_GMT";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my ($USERNAME,$PROFILE) = $sth->fetchrow() ) {
		my ($so) = SYNDICATION->new($USERNAME,$PROFILE,'AMZ','type'=>'product');
		next if (($so->get('.feedpermissions') & 1)==0);
		my $PRT = $so->prt();

		my $path = &ZOOVY::resolve_userpath($USERNAME);
		next if (! -d $path);

		print "SET: $USERNAME $PRT\n";
		my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
		next if (defined $gref->{'amz_prt'});
		$gref->{'amz_prt'} = $PRT;
		&ZWEBSITE::save_globalref($USERNAME,$gref);
		}
	
	$sth->finish();
	&DBINFO::db_user_close();
	}