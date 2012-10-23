#!/usr/bin/perl


use Data::Dumper;
use JSON::XS;
use Storable;
use strict;
use lib "/httpd/modules";
require GTOOLS;
require DBINFO;
require ZOOVY;
require LUSER;
require INVENTORY;
require SEARCH;
require BATCHJOB;
require YAML::Syck;

&ZOOVY::init();
&GTOOLS::init();

my ($LU) = LUSER->authenticate(flags=>'_M&16');
if (not defined $LU) { warn "Auth"; exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { warn "No auth"; exit; }


my $VERB = $ZOOVY::cgiv->{'VERB'};
my $template_file = 'index.shtml';

## start by checking for a hash
my $dataref = {};
if ($ZOOVY::cgiv->{'DATA'} ne '') {
	$dataref = &ZTOOLKIT::deser($ZOOVY::cgiv->{'DATA'},1,0);
	}
else {
	## initialize defaults
	}

if (defined $ZOOVY::cgiv->{'JOBTITLE'}) {
	$dataref->{'JOBTITLE'} = $ZOOVY::cgiv->{'JOBTITLE'};
	}


if ($VERB eq 'LOOKUP') {
	my ($jobs) = BATCHJOB::find_jobs($USERNAME,JOB_TYPE=>'PPT');
	# my $jobs = [];
	
	my $c = '';
	foreach my $job (@{$jobs}) {
		$c .= "<tr>";
		$c .= "<td><a href=\"index.cgi?VERB=EDITJOB&JOBID=$job->{'ID'}\">$job->{'ID'}</a></td>";
		$c .= "<td>$job->{'TITLE'}</td>";
		$c .= "<td>$job->{'LUSERNAME'}</td>";
		$c .= "<td>".&ZTOOLKIT::pretty_date($job->{'CREATED_GMT'})."</td>";
		$c .= "<td>$job->{'STATUS'}</td>";
		$c .= "</tr>";		
		}

	if ($c eq '') {
		$c .= "<tr><td>No Jobs Found</td></tr>";
		}
	else {
		$c = qq~
<tr class="zoovysub1header">
	<td>Job ID</td>
	<td>Job Title</td>
	<td>Created By</td>
	<td>Created</td>
	<td>Status</td>
</tr>
$c
~;
		}
	$GTOOLS::TAG{'<!-- JOBS -->'} = $c;

	$template_file = 'lookup.shtml';
	}



if ($VERB eq 'EDITJOB') {
	my ($JOBID) = int($ZOOVY::cgiv->{'JOBID'});
	my ($bj) = BATCHJOB->new($USERNAME,$JOBID);

	my $vars = $bj->meta();

	$dataref->{'JOBID'} = $bj->id();
	$dataref->{'@ACTIONS'} = YAML::Syck::Load($vars->{'ACTIONS'});
	$dataref->{'PRODUCTS'} = $vars->{'PRODUCTS'};
	$dataref->{'JOBTITLE'} = $bj->{'TITLE'};

	$VERB = '';
	}


if ($VERB eq 'STARTBATCH') {
	## YAY!
	my %vars = ();
	$vars{'APP'} = 'PRODUCT_POWERTOOL';
	$vars{'ACTIONS'} = YAML::Syck::Dump($dataref->{'@ACTIONS'});
	$vars{'PRODUCTS'} = $dataref->{'PRODUCTS'};

	my $title = $ZOOVY::cgiv->{'jobtitle'};
	if ($title eq '') {
		$title = "Product Power Tool Job (purpose not specified)";
		}

	my ($JOBID) = int($dataref->{'JOBID'});

	my ($bj) = BATCHJOB->new($USERNAME,$JOBID,
		PRT=>$PRT,
		GUID=>&BATCHJOB::make_guid(),
		EXEC=>"UTILITY",
		TITLE=>$title,
		VARS=>&ZTOOLKIT::buildparams(\%vars,1),
		JOB_TYPE=>'PPT',
		'*LU'=>$LU,
		);

	require Digest::MD5;
	my ($action_digest) = Digest::MD5::md5_hex($vars{'ACTIONS'});
	my ($products_digest) = Digest::MD5::md5_hex($vars{'PRODUCTS'});

	if ($JOBID > 0) {
		## existing job
		$bj->update('BATCH_VARS'=>&ZTOOLKIT::buildparams(\%vars,1),'CREATED_GMT'=>time(),'TITLE'=>$title,'STATUS'=>'NEW','STATUS_MSG'=>'Job restarted');
		$LU->log("POWERTOOL.RESTART","Job $JOBID was restarted actions=[$action_digest] products=[$products_digest]","SAVE");
		}
	else {
		## this is a new job
		$JOBID = $bj->id();
		$LU->log("POWERTOOL.CREATED","Job $JOBID was created actions=[$action_digest] products=[$products_digest]","SAVE");
		}
	

	$template_file = '';
	print "Location: /biz/batch/index.cgi?VERB=LOAD&JOB=".$bj->id()."\n\n";
	exit;
	}

if ($VERB =~ /^ACTION-DEL\:([\d]+)$/) {
	my ($del) = $1;
	my $i = 0;
	my @keep = ();
	foreach my $ref (@{$dataref->{'@ACTIONS'}}) {
		next if ($i++ == $del);
		push @keep, $ref;
		}
	$dataref->{'@ACTIONS'} = \@keep;
	$VERB = '';
	}


if ($VERB eq 'ACTION-ADD') {
	my %ACTION = ();
	$ACTION{'verb'} = $ZOOVY::cgiv->{'verb'};
	$ACTION{'attrib'} = $ZOOVY::cgiv->{'attrib'};
	if ($ACTION{'attrib'} eq '_') {
		$ACTION{'attrib'} = $ZOOVY::cgiv->{'attrib_custom'};
		}
	if ($ACTION{'verb'} eq 'set') { 
		$ACTION{'value'} = $ZOOVY::cgiv->{'setval'}; 
		}
	if (($ACTION{'verb'} eq 'set-option') || ($ACTION{'verb'} eq 'nuke-option')) { 
		$ACTION{'attrib'} = 'finder';
		$ACTION{'value'} = $ZOOVY::cgiv->{'set-option'}; 
		}
	if ($ACTION{'verb'} eq 'copy') {
		$ACTION{'copyto'} = $ZOOVY::cgiv->{'copyto'};
		$ACTION{'copyto'} =~ s/[\s]+//g;
		}

	if ($ACTION{'verb'} eq 'copyfrom') {
		$ACTION{'copyfrom'} = $ZOOVY::cgiv->{'copyfrom'};
		$ACTION{'copyfrom'} =~ s/[\s]+//g;
		}

	if ($ACTION{'verb'} eq 'add') { $ACTION{'value'} = $ZOOVY::cgiv->{'addval'}; }
	if ($ACTION{'verb'} eq 'replace') { 
		$ACTION{'value'} = $ZOOVY::cgiv->{'searchval'}; 
		$ACTION{'replacewith'} = $ZOOVY::cgiv->{'replaceval'}; 
		}

	if ($ZOOVY::cgiv->{'when'} ne '') {
		$ACTION{'when'} = $ZOOVY::cgiv->{'when'};
		$ACTION{'when-attrib'} = $ZOOVY::cgiv->{'when-attrib'};
		if ($ACTION{'when'} eq 'when-attrib-contains') {
			$ACTION{'when-attrib-operator'} = $ZOOVY::cgiv->{'when-attrib-operator'};
			$ACTION{'when-attrib-contains'} = $ZOOVY::cgiv->{'when-attrib-contains'};
			}
		}


	if ($ACTION{'verb'} eq '') {
		## verb is required!
		$GTOOLS::TAG{'<!-- STEP2_ERRORS -->'} = "<div class='alert'>VERB is required</div>";
		}
	else {
		push @{$dataref->{'@ACTIONS'}}, \%ACTION;
		}
	$VERB = '';
	}




########################################################


if ($VERB eq 'CUSTOM') {
	$GTOOLS::TAG{'<!-- CHOOSER -->'} = q~
<font class='title'>Modify Product Power Tool</font><br>
<br>
Please Upload products separated by either commas, or hard returns.<br>
<textarea rows="10" cols="60" name="PRODUCTS"></textarea><br>
<i>HINT: You can also specify navigation categories or lists using the
safename of the category (one per line)<br>
<br>
~;
	$GTOOLS::TAG{'<!-- VERB -->'} = 'CUSTOM-SAVE';
	$GTOOLS::TAG{'<!-- HEADER -->'} = "Upload Custom Product List";
	$template_file = 'select.shtml';	
	}

if ($VERB eq 'CUSTOM-SAVE') {
	my %hash = &ZOOVY::fetchproducts_by_name($USERNAME);	
	my $ERRORS = '';
	my $prods = '';

	require NAVCAT;
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	my %matches = ();
	foreach my $line (split(/[\n\r]+/,$ZOOVY::cgiv->{'PRODUCTS'})) {
		if ($line =~ /^[\.\$]{1}/) {
			## line is a category
			my (@cat) = $NC->get($line);
			if (defined $cat[2]) {
				foreach my $pid (split(/,/,$cat[2])) {
					$matches{$pid}++;
					}
				}			
			}
		else {
			## line is a comma separated list of products
			foreach my $prod (split(/[^\w-]+/s,$line)) {
				# print STDERR "PRODUCT: $prod\n";
				if (defined $hash{$prod}) {
					$matches{$prod}++;
					}
				else {	
					$ERRORS .= "Product: $prod not found - discarded.<br>\n";
					}
				}
			}
		## end foreach line
		}
	$prods = join(",",keys %matches);
	$GTOOLS::TAG{'<!-- PRODUCT_ERRORS -->'} = "<font color='red'>".$ERRORS."</font>";
	$dataref->{'PRODUCTS'} = $prods;
	$VERB = '';
	}

########################################################

if ($VERB eq 'RANGE') {
	$GTOOLS::TAG{'<!-- VERB -->'} = 'RANGE-SAVE';
	$GTOOLS::TAG{'<!-- CHOOSER -->'} = qq~
<td>
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
<br>
</td>
~;
	$template_file = 'select.shtml';
	}

if ($VERB eq 'RANGE-SAVE') {
	my $prods = '';
	my @list = &ZOOVY::fetchproduct_list_by_merchant($USERNAME);
	my $start = $ZOOVY::cgiv->{'RSTART'};
	my $end = $ZOOVY::cgiv->{'REND'};
	if ($start gt $end) { my $t = $start; $start = $end; $end = $t; }
	foreach my $p (@list) {
		if (($start le $p) && ($end ge $p)) {
			$prods .= $p.',';
			}
		}
	chop($prods);
	$dataref->{'PRODUCTS'} = $prods;
	$VERB = '';
	}

########################################################


if ($VERB eq 'NAVCAT-SAVE') {
	$VERB = '';
	my $prods = '';
	my %prodref = ();
	my $count=0;

	require NAVCAT;
	my ($NC) = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		next if (substr($k,0,1) ne '!');
		my (undef,undef,$prods) = $NC->get(substr($k,1));
		foreach my $prod (split(/,/,$prods)) {
			$prodref{$prod}++;
			$count++;
			}
		}
	undef $NC;

	$prods = '';
	foreach my $k (keys %prodref) {
		$prods .= $k.',';
		}
	chop($prods);

	$dataref->{'PRODUCTS'} = $prods;
	}


