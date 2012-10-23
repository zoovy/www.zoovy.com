#!/usr/bin/perl -w
##
## CGI-style script with dispatcher here. Allows browsing between categories, viewing item specifics
## one-attribute search, working with product finders and viewing prefilled specifics set.
##
## IMPORTANT! config is in modules/ebayConfig.pm
##
use strict;
use DBI;
use Template;
use CGI qw/param Vars/;
use CGI::Carp qw(fatalsToBrowser);
use XML::Parser;
use XML::SimpleObject;
use XML::Simple;
use URI::Escape;
use File::Temp;
use Data::Dumper;
#use FindBin;
#use lib "$FindBin::Bin/lib";
use lib '/httpd/modules';
use ebayConfig;
use ebayAPI;
require ZOOVY;
require LUSER;
require EBAY2;
require PRODUCT;
#chdir "..";

my $SREF = {}; ## global session variables.
my ($eb2, $edbh, $cgi, $action, $dispatch, $stash, $rendered, $MID, $USERNAME, $LUSERNAME, $FLAGS, $PRT, $SESSION);
my $XALAN = '/usr/local/xalan/bin/Xalan';

init();
dispatch();
end();

sub init {
	$cgi = new CGI;
	($MID, $USERNAME, $LUSERNAME, $FLAGS, $PRT) = LUSER->authenticate(sendto=>"/biz",scalar=>1);
	($eb2) = EBAY2->new($USERNAME,'ANYTOKENWILLDO'=>1);

	if (not defined $eb2) {
		die("Could not find a valid eBay token for partition:$PRT");
		}

	$edbh = $eb2->ebay_db_connect();
	##$stash->{MID} = $MID; $stash->{USERNAME} = $USERNAME; $stash->{LUSERNAME} = $LUSERNAME; $stash->{FLAGS} = $FLAGS;	$stash->{PRT} = $PRT;

	my @uri = split '/', $ENV{'REQUEST_URI'}; ## contains /biz/ebay/catchooser2008/index.cgi/action
	($action = $uri[5] || 'index') =~ s/\?.*//;

	if (defined $ZOOVY::cgiv->{'_SESSION'}) {
		$SREF = &ZTOOLKIT::fast_deserialize($ZOOVY::cgiv->{'_SESSION'});
		}
	elsif (defined $ZOOVY::cgiv->{'FRM'}) {
		# use Data::Dumper; die(Dumper($ZOOVY::cgiv));
		foreach my $k ('PID','V','FRM','CATID') {
			next if (not defined $ZOOVY::cgiv->{$k});
			$SREF->{$k} = $ZOOVY::cgiv->{$k};
			}
	 $SREF->{'CATID'} = int($SREF->{'CATID'});
		}
	else {
		$SREF = &ZTOOLKIT::fast_deserialize( $cgi->cookie('SESSION') );
		}
		
	 
	$stash->{'PID'} = $SREF->{'PID'};
	$stash->{'V'} = $SREF->{'V'};
	$stash->{'FRM'} = $SREF->{'FRM'};

	
	if ($SREF->{'PID'} eq '') {
		die("Product ID not set");
		}
		
	if ($SREF->{'V'} eq '') {
		die("Return value not set");
		}
		
	if ($SREF->{'FRM'} eq '') {
		die("Parent form not set");
		}
		
	if ($ZOOVY::cgiv->{'category_id'}) {
		## always save the CATID if we've set it.
		$SREF->{'CATID'} = int($ZOOVY::cgiv->{'category_id'});
		}
	elsif ($ZOOVY::cgiv->{'id'}) {
		## always save the CATID if we've set it.
		$SREF->{'CATID'} = int($ZOOVY::cgiv->{'id'});
		}

	$SESSION = &ZTOOLKIT::fast_serialize($SREF);
	
	my $categories;
	my $pstmt = qq~SELECT ec.id, ec.site, ec.name 
		FROM ebay_categories ec, ebay_last_categories elc 
		WHERE	(elc.user_id=$MID) AND (ec.id=elc.category_id) 
		ORDER BY elc.create_timestamp DESC~;
		
	my $sth = $edbh->prepare($pstmt) or die	$edbh->errstr;
	$sth->execute or die $sth->errstr;
	while ( my ($cat_id, $site, $cat_name) = $sth->fetchrow_array ) {
		my $cat = {};
		$cat->{id} = $cat_id;
		$cat->{name} = $cat_name;
		push @$categories, $cat;
		}
	$sth->finish();
	$stash->{last_categories} = $categories;

	## last categories from old chooser
	my $old_categories = [];
	$pstmt = qq~SELECT ec.id, ec.site, ec.name
		FROM ebay_categories ec, EBAY_USER_CATEGORIES euc
		WHERE	(euc.merchant='$USERNAME') AND (ec.id=euc.category)
		ORDER BY euc.CREATED_GMT DESC~;
	$sth = $edbh->prepare($pstmt) or die	$edbh->errstr;
	$sth->execute or die $sth->errstr;
	while ( my ($cat_id, $site, $cat_name) = $sth->fetchrow_array ) {
		my $cat = {};
		$cat->{id} = $cat_id;
		$cat->{name} = $cat_name;
		push @$old_categories, $cat;
		}
	$sth->finish();
	$stash->{old_last_categories} = $old_categories;


	$stash->{'CATID'} = $SREF->{'CATID'};
	$stash->{'selected_category_name'} = &EBAY2::get_cat_fullname($USERNAME,$stash->{'CATID'});

	## if we already saved category and user wants to review
	## lets begin from category + saved specifics form
	my $saved_category = PRODUCT->new($USERNAME,$SREF->{'PID'},'create'=>0)->fetch($SREF->{'V'});
	## check that saved cat exists in up-to-date category tree
	$sth = $edbh->prepare("SELECT id FROM ebay_categories WHERE id=?");
	my $temp_cat = $saved_category;
	$temp_cat = $1 if $temp_cat =~ /(\d+)\./; 
	$sth->execute($temp_cat);
	my $res = $sth->fetchrow_array;
	$sth->finish;

	if ($res and $action eq 'index' and $saved_category and not $stash->{'CATID'}) {
		$stash->{selected_category} = {};
		($stash->{'CATID'}, $SREF->{'CATID'}, $stash->{selected_category}{id}) = ($saved_category, $saved_category, $saved_category);
		($SREF->{'CATID'}, $stash->{selected_category}{id}) = ($1,$1) if $saved_category =~ /(\d+)\./;
		$action = 'get_categories';
	}

	## for save
	$SREF->{CATID} = $ZOOVY::cgiv->{'primary_category'} if $ZOOVY::cgiv->{'primary_category'};
	$SREF->{CATID} = $ZOOVY::cgiv->{'secondary_category'} if $ZOOVY::cgiv->{'secondary_category'};
	}
	

##
##
##
sub end {
	$eb2->ebay_db_close() or warn $edbh->errstr;
	}


##
##
##
sub render {
	my ($file) = @_;
	my $template;
	$stash->{action} = $action;

	$stash->{nowrapper} = 1 if ($ENV{HTTP_X_REQUESTED_WITH} and $ENV{HTTP_X_REQUESTED_WITH} eq 'XMLHttpRequest');
	$template = Template->new({
		INCLUDE_PATH => $TEMPLATES_PATH,
		WRAPPER => 'wrapper.tt2'
		});

	my $session_cookie = $cgi->cookie(
		-name=>'SESSION',
		-value=>$SESSION,
		-expires=>'+1h',
		-path=>'/biz/ebay/catchooser2008',
		-secure=>0
		);

	if(!$rendered) {
		if($stash->{xml}) {
			#print "Content-Type: text/xml; charset=utf8\n\n";
			print $cgi->header(
				-type=>'text/xml',
				-charset=>'utf-8'
				);
			} 
		else {
			#print "Content-Type: text/html; charset=uft8\n\n";
			print $cgi->header(
				-type=>'text/html',
				-charset=>'utf-8',
				-cookie=>[$session_cookie]
				);
			}
		$template->process($file, $stash); $rendered = 1;
		}
	}

