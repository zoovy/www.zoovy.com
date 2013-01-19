#!/usr/bin/perl -w

use strict;
use lib "/httpd/modules";
require GTOOLS;
require SEARCH;
require ZOOVY;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_P&2');
my ($udbh) = &DBINFO::db_user_connect($USERNAME);
if ($USERNAME eq '') { exit; }

my $template_file = 'search.shtml';
my $ACTION = defined($ZOOVY::cgiv->{'ACTION'}) ? $ZOOVY::cgiv->{'ACTION'} : '';
$ACTION = uc($ACTION);
my $VALUE = defined($ZOOVY::cgiv->{'VALUE'}) ? $ZOOVY::cgiv->{'VALUE'} : '';

#use Data::Dumper;
#$GTOOLS::TAG{'<!-- PARAMS -->'} = "<pre>".&ZOOVY::incode(Dumper($ZOOVY::cgiv))."</pre>";

#if ($ZOOVY::cgiv->{'FROM_HEADER'}) {
#	## this app is also run directly from the header and uses the variables below:
#	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'product:mkt') { $ACTION = 'MKT'; }
#	if ($ZOOVY::cgiv->{'FROM_HEADER'} eq 'product:keyword') { $ACTION = 'SEARCH'; }
#	$VALUE = $ZOOVY::cgiv->{'HEADER_VALUE'};
#	}

my $FORMAT = defined($ZOOVY::cgiv->{'FORMAT'}) ? $ZOOVY::cgiv->{'FORMAT'} : '';
$FORMAT = uc($FORMAT);
$GTOOLS::TAG{'<!-- VALUE -->'} = $VALUE;

my $searchType = $ZOOVY::cgiv->{'searchtype'};

if ($ACTION eq "LISTALL") {
	$ACTION = "SEARCH";
	$searchType = "LISTALL";
	}

my $PROD_IS_FILTER = 0;
if ($ACTION eq 'FILTER') {
	my $checked = 0;

	if (@ZOOVY::PROD_IS) {};	# stop 'used once' warning	
	foreach my $isa (@ZOOVY::PROD_IS) {
		my $attr = $isa->{'attr'};
		$GTOOLS::TAG{"<!-- CHK-$attr -->"} = '';
		if (defined $ZOOVY::cgiv->{"$attr"}) {
			$GTOOLS::TAG{"<!-- CHK-$attr -->"} = 'checked';
			$PROD_IS_FILTER |= (1<<$isa->{'bit'}); 
			}
		}

	if ($PROD_IS_FILTER>0) {
		$ACTION = 'SEARCH';
		$searchType = 'FILTER';
		}
	$template_file = 'search-filter.shtml';
	}

my $MKT_FILTER = 0;
if ($ACTION eq 'MKT') {
	my $checked = 0;
	if (@ZOOVY::INTEGRATIONS) {}; 	# stop 'used once' warning
	foreach my $intref (@ZOOVY::INTEGRATIONS) {
		my ($attr,$bitval,$default,$name) = ($intref->{'attr'},$intref->{'mask'},$intref->{'true'},$intref->{'title'});
		$GTOOLS::TAG{"<!-- CHK-$attr -->"} = '';
		if (defined $ZOOVY::cgiv->{"$attr"}) {
			# print STDERR "MKT_FILTER: $MKT_FILTER |= $bitval\n";
			$GTOOLS::TAG{"<!-- CHK-$attr -->"} = 'checked';
			$MKT_FILTER |= $bitval; 
			}
		}
	#foreach my $attr (keys %ZOOVY::MKT_BITVAL) {
	#	my ($bitval,$default,$name) = @{$ZOOVY::MKT_BITVAL{$attr}};
	#	$GTOOLS::TAG{"<!-- CHK-$attr -->"} = '';
	#	if (defined $ZOOVY::cgiv->{"$attr"}) {
	#		print STDERR "MKT_FILTER: $MKT_FILTER |= $bitval\n";
	#		$GTOOLS::TAG{"<!-- CHK-$attr -->"} = 'checked';
	#		$MKT_FILTER |= $bitval; 
	#		}
	#	}

	if ($MKT_FILTER>0) {
		$ACTION = 'SEARCH';
		$searchType = 'MKT';
		}
	$template_file = 'search-mkt.shtml';
	}




