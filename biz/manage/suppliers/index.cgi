#!/usr/bin/perl

use strict;

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;
use SUPPLIER;
use INVENTORY;
use ZTOOLKIT;
use ORDER;
use LUSER;
use PRODUCT::BATCH;
use Data::Dumper;
use strict;
use SITE::EMAILS;

my $title = "Utilities: Supply Chain Management";
my $q = new CGI; 

my $template_file = '';

## authenticate
require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_ADMIN');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my $VERB = $ZOOVY::cgiv->{'VERB'};

## Supply Chain (SC) Flag required
if ($FLAGS !~ /,SC,/) {
	my ($helplink, $helphtml) = GTOOLS::help_link('Supply Chain Webdoc', 50694);
	$GTOOLS::TAG{'<!-- WEBDOC -->'} = $helphtml;  
	$template_file = 'deny.shtml'; 
	$VERB = 'DENY';
	}


my @MSGS = ();

## hack until CUSTOMER MGR can be fixed and changed to VERB vs ACTION
if ($ZOOVY::cgiv->{'VERB'} ne '') { $VERB = $ZOOVY::cgiv->{'VERB'}; }

my $CODE = uc($ZOOVY::cgiv->{'CODE'});

## define SUPPLIER
my $S = undef;
##
## only grab SUPPLIER (and info) if this is a pre-existing SUPPLIER
##  (does profile need to be added here??)
print STDERR "SUPPLIER: VERB[$VERB] CODE[$CODE]\n";


## breadcrumbs
my @BC = ();
push @BC, { 'name'=>'Utilities', 'link'=>'/biz/utilities/index.cgi', 'target'=>'_top'};
push @BC, { 'name'=>'Supply Chain', link=>'/biz/utilities/suppliers/index.cgi', 'target'=>'_top'};

## TABS
my @TABS = ();


$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;


##
## SAVE New Supplier
##
if ($VERB eq 'NEW-SAVE') {
	require WHOLESALE;

	## create directory to store SC orders
#	my $path = &ZOOVY::resolve_userpath($USERNAME);
#	mkdir($path.'/SC',0777);
#	if (!-d $path.'/SC') {
#		$ERROR = 'Could not create directory for supply chain orders.';
#		}

	## validation checks
	if ($CODE eq '') { push @MSGS, "ERROR|Supplier Code cannot be blank"; }
	if (SUPPLIER::exists($USERNAME,$CODE)) { push @MSGS, "ERROR|Supplier Code [$CODE] already exists"; }
	if ($CODE !~ /^([0-9A-Z]+)$/) { push @MSGS, "ERROR|Supplier Code is invalid."; }
	if ($CODE eq 'GIFTCARD') { push @MSGS, "ERROR|The Code 'GIFTCARD' is reserved."; }

#	if (not &WHOLESALE::validate_formula($ZOOVY::cgiv->{'MARKUP'})) { push @MSGS, "ERROR|Markup formula does not appear to be valid."; }
#	if ($ZOOVY::cgiv->{'FORMAT'} eq '') {	push @MSGS, "ERROR|Supplier Order Format does not appear to be set";}
#	if ($ZOOVY::cgiv->{'MODE'} eq '') { push @MSGS, "ERROR|Supplier Data Integration Type does not appear to be set"; }
#	if (uc($ZOOVY::cgiv->{'MODE'}) eq 'API' && $FLAGS !~ /,API/) { push @MSGS, "ERROR|API bundle needs to be added to your account."; }

	if (scalar(grep /^ERROR\|/, @MSGS)==0) {
		($CODE,my $ERROR) = SUPPLIER::create($USERNAME,$CODE,'NEW'=>1,'PROFILE'=>$ZOOVY::cgiv->{'PROFILE'});
		if (defined $CODE) {
			$LU->log('SUPPLIER.CREATE',"[CODE: $CODE] was created",'INFO');
			($S) = SUPPLIER->new($USERNAME,$CODE);
			if (not defined $S) {
				push @MSGS, "ISE|SUPPLIER::create returned success, but supplier could not be instantiated after create!?!?";
				}	
			}
		else {
			push @MSGS, "ERROR|$ERROR";
			}
		}

	## MESSAGE back to merchant
	if (scalar(grep /^(ISE|ERROR)\|/, @MSGS)>0) {	
		$VERB = 'NEW';
		}
	else {	
		push @MSGS, "SUCCESS|Your Supplier $CODE has been successfully added.";
		$VERB = 'EDIT';
		}
	}



##
## Form for creating new Supplier
## 
## note: USETHEFORCE is passed to automatically setup a new JEDI business
##
if ($VERB eq 'NEW') { 
	$template_file = 'new.shtml';
	
#	print STDERR "Adding new supplier\n";
	$GTOOLS::TAG{'<!-- CODE -->'} = ($ZOOVY::cgiv->{'CODE'})?$ZOOVY::cgiv->{'CODE'}:'';
	$GTOOLS::TAG{'<!-- PARTNER_ATLAST -->'} = '';
	$GTOOLS::TAG{'<!-- PARTNER_SHIPWIRE -->'} = '';
	$GTOOLS::TAG{'<!-- PARTNER_DOBA -->'} = '';
	$GTOOLS::TAG{'<!-- PARTNER_QB -->'} = '';
	$GTOOLS::TAG{'<!-- PARTNER_AMZ -->'} = '';

	## http://www.zoovy.com/biz/utilities/suppliers/index.cgi?VERB=USETHEFORCE&USERNAME=ZSMC&MID=16804&LOGIN=brian@zoovy.com
	## IF VERB eq USETHEFORCE
	#if ($VERB eq 'USETHEFORCE') {
	#	$GTOOLS::TAG{'<!-- MODE_JEDI -->'} = 'checked';
	#	$GTOOLS::TAG{'<!-- JEDI_DOMAIN -->'} = ($ZOOVY::cgiv->{'USERNAME'})?$ZOOVY::cgiv->{'USERNAME'}:'';
	#	$GTOOLS::TAG{'<!-- JEDI_LOGIN -->'} = ($ZOOVY::cgiv->{'LOGIN'})?$ZOOVY::cgiv->{'LOGIN'}:'';
	#	$GTOOLS::TAG{'<!-- JEDI_PASS -->'} = ($ZOOVY::cgiv->{'LOGIN'})?$ZOOVY::cgiv->{'LOGIN'}:'';
	#	}
	#else {
#	$GTOOLS::TAG{'<!-- JEDI_DOMAIN -->'} = ($ZOOVY::cgiv->{'.jedi.domain'})?$ZOOVY::cgiv->{'.jedi.domain'}:'';
#	$GTOOLS::TAG{'<!-- JEDI_LOGIN -->'} = ($ZOOVY::cgiv->{'.jedi.login'})?$ZOOVY::cgiv->{'.jedi.login'}:'';
#	$GTOOLS::TAG{'<!-- JEDI_PASS -->'} = ($ZOOVY::cgiv->{'.jedi.pass'})?$ZOOVY::cgiv->{'.jedi.pass'}:'';
	#	}

#	if ($ZOOVY::cgiv->{'MODE'}) {
#		$GTOOLS::TAG{'<!-- MODE_'.($ZOOVY::cgiv->{'MODE'}).' -->'} = 'checked';
#		}

	$GTOOLS::TAG{'<!-- NAME -->'} = ($ZOOVY::cgiv->{'NAME'})?$ZOOVY::cgiv->{'NAME'}:'';
	$GTOOLS::TAG{'<!-- ACCOUNT -->'} = ($ZOOVY::cgiv->{'ACCOUNT'})?$ZOOVY::cgiv->{'ACCOUNT'}:'';
	$GTOOLS::TAG{'<!-- PHONE -->'} = ($ZOOVY::cgiv->{'PHONE'})?$ZOOVY::cgiv->{'PHONE'}:'';
	$GTOOLS::TAG{'<!-- EMAIL -->'} = ($ZOOVY::cgiv->{'EMAIL'})?$ZOOVY::cgiv->{'EMAIL'}:'';
	$GTOOLS::TAG{'<!-- WEBSITE -->'} = ($ZOOVY::cgiv->{'WEBSITE'})?$ZOOVY::cgiv->{'WEBSITE'}:'';	
	
	$GTOOLS::TAG{'<!-- MARKUP -->'} = ($ZOOVY::cgiv->{'MARKUP'})?$ZOOVY::cgiv->{'MARKUP'}:'';

	## PROFILE addition
	my $profileref = &ZOOVY::fetchprofiles($USERNAME);
	foreach my $profile (@{$profileref}) {
		my $selected = '';
		if ($profile eq 'DEFAULT') { $selected = "selected"; }
		$GTOOLS::TAG{'<!-- PROFILE -->'} .= qq~<option $selected value="$profile">$profile</option>~;
		} 
	
	push @BC, { name=>'Add New Supplier' };
	}



##
## SANITY: if we made it here and VERB is still set, we're going to need to set $S
##

if (defined $S) {
	## YAY!
	}
elsif (($VERB eq '') || ($VERB eq 'NEW') || ($VERB eq 'NEW-SAVE')) {
	## it's okay, we don't need a supplier code.
	}
elsif ($CODE eq '') {
	push @MSGS, "ISE|Supplier CODE not set";
	$VERB = '';
	}
else {
	($S) = SUPPLIER->new($USERNAME,$CODE); 
	if (not defined $S) {
		push @MSGS, "ISE|Supplier CODE:$CODE was not found";
		$VERB = '';
		}
	}




$GTOOLS::TAG{'<!-- CODE -->'} = $CODE;
if (defined $S) { push @BC, { name=>"$CODE", link=>"/biz/manage/suppliers/index.cgi?VERB=EDIT&CODE=$CODE", target=>'_top' }; }
if ($CODE ne '') {
	push @TABS, { 'name'=>"$CODE Setup", link=>"/biz/manage/suppliers/index.cgi?VERB=EDIT&CODE=$CODE" };
	push @TABS, { 'name'=>"$CODE Products", link=>"/biz/manage/suppliers/index.cgi?VERB=PRODUCTS&CODE=$CODE" };
	# push @TABS, { 'name'=>"$CODE Inventory", link=>"?VERB=INVENTORY&CODE=$CODE" };
	push @TABS, { 'name'=>"$CODE Orders", link=>"/biz/manage/suppliers/index.cgi?VERB=ORDERS&CODE=$CODE" };
	}
