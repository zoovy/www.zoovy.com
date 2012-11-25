#!/usr/bin/perl

use strict;
use Archive::Zip;
use Text::CSV_XS;
use Spreadsheet::WriteExcel::Simple;
use Spreadsheet::WriteExcel;
use POSIX qw (strftime);
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require BATCHJOB;
require DBINFO;
require PRODUCT;
require ZWEBSITE;
require INVENTORY;
require GTOOLS::Form;
require SITE;

my $template_file = '';
my $MAXOUT = 500;
my $HOSTNAME = $ENV{'HOSTNAME'};
if ($HOSTNAME eq 'webapi') { $MAXOUT = 5000; }

&ZOOVY::init();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&16');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }


if ($ZOOVY::cgiv->{'GUID'} eq '') {
	$ZOOVY::cgiv->{'GUID'} = BATCHJOB::make_guid();
	}

my @MSGS = ();


my $VERB = $ZOOVY::cgiv->{'VERB'};
my $FIELDSREF = [
	{ type=>'checkbox', key=>'.navcats' },
	{ type=>'checkbox', key=>'.categories' },
	{ type=>'checkbox', key=>'.imagelib' },
	{ type=>'checkbox', key=>'.produrls' },
	{ type=>'checkbox', key=>'.addtocart' },
	{ type=>'checkbox', key=>'.stripcrlf' },
	{ type=>'checkbox', key=>'.convertutfx' },
	{ type=>'checkbox', key=>'.expandpogs' },
	{ type=>'text', key=>'.pogs' },
	{ type=>'text', key=>'.fields' },
	];

my %params = ();

if ($VERB eq '') {
	## Load from LUSER defaults.
	%params = %{&ZTOOLKIT::parseparams($LU->get('utilities.csvexport'))};
	}
else {
	&GTOOLS::Form::serialize($FIELDSREF,$ZOOVY::cgiv,\%params);
	}
$params{'GUID'} = $ZOOVY::cgiv->{'GUID'};
$params{'REPORT'} = 'PRODUCT_EXPORT';
$GTOOLS::TAG{'<!-- GUID -->'} = $params{'GUID'};

if ($VERB eq 'REMEMBER_SETTINGS') {
	push @MSGS, "SUCCESS|Saved user preferences";
	$VERB = '';
	$LU->set('utilities.csvexport',&ZTOOLKIT::buildparams(\%params));
	$LU->save();
	}

##
## SANITY: at this point all the settings are loaded, and remembered (if applicable)
##

$params{'.fields'} =~ s/^[\s]+//gs;	# strip leading trailing space
$params{'.fields'} =~ s/[\s]+$//gs;

if ($params{'.fields'} ne '') {
	require REPORT::PRODUCT_EXPORT;
	my ($lines,$msgs) = REPORT::PRODUCT_EXPORT::parse_headers($params{'.fields'});
	my $c = '';
	my $HAD_ERRORS = 0;
	foreach my $msg (@{$msgs}) {
		my ($type,$txt) = split(/\|/,$msg,2);
		push @MSGS, $msg;
		if ($type eq 'ERROR') { $HAD_ERRORS++; }
		}
	if ($HAD_ERRORS) {
		push @MSGS, "WARNING|You will need to correct the errors before you can continue.";
		$VERB = '';
		}
	$GTOOLS::TAG{'<!-- FIELD_MSGS -->'} = $c;
	$params{'.lines'} = join("\n",@{$lines});
	}

foreach my $f (@{$FIELDSREF}) {
	my $k = $f->{'key'};
	if ($f->{'type'} eq 'text') {
		$GTOOLS::TAG{'<!-- FIELDS -->'} = ZOOVY::incode($params{$k});
		}
	elsif ($f->{'type'} eq 'checkbox') {
		$GTOOLS::TAG{'<!-- CHK_'.uc(substr($k,1)).' -->'} = ($params{$k}?'checked':'');
		}
	}


## CHECK FLAGS
if ($FLAGS =~ /,CSV,/) {
   }
elsif ($LU->is_zoovy()) {
   push @MSGS, "WARN|This account does not have the CSV flag. CSV Flag was added for support user";
   $FLAGS .= ',CSV,';
   }