if ($searchType eq '') { $searchType = 'FAST';	}

my @results = ();
if ($ACTION eq 'SEARCH') {

	$VALUE =~ s/[ ]+$//gs;	# strip trailing spaces
	$VALUE =~ s/^[ ]+//gs;	# strip leading spaces.
	my @prodlist = ();
	my $TITLE = '';
	my $pidsref = undef;
	# if we find an exact match, then we'll use that since most people will be searching by product id.

	if ($VALUE eq '') {
		## silly user has a blank product.. sku ''
		}
	elsif ($PROD_IS_FILTER>0) {
		## we're going to need to a real search..sorry, no direct pid lookups!
		}
	elsif ($MKT_FILTER>0) {
		## we're going to need to a real search..sorry, no direct pid lookups!
		}
	elsif (&ZOOVY::productidexists($USERNAME,$VALUE,cache=>0)) {
		# short cut, if we did a search for a product id
		push @results, $VALUE;
		}


	if (scalar(@results)==1) {
		## woot, already got a match!
		}	
	elsif ($searchType eq 'LISTALL') {
		# Full list of products
		$pidsref = &ZOOVY::fetchproducts_by_nameref($USERNAME);	
		@results = keys %{$pidsref};
		$TITLE = "Full list of Product's (".scalar(@results)." total)";
		}
	elsif ($searchType =~ /^CATALOG\:(.*?)$/) {
		my ($catalog) = ($1);
		(my $out,$pidsref) = &SEARCH::search($USERNAME,'CATALOG'=>$catalog,'KEYWORDS'=>$VALUE,'ISOLATION_LEVEL'=>0);
		@results = @{$out};
		$TITLE = &ZOOVY::incode("Catalog $catalog term: $VALUE results: ".scalar(@results));
		}
	elsif ($searchType =~ /\:/) {
		require PRODUCT::BATCH;
		my $pids = &PRODUCT::BATCH::list_by_attrib($USERNAME,$searchType,$VALUE);
		if ((defined $pids) && (ref($pids) eq 'ARRAY')) {
			@results = @{$pids};
			}
		}
	elsif (($searchType eq 'FAST') || ($searchType eq 'DETAIL') || ($searchType eq 'FILTER') || ($searchType eq 'MKT')) {

		$VALUE =~ s/[^\w\-\ ]+/_/gs;
		$VALUE = quotemeta(uc($VALUE));

		($pidsref) = &ZOOVY::fetchproducts_by_nameref($USERNAME,prod_is=>$PROD_IS_FILTER,mkt=>$MKT_FILTER);
		foreach my $prod (sort keys %{$pidsref}) {
			if (($PROD_IS_FILTER>0) && ($VALUE eq '')) {
				push @results, $prod;
				}
			elsif (($MKT_FILTER>0) && ($VALUE eq '')) {
				push @results, $prod;
				}
			elsif (uc($prod) =~ /$VALUE/) {
				push @results, $prod;
				}
			elsif (uc($pidsref->{$prod}) =~ /$VALUE/) { 
				push @results, $prod;
				}
			#elsif ($searchType eq 'DETAIL') {
			#	if (uc(&ZOOVY::fetchproduct_data($USERNAME,$prod)) =~ /$VALUE/s) {
			#		push @results, $prod;
			#		}
			#	}
			}
	
		$TITLE = "Matching sub-string results for $VALUE (".scalar(@results)." found, ".scalar(keys %{$pidsref})." total)\n";
		}
	elsif ($searchType eq 'EBAY') {
		require EBAY2;
		my ($udbh) = &DBINFO::db_user_connect($USERNAME);
		my $pstmt = "select PRODUCT from EBAY_LISTINGS where MID=$MID /* $USERNAME */ and EBAY_ID=".$udbh->quote($VALUE);
		my ($PRODUCT) = $udbh->selectrow_array($pstmt);
		if (defined $PRODUCT) {
			push @results, $PRODUCT;
			}
		&DBINFO::db_user_close();
	#	require EBAY::LISTING;
	#	my ($l) = EBAY::LISTING->new('EBAY',$USERNAME,listingid=>$VALUE,channel=>$VALUE);
	#	if (defined $l) { 
	#		push @results, $l->{'PRODUCT'};
	#		}
		}
	#elsif ($searchType eq 'OS') {
	#	require OVERSTOCK::LISTING;
	#	my ($l) = OVERSTOCK::LISTING->new('OVERSTOCK',$USERNAME,marketid=>$VALUE,channel=>$VALUE);
	#	if (defined $l) { 
	#		push @results, $l->{'PRODUCT'};
	#		}
	#	}
	else {
		$TITLE = "Unknown search type [$searchType]"; 
		}


	# now, if we only have one match, then we'll jump right to that product
	my $c = '';
	if ((scalar(@results)==1) && ($PROD_IS_FILTER==0)) {
		# take them straight there!
		print "Location: /biz/product/edit.cgi?PID=".$results[0]."\n\n";
		exit;
		}
	elsif (scalar(@results)==0) {
		$c = "<tr><td><font face='arial' color='red'>Sorry, No products matching $VALUE found.</font></td></tr>\n";
		}
	else {
		# More than one entry in results.
	
		if (not defined $pidsref) {
			## if we didn't already build pidsref, go ahead.. (hint: we could probably just load @results)
			$pidsref = &ZOOVY::fetchproducts_by_nameref($USERNAME);	
			}

		my $counter = 0;
		my $prod; 
		my $bgcolor;
		$c = '';
		foreach $prod (sort @results) {
			next if ($counter > 100000);
			
			if ($counter++ % 2 == 1) { $bgcolor = 'FFFFFF'; } else { $bgcolor='CCCCCC'; }
			my $prodname = '';
			if ($pidsref->{$prod} ne '') { 
				$prodname = $pidsref->{$prod}; 
				} 
			else { 
				$prodname = 'Product Name Not Set'; 
				}

			if ($FORMAT eq '') {
				$c .= "<tr bgcolor='#$bgcolor'><td><a href='edit.cgi?PID=$prod'>[Edit]</a><td><b>$prod</b></td><td>$pidsref->{$prod}</td></tr>\n";
				}
			elsif ($FORMAT eq 'PLAIN') {
				$c .= "<tr><td>$prod</td></tr>\n";
				}
			}
		$GTOOLS::TAG{'<!-- COUNTER -->'} = $counter.' products total.<br>';
		if ($counter>100000) {
			$GTOOLS::TAG{'<!-- COUNTER -->'} .= "100,000 products shown (maximum)<br>";
			}
			
		}

	$GTOOLS::TAG{"<!-- RESULTS -->"} = qq~
<table width=500 class="zoovytable">
<tr><td class="zoovytableheader"> Search Results: $TITLE</td></tr>
<tr><td>
<table>
$c
</table>
</td></tr>
</table>
	~;
	$c = '';

	}