else {
	push @TABS, { 'name'=>"Non-Confirmed Orders", link=>"/biz/manage/suppliers/index.cgi?VERB=NON_CONF_ORDERS" };	
	}

##
## sanity: at this point $S is guaranteed to be set, or VERB is ''
##


##
## Remove Supplier 
##
if ($VERB eq 'REMOVE') {
	$template_file = 'remove-confirm.shtml';
	push @BC, { name=>"Remove" };
	}

if ($VERB eq 'REMOVE-CONFIRM') {
	$VERB = '';
	&SUPPLIER::nuke($USERNAME,$CODE,products=>$ZOOVY::cgiv->{'products'});
	}

if ($VERB eq 'EDIT-PRODUCTS') {
	$GTOOLS::TAG{'<!-- MARKUP -->'} = ($S->fetch_property('MARKUP'))?$S->fetch_property('MARKUP'):$ZOOVY::cgiv->{'MARKUP'};
	}



if ($VERB eq 'SAVE-EDIT') {
	$VERB = 'EDIT';

	foreach my $k (keys %{$ZOOVY::cgiv}) {
		next if ($k eq '_NEXTVERB');

		my $was = $S->fetch_property($k);
		next if ($was eq $ZOOVY::cgiv->{$k});

		push @MSGS, "SUCCESS|Saved $k=$ZOOVY::cgiv->{$k} (was:$was)";
		$S->save_property($k,$ZOOVY::cgiv->{$k});
		}

	$S->save();

	if ($ZOOVY::cgiv->{'_NEXTVERB'} eq 'INVENTORY-IMPORT') {
		# push @MSGS, "SUCCESS|Did import! (not really)";

		require SUPPLIER::GENERIC;
		my ($JOBID,$lm) = &SUPPLIER::GENERIC::update_inventory($S,'*LU'=>$LU);

		foreach my $msg (@{$lm->msgs()}) {
			my ($ref,$status) = &LISTING::MSGS::msg_to_disposition($msg);
			push @MSGS, "$ref->{'_'}|$ref->{'+'}";
			}
		if ($JOBID > 0) {
			# push @MSGS, "LINK|/biz/batch/index.cgi?VERB=LOAD&JOB=$JOBID|View Job #$JOBID";
			}
		}

	}