$GTOOLS::TAG{'<!-- USERDATE -->'} = $USERNAME."-".strftime("%e-%b-%Y", localtime()).'_'.time();
$GTOOLS::TAG{'<!-- USERDATE -->'} =~ s/ /0/g;
$GTOOLS::TAG{'<!-- TS -->'} = time();

my ($tsref,$catref);
my $PRODUCTS = $ZOOVY::cgiv->{'PRODUCTS'};

if ($ZOOVY::cgiv->{'CATEGORIES'}) {
	($tsref,$catref) = &ZOOVY::build_prodinfo_refs($USERNAME);
	}

if ($ZOOVY::cgiv->{'NAVCATS'}) {
	require NAVCAT;
	}


if ($VERB eq 'ANALYZE_FIELDS') {
	if ($PRODUCTS eq '') {
		push @MSGS, "ERROR|You'll need to select products before using Analyze Fields.";
		}
	else {
		my @ar= split(/,/,$PRODUCTS);
		my $ref = &ZOOVY::fetchproducts_into_hashref($USERNAME,\@ar);
		my $out = '';
		my $vars = {};

		foreach my $PID (@ar) {
  		 	my $prodref = $ref->{$PID};

		   foreach my $var (keys %{$prodref}) {
   		   next if $var eq '';
				next if (substr($var,0,1) eq '_');		# don't show hidden fields.
				next if (substr($var,0,1) eq '@');
				next if (substr($var,0,1) eq '%');

     		 	my $prevar = '';
      		if ($var =~ /^(.*?):(.*?)$/o) { $prevar = $1; }
      		$vars->{$prevar}->{$var}++;
      		}
   		}
		foreach my $key (sort keys %{$vars}) {
   		$out .= "<tr><td valign=top><b>$key</b></td>";
   		my $fields = '';
   		foreach my $sub (sort keys %{$vars->{$key}}) {
     			$fields .= "$sub, ";
      		}
   		chop($fields);
   		$out .= "<td>$fields</td></tr>";
   		}

		$GTOOLS::TAG{'<!-- ANALYZED -->'} = $out;
		}

	$VERB = '';
	}




my $OUTPUT = '';


if ($VERB eq 'SAVE_DATERANGE') {
	my $begints = &ZTOOLKIT::mysql_to_unixtime($ZOOVY::cgiv->{'START'}."000000");
	my $endts = &ZTOOLKIT::mysql_to_unixtime($ZOOVY::cgiv->{'END'}."000000");

	require PRODUCT::BATCH;
	my $pids = &PRODUCT::BATCH::report($USERNAME,CREATED_BEFORE=>$endts,CREATED_SINCE=>$begints);
	$PRODUCTS = join(',',@{$pids});

	$VERB = '';
	}

if ($VERB eq 'SELECT_DATERANGE') {
	my $c = qq~
<b>Select Date Range</b>
<input type='hidden' name="VERB" value="SAVE_DATERANGE">
<table>
	<tr><td>Starting Date:</td><td><input size="8" type="textbox" name="START"> <div class="hint">Format: YYYYMMDD</div></td></tr>
	<tr><td>Ending Date:</td><td><input size="8" type="textbox" name="END"> <div class="hint">Format: YYYYMMDD</div></td></tr>
</table>
~;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}