## ACTIONS GO HERE
##
sub index {
	render('index.tt2');
	}



##
##
##
sub get_categories {
	prepare_category_tree();
	my $selected_category = $stash->{selected_category};

	if($selected_category && $selected_category->{leaf}) {
		## leaf category is a place where you can add your item.
		## so we gonna to render One-Attribute Search form (for categories with
		## ProductSearchPageAvailable) or Product Finder form (for categories,
		## supportion product finders) or simply render 'Describe your item'
		## with choose custom specifics form if any.

		##update last 10 categories
		my $sth = $edbh->prepare("SELECT count(category_id) FROM ebay_last_categories WHERE user_id = ?") or die $edbh->errstr;
		$sth->execute($MID) or die $sth->errstr;
		my $count = $sth->fetchrow_array;

		if ($count < 10) { ## less than 10 categories in list - create new or update timestamp if exists
			$sth = $edbh->prepare("SELECT category_id FROM ebay_last_categories WHERE user_id = ? AND category_id = ?") or die $edbh->errstr;
			$sth->execute($MID, $selected_category->{id}) or die $sth->errstr;
			my $category_id = $sth->fetchrow_array;
			if($category_id) {
				$sth = $edbh->prepare("UPDATE ebay_last_categories SET create_timestamp = ? WHERE user_id = ? AND category_id = ?") or die $edbh->errstr;
				$sth->execute(&EBAY2::timestamp(), $MID, $selected_category->{id}) or die $sth->errstr;
				} 
			else {
				$sth = $edbh->prepare("INSERT INTO ebay_last_categories(user_id, category_id, create_timestamp) VALUES(?,?,?)") or die $edbh->errstr;
				$sth->execute($MID, $selected_category->{id}, &EBAY2::timestamp()) or die $sth->errstr;
				}
			} 
		else { ## 10 categories in list - update oldest one - set new category_id and timestamp
			$sth = $edbh->prepare("SELECT category_id FROM ebay_last_categories WHERE user_id = ? AND category_id = ?") or die $edbh->errstr;
			$sth->execute($MID, $selected_category->{id}) or die $sth->errstr;
			my $category_id = $sth->fetchrow_array;
			if($category_id) {
				$sth = $edbh->prepare("UPDATE ebay_last_categories SET create_timestamp = ? WHERE user_id = ? AND category_id = ?") or die $edbh->errstr;
				$sth->execute(&EBAY2::timestamp(), $MID, $selected_category->{id}) or die $sth->errstr;
				} 
			else {
				$sth = $edbh->prepare("SELECT category_id FROM ebay_last_categories WHERE user_id = ? ORDER BY create_timestamp ASC LIMIT 1") or die $edbh->errstr;
				$sth->execute($MID) or die $sth->errstr;
				my $oldest = $sth->fetchrow_array();
				$sth = $edbh->prepare("UPDATE ebay_last_categories SET category_id = ?, create_timestamp = ? WHERE user_id = ? AND category_id = ?") or die $edbh->errstr;
				$sth->execute($selected_category->{id}, EBAY2::timestamp(), $MID, $oldest) or die $sth->errstr;
				}
			}

		## If user selects Secondary eBay category - just render 'Save' button, not allowing choose custom specifics
		if($SREF->{'V'} eq 'ebay:category2') {
			$stash->{secondary} = 1;
			render('get_categories.tt2');
			return;
		}

		$sth = $edbh->prepare('SELECT ebay_product_finders.data_present FROM ebay_category_2_product_finder, ebay_product_finders WHERE ebay_product_finders.id = ebay_category_2_product_finder.product_finder_id AND ebay_category_2_product_finder.category_id = '.$selected_category->{id}) or die $edbh->errstr;
		$sth->execute or die $sth->errstr;
		my $pf_available = $sth->fetchrow_array;
		$sth->finish();
		my $CATID = $selected_category->{id};
		my ($SITE) = &resolveSite( $CATID );
		
#		if($SITE == 0 && $selected_category->{catalog_enabled} && $selected_category->{product_search_page_available} && $pf_available) {
#			## if Both ProductSearchPage and ProductFinder available
#			## prepare them and render both.
#			show_sp_pf_form();
#			}
#		elsif($SITE == 0 && $selected_category->{catalog_enabled} && $selected_category->{product_search_page_available}) {
#			## if only ProductSearchPageAvailable
#			## prepare one-attribute search form and show it to user
#			show_sp_form();
#			}
#		elsif($SITE == 0 && $selected_category->{catalog_enabled} && $pf_available ) {
#			## if only ProductFinder available
#			## prepare PF form and render it to user
#			## product_finder->data_present check below is a tricky eBay move
#			## some categories has product finder support declared, but when you make a call
#			## to get ProductFinder Data - it returns XML with Success
#			## but without ProductFinderData section!!!
#			show_pf_form();
#			}
#		else { 
#			## if none of above available
#			## just render describe item form (not prefilled)
			describe_item(); 
#			}
		} 
	else {
		## just render category tree
		render('get_categories.tt2');
		}
	}

##
## takes query and tries to suggest category to list (with % item match)
sub get_suggested_categories {
	if($ZOOVY::cgiv->{'query'}) {
		$stash->{'query'} = $ZOOVY::cgiv->{'query'};
		my $api = new ebayAPI;
		my $xml = $api->getSuggestedCategories(&EBAY2::str_safe($ZOOVY::cgiv->{'query'}));
		if($xml && $xml !~ /An Error Occurred/) {
			my $parser = new XML::Parser (ErrorContext => 2, Style => "Tree");
			my $xmlobj = new XML::SimpleObject ($parser->parse($xml));
			if( $xmlobj->child('GetSuggestedCategoriesResponse')->child('Ack')->value eq 'Warning' ||
					$xmlobj->child('GetSuggestedCategoriesResponse')->child('Ack')->value eq 'Failure') {
				$stash->{'error'} = 'eBay returned after GetSuggestedCategories: '.$xmlobj->child('GetSuggestedCategoriesResponse')->child('Errors')->child('LongMessage')->value;
				$stash->{'error'} =~ s/ <0>//;
			} elsif($xmlobj->child('GetSuggestedCategoriesResponse')->child('Ack')->value eq 'Success') {
				$stash->{'category_count'} = $xmlobj->child('GetSuggestedCategoriesResponse')->child('CategoryCount')->value;
				if($xmlobj->child('GetSuggestedCategoriesResponse')->child('SuggestedCategoryArray')) {
					foreach my $category ($xmlobj->child('GetSuggestedCategoriesResponse')->child('SuggestedCategoryArray')->child('SuggestedCategory')) {
						my $category_to_template = {};
						$category_to_template->{id} = $category->child('Category')->child('CategoryID')->value;
						$category_to_template->{name} = $category->child('Category')->child('CategoryName')->value;
						$category_to_template->{percentage} = $category->child('PercentItemFound')->value;
						push @{$stash->{'categories'}}, $category_to_template;
					}
				}
			}
		} else {
			$stash->{'error'} = "Category Suggest - Cannot make call to eBay";
		}
	}

	## also fetch directly from ebay_categories
	if ($stash->{'query'}) {
		my $sth = $edbh->prepare("select id, name from ebay_categories where name like ? and leaf=1 limit 15");
		if(int $sth->execute('%'.$stash->{'query'}.'%')) {
			$stash->{direct_categories} = [];
			while(my ($catid, $catname) = $sth->fetchrow_array) {
				push @{$stash->{direct_categories}}, {id=>$catid, name=>&EBAY2::get_cat_fullname($USERNAME,$catid,2)};
			}

		}
	}

	render('suggested_categories.tt2');
}