if ($VERB eq 'EDIT') {

	## PROFILE addition
	my $profileref = &ZOOVY::fetchprofiles($USERNAME);
	my @PROFILESELECT = ();
	foreach my $profile (@{$profileref}) {
		push @PROFILESELECT, { v=>$profile, p=>$profile };
		} 

	my @FIELDS = ();
	push @FIELDS, { tab=>'GENERAL', id=>'PROFILE', title=>'Profile', type=>'select', options=>\@PROFILESELECT };
	push @FIELDS, { tab=>'GENERAL', id=>'MARKUP', title=>'Markup', type=>'text', size=>10, maxlength=>15 };
	push @FIELDS, { tab=>'GENERAL', id=>'NAME', title=>'Name', type=>'text', size=>30, maxlength=>40 };
	push @FIELDS, { tab=>'GENERAL', id=>'PHONE', title=>'Phone', type=>'text', size=>12, maxlength=>12 };
	push @FIELDS, { tab=>'GENERAL', id=>'EMAIL', title=>'Email', type=>'text', size=>30, maxlength=>40 };
	push @FIELDS, { tab=>'GENERAL', id=>'ACCOUNT', title=>'Account', type=>'text', size=>30, maxlength=>40 };
	push @FIELDS, { tab=>'GENERAL', id=>'WEBSITE', title=>'Website', type=>'text', size=>30, maxlength=>40 };
	push @FIELDS, { tab=>'GENERAL', id=>'ITEM_NOTES', title=>'Item Notes', type=>'checkbox', hint=>'Choose to display Supplier Code / Tracking info on Invoice (under each Item)'};
	push @FIELDS, { tab=>'GENERAL', type=>'text', title=>"Quickbooks Vendor Name", id=>".partner.vendor" };

	push @FIELDS, { tab=>'GENERAL', id=>'PARTNER', title=>'Partner', type=>'selectsubmit', options=>[
		{ v=>'', p=>'None' },
		#{ v=>'ATLAST', p=>'AtLast Fulfillment' },
		#{ v=>'SHIPWIRE', p=>'ShipWire' },
		#{ v=>'DOBA', p=>'DOBA', },
		#{ v=>'FBA', p=>'Fulfillment by Amazon', }
		# { v=>'QB' }
		]};



	if ($S->fetch_property('PARTNER') eq '') {
		}
	elsif ($S->fetch_property('PARTNER') eq 'ATLAST') {
		push @FIELDS, { type=>'text', title=>"AtLast Username", id=>".partner.username" };
		push @FIELDS, { type=>'text', title=>"AtLast Password", id=>".partner.password" };
		push @FIELDS, { title=>'API Inventory - Update Configuration', link=>"/biz/manage/suppliers/index.cgi?VERB=API-INVENTORY&CODE=$CODE" };
		}
	elsif ($S->fetch_property('PARTNER') eq 'SHIPWIRE') {
		push @FIELDS, { type=>'*hint', hint=>qq~<br>Signup for your <a target=_new href="http://partner.shipwire.com/o.php?id=1900">ShipWire account</a>~ };
		push @FIELDS, { type=>'text', title=>"ShipWire Username", id=>".partner.username" };
		push @FIELDS, { type=>'text', title=>"ShipWire Password", id=>".partner.password" };
		}
	elsif ($S->fetch_property('PARTNER') eq 'DOBA') {
		push @FIELDS, { type=>'text', title=>"DOBA Username", id=>".partner.username" };
		push @FIELDS, { type=>'text', title=>"DOBA Password", id=>".partner.password" };
		push @FIELDS, { type=>'text', title=>"DOBA Retailer ID", id=>".partner.retailer_id" };
		push @FIELDS, { type=>'text', title=>"DOBA Product Prefix", id=>".partner.product_prefix", size=>5, maxlength=>5, hint=>"This prefix will be prepended to the DOBA Supplier ID to create your PID [highly recommended!!]."};
		push @FIELDS, { type=>'checkbox', title=>"DOBA Prepay Merchant", id=>".partner.prepay", hint=>"Using Doba Prepay Services (prepay price will be used for product cost)." };
		push @FIELDS, { type=>'checkbox', title=>"Copy DOBA images to Zoovy", id=>".partner.image_copy", hint=>"You will want to copy images if you are syndicating these products to Googlebase or using them in a Newsletter." };
		push @FIELDS, { type=>'checkbox', title=>"Allow Product Updates", id=>".partner.product_updates", hint=>"Enabling this setting will allow doba to refresh/update descriptions images, etc. for existing products." };
		push @FIELDS, { type=>'info', title=>"DOBA Status", id=>".partner.status"};
		push @FIELDS, { type=>'info', title=>"DOBA Status Notes", id=>".partner.status_notes"};
		## changed so only SUPPORT can run reimport
		if ($LU->is_zoovy() eq 'SUPPORT') {
			push @FIELDS,  { title=>'Products - (Re)Import Watchlists - please run this import sparingly.', link=>"/biz/manage/suppliers/index.cgiindex.cgi?VERB=PRODUCTIMPORT&CODE=$CODE" };
			}
		else {
			push @FIELDS,  { title=>'Products - (Re)Import Watchlists - please submit a ticket to have your reimport run.', link=>"/biz/support/index.cgi?VERB=TICKET-CREATE" };
			}
		}

	my @AVAILABLE_PRODUCT_CONNECTORS = ();
	push @AVAILABLE_PRODUCT_CONNECTORS, {'v'=>'NONE','p'=>'NONE'};
	# push @AVAILABLE_PRODUCT_CONNECTORS,	{'v'=>'JEDI','p'=>'JEDI'};
	# push @AVAILABLE_PRODUCT_CONNECTORS, {'v'=>'CSV','p'=>'CSV'};
	push @FIELDS, { tab=>'PRODUCT', type=>'selectsubmit', id=>'PRODUCT_CONNECTOR', title=>'Product Connector', options=>\@AVAILABLE_PRODUCT_CONNECTORS };
	if ($S->fetch_property('PRODUCT_CONNECTOR') eq 'NONE') {
		# push @FIELDS, { tab=>'PRODUCT', type=>'*hint', 'hint'=>qq~Manually create and/or upload product lists.~ };
		push @FIELDS, { tab=>'PRODUCT', title=>'Products - Add Individual', link=>"/biz/manage/suppliers/index.cgi?VERB=PRODUCT-ADD&CODE=$CODE" };
		# push @FIELDS, { tab=>'PRODUCT', title=>'Products - Import Batch', link=>"index.cgi?VERB=PRODUCT-IMPORT&CODE=$CODE" };
		#push @FIELDS, {title=>'Products - Associate Existing', link=>"index.cgi?VERB=IMPORT&CODE=$CODE" };		
		}
	if ($S->fetch_property('PRODUCT_CONNECTOR') eq 'CSV') {
		}
	push @FIELDS, { tab=>'PRODUCT', title=>'Products - Report', link=>"/biz/manage/suppliers/index.cgi?VERB=PRODUCTS&CODE=$CODE" };		

	##
	##
	##
	push @FIELDS, { tab=>'SHIPPING',  type=>'selectsubmit', id=>'SHIP_CONNECTOR', title=>'Shipping Connector', options=>[	
		{'v'=>'NONE','p'=>'NONE'},
		# {'v'=>'JEDI','p'=>'JEDI'},
		{'v'=>'GENERIC','p'=>'GENERIC'},
		# {'v'=>'API','p'=>'API'},
		# {'v'=>'PARTNER','p'=>'PARTNER'},
		]};
	#if ($S->fetch_property('FORMAT') eq 'STOCK') {
	#	push @FIELDS, {tab=>'SHIPPING', title=>'Shipping - Configuration', note=>'Stock Shipping uses your Zoovy store configuration' };
	#	}
	if ($S->fetch_property('SHIP_CONNECTOR') eq 'NONE') {
		push @FIELDS, { type=>'note', tab=>'SHIPPING', title=>'Shipping', note=>'None uses your store configuration' };
		}
	elsif ($S->fetch_property('SHIP_CONNECTOR') eq 'GENERIC') {
		push @FIELDS, { type=>'link', tab=>'SHIPPING', title=>'Shipping - Configuration', link=>"/biz/manage/suppliers/index.cgi?VERB=GENERIC-SHIPPING&CODE=$CODE" };
		}
	#elsif ($S->fetch_property('SHIP_CONNECTOR') eq 'API') {
	#	push @FIELDS, { tab=>'SHIPPING',	type=>'text', title=>'ShipQuote URL',	id=>'.api.shipurl',  size=>90, maxlength=>128,	};
	#	}
	#elsif ($S->fetch_property('SHIP_CONNECTOR') eq 'PARTNER') {
#<!-- START_SHOW_IF_PARTNER -->
#	<tr>
#		<td colspan='2'><input type="checkbox" name=".ship.methods_4" <!-- .ship.methods_4 -->> <b>Enable Integrated Partner Shipping</b></td>
#	</tr>
#	<tr>	
#		<td width='30'>&nbsp;&nbsp;&nbsp;</td>
#		<td><i>This method (if enabled) will disable all other supplier shipping methods</i></td>
#	</tr>
#	<tr>
#		<td colspan='2'><hr></td>
#	</tr>
#<!-- END_SHOW_IF_PARTNER -->
	#	}
	#elsif ($S->fetch_property('SHIP_CONNECTOR') eq 'JEDI') {
	#	}
	#push @FIELDS, {tab=>'PRODUCT', title=>'Products - Add Individual', link=>"index.cgi?VERB=ADDPRODUCTS&CODE=$CODE" };
	#push @FIELDS, {tab=>'PRODUCT', title=>'Products - Import Batch', link=>"index.cgi?VERB=PRODUCTIMPORT&CODE=$CODE" };
	#push @FIELDS, {tab=>'PRODUCT', title=>'Products - Report', link=>"index.cgi?VERB=PRODUCTS&CODE=$CODE" };		

	
	push @FIELDS, { tab=>'INVENTORY',  type=>'selectsubmit', id=>'INVENTORY_CONNECTOR', title=>'Inventory Download Connector', options=>[	
		{'v'=>'NONE','p'=>'NONE'},
		{'v'=>'GENERIC','p'=>'GENERIC'},
		# {'v'=>'JEDI','p'=>'JEDI'},
		# {'v'=>'API','p'=>'API'},
		# {'v'=>'PARTNER','p'=>'PARTNER'},
		]};

	if ($S->fetch_property('INVENTORY_CONNECTOR') eq 'NONE') {
		}
	elsif ($S->fetch_property('INVENTORY_CONNECTOR') eq 'GENERIC') {
		push @FIELDS, { 'tab'=>'INVENTORY', type=>'url',	title=>'FTP/HTTP URL', id=>'.inv.url',  size=>90, maxlength=>128, 'hint'=>'use ftp://user:password@domain.com/path/to/file.csv' };
		push @FIELDS, { 'tab'=>'INVENTORY', type=>'select', title=>'Import Frequency', id=>'.inv.updateauto',  hint=>'', options=>[
			{'v'=>'0', 'p'=>'Manual' },
			{'v'=>'1', 'p'=>'Daily' },
			] };
		push @FIELDS, { 'tab'=>'INVENTORY', type=>'textarea', title=>'Inventory Header', id=>'.inv.header', cols=>90, rows=>4, };
		push @FIELDS, { 'tab'=>'INVENTORY', type=>'button', title=>'Start Import', 'verb'=>'INVENTORY-IMPORT' };
		}
#	elsif ($S->fetch_property('INVENTORY_CONNECTOR') eq 'JEDI') {
#		}
#	elsif ($S->fetch_property('INVENTORY_CONNECTOR') eq 'API') {
#		push @FIELDS, { tab=>'ORDER', title=>'API Inventory - Update Configuration', link=>"index.cgi?VERB=API-INVENTORY&CODE=$CODE" };
#		push @FIELDS, {
#			type=>'text',
#			title=>'REST Inventory URL',
#			id=>'.api.invurl',  
#			size=>90, maxlength=>128,
#			};
#		push @FIELDS, {
#			type=>'select',
#			title=>'API Protocol',
#			id=>'.api.invurl',  
#			size=>90, maxlength=>128,
#			options=>['',''],
#			};
#		}
#	elsif ($S->fetch_property('INVENTORY_CONNECTOR') eq 'PARTNER') {
#		}






	push @FIELDS, { tab=>'ORDER', id=>'FORMAT', type=>'selectsubmit', title=>'Order Formatting', options=>[
		{ 'v'=>'NONE', 'p'=>'NONE' },
		{ 'v'=>'STOCK', 'p'=>'STOCK' },
		{ 'v'=>'DROPSHIP', 'p'=>'DROPSHIP' },
		{ 'v'=>'FULFILL', 'p'=>'FULFILL' }		
		]
		};

	if ($S->fetch_property('FORMAT') eq 'NONE') {		
		## None
		}
	elsif ($S->fetch_property('FORMAT') =~ /^(STOCK|DROPSHIP|FULFILL)$/) {
		## Auto-approve ordres?
		push @FIELDS, { 'tab'=>'ORDER', type=>'selectsubmit', id=>'.order.auto_approve', title=>'Automatic Ordering', options=>[
			{ 'v'=>'0', 'p'=>'No' },
			{ 'v'=>'1', 'p'=>'Yes' },
			],
		'hint'=>q~Some merchants who receive a relatively small volume and wish to approve each order individually prefer
this option. Orders will NOT be transmitted to the supplier until they are closed. ~ 
			};

		}


	push @FIELDS, { tab=>'ORDER',  type=>'selectsubmit', id=>'ORDER_CONNECTOR', title=>'Order Connector', options=>[	
		{'v'=>'NONE','p'=>'NONE'},
		# {'v'=>'JEDI','p'=>'JEDI'},
		{'v'=>'EMAIL','p'=>'EMAIL'},
		# {'v'=>'FAX','p'=>'FAX'},
		{'v'=>'FTP','p'=>'FTP'},
		{'v'=>'API','p'=>'API'},
		{'v'=>'AMZSQS','p'=>'Amazon SQS'},
		# {'v'=>'AMZFWS','P'=>'Amazon Fulfillment'},
		# {'v'=>'PARTNER','p'=>'PARTNER'},
		]};
	
	my $GET_VERSION = 0;
	if ($S->order_connector() eq 'NONE') {
		}
	#elsif ($S->order_connector() eq 'JEDI') {
	#	}
	elsif ($S->order_connector() eq 'AMZSQS') {
		push @FIELDS, { 'tab'=>'ORDER', type=>'text', title=>'Amazon AWS Access key', id=>'.order.aws_access_key' };
		push @FIELDS, { 'tab'=>'ORDER', type=>'text', title=>'Amazon AWS Secret key', id=>'.order.aws_secret_key' };
		push @FIELDS, { 'tab'=>'ORDER', type=>'text', title=>'Amazon SQS Channel', id=>'.order.aws_sqs_channel' };
		$GET_VERSION++;
		}
	elsif ($S->order_connector() eq 'FTP') {
		push @FIELDS, { 'tab'=>'ORDER', type=>'url',	title=>'FTP URL', id=>'.order.ftp_url',  size=>90, maxlength=>128,	hint=>"Format: ftp://user\@pass/path/to/file.txt" };	
		$GET_VERSION++;
		}
	elsif ($S->order_connector() eq 'EMAIL') {
		## EMAIL and FAX are both really EMAIL
		#my @AVAILABLE_EMAILS = ();
		#my ($se) = SITE::EMAILS->new($USERNAME,PROFILE=>$S->fetch_property('PROFILE'));
		#my $msgs = $se->available('SUPPLY');
		#foreach my $ref (@{$msgs}){
		#	push @AVAILABLE_EMAILS, { 'p'=>"$ref->{'MSGID'}: $ref->{'MSGTITLE'}", 'v'=>"$ref->{'MSGID'}" };
		#	}
		#if (scalar(@AVAILABLE_EMAILS)==0) {
		#	push @AVAILABLE_EMAILS, { 'p'=>'No Supply Chain Emails Defined', 'v'=>'' };
		#	}
		#if ($S->order_connector() eq 'EMAIL') {
		push @FIELDS, { 'tab'=>'ORDER', type=>'select',	title=>'Email Format', id=>'.order.email.format',  
			options=>[
				{ p=>'HTML', v=>'HTML' },
				{ p=>'TXT', v=>'TXT' },
				{ p=>'XML', v=>'XML' },
				]
			};		
		push @FIELDS, { 'tab'=>'ORDER', type=>'email',	title=>'Email From:', id=>'.order.email_src',  size=>90, maxlength=>128,	};		
		push @FIELDS, { 'tab'=>'ORDER', type=>'email',	title=>'Email To:', id=>'.order.email',  size=>90, maxlength=>128,	};		
		push @FIELDS, { 'tab'=>'ORDER', type=>'email',	title=>'Bcc', id=>'.order.bcc',  size=>90, maxlength=>128,	};		
		push @FIELDS, { 'tab'=>'ORDER', type=>'text',	title=>'Subject', id=>'.order.email.subject',  size=>90, maxlength=>128,	};		
		push @FIELDS, { 'tab'=>'ORDER', type=>'textarea',	title=>'Message Body', id=>'.order.email.body', cols=>77, rows=>20, 'hint'=>q~~ };		

		# push @FIELDS, { 'tab'=>'ORDER', type=>'select', 'id'=>'.order.msgid', 'options'=>\@AVAILABLE_EMAILS };
		#elsif ($S->order_connector() eq 'FAX') {
		#	push @FIELDS, { 'tab'=>'ORDER', type=>'phone',	title=>'Fax Phone', id=>'.order.fax',  size=>90, maxlength=>128,	};		
		#	push @FIELDS, { 'tab'=>'ORDER', type=>'*hint', 'hint'=>'Example: 1-###-###-####' };
		#	$GET_VERSION++;
		#	}
	
		}
	elsif ($S->order_connector() eq 'API') {
		push @FIELDS, { 'tab'=>'ORDER', type=>'url',	title=>'API URL', id=>'.order.api_url',  size=>90, maxlength=>128,	hint=>"Format: http://user\@pass/path/to/post.cgi" };		
		$GET_VERSION++;
		}

	if ($S->order_connector() ne 'NONE') {
		## confirmation required
		# push @FIELDS, { id=>'.order.conf' };
		## include Order Notes (from the original order)
		push @FIELDS, { 'tab'=>'ORDER', 'type'=>'checkbox', title=>'Include Order Notes', id=>'.order.notes', 'hint'=>'Include Order Notes (from original order)' };
		push @FIELDS, { 'tab'=>'ORDER', 'type'=>'checkbox', title=>'Show Cost Field', id=>'.order.field_cost' };
		push @FIELDS, { 'tab'=>'ORDER', 'type'=>'checkbox', title=>'Hide Zero Qty Items', id=>'.order.dont_show_zero_qtys', 'hint'=>'This will override the title in the email message' };
		}

	#elsif ($S->order_connector() eq 'PARTNER') {
	#	}

	if ($GET_VERSION) {
		push @FIELDS, { 
			'tab'=>'ORDER',
			type=>'selectsubmit',
			title=>'Order Format',
			id=>".order.format",
			options=>[
#				{ p=>"ORDER v3.108 - released: 2007-03-13 supported: 2010-03-13", v=>108 },
#				{ p=>"ORDER v3.118 - released: 2009-10-01 supported: 2012-10-01", v=>118 },
				{ v=>'', p=>"-", },
				{ v=>'XML#201240',  p=>"v.201240 XML - valid until: 2015-10-15", },
				{ v=>'XSLT#201240', p=>"v.201240 XML w/XSLT- valid until: 2015-10-15", },
				{ v=>'JSON#201240', p=>"v.201240 JSON - valid until: 2015-10-15", },
				{ v=>'CSV3D#0', p=>"ORDER CSV-3D (brief output - no expiration)" },
				{ v=>'XCBL#4', p=>"XCBL v4 (brief output - no expiration)" },
				{ v=>'XML#200', p=>"** END OF LIFE ** XML ORDER v3.200 - valid until: 2013-09-01",},
#				{ p=>"ORDER v1 (deprecated)", v=>1 }
				], 
			};

		if ($S->fetch_property('.order.format') =~ /^XSLT\#/) {
			push @FIELDS, {
				'tab'=>'ORDER',
				'type'=>'textarea',
				'id'=>'.order.xslt',
				'title'=>'XSLT Transformation',
				'rows'=>30, cols=>120,
				};
			}

		}


	if ($S->order_connector() eq 'NONE') {
		## nothing to do here..
		}
	else {
		push @FIELDS, {
			tab=>'ORDER',	type=>'select', title=>'Automatically Transmit Orders without Payment', 
			id=>".api.dispatch_on_create",
			hint=>'Normally orders will wait until they are paid in full before they are transmitted (dispatched) to supplier',
			options=>[
				{ p=>"No [RECOMMENDED]", v=>"0" },
				{ p=>"Yes", v=>"1" },
				],
			};
		push @FIELDS, { tab=>'ORDER',	type=>'select',title=>'Transmit Full Order Contents', id=>".api.dispatch_full_order",
			options=>[
				{ p=>"No [RECOMMENDED]", v=>"0" },
				{ p=>"Yes", v=>"1" },
				],
			};
		}

	


	# push @FIELDS, { tab=>'ORDER', title=>'Orders - Delivery Configuration', link=>"index.cgi?VERB=ORDERING&CODE=$CODE" };
	push @FIELDS, { tab=>'ORDER', title=>'Orders - Report', link=>"/biz/manage/suppliers/index.cgi?VERB=ORDERS&CODE=$CODE" };

#		push @FIELDS, {
#			tab=>'ORDER',
#			type=>'text',
#			title=>'API Order URL',
#			id=>'.api.orderurl',  
#			size=>90, maxlength=>128,
#			hint=>qq~Examples of URLs:<br>
#<table class="zoovytable">
#<tr class="zoovysub1header">
#<th>TYPE</th>
#<th>EXAMPLE</th>
#<th>NOTES</th>
#</tr>
#<tr>
#	<td class="hint">REST</td>
#	<td class="hint">https://user:pass\@www.somedomain.com/path/to/file.php</td>
#	<td class="hint">POST will contain variable Contents (text string of file), OrderID</td>
#</tr>
#<tr>
#	<td class="hint">FTP</td>
#	<td class="hint">ftp://user:pass\@www.somedomain.com/path/file-%orderid%.xml</td>
#	<td class="hint">%order% will be interpolated with the actual order id. zoovy only supports passive FTP transfers.</td>
#</tr>
#<tr>
#	<td class="hint">EMAIL</td>
#	<!-- removed '?subject=%orderid' from the end of 'mailto:email\@domain.com' to resolve issue of mail not being sent. andrewt 03/29/2010 -->
#	<td class="hint">mailto:email\@domain.com</td>
#	<td class="hint">document will be sent as mime attachment.</td>
#</tr>
#<tr>
#	<td class="hint">AMAZON SQS</td>
#	<td class="hint" colspan=2><i>Please contact Zoovy for assistance</i></td>
#</tr>
#</table>
#~,

#	if (0) {
#		push @FIELDS, {title=>'Products - Report', link=>"index.cgi?VERB=PRODUCTS&CODE=$CODE" };		
#		push @FIELDS, {title=>'Orders - Delivery Configuration', link=>"index.cgi?VERB=ORDERING&CODE=$CODE" };
#		push @FIELDS, {title=>'Orders - Report', link=>"index.cgi?VERB=ORDERS&CODE=$CODE" };
#
#		## DOBA
#		}
#	## JEDI
#	elsif ($MODE eq 'JEDI') {
##		push @FIELDS, { title=>"Products - Subscribe from ".$S->fetch_property('.jedi.customer')." login", 
##							link=>"https://ssl.zoovy.com/".$S->fetch_property('.jedi.username')."/login.cgis?login=".$S->fetch_property('.jedi.customer') };
#		push @FIELDS, {title=>'Products - Report', link=>"index.cgi?VERB=PRODUCTS&CODE=$CODE" };		
#		push @FIELDS, { title=>'Orders - Delivery Configuration', link=>"index.cgi?VERB=ORDERING&CODE=$CODE" };	
#		push @FIELDS, {title=>'Orders - Report', link=>"index.cgi?VERB=ORDERS&CODE=$CODE" };
#		push @FIELDS, { title=>'Payment Method - Configuration', link=>"index.cgi?VERB=PAYMENT-EDIT&CODE=$CODE" };	
#		push @FIELDS, { title=>'JEDI Inventory', link=>"index.cgi?VERB=JEDI-LOAD-INVENTORY&CODE=$CODE" };	
#		}


	push @FIELDS, { tab=>'TRACK',  type=>'selectsubmit', id=>'TRACK_CONNECTOR', title=>'Connector', options=>[	
		{'v'=>'NONE','p'=>'NONE'},
		# {'v'=>'JEDI','p'=>'JEDI'},
		{'v'=>'API','p'=>'API'},
		# {'v'=>'PARTNER','p'=>'PARTNER'},
		]};


	##
	## SANITY: at this point all fields are configured and just need to be output.
	##
	
	## Build FIELDS
	foreach my $field (@FIELDS) {
		my $out = '';
		# print STDERR Dumper($field);
		my $value = $S->fetch_property($field->{'id'});
		if ($field->{'type'} eq 'text') {
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><input class="formed" type="textbox" name="$field->{'id'}" value="$value" size="$field->{'size'}" maxlength="$field->{'maxlength'}"></td></tr>~;
			}
		elsif ($field->{'type'} eq 'textarea') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><textarea name="$field->{'id'}" rows="$field->{'rows'}" cols="$field->{'cols'}">$value</textarea></td></tr>~;
			} 
		elsif ($field->{'type'} eq 'url') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><input type='textbox' size=150 name="$field->{'id'}" value="$value"></td></tr>~;
			} 
		elsif ($field->{'type'} eq 'email') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><input type='textbox' size=65 name="$field->{'id'}" value="$value"></td></tr>~;
			} 
		elsif ($field->{'type'} eq 'select') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><select name="$field->{'id'}">~;
			foreach my $set (@{$field->{'options'}}) {
				my $selected = ($set->{'v'} eq $value)?'selected':'';
				$out .= "<option $selected value=\"$set->{'v'}\">$set->{'p'}</option>\n";
				}
			$out .= qq~</td></tr>~;
			}
		elsif ($field->{'type'} eq 'selectsubmit') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><select onChange="\$('#thisFrm').showLoading().submit();" name="$field->{'id'}">~;
			foreach my $set (@{$field->{'options'}}) {
				my $selected = ($set->{'v'} eq $value)?'selected':'';
				$out .= "<option $selected value=\"$set->{'v'}\">$set->{'p'}</option>\n";
				}
			$out .= qq~</td></tr>~;
			}
		elsif ($field->{'type'} eq 'checkbox') { 
			my $checked = ($value == 1)?'checked':'';
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td>~.
					  qq~<td><select name="$field->{'id'}">
								<option value="0" ~.(($value==0)?'selected':'').qq~>No</option>
								<option value="1" ~.(($value==1)?'selected':'').qq~>Yes</option>
								</select></td></tr>~;
			
			} 
		elsif ($field->{'type'} eq 'note') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td><td>$field->{'note'}</td></tr>~;
			} 
		elsif ($field->{'type'} eq '*hint') { 
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150><div class='hint'>$field->{'hint'}</div></td></tr>~;
			} 
		elsif ($field->{'type'} eq 'info') {
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top size=150>$field->{'title'}:</td><td><input class="formed" type="hidden" name="$field->{'id'}" value="$value">$value</td></tr>~;
			}
		elsif (($field->{'type'} eq 'link') || ($field->{'link'} ne '')) {
			$out .= qq~<tr><td valign=top size=200>$field->{'title'}:</td><td valign=top size=100>~;
			if ($field->{'link'} ne '') { $out .= qq~<a href="$field->{'link'}">Click Here~; }
			if ($field->{'note'} ne '') { $out .= qq~ * $field->{'note'}~; }
			$out .= "</td></tr>";
			}
		elsif ($field->{'type'} eq 'hidden') {
			## just sets a field the way we want it.
			}
		elsif ($field->{'type'} eq 'button') {
			$out .= qq~<tr bgcolor="#ffffff"><td><input type='button' class='minibutton' value='$field->{'title'}' onClick=" \$('#_NEXTVERB').val('$field->{'verb'}'); \$('#thisFrm').showLoading().submit();"></td></tr>~;
			}
		else {
			push @MSGS, "ISE|UNKNOWN FIELD TYPE: ".Dumper($field);
			}

		## add hint
		if ($field->{'hint'} ne '') {
			$out .= qq~<tr bgcolor="#ffffff"><td valign=top colspan=2><div class="hint">$field->{'hint'}</div></td></tr>~;
			}

		my $tab = $field->{'tab'};
		if ($tab eq 'GENERAL') {}
		elsif ($tab eq 'PRODUCT') {}
		elsif ($tab eq 'SHIPPING') {}
		elsif ($tab eq 'INVENTORY') {}
		elsif ($tab eq 'ORDER') {}
		elsif ($tab eq 'TRACK') {}
		else { push @MSGS, "ISE|Internal unknown tab[$tab] for field: ".Dumper($field); }

		$GTOOLS::TAG{"<!-- $tab\_FIELDS -->"} .= "$out\n";
		}