##
##
##
if ($VERB eq 'SELECT_RANGE') {
	my $c = qq~
<input type='hidden' name='VERB' value='SAVE_RANGE'>
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
~;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($VERB eq 'SAVE_RANGE') {
	my @list = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
	my $start = &ZTOOLKIT::alphatonumeric($ZOOVY::cgiv->{'RSTART'});
	my $end = &ZTOOLKIT::alphatonumeric($ZOOVY::cgiv->{'REND'});
	if ($start gt $end) { my $t = $start; $start = $end; $end = $t; }
	$PRODUCTS = '';
	foreach my $p (sort @list) {
		my $i = &ZTOOLKIT::alphatonumeric($p);
	#	my $didit = 0;
		if (($start <= $i) && ($end >= $i)) {
			$PRODUCTS .= $p.','; 
			# $didit++;
			}
	# 	print STDERR "[$didit] $p $start le $i  &&  $end ge $i\n";
		}
	chop($PRODUCTS);
	$VERB = '';
	}


if ($VERB eq 'SELECT_USERLIST') {
	my $c = qq~
<input type='hidden' name='VERB' value='SAVE_USERLIST'>
<b>User Specified List</b><br>
<br>

Provide a list of Product Id's separated by either commas, tabs, spaces, or one per line
(or any combination of the above).<br>
<hr>
<textarea cols=70 rows=30 name="LIST">
</textarea>
<br>
~;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}


if ($VERB eq 'SELECT_USERRANGE') {
	my $c = qq~
<input type='hidden' name='VERB' value='SAVE_USERRANGE'>
<b>User Specified Range</b><br>
<br>

Provide a list of Product Id's separated by either commas, tabs, spaces, or one per line
(or any combination of the above).<br>
<hr>
Start Product #: <input type="textbox" name="START-RANGE"> ex:1<br>
End Product #: <input type="textbox" name="END-RANGE"> ex:100<br>
<br>
~;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}



if ($VERB eq 'SAVE_USERLIST') {
	my @list = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
	foreach my $SKU (split(/[\s\t\n\r]+/s,$ZOOVY::cgiv->{'LIST'})) {
		$PRODUCTS .= $SKU.',';
		}
	chop($PRODUCTS);
	$VERB = '';
	}




#######################################################################################

#######################################################################################



if ($VERB eq 'SAVE_PRODUCTS') {
	$PRODUCTS = '';
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /product\-(.*?)$/) {
			$PRODUCTS .= "$1,";
			}
		}
	chop($PRODUCTS);
	$VERB = '';
	}


if ($VERB eq 'SELECT_PRODUCTS') {
	my %prodhash = &ZOOVY::fetchproducts_by_name($USERNAME);
	my %p = ();
	my $c = '';
	foreach my $k (split(',',$PRODUCTS)) { $p{$k}++; }
	foreach my $thisprod (sort keys %prodhash) {
	   $prodhash{$thisprod} = &strip_html($prodhash{$thisprod});
   	$c .= "<input type='CHECKBOX' ";
		if (defined $p{$thisprod}) { $c .= 'checked'; }
		$c .= " name=\"product-$thisprod\">$thisprod - ".$prodhash{$thisprod}."<br>\n";
		}
	$c = qq~
<input type='hidden' name='VERB' value='SAVE_PRODUCTS'>
<b>Select Products</b><br>
~.$c;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($VERB eq 'SELECT_ALL') {
	$PRODUCTS = '';
	my %prodhash = &ZOOVY::fetchproducts_by_name($USERNAME);
	foreach my $k (keys %prodhash) {
		$PRODUCTS .= "$k,";
		}
	chop($PRODUCTS);
	$VERB = '';
	}


#######################################################################################

if ($VERB eq 'SELECT_MANAGECAT') {
	require CATEGORY;
	my $info = &CATEGORY::fetchcategories($USERNAME);
	my $c = '';
	foreach my $safe (sort keys %{$info}) {
		$c .= "<input type='checkbox' name='mcat-$safe'> $safe<br>";
		}
	
	$c = qq~
<input type='hidden' name='VERB' value='SAVE_MANAGECATS'>
<b>Select from Management Categories</b><br>
~.$c;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

if ($VERB eq 'SAVE_MANAGECATS') {
	require CATEGORY;
	$PRODUCTS = '';
	my $info = &CATEGORY::fetchcategories($USERNAME);
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /mcat\-(.*?)$/) {
			my $safe = $1;
			$PRODUCTS .= $info->{$safe}.',';
			}
		}
	chop($PRODUCTS);
	$VERB = '';
	}

#######################################################################################

if ($VERB eq 'SAVE_NAVCATS') {
	require NAVCAT;
	$PRODUCTS = '';
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		if ($k =~ /navcat\-(.*?)$/) {
			my $safe = $1;
			my ($pretty, $children, $productstr, $sortby) = $NC->get($safe);
			$PRODUCTS .= $productstr.',';
			}
		}
	chop($PRODUCTS);
	$VERB = '';
	}

