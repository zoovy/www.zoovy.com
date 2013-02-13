#!/usr/bin/perl

use Data::Dumper;
use lib "/httpd/modules";
use ZOOVY;
use ZWEBSITE;
use ORDER::BATCH;
use POSIX; 

my $USERNAME = 'zephyrsports';

my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,0);
open F, ">/tmp/$USERNAME.tsv\n";

my ($ts) = &ORDER::BATCH::report($USERNAME,'CREATED_GMT'=>time()-(86400*60));
print F "ORDER\tSHIP-DATE\tSUBTOTAL\tCREATED\tCARRIER\tTRACKING\tDECLAREDVAL\n";
foreach my $oidref (@{$ts}) {
	my $oid = $oidref->{'ORDERID'};
	print "OID: $oid\n";
	next if ($oid eq '');
	my ($o) = ORDER->new($USERNAME,$oid);

#$VAR1 = {
#          'cost' => '4.58',
#          'actualwt' => '0',
#          'track' => '518355710166299',
#          'content' => '',
#          'void' => '0',
#          'ins' => '',
#          'carrier' => 'FDXG',
#          'created' => '1209672158',
#          'dv' => '0.00',
#          'notes' => ''
#        };

	my $total = sprintf("%.2f",$o->get_attrib('order_subtotal'));

	foreach my $trk (@{$o->tracking()}) {
		# print Dumper($trk);
		$trk->{'dv'} = sprintf("%.2f",$trk->{'dv'});
		my $shipdate = POSIX::strftime("%Y%m%d%H%M%S",localtime($trk->{'created'}));
		
		print F "$oid\t$shipdate\t$total\t$trk->{'carrier'}\t$trk->{'track'}\t$trk->{'dv'}\n";
		}
	
	}

close F;
