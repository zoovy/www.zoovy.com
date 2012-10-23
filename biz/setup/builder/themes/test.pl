#!/usr/bin/perl

use lib "/httpd/modules";
use ZWEBSITE;
use ZTOOLKIT;

my $USERNAME = 'brian';

      my ($prtsref) = &ZWEBSITE::list_partitions($USERNAME);
      my $i = 0;
      my @PRTS = ();
      foreach my $prtref (@{$prtsref}) {
         my ($prtref) = &ZWEBSITE::prtinfo($USERNAME,$i);
         $prtref->{'id'} = $i;
			my $nsref = &ZOOVY::fetchmerchantns_ref($USERNAME,$prtref->{'profile'});
			my %data = ();
			foreach my $k ('zoovy:company_name','zoovy:address1','zoovy:address2') {
				my $kk = substr($k,index($k,':')+1);
				$data{$kk} = $k;
				}
			$prtref->{'data'} = "\n".&ZTOOLKIT::hashref_to_xmlish(\%data); 
         push @PRTS, $prtref;
         $i++;
         }
      $PARTITIONS = &ZTOOLKIT::arrayref_to_xmlish_list(\@PRTS,tag=>'prt',content_attrib=>'data',content_raw=>1);


print $PARTITIONS;