#	push @MSGS, "SUCCESS|".Dumper(\%GTOOLS::TAG);	

	## Build LINKS
	$template_file = 'edit.shtml';
	}



## Disassociate product from SUPPLIER
## (this doesn't remove product from Zoovy Store)
if ($VERB eq 'DISASSOCIATE') {
	my @prods = ();
	foreach my $var (keys %{$ZOOVY::cgiv}){
		next unless ($var =~ /^SKU_/);
		push @prods, $ZOOVY::cgiv->{$var};
		}

	if (scalar(@prods) > 0) {
		SUPPLIER::disassociate_products($USERNAME, $ZOOVY::cgiv->{'CODE'}, \@prods);
		}

	$VERB = 'PRODUCTS';	
	}


##
##
##
if ($VERB eq 'PRODUCTS') {

	my ($sup_to_prodref,$prod_to_supref) = $S->fetch_supplier_products();
	my @skus = (sort keys %{$prod_to_supref});
	my $c = '';

	my $PAGE = int($ZOOVY::cgiv->{'PAGE'});	## current page we are on, starts at zero.
	my $PAGESIZE = 500;
	my $PAGES = int(scalar(@skus)/$PAGESIZE);
	$GTOOLS::TAG{'<!-- PAGES -->'} = $PAGES;	
	$GTOOLS::TAG{'<!-- PAGE -->'} = $PAGE+1;
	
	if ($PAGE+1>1) {
		$GTOOLS::TAG{'<!-- NAVIGATION -->'} .= qq~&nbsp; <a href="/biz/manage/suppliers/?VERB=PRODUCTS&CODE=$CODE&PAGE=~.($PAGE-1).qq~">&lt;&lt; Last</a>~;
		}
	if ($PAGE<$PAGES) {
		$GTOOLS::TAG{'<!-- NAVIGATION -->'} .= qq~&nbsp; <a href="/biz/manage/suppliers/?VERB=PRODUCTS&CODE=$CODE&PAGE=~.($PAGE+1).qq~">Next &gt;&gt;</a> ~;
		}

	@skus = splice(@skus, $PAGE*$PAGESIZE, $PAGESIZE);

	if (scalar(@skus) > 1000) {
		$c .= "<tr><td valign=top colspan=10>Sorry, you have more than 500 SKUs (you have: ".scalar(@skus)."), cannot display</td></tr>";	
		}
	else {
		my $jedi_username = lc($S->fetch_property('.jedi.username'));
		my ($invref) = &INVENTORY::fetch_qty($USERNAME,\@skus);

		my $count = 0;
		my $prodsref = &PRODUCT::group_into_hashref($USERNAME,\@skus);
	
		foreach my $sku (sort (@skus)) {
			my $class = ($count++%2)?'r0':'r1';
			my ($pid) = PRODUCT::stid_to_pid($sku);
			my ($P) = $prodsref->{$pid};
			if (not defined $P) {
				## is this ever actually run/necesary?
				push @MSGS, "ERROR|PID:$pid could not be loaded from database";
				next;
				}

			## VERB CHECKBOX
			$c .= qq~<tr class="$class">~;
			$c .= qq~<td valign=top nowrap><input type="checkbox" name="SKU_$count" value="$pid"></td>~;

			## COUNT
			$c .= qq~<td>$count</td>~;
			
			## SKU
			$c .= qq~<td valign=top nowrap><a href="navigateTo('#:products?product=$pid');">$pid</a></td>~;

			$c .= "<td>$prod_to_supref->{$pid}</td>"; 				
			my $inv_enable = $P->fetch('zoovy:inv_enable');
	
			## INVENTORY
			## check if Unlimited
			if (($inv_enable & 32) > 0) { $c .= "<td>Unlimited</td>"; }
			else { 
				## check the sku level
				if ($invref->{$pid} eq ''){
					## I HAVE NO IDEA WHY/WHAT THIS CODE IS SUPPOSED TO DO. IT DOESN'T LOOK LIKE IT HANDLES
					## OPTIONS CORRECTLY ANYWAY.
					$c .= "<td>";
					$c .= "</td>";
					}
				## inv at the product level
				else {
					$c .= "<td>$invref->{$pid}</td>";
					}
				}
			
			## PRODUCT NAME
			$c .= "<td>".$P->fetch('zoovy:prod_name')."</td>";
			
			## SHIPPING
			if (defined $P->fetch('zoovy:ship_cost1') && $P->fetch('zoovy:ship_cost1') > 0) {
				$c .= "<td>\$".sprintf("%.2f",$P->fetch('zoovy:ship_cost1'))."</td>";
				}
			else { $c .= "<td>TBD</td>"; }

			## COST, PRICE
			foreach my $k ('zoovy:base_cost','zoovy:base_price') {
				$c .= "<td>\$".sprintf("%.2f",$P->fetch($k))."</td>";
				}
			$c .= "</tr>";
			}
		}

	if ($c eq '') {
		$c .= "<tr><td valign=top colspan='5'>No products found - please add some</td></tr>";
		}
	$GTOOLS::TAG{'<!-- PRODUCTS -->'} = $c;

	$template_file = 'products.shtml';
	push @BC, { name=>"Products" };

	}


