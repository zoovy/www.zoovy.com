#!/usr/bin/perl -w 

use strict;
use File::Slurp;

use lib "/httpd/modules";
use ZOOVY;
use SEARCH;
use ZWEBSITE;
use GTOOLS;
use ZTOOLKIT;
use strict;
use PRODUCT::FLEXEDIT;
use LUSER;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_S&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my ($udbh) = DBINFO::db_user_connect($USERNAME);
&ZOOVY::init();
&ZWEBSITE::init();

my $template_file = '';
my $VERB = $ZOOVY::cgiv->{'ACTION'};

my @MSGS = ();

if ($FLAGS !~ /,WEB,/) { $VERB = 'DENY';  }
if ($PRT>0) {
	push @MSGS, "WARN|Search catalogs (and logs) are shared across partitions - however it is possible to specify a different catalog per partition";
	}



if (($VERB eq 'GLOBAL') || ($VERB eq 'SAVE-GLOBAL')) {
	if (not $LU->is_level(7)) {
		if ($LU->is_zoovy()) {
			push @MSGS, "WARN|Account level is insufficient (Zoovy support - you can save changes)";
			}
		else {
			push @MSGS, "WARN|Account level is insufficient (you can view, but not save changes)";
			$VERB = 'GLOBAL-DENY';
			}
	   }
	elsif (not $LU->is_admin()) {
		push @MSGS, "WARN|Requires Administrative priviledges (you can view, but not save changes)";
		$VERB = 'GLOBAL-DENY';
		}
   }



if ($VERB eq 'SAVE-GLOBAL') {
	my $USER_PATH = &ZOOVY::resolve_userpath($USERNAME);



	unlink "$USER_PATH/elasticsearch-product-synonyms.txt";
	if ($ZOOVY::cgiv->{'SYNONYMS'}) {
		File::Slurp::write_file("$USER_PATH/elasticsearch-product-synonyms.txt",$ZOOVY::cgiv->{'SYNONYMS'});
		chmod 0666, "$USER_PATH/elasticsearch-product-synonyms.txt";
		push @MSGS, "SUCCESS|Saved product synonyms (reindex-needed)";
		}

	unlink "$USER_PATH/elasticsearch-product-stopwords.txt";
	if ($ZOOVY::cgiv->{'STOPWORDS'}) {
		File::Slurp::write_file("$USER_PATH/elasticsearch-product-stopwords.txt",$ZOOVY::cgiv->{'STOPWORDS'});
		chmod 0666, "$USER_PATH/elasticsearch-product-stopwords.txt";
		push @MSGS, "SUCCESS|Saved product stopwords (reindex-needed)";
		}

	unlink "$USER_PATH/elasticsearch-product-charactermap.txt";
	if ($ZOOVY::cgiv->{'CHARACTERMAP'}) {
		my @LINES = ();
		my %DUPS = ();
		my $linecount = 0;
		foreach my $line (split(/[\n\r]+/,$ZOOVY::cgiv->{'CHARACTERMAP'})) {
			$linecount++;
			my ($k,$v) = split(/\=\>/,$line);
			$k =~ s/^[s]+//gs;
			$k =~ s/[s]+$//gs;
			if (not defined $DUPS{$k}) {
				push @LINES, $line;
				}
			else {
				push @MSGS, "WARN|Line[$linecount] \"$line\" was ignored because it was duplicated earlier.";
				$DUPS{$k}++;
				}
			}
		File::Slurp::write_file("$USER_PATH/elasticsearch-product-charactermap.txt",join("\n",@LINES));
		chmod 0666, "$USER_PATH/elasticsearch-product-charactermap.txt";
		push @MSGS, "SUCCESS|Saved product character map (reindex-needed)";
		}

	$VERB = 'GLOBAL';
	}


