#!/usr/bin/perl

use Data::Dumper;
use strict;
use JSON::XS;
use URI::Escape;
use lib "/httpd/modules";
require ZOOVY;
require ZTOOLKIT;
require GTOOLS;
require LUSER;
require KPIBI;

## note: requires reports access
my ($LU) = LUSER->authenticate(flags=>'_M&2');
if (not defined $LU) { exit; }

my @MSGS = ();

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- PRT -->'} = $PRT;
$GTOOLS::TAG{'<!-- COLLECTION -->'} = $ZOOVY::cgiv->{'collection'};

my $template_file = 'index.shtml';

my ($VERB) = $ZOOVY::cgiv->{'VERB'};
# if ($VERB eq '') { $VERB = 'SHOW'; }
print STDERR "VERB: $VERB\n";

my $KPI = KPIBI->new($USERNAME,$PRT);

if ($KPI->is_aggregate()) {
	push @MSGS, "WARN|You are a super-user and are being displayed aggregated data for all clusters.";
	}

if ($VERB eq '') {
	$VERB = 'SHOW';
	my ($kpiv) = &ZWEBSITE::globalfetch_attrib($USERNAME,'kpi-version');
#	if ($USERNAME eq 'toynk') {
#		## they are the master list right now.
#		}
	if ($kpiv == 0) {
		$VERB = 'INITIALIZE';
		}
	print STDERR "KPI: $kpiv\n";
	}




if ($VERB eq 'SAVE-ORDER') {
	## verbdata will contain a comma separated list of guid's
	my ($order) = $ZOOVY::cgiv->{'verbdata'};
	my @GUIDS = split(/,/,$order);	

	my $collection = int($ZOOVY::cgiv->{'collection'});
	$KPI->save_collection_order($collection,\@GUIDS);

	# print STDERR "ORDER: $order\n";
	$VERB = 'SHOW';
	}

if ($VERB eq 'INITIALIZE') {
	my $pstmt = "delete from KPI_USER_GRAPHS where IS_SYSTEM>0 and MID=$MID /* $USERNAME */";
	print STDERR $pstmt."\n";
	$KPI->udbh()->do($pstmt);

	## load the default list of collections
	#mysql> desc KPI_USER_COLLECTIONS;
	#+---------+------------------+------+-----+---------------------+----------------+
	#| Field   | Type             | Null | Key | Default             | Extra          |
	#+---------+------------------+------+-----+---------------------+----------------+
	#| ID      | int(10) unsigned | NO   | PRI | NULL                | auto_increment |
	#| MID     | int(10) unsigned | NO   | MUL | 0                   |                |
	#| PRT     | tinyint(4)       | NO   |     | 0                   |                |
	#| TITLE   | varchar(60)      | NO   |     | NULL                |                |
	#| CREATED | datetime         | NO   |     | 0000-00-00 00:00:00 |                |
	#+---------+------------------+------+-----+---------------------+----------------+
	#5 rows in set (0.00 sec)
	my %SYSTEM_COLLECTION_LOOKUP = ();
	open F, "</httpd/htdocs/biz/kpi/collections.txt";
	while (<F>) {
		chomp();
		next if ($_ eq '');
		next if (substr($_,0,1) eq '#');	# skip lines that start with a #
		my ($id,$title) = split(/\|/,$_,2);

		my $pstmt = "select ID from KPI_USER_COLLECTIONS where MID=$MID and IS_SYSTEM=".int($id);
		my ($dbID) = $KPI->udbh()->selectrow_array($pstmt);
		print STDERR "DBID: $dbID\n";
		if (not defined $dbID) {
			my $pstmt = &DBINFO::insert($KPI->udbh(),'KPI_USER_COLLECTIONS',{
				ID=>0,IS_SYSTEM=>$id,MID=>$MID,PRT=>$PRT,TITLE=>$title,'*CREATED'=>'now()'
				},sql=>1);
			$KPI->udbh()->do($pstmt);

			$pstmt = "select last_insert_id()";
			($dbID) = $KPI->udbh->selectrow_array($pstmt);
			}
		$SYSTEM_COLLECTION_LOOKUP{ $id} = $dbID;
		}
	# print STDERR Dumper(\%SYSTEM_COLLECTION_LOOKUP);
	close F;

	#mysql> desc KPI_USER_GRAPHS;
	#+------------+------------------+------+-----+---------+-------+
	#| Field      | Type             | Null | Key | Default | Extra |
	#+------------+------------------+------+-----+---------+-------+
	#| UUID       | varchar(32)      | NO   | PRI | NULL    |       |
	#| USERNAME   | varchar(20)      | NO   |     | NULL    |       |
	#| MID        | int(10) unsigned | NO   | PRI | 0       |       |
	#|  CREATED    | datetime         | YES  |     | NULL    |       |
	#| GRAPH      | varchar(20)      | NO   |     | NULL    |       |
	#| TITLE      | varchar(60)      | NO   |     | NULL    |       |
	#| CONFIG     | text             | NO   |     | NULL    |       |
	#| COLLECTION | int(10) unsigned | NO   |     | 0       |       |
	#+------------+------------------+------+-----+---------+-------+
	#8 rows in set (0.00 sec)

	require YAML::Syck;
	my $guids = YAML::Syck::LoadFile("/httpd/htdocs/biz/kpi/default-graphs.yaml");
	foreach my $guid (keys %{$guids}) {
		$guids->{$guid}->{'USERNAME'} = $USERNAME;
		$guids->{$guid}->{'MID'} = $MID;
		$guids->{$guid}->{'COLLECTION'} = $SYSTEM_COLLECTION_LOOKUP{ $guids->{$guid}->{'IS_SYSTEM'} };
		if ($guids->{$guid}->{'COLLECTION'} == 0) {
			warn sprintf("Could not resolve SYSTEM_COLLECTION for IS_SYSTEM=%s\n",$guids->{$guid}->{'IS_SYSTEM'});
			}
		else {
			my ($pstmt) = &DBINFO::insert($KPI->udbh(),'KPI_USER_GRAPHS',$guids->{$guid},sql=>1);
			print STDERR $pstmt."\n";
			$KPI->udbh()->do($pstmt);
			}
		}	

	# &ZWEBSITE::globalset_attribs($USERNAME,'kpi-version',1);
	$VERB = 'SHOW';
	}