##
##
## Allow merchant to confirm, redispatch, receive orders
##
##
if ($VERB eq 'ORDER-UPDATE') {

	my $results = '';
	my %oid_info = ();
	foreach my $var (keys %{$ZOOVY::cgiv}){
		if ($var =~ /^(.*)_ID$/) {
			my($orderid,$id) = split(/:/,$1);
			$oid_info{$id} = $orderid;
			}
		}
	my @OIDS = keys %oid_info;	
	my $MID = ZOOVY::resolve_mid($USERNAME);

	my $ACTION = uc($ZOOVY::cgiv->{'update'});
	if ($ACTION eq 'CONFIRM') {
		if ($ZOOVY::cgiv->{'name'} eq '' || $ZOOVY::cgiv->{'email'} eq '') {
			push @MSGS, "ERROR|Both name and email are required when confirming orders from this screen.";
			}
		elsif (not ZTOOLKIT::validate_email($ZOOVY::cgiv->{'email'})) {
			push @MSGS, "ERROR|Email is invalid";
			}
		$ACTION = '';	
		}
	elsif ($ACTION eq '') {
		push @MSGS, "ERROR|An action must be specified";
		}

	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
	foreach my $ID (@OIDS) {
		$ID = int($ID);

		if ($ACTION eq '') {
			}
		elsif ($ACTION eq 'APPROVE') {
			## only orders which are hold
			my $pstmt = "update VENDOR_ORDERS set STATUS='OPEN' where STATUS='HOLD' and MID=$MID /* $USERNAME */ and ID=$ID /* $oid_info{$ID} */";
			print STDERR $pstmt."\n";
			$LU->log('SUPPLIER.ORDERS.APPROVE',"[ORDER: $oid_info{$ID}] was approved",'INFO');

			my ($rv) = $udbh->do($pstmt);
			if ($rv==1) {
				push @MSGS, "SUCCESS|APPROVED ORDER: $oid_info{$ID}";
				}
			else {
				push @MSGS, "ERROR|APPROVE FAILURE ON ORDER: $oid_info{$ID}";
				}
			}
		elsif ($ACTION eq 'CLOSE') {
			## only orders which are open 
			## NOTE: this may fail because it happens automatically.
			my $pstmt = "update VENDOR_ORDERS set STATUS='CLOSE' where STATUS in ('OPEN','HOLD') and MID=$MID /* $USERNAME */ and ID=$ID /* $oid_info{$ID} */";
			print STDERR $pstmt."\n";
			my ($rv) = $udbh->do($pstmt);
			if ($rv==1) {
				push @MSGS, "SUCCESS|CLOSED ORDER: $oid_info{$ID}";
				}
			else {
				push @MSGS, "ERROR|CLOSE FAILURE ON ORDER: $oid_info{$ID}";
				}
			}	
		elsif ($ACTION eq 'RECEIVE') {
			#my $pstmt = "update VENDOR_ORDERS set RECEIVED_TS=now(),STATUS='RECEIVED' where ID=$ID and MID=$MID";
			#print STDERR $pstmt."\n";
			#my $results = $udbh->do($pstmt);
			#$pstmt = "select OUR_ORDERID from SUPPLIER_ORDERS where ID=".$udbh->quote($ID);
			#my $sth = $udbh->prepare($pstmt);
			#$sth->execute();
			#my ($orderid) = $sth->fetchrow();
			#$sth->finish;

			my $pstmt = "update VENDOR_ORDERITEMS VOI,VENDOR_ORDERS set 
				VO.RECEIVED_TS=now(),VO.STATUS='RECEIVED',VOI.STATUS='RECEIVED' 
				where VO.MID=$MID and VOI.MID=$MID and VOI.VENDOR_ORDER_DBID=VO.ID and VO.ID=$ID";
			$udbh->do($pstmt);
			push @MSGS, "SUCCESS|RECEIVED ORDER $oid_info{$ID}";
			}
		elsif ($ACTION eq 'ARCHIVE') {
			my $pstmt = "update VENDOR_ORDERS set ARCHIVED_TS=now() where ID=$ID and MID=$MID";
			$udbh->do($pstmt);
			push @MSGS, "SUCCESS|Archived $oid_info{$ID}";
			}
		elsif ($ACTION eq 'REDISPATCH') {
			my $pstmt = "update VENDOR_ORDERS set DISPATCHED_TS=0,STATUS='CLOSED',LOCK_PID=0 where ID=$ID and MID=$MID";
			my $results = $udbh->do($pstmt);
			$LU->log('SUPPLIER.ORDERS.REDISPATCH',"[ORDER: $oid_info{$ID}] was redispatched",'INFO');
			push @MSGS, "SUCCESS|Redispatched $oid_info{$ID}";
			}
		elsif ($ACTION eq 'CONFIRM') {
			$LU->log('SUPPLIER.ORDERS.CONFIRM',"[ORDER: $oid_info{$ID}] was confirmed",'INFO');
			my (@errors) = SUPPLIER::confirm_order($USERNAME,$oid_info{$ID},'NA','','','',$ZOOVY::cgiv->{'name'},$ZOOVY::cgiv->{'email'});
			foreach my $error (@errors) {
				push @MSGS, "ERROR|$error";
				}
			}	
		else {
			push @MSGS, "ERROR|Unknown Action:$ACTION";
			}
		}

	&DBINFO::db_user_close();
	$VERB = 'ORDERS';	
	if ($CODE eq '') { $VERB = "NON_CONF_ORDERS"; }
	}
	