if (($VERB eq 'GLOBAL') || ($VERB eq 'GLOBAL-DENY')) {
#-rw-r--r--+  1 root   root       1376 May 19 16:02 elasticsearch-product-charactermap.txt
#-rw-r--r--+  1 root   root        163 May 19 16:02 elasticsearch-product-stopwords.txt
#-rw-r--r--+  1 root   root      14170 May 19 16:02 elasticsearch-product-synonyms.txt	
	my $USER_PATH = &ZOOVY::resolve_userpath($USERNAME);	
	if (-f "$USER_PATH/elasticsearch-product-synonyms.txt") {
		$GTOOLS::TAG{'<!-- SYNONYMS -->'} = File::Slurp::read_file("$USER_PATH/elasticsearch-product-synonyms.txt") ;
		}
	if (-f "$USER_PATH/elasticsearch-product-stopwords.txt") {
		$GTOOLS::TAG{'<!-- STOPWORDS -->'} = File::Slurp::read_file("$USER_PATH/elasticsearch-product-stopwords.txt") ;
		}
	if (-f "$USER_PATH/elasticsearch-product-charactermap.txt") {
		$GTOOLS::TAG{'<!-- CHARACTERMAP -->'} = File::Slurp::read_file("$USER_PATH/elasticsearch-product-charactermap.txt") ;
		}

	require PRODUCT::FLEXEDIT;
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	my @FIELDS = ();
	if (defined $gref->{'@flexedit'}) {
		foreach my $set (@{$gref->{'@flexedit'}}) {
			next unless (defined $set->{'index'});
			if (defined $PRODUCT::FLEXEDIT::fields{$set->{'id'}}) {
				## copy custom fields into global.bin ex: type, options, etc.
				foreach my $k (keys %{$PRODUCT::FLEXEDIT::fields{$set->{'id'}}}) {
					next if (defined $set->{$k});
					$set->{$k} = $PRODUCT::FLEXEDIT::fields{$set->{'id'}}->{$k};
					}
				}
			push @FIELDS, $set;
			}
		}

	if (scalar(@FIELDS)==0) {
		$GTOOLS::TAG{'<!-- PRODUCT_INDEXED_ATTRIBUTES -->'} = "<li> <i>None</i>\n";
		}
	else {
		foreach my $set (@FIELDS) {	
			$GTOOLS::TAG{'<!-- PRODUCT_INDEXED_ATTRIBUTES -->'} .= "<li> $set->{'id'}.$set->{'type'} =&gt; $set->{'index'}\n";
			}
		}


	$template_file = 'global.shtml';
	}



if ($VERB eq 'ADD') {
	my @ERRORS = ();
	my $CATALOG = uc($ZOOVY::cgiv->{'CATALOG'});
	# my $ATTRIBS = lc($ZOOVY::cgiv->{'FULLTEXT_ATTRIBS'});
	my $ATTRIBS = '';

	foreach my $id ('SUBSTRING','FINDER','COMMON') {
		if ($CATALOG eq $id) { push @ERRORS, "catalog:$id is reserved and cannot be used."; }
		}

	my @ATTRIBS = ();
	my ($fieldsref) = PRODUCT::FLEXEDIT::elastic_fields($USERNAME);
	foreach my $id ('id','tags','options','pogs') {
		if (defined $ZOOVY::cgiv->{"field:$id"}) {
			push @ATTRIBS, $id;
			}
		}
	foreach my $fieldset (@{$fieldsref}) {
		if (defined $ZOOVY::cgiv->{"field:$fieldset->{'id'}"}) {
			push @ATTRIBS, $fieldset->{'id'};
			}
		}

	if ($CATALOG eq '') { push @ERRORS, 'Sorry, you must specify a catalog name'; }
	if (scalar(@ATTRIBS)==0) {
 		push @ERRORS, 'You must specify at least one valid (indexed) attribute'; 
		}
	else {
		$ATTRIBS = join(",",@ATTRIBS);
		}

	if (scalar(@ERRORS)>0) {
		foreach my $err (@ERRORS) { push @MSGS, "ERROR|$err"; }			
		}
	else {
		my $DICTDAYS = 0;
		&SEARCH::add_catalog($USERNAME,$CATALOG,$ATTRIBS);
		$LU->log("SETUP.SEARCH.ADD","CATALOG=$CATALOG ATTRIBS=$ATTRIBS",'INFO');
		}
	$VERB = '';
	}

if ($VERB eq 'DELETE') {
	&SEARCH::del_catalog($USERNAME,$ZOOVY::cgiv->{'CATALOG'});
	$LU->log("SETUP.SEARCH.NUKE","Deleted catalog $ZOOVY::cgiv->{'CATALOG'}",'INFO');
	$VERB = '';
	}


if ($VERB eq 'CREATE') {
	$template_file = 'create.shtml';
	}

