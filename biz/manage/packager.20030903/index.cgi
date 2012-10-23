#!/usr/bin/perl

use lib "/httpd/modules";
use GT;
use ZOOVY;
use IMGLIB;
use Archive::Zip;
use Text::CSV;
use Spreadsheet::WriteExcel::Simple;
use Spreadsheet::WriteExcel;
use POSIX qw (strftime);
use DBINFO;

$MAXOUT = 500;
my $HOSTNAME = $ENV{'HOSTNAME'};
if ($HOSTNAME eq 'webapi') { $MAXOUT = 5000; }


&ZOOVY::init();
&DBINFO::db_zoovy_connect();
($USERNAME,$FLAGS) = &ZOOVY::authenticate('/biz');
if ($FLAGS =~ /,L1,/) { $FLAGS .= ',CSV,'; }

if ($FLAGS !~ /,CSV,/) {
	$ACTION = 'DENY';
	}

$GT::TAG{'<!-- USERDATE -->'} = $USERNAME."-".strftime("%e-%b-%Y", localtime());
$GT::TAG{'<!-- USERDATE -->'} =~ s/ /0/g;
$GT::TAG{'<!-- TS -->'} = time();

my ($tsref,$catref);
my $PRODUCTS = $ZOOVY::cgiv->{'PRODUCTS'};

if ($ZOOVY::cgiv->{'CATEGORIES'}) {
	($tsref,$catref) = &ZOOVY::build_prodinfo_refs($USERNAME);
	}

if ($ZOOVY::cgiv->{'NAVCATS'}) {
	require NAVCAT;
	}

$ACTION = $ZOOVY::cgiv->{'ACTION'};

if ($ACTION eq 'PACKAGE' || $ACTION eq 'SCREEN' || $ACTION eq 'EXCEL') {
	my @ar= split(/,/,$PRODUCTS);
	if (scalar(@ar)>$MAXOUT) { $ACTION = ''; }
	if ($PRODUCTS eq '') { $ACTION = ''; }
	}

if ($ACTION eq 'PACKAGE' || $ACTION eq 'SCREEN' || $ACTION eq 'EXCEL') {
	%ALLKEYS = ();
	%PRODS = ();

   my $csv = Text::CSV->new();              # create a new object

	my @ar = split(/,/,$PRODUCTS);
	my $prodref = &ZOOVY::fetchproducts_into_hashref($USERNAME,\@ar);
	$out = '';
	
	foreach $prod (sort keys %{$prodref}) {
		print STDERR $prod."\n<br>";

		if ($ZOOVY::cgiv->{'IMAGELIB'}) {
			$x = 1;
			while ( defined $prodref->{$prod}->{'zoovy:prod_image'.$x} ) { 
				if ($prodref->{$prod}->{'zoovy:prod_image'.$x} ne '') {
					$prodref->{$prod}->{'%IMGURL=zoovy:prod_image'.$x} = &GT::imageurl($USERNAME,$prodref->{$prod}->{'zoovy:prod_image'.$x},undef,undef,undef,0,'jpg');		
					}
				delete $prodref->{$prod}->{'zoovy:prod_image'.$x}; 
				$x++;
				}
			if (defined $prodref->{$prod}->{'zoovy:prod_thumb'}) {
				if ($prodref->{$prod}->{'zoovy:prod_thumb'} ne '') {
					$prodref->{$prod}->{'%IMGURL=zoovy:prod_thumb'} = &GT::imageurl($USERNAME,$prodref->{$prod}->{'zoovy:prod_thumb'},undef,undef,undef,0,'jpg');
						}
				delete $prodref->{$prod}->{'zoovy:prod_thumb'}; 
				}
			}
		
		if (defined $ZOOVY::cgiv->{'CATEGORIES'}) {
			$prodref->{$prod}->{'%CATEGORY'} = $catref->{$prod};
			}
	
		if (defined $ZOOVY::cgiv->{'NAVCATS'}) {
			$count = 1;
			foreach $path (&NAVCAT::product_categories($USERNAME,$prod,1)) {
				$prodref->{$prod}->{'%CATEGORY'.($count++).'%'} = $path;
				}
			}

		foreach $k (keys %{$prodref->{$prod}}) {
			print STDERR "adding $k to allkeys\n";
			$ALLKEYS{$k}++;
			}
		}


	# Fix up some keys
	delete $ALLKEYS{''};
	$x = 1;	
	
	push @keyorder, '%SKU';
	push @keyorder, reverse sort keys %ALLKEYS;
	$csv = Text::CSV->new();
	$status = $csv->combine(@keyorder);    # combine columns into a string
	$output = $csv->string()."\n";               # get the combined string

	$excel = '<Tr style="font-weight: bold;">';
	foreach (@keyorder) {
		$excel .= "<td>$_</td>";
		}
	$excel .= "</tr>\n";

	foreach $prod ( keys %{$prodref} ) {	
		$excel .= "<tr>\n";
		$excel .= "<td>$prod</td>";
		$csv = Text::CSV->new();
		@columns = ();
		@columns = ($prod);
		foreach $k ( @keyorder ) {
			next if ($k eq '%SKU');
			$prodref->{$prod}->{$k} =~ s/[\n\r]+//igs;
	#		$prodref->{$prod}->{$k} = substr( $prodref->{$prod}->{$k} ,0,$MAXOUT);
			$prodref->{$prod}->{$k} = strip_bad( $prodref->{$prod}->{$k});

			$excel .= "<td>".&ZOOVY::incode($prodref->{$prod}->{$k})."</td>\n";

			push @columns, $prodref->{$prod}->{$k};
			}
		$status = $csv->combine(@columns);
		$output .= $csv->string()."\n";
		$excel .= "</tr>\n";
		}

	$GT::TAG{'<!-- CONTENT -->'} = $excel;
	$GT::TAG{'<!-- OUTPUT -->'} = &ZOOVY::incode($output);
	$template_file = 'output.shtml';

	}


