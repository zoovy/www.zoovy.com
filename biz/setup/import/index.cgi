#!/usr/bin/perl

require Archive::Zip;
use strict;
use lib "/httpd/modules";
use GTOOLS;
use CGI qw/:push -nph/;
use ZOOVY;
use INVENTORY;
use NAVCAT;
use CUSTOMER;
use ORDER;
use ORDER::TOOLS;
use DBINFO;
use ZWEBSITE;
use ZCSV;
use TODO;

use Data::Dumper;
$|++;


sub validsku {
	my ($sku) = @_;

	my $c = $sku;
	$sku =~ s/[^\w\-\:]+//g;
	return($c eq $sku);
	}

my $LAST_ERROR = '';

my $safepath;
my $BUFFER ;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&16');
if (not defined $LU) { exit; }

my @MSGS = ();
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT,$RESELLER) = $LU->authinfo();
if ($MID<=0) { exit; }

if ($FLAGS =~ /,CSV,/) {
	}
elsif ($LU->is_zoovy()) { 
	push @MSGS, "WARN|This account does not have the CSV flag. CSV Flag was added for support user";
	$FLAGS .= ',CSV,'; 
	}

my $q = new CGI;

print STDERR 'CGI PARAMS: '.Dumper($q)."\n";

my $VERB = $q->param('ACTION');
if ($VERB eq '') { $VERB = $q->param('VERB'); }
if ($VERB eq '') { $VERB = 'HELP'; }
print STDERR Dumper($ZOOVY::cgiv);
my $template_file = '';
my $c;
my $filename;
my $ERROR;



## get WEBDOCs for main page
## Advanced Product Import Guide
my ($prodfile, $prodhtml) = GTOOLS::help_link('Advanced Product Import Guide', 50285);
$GTOOLS::TAG{'<!-- PROD_IMPORT_WD -->'} = $prodhtml;
## Category Import Guide
my ($catfile, $cathtml) = GTOOLS::help_link('Category Import Guide', 50326);
$GTOOLS::TAG{'<!-- CAT_IMPORT_WD -->'} = $cathtml;
## Advanced Customer Import Guide
my ($custfile, $custhtml) = GTOOLS::help_link('Advanced Customer Import Guide', 50388);
$GTOOLS::TAG{'<!-- CUST_IMPORT_WD -->'} = $custhtml;
## Advanced Order Import Guide
my ($orderfile, $orderhtml) = GTOOLS::help_link('Advanced Order Import Guide', 50890);
$GTOOLS::TAG{'<!-- ORDER_IMPORT_WD -->'} = $orderhtml;
## Advanced Tracking Import Guide
my ($trackfile, $trackhtml) = GTOOLS::help_link('Advanced Tracking Import Guide', 51628);		
$GTOOLS::TAG{'<!-- TRACKING_IMPORT_WD -->'} = $trackhtml;


print STDERR "VERB: $VERB\n";

if ($VERB =~ /UPLOAD-(.*?)$/) {
	## UPLOAD-PRODUCTS, UPLOAD-NAVCATS, UPLOAD-etc.
	$VERB = $1;

	if ($VERB eq 'JEDI') {
		## memorize jedi settings for next use.
		}

	my ($RESULT) = $ZOOVY::cgiv->{'hidFileID'};
	require BATCHJOB;

	$RESULT =~ s/[\n\r]+//gs;
	print STDERR "RESULT[$RESULT]\n";

	## the hidFileID will contain either:
	if ($RESULT =~ /^ERROR\:(.*?)$/s) {
		$GTOOLS::TAG{'<!-- ERROR -->'} = $1;
		warn("upload.cgi returned error: $1");
		## note: $VERB was set above to UPLOAD-?????? where ????? is the return VERB
		}
	elsif ($RESULT =~ /^JOBID\:([\d]+)$/s) {
		print "Location: http://www.zoovy.com/biz/batch/index.cgi?VERB=LOAD&JOB=$1\n\n";
		$VERB = '_';
		exit;
		}
	else {
		$GTOOLS::TAG{'<!-- ERROR -->'} = "Unknown response from upload.cgi ($RESULT)\n";
		}

	print STDERR "VERB: $VERB\n";
	## redirect to the batch job.
	}