##
## just renders 'describe item form'
sub describe_item {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my ($SITE) = &resolveSite( $stash->{selected_category}{id} );
	prepare_cs_form();# if $SITE == 0; ## we have specifics only for ebay.com site 0
	## check if we need to display UPC/ISBN/EAN field (in media/books category)
	## that improves listing (ebay insers rating/picture/... automagically)
	$stash->{is_media_cat} = 1 if $eb2->is_media_cat($stash->{selected_category}{id});

	restore_cs_form(); ## if user returns to review saved category

	render('add_item.tt2');
}

##
## renders both one attribute search form and product finder for selected category
sub show_sp_pf_form {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my $selected_category = $stash->{'selected_category'};
	if ( $selected_category->{product_search_page_available} ) {
		prepare_sp_form();
		}

	my $sth = $edbh->prepare('SELECT ebay_product_finders.data_present FROM ebay_category_2_product_finder, ebay_product_finders WHERE ebay_product_finders.id = ebay_category_2_product_finder.product_finder_id AND ebay_category_2_product_finder.category_id = '.$selected_category->{id}) or die $edbh->errstr;
	$sth->execute or die $sth->errstr;
	my $pf_available = $sth->fetchrow_array;
	if ( $pf_available ) {
		prepare_pf_form();
		}
	render('sp_and_pf_form.tt2');
	}

##
## renders one attribute search form for selected category
sub show_sp_form {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my $selected_category = $stash->{'selected_category'};
	if( $selected_category->{product_search_page_available} ) {
		prepare_sp_form();
		}
	render('search_page_form.tt2');
	}

##
## renders product finder form for selected category
sub show_pf_form {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my $selected_category = $stash->{'selected_category'};

	my $sth = $edbh->prepare('SELECT ebay_product_finders.data_present FROM ebay_category_2_product_finder, ebay_product_finders WHERE ebay_product_finders.id = ebay_category_2_product_finder.product_finder_id AND ebay_category_2_product_finder.category_id = '.$selected_category->{id}) or die $edbh->errstr;
	$sth->execute or die $sth->errstr;
	my $pf_available = $sth->fetchrow_array;

	if( $pf_available ) {
		prepare_pf_form();
		}
	render('product_finder_form.tt2');
	}

##
## takes data from One-attribute search form or ProductFinder form
## calls GetProductSearchResult and renders found items to user
sub get_product_search_results {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my $selected_category = $stash->{'selected_category'};
	my $xml = '';

	if($ZOOVY::cgiv->{'sp_search'}) {
		## One-attribute search
		my $attribute_set_id = $ZOOVY::cgiv->{'attribute_set_id'};
		$stash->{'attribute_set_id'} = $attribute_set_id;
		my $attribute_id = $ZOOVY::cgiv->{'attribute_id'};
		my $attribute_value = &EBAY2::str_safe($ZOOVY::cgiv->{'attribute_value'});
		my $in_xml = "<ProductSearch>
		<AttributeSetID>$attribute_set_id</AttributeSetID>
			<SearchAttributes>
				<AttributeID>$attribute_id</AttributeID>
				<ValueList>
					<ValueLiteral>$attribute_value</ValueLiteral>
				</ValueList>
			</SearchAttributes>
		</ProductSearch>";
		my $api = new ebayAPI;
		#open F, "$PATH_TO_STATIC/xml/GetProductSearchResults/sample.xml"; $xml .= $_ while(<F>); close F;
		$xml = $api->getProductSearchResults($in_xml);
	} else {
		## product finder search
		#my $attribute_set_id = $selected_category->category2cs->first->attribute_set_id;
		my $sth = $edbh->prepare('SELECT attribute_set_id FROM ebay_category_2_cs WHERE category_id = '.$selected_category->{id}) or die $edbh->errstr;
		$sth->execute or die $sth->errstr;
		my $attribute_set_id = $sth->fetchrow_array;

		$stash->{'attribute_set_id'} = $attribute_set_id;
		my $product_finder_id = $ZOOVY::cgiv->{'pfid'};
		my $in_xml = "<ProductSearch>
		<AttributeSetID>$attribute_set_id</AttributeSetID>
		<ProductFinderID>$product_finder_id</ProductFinderID>";
		foreach my $attribute_id (keys %{$ZOOVY::cgiv}) {
			if($attribute_id =~ /^a[\d]*$/) {
				my $attribute_value = &EBAY2::str_safe($ZOOVY::cgiv->{$attribute_id});
				$attribute_id =~ s/a//;
				$in_xml .= "
				<SearchAttributes>
					<AttributeID>$attribute_id</AttributeID>
					<ValueList>
						<ValueLiteral>$attribute_value</ValueLiteral>
					</ValueList>
				</SearchAttributes>";
				}
			}
		$in_xml .= "</ProductSearch>";
		my $api = new ebayAPI;
		#open F, "$PATH_TO_STATIC/xml/GetProductSearchResults/sample_pf.xml"; $xml .= $_ while(<F>); close F;
		$xml = $api->getProductSearchResults($in_xml);
		}

	if($xml !~ /An Error Occurred/) {
		my $parser = new XML::Parser (ErrorContext => 2, Style => "Tree");
		my $xmlobj = new XML::SimpleObject ($parser->parse($xml));

		if( $xmlobj->child('GetProductSearchResultsResponse')->child('Ack')->value eq 'Warning' ||
				$xmlobj->child('GetProductSearchResultsResponse')->child('Ack')->value eq 'Failure') {
			$stash->{'error'} = $xmlobj->child('GetProductSearchResultsResponse')->child('Errors')->child('LongMessage')->value;
			$stash->{'error'} =~ s/ <0>//;
			}

		if(not defined $stash->{'error'}) {
			foreach my $product_family ($xmlobj->child('GetProductSearchResultsResponse')->child('ProductSearchResult')->child('AttributeSet')->child('ProductFamilies')) {
				my $product = $product_family->child('ParentProduct');
				if($product) {
					my $product_to_template = {};
					$product_to_template->{'characteristics'} = {};
					foreach my $characteristic ($product->child('CharacteristicsSet')->child('Characteristics')) {
						my ($name, $value) = ('', '');
						$name = $characteristic->child('Label')->child('Name')->value if $characteristic->child('Label');
						$value = $characteristic->child('ValueList')->child('ValueLiteral')->value if $characteristic->child('ValueList');
						$product_to_template->{'characteristics'}->{$name} = $value;
						}
						
					if($product->child('DetailsURL')) {
						$product_to_template->{'details_url'} = $product->child('DetailsURL')->value;
						}
					my %product_attributes = $product->attributes;
					$product_to_template->{'stock_photo_url'} = $product_attributes{'stockPhotoURL'};
					$product_to_template->{'id'} = $product_attributes{'productID'};
					push @{$stash->{'products'}}, $product_to_template;
					}
				}
			}
		} 
	else {
		$stash->{'error'} = "Product Search Results - Cannot make call to eBay";
		}
	render('product_search_results.tt2');
	}