if ($VERB eq 'NAVCAT') {
	my $c = '';
	my %prods = ();

	require NAVCAT;
	my $NC = NAVCAT->new($USERNAME,PRT=>$PRT);
	foreach my $safe (sort $NC->paths()) {
		my ($pretty) = $NC->get($safe);
		if ($safe eq '.') { $pretty = 'Homepage'; }
		$c .= "<tr>";
		$c .= "<td><input type='checkbox' name='!$safe'>$pretty</td>\n";
		$c .= "</tr>";
		}

	$GTOOLS::TAG{'<!-- CHOOSER -->'} = $c;
	$GTOOLS::TAG{'<!-- HEADER -->'} = 'Select Navcats';
	$GTOOLS::TAG{'<!-- VERB -->'} = 'NAVCAT-SAVE';

	$template_file = 'select.shtml';
	}


print STDERR "VERB: $VERB\n";
if ($VERB eq 'MCAT-SAVE') {
	$VERB = '';
	my $prods = '';
	my %prodref = ();
	my $count=0;

	require CATEGORY;
	foreach my $k (keys %{$ZOOVY::cgiv}) {
		next if (substr($k,0,1) ne '^');

		print STDERR "PID: $k\n";		
		foreach my $pid (@{&CATEGORY::products_by_category($USERNAME,substr($k,1))}) {
			$prodref{$pid}++;
			$count++;
			}
		}

	$prods = '';
	foreach my $k (keys %prodref) {
		$prods .= $k.',';
		}
	chop($prods);

	$dataref->{'PRODUCTS'} = $prods;
	}