##
## individual STOCK ORDER display
##
if ($VERB eq 'STOCK_ORDER') {
	$template_file = 'stock_order.shtml';
	push @BC, { name=>"Stock Orders",link=>"/biz/utilities/suppliers/index.cgi?VERB=ORDERS&CODE=$CODE" };

#	my $itemref = SUPPLIER::STOCK::order_detail($S->fetch_property('MID'), $ZOOVY::cgiv->{'ID'});
	my ($ID) = $ZOOVY::cgiv->{'ID'};
	my $pstmt = "select VOI.SKU,VOI.description,VOI.qty,VOI.cost,VOI.CREATED_TS from VENDOR_ORDERS VO,VENDOR_ORDERITEMS VOI ".
			 		" where VOI.VENDOR_ORDER_DBID=VO.ID and VO.ID=".$udbh->quote($ID). " and VO.mid=$MID and VOI.MID=VO.MID ".
			 		" order by VOI.CREATED_TS,VOI.SKU";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();

	my @ITEMS = ();
	while( my ($sku,$desc,$qty,$cost,$added) = $sth->fetchrow()) {
		push @ITEMS, { sku=>$sku, desc=>$desc, qty=>$qty, cost=>$cost, added=>$added };
		}
	$sth->finish();
	my $itemref = \@ITEMS;
	
	use Data::Dumper;

	my $c = '';
	my $total = 0;
	foreach my $item (@{$itemref}) {
		print STDERR Dumper ($item);
		$total += ($item->{'cost'}*$item->{'qty'});
		$c .= "<tr><td>$item->{'added'}</td><td>$item->{'sku'}</td><td>$item->{'desc'}</td><td>$item->{'qty'}</td><td>".
				'$'.sprintf("%.2f",($item->{'cost'}*$item->{'qty'}))."</td></tr>";
		}
	
	$c .= "<tr><td valign=top colspan=4 halign=right><b>TOTAL:</b></td><td>".'$'.sprintf("%.2f",($total))."</td></tr>";

	$GTOOLS::TAG{'<!-- ORDER_ID -->'} = $ZOOVY::cgiv->{'ID'};		
	$GTOOLS::TAG{'<!-- ORDER_ITEMS -->'} = $c;		
	}
	
##
## Non-Confirmed Orders tab for all Suppliers
## 
if ($VERB eq 'NON_CONF_ORDERS') {

	my $c = '';
	my $count = 0;
	
	my $pstmt = "select * from VENDOR_ORDERS where MID=$MID and status != 'CORRUPT' and status != 'ERROR' ".
					" and CONF_GMT = '' order by OUR_ORDERID desc limit 300";
	print STDERR $pstmt."\n";

	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my %H = ();
	## make srcorder the key to sort on
	my $r = '';
	while ( my $orderref = $sth->fetchrow_hashref() ) {
		next if ($orderref->{'OUR_ORDERID'} eq '');
		my ($O2) = CART2->new_from_oid($USERNAME,$orderref->{'OUR_ORDERID'});
		#my ($O) = ORDER->new($USERNAME,$orderref->{'OUR_ORDERID'});
		my $r = ($r eq 'r0')?'r1':'r0';

		#my ($SRCOID,$SUPPLIEROID,$STATUS,$CREATED_GMT,$DISPATCHED_GMT,undef,undef,undef,$CODE) = split(/\|/,$orderref);
		my $CREATED_TS = $orderref->{'CREATED_TS'};
		my $DISPATCHED_TS = $orderref->{'DISPATCHED_TS'};
		
		my $VERBS = '';
		$c .= qq~<tr class="$r">~;
		
		if ($orderref->{'FORMAT'} ne 'JEDI') {
			$c .= qq~<td><input type="checkbox" name="$orderref->{'OUR_ORDERID'}:$orderref->{'ID'}_ID"></td>~; 
			}
		else { $c .= "<td></td>"; }
		
		$c .= qq~<td><a href="?VERB=ORDERS&CODE=$orderref->{'SUPPLIERCODE'}">$orderref->{'SUPPLIERCODE'}</a></td>~;

		if ($orderref->{'FORMAT'} ne 'STOCK') {
			$c .= qq~<td><a target=_new href="https://www.zoovy.com/biz/orders/view.cgi?ID=$orderref->{'OUR_ORDERID'}">$orderref->{'OUR_ORDERID'}</a></td>~;
			}
		else {
			$c .= qq~<td><a target=_new href="?VERB=STOCK_ORDER&CODE=$orderref->{'SUPPLIERCODE'}&ID=$orderref->{'ID'}">$orderref->{'ID'}</a> </td> ~;
			}

		if (defined $O2) { $c .= "<td>".$O2->in_get('flow/pool')."</td>"; }
		else { $c .= "<td>DELETED</td>"; }
		
		$c .= qq~ 
	<td>$CREATED_TS</td>
	<td>$DISPATCHED_TS</td>
	<td>$orderref->{'DISPATCHED_COUNT'}</td>
	<td><a target="_new" href="http://$USERNAME.zoovy.com/confirm.cgis?reference=$orderref->{'OUR_ORDERID'}">Never</a></td></tr>~;
		}
	$sth->finish();	
	&DBINFO::db_user_close();

	if ($c eq '') {
		$c = "<tr class='table_bg2'><td valign=top colspan='7'><i>No non-confirmed orders found.</td></tr>";
		}

	$GTOOLS::TAG{'<!-- ORDERS -->'} = $c;

	$template_file = 'non_conf_orders.shtml';
	push @BC, { name=>"Non-Confirmed Orders" };
	}

	

##
## Orders tab for a particular Supplier
## 
if ($VERB eq 'ORDERS') {
 	if ($S->fetch_property('FORMAT') eq 'STOCK') {
		$VERB = 'STOCK_ORDERS';
		}
	}

if ($VERB eq 'ORDERS') {
	my $c = '';
	$template_file = 'orders.shtml';


	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
 	my $MID = &ZOOVY::resolve_mid($USERNAME);
	my $qtVENDORID = $udbh->quote($S->id());
	my @SOIDS = ();
	my ($needs_approve) = (0);

	## 
	my $pstmt = "select SKU,QTY,STATUS,OUR_ORDERID,CREATED_TS,OUR_VENDOR_DBID,ID from VENDOR_ORDERITEMS where MID=$MID and VENDOR=$qtVENDORID order by ID ";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ROWS = ();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		#print STDERR $srcoid."|".$sku."|".$qty."|". $stat."|".$srcoid."|".$cts."\n";
		push @ROWS, $hashref;
		}
	$sth->finish();	

	my $pstmt = "select * from VENDOR_ORDERS where MID=$MID and VENDOR=$qtVENDORID and ARCHIVED_TS=0 order by ID desc limit 0,300";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ORDERS = ();
	## make srcorder the key to sort on
	while ( my $orderref = $sth->fetchrow_hashref() ) {
		#$H{$orderref->{'ORDERID'}.$orderref->{'SUPPLIERCODE'}} = $orderref;
		push @ORDERS, $orderref;
		push @SOIDS, $orderref->{'OUR_ORDERID'};
		if ($orderref->{'STATUS'} eq 'HOLD') { $needs_approve++; }
		}
	$sth->finish();	

	##	
	## BUILD ITEMS TO BE ORDERED	
	##
	my $count = 0;
	foreach my $row (@ROWS) {
		my $class = ($count++%2)?'r0':'r1';

		# next unless (($row->{'STATUS'} eq 'NEW') || ($row->{'STATUS'} eq 'ADDED')); 
		next unless (($row->{'STATUS'} eq 'NEW'));
		my $VERBS = '';
		$c .= qq~<tr class="$class">~;
		$c .= qq~<td></td>~;
		$c .= qq~<td><a target=_new href="https://www.zoovy.com/biz/orders/view.cgi?ID=$row->{'OUR_ORDERID'}">$row->{'OUR_ORDERID'}</a></td>~;
		$c .= qq~<td>$row->{'SKU'}</td>~;
		$c .= qq~<td>$row->{'QTY'}</td>~;
		$c .= qq~<td></td>~;
		$c .= qq~<td>$row->{'STATUS'}</td>~;
		$c .= sprintf("<td>%s</td>",$row->{'CREATED_TS'});
		$c .= qq~</tr>~;
		}

	if ($c eq '') { $c = "<tr class='table_bg2'><td valign=top colspan='7'><i>No New order items found for this supplier</td></tr>"; }
	$GTOOLS::TAG{'<!-- ORDERITEMS -->'} = $c;


	## JEDI orders aren't "redispatchable"
	$GTOOLS::TAG{'<!-- VERBS -->'} .= qq~<option value="CLOSE">Close</option>~;
	$GTOOLS::TAG{'<!-- VERBS -->'} .= qq~<option value="ARCHIVE">Archive</option>~;
	#if ($S->fetch_property('MODE') ne 'JEDI') {
	#	$GTOOLS::TAG{'<!-- VERBS -->'} .= qq~<option value="REDISPATCH">Redispatch</option>~;
	#	}

	## okay now we should lookup pool from the database.
	# my $sorefs = $S->list_orders(LIMIT=>300);



	require ORDER::BATCH;
	if ($needs_approve) {
		$GTOOLS::TAG{'<!-- VERBS -->'} .= qq~<option value="APPROVE">Approve Hold Orders</option>~;
		}

	my ($orefs) = ORDER::BATCH::report($USERNAME,'@OIDS'=>\@SOIDS,DETAIL=>3);
	## %somap is a hashref keyed by orderid with value being a ref to order properties.
	my %ordermap = ();
	foreach my $ref (@{$orefs}) { $ordermap{ $ref->{'ORDERID'} } = $ref; }

	&DBINFO::db_user_close();

	##
	## Build ORDERS table
	## 
	$c = '';
	my $nowts = time();

	## reverse sort
	foreach my $line (@ORDERS) {
		# my ($O) = ORDER->new($USERNAME,$sorefs->{$id}->{'OUR_ORDERID'});
		my $pool = $ordermap{ $line->{'OUR_ORDERID'} }->{'POOL'};
		my $class = ($count++%2)?'r0':'r1';
		my $CONFIRMED_GMT = &ZTOOLKIT::pretty_date($line->{'CONF_GMT'});


		$c .= qq~<tr class="$class">~;
		$c .= qq~<td><input type="checkbox" name="$line->{'OUR_ORDERID'}:$line->{'ID'}_ID"></td>~;

		## Store order
		$c .= qq~<td valign=top nowrap><a target=_new href="https://www.zoovy.com/biz/orders/view.cgi?ID=$line->{'OUR_ORDERID'}">$line->{'OUR_ORDERID'}</a> ~;
		if ($pool ne '') { $c .= "($pool)"; }

		# $c .= Dumper( $somap{ $line->{'OUR_ORDERID'} }->{'POOL'} );
		# if (defined $O) { $c .= "(".$O->get_attrib('pool').")"; } 
		
		$c .= qq~</td>~;
			
		## JEDI ORDER
		#if ($S->fetch_property('MODE') eq 'JEDI') {
		#	$c .= qq~<td><a target=_new href="https://ssl.zoovy.com/$S->fetch_property('.jedi.username')/order_status.cgis?order_id=$line->{'VENDOR_REFID'}">$line->{'VENDOR_REFID'}</a></td>~;
		#	}
		if (defined $line->{'VENDOR_REFID'}) {
			$c .= qq~<td>$line->{'VENDOR_REFID'}</td>~; 
			}
		else { 
			$c .= qq~<td>ERR-SOREF: $line->{'ID'}</td>~; 
			}
		
		my $confirmed = $CONFIRMED_GMT . qq~ <a href="mailto:$line->{'CONF_EMAIL'}">~ . 
			($line->{'CONF_PERSON'} eq ''?$line->{'CONF_EMAIL'}:$line->{'CONF_PERSON'})."</a>";
			
		if (($line->{'STATUS'} eq 'OPEN') && ($line->{'WAIT_GMT'}<=$nowts)) {
			$c .= qq~<td>OPEN (will be closed)</td>~;
			}
		else {
			$c .= qq~<td>$line->{'STATUS'}</td>~;
			}
			
		$c .= qq~
			<td>$line->{'CREATED_TS'}</td>
			<td>$line->{'DISPATCHED_TS'}</td>
			<td>$confirmed</td></tr>~;
		}

	if ($c eq '') { $c = "<tr class='table_bg2'><td valign=top colspan='7'><i>No orders found for this supplier</td></tr>"; }

	$GTOOLS::TAG{'<!-- ORDERS -->'} = $c;
		
	$template_file = 'orders.shtml';
  	push @BC, { name=>"Orders" };
	}