sub get_product_selling_pages {
	prepare_category_tree() if not defined $stash->{'selected_category'};
	my $selected_category = $stash->{'selected_category'};
	prepare_prefilled_cs_form();
	$stash->{'pf'} = 1;
	render('add_item.tt2');
	}

##
## builds XML for AddItem call and prints to user
sub add_item {
	$stash->{'pars'} = $ZOOVY::cgiv;
	$stash->{'title'} = &EBAY2::str_safe($ZOOVY::cgiv->{'title'}) || 'Sample Title';
	$stash->{'subtitle'} = &EBAY2::str_safe($ZOOVY::cgiv->{'subtitle'}) || '';
	$stash->{'attribute_set_id'} = [ $ZOOVY::cgiv->{'vcsid'} ] || '';
	$stash->{'primary_category'} = $ZOOVY::cgiv->{'primary_category'} || '';
	$stash->{'start_price'} = $ZOOVY::cgiv->{'start_price'} || '5';
	$stash->{'quantity'} = $ZOOVY::cgiv->{'quantity'} || 1;
	$stash->{'description'} = &EBAY2::str_safe($ZOOVY::cgiv->{'description'}) || 'Sample Description';
	$stash->{'item_location'} = &EBAY2::str_safe($ZOOVY::cgiv->{'item_location'}) || 'Sample Location';
	$stash->{'listing_duration'} = $ZOOVY::cgiv->{'listing_duration'} || 'Days_3';
	$stash->{'payment_email'} = &EBAY2::str_safe($ZOOVY::cgiv->{'payment_email'}) || 'ebay@ebay.com';
	$stash->{'product_id'} = $ZOOVY::cgiv->{'product_id'};
	my ($SITE) = &resolveSite($SREF->{'CATID'});
	$stash->{'FRM'} = $SREF->{'FRM'};
	$stash->{'V'} = $SREF->{'V'};
	$stash->{'CATID'} = $SREF->{'CATID'}.(($SITE>0)?('.'.$SITE):'');
	$stash->{'ebay:ext_pid_type'} = $ZOOVY::cgiv->{'ebay:ext_pid_type'} || '';	
	$stash->{'ebay:ext_pid_value'} = $ZOOVY::cgiv->{'ebay:ext_pid_value'} || '';
	$stash->{'selected_category_name'} = &EBAY2::get_cat_fullname($USERNAME,$SREF->{'CATID'});


	print STDERR "PIRMARY: $ZOOVY::cgiv->{'primary_category'})\n";

	## Can save category now. And item attributes will be saved after successful VerifyAddItem call
	if ($ZOOVY::cgiv->{'primary_category'}) {
		my $CATID = int($ZOOVY::cgiv->{'primary_category'});
		my ($SITE) = &resolveSite( $CATID );
		if ($SITE>0) { $CATID = "$CATID.$SITE"; }		

		my ($P) = PRODUCT->new($USERNAME,$SREF->{'PID'});
		# my ($prodref) = &ZOOVY::fetchproduct_as_hashref($USERNAME,$SREF->{'PID'});
		$P->store('ebay:category',$CATID);
		# &ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:category', $CATID);
#		$CATID = $1 if $CATID =~ /(\d+)\./;
		## reset old specifics to ''
		# &ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:attributeset','');
		$P->store('ebay:attributeset','');
		# &ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:attributes','');	
		if ($stash->{'ebay:ext_pid_type'} and $stash->{'ebay:ext_pid_value'}) {
			#&ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_type', $stash->{'ebay:ext_pid_type'});
			#&ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_value', $stash->{'ebay:ext_pid_value'});
			$P->store('ebay:ext_pid_type',$stash->{'ebay:ext_pid_type'});
			$P->store('ebay:ext_pid_value',$stash->{'ebay:ext_pid_value'});
			} 
		elsif ($stash->{'ebay:ext_pid_type'}) {
			#&ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_type', '');
			#&ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_value', '');
			$P->store('ebay:ext_pid_type','');
			$P->store('ebay:ext_pid_value','');
			}

		$P->save();
		# &ZOOVY::saveproduct_from_hashref($USERNAME,$SREF->{'PID'},$prodref);
		print STDERR "ZOOVY:\n";
		print STDERR Dumper($ZOOVY::cgiv);

		## if form was blank - just save and close		
		my $blank_form = 1;
		foreach my $attr (keys %$ZOOVY::cgiv) {
			if ($attr =~ /^attr/) { $blank_form = 0; }		# has item specifics
			if ($attr =~ /^cs_name/) { $blank_form = 0; }	# has custom attributes
			}
		if ($blank_form) { 
			render('saved.tt2');
			return;
			}
		}

	foreach my $attr (keys %$ZOOVY::cgiv) {
		if ($attr =~ /^attr/ and $attr !~ /2135_/) { ## 2135 is return policy - we'll process it separately'
			my @attr = split '_', $attr;
			my $type = 'ValueID';
			$type = 'ValueLiteral' if $attr[1] =~ /[tdy]\d+/; ## inputs where literal expected looks like <input name=attr_t2135_3806 value..../>
			if( $ZOOVY::cgiv->{$attr} eq '-6') {
				## if user selected 'other' and entered his value
				$stash->{'attributes'}->{$attr[1]} = {type=>'ValueLiteral', value=>[&EBAY2::str_safe( $ZOOVY::cgiv->{'other_'.$attr} )]} if $ZOOVY::cgiv->{'other_'.$attr};
				} 
			else {
				$stash->{'attributes'}->{$attr[1]} = {type=>$type, value=>[param($attr)]} if $attr[1] !~ /\D/ and $ZOOVY::cgiv->{$attr};
				$stash->{'attributes'}->{$attr[2]} = {type=>$type, value=>[param($attr)]} if $attr[2] and $attr[2] =~ /^[\d]*$/ and $ZOOVY::cgiv->{$attr};
			 
				## if many checkboxes selected and there was Other:
				if (defined $stash->{'attributes'}->{$attr[1]} and ref $stash->{'attributes'}->{$attr[1]}{value} eq 'ARRAY') {
					for(my $i=0; $i< scalar @{$stash->{'attributes'}->{$attr[1]}{value}}; $i++) {
						$stash->{'attributes'}->{$attr[1]}{value}[$i] = &EBAY2::str_safe(param('other_'.$attr)) if $stash->{'attributes'}->{$attr[1]}{value}[$i] == -6;
					}	
				}

			}
		}
			
		if ($attr =~ /^cs_name(\d+)/) {
			## process custom specifics
			if($ZOOVY::cgiv->{'cs_value'.$1}) { 
				##if value not blank
				push @{ $stash->{'custom_specifics'}->{&EBAY2::str_safe($ZOOVY::cgiv->{$attr})} }, &EBAY2::str_safe($ZOOVY::cgiv->{'cs_value'.$1});
				}
			}
		}

	if ($ZOOVY::cgiv->{'attr2135_3803'}) {
		## return policy tick enabled - lets process
		$stash->{'ret_policy_attributes'}->{3803} = {type=>'ValueID', value=>$ZOOVY::cgiv->{'attr2135_3803'}};
		$stash->{'ret_policy_attributes'}->{3804} = {type=>'ValueID', value=>$ZOOVY::cgiv->{'attr2135_3804'}};
		$stash->{'ret_policy_attributes'}->{3805} = {type=>'ValueID', value=>$ZOOVY::cgiv->{'attr2135_3805'}};
		if ($ZOOVY::cgiv->{'attr_t2135_3806'}) {
			$stash->{'ret_policy_attributes'}->{3806} = {type=>'ValueLiteral', value=>&EBAY2::str_safe($ZOOVY::cgiv->{'attr_t2135_3806'})};
			}
		}

	##$stash->{xml} = 1;
	##render('item_xml.tt2');
	## build xml and execute VerifyAddItem to check that there were no errors
	my $item_xml = '';
	my $template = Template->new({ INCLUDE_PATH => $TEMPLATES_PATH });
	$template->process('item_xml.tt2', $stash, \$item_xml);
#	use Data::Dumper; open F, ">/tmp/ddd"; print F Dumper([param('attr1785_25662')]); close F;
#	open F, ">/tmp/chooser.dump";
#	print F $item_xml;
#	close F;

##COMMENTED BECAUSE OF NEW EBAY BUG - RETURNS ILLOGICAL ERROR - #174362	
#	my $api = new ebayAPI;
#	my $xml = $api->verifyAddItem($item_xml,$SITE);
#	if($xml !~ /An Error Occurred/) {
#	
#		my $parser = new XML::Parser (ErrorContext => 2, Style => "Tree");
#		my $xmlobj = new XML::SimpleObject ($parser->parse($xml));
#		if( $xmlobj->child('VerifyAddItemResponse')->child('Ack')->value eq 'Warning' ||
#				$xmlobj->child('VerifyAddItemResponse')->child('Ack')->value eq 'Failure' ) {
#			$stash->{'error'} = '<p>'.$xmlobj->child('VerifyAddItemResponse')->child('Errors')->child('ShortMessage')->value . '</p>';
#			$stash->{'error'} .= '<p>'.$xmlobj->child('VerifyAddItemResponse')->child('Errors')->child('LongMessage')->value . '</p>';
#			$stash->{'error'} .= '<p>Anyway, eBay Category was saved, only selected item specifics were not.</p>';
#
#			render('error.tt2');
#			} 
#		else {
			## OK, can save item specifics
			my $item_attributes_xml = '';
			## will contain both <AttributeSetArray>...</AttributeSetArray> and <ItemSpecifics>...</ItemSpecifics> sections - see template.
## ENCODE VALUES WITH &amp; etc. BHBH
#		foreach my $k (keys %{$stash}) {
#			$stash->{$k} = &ZTOOLKIT::encode($stash->{$k});
#			}
			$template->process('item_attributes_xml.tt2', $stash, \$item_attributes_xml);
			print STDERR "XML:$item_attributes_xml\n";
			if ($item_attributes_xml) {
				## EBAY::CREATE uses only ebay:attributeset, not ebay:attribute!!!
				my ($P) = PRODUCT->new($USERNAME,$SREF->{'PID'});
				$P->store('ebay:attributeset',$item_attributes_xml);
				$P->save();
				# ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:attributeset',$item_attributes_xml);
			}
				
			#$stash->{xml} = 1;
			#render('item_xml.tt2');
			render('saved.tt2');
	#		}
	#	} 
	#else {
	#	$stash->{'error'} = '<p>Error happened while making call to eBay. Sorry.</p>';
	#	$stash->{'error'} .= '<p>Anyway, eBay Category was saved, only selected item specifics were not.</p>';
	#	render('error.tt2');
	#	}
	}