if ($VERB eq 'SELECT_NAVCAT') {
	require NAVCAT;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	my $c = '';
	foreach my $safe (sort $NC->paths()) {
		my ($pretty, $children, $productstr, $sortby) = $NC->get($safe);
		$c .= "<input type='checkbox' name='navcat-$safe'> $safe<br>";
		}
	$c = qq~
<input type='hidden' name='VERB' value='SAVE_NAVCATS'>
<b>Select from Navigation Categories</b><br>
~.$c;
	$GTOOLS::TAG{'<!-- OUTPUT -->'} = $c;
	$template_file = 'select.shtml';
	}

print STDERR "VERB:$VERB\n";
if ($VERB eq 'EXPORT_REDIRECT') {
	require BATCHJOB;
	$params{'.products'} = $ZOOVY::cgiv->{'PRODUCTS'};
	my ($bj) = BATCHJOB->new($USERNAME,
		&BATCHJOB::resolve_guid($USERNAME,$params{'GUID'}),
		PRT=>$PRT,
		GUID=>$params{'GUID'},
		EXEC=>'REPORT',
		'%VARS'=>\%params,
		'*LU'=>$LU,
		## ??
		);

	if ($bj->id()>0) {
		## lets redirect to the batch viewer
		$bj->start();
		# print "Location: /biz/batch/index.cgi?VERB=LOAD&JOB=".($bj->id())."&GUID=$params{'GUID'}\n\n";
		my $URL = "/biz/batch/index.cgi?VERB=LOAD&JOB=".($bj->id())."&GUID=$params{'GUID'}";
		# print "Content-type: text/html\n\n";
		# print "\n";
		# print "<a href=\"$URL\">click here if this page does not automatically reload</a>";
		# print "<script>\nnavigateTo('$URL');\n</script>";
		$GTOOLS::TAG{'<!-- URL -->'} = $URL;
		$template_file = '_/redirect.shtml';
		$VERB = 'EXPORT';
		}
	else {
		$VERB = '';
		## ??!? wtf happened.
		push @MSGS, "ERROR|+could not start job";
		}
	}

if ($VERB eq 'SEARCH') {
	my ($keywords) = $ZOOVY::cgiv->{'ELASTIC-KEYWORDS'};
	if ($keywords ne '') {
		my @TRACE = ();
		my @PIDS = @{&SEARCH::search_elastic($USERNAME,$keywords,\@TRACE,'_size'=>1000,'allow_ranges'=>1)};
		$PRODUCTS = ",".join(',',@PIDS);
		foreach my $msg (@TRACE) {
			push @MSGS, "INFO|+$msg";
			}
		push @MSGS, "SUCCESS|+Search found ".scalar(@PIDS)." products";
		}
	$VERB = '';
	}


if ($VERB eq '') {
	$template_file = 'index.shtml';
	my $c = '';
	my @ar = split(/,/,$PRODUCTS);
	$GTOOLS::TAG{'<!-- PRODUCTS -->'} = $PRODUCTS;
	if ($PRODUCTS eq '') {
		$GTOOLS::TAG{'<!-- PRODUCT_WARNING -->'} = qq~<font color='red'>Please select some products</font><br>~;
		}
	else {
		$GTOOLS::TAG{'<!-- PRODUCT_WARNING -->'} = "<font color='blue'>".scalar(@ar)." products selected.</font><br>";
		}
	$PRODUCTS =~ s/,/, /gs;
	$GTOOLS::TAG{'<!-- PRODUCTOUT -->'} = $PRODUCTS;
	}

if ($VERB eq 'DENY') {
	$template_file = 'denied.shtml';
	}


&GTOOLS::output(
   'title'=>'Product Export',
   'file'=>$template_file,
   'header'=>'1',
	'msgs'=>\@MSGS,
   'help'=>'#50365',
   'bc'=>[
      { name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
      { name=>'Product Export',link=>'','target'=>'_top', },
      ],
   );




sub strip_html {
   my ($foo) = @_;

   $foo =~ s/\<.*?\>//gis;

   return($foo);
}

sub strip_bad {
	my ($foo) = @_;
	my $c = '';
	foreach (split(//,$foo)) { 
		next if (ord($_)>128);
		next if (ord($_)<32);
		$c .= $_;
		}
	return ($c);
}
