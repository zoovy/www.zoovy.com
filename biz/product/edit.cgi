#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
require GTOOLS;
require ZOOVY;
require AJAX::PANELS;
require PRODUCT::PANELS;
require LUSER;
require ZWEBSITE;
require INVENTORY;
require PRODUCT;

my $html = '';
my @ERRORS = ();

require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_P&2');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my $template_file = 'edit.shtml';
my $VERB = $ZOOVY::cgiv->{'VERB'};
my $PID = $ZOOVY::cgiv->{'PID'};
if ($PID =~ /^(.*?):/) { $PID = $1; }
$PID =~ s/[^\w\-]+//gs;		# strip non compatible characters (e.g. space) from the product id
$PID = uc($PID);


my ($P) = PRODUCT->new($LU,$PID,'create'=>1);

my $CSS = '/biz/standard.css'; 
if ($FLAGS =~ /,MSUSER,/) {
	$CSS = '/biz/images/ms_header/ms_standard.css';
	}
$GTOOLS::TAG{'<!-- CSS -->'} = $CSS;

## SANITY: at this point $PID, $VERB, and $prodref are all initialized

# print STDERR "VERB: $VERB\n";

if (($VERB eq '') && ($PID eq '')) { $VERB = 'WELCOME'; }

if ($VERB =~ /CREATE/) {
	}
elsif ($VERB eq 'WELCOME') {
	my $gref = &ZWEBSITE::fetch_globalref($USERNAME);
	if ((defined $gref->{'%tuning'}->{'auto_product_cache'}) && 
		($gref->{'%tuning'}->{'auto_product_cache'}==0)) {
		print "Location: /biz/product/search.cgi\n\n";
		exit;
		}
	else {		
		$template_file = 'welcome.shtml';
		$VERB = '*';
		}
	}
elsif ($PID eq '') {
	$VERB = 'ERROR';
	$html = "<li>ERROR: Product ID was not passed.";
	}



## CREATE

my $product_id = uc($ZOOVY::cgiv->{"product"});
$product_id = substr($product_id, 0, 20);
$product_id = uc($product_id);
$product_id =~ s/^[^A-Z0-9]+//og; # strips anything which not a leading A-Z0-9



# if we clone a product we'll populate it if it not it'll be blank

#if (($FLAGS =~ /,MEDIA,/) && ($VERB eq 'CREATE-DOWNLOAD')) {
#	require CATALOGS;
#
#	my $catalog = $ZOOVY::cgiv->{'catalog'};
#	$GTOOLS::TAG{'<!-- CATALOG -->'} = $catalog;
#	
#	($product_id,my $prodref) = &CATALOGS::download($USERNAME,$ZOOVY::cgiv->{'CATALOG'},$ZOOVY::cgiv->{'ID'});
#	%PRODUCT = %{$prodref};
#	$PRODREF{'zoovy:catalog'} = $prodref->{'zoovy:catalog'};
#	$ZOOVY::cgiv->{'catalog'} = $prodref->{'zoovy:catalog'};
#	$ZOOVY::cgiv->{'prod_id'} = $product_id;
#	$VERB = '*';
#	}


#if (($FLAGS =~ /,MEDIA,/) && ($VERB eq 'CREATE-SEARCH_CATALOG')) {
#	my $catalog = $ZOOVY::cgiv->{'catalog'};
#	$GTOOLS::TAG{'<!-- CATALOG -->'} = $catalog;
#	
#	my $TEXT = $ZOOVY::cgiv->{'prod_id'};
#	$GTOOLS::TAG{'<!-- PROD_ID -->'} = $TEXT;
#	if ($ZOOVY::cgiv->{'TEXT'}) { $TEXT = $ZOOVY::cgiv->{'TEXT'}; }
#	
#	require CATALOGS;
#	my $PRODS = &CATALOGS::find_products($catalog,'SKU',$TEXT);
#
#	my $out = '';
#	foreach my $prod (@{$PRODS}) {
#		#$prod->{'attrib'}->{'sku|name'};
#		#$prod->{'content'}->[0]->{'content'};
#		$out .= "<tr><td bgcolor='CCCCCC'>&nbsp; [<a href=\"create.cgi?ACTION=DOWNLOAD&CATALOG=$catalog&ID=$prod->{'attrib'}->{'sku'}\">Download</a>] <b>$prod->{'attrib'}->{'name'}</b></td></tr>";
#		$out .= "<tr><td><br>$prod->{'content'}->[0]->{'content'}</td></tr>";
#		}
#		
#	if ($out eq '') {
#		$out = "<tr><td><i>Sorry no results found for <b>$TEXT</b> in catalog <b>".uc($catalog)."</b></i></td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- RESULTS -->'} = $out;
#	$template_file = 'create-catalog.shtml';
#	$VERB = '*';
#	}