##
##
##
if ($VERB eq 'STOCK_ORDERS') {

	my $c = '';
	$template_file = 'stock-orders.shtml';

	## make srcorder the key to sort on

	# my $rows = $S->list_orderitems();
	my ($udbh) = &DBINFO::db_user_connect($USERNAME);
 	my $MID = &ZOOVY::resolve_mid($USERNAME);
	my $qtVENDORID = $udbh->quote($S->id());

	## 
	my $pstmt = "select SKU,QTY,STATUS,OUR_ORDERID,CREATED_TS,OUR_VENDOR_DBID,ID from VENDOR_ORDERITEMS where MID=$MID and VENDOR=$qtVENDORID order by ID ";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ROWS = ();
	while ( my $hashref = $sth->fetchrow_hashref() ) {
		#print STDERR $srcoid."|".$sku."|".$qty."|". $stat."|".$srcoid."|".$cts."\n";
		push @ROWS, $hashref;
		}
	$sth->finish();	

	$pstmt = "select * from VENDOR_ORDERS where MID=$MID and VENDOR=$qtVENDORID and ARCHIVED_TS=0 order by ID desc limit 0,100";
	print STDERR $pstmt."\n";
	$sth = $udbh->prepare($pstmt);
	$sth->execute();
	my @ORDERS = ();
	## make srcorder the key to sort on
	while ( my $line = $sth->fetchrow_hashref() ) {
		push @ORDERS, $line;
		}
	$sth->finish();	
	&DBINFO::db_user_close();

	##
	## BUILD ITEMS TO BE ORDERED
	##
	my $count = 0;
	my $stock_new_count = 0;
	foreach my $row (@ROWS) {
		my $class = ($count++%2)?'r0':'r1';
		next unless ($row->{'STATUS'} eq 'NEW' || $row->{'STATUS'} eq 'ADDED'); 

		my $ID = $row->{'ID'};
		my $cost = 0;
		$c .= qq~<tr class="$class">~;
		if ($row->{'STATUS'} eq 'NEW') {
			$c .= qq~<td><input type="checkbox" name="${ID}_DISPATCH">Order?</td>~;
			}
		else {
			$c .= qq~<td></td>~;
			}

		$c .= qq~<td>STOCK</td>~;
		$c .= qq~<td>$row->{'SKU'}</td>~;
		
		if ($row->{'STATUS'} eq 'NEW') {
			$c .= qq~<td><input type="textbox" size="4" name="${ID}_QTY" value="$row->{'QTY'}"></td>~;
			}
		else {
			$c .= qq~<td>$row->{'QTY'}</td>~;
			}
	
		$c .= qq~<td>$cost</td>~;
		$c .= qq~<td>$row->{'STATUS'}</td>~;
		$c .= sprintf("<td>%s</td>",$row->{'CREATED_TS'});
		$c .= qq~</tr>~;
		}


	if ($c eq '') {
		$c = "<tr class='table_bg2'><td valign=top colspan='7'><i>No New order items found for this supplier</td></tr>";
		}
	
	## add UPDATE button
	elsif ($c ne '' && $stock_new_count>0) {
		$c .= qq~<tr><td valign=top colspan=6 align=center><input type="submit" src="/images/bizbuttons/update.gif" value="Update">
				</td></tr>~;
		}

	$GTOOLS::TAG{'<!-- ORDERITEMS -->'} = $c;

	

	use Data::Dumper;
	#print STDERR Dumper($sorefs);

	##
	## Build ORDERS table
	## 
	$c = '';
	foreach my $line (@ORDERS) {
		my $class = ($count++%2)?'r0':'r1';
		my $CONFIRMED_GMT = &ZTOOLKIT::pretty_date($line->{'CONF_GMT'});
	
		my $TOTAL_COST = $line->{'TOTAL_COST'};;

		#if (int($TOTAL_COST) == 0) {
		#	$TOTAL_COST = SUPPLIER::STOCK::order_item_total($S->fetch_property('MID'),VENDOR_REFID=>$line->{'ID'});
		#	}

		$c .= qq~<tr class="$class">~;
		## VERB
		$c .= qq~<td><input type="checkbox" name="$line->{'OUR_ORDERID'}:$line->{'ID'}_ID"></td>~;
		## Zoovy Order ID
		$c .= qq~<td><a target=_new href="?VERB=STOCK_ORDER&CODE=$CODE&ID=~.$line->{'ID'}.
				qq~">$line->{'ID'}</a> </td> ~;
		## Supplier Order ID
		$c .= qq~<td>$line->{'VENDOR_REFID'}</td>~; 
		## Total Cost
		$c .= qq~<td>\$~.sprintf("%.2f",$TOTAL_COST).qq~</td>~;
		
		## Status, Created, Dispatched, Confirmed
		my $confirmed = $CONFIRMED_GMT . qq~ <a href="mailto:$line->{'CONF_EMAIL'}">~ . 
			($line->{'CONF_PERSON'} eq ''?$line->{'CONF_EMAIL'}:$line->{'CONF_PERSON'})."</a>";
		$c .= qq~<td>$line->{'STATUS'}</td>~;
		$c .= sprintf("<td>%s</td>",$line->{'CREATED_TS'});
		$c .= sprintf("<td>%s</td>",$line->{'DISPATCHED_TS'});
		$c .= sprintf("<td>$confirmed</td>");
		$c .= sprintf("<td>%s</td>",$line->{'RECEIVED_TS'});
		}

	if ($c eq '') {
		$c = "<tr class='table_bg2'><td valign=top colspan='7'><i>No orders found for this supplier</td></tr>";
		}

	$GTOOLS::TAG{'<!-- ORDERS -->'} = $c;
	$GTOOLS::TAG{'<!-- VERBS -->'} = qq~Action: <select name="update">
				<option value="">-</option>
				<option value="CLOSE">Close</option>
				<option value="RECEIVE">Receive Order</option>
				<option value="REDISPATCH">Redispatch</option>
				</select><input type="submit" class="button" value="Go">~;

	push @BC, { name=>"Orders" };
	}





##
##
if ($VERB eq 'SAVE-GENERIC-SHIPPING') {
	# deal with SHIPPING METHOD checkboxes
	# add up all the values for bitwise comparison
	my $total_shipping_method = ($ZOOVY::cgiv->{'.ship.methods_1'}?1:0) + 
		($ZOOVY::cgiv->{'.ship.methods_2'}?2:0) + 
		($ZOOVY::cgiv->{'.ship.methods_4'}?4:0) + 
		($ZOOVY::cgiv->{'.ship.methods_32'}?32:0);

	## setting 4 (API shipping) is predatory and cannot be enabled with others.
	if ($total_shipping_method&4) { $total_shipping_method = 4; }

	if (defined $ZOOVY::cgiv->{'.ship.methods_0'}) {	
		$total_shipping_method = 0;
		}

	# deal with SHIPPING OPTIONS checkboxes
	# add up all the values for bitwise comparison
	my $total_shipping_options = ($ZOOVY::cgiv->{'.ship.options_1'}?1:0); 

	$S->save_property('USERNAME',$USERNAME);
	$S->save_property('.ship.methods',$total_shipping_method);
	$S->save_property('.ship.origzip', $ZOOVY::cgiv->{'.ship.origzip'});
	$S->save_property('.ship.origstate', $ZOOVY::cgiv->{'.ship.origstate'});
	$S->save_property('.ship.provider', $ZOOVY::cgiv->{'.ship.provider'});
	$S->save_property('.ship.account', $ZOOVY::cgiv->{'.ship.account'});
	$S->save_property('.ship.options', $total_shipping_options);
	$S->save_property('.ship.hnd.perorder', $ZOOVY::cgiv->{'.ship.hnd.perorder'});
	$S->save_property('.ship.hnd.peritem', $ZOOVY::cgiv->{'.ship.hnd.peritem'});
	$S->save_property('.ship.hnd.perunititem', $ZOOVY::cgiv->{'.ship.hnd.perunititem'});
	$S->save();
	
	push @MSGS, "SUCCESS|Successfully edited shipping for $CODE";
	$LU->log('SUPPLIER.SHIPPING.SAVE',"[CODE: $CODE] shipping settings were updated.",'INFO');
	$VERB = 'GENERIC-SHIPPING';
	}