if ($VERB eq 'LOG-DELETE') {
	my $path = &ZOOVY::resolve_userpath($USERNAME).'/IMAGES';
	my $file = $ZOOVY::cgiv->{'FILE'};
	$file =~ s/[\.]+/./g;	# remove multiple periods.
	$file =~ s/[\/\\]+//gs;	# remove all slashes
	unlink("$path/$file");
	$VERB = 'LOGS';
	}



if ($VERB eq 'LOGS') {
	##
	my $c = '';
	require BATCHJOB;
	my $GUID = &BATCHJOB::make_guid();
	my $path = &ZOOVY::resolve_userpath($USERNAME).'/IMAGES';
	my $D = undef;
	opendir $D, $path;
	while ( my $file = readdir($D) ) {
		next if (substr($file,0,1) eq '.');
		my $CATALOG = '';
		if ($file =~ /^SEARCH-(.*?)\.(log|csv)$/) {
			$CATALOG = $1;
			if ($CATALOG eq '') { $CATALOG = 'N/A'; }
			my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks) = stat($path.'/'.$file);
			$c .= "<tr><td>$CATALOG</td><td>$file</td><td>".&ZTOOLKIT::pretty_date($mtime,1)."</td>";
			$c .= "<td nowrap>";
			$c .= "<a target=\"_blank\" href=\"http://static.zoovy.com/merchant/$USERNAME/$file\">[View]</a> ";
			$c .= " <a href=\"index.cgi?ACTION=LOG-DELETE&FILE=$file\">[Delete]</a>";
			$c .= " <a href=\"/biz/batch/index.cgi?VERB=NEW&GUID=$GUID&EXEC=REPORT&REPORT=SEARCHLOG_SUMMARY&.file=$file\">[Report]</a>";
			$c .= " </td></tr>\n";
			}
		}
	closedir $D;
	if ($c eq '') { $c .= "<tr><td colspan=3><i>Sorry, no log files are available yet. Try performing a search on your website.</td></tr>"; }
	$GTOOLS::TAG{'<!-- LOG_FILES -->'} = $c;
	$template_file = 'logs.shtml';
	}



if (($VERB eq 'RAWE') || ($VERB eq 'RAWE-DEBUGPID') || ($VERB eq 'RAWE-QUERY')) {
	$template_file = 'rawe.shtml';

	$GTOOLS::TAG{'<!-- OUTPUT -->'} = '';
	
	my ($PID,$QUERY) = undef;

	my ($es) = &ZOOVY::getElasticSearch($USERNAME);		
	if ($VERB eq 'RAWE') {
		## not a "RUN"
		$es = undef;
		}
	elsif ($VERB eq 'RAWE-QUERY') {
		$QUERY = $ZOOVY::cgiv->{'QUERY'};
		if ($ZOOVY::cgiv->{'QUERY'} eq '') {
			push @MSGS, "WARN|No query specified"; 
			}
		}
	elsif ($VERB eq 'RAWE-DEBUGPID') {
		$PID = $ZOOVY::cgiv->{'PID'};
		if ($ZOOVY::cgiv->{'PID'} eq '') {
			push @MSGS, "WARN|No PID specified"; 
			}
		}
	else {
		}

	if (not defined $es) {
		## bad things alreadly happens.
 		}
	elsif ($VERB eq 'RAWE-QUERY') {
		use JSON::XS;

		my $Q = undef;
		my $results = undef;
		eval { $Q = JSON::XS::decode_json($QUERY); };
		if ($@) {
			push @MSGS, "ERROR|JSON Decode Error: $@"; 
			$Q = undef;
			}
		else {
			$Q->{'index'} = lc("$USERNAME.public");
			}

		if ((defined $Q) && (defined $es)) {
		   eval { $results = $es->search(%{$Q}); };
			if ($@) {
				push @MSGS, "ERROR|Elastic Search Error:$@";
				}
			}

		$GTOOLS::TAG{'<!-- QUERY -->'} = $QUERY;
		$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<pre><h2>Search Results:</h2>".Dumper($Q,$results)."</pre>";
		}
	elsif ($VERB eq 'RAWE-DEBUGPID') {
     	my $result = $es->get(index =>lc("$USERNAME.public"),'type'=>'product','id'=>$PID);
		$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<pre><h2>Product Document Get:</h2>".Dumper($result)."</pre>";

		}

	$VERB = 'RAWE';
	}