if ($VERB eq 'SAVE-COLLECTION') {
	$KPI->create_collection($ZOOVY::cgiv->{'title'});
	$VERB = 'COLLECTIONS';
	}

if ($VERB eq 'NUKE-COLLECTION') {
	$KPI->nuke_collection($ZOOVY::cgiv->{'ID'});
	$VERB = 'COLLECTIONS';
	}

##
##
if ($VERB eq 'NUKE-GRAPH') {
	my ($UUID) = $ZOOVY::cgiv->{'UUID'};
	$KPI->nuke_graphcfg($UUID);
	$VERB = 'COLLECTIONS';
	}


if ($VERB eq 'COLLECTIONS') {
	my $c = '';
	my $r = '';
	foreach my $ref (@{$KPI->user_collections()}) {
		my $RESULTS = $KPI->list_graphcfgs('COLLECTION'=>$ref->{'ID'});
		$c .= "<tr class='zoovytableheader'>";
		$c .= "<td nowrap>";
		if (scalar(@{$RESULTS})==0) {
			$c .= qq~<input type='button' class='minibutton' onClick="navigateTo('index.cgi?VERB=NUKE-COLLECTION&ID=$ref->{'ID'}');" value="Delete">~;
			}
		$c .= qq~<input type='button' class='minibutton' onClick="navigateTo('index.cgi?VERB=ADD-GRAPH&collection=$ref->{'ID'}');" value="Add">~;
		$c .= "</td>";		
		# $c .= "<td>\#$ref->{'ID'}</td>";
		$c .= "<td width=\"90%\">".&ZOOVY::incode($ref->{'TITLE'})."</td>";
		$c .= "</tr>";

		$c .= "<tr><td>&nbsp;</td><td colspan=3><table width=100%>";
		if (scalar(@{$RESULTS})==0) {
			$c .= "<tr><td><div class=\"warning\">There are no graphs configured in this collection</i></td></tr>";
			}
		else {
			$c .= qq~
	<tr class="zoovysub1header">
		<td></td>
		<td>TITLE</td>
		<td>TYPE</td>
		<td>SIZE</td>
		<td>PERIOD</td>
		<td>GRPBY</td>
	</tr>
	~;
			}
		foreach my $ref (@{$RESULTS}) {
			# $c .= "<tr><td colspan=3>".Dumper($ref)."</td></tr>";
			$c .= "<tr>";
			$c .= qq~<td width=100>~;
			$c .= qq~<input type='button' class='minibutton' onClick="navigateTo('index.cgi?VERB=NUKE-GRAPH&UUID=$ref->{'UUID'}');" value="Delete">~;
			$c .= qq~<input type='button' class='minibutton' onClick="navigateTo('index.cgi?VERB=EDIT-GRAPH&UUID=$ref->{'UUID'}');" value="Edit">~;
			$c .= qq~</td>~;
			$c .= qq~<td>$ref->{'TITLE'}</a></td>~;
			$c .= qq~<td>$ref->{'GRAPH'}</a></td>~;
			$c .= qq~<td>$ref->{'SIZE'}</a></td>~;
			$c .= qq~<td>$ref->{'PERIOD'}</a></td>~;
			$c .= qq~<td>$ref->{'GRPBY'}</a></td>~;
			$c .= "</tr>\n";
			}
		$c .= "\n</table><br><br></td></tr>\n";
		}
	if ($c eq '') {
		$c = "<tr><td><i>No existing collections</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- EXISTING_COLLECTIONS -->'} = $c;

	##
	##

	$template_file = 'collections.shtml';
	}





if ($VERB eq 'COPY-GRAPH') {
	my ($UUID) = $ZOOVY::cgiv->{'UUID'};
	my $graphref = $KPI->get_graphcfg($UUID);

	delete $graphref->{'UUID'};
	my $GRAPHID = $graphref->{'GRAPH'};
	my $TITLE = "New Graph (copy: $UUID)";
	my $COLLECTION = $graphref->{'COLLECTION'};
	$graphref->{'size'} = $graphref->{'SIZE'};
	$graphref->{'period'} = $graphref->{'PERIOD'};
	$graphref->{'grpby'} = $graphref->{'GRPBY'};
	$graphref->{'columns'} = $graphref->{'COLUMNS'};

	($UUID) = $KPI->store_graphcfg('',$GRAPHID,$TITLE,$COLLECTION,$graphref);
	if ($UUID ne '') {
		$ZOOVY::cgiv->{'UUID'} = $UUID;
		$VERB = 'GRAPHS';
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>Successfully copied UUID: $UUID</div>";
		}
	}


##
##
if (($VERB eq 'SAVE-GRAPH') || ($VERB eq 'PREVIEW-GRAPH')) {
	$VERB = 'GRAPHS';	
	my ($UUID) = $ZOOVY::cgiv->{'UUID'};
	my ($GRAPHID) = $ZOOVY::cgiv->{'graph'};
	my ($TITLE) = $ZOOVY::cgiv->{'title'};
	my ($COLLECTION) = int($ZOOVY::cgiv->{'collection'});

	my %config = ();

	#mysql> desc KPI_USER_GRAPHS;
	#+------------+------------------+------+-----+---------+-------+
	#| Field      | Type             | Null | Key | Default | Extra |
	#+------------+------------------+------+-----+---------+-------+
	#| UUID       | varchar(32)      | NO   | PRI | NULL    |       |
	#| USERNAME   | varchar(20)      | NO   |     | NULL    |       |
	#| MID        | int(10) unsigned | NO   | PRI | 0       |       |
	#| CREATED    | datetime         | YES  |     | NULL    |       |
	#| GRAPH      | varchar(20)      | NO   |     | NULL    |       |
	#| TITLE      | varchar(60)      | NO   |     | NULL    |       |
	#| CONFIG     | text             | NO   |     | NULL    |       |
	#| COLLECTION | int(10) unsigned | NO   |     | 0       |       |
	#| SIZE       | varchar(6)       | NO   |     | NULL    |       |
	#| PERIOD     | varchar(20)      | NO   |     | NULL    |       |
	#| GRPBY      | varchar(10)      | NO   |     | NULL    |       |
	#| COLUMNS    | int(10) unsigned | NO   |     | 0       |       |
	#+------------+------------------+------+-----+---------+-------+
	#12 rows in set (0.00 sec)

	my $graphref = $KPI->get_graphref($GRAPHID);
	if (defined $graphref) {
		## setup global variables such as period
		$config{'period'} = $ZOOVY::cgiv->{'period'};
		$config{'size'} = $ZOOVY::cgiv->{'size'};
		$config{'grpby'} = $ZOOVY::cgiv->{'grpby'};
		$config{'columns'} = $ZOOVY::cgiv->{'columns'};
		$config{'user-json'} = $ZOOVY::cgiv->{'user-json'};
		if ($config{'columns'}==0) {
			my ($dsid,$dsparams) = &ZTOOLKIT::dsnparams($ZOOVY::cgiv->{"ddataset"});
			$dsparams->{'fmt'} = $ZOOVY::cgiv->{"dformat"};
			$config{"ddataset"} = &ZTOOLKIT::builddsn($dsid,$dsparams);
			}
		elsif ($config{'columns'}>0) {
			## now store each selected dataset.
			my $i = 1;
			while ($i <= $config{'columns'}) {
				my ($dsid,$dsparams) = &ZTOOLKIT::dsnparams($ZOOVY::cgiv->{"dataset-$i"});
				$dsparams->{'fmt'} = $ZOOVY::cgiv->{"format-$i"};
				$config{"dataset-$i"} = &ZTOOLKIT::builddsn($dsid,$dsparams);
				$i++;
				}
			}
		}


	print STDERR "UUID: $UUID\n";
	($UUID) = $KPI->store_graphcfg($UUID,$GRAPHID,$TITLE,$COLLECTION,\%config);
	if ($UUID ne '') {
		$ZOOVY::cgiv->{'UUID'} = $UUID;
		$VERB = 'GRAPHS';
		$GTOOLS::TAG{'<!-- MESSAGE -->'} = "<div class='success'>Successfully saved UUID: $UUID</div>";
		}
	}


##
##
##
if (($VERB eq 'GRAPHS') || ($VERB eq 'ADD-GRAPH') || ($VERB eq 'EDIT-GRAPH') || ($VERB eq 'PREVIEW-GRAPH')) {

	

	my $graphref = undef;
	my $UUID = $ZOOVY::cgiv->{'UUID'};
	print STDERR "VERB: $VERB UUID: $UUID\n";
	if ($UUID ne '') {
		$graphref = $KPI->get_graphcfg($UUID);
		}

	if ($VERB eq 'GRAPHS') {
		## this is a reload
		}
	elsif (($VERB eq 'ADD-GRAPH') || ($UUID eq '')) {
		}
	elsif ($VERB eq 'PREVIEW-GRAPH') {
		}
	else {
		# print "UUID: $UUID\n";
		$ZOOVY::cgiv->{'collection'} = $graphref->{'COLLECTION'};
		$ZOOVY::cgiv->{'UUID'} = $graphref->{'UUID'};
		$ZOOVY::cgiv->{'title'} = $graphref->{'TITLE'};
		$ZOOVY::cgiv->{'graph'} = $graphref->{'GRAPH'};
		$ZOOVY::cgiv->{'size'} = $graphref->{'SIZE'};
		$ZOOVY::cgiv->{'columns'} = $graphref->{'COLUMNS'};
		$ZOOVY::cgiv->{'period'} = $graphref->{'PERIOD'};
		$ZOOVY::cgiv->{'grpby'} = $graphref->{'GRPBY'};
		$ZOOVY::cgiv->{'user-json'} = $graphref->{'%'}->{'user-json'};
		if ($graphref->{'COLUMNS'}==0) {
			## dynamic dataset's have no columns
			$ZOOVY::cgiv->{'ddataset'} = $graphref->{'%'}->{'ddataset'};
			my ($dsid,$dsparams) = &ZTOOLKIT::dsnparams($graphref->{'%'}->{'ddataset'});
			$ZOOVY::cgiv->{'dformat'} = $dsparams->{'fmt'};
			}
		else {
			## otherwise, load each column from the config.
			foreach my $i (1..$graphref->{'COLUMNS'}) {
				$ZOOVY::cgiv->{"dataset-$i"} = $graphref->{'%'}->{"dataset-$i"};
				my ($dsid,$dsparams) = &ZTOOLKIT::dsnparams($graphref->{'%'}->{"dataset-$i"});
				$ZOOVY::cgiv->{"format-$i"} = $dsparams->{'fmt'};
				}
			}
		}

	if ($UUID ne '') {
		print STDERR "PREVIEW ".Dumper($UUID,$graphref);
		my $JSON = $KPI->makejson($graphref,'preview');
		$GTOOLS::TAG{'<!-- GRAPHJS -->'} .= qq~
<script type="text/javascript">
var preview; 
jQuery(document).ready(function() {
      preview = new Highcharts.Chart($JSON);
		});
</script>
~;
		}

	$template_file = 'graphs.shtml';
	my $c = '';

	my %COLLECTIONS = ();
	$c = '';
	$c .= "<option value=\"0\">New Collection</option>";
	foreach my $ref (@{$KPI->user_collections()}) {
		my $selected = ($ZOOVY::cgiv->{'collection'} eq $ref->{'ID'})?'selected':'';
		$c .= "<option $selected value=\"$ref->{'ID'}\">$ref->{'TITLE'}</option>";
		$COLLECTIONS{ $ref->{'ID'} } = $ref->{'TITLE'};
		}
	$GTOOLS::TAG{'<!-- COLLECTIONS -->'} = $c;

	$c = '';
	foreach my $g (@KPIBI::GRAPHS) {
		my $selected = '';
		my ($selected) = '';
		if ($ZOOVY::cgiv->{'graph'} eq $g->{'id'}) {
			$selected = 'selected';
			$graphref = $g;
			}		
		$c .= sprintf("<option $selected value=\"%s\">%s</option>",$g->{'id'},$g->{'title'});
		}
	$GTOOLS::TAG{'<!-- GRAPHS -->'} = $c;
	$GTOOLS::TAG{'<!-- TITLE -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'title'});

	$c = '';
	foreach my $id (sort keys %KPIBI::SIZES) {
		my $sizeref = $KPIBI::SIZES{$id};
		my ($selected) = ($id eq $ZOOVY::cgiv->{'size'})?'selected':'';
		$c .= "<option $selected value=\"$id\">$sizeref->{'title'}</option>";
		}
	$GTOOLS::TAG{'<!-- SIZES -->'} = $c;
	

	my $columns = undef;
	if (not defined $graphref) {
		$c = qq~<tr><td><div class="hint">HINT: Please select a graph type</div></td></tr>~;
		}	
	elsif (defined $graphref) {
		## if graphref is set then we are displaying the option to choose one or more datasets.
		$c = '';

		$c .= qq~
		<tr>
			<td>Data Columns</td>
			<td>
				<select onChange="jQuery('#thisFrm').showLoading(); thisFrm.VERB.value='GRAPHS'; thisFrm.submit();" name="columns">
				<option value="0">0 - Dynamic Datasets</option>
				~;
		$columns = int($ZOOVY::cgiv->{'columns'});
		for my $i (1..60) {
			my ($selected) = ($i == $columns)?'selected':'';
			$c .= "<option $selected value=\"$i\">$i column(s)</option>";
			}
		$c .= qq~</select>
			</td>
		</tr>
		<tr>
			<td>Report Period:</td>
			<td>
			<select name="period">
			~;
			foreach my $p (@KPIBI::PERIODS) {
				# $p = [ 'period', 'pretty ];
				my ($selected) = ($p->[0] eq $ZOOVY::cgiv->{"period"})?'selected':'';
				$c .= sprintf("<option $selected value=\"%s\">%s</option>",$p->[0],$p->[1]);
				}
			$c .= qq~
			</select>
		</td>
		</tr>
		<tr>
			<td>Grouping:</td>
			<td>
			<select name="grpby">
			~;
			foreach my $s (@KPIBI::GRPBY) {
				my ($selected) = ($s->[0] eq $ZOOVY::cgiv->{'grpby'})?'selected':'';
				$c .= "<option $selected value=\"$s->[0]\">$s->[1]</option>";
				}
		$c .= qq~
			</select>
			</td>
		</tr>
		~;
		}

	my $HAS_ALIGNMENT_ERROR = 0;
	if ($ZOOVY::cgiv->{'grpby'} eq 'none') {
		## 'none' type will merge into one big value, useful for sales last quarter
		}
	elsif ($ZOOVY::cgiv->{'grpby'} eq 'day') {
		## no possible issues with grouping because there isn't any lower level data
		}
	elsif ($ZOOVY::cgiv->{'grpby'} eq 'dow') {
		## we should probably check to make sure they're using an average
		}
	elsif ($ZOOVY::cgiv->{'grpby'} eq 'week') {
		if ($ZOOVY::cgiv->{'period'} !~ /^(dow|week)/) {
			$HAS_ALIGNMENT_ERROR++;
			}
		}
	elsif ($ZOOVY::cgiv->{'grpby'} eq 'month') {
		if ($ZOOVY::cgiv->{'period'} !~ /^(month|quarter)/) {
			$HAS_ALIGNMENT_ERROR++;
			}
		}
	elsif ($ZOOVY::cgiv->{'grpby'} eq 'quarter') {
		if ($ZOOVY::cgiv->{'period'} !~ /^(month|quarter)/) {
			$HAS_ALIGNMENT_ERROR++;
			}
		}

	if ($HAS_ALIGNMENT_ERROR) {
		$c .= "<tr><td colspan=2><div class='warning'>
You have selected a grouping type ($ZOOVY::cgiv->{'grpby'}) that does not align properly with your period ($ZOOVY::cgiv->{'period'}), this will generate
graphs which will likely cause the viewer to make highly inaccurate conclusions due to excluded data.
<div class='hint'>
WHAT CAUSES THIS MESSAGE: 
The most common cause of this message is when the selected reporting period is relative 
ex: Last 4 Weeks (which would be the last Monday, minus 28 days), 
and the grouping is using a different day such as Month (which would summarize the 1st through the last day of the month). 
These groupings and report periods are incompatible because not every month starts on a Monday, 
and so the first month of data in the graph would summarize an incomplete data-set (it would say 'Feb' as the month, but would
not have all the data for February.)<br>
<br>
For example if the report was viewed on the
12th of March, which was a Wednesday, then the report period would be the 10th of March (Monday) minus 28 days which would be
the 10th of Feb (in a non leap year), or the 9th of Feb (in a leap year) - HOWEVER the graph would be summarized into two
months Feb, and March -- with Feb data showing Feb 9th, or 10th through Feb 28th, or 29th, and March showing the 1st through
the 12th (current day). The next day the graph for Feb will get smaller (because less days in Feb will be included), and March
will get bigger. 
This graph - while it may be fun to create is not useful since you're not able to compare similar data sets.
There are cases where this type of warning can be ignored (specifically for reports looking at average values, 
where the alignment of data is not important, and in fact having an incompatible window might even be considered useful).
</div>
</div></td></tr>";
		}

	if ((not defined $columns) || (not defined $graphref)) {
		## don't let them configure a column till they pick a graph type!
		}
	elsif ($columns>0) {
		my $i = 0;
		while ( $i < $columns ) {
			$i++;

			$c .= qq~
			<tr>
				<td colspan="2">&nbsp;</td>
			</tr>
			<tr>
				<td>Dataset Axis-$i:</td>
				<td>
					<select name="dataset-$i">
					~;
					## $selected is a bit squirrly since $d->[0] will be something like: OGMS?c=2&f=#
					## and $ZOOVY::cgiv->{'dataset-$i'} will be something like: OGMS?c=1&f=$&t=All Orders (GMS $)
					## so we *actually* only need to match on the URI + 'c' param value + 'fm'
					my ($cgivuri,$cgivuriparams) = &ZTOOLKIT::dsnparams($ZOOVY::cgiv->{"dataset-$i"});
					foreach my $d ($KPI->user_datasets()) {
						my ($dsnid,$dsparams) = &ZTOOLKIT::dsnparams($d->[0]);
						my ($selected) = '';
						if ($d->[0] eq $ZOOVY::cgiv->{"dataset-$i"}) {
							## best case (this will never happen since fmt is not specified here)
							$selected = 'selected';
							}
						elsif (
								($dsnid eq $cgivuri) && 
								($cgivuriparams->{'c'} eq $dsparams->{'c'}) &&
								($cgivuriparams->{'fm'} eq $dsparams->{'fm'}) &&
								($cgivuriparams->{'ctype'} eq $dsparams->{'ctype'})
								) {
							## worst case
							$selected = 'selected';
							}
						$c .= sprintf("<option $selected value=\"%s&t=%s\">%s</option>",$d->[0],$d->[1],$d->[1]);
						}
					$c .= qq~
					</select>
				</td>
			</tr>
			<tr>
				<td>Format Axis-$i:</td>
				<td>
				<select name="format-$i">
				~;
				foreach my $f (@KPIBI::DATA_FORMATTING) {
					my ($selected) = ($f->[0] eq $ZOOVY::cgiv->{"format-$i"})?'selected':'';
					$c .= "<option $selected value=\"$f->[0]\">$f->[1]</option>";
					}
				$c .= qq~
				</select>
				</td>
			</tr>
			~;
			}
		}
	else {
		$c .= qq~
		<tr>
			<td colspan="2">&nbsp;</td>
		</tr>
		<tr>
			<td>Dynamic DataSets</td>
			<td>
				<select name="ddataset">
				~;
			foreach my $dd (@KPIBI::DYNDATASETS) {
				my ($selected) = ($dd->[0] eq $ZOOVY::cgiv->{'ddataset'})?'selected':'';
				$c .= "<option $selected value=\"$dd->[0]\">$dd->[1]</option>\n";
				}
			$c .= qq~
				</select>
			</td>
			</tr>
			<tr>
				<td>Format Axis:</td>
				<td>
				<select name="dformat">
				~;
				foreach my $df (@KPIBI::DATA_FORMATTING) {
					my ($selected) = ($df->[0] eq $ZOOVY::cgiv->{"dformat"})?'selected':'';
					$c .= "<option $selected value=\"$df->[0]\">$df->[1]</option>";
					}
				$c .= qq~
				</select>
				</td>
			</tr>
			~;
		}



	if ($ZOOVY::cgiv->{'UUID'} ne '') {	
		$c .= qq~<tr>
			<td colspan="2">Additional Parameters:
<div class="hint">Optional parameters to customize the display behavior of highcharts.</div>
<textarea onClick="this.rows=15;" cols=60 name="user-json">~.&ZOOVY::incode($ZOOVY::cgiv->{'user-json'}).qq~</textarea>
			</td>
		</tr>
		~;
		}


	if ($UUID ne '') {
		$GTOOLS::TAG{'<!-- BUTTONS -->'} = qq~
<input type="button" class="button" value=" Copy " onClick="thisFrm.VERB.value='COPY-GRAPH'; thisFrm.submit();">
<!--
<input type="button" class="button" value=" Preview " onClick="thisFrm.VERB.value='PREVIEW-GRAPH'; thisFrm.submit();">
-->
~;
		}

	$GTOOLS::TAG{'<!-- UUID -->'} = $ZOOVY::cgiv->{'UUID'};
	$GTOOLS::TAG{'<!-- GRAPH_CONFIG -->'} = $c;
	}


if ($VERB eq 'SHOW') {
	$template_file = 'index.shtml';
	my @DIVS;
	my ($KPI) = KPIBI->new($USERNAME,$PRT);

	## STAGE1: OUTPUT LEFT HAND NAVIGATION
	my @COLLECTIONS = @{$KPI->user_collections()};
	#my @COLLECTIONS = ('Collection1','Collection2','Collection3');
	my $collection = int($ZOOVY::cgiv->{'collection'});
	if ($collection==0) { $collection = $COLLECTIONS[0]->{'ID'}; }
	my $c = '';
	foreach my $cref (@COLLECTIONS) {
		my ($class) = ($cref->{'ID'} eq $collection)?'selected':'';
		$c .= qq~<div class=\"$class\"><a href=\"javascript:navigateTo('/biz/kpi/index.cgi?collection=$cref->{'ID'}');\">$cref->{'TITLE'}</a></div>~;
		}
	$GTOOLS::TAG{'<!-- COLLECTIONS -->'} = $c;


	## STAGE2: OUTPUT THE GRAPHS ON THIS PAGE.
	$GTOOLS::TAG{'<!-- GRAPHJS -->'} = '';
	$c = '';
	my $grefs = $KPI->list_graphcfgs('COLLECTION'=>$collection);
	if (not defined $grefs) { $grefs = []; }


	# $grefs = [ $grefs->[0] ];

	my $i = 0;
	foreach my $g (@{$grefs}) {
		my $containerid = sprintf("container%d",++$i);
		## each $g is a graph, which will be output separately.
		my $class = $g->{'%'}->{'size'};
		my $style = '/* invalid size */';
#		my $width = 100;
		if (defined $KPIBI::SIZES{$class}) { 
			$style = $KPIBI::SIZES{$class}->{'style'}; 
#			$width = $KPIBI::SIZES{$class}->{'width'}; 
#			$width = $width - 20;
			}

		my $UUID = $g->{'UUID'};
		$GTOOLS::TAG{'<!-- GRAPHS -->'} .= qq~<li class="ui-state-default $class" id='$containerid' style='$style'>$UUID</li>\n~;

		# $GTOOLS::TAG{'<!-- GRAPHS -->'} .= qq~<li>~.Dumper($g).qq~</li>~;

		my $JSON = $KPI->makejson($g,$containerid);

		$GTOOLS::TAG{'<!-- GRAPHJS -->'} .= qq~
<script type="text/javascript">
var $containerid; 
jQuery(document).ready(function() {
      $containerid = new Highcharts.Chart($JSON);
		});
</script>
~;

#		$GTOOLS::TAG{'<!-- GRAPHJSX -->'} = qq~
#<script type="text/javascript">
# 
#		var $containerid;
#		jQuery(document).ready(function() {
#			$containerid = new Highcharts.Chart({
#				chart: {
#					renderTo: '$containerid',
#					defaultSeriesType: 'line',
#					marginRight: 130,
#					marginBottom: 25
#				},
#				title: {
#					text: 'Monthly Average Temperature',
#					x: -20 //center
#				},
#				subtitle: {
#					text: 'Source: WorldClimate.com',
#					x: -20
#				},
#				xAxis: {
#					categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
#						'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
#				},
#				yAxis: {
#					title: {
#						text: 'Temperature (C)'
#					},
#					plotLines: [{
#						value: 0,
#						width: 1,
#						color: '#808080'
#					}]
#				},
#				tooltip: {
#					formatter: function() {
#			                return '<b>'+ this.series.name +'</b><br/>'+
#							this.x +': '+ this.y +'C';
#					}
#				},
#				legend: {
#					layout: 'vertical',
#					align: 'right',
#					verticalAlign: 'top',
#					x: -10,
#					y: 100,
#					borderWidth: 0
#				},
#				series: [{
#					name: 'Tokyo',
#					data: [7.0, 6.9, 9.5, 14.5, 18.2, 21.5, 25.2, 26.5, 23.3, 18.3, 13.9, 9.6]
#				}, {
#					name: 'New York',
#					data: [-0.2, 0.8, 5.7, 11.3, 17.0, 22.0, 24.8, 24.1, 20.1, 14.1, 8.6, 2.5]
#				}, {
#					name: 'Berlin',
#					data: [-0.9, 0.6, 3.5, 8.4, 13.5, 17.0, 18.6, 17.9, 14.3, 9.0, 3.9, 1.0]
#				}, {
#					name: 'London',
#					data: [3.9, 4.2, 5.7, 8.5, 11.9, 15.2, 17.0, 16.6, 14.2, 10.3, 6.6, 4.8]
#				}]
#			});
#			
#			
#		});
#	</script>
#
#~;

		}
		
	}



my @TABS = ();
push @TABS, { name=>'KPI/Dashboards',link=>'?VERB=SHOW',selected=>($VERB eq 'SHOW')?1:0 };
push @TABS, { name=>'Collections',link=>'?VERB=COLLECTIONS',selected=>($VERB eq 'COLLECTIONS')?1:0 };
# push @TABS, { name=>'Re-Initialize',link=>'?VERB=INITIALIZE',selected=>($VERB eq 'INITIALIZE')?1:0 };

&GTOOLS::output(file=>$template_file,tabs=>\@TABS,header=>1,jquery=>1,
	msgs=>\@MSGS,
	webdoc=>51600,
	headjs=>'<script src="/biz/kpi/highcharts-2.1.9/js/highcharts.js" type="text/javascript"></script>',
	);


__DATA__