##
## saves secondary category (ebay::category2, without item specifics)
sub save_secondary {
	if($ZOOVY::cgiv->{'secondary_category'}) {
		my $CATID = int($ZOOVY::cgiv->{'secondary_category'});
		my ($SITE) = &resolveSite( $CATID );
		if ($SITE>0) { $CATID = "$CATID.$SITE"; }	
		$stash->{'FRM'} = $SREF->{'FRM'};
		$stash->{'V'} = $SREF->{'V'};
		$stash->{'CATID'} = $SREF->{'CATID'}.(($SITE>0)?('.'.$SITE):'');	
		# &ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:category2', $CATID);
      my ($P) = PRODUCT->new($USERNAME,$SREF->{'PID'});
      $P->store('ebay:category2', $CATID);
      $P->save();
 
		# ZOOVY::saveproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:category2', $ZOOVY::cgiv->{'secondary_category'});
		render('saved.tt2');
		} 
	else {
		render('index.tt2');
		}
	}
## END ACTIONS
##

##
## Private Actions here
sub prepare_category_tree {
	my ($categories, $parent_categories, $selected_category);
	$selected_category->{id} = $stash->{selected_category}{id} if $stash->{selected_category};
	$selected_category->{id} = $ZOOVY::cgiv->{'id'} if int($ZOOVY::cgiv->{'id'});	

	if ($selected_category->{id}) {
		## extract this category with all children from db
		my $sth = $edbh->prepare("SELECT id, site, name, leaf, level, parent_id, item_specifics_enabled, product_search_page_available, catalog_enabled FROM ebay_categories WHERE id = ?") or die $edbh->errstr;
		$sth->execute($selected_category->{id}) or die $sth->errstr;
		my ($cat_id, $cat_site, $cat_name, $cat_leaf, $cat_level, $cat_parent_id, $cat_item_specifics_enabled, $cat_product_search_page_available, $cat_catalog_enabled) = $sth->fetchrow_array;
		$selected_category->{id} = $cat_id;
		$selected_category->{site} = $cat_site,
		$selected_category->{name} = $cat_name;
		$selected_category->{leaf} = $cat_leaf;
		$selected_category->{level} = $cat_level;
		$selected_category->{parent_id} = $cat_parent_id;
		$selected_category->{item_specifics_enabled} = $cat_item_specifics_enabled;
		$selected_category->{product_search_page_available} = $cat_product_search_page_available;
		$selected_category->{catalog_enabled} = $cat_catalog_enabled;
		my $sth1 = $edbh->prepare("SELECT count(id) FROM ebay_categories WHERE parent_id = $cat_id") or die $edbh->errstr;
		$sth1->execute or die $sth->errstr;
		$selected_category->{children_count} = $sth1->fetchrow_array;

		my $category = $selected_category;
		if($category) {
			my $sth = $edbh->prepare("SELECT id, site, name, leaf, item_specifics_enabled from ebay_categories where parent_id = $selected_category->{id} and id != parent_id") or die $edbh->errstr;
			#my $sth = $edbh->prepare("SELECT b.id, b.name, b.leaf, b.item_specifics_enabled ,count(b.id) FROM `ebay_categories` as a LEFT JOIN `ebay_categories` as b ON b.id=a.parent_id AND b.parent_id=$ZOOVY::cgiv->{id} GROUP BY b.id ORDER BY b.name") or die $edbh->errstr;
			$sth->execute or die $sth->errstr;
			while ( my ($cat_id, $cat_site, $cat_name, $cat_leaf, $cat_item_specifics_enabled) = $sth->fetchrow_array ) {
				my $cat = {};
				$cat->{id} = $cat_id;
				$cat->{site} = $cat_site;
				$cat->{name} = $cat_name;
				$cat->{leaf} = $cat_leaf;
				$cat->{item_specifics_enabled} = $cat_item_specifics_enabled;
				my $sth1 = $edbh->prepare("SELECT count(id) FROM ebay_categories WHERE parent_id = $cat_id") or die $edbh->errstr;
				$sth1->execute or die $sth->errstr;
				$cat->{children_count} = $sth1->fetchrow_array;
				push @$categories, $cat;
			}

			## get all parent categories
			push(@$parent_categories, $category) if $category->{level} != 1;
			my $parent_category;
			$sth = $edbh->prepare('SELECT id, site, name, leaf, item_specifics_enabled, level, parent_id from ebay_categories where id = '.$category->{parent_id}) or die $edbh->errstr;
			$sth->execute or die $sth->errstr;
			my ($cat_id, $cat_site, $cat_name, $cat_leaf, $cat_item_specifics_enabled, $cat_level, $cat_parent_id) = $sth->fetchrow_array;
			my $cat = {};
			$cat->{id} = $cat_id;
			$cat->{site} = $cat_site;
			$cat->{name} = $cat_name;
			$cat->{leaf} = $cat_leaf;
			$cat->{item_specifics_enabled} = $cat_item_specifics_enabled;
			$cat->{level} = $cat_level;
			$cat->{parent_id} = $cat_parent_id;
			my $sth1 = $edbh->prepare("SELECT count(id) FROM ebay_categories WHERE parent_id = $cat_id") or die $edbh->errstr;
			$sth1->execute or die $sth->errstr;
			$cat->{children_count} = $sth1->fetchrow_array;
			$parent_category = $cat;
			push(@$parent_categories, $parent_category);

			while($parent_category->{parent_id} != $parent_category->{id}) {
				$category = $parent_category;
				my $sth = $edbh->prepare('SELECT id, site, name, leaf, item_specifics_enabled, level, parent_id from ebay_categories where id = '.$category->{parent_id}) or die $edbh->errstr;
				$sth->execute or die $sth->errstr;
				my ($cat_id, $cat_site, $cat_name, $cat_leaf, $cat_item_specifics_enabled, $cat_level, $cat_parent_id) = $sth->fetchrow_array;
				my $cat = {};
				$cat->{id} = $cat_id;
				$cat->{site} = $cat_site;
				$cat->{name} = $cat_name;
				$cat->{leaf} = $cat_leaf;
				$cat->{item_specifics_enabled} = $cat_item_specifics_enabled;
				$cat->{level} = $cat_level;
				$cat->{parent_id} = $cat_parent_id;
				my $sth1 = $edbh->prepare("SELECT count(id) FROM ebay_categories WHERE parent_id = $cat_id") or die $edbh->errstr;
				$sth1->execute or die $sth->errstr;
				$cat->{children_count} = $sth1->fetchrow_array;
				$parent_category = $cat;
				push(@$parent_categories, $parent_category);
			}
		}
	} else { ## id not defined. extract root category
		#my $sth = $edbh->prepare('SELECT id, name, leaf, item_specifics_enabled from ebay_categories where level = 1') or die $edbh->errstr;
		my $sth = $edbh->prepare("SELECT id, site, name, leaf, item_specifics_enabled FROM `ebay_categories` where level=1 order by name") or die $edbh->errstr;
		$sth->execute or die $sth->errstr;
		while ( my ($cat_id, $cat_site, $cat_name, $cat_leaf, $cat_item_specifics_enabled) = $sth->fetchrow_array ) {
			my $cat = {};
			$cat->{id} = $cat_id;
			$cat->{site} = $cat_site;
			$cat->{name} = $cat_name;
			$cat->{leaf} = $cat_leaf;
			$cat->{item_specifics_enabled} = $cat_item_specifics_enabled;
			$cat->{children_count} = $eb2->get_children_count($cat_id);
			push @$categories, $cat;
		}
	}
	$stash->{'categories'} = $categories;
	$stash->{'parent_categories'} = $parent_categories;
	$stash->{'selected_category'} = $selected_category;
 
	1;
}