if ($VERB eq 'DEBUG') {
	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = "<i>No debug output.</i>";
	}

if ($VERB eq 'EXPLODE-DEBUG') {
	my $c = '';
	my $explode = $ZOOVY::cgiv->{'EXPLODE'};
	if ($explode eq '') { 
		$c = "<div class='error'>No sku/model # for explosion was passed</div>";
		}
	else {
		my $results = &SEARCH::explode($explode);
		$c .= "<b>Keyword explosion for $explode:</b><br>".$results;
		}
	
	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = $c;
	$VERB = 'DEBUG';
	}


##
##
if ($VERB eq 'DEBUG-RUN') {
	use Data::Dumper;
	my $log = '';

	my ($CATALOG) = $ZOOVY::cgiv->{'CATALOG'};
	my ($SEARCHFOR) = $ZOOVY::cgiv->{'SEARCHFOR'};
	my ($PID) = $ZOOVY::cgiv->{'PRODUCT'};
	$SEARCHFOR =~ s/^[\s]+//g; # strip leading whitespace
	$SEARCHFOR =~ s/[\s]+$//g;	# strip trailing whitespace

	$LU->set('setup.search.debug.catalog',$CATALOG);
	$LU->set('setup.search.debug.root',$ZOOVY::cgiv->{'SITE'});
	$LU->save();

	my ($xPRT,$ROOT) = split(/-/,$ZOOVY::cgiv->{'SITE'});

	if ($PID ne '') {
		$log .= "<tr><td valign=top>Debug Product: $PID</td></tr>";
		}

	my %params = (MODE=>'',KEYWORDS=>$SEARCHFOR,CATALOG=>$CATALOG,TRACEPID=>$PID,debug=>1,ROOT=>$ROOT,PRT=>$xPRT);
	my $ref = &ZTOOLKIT::parseparams($ZOOVY::cgiv->{'ELEMENT'});
	foreach my $k (keys %{$ref}) {
		$params{$k} = $ref->{$k};
		}

	my ($outref,$prodsref,$tracelog) = SEARCH::search($USERNAME,%params);

	foreach my $line (@{$tracelog}) {
		$log .= "<tr><td valign=top>$line</td></tr>";
		}
	
	$GTOOLS::TAG{'<!-- DEBUG_OUT -->'} = "Searching for: $SEARCHFOR<br><br>Element Parameters: ".Dumper(\%params)."<br><br>Trace Log:<br>".
	"<table>$log</table>".
	"<hr>Output:<br><pre>".Dumper(SHORT_RESULTS=>$outref)."</pre>";

	$VERB = 'DEBUG';
	}

