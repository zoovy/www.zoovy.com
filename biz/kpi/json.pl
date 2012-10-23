#!/usr/bin/perl

use strict;
use CGI;
use Data::Dumper;
use JSON::XS;
use lib "/httpd/modules";
require ZOOVY;
require DBINFO;
require KPIBI;


print "Content-Type: text/json\n\n";

my ($v) = &ZTOOLKIT::parseparams($ENV{'QUERY_STRING'});
#print "<div>URI PARAMS: ".Dumper($v)."</div>";
my ($USER) = $v->{'USER'};
my ($UUID) = $v->{'UUID'};
my ($DIVID) = $v->{'DIVID'};
my $KPI = undef;

my $ERROR = '';
if ($UUID eq '') {
	$ERROR = "UUID is a required parameter";
	}
elsif ($USER eq '') {
	$ERROR = "USER is a required parameter";
	}


if (not $ERROR) {
	$KPI = KPIBI->new($USER);
	if (not defined $KPI) {
		$ERROR = "Could not create KPI object";
		}
	}

##
## SANITY: at this point $KPI is instantiated
##

my $graphcfg = undef;
if (not $ERROR) {
	$graphcfg = $KPI->get_graphcfg($UUID);
	
	if (not defined $graphcfg) {
		$ERROR = "GraphCFG for UUID:$UUID could not be loaded";
		}
	else {
		($graphcfg->{'.start'}, $graphcfg->{'.stop'}) = &KPIBI::relative_to_current($graphcfg->{'%'}->{'period'});
		}
	}

$graphcfg->{'ts'} = time();

if ($ERROR) {
	print qq~<!-- $ERROR -->~;	
	exit;
	}
#else {
#	print Dumper(\%ENV);
#	}


print sprintf("USER=%s UUID=%s GRAPH=%s<br>",$USER,$UUID,$graphcfg->{'GRAPH'});
print sprintf("START=%s STOP=%s<br>",$graphcfg->{'.start'},$graphcfg->{'.stop'});


my $DATAVAR = $DIVID;
$DATAVAR =~ s/[^A-Za-z0-9]//gs; $DATAVAR = "x$DATAVAR";

my @JS = ();
push @JS, qq~google.load("visualization", "1", {packages:["imagebarchart","corechart"]});~;
push @JS, qq~var $DATAVAR = new google.visualization.DataTable();~;
push @JS, qq~$DATAVAR.addColumn('string','Date');~;

my %params = ();
## these parameters are the same for all charts:
## chtt: chart title
$params{'chtt'} = $graphcfg->{'TITLE'};

#foreach my $dt ( &KPIBI::dt_series($graphcfg->{'.start'},$graphcfg->{'.stop'}) ) {
my $dt_start = &KPIBI::yyyymmdd_to_dt($graphcfg->{'.start'});
my $dt_stop = &KPIBI::yyyymmdd_to_dt($graphcfg->{'.stop'});

my @DTS = &KPIBI::dt_series($dt_start,$dt_stop);
push @JS, sprintf("$DATAVAR.addRows(%d);",scalar(@DTS));

my $row = 0;
my %DT_ROW_LOOKUP = ();
foreach my $dt ( @DTS ) {
	my $pretty = &KPIBI::dt_to_shortpretty($dt);
	push @JS, qq~$DATAVAR.setValue($row, 0, '$pretty');~;
	$DT_ROW_LOOKUP{$dt} = $row;
	$row++;
	}

my @DATASET_MAX = 0;
foreach my $set (1..3) {
	my $dataset = sprintf("dataset-%d",$set);
	my $dsn = $graphcfg->{'%'}->{$dataset};
	next unless ($dsn ne '');
	my $dsnparams = &ZTOOLKIT::urlparams($dsn);
	push @JS, "$DATAVAR.addColumn('number', '$dsnparams->{'t'}');";

	my ($result) = $KPI->get_data($graphcfg->{'%'}->{$dataset},$graphcfg->{'.start'},$graphcfg->{'.stop'});
	# print Dumper($result);
	my @d = ();
	my $max = undef;
	foreach my $line (@{$result}) {
		my $rowid = $DT_ROW_LOOKUP{ sprintf("%05d",$line->[0]) };
		if (not defined $rowid) { $rowid = 0; }
		my $data = $line->[1];
		push @JS, "$DATAVAR.setValue($rowid, $set, $data); /* $line->[0] */";
		if (not defined $max) { $max = $line->[1]; }
		elsif ($line->[1]>$max) { $max = $line->[1]; }
		}
	}


if (1) {

	print qq~
<div id="$DIVID-chart"></div>
<script type="text/javascript">
	~;

	foreach my $js (@JS) {
		print "$js\n";
		}

	my $TITLE = $graphcfg->{'TITLE'};	
	print qq~
 var chart = new google.visualization.ImageBarChart(document.getElementById('$DIVID-chart'));
 // var chart = new google.visualization.ImageAreaChart(document.getElementById('$DIVID-chart'));
 chart.draw($DATAVAR, {width: 800, height: 600, min: 0, title: '$TITLE'});

 // var chart = new google.visualization.LineChart(document.getElementById('$DIVID-chart'));
 //var chart = new google.visualization.BarChart(document.getElementById('$DIVID-chart'));
 //var chart = new google.visualization.ColumnChart(document.getElementById('$DIVID-chart'));
 //chart.draw($DATAVAR, {width: 400, height: 240, title: 'Company Performance',
 //                        vAxis: {title: 'Year', titleTextStyle: {color: 'red'}}
 //                        });

    </script>
~;


#	foreach my $k (keys %params) {
#		print sprintf(qq~<input type=hidden name=$k value="%s">\n~,&ZOOVY::incode($params{$k}));
#		$data .= "$k=".&ZOOVY::incode($params{$k})."&";
#		}
#	chop($data);
#	print qq~<input type=submit>~;
#	print qq~</form>~;
#	print qq~<script type="text/javascript">
#alert("$data");
#jQuery.post("http://chart.apis.google.com/chart",
#"$data",function(data) {
#	alert(data);
# 	\$('#$DIVID').html(data);
#});
#</script>~;
	print "hello";
	}