if ($VERB eq 'MCAT') {
	my $c = '';
	my %prods = ();

	require CATEGORY;
	my ($arref) = &CATEGORY::listcategories($USERNAME);
	foreach my $cat (sort @{$arref}) {
		$c .= "<tr>";
		$c .= "<td><input type='checkbox' name='^$cat'>$cat</td>\n";
		$c .= "</tr>";
		}

	$GTOOLS::TAG{'<!-- CHOOSER -->'} = $c;
	$GTOOLS::TAG{'<!-- HEADER -->'} = 'Select Management Categories';
	$GTOOLS::TAG{'<!-- VERB -->'} = 'MCAT-SAVE';

	$template_file = 'select.shtml';
	}


########################################################
if ($VERB eq 'PROFILE-SAVE') {
	$VERB = '';
	require PRODUCT::BATCH;
	my $ARREF = &PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:profile',$ZOOVY::cgiv->{'PROFILE'});
	if (defined $ARREF) {	
		$dataref->{'PRODUCTS'} = join(',',@{$ARREF});
		}
	}


if ($VERB eq 'PROFILE') {
	my $PROFILES = &ZOOVY::fetchprofiles($USERNAME);
	my $c = '';
	foreach my $p (@{$PROFILES}) {
		$c .= qq~<input type="radio" name="PROFILE" value="$p"> $p<br>~;
		}
	$c = "<td>$c</td>";
	$GTOOLS::TAG{'<!-- CHOOSER -->'} = $c;
	$GTOOLS::TAG{'<!-- HEADER -->'} = "Select by Launch Profile";
	$GTOOLS::TAG{'<!-- VERB -->'} = "PROFILE-SAVE";
	$template_file = 'select.shtml';
	}