if ($ACTION eq 'PACKAGE') {
	print "Content-type: text/csv\n\n";
	print "$output\n";
	exit;
	}

if ($ACTION eq 'EXCEL') {
	# print "Content-type: application/vnd.ms-excel\n\n";
	print "Content-type: application/excel\n\n";
	&GT::print_form('','excel.shtml',0);
	exit;
	}

if ($ACTION eq 'SCREEN') {
	print "Content-type: text/html\n\n";
	print "<table>";
	print "$excel";
	print "</table>";
	exit;
	}

# What the heck is this?
# -bh 
if ($ACTION eq 'PACKAGE2') {

	my $zip = Archive::Zip->new();
	my $imagedir = $zip->addDirectory( 'IMAGES/' );

	($tsref,$catref) = &ZOOVY::build_prodinfo_refs($USERNAME);
	$out = '';
	foreach $prod (keys %{$ZOOVY::cgiv}) {
		next if ($prod !~ /product-(.*?)/);
		$prod = substr($prod,8);
		print STDERR $prod."\n<br>";
		
		$x = 1;	
		use Data::Dumper;
		print STDERR Dumper($prodref->{$prod});
		while ( defined $prodref->{$prod}->{'zoovy:prod_image'.$x} ) {
			$file = $prodref->{$prod}->{'zoovy:prod_image'.$x};
			next if ($file =~ /^http/i);
			my $col = &IMGLIB::load_collection_info($USERNAME,$file);				
			print STDERR "trying to add $file\n";
			$zip->addFile($file);
			$x++;
			}

		&ZOOVY::fetchproduct_data($USERNAME,$prod);
		$out .= "<PRODUCT NAME=\"$prod\" TS=\"$tsref->{$prod}\" CAT=\"$catref->{$prod}\">";
#		$out .= $buffer;
		$out .= "</PRODUCT>";
		}
	$zip->addString( $out, 'products.zml' );
	my $status = $zip->writeToFileNamed( '/tmp/'.$USERNAME.'.packager.zip' );
		die "error somewhere" if $status != AZ_OK;

	# output to screen
	print "Content-type: binary/x-zip\n\n";
	open F, "</tmp/".$USERNAME.".packager.zip";
	while (<F>) { print $_; }
	close F;
	}


if ($ACTION eq 'SELECT_RANGE') {
	$c = qq~
<input type='hidden' name='ACTION' value='SAVE_RANGE'>
<b>Select Range of Products</b><br>
<i>NOTE: Products are sorted alphanumerically (e.g. 1, 100, 101, 2, 3, 4, 40, 41, 42, A123, B001)</i><br>
<br>
<table>
	<tr>
		<td>First Product:</td>
		<td><input type='textbox' name='RSTART'></td>
	</tr>
	<tr>
		<td>Last Product:</td>
		<td><input type='textbox' name='REND'></td>
	</tr>
</table>
~.$c;
	$GT::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($ACTION eq 'SAVE_RANGE') {
	my @list = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
	my $start = $ZOOVY::cgiv->{'RSTART'};
	my $end = $ZOOVY::cgiv->{'REND'};
	if ($start gt $end) { my $t = $start; $start = $end; $end = $t; }
	foreach my $p (@list) {
		if (($start le $p) && ($end ge $p)) {
			$PRODUCTS .= $p.',';
			}
		}
	chop($PRODUCTS);
	$ACTION = '';
	}

#######################################################################################

#######################################################################################



if ($ACTION eq 'SAVE_PRODUCTS') {
	$PRODUCTS = '';
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /product\-(.*?)$/) {
			$PRODUCTS .= "$1,";
			}
		}
	chop($PRODUCTS);
	$ACTION = '';
	}