##
## prepare 'choose category specifics' form
sub prepare_cs_form {
	my $selected_category = $stash->{'selected_category'};
	$selected_category->{id} = $1 if $selected_category->{id} =~ /(\d+)\./;
	my $site = resolveSite($selected_category->{id});
	$stash->{site} = $site;

	my $pstmt = 'SELECT attribute_set_id FROM ebay_category_2_cs WHERE category_id = '.int($selected_category->{id});

	my $sth = $edbh->prepare($pstmt) or die $edbh->errstr;
	my $rv = $sth->execute or die $sth->errstr;
	my $attr_set_id = $sth->fetchrow_array;

	my $in_xml = "$PATH_TO_STATIC/xml/GetAttributesCS_AttributeData/$site/GetAttributesCS_".$attr_set_id."_AttributeData.xml";
	print STDERR "$PATH_TO_STATIC/xml/GetAttributesCS_AttributeData/$site/GetAttributesCS_".$attr_set_id."_AttributeData.xml\n";
	#my $in_xml = "/httpd/htdocs/biz/ebay/catchooser2008/xml/GetAttributesCS_AttributeData/GetAttributesCS_".$attr_set_id."_AttributeData.xml"; 
#	die($in_xml);
	
	if(-e $in_xml) {
		my $in_xml_data;
		open(F,$in_xml); $in_xml_data .= $_ while(<F>);	close(F); ## read XML
		$in_xml_data =~ s/<eBay>//;
		$in_xml_data =~ s/[^\0-\x80]//g; ## strip wide characters
		my $temp_file = mktemp('/tmp/ebayXXXXXX');
		open(F,">$temp_file");
	 # print F "<eBay><SelectedAttributes><AttributeSet id='$attr_set_id'/><AttributeSet id='2135'/></SelectedAttributes>", $in_xml_data;
		print F "<eBay><SelectedAttributes><AttributeSet id='$attr_set_id'/>";
		print F "<AttributeSet id='2135'/>" if $site == 0;
		print F "</SelectedAttributes>", $in_xml_data;
		# print F "<eBay><SelectedAttributes><AttributeSet id='$attr_set_id'/><AttributeSet id='2953'/></SelectedAttributes>", $in_xml_data;
		# print F "<eBay>", $in_xml_data;
		close(F);

		
		#my $specifics_html = `xalan -in $temp_file -xsl $PATH_TO_STATIC/xsl/syi_attributes.xsl`;
		my $specifics_html = `$XALAN $temp_file $PATH_TO_STATIC/xsl/syi_attributes.xsl`;
		#die $temp_file;
		`rm $temp_file`;
		
		$specifics_html = fix_dropdown_menus($specifics_html);
		$specifics_html =~ s/var formName = 'APIForm';/var formName = 'add-item-form';/g;
		$specifics_html =~ s/^.*?<form/<form/s;
		$specifics_html =~ s/<\/body>//;
		$specifics_html =~ s/<form.*?>//;
		$specifics_html =~ s/<\/form>//;
		$specifics_html =~ s/color="#000000"/color="#444"/g;
		$specifics_html =~ s/face="Arial, Helvetica, Sans-Serif"//g;
		$specifics_html =~ s/size="2"//g;
		$stash->{'specifics_html'} = $specifics_html;
		}
	$sth->finish();
	1;
}

##
## prepare search page form
sub prepare_sp_form {
	my $selected_category = $stash->{'selected_category'};
	my $sth = $edbh->prepare('SELECT attribute_set_id FROM ebay_category_2_cs WHERE category_id = '.$selected_category->{id}) or die $edbh->errstr;
	$sth->execute or die $sth->errstr;
	my $attribute_set_id = $sth->fetchrow_array;

	my $attributes = [];
	$sth = $edbh->prepare('SELECT ebay_attributes.id, ebay_attributes.name from ebay_attributes, ebay_attribute_set_2_attribute where ebay_attribute_set_2_attribute.attribute_id = ebay_attributes.id AND ebay_attribute_set_2_attribute.attribute_set_id = '.$attribute_set_id) or die $edbh->errstr;
	$sth->execute or die $sth->errstr;
	while ( my ($attr_id, $attr_name) = $sth->fetchrow_array ) {
		my $attr = {};
		$attr->{id} = $attr_id;
		$attr->{name} = $attr_name;
		push(@$attributes, $attr);
	}
	$stash->{'attributes'} = $attributes;
	$stash->{'attribute_set_id'} = $attribute_set_id;
	1;
}