##
##
if ($VERB eq 'DEBUG') {
	my $catalogref = &SEARCH::list_catalogs($USERNAME);
	my $c = '';

	my $FOCUS_CATALOG = $ZOOVY::cgiv->{'CATALOG'};
	if (not defined $FOCUS_CATALOG) {
		$FOCUS_CATALOG = $LU->get('setup.search.debug.catalog');
		}
	my $FOCUS_SITE = $ZOOVY::cgiv->{'SITE'};
	if (not defined $FOCUS_SITE) {
		$FOCUS_SITE = $LU->get('setup.search.debug.root');
		}

	$c .= "<option></option>";
	foreach my $cat (keys %{$catalogref}) {
		my $hashref = $catalogref->{$cat};
		my $selected = ($FOCUS_CATALOG eq $hashref->{'CATALOG'})?'selected':'';
		$c .= "<option $selected value='$hashref->{'CATALOG'}'>$hashref->{'CATALOG'}</option>\n";
		}
	$c .= "<option value='FINDER'>FINDER (built-in)</option>\n";
	$c .= "<option value='COMMON'>COMMON (built-in)</option>\n";
	$c .= "<option value='SUBSTRING'>SUBSTRING (built-in)</option>\n";
	$GTOOLS::TAG{'<!-- CATALOGS -->'} = $c;

	$GTOOLS::TAG{'<!-- SEARCHFOR -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'SEARCHFOR'});
	$GTOOLS::TAG{'<!-- ELEMENT -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'ELEMENT'});
	
	$c = '';
	my $i = 0;
	require DOMAIN::TOOLS;
	foreach my $prt (@{&ZWEBSITE::list_partitions($USERNAME)}) {
		my ($prtinfo) = &ZWEBSITE::prtinfo($USERNAME,$i);
		my ($PROFILE) = $prtinfo->{'profile'};
		my ($root) = &ZOOVY::fetchmerchantns_attrib($USERNAME,$PROFILE,'zoovy:site_rootcat');
		if ($root eq '') { $root = '.'; }

		my $value = "$i-$root";
		my ($selected) = ($value eq $FOCUS_SITE)?'selected':'';

		$c .= "<option disabled></option>";
		$c .= "<option $selected value=\"$value\">PRT:$prt [profile=$PROFILE] [root=$root]</option>";

		my @DOMAINS = &DOMAIN::TOOLS::domains($USERNAME,PRT=>$prt,DETAIL=>1);
		foreach my $dref (@DOMAINS) {
			my ($nsref) = &ZOOVY::fetchmerchantns_ref($USERNAME,$dref->{'PROFILE'});
			my $root = $nsref->{'zoovy:site_rootcat'};
			my $value = "$i-$root";
			my ($selected) = ($value eq $FOCUS_SITE)?'selected':'';
			$c .= "<option $selected value=\"$value\">- DOMAIN: $dref->{'DOMAIN'} [prt=$prt] [profile=$PROFILE] [root=$root]</option>";
			}


		$i++;
		}
	$GTOOLS::TAG{'<!-- PARTITIONS -->'} = $c;

	

	$template_file = 'debug.shtml';
	}

if ($VERB eq 'CONFIG-SAVE') {
	my ($CATALOG) = $ZOOVY::cgiv->{'CATALOG'};
	&DBINFO::insert($udbh,'SEARCH_CATALOGS',{
		'MID'=>$MID,
		'CATALOG'=>$CATALOG,
		'ATTRIBS'=>$ZOOVY::cgiv->{'ATTRIBS'},
		'ISOLATION_LEVEL'=>int($ZOOVY::cgiv->{'ISOLATION_LEVEL'}),
		'USE_EXACT'=>(defined $ZOOVY::cgiv->{'USE_EXACT'})?1:0,
		'USE_WORDSTEMS'=>(defined $ZOOVY::cgiv->{'USE_WORDSTEMS'})?1:0,
		'USE_INFLECTIONS'=>(defined $ZOOVY::cgiv->{'USE_INFLECTIONS'})?1:0,
		'USE_SOUNDEX'=>(defined $ZOOVY::cgiv->{'USE_SOUNDEX'})?1:0,
		'USE_ALLWORDS'=>(defined $ZOOVY::cgiv->{'USE_ALLWORDS'})?1:0,
		},key=>['MID','CATALOG'],debug=>1);
	$VERB = 'CONFIG';
	}

##
##
##
if ($VERB eq 'CONFIG') {
	$template_file = 'config.shtml';
	my ($CATALOG) = $ZOOVY::cgiv->{'CATALOG'};
	
	my ($ref) = &SEARCH::fetch_catalog($USERNAME,$CATALOG);

	my $i = 0;
	my @ERRORS = ();
	require PRODUCT::FLEXEDIT;
	foreach my $k (split(/[,\n\r]+/,$ref->{'ATTRIBS'})) {
		next if ($k eq '');
		$k =~ s/^[\s]+//g;
		$k =~ s/[\s]+$//g;
		if ($k eq 'id') {
			$i++;
			}
		elsif ($PRODUCT::FLEXEDIT::fields{ $k }) {
			$i++;
			}
		## amended code to enable 'user:' attributes to pass validation.
		## nick advised these attributes would be appearing a lot more in merchant global.bin files
		elsif (($k =~ /^$USERNAME\:/) || ($k =~ /^user\:/)) {
			$i++;
			}
		else {
			push @ERRORS, "<div><font color='red'>Unknown/Invalid attribute: $k</font></div>";
			}
		}
	if ($i==0) {
		push @ERRORS, "<div><font color='red'>No Attributes found.</font></div>";
		}
	$GTOOLS::TAG{'<!-- ATTRIBS_WARNING -->'} = join('',@ERRORS);

	$GTOOLS::TAG{'<!-- ATTRIBS -->'} = &ZOOVY::incode($ref->{'ATTRIBS'});

	$GTOOLS::TAG{'<!-- ISO_0 -->'} = ($ref->{'ISOLATION_LEVEL'}==0)?'checked':'';
	$GTOOLS::TAG{'<!-- ISO_5 -->'} = ($ref->{'ISOLATION_LEVEL'}==5)?'checked':'';
	$GTOOLS::TAG{'<!-- ISO_10 -->'} = ($ref->{'ISOLATION_LEVEL'}==10)?'checked':'';

	$GTOOLS::TAG{'<!-- USE_INFLECTIONS -->'} = ($ref->{'USE_INFLECTIONS'})?'checked':'';
	$GTOOLS::TAG{'<!-- USE_WORDSTEMS -->'} = ($ref->{'USE_WORDSTEMS'})?'checked':'';
	$GTOOLS::TAG{'<!-- USE_SOUNDEX -->'} = ($ref->{'USE_SOUNDEX'})?'checked':'';
	$GTOOLS::TAG{'<!-- USE_EXACT -->'} = ($ref->{'USE_EXACT'})?'checked':'';
	$GTOOLS::TAG{'<!-- USE_ALLWORDS -->'} = ($ref->{'USE_ALLWORDS'})?'checked':'';

	$GTOOLS::TAG{'<!-- CATALOG -->'} = $CATALOG;
	}


if ($VERB eq '') { 
	my $catalogref = &SEARCH::list_catalogs($USERNAME);
	my $c = '';
	my $cat;
	my $lasttime;
	my $catalogcount = 0;

	my ($fieldsref) = PRODUCT::FLEXEDIT::elastic_fields($USERNAME);
	foreach my $ref (@{$fieldsref}) {
		$c .= "<tr><td><input type=\"checkbox\" name=\"field:$ref->{'id'}\"><td>$ref->{'id'}</td><td>$ref->{'index'}</td></tr>";
		}
	$GTOOLS::TAG{'<!-- INDEXED_FIELDS -->'} = $c;

	$c = '';
	my ($webdbref) = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
	$catalogref->{'COMMON'} = { 
		'CATALOG'=>'COMMON',
		'FORMAT'=>'ELASTIC',
		'ATTRIBS'=>'** performs elastic search on common fields **',
		LASTINDEX=>0,
		DIRTY=>0
		};

	$GTOOLS::TAG{'<!-- SUBSTRING_NOT_AVAILABLE -->'} = '';
	my ($gref) = &ZWEBSITE::fetch_globalref($USERNAME);
	if (defined $gref->{'%tuning'}) {
		## tuning parameters can alter behaviors here.
		if (defined $gref->{'%tuning'}->{'disable_substring'}) {
			delete $catalogref->{'SUBSTRING'};
			$GTOOLS::TAG{'<!-- SUBSTRING_NOT_AVAILABLE -->'} = '[NOT AVAILABLE]';
			}
		}
	
	require BATCHJOB;
	my ($GUID) = BATCHJOB::make_guid();

	foreach $cat (keys %{$catalogref}) {
		my $hashref = $catalogref->{$cat};

		$catalogcount++;
		my $row = "r".($catalogcount%2);

		$c .= "<tr>";
		$c .= "<td nowrap valign=top class='$row'>";
		$c .= "ID: $hashref->{'CATALOG'}<br>";
		# $c .= "TYPE: $hashref->{'FORMAT'}<br>";
		$c .= "</td>";

		
		if ($hashref->{'ID'} eq 'FINDER') {
			$c .= "<td valign=top class='$row'>product options</td>";
			}
		elsif ($hashref->{'ID'} eq 'SUBSTRING') {
			$c .= "<td valign=top class='$row'>product id, sku, product name</td>";
			}
		elsif ($hashref->{'ID'} eq 'COMMON') {
			$c .= "<td valign=top class='$row'>most commonly used fields (designed by zoovy)</td>";
			}
		else {
			$hashref->{'ATTRIBS'} =~ s/,[\s]*/, /g;
			$c .= "<td valign=top class='$row'>$hashref->{'ATTRIBS'}</td>";
			}
		$c .= "<td valign=top class='$row' nowrap>";

		$c .= '[<a href="index.cgi?ACTION=DELETE&CATALOG='.$hashref->{'CATALOG'}.'">DELETE</a>]<br>';


#		$lasttime = &ZTOOLKIT::mysql_to_unixtime($hashref->{'LASTINDEX'});
#		if ($hashref->{'FORMAT'} eq 'SUBSTRING') {
#			## can't reset finders.
#			}
#		elsif ($hashref->{'FORMAT'} eq 'ELASTIC') {
#			}
#		else {
#			if (int($lasttime) <= 0) {
#				$lasttime = "Never";
#				}
#			else {
#				$lasttime = &ZTOOLKIT::pretty_time_since($lasttime,time());
#				}
#			$c .= " [<a class='smlink' href=\"/biz/batch/index.cgi?VERB=ADD&GUID=$GUID&EXEC=UTILITY&APP=CATALOG_REBUILD&.format=$hashref->{'FORMAT'}&.catalog=$hashref->{'CATALOG'}\">RESET</a>]<br>";
#			}
#

		$c .= "</td>";

#		if ($hashref->{'DIRTY'}>0) { $c .= "<td valign=top class='$row'>NOT-CURRENT</td>"; } else { $c .= "<td valign=top class='$row'>OKAY</td>"; }
#		$c .= "<td valign=top class='$row'>$lasttime</td>"; 
#		my %AR;
#		my $file = &ZOOVY::resolve_userpath($USERNAME)."/SEARCH-$hashref->{'CATALOG'}.cdb";
#		my $cdb = tie %AR, 'CDB_File', $file;
#		my $keycount = -1;
#		if (defined $cdb) {
#			$keycount = scalar(keys %AR);
#			$cdb = undef;
#			untie(%AR);	
#			}
##		$c .= "<td valign=top class='$row'>".$keycount."</td>";
#		if ($hashref->{'FORMAT'} ne 'FULLTEXT') { $c .= "<td valign=top class='$row'>N/A</td>"; }
#		elsif ($hashref->{'FORMAT'} == -1) { $c .= "<td valign=top class='$row'>Disabled</td>"; }
#		elsif ($hashref->{'FORMAT'} == 0) { $c .= "<td valign=top class='$row'>All Days</td>"; }
#		else { $c .= "<td valign=top class='$row'>$hashref->{'DICTIONARY_DAYS'} days</td>"; }
#		$c .= "</tr>";
		}

	if ($c ne '') {
		$c = qq~
		<tr class="zoovytableheader">
			<td>Name</td>
			<td>Attributes</td>
			<td>&nbsp;</td>
		</tr>~.$c;
		} 
	else {
		$c .= "<tr><td><i>No catalogs currently exist, create the default catalog first.</i></td></tr>";
		}
	$GTOOLS::TAG{'<!-- CATALOG_LIST -->'} = $c;
	$c = '';

	
#	my $sogsref = &POGS::list_sogs($USERNAME);
#	if (defined $sogsref) {
#		foreach my $id (keys %{$sogsref}) {
#			$c .= "<option value=\"$id\">[$id] ".$sogsref->{$id}."</option>\n";
#			}
#		}
#	$GTOOLS::TAG{'<!-- AVAILABLE_SOGS -->'} = $c;
#	$c = '';
#
#	$c = '';
	$template_file = 'index.shtml';
	}


if ($VERB eq 'DENY') {
	$template_file = 'deny.shtml';
	}

&DBINFO::db_user_close();


my @TABS = ();
push @TABS, { name=>"Catalogs", selected=>($VERB eq '')?1:0, link=>"index.cgi?ACTION="  };
push @TABS, { name=>"Logs", selected=>($VERB eq 'LOGS')?1:0, link=>"index.cgi?ACTION=LOGS"  };
push @TABS, { name=>"Catalog Debug", selected=>($VERB eq 'DEBUG')?1:0, link=>"index.cgi?ACTION=DEBUG"  };
push @TABS, { name=>"Tuning", selected=>($VERB eq 'GLOBAL')?1:0, link=>"index.cgi?ACTION=GLOBAL" };
push @TABS, { name=>"Elastic Raw", selected=>($VERB eq 'DEBUG')?1:0, link=>"index.cgi?ACTION=RAWE"  };


&GTOOLS::output(
   'title'=>'Setup : Advanced Site Search',
   'file'=>$template_file,
   'header'=>'1',
   'help'=>'#50345',
	'jquery'=>1,
   'tabs'=>\@TABS,
	'msgs'=>\@MSGS,
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'Advanced Site Search',link=>'http://www.zoovy.com/biz/setup/search','target'=>'_top', },
      ],
   );