if ($ACTION eq 'SELECT_PRODUCTS') {
	%prodhash = &ZOOVY::fetchproducts_by_name($USERNAME);
	my %p = ();
	foreach $k (split(',',$PRODUCTS)) { $p{$k}++; }
	foreach $thisprod (sort keys %prodhash) {
	   $prodhash{$thisprod} = &strip_html($prodhash{$thisprod});
   	$c .= "<input type='CHECKBOX' ";
		if (defined $p{$thisprod}) { $c .= 'checked'; }
		$c .= " name=\"product-$thisprod\">$thisprod - ".$prodhash{$thisprod}."<br>\n";
		}
	$c = qq~
<input type='hidden' name='ACTION' value='SAVE_PRODUCTS'>
<b>Select Products</b><br>
~.$c;
	$GT::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($ACTION eq 'SELECT_ALL') {
	$PRODUCTS = '';
	%prodhash = &ZOOVY::fetchproducts_by_name($USERNAME);
	foreach my $k (keys %prodhash) {
		$PRODUCTS .= "$k,";
		}
	chop($PRODUCTS);
	$ACTION = '';
	}


#######################################################################################

if ($ACTION eq 'SELECT_MANAGECAT') {
	require CATEGORY;
	$info = &CATEGORY::fetchcategories($USERNAME);
	foreach $safe (sort keys %{$info}) {
		$c .= "<input type='checkbox' name='mcat-$safe'> $safe<br>";
		}
	
	$c = qq~
<input type='hidden' name='ACTION' value='SAVE_MANAGECATS'>
<b>Select from Management Categories</b><br>
~.$c;
	$GT::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($ACTION eq 'SAVE_MANAGECATS') {
	require CATEGORY;
	$PRODUCTS = '';
	$info = &CATEGORY::fetchcategories($USERNAME);
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /mcat\-(.*?)$/) {
			$safe = $1;
			$PRODUCTS .= $info->{$safe}.',';
			}
		}
	chop($PRODUCTS);
	$ACTION = '';
	}

#######################################################################################

if ($ACTION eq 'SAVE_NAVCATS') {
	require NAVCAT;
	$PRODUCTS = '';
	$info = &NAVCAT::fetch_all($USERNAME);
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /navcat\-(.*?)$/) {
			$safe = $1;
			my ($pretty, $children, $productstr, $sortby) = split (/\n/, $info->{$safe}, 4);
			$PRODUCTS .= $productstr.',';
			}
		}
	chop($PRODUCTS);
	$ACTION = '';
	}

if ($ACTION eq 'SELECT_NAVCAT') {
	require NAVCAT;
	$info = &NAVCAT::fetch_all($USERNAME);
	foreach $safe (sort keys %{$info}) {
		my ($pretty, $children, $productstr, $sortby) = split (/\n/, $info->{$safe}, 4);
		$c .= "<input type='checkbox' name='navcat-$safe'> $safe<br>";
		}
	$c = qq~
<input type='hidden' name='ACTION' value='SAVE_NAVCATS'>
<b>Select from Navigation Categories</b><br>
~.$c;
	$GT::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}


if ($ACTION eq '') {
	$template_file = 'index.shtml';
	$c = '';
	my @ar = split(/,/,$PRODUCTS);
#	%prodhash = &ZOOVY::fetchproducts_by_name($USERNAME);
#	foreach $thisprod (sort keys %prodhash) {
#	   $prodhash{$thisprod} = &strip_html($prodhash{$thisprod});
#   	$c .= "<input type='CHECKBOX' name=\"product-$thisprod\">$thisprod - ".$prodhash{$thisprod}."<br>\n";
#		}
	$GT::TAG{'<!-- PRODUCTS -->'} = $PRODUCTS;
	if ($PRODUCTS eq '') {
		$GT::TAG{'<!-- PRODUCT_WARNING -->'} = qq~
<font color='red'>Please select some products</font><br>
		~;
		}
	elsif (scalar(@ar)>$MAXOUT) {
		$GT::TAG{'<!-- PRODUCT_WARNING -->'} = qq~
<font color='red'>WARNING: You may not export more than $MAXOUT products at a time</font><br>
		~;
		}
	else {
		$GT::TAG{'<!-- PRODUCT_WARNING -->'} = "<font color='blue'>".scalar(@ar)." products selected.</font><br>";
		}
	$PRODUCTS =~ s/,/, /gs;
	$GT::TAG{'<!-- PRODUCTOUT -->'} = $PRODUCTS;
	}

if ($ACTION eq 'DENY') {
	$template_file = 'denied.shtml';
	}

&GT::print_form('',$template_file,1);
&DBINFO::db_zoovy_close();


sub strip_html {
   my ($foo) = @_;

   $foo =~ s/\<.*?\>//gis;

   return($foo);
}

sub strip_bad {
	my ($foo) = @_;
	$c = '';
	foreach (split(//,$foo)) { 
		next if (ord($_)>128);
		next if (ord($_)<32);
		$c .= $_;
		}
	return ($c);
}