##
## prepare product finder form
sub prepare_pf_form {
	my $selected_category = $stash->{'selected_category'};
	my $category_id = $selected_category->{id};
	#my $product_finder_id = $selected_category->category2pf->first->product_finder_id;
	my $sth = $edbh->prepare('SELECT ebay_product_finders.id FROM ebay_category_2_product_finder, ebay_product_finders WHERE ebay_product_finders.id = ebay_category_2_product_finder.product_finder_id AND ebay_category_2_product_finder.category_id = '.$selected_category->{id}) or die $edbh->errstr;
	$sth->execute or die $sth->errstr;
	my $product_finder_id = $sth->fetchrow_array;
	##prepare product finder form
	my $in_xml = "$PATH_TO_STATIC/xml/GetProductFinder_ProductFinderData/GetProductFinder_".$product_finder_id."_ProductFinderData.xml";
	if(-e $in_xml) {
		my $in_xml_data;
		open(F,$in_xml); $in_xml_data .= $_ while(<F>);	close(F); ## read XML
		$in_xml_data =~ s/[^\0-\x80]//g; ## strip wide characters
		my $temp_file = mktemp('/tmp/ebayXXXXXX');
		open(F,">$temp_file"); print F $in_xml_data; close(F);
		#my $html = `xalan -in $temp_file -xsl $PATH_TO_STATIC/xsl/product_finder.xsl`;
		my $html = `$XALAN $temp_file $PATH_TO_STATIC/xsl/product_finder.xsl`;
		$html =~ s/var formName = 'APIForm';/var formName = 'pf-form';/g;
		`rm $temp_file`;
		$html =~ s/<\/form>/<input type="hidden" id="category_id" name="id" value="$category_id" \/><\/form>/g;
		$html =~ s/action="PFPage"/action="\/biz\/ebay\/catchooser2008\/index.cgi\/get_product_search_results"/g;
		$html =~ s/id="tmppfform"/id="pf-form"/;
		$html =~ s/<form method="post"/<form method="post" id="pf-form"/;
		$stash->{'product_finder_html'} = $html;
	}
	1;
}

##
## prepare prefilled item specifics form
sub prepare_prefilled_cs_form {
	my $selected_category = $stash->{'selected_category'};
	my $product_id = $ZOOVY::cgiv->{'product_id'};
	my $attribute_set_id = $ZOOVY::cgiv->{'attribute_set_id'};

	my $api = new ebayAPI;
	my $xml = $api->getProductSellingPages($product_id, $attribute_set_id);

	if($xml !~ /An Error Occurred/) {
		my $parser = new XML::Parser (ErrorContext => 2, Style => "Tree");
		my $xmlobj = new XML::SimpleObject ($parser->parse($xml));

		## parse response
		$xml = $xmlobj->child('GetProductSellingPagesResponse')->child('ProductSellingPagesData')->value;
		$xmlobj = new XML::SimpleObject ($parser->parse($xml));
		$stash->{'product_title'} = $xmlobj->child('Products')->child('Product')->child('ProductInfo')->child('Title')->value;
		$xml =~ s/.*?<Attributes>/<Attributes>/sm;
		$xml =~ s/<\/Product>\n//;
		$xml =~ s/<\/Products>/<\/eBay>/;
		$xml = "<eBay><SelectedAttributes><AttributeSet id='$attribute_set_id'/><AttributeSet id='2135'/></SelectedAttributes>" . $xml;

		## apply xsl
		my $temp_file = mktemp('/tmp/ebayXXXXXX');
		$xml =~ s/[^\0-\x80]//g; ## strip wide characters
		open F, ">$temp_file"; print F $xml; close F;
		#my $specifics_html = `xalan -in $temp_file -xsl $PATH_TO_STATIC/xsl/syi_attributes.xsl`;
		my $specifics_html = `$XALAN $temp_file $PATH_TO_STATIC/xsl/syi_attributes.xsl`;
		`rm $temp_file`;
		$specifics_html = fix_dropdown_menus($specifics_html);
		$specifics_html =~ s/var formName = 'APIForm';/var formName = 'add-item-form';/g;
		$specifics_html =~ s/^.*?<form/<form/s;
		$specifics_html =~ s/<\/body>//;
		$specifics_html =~ s/<form.*?>//;
		$specifics_html =~ s/<\/form>//;
		$specifics_html =~ s/color="#000000"/color="#444"/g;
		$specifics_html =~ s/face="Arial, Helvetica, Sans-Serif"//g;
		$specifics_html =~ s/size="2"//g;
		$stash->{'specifics_html'} = $specifics_html;
		$stash->{'product_id'} = $product_id;
		} 
	else {
		$stash->{'error'} = 'Prefilled Attributes Form - cannot make call to eBay';
		}
	1;
	}
	
	
sub resolveSite {
	my ($category) = @_;
	
	my $edbh = &DBINFO::db_user_connect($USERNAME);
	my $pstmt = "select site from ebay_categories where id=".int($category);
	my $sth = $edbh->prepare($pstmt);
	$sth->execute();
	my ($SITE) = $sth->fetchrow();
	$sth->finish();
	&DBINFO::db_user_close();
	return($SITE);
	}
	


## makes ugly eBay dropdown menus javascript work.
sub fix_dropdown_menus {
	my $html = shift;

	## disable form autosubmit on dropdown change
	$html =~ s/(aus_form\.submit\(\);)/\/\/$1/g;
	$html =~ s/(document\.forms\[formName\]\.submit\(\);)/\/\/$1/;
	## fix dropdown
 # my $search_str = qr/<select\sonChange="aus_set_parent\('.*?',1\);api_check_on_other\('.*?',this\.value\);"\sname="(.*?)"/;
 # my $replace_template = qq/<select onChange="aus_set_parent('$1',1);api_check_on_other('$1',this.value);aus_init_cascades('$1',1);display_input_for_other(this,'$1', this.value);"/;
 # my $search_str1 = qr/<select\sonChange="api_check_on_other\('.*?',this\.value\);"/;
 # my $replace_template1 = qq/<select onChange="api_check_on_other('xxxxxx',this.value);display_input_for_other(this,'xxxxxx', this.value);"/;
	#$html =~ /aus_init_cascades\("(.*?)",1\);/;
	#my $par = $1;
	#$replace_template =~ s/xxxxxx/$par/g;
	#$replace_template1 =~ s/xxxxxx/$par/g;
	#$html =~ s/$search_str/$replace_template/g;
	#$html =~ s/$search_str1/$replace_template1/g;

	## fix dropdown behaviour - some dropdowns depend on other ones, becoming active/inactive
	## $1 contains attr id (=select name="...") - must be passed into js functions.
	$html =~ s/<select\sonChange="aus_set_parent\('.*?',1\);api_check_on_other\('.*?',this\.value\);"\sname="(.*?)"/<!-- select:$1 --><select id="$1" onChange="aus_set_parent('$1',1);api_check_on_other('$1',this.value);aus_init_cascades('$1',1);display_input_for_other(this,'$1', this.value);" name="$1"/g;
	
	## when user selects 'other' option - we show him input to enter that other (eBay doesn't provide)
	$html =~ s/<select\sonChange="api_check_on_other\('.*?',this\.value\);"\sname="(.*?)"/<select onChange="api_check_on_other('$1',this.value);display_input_for_other(this,'$1', this.value);" name="$1"/g;

	$html =~ s/<input\stype="checkbox"\svalue="-6"\sonClick="api_check_on_other\('.*?',-6\);"\sname="(.*?)"/<input type="checkbox" value="-6" onChange="api_check_on_other('$1',-1);display_input_for_other(this,'$1',-6);" name="$1"/g;

	## we need to get a list of select id's
	#foreach my $id (split(/\<\!-- (select:.*?) -->/,$html)) {
	#	next if ($id !~ /^select:(.*?)$/);
	#	# $html .= qq~<script>alert("$1");</script>~;
	#	$html .= qq~<script>
	#	aus_set_parent('$1',1);
	#	api_check_on_other('$1',document.forms["add-item-form"].$1.value);
	#	aus_init_cascades('$1',1);
	#	// document.forms["add-item-form"].$1.onchange();
	#	</script>~;
	#	}


	return $html;
	}