########################################################
if ($VERB eq 'SUPPLIER-SAVE') {
	$VERB = '';
	require PRODUCT::BATCH;
	my $ARREF = &PRODUCT::BATCH::list_by_attrib($USERNAME,'zoovy:prod_supplier',$ZOOVY::cgiv->{'SUPPLIER'});
	if (defined $ARREF) {	
		$dataref->{'PRODUCTS'} = join(',',@{$ARREF});
		}
	}


if ($VERB eq 'SUPPLIER') {
	require SUPPLIER;
	my $SUPPLIERS = &SUPPLIER::list_suppliers($USERNAME);
	my $c = '';
	foreach my $s (keys %{$SUPPLIERS}) {
		$c .= qq~<tr><td><input type="radio" name="SUPPLIER" value="$s"> $s<br></td></tr>~;
		}
	$GTOOLS::TAG{'<!-- CHOOSER -->'} = $c;
	$GTOOLS::TAG{'<!-- VERB -->'} = 'SUPPLIER-SAVE';
	$GTOOLS::TAG{'<!-- HEADER -->'} = "Select Products by Supplier";
	$template_file = 'select.shtml';
	}


########################################################
if ($VERB eq 'SELECTALL') {
	$VERB = '';
	$dataref->{'PRODUCTS'} = '~ALL';
	}

##
if ($VERB eq 'LIST-SAVE') {
	$VERB = '';
	my $prods = '';
	foreach my $p (keys %{$ZOOVY::cgiv}) {
		next if (substr($p,0,1) ne '_');
		$prods .= substr($p,1).',';
		}
	chop($prods);
	$dataref->{'PRODUCTS'} = $prods;
	}