if ($VERB eq 'GENERIC-SHIPPING') {
		# bitwise compare
		$GTOOLS::TAG{'<!-- .ship.methods_0 -->'} = ($S->fetch_property('.ship.methods')==0)?"checked":"";
		$GTOOLS::TAG{'<!-- .ship.methods_1 -->'} = ($S->fetch_property('.ship.methods') & 1)?"checked":"";
		$GTOOLS::TAG{'<!-- .ship.methods_2 -->'} = ($S->fetch_property('.ship.methods') & 2)?"checked":"";
		$GTOOLS::TAG{'<!-- .ship.methods_4 -->'} = ($S->fetch_property('.ship.methods') & 4)?"checked":"";
		$GTOOLS::TAG{'<!-- .ship.methods_32 -->'} = ($S->fetch_property('.ship.methods') & 32)?"checked":"";


		## Origin Zip Code, State, Provider, Account
		$GTOOLS::TAG{'<!-- .ship.origzip -->'} = $S->fetch_property('.ship.origzip');
		$GTOOLS::TAG{'<!-- .ship.origstate -->'} = $S->fetch_property('.ship.origstate');	
	
		## Configure veribiage for Shipping Meter
		my $params = &ZTOOLKIT::parseparams($S->fetch_property('.ship.meter'));
		if($params->{'type'} eq "UPS"){
			$GTOOLS::TAG{'<!-- .ship.meter -->'} = $params->{'type'} ." Shipper #: ". $params->{'shipper_number'}. "<br>License: ". $params->{'license'};
			}	
		elsif($params->{'type'} eq "FEDEX"){
			$GTOOLS::TAG{'<!-- .ship.meter -->'} = $params->{'type'} ." Account #: ". $params->{'account_number'}. "<br>Meter: ". $params->{'meter'};
			}	
		else{ $GTOOLS::TAG{'<!-- .ship.meter -->'} = "None confirmed at this time..."; }
		##

		my ($webdb) = &ZWEBSITE::fetch_website_dbref($USERNAME);
		if ($webdb->{'google_api_env'}==0) {}
		elsif ($webdb->{'google_dest_zip'} eq '00000') {
			push @MSGS, "WARN|your google checkout settings are incompatible with zone based shipping.";
			}

		$GTOOLS::TAG{'<!-- .ship.options_1 -->'} = ($S->fetch_property('.ship.options') & 1)?"checked":"";
		$GTOOLS::TAG{'<!-- .ship.hnd.perorder -->'} = $S->fetch_property('.ship.hnd.perorder');
		$GTOOLS::TAG{'<!-- .ship.hnd.peritem -->'} = $S->fetch_property('.ship.hnd.peritem');
		$GTOOLS::TAG{'<!-- .ship.hnd.perunititem -->'} = $S->fetch_property('.ship.hnd.perunititem');

	$template_file = 'generic-shipping.shtml';
	push @BC, { name=>"Generic Shipping" };
	}





##
##
##
#if ($VERB eq 'INVENTORY') {
##
#	my $rows = $S->fetch_inventory();
#	
#	my $c = '';
#	my $r = '';
#	foreach my $row (@{$rows}) {
#		$r = ($r eq 'r0')?'r1':'r0';
#		## SKU
#
#		$c .= "<tr class='$r'>";
#		$c .= qq~<a target="_new" href="http://www.zoovy.com/biz/product/index.cgi?VERB=QUICKSEARCH&VALUE=$pid">[Edit]</a></td>~;
#		$c .= "<td>$pid</td>";
#		$c .= "<td>".$P->fetch('zoovy:prod_name')."</td>";
#		$c .= "<td>".$P->fetch('zoovy:base_price')."</td>";
#		$c .= "</tr>";
#		my ($P) = PRODUCT->new($USERNAME,$pid);
#		foreach my $set (@{$P->list_skus()}) {
#			my ($sku,$skuref) = @{$set};
#			$c .= "<tr class='$r'>";
#			$c .= "<td></td>";
#			$c .= "<td>$sku</td>";
#			$c .= "<td>$skuref->{'zoovy:prod_name'}</td>";
#			$c .= "<td>$skuref->{'zoovy:base_price'}</td>";
#			$c .= "</tr>";
#			}
#
#		}
#
#	if ($c eq '') {
#		$c .= "<tr><td valign=top colspan='5'>No inventory found - please add some</td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- INVENTORY -->'} = $c;
#
#	$template_file = 'inventory.shtml';
#	push @BC, { name=>"Inventory" };
#	}





##
##
##



if ($VERB eq 'PRODUCT-ADD-SAVE')  {
	my $SKU = $ZOOVY::cgiv->{'sku'};

	## get current product information
	my ($P) = PRODUCT->new($USERNAME,$SKU,'create'=>1);
	
	## if values are put in, use those otherwise you current properties
	$P->store('zoovy:prod_name', ($ZOOVY::cgiv->{'prod_name'} ne ''?$ZOOVY::cgiv->{'prod_name'}:$P->fetch('zoovy:prod_name')));
	$P->store('zoovy:base_cost', ($ZOOVY::cgiv->{'cost'} ne ''?$ZOOVY::cgiv->{'cost'}:$P->fetch('zoovy:base_cost')));

	$P->store('zoovy:ship_cost1', ($ZOOVY::cgiv->{'suppliership'} ne ''?$ZOOVY::cgiv->{'suppliership'}:$P->fetch('zoovy:ship_cost1')));
	$P->store('zoovy:base_weight', ($ZOOVY::cgiv->{'base_weight'} ne ''?$ZOOVY::cgiv->{'base_weight'}:$P->fetch('zoovy:base_weight')));
	$P->store('zoovy:prod_supplierid', ($ZOOVY::cgiv->{'suppliersku'} ne ''?$ZOOVY::cgiv->{'suppliersku'}:$P->fetch('zoovy:prod_supplierid')));
	$P->store('zoovy:prod_supplier', $CODE);
	$P->store('zoovy:virtual', "SUPPLIER:$CODE");
	
	$P->store('zoovy:inv_enable',1);
	if (defined $ZOOVY::cgiv->{'inv_unlimited'}) {
		$P->store('zoovy:inv_enable', 33);
		INVENTORY::add_incremental($USERNAME,$SKU,'I',9999);
		}

	## set price based on MARKUP
	if ($P->fetch('zoovy:base_price') eq '') {
		my $formula = $S->fetch_property('MARKUP');
		my $price = '';

		require Math::Symbolic;
		my $tree = Math::Symbolic->parse_from_string($formula);			
		if (defined $tree) {
			$tree->implement('COST'=> sprintf("%.2f",$P->fetch('zoovy:base_cost')) );
			$tree->implement('BASE'=> sprintf("%.2f",$P->fetch('zoovy:base_price')) );
			$tree->implement('SHIP'=> sprintf("%.2f",$P->fetch('zoovy:ship_cost1')) );
			$tree->implement('MSRP'=> sprintf("%.2f",$P->fetch('zoovy:prod_msrp')) );

			my ($sub) = Math::Symbolic::Compiler->compile_to_sub($tree);
			$price = sprintf("%.2f",$sub->());
			}
		$P->store('zoovy:base_price', $price);
		}
		
	$P->folder("/$CODE");	
	$P->save();

	push @MSGS, "SUCCESS|edited product $SKU";
	$LU->log('SUPPLIER.PRODUCT.MAP',"[CODE: $CODE] product $SKU was associated",'INFO');
	$VERB = 'PRODUCT-ADD';
	}


if ($VERB eq 'PRODUCT-ADD') {
	$template_file = 'product-add.shtml';	
	push @BC, { name=>"Add Product" };
	}












##
## 
##
if ($VERB eq '') {
	my $c = '';

	$template_file = 'index.shtml';	
	my ($supref) = SUPPLIER::list_suppliers($USERNAME);
	my $count = 0;

	my $r = '';
	foreach my $code (sort keys %{$supref}) {
		$r = ($r eq 'r0')?'r1':'r0';
		$c .= "<tr class=\"$r\">";
		$c .= qq~<td valign=top nowrap><button class='minibutton' onClick="navigateTo('/biz/manage/suppliers/index.cgi?VERB=EDIT&CODE=$code')">Config</button></td>~;
		$c .= qq~<td>$code</td>~;
		$c .= "<td valign=top nowrap>$supref->{$code}->{'FORMAT'}</td>";
		$c .= "<td valign=top nowrap>$supref->{$code}->{'NAME'}</td>";
		$c .= "<td valign=top nowrap>";
			$c .= qq~<input type='button' class='minibutton' value='Orders' onClick="navigateTo('/biz/manage/suppliers/index.cgi?VERB=ORDERS&CODE=$code');">~;
			$c .= qq~<input type='button' class='minibutton' value='Products' onClick="navigateTo('/biz/manage/suppliers/index.cgi?VERB=PRODUCTS&CODE=$code');">~;
#			$c .= qq~<input type='button' class='minibutton' value='Inventory' onClick="navigateTo('index.cgi?VERB=INVENTORY&CODE=$code');">~;
		$c .= "</td>";
#		$c .= "<td valign=top nowrap>$supref->{$code}->{'FORMAT'}</td>";
		$c .= "</tr>";
		}
	
	if ($c eq '') { $GTOOLS::TAG{'<!-- SUPPLIERS -->'} = '<tr class="r0"><td valign=top colspan="5"><i>No suppliers currently exist.</i></td>'; }
	else { $GTOOLS::TAG{'<!-- SUPPLIERS -->'} = "$c"; }

	push @BC, { name=>"Suppliers" };
	}




&GTOOLS::output(
	'file'=>$template_file,
	'title'=>$title,
	'header'=>1,
	'help'=>"#50694",
	'bc'=>\@BC,
	'tabs'=>\@TABS,
	'msgs'=>\@MSGS,
	'jquery'=>1,
	);

&DBINFO::db_user_close();





__DATA__