##
## Create and Add to Website
## take the same path
##
my $error;
my %COPYREF = ();
if (($VERB eq "CREATE-SAVE") || ($VERB eq "CREATE-PROCEED")) {
	# step 0 - load and parse the clone buffer (if it exists) - remember
	# its already been dcoded by CGI.pm [shit]
	$error = 0;

	$COPYREF{"zoovy:prod_name"} = $ZOOVY::cgiv->{"prod_name"};
	$COPYREF{"zoovy:prod_desc"} = $ZOOVY::cgiv->{"prod_desc"};

	if (defined $ZOOVY::cgiv->{'catalog'}) {
		$COPYREF{'zoovy:catalog'} = $ZOOVY::cgiv->{'catalog'};
		}
	my $c = uc($ZOOVY::cgiv->{"prod_id"}); 
	$c =~ s/[^\w\-]+//g;
	$c =~ s/^[^A-Z0-9]+//og; # strips anything which not a leading A-Z0-9

	if ($c eq "") {
		# if a product id was not input then lets build one.
		$c = &ZOOVY::builduniqueproductid($USERNAME, $COPYREF{'zoovy:prod_name'});
		}	

	if (&ZOOVY::productidexists($USERNAME, $c)) {
		$error = 1;
		$GTOOLS::TAG{"<!-- ERROR_MSG -->"} .= "The product ID you requested already exists.<br>\n";
		$GTOOLS::TAG{"<!-- ERR_PROD_ID -->"} .= "<font color='red'>*</font>";
		}
	else {
		$GTOOLS::TAG{"<!-- ERR_PROD_ID -->"} = "<font>";
		}
	$product_id = uc(substr($c, 0, 20));

	$c = $ZOOVY::cgiv->{"base_price"};
	$c =~ s/\$//g;
	if ($c =~ /[^0-9&^.]/) {
		$error = 1;
		$GTOOLS::TAG{"<!-- ERROR_MSG -->"} .= "Invalid characters in base price!.<br>\n";
		$GTOOLS::TAG{"<!-- ERR_BASE_PRICE -->"} .= "<font color='red'>* ";
		}
	else {
		$GTOOLS::TAG{"<!-- ERR_BASE_PRICE -->"} = "<font>";
		}
	$COPYREF{"zoovy:base_price"} = $c;

	$c = $ZOOVY::cgiv->{"base_cost"};
	$c =~ s/\$//g;
	if ($c =~ /[^0-9&^.]/) {
		$error = 1;
		$GTOOLS::TAG{"<!-- ERROR_MSG -->"} .= "Invalid characters in base cost!.<br>\n";
		$GTOOLS::TAG{"<!-- ERR_BASE_PRICE -->"} .= "<font color='red'>* ";
		}
	else {
		$GTOOLS::TAG{"<!-- ERR_BASE_PRICE -->"} = "<font>";
		}
	$COPYREF{"zoovy:base_cost"} = $c;


	$c = $ZOOVY::cgiv->{"base_weight"};
	if ($c =~ /[^0-9\#\.]+/) {
		$error = 1;
		$GTOOLS::TAG{"<!-- ERROR_MSG -->"} .= "Invalid characters in Base Weight.<br>\n";
		$GTOOLS::TAG{"<!-- ERR_BASE_WEIGHT -->"} .= "<font color='red'>*</font>";
		}
	else { $GTOOLS::TAG{"<!-- ERR_BASE_WEIGHT -->"} = "<font>"; }
	$COPYREF{"zoovy:base_weight"} = $c;
	$COPYREF{"zoovy:taxable"} = &ZOOVY::is_true($ZOOVY::cgiv->{'taxable'})?'Y':'N';


	# second save the data.
	# third, redirect to modify_product.cgi
	my $inv_enable = 0;
	if ($error == 0) {
		$inv_enable = 1;
		if (defined $ZOOVY::cgiv->{'INV_UNLIMITED'}) { $inv_enable += 32; }
		$COPYREF{'zoovy:inv_enable'} = $inv_enable;
		foreach my $k (keys %COPYREF) {
			## strip LF's to compensate for strangness in LibYAML
			$COPYREF{$k} =~ s/[\r]+//gs;
			}

		($P) = PRODUCT->new($LU,$product_id,'create'=>1);
		foreach my $k (keys %COPYREF) {
			$P->store($k,$COPYREF{$k});
			}
		$P->save();
		$product_id = $P->pid();

		## Calling save record is not necessary! (and doesn't create a log)
		## &INVENTORY::save_record($USERNAME,$product_id,0,'U','','CREATE');
		&INVENTORY::add_incremental($USERNAME,$product_id,'U',int($ZOOVY::cgiv->{'INVENTORY'})); 

		print "Location: index.pl?goto=" . CGI->escape("edit.cgi?PID=$product_id") . "\n\n";
		} ## end if ($error == 0)
	else {
		$VERB = 'CREATE';
		}
	} ## end if ($VERB eq "SAVE" ...

if ($VERB eq 'CREATE') {
	$GTOOLS::TAG{"<!-- PRODUCT_ID -->"} = substr($product_id, 0, 25);
	$GTOOLS::TAG{"<!-- PRODUCT_NAME -->"}        = &ZOOVY::incode($COPYREF{"zoovy:prod_name"});
	$GTOOLS::TAG{"<!-- PRODUCT_DESCRIPTION -->"} = &ZOOVY::incode($COPYREF{"zoovy:prod_desc"});
	$GTOOLS::TAG{"<!-- BASE_PRICE -->"}          = $COPYREF{"zoovy:base_price"};
	$GTOOLS::TAG{"<!-- BASE_COST -->"}          = $COPYREF{"zoovy:base_cost"};
	$GTOOLS::TAG{"<!-- BASE_WEIGHT -->"}         = $COPYREF{"zoovy:base_weight"};
	$GTOOLS::TAG{'<!-- INVENTORY -->'} = $ZOOVY::cgiv->{'INVENTORY'};

	if (!defined($COPYREF{"zoovy:taxable"}) || $COPYREF{'zoovy:taxable'} eq '') { $COPYREF{"zoovy:taxable"} = 1; }

	if ($COPYREF{"zoovy:taxable"} =~ /y|1/i) {
		$GTOOLS::TAG{"<!-- TAXABLE -->"}     = "checked";
		$GTOOLS::TAG{"<!-- NOT_TAXABLE -->"} = "";
		}
	else {
		$GTOOLS::TAG{"<!-- TAXABLE -->"}     = "";
		$GTOOLS::TAG{"<!-- NOT_TAXABLE -->"} = "checked";
		}
	$GTOOLS::TAG{'<!-- INVENTORY -->'} = '';

	my %CATALOGS = ();
	if ($FLAGS =~ /,APPAREL,/) {
		%CATALOGS = (
			'clothing'=>'Clothing',
			'clothing.misc'=>'Clothing: Miscellaneous',
			'clothing.shoes'=>'Clothing: Shoes',
			'jewelry' => 'Jewelry',
			'jewelry.bracelets' => 'Jewelry: Bracelets',
			'jewelry.earrings' => 'Jewelry: Earrings',
			'jewelry.necklace' => 'Jewelry: Necklace',
			'jewelry.ring' => 'Jewelry: Ring',
			'jewelry.watch' => 'Jewelry: Watch',
			);
		}

	if ($FLAGS =~ /,MEDIA,/) {
		%CATALOGS = (
			'dvd'=>'DVD',
			'vhs'=>'VHS',
			'book'=>'Book',
			'cd'=>'CD',
			);
		}

	if (scalar(%CATALOGS)>0) {
		my $out = qq~
			<tr>
			<td class="data">Catalog:</td>
			<td nowrap align="left">
				<select name="catalog">
					<option ~.(($ZOOVY::cgiv->{'catalog'} eq '')?'SELECTED':'').qq~ value="">None</option>
					~;
		foreach my $cat (sort keys %CATALOGS) {
			$out .= qq~<option ~.((lc($ZOOVY::cgiv->{'catalog'}) eq $cat)?'SELECTED':'').qq~ value="$cat">$CATALOGS{$cat}</option>~;
			}
	
		$out .= '</select>';
		if ($FLAGS =~ /,MEDIA,/) {
			$out .= qq~
				&nbsp; 
				<input type="button" onClick="thisFrm.ACTION.value='SEARCH_CATALOG'; thisFrm.submit();" value=" Search Catalog ">
				~;
			}
		
	
		$out .= qq~
			</td>
			</tr>
		~;
		$GTOOLS::TAG{'<!-- CATALOGS -->'} = $out;
		}
	$template_file = 'create.shtml';
	$VERB = '*';
	}


## END CREATE


if (($VERB eq 'NUKE') && (not defined $ZOOVY::cgiv->{'confirm'})) { $VERB = ''; }
if ($VERB eq 'NUKE') {
	if (($ZOOVY::cgiv->{'delimages'} eq 'true') || ($ZOOVY::cgiv->{'delimages'} eq 'on')) {
		require MEDIA;
		my @images = ();
		push @images, 'zoovy:prod_thumb';
		foreach my $i (1..9999) { push @images, 'zoovy:prod_image'.$i; }
		
		foreach my $img (@images) {
			next if ($P->fetch($img) eq '');

			print STDERR "NUKE: $img\n";
			$LU->log('PRODEDIT.NUKEIMG',"[PID:$PID] Nuking image $img=".$P->fetch($img),'INFO');
			&MEDIA::nuke($USERNAME,$P->fetch($img));
			}
		}
	$LU->log('PRODEDIT.NUKE',"Nuking Product $PID",'INFO');
	&ZOOVY::deleteproduct($USERNAME,$PID);
	print "Location: /biz/product/edit.cgi\n\n";
	exit;
	}


if (($VERB eq 'RENAME') || ($VERB eq 'CLONE')) {

	my $NEWID = uc($ZOOVY::cgiv->{'NEW_PID'}); 
	if ($VERB eq 'CLONE') { $NEWID = uc($ZOOVY::cgiv->{'new_pid'}); }
	$NEWID =~ s/[^\w-]+//g;

	if (($VERB eq 'RENAME') && ($NEWID eq '')) { 	
		push @ERRORS, "You must input a Product ID for $PID to be renamed to"; $NEWID = '';
		}
	if (($VERB eq 'CLONE') && ($NEWID eq '')) { 	
		push @ERRORS, "You must input a Product ID for $PID to be cloned to"; $NEWID = '';
		}
	if (&ZOOVY::productidexists($USERNAME,$NEWID)) { 
		push @ERRORS, "A product with the id $NEWID already exists"; $NEWID = '';
		}

	my $Pnew = undef;
	if (scalar(@ERRORS)==0) {
		$Pnew = PRODUCT->new($USERNAME,$NEWID,'create'=>1);
		}

	if (defined $Pnew) {
		require INVENTORY;
		require NAVCAT;
		my ($onref,$reserveref,$locref,$reorderref,$onorderref) = &INVENTORY::fetch_incrementals($USERNAME,[$PID],undef,8+16+32+64+128);
		foreach my $sku (keys %{$onref}) {
			my ($pid,$claim,$invopts,$noinvopts) = &PRODUCT::stid_to_pid($sku);
			next if ($pid ne $PID);	## wtf, sometimes fetch_incrementals returns us products that we didn't ask for. (yeah it's supposed to do that)
			my $NEWSKU = $NEWID.(($invopts ne '')?':'.$invopts:'').(($noinvopts ne '')?'/'.$noinvopts:'');
			if ($VERB eq 'RENAME') { 
				&INVENTORY::save_record($USERNAME,$NEWSKU,$onref->{$sku},'U',$locref->{$sku},'CHANGEPID');
				&INVENTORY::nuke_record($USERNAME,$PID,$sku,"Rename to $NEWSKU"); 
				}
			## NOTE: inventory on cloned products may not be set to unlimited properly. not sure why? 8/16/2012
			## 		but inventory changes are coming soon so i'm not going to fix?
			}		

		## NOTE: we need to copy the product if we're cloning or renaming (but we only need to delete if we're renaming)
		my $PREF = $P->prodref();
		# my ($PREF) = &ZOOVY::fetchproduct_as_hashref($USERNAME,$PID);

		if ($VERB eq 'CLONE') {
			$LU->log('PRODEDIT.CLONE',"PID[$PID] cloned to PID[$NEWID]",'INFO');
			}
		elsif ($VERB eq 'RENAME') {
			$LU->log('PRODEDIT.RENAME',"PID[$PID] renamed to PID[$NEWID]",'INFO');
			}

		foreach my $k (keys %{$PREF}) { 
			my $skip = 0;
			if ($VERB eq 'RENAME') {}					## on a rename, don't destory fields.
			elsif ($k =~ /^zoovy\:/) {} 												## always CLONE zoovy: fields
			elsif (substr($k,0,1) eq '%') { $skip++; }		## ex: %SKU 
			elsif (substr($k,0,1) eq '@') { $skip++; }		## ex: @POGS
			elsif (($k =~ /^ebay/) && ($ZOOVY::cgiv->{'CLONE_EBAY'})) {}	## only CLONE ebay: fields if indicated by merchant
			elsif ($ZOOVY::cgiv->{'CLONE_OTHER'} && $k ne 'amz:asin') {}	## only CLONE other: (amz:, etc) fields if indicated by merchant
			else {				
				$skip++;																			## never CLONE amz:asin, this causes major merging issues!!	
				}
			
			if (not $skip) {
				$Pnew->store($k,$PREF->{$k});
				}
			}

		if (scalar(@{$P->fetch_pogs()})>0) {
			## copy product options and sku level data.
			$Pnew->store_pogs($P->pogs());

			foreach my $skuset (@{$P->list_skus('verify'=>1)}) {
				my ($SKU,$dataref) = @{$skuset};
				next if ($SKU eq '');
				next if ($SKU eq '.');
				my $NEWSKU = $NEWID.substr($SKU,0,length($SKU));
				foreach my $k (keys %{$dataref}) {
					$Pnew->skustore($NEWSKU,$k,$dataref->{$k});
					}
				}
			}

		if ($ZOOVY::cgiv->{'CLONE_DISABLESYNDICATION'}) {
			## forces syndication off for all products.
			foreach my $ref (@ZOOVY::INTEGRATIONS) {
				if ($ref->{'attr'}) { 
					#print STDERR "PREF: $ref->{'attr'}\n";
					$Pnew->store($ref->{'attr'},0);
					# $PREF->{ $ref->{'attr'} } = 0; 
					}
				}
			}
		$Pnew->save();
	
		if ($VERB eq 'RENAME') {
			# handle navcats
			$LU->log('PRODEDIT.RENAME',"PID[$PID] renamed to PID[$NEWID]",'INFO');
			require NAVCAT;
			foreach my $prttext (@{&ZWEBSITE::list_partitions($USERNAME)}) {		
				my ($prt) = split(/:/,$prttext);
				my $NC = NAVCAT->new($USERNAME,PRT=>$prt);
				my $arref = $NC->paths_by_product($PID);
				if (defined $arref) {
					foreach my $safe (@{$arref}) {
						$NC->set( $safe, insert_product=>$NEWID, delete_product=>$PID);
						}
					$NC->save();
					}
				}

			require PRODUCT::REVIEWS;
			&PRODUCT::REVIEWS::rename_product($USERNAME,$PID,$NEWID);
			&ZOOVY::deleteproduct($USERNAME,$PID);
			}
		$P = $Pnew;
		$PID = $P->pid();
		}
	$VERB = '';
	}


##
## some ground rules.
##		each form should have the fields named the same as the variable they are editing.
##		each form should have some sort of identifier e.g. _ID= which designates which form is being saved.
##


if (($VERB ne '*') && (ref($P) ne 'PRODUCT')) {
	$html = "<li> Could not load product from database";
	$VERB = 'ERROR';
	}

if (($VERB ne '*') && ($PID eq '')) {
	$html = "<li> Product id not set, please let support know what you were doing when this message occurred.";
	use Data::Dumper;
	$html .= "<pre>".Dumper($ZOOVY::cgiv)."</pre>";
	$VERB = 'ERROR';
	}

if ($VERB eq '*') {
	}
elsif ($VERB eq 'ERROR') {
	}
else {
	# $GTOOLS::TAG{'<!-- GENERAL_PANEL -->'} = $PRODUCT::PANELS::func{'general'}->($LU,$PID,'',$prodref,{});
	$GTOOLS::TAG{'<!-- GENERAL_PANEL -->'} = &PRODUCT::PANELS::panel_general($LU,$P,'',{});
	$GTOOLS::TAG{'<!-- PID -->'} = $PID;


	my @PANELS = ();
	my $ERRORS = &GTOOLS::errmsg( join("<li>",@ERRORS) );

	my $PANELSAR = &PRODUCT::PANELS::return_user_panels($LU,$P);

	my $fastlookupjs = '';
	my $PANELSHTML = '';
	foreach my $panelref (@{$PANELSAR}) {
		# example:
		#$content = ($state)?$PRODUCT::PANELS::func{'catalog'}->($USERNAME,$PID,'',$prodref):'';
		#$GTOOLS::TAG{'<!-- CATALOG_PANEL -->'} = &PRODUCT::PANELS::render_panel('catalog','Catalogs',$state,$content);
		my ($content,$state) = ('',0);
		if (defined $LU) { ($state) = $LU->get('prodedit.'.$panelref->{'id'},0); }
		
		next if ($panelref->{'id'} eq '');
		next if ($panelref->{'id'} eq 'general');	# we've already done this!
		next if ($panelref->{'position'} <= 0);	# we shouldn't display this.

		if ($panelref->{'id'} eq 'buy') {
		$fastlookupjs = q~<script language="JavaScript1.2" type="text/javascript" src="/biz/syndication/fastlookup.js"></script>
<script>
<!--

var popWin;

function selectCategory(MKT,NAVCAT,VAL,FRM) {
   popWin = openWindow('/biz/syndication/catchooser.cgi?FRM='+FRM+'&MKT='+MKT+'&CATID='+VAL+'&NAVCAT='+NAVCAT);
   }

function closeWindow(nc,catid) {
   window.opener.ajaxUpdate('JLY',window.document.catFrm[nc]);
   }

//-->
</script>
~;
		}

#	print STDERR "$panelref->[0]\n";
#	print STDERR Dumper($P);

	($content,my $js) = ($state) ? $panelref->{'func'}->($LU,$P,'',{}):'';
	$content .= "<script>\n$js\n</script>";
	$PANELSHTML .= &AJAX::PANELS::render_panel($panelref->{'id'},$panelref->{'title'},$state,$content);
	}

$html = qq~
<head>
$fastlookupjs
<!-- HEADER_ONLY -->
~.AJAX::PANELS::header('PRODEDIT',$PID,'edit.cgi').qq~</head>
<body  marginwidth="0" marginheight="0">
<!-- MYTODO -->

$ERRORS

<!-- general information table -->
<table width="800" class="border_top border_right border_bottom border_left" cellpadding="5" cellspacing="0">
	<tr>
		<td class="border_bottom bold" colspan="2"><!-- PID --></td>
	</tr>
	<tr>
		<td class="divider bold" colspan="2">General Information</td>
	</tr>
	<tr>
		<td>
		<form style="margin: 0px;" id="general!frm" name="general!frm">
		<div id="general!content"><!-- GENERAL_PANEL --></div>
		</form>
		</td>
	</tr>
</table>

<table width="800" cellpadding="0" cellspacing="0" style="margin-top: 4px;">
	<tr>
		<td>
		$PANELSHTML
		</td>
	</tr>
</table>

<br>
<br>
<br>
</form>
</center>


</body>
~;

	}


my %NEED = ();
if ($LU->get('todo.setup')) {
	require TODO;
	my $t = TODO->new($USERNAME);	
	my ($need,$tasks) = $t->setup_tasks('products',LU=>$LU);
	$GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('products',$tasks);
   }



&GTOOLS::output(file=>$template_file,html=>$html,header=>1,todo=>1,jquery=>1,zmvc=>1);
undef $LU;

exit;