if ($VERB eq 'LIST') {
	$template_file = 'select.shtml';
	$GTOOLS::TAG{'<!-- HEADER -->'} = 'Select Products Individually';
	$GTOOLS::TAG{'<!-- VERB -->'} = 'LIST-SAVE';
	my ($hashref) = &ZOOVY::fetchproducts_by_nameref($USERNAME);
	my $c = '';
	foreach my $prod (sort keys %{$hashref}) {
		$c .= "<tr><td><input type=\"checkbox\" name=\"_$prod\"></td><td>$prod</td><td>$hashref->{$prod}</td></tr>\n";
		}
	$GTOOLS::TAG{'<!-- CHOOSER -->'} = $c;
	}

if ($ZOOVY::cgiv->{'attrib'} eq '_') { 
	$ZOOVY::cgiv->{'attrib'} = $ZOOVY::cgiv->{'attrib_custom'}; 
	$ZOOVY::cgiv->{'attrib'} =~ s/[\s]+//g;		## remove spaces from attribute names .. dammit karlo!
	}









if ($VERB eq 'SAVE') {
	$template_file = 'save.shtml';
	}



if ($VERB eq 'ADVANCED-EDITOR-SAVE') {
	$dataref->{'@ACTIONS'} = &JSON::XS::decode_json($ZOOVY::cgiv->{'actions-expert'});
	$VERB = '';
	}