##
##
## gets saved ebay:attributeset and tries to restore it if user wants to review
## brrrrr, thats parsing eBay-only-readable data
sub restore_cs_form {

	my ($P) = PRODUCT->new($USERNAME,$SREF->{'PID'},'create'=>0);
	#my $ebay_category = &ZOOVY::fetchproduct_attrib($USERNAME,$SREF->{'PID'},$SREF->{'V'});
	#my $ebay_attributeset = &ZOOVY::fetchproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:attributeset');
	#my $ext_pid_type = &ZOOVY::fetchproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_type');
	#my $ext_pid_value = &ZOOVY::fetchproduct_attrib($USERNAME,$SREF->{'PID'},'ebay:ext_pid_value');	
	my $ebay_category = $P->fetch( $SREF->{'V'} );
	my $ebay_attributeset = $P->fetch('ebay:attributeset');
	my $ext_pid_type = $P->fetch('ebay:ext_pid_type');
	my $ext_pid_value = $P->fetch('ebay:ext_pid_value');

	## earlier we saved specs wrapped with <Attributes></Attributes>
	## now we save <AttributeSetArray></AttributeSetArray>, ready to pass to ebay
	if ($ebay_attributeset =~ /Attributes/) {
		## old format, <Attributes> should be <AttributeSetArray> .. plus other changes, not sure,
		## we'll blank it and see if somebody complains.
		$ebay_attributeset = '';	
		}

	if ($ebay_category and $ebay_attributeset and $ebay_attributeset =~ /<AttributeSetArray>/) {
		$ebay_attributeset =~ s/&(?!amp;|lt;|gt;)/&amp;/g; ## replace unescaped & with &amp;, but dont touch &lt;, &gt;, &amp;
		$ebay_attributeset =~ s/(<AttributeSetArray>.*?<\/AttributeSetArray>)(.*)/$1/s;
		my $custom_specifics = $2;
		# $ebay_attributeset =~ s/>[\s]+</></gs;  # this fixes purewave.

		my $ref = XML::Simple::XMLin($ebay_attributeset,ForceArray=>1);
		my $cs = {};
		foreach my $AttributeSet (@{$ref->{'AttributeSet'}}) {
			my $attributeSetID = $AttributeSet->{'attributeSetID'};
			$cs->{$attributeSetID} = {};
			foreach my $Attribute (@{$AttributeSet->{'Attribute'}}) {
				my $attributeID = $Attribute->{'attributeID'};
				$cs->{$attributeSetID}{$attributeID} = [];
				foreach my $Value (@{$Attribute->{'Value'}}) {
					my $ValueID = $Value->{'ValueID'}->[0];
					push @{$cs->{$attributeSetID}->{$attributeID}}, $ValueID;
					}
				}
			}
		$stash->{cs} = $cs;



#		my $xml_parser = new XML::Parser(Style => 'Tree');
#		my $ref = $xml_parser->parse($ebay_attributeset);
#		$ref = $ref->[1];
#
#		print STDERR Dumper($ref);
#
#		my $cs = {};
#		for(my $i=3; $i < scalar @$ref; $i+=4) {
#			## parse AttributeSets
#			my $attributeSetID = $ref->[$i+1][0]{attributeSetID} if defined $ref->[$i+1][0]{attributeSetID};
#			$attributeSetID = $ref->[$i+1][0]{id} if defined $ref->[$i+1][0]{id};
#			$cs->{$attributeSetID} = {};
#			for(my $j=3; $j < scalar @{$ref->[$i+1]}; $j+=4) {
#				## parse AttributeIDs
#				my $attributeID = $ref->[$i+1][$j+1][0]{attributeID} if defined $ref->[$i+1][$j+1][0]{attributeID};
#				$attributeID = $ref->[$i+1][$j+1][0]{id} if defined $ref->[$i+1][$j+1][0]{id};	
#				$cs->{$attributeSetID}{$attributeID} = [];
#				for(my $k=3; $k < scalar @{$ref->[$i+1][$j+1]}; $k+=4) {
#					## parse Values
#					if(!$new_format) {
#						push @{$cs->{$attributeSetID}{$attributeID}},$ref->[$i+1][$j+1][$k+1][4][0]{id} if defined $ref->[$i+1][$j+1][$k+1][4][0]{id};
#						push @{$cs->{$attributeSetID}{$attributeID}},$ref->[$i+1][$j+1][$k+1][4][4][2] if defined $ref->[$i+1][$j+1][$k+1][4][4][2];
#					} else {
#						push @{$cs->{$attributeSetID}{$attributeID}},$ref->[$i+1][$j+1][$k+1][4][2];
#					}
#				}
#			}
#		}
#		$stash->{cs} = $cs;


		## user defuned specs (that blue + button - add custom detail - in cs form)
		if($custom_specifics and $custom_specifics =~ /ItemSpecifics/) {
			my $xml_parser = new XML::Parser(Style => 'Tree');
			my $ref = $xml_parser->parse($ebay_attributeset);
			$custom_specifics =~ s/.*?(<ItemSpecifics>.*?<\/ItemSpecifics>).*/$1/s;
			$ref = $xml_parser->parse($custom_specifics);
			$ref = $ref->[1];
			$stash->{cs1} = {};
			for(my $i=3; $i < scalar @$ref; $i+=4) {
				## parse NameValueLists
				$stash->{cs1}{$ref->[$i+1][4][2]} = $ref->[$i+1][8][2];
				}
			}

		
		#print Dumper($ref);
		#print Dumper($cs);
		if ($stash->{is_media_cat}) {
			$stash->{ext_pid_type} = $ext_pid_type;
			$stash->{ext_pid_value} = $ext_pid_value;
			}
		}

	}

## Private Actions END
##

## Dispatcher
##
sub dispatch {

	## each of the various actions which can be requested.
	$dispatch->{'index'} = \&index;
	$dispatch->{'logout'} = \&logout;
	$dispatch->{'get_categories'} = \&get_categories;
	$dispatch->{'get_suggested_categories'} = \&get_suggested_categories;
	$dispatch->{'describe_item'} = \&describe_item;
	$dispatch->{'show_sp_pf_form'} = \&show_sp_pf_form;
	$dispatch->{'show_sp_form'} = \&show_sp_form;
	$dispatch->{'show_pf_form'} = \&show_pf_form;
	$dispatch->{'get_product_search_results'} = \&get_product_search_results;
	$dispatch->{'get_product_selling_pages'} = \&get_product_selling_pages;
	$dispatch->{'add_item'} = \&add_item;
	$dispatch->{'save_secondary'} = \&save_secondary;

	if ((defined $action) and (defined $dispatch->{$action})) {
		$dispatch->{$action}->();
		} 
	else {
		## always default back to index
		$dispatch->{'index'}->();
		}
		
	}