$GTOOLS::TAG{'<!-- SEARCHTYPE_FAST -->'} = ($searchType eq 'FAST')?'checked':'';
$GTOOLS::TAG{'<!-- SEARCHTYPE_UPC -->'} = ($searchType eq 'zoovy:prod_upc')?'checked':'';
$GTOOLS::TAG{'<!-- SEARCHTYPE_SUPPLIERID -->'} = ($searchType eq 'zoovy:prod_supplierid')?'checked':'';
$GTOOLS::TAG{'<!-- SEARCHTYPE_MFGID -->'} = ($searchType eq 'zoovy:prod_mfgid')?'checked':'';

if (1) {
	my $c = '';
	my $catalogs = &SEARCH::list_catalogs($USERNAME);
	foreach my $k (keys %{$catalogs}) {
		next if ($k eq 'SUBSTRING');
		next if ($k eq 'FINDER');
		my $ID = sprintf("CATALOG:%s",$catalogs->{$k}->{'CATALOG'});
		my $selected = ($searchType eq $ID)?'checked':''; 
		$c .= "<input name=\"searchtype\" $selected value=\"$ID\" type=\"radio\"> CATALOG ".$catalogs->{$k}->{'CATALOG'}."<br>";
		}
	$GTOOLS::TAG{'<!-- CATALOGS -->'} = $c;
	}

&GTOOLS::output(
	title=>'',
	file=>$template_file,
	header=>1
	);

&DBINFO::db_user_close();