if ($VERB eq '') {
	## populate the htmlwizards 
	my $c = '';
	my $htmlwiz = &ZOOVY::fetchmerchant_attrib($USERNAME,'zoovy:htmlwiz');	
	if ($htmlwiz eq '') {
		$c = "<option value=''>[No Default Selected]</option>";
		}

	my $prods = '';
	if ($dataref->{'PRODUCTS'}) {
		$prods = $dataref->{'PRODUCTS'};
		$prods =~ s/,/, /g;
		$GTOOLS::TAG{'<!-- PRODUCTS -->'} = $prods;
		}
	else {
		$GTOOLS::TAG{'<!-- PRODUCTS -->'} = "<font color='red'>No Products Currently Selected</font>";
		}

	my $actions = '';


	if ((ref($dataref->{'@ACTIONS'}) ne 'ARRAY') || (scalar(@{$dataref->{'@ACTIONS'}})==0)) {
		$GTOOLS::TAG{'<!-- ACTIONS -->'} = "<font class='hint' color='red'>No Actions Currently Specified</font>";		
		}
	else {
		my $js = '';
		if (ref($dataref->{'@ACTIONS'}) eq 'ARRAY') {
			$js = &ZOOVY::incode(&JSON::XS::encode_json($dataref->{'@ACTIONS'}));
			}
	
		my $basictable = '';
		my $i = 0;
		foreach my $aref (@{$dataref->{'@ACTIONS'}}) {
			my $when = '';
			if ($aref->{'when'} eq 'when-attrib-contains') {
				my $pretty = $aref->{'when-attrib-operator'};
				if ($pretty eq 'lt') { $pretty = 'less-than'; }
				elsif ($pretty eq 'gt') { $pretty = 'more-than'; }
				elsif ($pretty eq 'eq') { $pretty = 'equals'; }
				elsif ($pretty eq 'ne') { $pretty = 'not-equal-to'; }
				elsif ($pretty eq 'has') { $pretty = 'matches'; }
				$when = sprintf("%s %s \"%s\"", $aref->{'when-attrib'}, $pretty, $aref->{'when-attrib-contains'});
				}

			$basictable.= "<tr>";
			$basictable.= "<td valign=top><a onClick=\"document.thisFrm.VERB.value='ACTION-DEL:$i'; document.thisFrm.submit();\" href=\"#\">[x]</a></td>";

			my $verbtxt = $aref->{'verb'};
			if ($aref->{'verb'} eq 'copy') { $verbtxt = "copy-attrib-to-value"; }
			elsif ($aref->{'verb'} eq 'copyfrom') { $verbtxt = "copy-value-to-attrib"; }
			$basictable.= "<td valign=top>$verbtxt</td>";
			
			my $attrib = $aref->{'attrib'};
			if ($attrib eq '') { $attrib = "<font color='red'>NOT-SET-ERROR</font>"; }
			$basictable.= "<td valign=top>$attrib</td>";

			my $val = $aref->{'value'};
			if ($aref->{'verb'} eq 'replace') {
				$val = sprintf("\"%s\" with \"%s\"",$aref->{'value'}, $aref->{'replacewith'});
				}
			elsif ($aref->{'verb'} eq 'copy') {
				$val = sprintf("%s",$aref->{'copyto'});
				}
			elsif ($aref->{'verb'} eq 'copyfrom') {
				$val = sprintf("%s",$aref->{'copyfrom'});
				}
			$basictable.= "<td valign=top>$val</td>";
			$basictable.= "<td valign=top>$when</td>";
			$basictable.= "</tr>";
			# $c .= "<tr><td>".Dumper($aref)."</td></tr>";
			$i++;
			}

		$GTOOLS::TAG{'<!-- ACTIONS -->'} = qq~
<div style="" id="basic">
<b>Basic</b><br>
<table>
<tr>
	<td class='zoovysub2header'></td>
	<td class='zoovysub2header'>verb</td>
	<td class='zoovysub2header'>attrib</td>
	<td class='zoovysub2header'>value</td>
	<td class='zoovysub2header'>condition</td>
</tr>
$basictable
</table>
<a class="hint" href="#" onClick="\$('basic').hide(); \$('advanced').show(); \$('action-editor').value='json';">[json]</a>
</div>
<div style="display: none" id="advanced">
<b>Advanced Editor</b> 
<a class="hint" href="#" onClick="\$('advanced').hide(); \$('basic').show(); \$('action-editor').value='basic';">[turn off]</a><br>
<textarea cols=70 rows=20 name="actions-expert">$js</textarea>
<input type="button" class="button2" onClick="document.thisFrm.VERB.value='ADVANCED-EDITOR-SAVE'; document.thisFrm.submit();" value="Update">
</div>
~;
		}


#	if (0) {
#	elsif ($LUSERNAME eq 'SUPPORT') {
#		$GTOOLS::TAG{'<!-- ACTIONS -->'} = qq~
#
#~;
#		}
#	else {
#		}

	
	## PROD_IS FIELDS
	my $c = '';
	foreach my $ref (@ZOOVY::PROD_IS ) {
		$c .= "<option value='$ref->{'attr'}'>$ref->{'attr'} (tag:$ref->{'tag'})</option>";
		}
	$GTOOLS::TAG{'<!-- OPTIONS_PROD_IS -->'} = $c;

	## MKT_BITVAL options
	$c = '';
	#foreach my $key (sort keys %ZOOVY::MKT_BITVAL) {
	#	$c .= "<option value='$key'>$key</option>";
	#	}
	foreach my $intref (@ZOOVY::INTEGRATIONS) {
		next if ($intref->{'attr'} eq '');
		$c .= "<option value='$intref->{'attr'}'>$intref->{'attr'}</option>";
		}
	$GTOOLS::TAG{'<!-- OPTIONS_MKT_BITVAL -->'} = $c;

	}


$GTOOLS::TAG{'<!-- JOBID -->'} = int($dataref->{'JOBID'});
$GTOOLS::TAG{'<!-- JOBTITLE -->'} = $dataref->{'JOBTITLE'};
$GTOOLS::TAG{'<!-- DATA -->'} = &ZTOOLKIT::ser($dataref,1,0);


my @TABS = ();
push @TABS, { name=>'Create', link=>'index.cgi', selected=>($VERB eq '')?1:0 };
push @TABS, { name=>'Lookup/Edit', link=>'index.cgi?VERB=LOOKUP', selected=>($VERB eq 'LOOKUP')?1:0 }; 

if ($template_file ne '') {
	&GTOOLS::output(
	   'title'=>'Product Power Tool',
		'file'=>$template_file,
  	 	'header'=>'1',
		'js'=>2,
		'tabs'=>\@TABS,
  	 	'help'=>'#50287',
  	 	'bc'=>[
  			{ name=>'Utilities',link=>'https://www.zoovy.com/biz/utilities','target'=>'_top', },
  			{ name=>'Product Power Tool',link=>'','target'=>'_top', },
  			],
		);
	}








