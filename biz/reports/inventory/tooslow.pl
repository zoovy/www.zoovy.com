#!/usr/bin/perl

use lib "/httpd/modules";
use INVENTORY;
use DBINFO;
use POGS;

my $dbh = &DBINFO::db_zoovy_connect();
my $USERNAME = 'greatlookz';


	print "%SKU,%INVENTORY,%LOCATION,!RESERVED,!DESCRIPTION\n";

	my %prodnames = &ZOOVY::fetchproducts_by_name($USERNAME);
	my ($invref,$reserveref,$locref) = &INVENTORY::fetch_qty($USERNAME,undef);

	my $c = '';
	my @col = ();
	my $k = '';
	foreach my $sku (keys %{$invref}) {
		$col[0] = $sku;
		$col[1] = $invref->{$sku};
		$col[2] = $locref->{$sku};
		$col[3] = $reserveref->{$sku};

		## Handle for IN STOCK, OUT OF STOCK, ALL
		if ($ACTION eq 'EXPORTCSV_OUT' && $invref->{$sku} > 0) { next; }
		elsif ($ACTION eq 'EXPORTCSV_IN' && $invref->{$sku} <= 0) { next; }

		my $itemref = &ZOOVY::fetchproduct_as_hash($USERNAME,$sku);

		if ($sku =~ /\:(.*?)$/) {
			&POGS::apply_options($USERNAME,$sku,$itemref);
			$itemref->{'zoovy:prod_name'} =~ s/\n/ /g;
			}
		$col[4] = $itemref->{'zoovy:prod_name'};

		$c = '';
		foreach $k (@col) { 
			$k =~ s/"/""/gs;
			$k =~ s/[\n\r]+//gs;
			$c .= '"'.$k.'",'; 
			}
		chop($c);
		print "$c\n";
		}

	&DBINFO::db_zoovy_close();