##
##
##
if ($VERB eq 'JEDI') {
	my %params = %{&ZTOOLKIT::parseparams($LU->get('.jedi-import'))};
	$GTOOLS::TAG{'<!-- JEDI_PRODUCTS_RESET -->'} = (($params{'products'} eq 'reset')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_PRODUCTS_SMART -->'} = (($params{'products'} eq 'smart')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_PRODUCTS_NEW -->'} = (($params{'products'} eq 'new')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_NAVCATS_RESET -->'} = (($params{'navcats'} eq 'reset')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_NAVCATS_SMART -->'} = (($params{'navcats'} eq 'smart')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_NAVCATS_IGNORE -->'} = (($params{'navcats'} eq 'ignore')?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_JEDI_INVENTORY -->'} = (($params{'inventory'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_JEDI_CREATE -->'} = (($params{'create'})?'checked':'');
	$GTOOLS::TAG{'<!-- CHK_JEDI_THEMES -->'} = (($params{'themes'})?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_ORDERING_YES -->'} = (($params{'ordering'} eq 'yes')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_ORDERING_NO -->'} = (($params{'ordering'} eq 'no')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_ORDERING_ -->'} = (($params{'ordering'} eq '')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_SHIPPING_YES -->'} = (($params{'shipping'} eq 'yes')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_SHIPPING_NO -->'} = (($params{'shipping'} eq 'no')?'checked':'');
	$GTOOLS::TAG{'<!-- JEDI_SHIPPING_ -->'} = (($params{'shipping'} eq '')?'checked':'');
	$template_file = 'jedi.shtml';
	}


##
##
##
if ($VERB eq 'SHOW_SOGXML') {
	require POGS;
	my ($pog2) = POGS::load_sogref($USERNAME,$q->param('ID'),undef,0);

	print "Content-type: text/xml\n\n";
	my ($xml) = &POGS::serialize([$pog2]);
	print $xml;
	exit;
	}

if ($VERB eq 'EXPORT-RULES') {
	require ZWEBSITE;
	require ZSHIP::RULES;

	print "Content-type: text/csv\n\n";

	my $allrulesref = &ZSHIP::RULES::loadbin($USERNAME,$PRT);
	use Text::CSV_XS;

	my $csv = Text::CSV_XS->new({binary=>1});          # create a new object
	my @COLUMNS = ();
	push @COLUMNS, "%TYPE";			## UBER,SHIP,COUPON
	push @COLUMNS, "%RULESET";
	push @COLUMNS, "NAME";
	push @COLUMNS, "MATCH";
	push @COLUMNS, "MATCHVALUE";	## VALUE
	push @COLUMNS, "FILTER";
	push @COLUMNS,	"EXEC";
	push @COLUMNS, "EXECVALUE";
	push @COLUMNS, "SHIP_SCHEDULE";
	push @COLUMNS, "UBER_GROUP";		## GROUP=CODE
	push @COLUMNS, "UBER_IMAGE";
	push @COLUMNS, "UBER_TAX";
	push @COLUMNS, "UBER_WEIGHT";
	my $status  = $csv->combine(@COLUMNS);  # combine columns into a string
	my $line    = $csv->string();           # get the combined string
	print "$line\n\r";

	foreach my $ruleset (sort keys %{$allrulesref}) {
		my $rules = $allrulesref->{$ruleset};

		foreach my $rule (@{$rules}) {
	
			@COLUMNS = ();
			if ($ruleset =~ /^COUPON-(.*?)$/) {
				push @COLUMNS, "COUPON";
				push @COLUMNS, $1;
				}
			elsif ($ruleset =~ /^SHIP-(.*?)$/) {
				push @COLUMNS, "SHIP";
				push @COLUMNS, $1;
				}
			elsif ($ruleset =~ /^(.*?)$/) {
				push @COLUMNS, "UBER";
				push @COLUMNS, $1;
				}

			if (defined $rule->{'HINT'}) { $rule->{'NAME'} = $rule->{'HINT'}; }
			push @COLUMNS, $rule->{'NAME'};
			push @COLUMNS, $rule->{'MATCH'};
			push @COLUMNS, $rule->{'MATCHVALUE'};
			push @COLUMNS, $rule->{'FILTER'};
			push @COLUMNS, $rule->{'EXEC'};
			push @COLUMNS, $rule->{'VALUE'};		# EXECVALUE
			push @COLUMNS, $rule->{'SCHEDULE'};	# SHIP_SCHEDULE
			push @COLUMNS, $rule->{'CODE'};	# UBER_GROUP
			push @COLUMNS, $rule->{'IMAGE'}; # UBER_IMAGE
			push @COLUMNS, $rule->{'TAX'};	# UBER_TAX
			push @COLUMNS, $rule->{'WEIGHT'};# UBER_WEIGHT

			my $status  = $csv->combine(@COLUMNS);  # combine columns into a string
			my $line    = $csv->string();           # get the combined string
			print "$line\r\n";
			}

		}
	exit;
	}

if ($VERB eq 'IMAGES') { 
	foreach my $r (@{MEDIA::folderlist($USERNAME)}) {
		}
	$template_file = 'images.shtml'; 
	}



if ($VERB eq 'DUMP_PAGE') {
	require PAGE;
	use YAML::Syck;

	my ($SAFE) = $ZOOVY::cgiv->{'SAFENAME'};
	
	use Data::Dumper;
	my ($PG) = PAGE->new($USERNAME,$SAFE,PRT=>$PRT,NS=>'_');
	foreach my $k (keys %{$PG}) {
		if (substr($k,0,1) eq '_') { delete $PG->{$k}; }
		}
	$GTOOLS::TAG{'<!-- DUMP -->'} = "YAML DUMP:\n".YAML::Syck::Dump($PG);
	$VERB = 'NAVCATS';
	}

##
##
##
if ($VERB eq 'SOGS-SAVE') {
	require POGS;

   my $XML = '';
	my $fh = $q->param('FILE');
   my $filename = $fh;
   print STDERR "FILENAME: $filename\n";
   if (not defined $fh) {
      ## Crap, not defined!
      }
   elsif (defined $fh) {
      while (<$fh>) { $XML .= $_; }
      }

	# print STDERR "INPUT XML: $XML\n";

	my ($sogref) = @{&POGS::deserialize($XML)};

	my $ID = $sogref->{'id'};
	my $NAME = $sogref->{'prompt'};
	$sogref->{'debug'} = "XML-IMPORT.$LUSERNAME.".time();

	# print STDERR "[$ID] [$NAME] [$XML]\n";
	$LU->log("SETUP.IMPORT.SOG","Uploaded/Saved SOG ID=$ID NAME=$NAME","SAVE");

	# &POGS::register_sog($USERNAME,$ID,$NAME,$XML);
	&POGS::store_sog($USERNAME,$sogref);
	$VERB = 'SOGS';
	}

##
## resort the @options by the prompt of the option
##
if ($VERB eq 'SOG_RESORT') {
	require POGS;
	my $ID = $ZOOVY::cgiv->{'ID'};
	my $NAME = $ZOOVY::cgiv->{'NAME'};
	my ($sogref) = &POGS::load_sogref($USERNAME,$ID);

	my $options = $sogref->{'@options'};
	my %prompts = ();
	foreach my $ref (@{$options}) {
		$prompts{"$ref->{'prompt'}\t$ref->{'v'}"} = $ref;
		}
	
	my @options = ();
	foreach my $k (sort keys %prompts) {
		push @options, $prompts{$k};
		}

	$sogref->{'@options'} = \@options;
	&POGS::store_sog($USERNAME,$sogref);

	$VERB = 'SOGS';
	}


##
##
##
if ($VERB eq 'SOGS') { 
	require POGS;
	my $listref = &POGS::list_sogs($USERNAME);	
	my $c = '';
	my $r = '';
	foreach my $k (sort keys %{$listref}) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class=\"$r\">";
		$c .= "<td>$k</td><td>&nbsp;</td><td>$listref->{$k}</td><td>&nbsp;</td>";
		$c .= "<td>&nbsp;|&nbsp;</td>";
		$c .= "<td><a target=\"_blank\" href=\"index.cgi?VERB=SHOW_SOGXML&ID=$k&NAME=$listref->{$k}\">View XML</a></td>";
		$c .= "<td>&nbsp;|&nbsp;</td>";
		$c .= "<td><a target=\"_blank\" href=\"index.cgi?VERB=SOG_RESORT&ID=$k&NAME=$listref->{$k}\">Resort by Prompt</a></td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- SOGS -->'} = $c;
	$template_file = 'sogs.shtml'; 
	}

if ($VERB eq 'PRODUCTS') { $template_file = 'products.shtml'; }
if ($VERB eq 'INVENTORY') { $template_file = 'inventory.shtml'; }
if ($VERB eq 'NAVCATS') { $template_file = 'navcats.shtml'; }
if ($VERB eq 'ORDERS') { $template_file = 'orders.shtml'; }
if ($VERB eq 'TRACKING') { $template_file = 'tracking.shtml'; }
if ($VERB eq 'CUSTOMERS') { $template_file = 'customers.shtml'; }
if ($VERB eq 'REVIEWS') { $template_file = 'reviews.shtml'; }
if ($VERB eq 'REWRITES') { $template_file = 'rewrites.shtml'; }
if ($VERB eq 'YAHOO') { $template_file = 'yahoo.shtml'; }
if ($VERB eq 'OTHER') { $template_file = 'other.shtml'; }
if ($VERB eq 'LISTINGS') { $template_file = 'listings.shtml'; }
if ($VERB eq 'RULES') { $template_file = 'rules.shtml'; }
if ($VERB eq 'FAQS') { $template_file = 'faqs.shtml'; }
#if ($VERB eq 'TAXES') { $template_file = 'taxes.shtml'; }


# Note this is only reached if we are not saving, and/or we encountered an error which
# prevented the dumping.

my @TABS = ();
push @TABS, { name=>'HELP', link=>'index.cgi?VERB=', selected=>(($VERB eq 'HELP')?1:0) };
#if (($RESELLER eq 'MSOL') || ($LUSERNAME eq 'SUPPORT')) {
#	push @TABS, { name=>'Office Live', link=>'index.cgi?VERB=OFFICELIVE', selected=>(($VERB eq 'OFFICELIVE')?1:0) };
#	}
push @TABS, { name=>'Products',link=>'index.cgi?VERB=PRODUCTS', selected=>(($VERB eq 'PRODUCTS')?1:0) };
push @TABS, { name=>'Inventory',link=>'index.cgi?VERB=INVENTORY', selected=>(($VERB eq 'INVENTORY')?1:0) };
push @TABS, { name=>'SOGS',link=>'index.cgi?VERB=SOGS', selected=>(($VERB eq 'SOGS')?1:0) };
push @TABS, { name=>'Customers',link=>'index.cgi?VERB=CUSTOMERS', selected=>(($VERB eq 'CUSTOMERS')?1:0) };
push @TABS, { name=>'Reviews',link=>'index.cgi?VERB=REVIEWS', selected=>(($VERB eq 'REVIEWS')?1:0) };
push @TABS, { name=>'Categories',link=>'index.cgi?VERB=NAVCATS', selected=>(($VERB eq 'NAVCATS')?1:0) };
push @TABS, { name=>'URL Rewrites',link=>'index.cgi?VERB=REWRITES', selected=>(($VERB eq 'REWRITES')?1:0) };
push @TABS, { name=>'Orders',link=>'index.cgi?VERB=ORDERS', selected=>(($VERB eq 'ORDERS')?1:0) };
push @TABS, { name=>'Tracking',link=>'index.cgi?VERB=TRACKING', selected=>(($VERB eq 'TRACKING')?1:0) };
push @TABS, { name=>'Rules',link=>'index.cgi?VERB=RULES', selected=>(($VERB eq 'RULES')?1:0) };
push @TABS, { name=>'Listings',link=>'index.cgi?VERB=LISTINGS', selected=>(($VERB eq 'LISTINGS')?1:0) };
push @TABS, { name=>'Images',link=>'index.cgi?VERB=IMAGES', selected=>(($VERB eq 'IMAGES')?1:0) };
#push @TABS, { name=>'FAQS',link=>'index.cgi?VERB=FAQS', selected=>(($VERB eq 'FAQS')?1:0) };
push @TABS, { name=>'Other',link=>'index.cgi?VERB=OTHER', selected=>(($VERB eq 'OTHER')?1:0) };


if ($PRT>0) {
	@TABS = ();
	push @TABS, { name=>'HELP', link=>'index.cgi?VERB=', selected=>(($VERB eq 'HELP')?1:0) };
	push @TABS, { name=>'Categories',link=>'index.cgi?VERB=NAVCATS', selected=>(($VERB eq 'NAVCATS')?1:0) };	
	push @TABS, { name=>'Customers',link=>'index.cgi?VERB=CUSTOMERS', selected=>(($VERB eq 'CUSTOMERS')?1:0) };
	push @TABS, { name=>'Reviews',link=>'index.cgi?VERB=REVIEWS', selected=>(($VERB eq 'REVIEWS')?1:0) };
	push @TABS, { name=>'URL Rewrites',link=>'index.cgi?VERB=REWRITES', selected=>(($VERB eq 'REWRITES')?1:0) };
	push @TABS, { name=>'Listings',link=>'index.cgi?VERB=LISTINGS', selected=>(($VERB eq 'LISTINGS')?1:0) };
	push @TABS, { name=>'Images',link=>'index.cgi?VERB=IMAGES', selected=>(($VERB eq 'IMAGES')?1:0) };
#	push @TABS, { name=>'FAQS',link=>'index.cgi?VERB=FAQS', selected=>(($VERB eq 'FAQS')?1:0) };
	push @TABS, { name=>'Rules',link=>'index.cgi?VERB=RULES', selected=>(($VERB eq 'RULES')?1:0) };
	}

push @TABS, { name=>'JEDI', link=>'index.cgi?VERB=JEDI', selected=>(($VERB eq 'JEDI')?1:0) };

#push @TABS, { name=>'Yahoo',link=>'index.cgi?VERB=YAHOO', selected=>(($VERB eq 'YAHOO')?1:0) };
#push @TABS, { name=>'Taxes',link=>'index.cgi?VERB=TAXES', selected=>(($VERB eq 'TAXES')?1:0) };

my $c = '';
foreach my $tab (@TABS) {
	next if ($tab->{'selected'});
	if ($c ne '') { $c .= " &nbsp; | &nbsp; "; }
	$c .= "<a href=\"$tab->{'link'}\">$tab->{'name'}</a>\n";
	};
$GTOOLS::TAG{'<!-- IMPORT_LINKS -->'} = $c;


if ($LU->get('todo.setup')) {
	my $t = TODO->new($USERNAME);	

	my ($need,$tasks) = $t->setup_tasks('import',LU=>$LU);
	$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('import',$tasks);
	}


if ($VERB eq 'SWF') {
	$template_file = 'swf.shtml';
	}

if ($VERB eq 'HELP') { 
	my $c = '';
	my $odbh = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select CREATED,CREATEDBY,FILETYPE,FILENAME from PRIVATE_FILES where FILETYPE='CSV' and MID=$MID /* $USERNAME */ order by CREATED desc limit 0,25";
	print STDERR "$pstmt\n";
	my $sth = $odbh->prepare($pstmt);
	$sth->execute();
	while ( my ($CREATED,$LUSERNAME,$TYPE,$FILENAME) = $sth->fetchrow() ) {
		$c .= "<tr>";
		$c .= "<td>$CREATED</td>";
		$c .= "<td>$LUSERNAME</td>";
		$c .= "<td>$TYPE</td>";
		my $DOWNLOAD_FILE = $FILENAME; $DOWNLOAD_FILE =~ s/_csv$/\.csv/g;
		$c .= "<td><a target=\"_top\" href=\"/biz/setup/private/index.cgi/$DOWNLOAD_FILE?VERB=VIEW&FILENAME=$FILENAME\">$FILENAME</a></td>";
		$c .= "</tr>";
		}
	$sth->finish();
	&DBINFO::db_user_close();
	if ($c eq '') { $c = "<tr><td colspan=3><td><i>No CSV Imports on record</i></td></tr>"; }
	$GTOOLS::TAG{'<!-- LOG -->'} = $c;

	$template_file = 'help.shtml'; 
	}


my $warning = '';
if (&ZOOVY::servername() eq 'newdev') {
	$warning = q~<div><font color='red'>ATTENTION ZOOVY EMPLOYEE: 
You appear to be accessing this application from NEWDEV, this application uses FLASH which uses your IE proxy settings. 
EVEN IF YOU ARE USING FIREFOX please make sure your IE proxy settings are correct or this will happen on production.</font></div>~;
	}

$GTOOLS::TAG{"<!-- SWFUPLOAD -->"} = qq~
<table><tr><td>
<label for="txtFileName">CSV File:</label>
</td><td>
<div>
	<div>
	<input type="text" id="txtFileName" disabled="true" style="border: solid 1px; background-color: #FFFFFF;" />
	<span id="spanButtonPlaceholder"></span>
	(10 MB max)
	</div>
	<div class="flash" id="fsUploadProgress">
	<!-- This is where the file progress gets shown.  SWFUpload doesn't update the UI directly.
			The Handlers (in handlers.js) process the upload events and make the UI updates -->
	</div>
	<input type="hidden" name="hidFileID" id="hidFileID" value="" />
	<!-- This is where the file ID is stored after SWFUpload uploads the file and gets the ID back from upload.php -->
</div>
$warning
</td></tr></table>

~;

my $ts = '';

my $ZJSID = $ZOOVY::ZJSID;

&GTOOLS::output(
   'title'=>'Setup : CSV Utility',
   'file'=>$template_file,
   'header'=>'1',
	'jquery'=>1,
	'head'=>qq~
<link href="swf/css/default.css" rel="stylesheet" type="text/css" />
<script type="text/javascript" src="swf/swfupload.js"></script>
<script type="text/javascript" src="swf/swfupload.swfobject.js"></script>
<script type="text/javascript" src="swf/js/fileprogress.js"></script>
<script type="text/javascript" src="swf/handlers-forms.js"></script>
<script type="text/javascript">
		var swfu;

		function uploadStartSaveParams() {
			// note: i'm using the prototype Form serialize!
			swfu.addPostParam('thisFrm',jQuery('#thisFrm').serialize());
			};

		 // Called by the queue complete handler to submit the form
		function uploadDone() {
		   try {
	      document.forms['thisFrm'].submit();
		   } catch (ex) {
	      alert("Error submitting form thisFrm");
   		}
		};


		window.onload = function () {
			swfu = new SWFUpload({
				// Backend settings
				upload_url: "/biz/setup/import/upload.cgi/$VERB",
				file_post_name: "file",
				post_params: {"USERNAME" : "$USERNAME", "ZJSID":"$ZJSID" },

				// Flash file settings
				file_size_limit : "20 MB",
				file_types : "*.*",			// or you could use something like: "*.doc;*.wpd;*.pdf",
				file_types_description : "All Files",
				file_upload_limit : "0",
				file_queue_limit : "1",

				// Event handler settings
				swfupload_loaded_handler : swfUploadLoaded,
				
				file_dialog_start_handler: fileDialogStart,
				file_queued_handler : fileQueued,
				file_queue_error_handler : fileQueueError,
				file_dialog_complete_handler : fileDialogComplete,
				
				upload_start_handler : uploadStartSaveParams,	// I could do some client/JavaScript validation here, but I don't need to.
				upload_progress_handler : uploadProgress,
				upload_error_handler : uploadError,
				upload_success_handler : uploadSuccess,
				upload_complete_handler : uploadComplete,

				// Button Settings
				button_image_url : "/biz/setup/import/swf/XPButtonBrowseText_61x22.png",
				button_placeholder_id : "spanButtonPlaceholder",
				button_width: 61,
				button_height: 22,
				
				// Flash Settings
				flash_url : "/biz/setup/import/swf/swfupload.swf",

				custom_settings : {
					progress_target : "fsUploadProgress",
					upload_successful : false
					},
				
				// Debug settings
				debug: false
			});


		};

//-->
</script>
~,
   'help'=>'#50344',
   'tabs'=>\@TABS,
   'bc'=>[
      { name=>'Setup',link=>'http://www.zoovy.com/biz/setup','target'=>'_top', },
      { name=>'CSV Utility',link=>'http://www.zoovy.com/biz/setup/import','target'=>'_top', },
      ],
	'msgs'=>\@MSGS,
	'todo'=>1,
   );




