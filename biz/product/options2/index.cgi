#!/usr/bin/perl

use URI::Escape qw (uri_escape);
use Data::Dumper;
use Digest::MD5;
use strict;
use lib "/httpd/modules";
require ZOOVY;
require GTOOLS;
require ZTOOLKIT;
require POGS;
require AMAZON3;
require ZWEBSITE;
require LUSER;
require PRODUCT;

my @MSGS = ();


my ($LU) = LUSER->authenticate('flags'=>'_P&2');
my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();

#use Data::Dumper;
#print STDERR Dumper($ZOOVY::cgiv,$LU,$USERNAME,$LUSERNAME);


my $PRODUCT = $ZOOVY::cgiv->{'PRODUCT'};
if (not defined $PRODUCT) { 
	$PRODUCT = $ZOOVY::cgiv->{'product'}; 
	}
# my $prodref = &ZOOVY::fetchproduct_as_hashref($USERNAME,$PRODUCT);
my $P = undef;
if ($PRODUCT ne '') { ($P) = PRODUCT->new($LU,$PRODUCT); }
if (not defined $P) {
	}

if (($USERNAME ne '') && ($ZOOVY::cgiv->{'MODE'} eq 'TOKEN')) {
	## IN TOKEN MODE, YOU PASS:
	##		MD5(TS + TOKEN)   and TS and CLIENT (which is the one the token was issued for)
	##
	my $CONTENT = $ZOOVY::cgiv->{'CONTENT'};
	if ($CONTENT =~ /<PRODUCT(.*?)>(.*?)<\/PRODUCT>/s) {
		my $TMP = $1;
		my $hashref = &ZOOVY::attrib_handler_ref($2);
		if ($TMP =~ / NAME="(.*?)"/) { $PRODUCT = $1; }

		# print STDERR Dumper($hashref);

		foreach my $k (keys %{$hashref}) {
			$P->store($k,$hashref->{$k});
			# &ZOOVY::saveproduct_attrib($USERNAME,$PRODUCT,$k,$hashref->{$k});
			}
		$P->save();
		}
	}


my $DEBUG = 0;
my $template_file = '';



$GTOOLS::TAG{'<!-- MODE -->'} = '';

## This is a normal session, just process the login.
if ((not defined $USERNAME) || ($USERNAME eq '')) {
	warn "USERNAME NOT SET\n";
	print "Content-type: text/plain\n\n";
	print "USERNAME not set.\n";
	exit; 
	}




my $VERB = $ZOOVY::cgiv->{'VERB'};
print STDERR "VERB: $VERB\n";
$GTOOLS::TAG{'<!-- POG -->'} = $ZOOVY::cgiv->{'POG'};
$GTOOLS::TAG{'<!-- SOG -->'} = $ZOOVY::cgiv->{'SOG'};
$GTOOLS::TAG{'<!-- TS -->'} = $ZOOVY::cgiv->{'TS'};
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
my $SOGID = '';

## moves a POG (designed by CGI param POG) up one position
if ($VERB eq 'PROMOTE' || $VERB eq 'DEMOTE') {
	my $CODE = $ZOOVY::cgiv->{'POG'};
	# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
	my @pogs2 = @{$P->fetch_pogs()};
	# my $pogstr = $prodref->{'zoovy:pogs'};
	# &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs');
	# my @pogs = &POGS::text_to_struct($USERNAME,$pogstr,0);
	my $pos = -1; my $count = 0;
	foreach my $pog (@pogs2) {
		if ($pog->{'id'} eq $CODE) { $pos = $count; }
		$count++;
		}
	## SANITY: at this point $pos is -1 if failure occurred, 
	## 			or the position in the @pogs array for the item we should promote/demote
	if (($VERB eq 'DEMOTE') && ($pos<$count)) {
		my $tmp = $pogs2[$pos+1]; $pogs2[$pos+1] = $pogs2[$pos]; $pogs2[$pos] = $tmp; 
		}
	elsif (($VERB eq 'PROMOTE') && ($pos>0)) {
		my $tmp = $pogs2[$pos-1]; $pogs2[$pos-1] = $pogs2[$pos]; $pogs2[$pos] = $tmp; 
		}
	# &POGS::store_pogs($LU,$PRODUCT,$prodref,\@pogs2);
	$P->store_pogs(\@pogs2); 
	$P->save();
	$VERB = '';
	}



if ($VERB eq 'COPYSWOG') {
	&POGS::import_swog($USERNAME,$ZOOVY::cgiv->{'ID'});
	$VERB = '';
	}


## Associates a SOG to the current product
if ($VERB eq 'ADDSOG') {
	# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
	my @pogs2 = ();
	if ( (defined $P) && (defined $P->fetch_pogs()) ) {
		@pogs2 = @{$P->fetch_pogs()};
		}
	#my $pogstr = $prodref->{'zoovy:pogs'}; 
	## &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs');
	#my @pogs = &POGS::text_to_struct($USERNAME,$pogstr,0);

	my $ERROR = 0;
	my $ID = $ZOOVY::cgiv->{'SOG'};
	my $INVCOUNT = 0;
	foreach my $pog (@pogs2) {
		if ($pog->{'inv'}>0) { $INVCOUNT++; }
		if ($pog->{'id'} eq $ID) {
			$ERROR++;
			$GTOOLS::TAG{'<!-- OUTPUT -->'} = '<br><b><font color="red">Sorry, the store option group '.$ID.' is already associated!</font></b><br>'; 
			}
		}

	if (not $ERROR) {
		## now we load the SOG struct into memory so we can figure out if it's inventoriable
		# my @sog = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$ID,$NAME));
		my ($sog) = &POGS::load_sogref($USERNAME,$ID);

		## now we add a stub POG as text
		my %pog = %{$sog};
		if (defined $pog{'@options'}) {
			delete $pog{'@options'};
			}

		if (($pog{'inv'}>0) && ($INVCOUNT>=3)) { 
			$ERROR++;
			$GTOOLS::TAG{'<!-- OUTPUT -->'} = "<div class='error'>ERROR: You may have a maximum of 3 inventoriable option groups per product.</div>"; 
			}
		
		if (not $ERROR) {
			## load the POG back into memory as an array.
			# my @pog = &POGS::text_to_struct($USERNAME,$output,1);

			## now, if this is global.. we need to re-import it without any options
			if ($sog->{'global'}) { %pog = %{$sog}; } 
			$pog{'id'} = $ID;
			$pog{'sog'} = $ID;
			push @pogs2, \%pog;

			# &POGS::store_pogs($LU,$PRODUCT,$prodref,\@pogs2);
			$P->store_pogs(\@pogs2); 
			open F, ">/tmp/foozzz";
			print F Dumper($P);
			close F;
			$P->save();
			}
		}
	$VERB = '';
	}


##
##
##

if ($VERB eq 'SAVE-CREATEPOG' || $VERB eq 'SAVE-CREATESOG') {
	## NOTE: if we encounter an error we simply reset VERB to "CREATE"
	my $TYPE = $ZOOVY::cgiv->{'TYPE'};
	my $ERROR = 0;

	if (length($ZOOVY::cgiv->{'PROMPT'})<4) {
		$ERROR++;
		$GTOOLS::TAG{'<!-- PROMPT_ERROR -->'} = "<div class='error'>ERROR: Prompt is a required field and cannot be left blank.</div><br>";
		}
	
	my %og = ();
	$og{'prompt'} = $ZOOVY::cgiv->{'PROMPT'};
		
	$og{'type'} = $TYPE;
	if (defined $ZOOVY::cgiv->{'FINDER'}) { 
		$og{'inv'} = 0;
		$og{'global'} = 0;
		$og{'type'} = 'attribs';
		}
	else {
		if ($ZOOVY::cgiv->{'ASSEMBLY'}) { $ZOOVY::cgiv->{'INV'} += 2; }
		if (defined $ZOOVY::cgiv->{'INV'}) { $og{'inv'} = int($ZOOVY::cgiv->{'INV'}); }
		if (defined $ZOOVY::cgiv->{'GLOBAL'}) { $og{'global'} = int($ZOOVY::cgiv->{'GLOBAL'}); }
		}
		
	if (defined $ZOOVY::cgiv->{'AMZ'}) { $og{'amz'} = $ZOOVY::cgiv->{'AMZ'}; }
	if (defined $ZOOVY::cgiv->{'GOO'}) { $og{'goo'} = $ZOOVY::cgiv->{'GOO'}; }
	if (defined $ZOOVY::cgiv->{'EBAY'}) { $og{'ebay'} = $ZOOVY::cgiv->{'EBAY'}; }

	if ($TYPE eq 'text') {
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with text fields.</div><br>"; }
#		print STDERR "$output\n";
		}
	elsif ($TYPE eq 'cb') {		
		$og{'@options'} = [ { v=>'NO', 'prompt'=>'Not Checked' }, { 'v'=>'ON', 'prompt'=>'Checked' } ];
		}
	## HIDDEN
	elsif ($TYPE eq 'hidden') {
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with text fields.</div><br>"; }
		}
	## FINDER
	elsif ($TYPE eq 'attribs') {
		}	
	elsif ($TYPE eq 'assembly') {
		}	
	elsif ($TYPE eq 'select') {
		}
	elsif ($TYPE eq 'radio') {
		}
	elsif ($TYPE eq 'textarea') {
		$og{'cols'} = 80;
		$og{'rows'} = 3;
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with textarea fields.</div><br>"; }
		}
	elsif ($TYPE eq 'number') {
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with number fields.</div><br>"; }
		}
	elsif ($TYPE eq 'biglist') {
		}
	elsif ($TYPE eq 'imgselect') {
		$og{'width'} = 75;
		$og{'height'} = 75;
		$og{'zoom'} = 1;
		$og{'img_type'} = 'sku_image';
		}
	elsif ($TYPE eq 'imggrid') {
		$og{'width'} = 50;
		$og{'height'} = 50;
		$og{'zoom'} = 1;
		$og{'cols'} = 8;
		$og{'img_type'} = 'sku_image';
		}
	elsif ($TYPE eq 'calendar') {
		$og{'flags'} = 255;
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with calendar fields.</div><br>"; }
		}
	elsif ($TYPE eq 'readonly') {
		$og{'default'} = 'Type your Text/Instructions Here!';
		if ($og{'inv'}>0) { $ERROR++; $GTOOLS::TAG{'<!-- INV_ERROR -->'} = "<div class='error'>ERROR: Inventory cannot be used with readonly fields.</div><br>"; }
		}
	else { 
		$og{'type'} = "ERROR.$TYPE";
		$ERROR++;
		$GTOOLS::TAG{'<!-- ERROR -->'} = "<div class='error'>ERROR: Unknown type: $TYPE</div><br>";
		}


	## if we are creating a SOG
	if ($VERB eq 'SAVE-CREATESOG') {
		#my $listref = &POGS::list_sogs($USERNAME);
		#foreach my $k (keys %{$listref}) {
		#	if ($listref->{$k} eq $SOGNAME) {
		#		$ERROR++;
		#		$GTOOLS::TAG{'<!-- ERROR -->'} = "<div class='error'>A SOG named $SOGNAME already exists [ID=$k].</div><br>";
		#		}
		#	}
		if ($ERROR) {
			$VERB = 'CREATESOG';
			}
		else {
			## SOGS are so simple
			my ($sog) = &POGS::store_sog($USERNAME,\%og,'new'=>1);
			$VERB = 'EDITSOG';
			}
		}

	## if we didn't have an error we ALWAYS save PRODUCT
	if ($VERB eq 'SAVE-CREATEPOG') {
		# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		my @pogs2 = ();
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
		#my $pogstr = $prodref->{'zoovy:pogs'};
		### step2: parse the pogs into memory
		#my @pogs = &POGS::text_to_struct($USERNAME,$pogstr,0);

		my $INVCOUNT = 0;
		foreach my $pog (@pogs2) {
			if ($pog->{'inv'}>0) { $INVCOUNT++; }
			if ($pog->{'iname'} eq $ZOOVY::cgiv->{'INAME'}) {
				## INAME is a unique identifier (this probably ought to a guid, currently it's a timestamp)(
				$ERROR++;
				$GTOOLS::TAG{'<!-- ERROR -->'} = "<div class='error'>A POG iname=[$ZOOVY::cgiv->{'INAME'}] already exists [ID=$pog->{'id'}] - cannot create another one! (hint: you probably just pressed refresh on the browser)</div><br>";
				}
			}

		if (($og{'inv'}>0) && ($INVCOUNT>=3)) {
			$ERROR++;
			$GTOOLS::TAG{'<!-- ERROR -->'} = "<div class='error'>A single product may not have more than 3 inventoriable option groups associated with it.</div><br>";
			}

		if ($ERROR) {
			$VERB = 'CREATEPOG';
			}
		else {
			## POGS aren't as simple! 
			## step1: load the pogs from the product.
			## step4: load the new POG into memory, and set the ID to the next ID
			# my @pog = &POGS::text_to_struct($USERNAME,$output,1);
#			print STDERR Dumper(\@pog);
			$og{'id'} = &POGS::find_next_available_pog_id(\@pogs2);
			$og{'iname'} = $ZOOVY::cgiv->{'INAME'};
			$ZOOVY::cgiv->{'POG'} = $og{'id'};


			## step5: push the option to the end of the product.
			push @pogs2, \%og;
			# push @pogs, $pog[0];

			## step6: store the pogs back into the product.
			# &POGS::store_pogs($LU,$PRODUCT,$prodref,\@pogs2);
			$P->store_pogs(\@pogs2); 
			$P->save();
			$VERB = 'EDITPOG';
			}
		}
	}


#######################################
if ($VERB eq 'SAVEPOG') {
	my $POGID = $ZOOVY::cgiv->{'POG'};
	my $SOGID = $ZOOVY::cgiv->{'SOG'};
	my @pogs2 = ();
	my $psog = undef;

	if ($POGID) {
		# @pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},0);
		## &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs'),0);
		# @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
		$psog = &POGS::find_pog_in_pogs(\@pogs2,$POGID);
		$psog->{'id'} = $POGID;
		}
	if ($SOGID) {
		# @pogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$SOGID));
		# $psog = $psogs[0];
		$psog = &POGS::load_sogref($USERNAME,$SOGID);
		$psog->{'id'} = $SOGID;
		}

	$psog->{'v'} = 2;		## version#
	if (defined $ZOOVY::cgiv->{'PROMPT'}) { $psog->{'prompt'} = $ZOOVY::cgiv->{'PROMPT'}; }
	if (defined $ZOOVY::cgiv->{'INV'}) { $psog->{'inv'} = $ZOOVY::cgiv->{'INV'}; }
	if (defined $ZOOVY::cgiv->{'GLOBAL'}) { $psog->{'global'} = $ZOOVY::cgiv->{'GLOBAL'}; }
	if (defined $ZOOVY::cgiv->{'OGHINT'}) { $psog->{'oghint'} = $ZOOVY::cgiv->{'OGHINT'}; }
	## META is used by designers to hint how options should be displayed.
	if (defined $ZOOVY::cgiv->{'META'}) { $psog->{'meta'} = $ZOOVY::cgiv->{'META'}; }
	if (defined $ZOOVY::cgiv->{'AMZ'}) { $psog->{'amz'} = $ZOOVY::cgiv->{'AMZ'}; }
	if (defined $ZOOVY::cgiv->{'GOO'}) { $psog->{'goo'} = $ZOOVY::cgiv->{'GOO'}; }
	if (defined $ZOOVY::cgiv->{'EBAY'}) { $psog->{'ebay'} = $ZOOVY::cgiv->{'EBAY'}; }
	if (defined $ZOOVY::cgiv->{'GHINT'}) { $psog->{'ghint'} = $ZOOVY::cgiv->{'GHINT'};  }
		
	delete $psog->{'optional'};
	if ($psog->{'inv'}==0) {
		## optional is only available for non-inventoriable options.
		$psog->{'optional'} = (defined $ZOOVY::cgiv->{'optional'})?1:0; 	
		}

	if ($psog->{'type'} eq 'imgselect' || $psog->{'type'} eq 'imggrid') {
		$psog->{'width'} = $ZOOVY::cgiv->{'WIDTH'};
		$psog->{'height'} = $ZOOVY::cgiv->{'HEIGHT'};
		$psog->{'zoom'} = $ZOOVY::cgiv->{'ZOOM'};
		$psog->{'img_type'} = $ZOOVY::cgiv->{'IMG_TYPE'};
		if ($psog->{'type'} eq 'imggrid') {
			$psog->{'cols'} = $ZOOVY::cgiv->{'COLS'};
			}
		}

	if ($psog->{'type'} eq 'calendar') {
		$psog->{'flags'} = 0;
		$psog->{'fee_rush'} = sprintf("%.2f",$ZOOVY::cgiv->{'FEE_RUSH'});
		$psog->{'rush_msg'} = $ZOOVY::cgiv->{'RUSH_MSG'};
		$psog->{'rush_prompt'} = $ZOOVY::cgiv->{'RUSH_PROMPT'};
		$psog->{'rush_days'} = int($ZOOVY::cgiv->{'RUSH_DAYS'});
		}

#	if ($psog->{'type'} eq 'attribs') {
#		$psog->{'lookup_attrib'} = $ZOOVY::cgiv->{'LOOKUP_ATTRIB'};
#		}

	if ($psog->{'type'} eq 'assembly') {
		$psog->{'inv'} = $psog->{'inv'} | 2;	## has inventoriable options
		$psog->{'assembly'} = $ZOOVY::cgiv->{'ASSEMBLY'};
		}

	if ($psog->{'type'} eq 'text' || $psog->{'type'} eq 'textarea' || $psog->{'type'} eq 'number' 
			|| $psog->{'type'} eq 'readonly' || $psog->{'type'} eq 'hidden') {
		$psog->{'default'} = $ZOOVY::cgiv->{'DEFAULT'};
		$psog->{'maxlength'} = $ZOOVY::cgiv->{'MAXLENGTH'};
		if ($psog->{'type'} eq 'textarea') {
			$psog->{'cols'} = $ZOOVY::cgiv->{'COLS'};
			$psog->{'rows'} = $ZOOVY::cgiv->{'ROWS'};
			}
		if ($psog->{'type'} eq 'number') {
			$psog->{'min'} = $ZOOVY::cgiv->{'MIN'};
			$psog->{'max'} = $ZOOVY::cgiv->{'MAX'};
			}
		else {
			$psog->{'fee_line'} = sprintf("%.2f",$ZOOVY::cgiv->{'FEE_LINE'});
			$psog->{'fee_word'} = sprintf("%.2f",$ZOOVY::cgiv->{'FEE_WORD'});
			$psog->{'fee_char'} = sprintf("%.2f",$ZOOVY::cgiv->{'FEE_CHAR'});
			}
		}
	$psog->{'@options'} = [];

	my %ids = ();	# tracks id's already in use!
	my @needid = ();
	print STDERR "LISTORDER: $ZOOVY::cgiv->{'listorder'}\n";
	foreach my $kvs (split(/[\n\r]+/,$ZOOVY::cgiv->{'listorder'})) {
		my %opt = ();
		foreach my $kvss (split(/\|/,$kvs)) {
#			print STDERR "kvs: $kvs KVSS: $kvss\n";
			my ($k,$v) = split(/=/,$kvss,2);
			if ($v eq '') { }
			elsif ($k eq 'id') {
				## note: I'm not sure 'id' is even used anymore, it seems like it's passed as 'v' now but
				## i'm keeping this just for compatibility.
				if (length($v)==2) {
					$opt{'v'} = uc($v); 
					}
				}
			elsif ($k eq 'pt') { $opt{'prompt'} = $v; }	 #this is a cheap hack, probalby should remove it.
			elsif ($k eq 'html') { $opt{'html'} = $v; }
			# v, w, p, etc.
			else { $opt{$k} = $v; }
			}
		push @{$psog->{'@options'}}, \%opt;
		## NOTE: remember that needid contains a ref to the same data structure as $psog->{'options'} 
		## this means we can recurse @needid later and change $psog->{'options'} - if you don't understand this, don't muck with it!
		if ($opt{'v'} eq '') { 
			## v not set, we'll allocate one!
			push @needid, \%opt; 
			}
		elsif (defined $ids{uc($opt{'v'})}) {
			## v already used by another option, we'll redefine this.
			$opt{'v'} = '';
			push @needid, \%opt; 
			}
		elsif ($opt{'v'} ne '') {
			## v is set, not blank, and the 'v' should not (and has not) appeared on another option.
			$ids{uc($opt{'v'})}++; 
			}
		else {
			die("never reached!");
			}
		}
#	print STDERR "NEED ID: ".Dumper(\@needid)."\n";
	
	if ($psog->{'type'} eq 'biglist') {
		foreach my $line (split(/[\n\r]+/,$ZOOVY::cgiv->{'biglist_contents'})) {
#			print STDERR "LINE: $line\n";
			next if ($line eq '');
			my %opt = ();
			my ($opt1,$opt2) = split(/\|/,$line);
			$opt{'m'} = '';
			$opt{'prompt'} = "$opt1|$opt2";
			push @{$psog->{'@options'}}, \%opt;
			push @needid, \%opt;			# needid is simply a reference into @{$psog->{'options'}} for options which need values!
			}

		if (($POGID) && ($psog->{'global'})) {
			push @MSGS, "WARN|Attempting to update POG:$POGID when biglist references global list - changes were discarded.";
			delete $psog->{'@options'};	## these should NEVER be stored in the product
			}
		}

#	print STDERR Dumper(\@needid);

	## assign ID's to any option that doesn't have one!
	my $counter = -1;
	foreach my $opt (@needid) {
		while (defined $ids{ &POGS::base36( ++$counter) }) {
			## do nothing!
			};
		$opt->{'v'} = &POGS::base36($counter);
		$ids{ &POGS::base36($counter) }++;
		}

	# print "Content-type: text/html\n\n"; print "<pre>".&ZOOVY::incode(Dumper([$SOGID,$POGID]))."</pre>"; exit;
	if ($POGID) {
		$P->store_pogs(\@pogs2); 
		$P->save();
		}

	if ($SOGID) {
		&POGS::store_sog($USERNAME,$psog,'new'=>0);
		}

	$VERB = '';
	}




#######################################
if ($VERB eq 'KILLPOG') {
	my $POGID = $ZOOVY::cgiv->{'POG'};
	my $SOGID = $ZOOVY::cgiv->{'SOG'};

	if ($POGID) {
		# my @pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},0);
		# &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs'),0);
		# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		my @pogs2 = ();
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
		my @new2 = ();
		for (my $x = 0; $x < scalar(@pogs2); $x++) {
			if ($pogs2[$x]->{'id'} ne $POGID) { push @new2, $pogs2[$x]; }
			}
		# &POGS::store_pogs($LU,$PRODUCT,$prodref,\@new2);
		$P->store_pogs(\@new2); 
		$P->save();
		}

	$VERB = '';
	if ($SOGID) {
		$VERB = 'WARNKILLSOG';
		}
	}

#######################################
if ($VERB eq 'WARNKILLSOG') {
	$template_file = 'warnkillsog.shtml';
	}


#######################################
if ($VERB eq 'KILLSOG') {
	my $SOGID = $ZOOVY::cgiv->{'SOG'};
#	print STDERR "USERNAME: $USERNAME SOG: $SOGID\n";
	$LU->log('PRODUCT.SOGS',"NUKING SOG: $SOGID",'INFO');
	if ($SOGID) { &POGS::kill_sog($USERNAME,$SOGID); }
	$VERB = '';
	}


#######################################
if ($VERB eq 'SAVEGRID') {
	my $POGID = $ZOOVY::cgiv->{'POG'};
	my @pogs2 = ();
	my $optionsref = undef;
	my $pog = undef;
	my $sogref = undef;

	if ($POGID) {
		#@pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},0);
		## &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs'),0);
		#$pog = &POGS::find_pog_in_pogs(\@pogs,$POGID);
		# @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
		$pog = &POGS::find_pog_in_pogs(\@pogs2,$POGID);
		$optionsref = $pog->{'@options'};
		}

	if ($pog->{'sog'}) {
		my ($sogid,$sogname) = split(/-/,$pog->{'sog'});	 # legacy (probably not needed?)
		($sogref) = &POGS::load_sogref($USERNAME,$sogid);
		# my @sogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$sogid,$sogname),0);
		# $sogref = pop @sogs;
		$optionsref = $sogref->{'@options'};
		}

	##
	## SANITY:
	##		at this point $optionsref is populated with the list of options from the sog
	##

	my $c = '';
	my @saveoptions = ();
	foreach my $opt (@{$optionsref}) {
		my $v = $opt->{'v'};
		next unless (defined $ZOOVY::cgiv->{'check-'.$v});
#		print STDERR "PARSING: $v\n";
		$opt->{'prompt'} = $ZOOVY::cgiv->{'prompt-'.$v};
		# my $metaref = &POGS::parse_meta($opt->{'m'});
		$opt->{'p'} = $ZOOVY::cgiv->{'price-'.$v};
		$opt->{'p'} =~ s/ //g;
		$opt->{'w'} = $ZOOVY::cgiv->{'weight-'.$v};
		$opt->{'w'} =~ s/ //g;
#		$opt->{'m'} = &POGS::encode_meta($metaref);
		push @saveoptions, $opt;
		}
	$pog->{'@options'} = \@saveoptions;

#	print STDERR "DUMPER: ".Dumper(\@pogs);
#	print STDERR "OUTPUT: ".&POGS::struct_to_text(\@pogs);
#	print STDERR "OPTIONS: ".Dumper(\@saveoptions);

	if ($POGID) {
		# print STDERR &POGS::struct_to_text(\@pogs)."\n"; exit;
		# &POGS::store_pogs($LU,$PRODUCT,$prodref,\@pogs2);
		$P->store_pogs(\@pogs2); 
		$P->save();
		# &ZOOVY::saveproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs',&POGS::struct_to_text(\@pogs));
		}

	$VERB = 'GRIDEDIT';
	}






#######################################
if ($VERB eq 'GRIDEDIT') {
	my $POGID = $ZOOVY::cgiv->{'POG'};
	my $pog = undef;
	my $sogref = undef;
	my $optionsref = undef;
	my %INCLUDED = ();			# a hash of included options, along with modifiers, etc.
	if ($POGID) {
		#@pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},0);
		## &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs'),0);
		#$pog = &POGS::find_pog_in_pogs(\@pogs,$POGID);
      # my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		my @pogs2 = ();
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
      ($pog) = &POGS::find_pog_in_pogs(\@pogs2,$POGID);
		$optionsref = $pog->{'@options'};	## can you actually edit a pog in gridedit? hmm.. this may not be necessary.
		foreach my $opt (@{$optionsref}) {
			$INCLUDED{$opt->{'v'}} = $opt;
			}
		}

	if ($pog->{'sog'}) {
		## okay we're gridediting a sog, so we need to load the options that weren't checked 
		##		ideally we'd be merging these, but whatever.
		##	
		my ($sogid,$sogname) = split(/-/,$pog->{'sog'});
		($sogref) = &POGS::load_sogref($USERNAME,$sogid);

		#my @sogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$sogid,$sogname),0);
		#$sogref = pop @sogs;
		# print STDERR Dumper($pog,$sogref);
		$optionsref = $sogref->{'@options'};  
		}

#	print STDERR "INCLUDED: ".Dumper(\%INCLUDED);

	##
	## SANITY:
	##		$sogref is undef if we are editing a pog, otherwise it's the complete sog
	##		$pog is a reference to the pog we're editing
	##		$optionslist is the full list of options available
	##		%INCLUDED is a hash keyed by value with the data the merchant has customized
	##
	$GTOOLS::TAG{'<!-- PROMPT -->'} = $pog->{'prompt'};
	$GTOOLS::TAG{'<!-- TYPE -->'} = $pog->{'type'};
	$GTOOLS::TAG{'<!-- POG -->'} = $POGID;
	$GTOOLS::TAG{'<!-- SOG -->'} = $SOGID;

	my $c = '';	
	# $c .= "<tr><td colspan=5>".Dumper($prodref,\%INCLUDED)."</td></tr>";

	foreach my $opt (@{$optionsref}) {
		my $checked = '';
		my $restore_js = '';
		my $v = $opt->{'v'};

		# $c .= "<tr><td colspan='5'>".Dumper(\%INCLUDED)."</td></tr>";
		$c .= "<tr>";
		if (defined $INCLUDED{$v}) { 
			my $sogopt = $opt;	## keep a copy of the option from the sog (used to restore values)
			$opt = $INCLUDED{$v};
			$checked = 'checked'; 

			my $pogopt_is_different_than_sogopt = 0;
			foreach my $attrib ('prompt','w','p') { 
				## compare the prompt and meta to see if they are different between sog and pog.
				if ($opt->{$attrib} ne $sogopt->{$attrib}) { $pogopt_is_different_than_sogopt++; }
				}

			if ($pogopt_is_different_than_sogopt) {
				$restore_js = qq~
					<a border="0" onClick="
					alert('w: $sogopt->{'w'}');
					document.forms[0].elements['price-$v'].value = '$sogopt->{'p'}';
					document.forms[0].elements['weight-$v'].value = '$sogopt->{'w'}'; 
					document.images['recover$v'].src='/images/blank.gif';
					" href="#"><img name="recover$v" border="0" src="restore.gif"></a>~;
				}
			}
		## SANITY: at this point:
		##		$checked is set to 'checked' if the option was selected in the pog
		##		$checked is set to '' if the option was loaded from the sog
		##		$opt is set to the option reference from the sog UNLESS  $checked is 'checked' then $opt came from the pog
		##		$restore_js contains "restore javascript" that will reset price-$v weight-$v prompt-$v to default values
		##		

		$c .= "<td nowrap align='center'>$v &nbsp; $restore_js</td>";
		$c .= "<td align='center'><input type=\"checkbox\" $checked name=\"check-$v\"></td>";
		$c .= "<td><input type='textbox' name='prompt-$v' value=\"".&ZOOVY::incode($opt->{'prompt'})."\"></td>";
		$c .= "<td align='center'><input size='5' type='textbox' name='price-$v' value=\"".&ZOOVY::incode($opt->{'p'})."\"></td>";
		$c .= "<td align='center'><input size='5' type='textbox' name='weight-$v' value=\"".&ZOOVY::incode($opt->{'w'})."\"></td>";
		$c .= "</tr>";
		}
	$GTOOLS::TAG{'<!-- GRID -->'} = $c;

	$template_file = 'gridedit.shtml';
	}


#######################################
if ($VERB eq 'EDITPOG' || $VERB eq 'EDITSOG') {

	if ($VERB eq 'EDITPOG') {
		}

	if ($VERB eq 'EDITSOG') {
		$GTOOLS::TAG{'<!-- PRODUCT -->'} = "";
		}

	my $POGID = $ZOOVY::cgiv->{'POG'};
	my $SOGID = $ZOOVY::cgiv->{'SOG'};

#	print STDERR "$VERB - SOGID: $SOGID\n";
	my @pogs2 = ();
	my $psog = undef;
	if ($POGID) {
		# @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
		if ( (defined $P) && (defined $P->fetch_pogs()) ) {
			@pogs2 = @{$P->fetch_pogs()};
			}
		$psog = &POGS::find_pog_in_pogs(\@pogs2,$POGID);
		# @pogs = &POGS::text_to_struct($USERNAME,$prodref->{'zoovy:pogs'},0);
		## &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs'),0);
		#$psog = &POGS::find_pog_in_pogs(\@pogs,$POGID);
		}
	if ($SOGID) {
		#@pogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$SOGID));
		# $psog = $psogs[0];
		$psog = &POGS::load_sogref($USERNAME,$SOGID);
		$psog->{'sog'} = $SOGID;
		}

	# print STDERR Dumper($POGID,$SOGID,$psog,\@pogs2);


	## SANITY CHECKS!
	if ($POGID) {
		## we're
		if (($psog->{'type'} eq 'biglist') && ($psog->{'global'})) {
			push @MSGS, "WARN|This appears to be a globally managed biglist, you cannot make changes here (global biglists must be managed from the store option group and have all the same options)";
			}
		}


	# print "Content-type: text/plain\n\n"; print Dumper($psog); exit;
	$GTOOLS::TAG{'<!-- ASSEMBLY_MODIFIER -->'} = '';
	$GTOOLS::TAG{'<!-- PROMPT -->'} = $psog->{'prompt'};
	$GTOOLS::TAG{'<!-- TYPE -->'} = $psog->{'type'};
	$GTOOLS::TAG{'<!-- POG -->'} = $POGID;
	$GTOOLS::TAG{'<!-- SOG -->'} = $SOGID;



	$GTOOLS::TAG{'<!-- IMAGE_MODIFIER -->'} = '<input type="hidden" id="img" name="img" value=""> <input id="imgimg" name="imgimg" type="image" src="/images/blank.gif" width=1 height=1>';	 	## blank is not saved.
	$GTOOLS::TAG{'<!-- HIDE_BIGLIST_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_BIGLIST_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- BIGLIST_CONTENTS -->'} = '';
	$GTOOLS::TAG{'<!-- HIDE_SELECT_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_SELECT_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- HIDE_TEXTAREA_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_TEXTAREA_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- HIDE_READONLY_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_READONLY_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- HIDE_ASSEMBLY_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_ASSEMBLY_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- HIDE_TEXTBOX_START -->'} = '<!--';
	$GTOOLS::TAG{'<!-- HIDE_TEXTBOX_END -->'} = '-->';
	$GTOOLS::TAG{'<!-- NUMBER_FIELDS -->'} = '';						# this is replaced with min, max if a number
	$GTOOLS::TAG{'<!-- TEXT_FIELDS -->'} = '';						# this is replaced with min, max if a number
	$GTOOLS::TAG{'<!-- SELECT_OPTS -->'} = '';
	$GTOOLS::TAG{'<!-- REMOVE -->'} = '';
	$GTOOLS::TAG{'<!-- DEFAULT -->'} = $psog->{'default'};
	$GTOOLS::TAG{'<!-- ASSEMBLY -->'} = $psog->{'assembly'};
	$GTOOLS::TAG{'<!-- MAXLENGTH -->'} = $psog->{'maxlength'};
	$GTOOLS::TAG{'<!-- FEE_LINE -->'} = $psog->{'fee_line'};
	$GTOOLS::TAG{'<!-- FEE_CHAR -->'} = $psog->{'fee_char'};
	$GTOOLS::TAG{'<!-- FEE_WORD -->'} = $psog->{'fee_word'};
	$GTOOLS::TAG{'<!-- COLS -->'} = $psog->{'cols'}; 
	$GTOOLS::TAG{'<!-- ROWS -->'} = $psog->{'rows'}; 
	$GTOOLS::TAG{'<!-- GHINT -->'} = &ZOOVY::incode($psog->{'ghint'});	## note: must oghint so it doesn't overwrite option hint.

	$GTOOLS::TAG{'<!-- INV_CHECKED -->'} = ($psog->{'inv'})?'checked':'';

	$template_file = 'editpog.shtml';

	if ($psog->{'type'} eq 'textarea') {
		$GTOOLS::TAG{'<!-- HIDE_TEXTAREA_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_TEXTAREA_END -->'} = '';
		}

	if ($psog->{'type'} eq 'readonly') {
		$GTOOLS::TAG{'<!-- HIDE_READONLY_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_READONLY_END -->'} = '';
		}

	if ($psog->{'type'} eq 'assembly') {
		$GTOOLS::TAG{'<!-- HIDE_ASSEMBLY_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_ASSEMBLY_END -->'} = '';
		}

	if ($psog->{'type'} eq 'text' || $psog->{'type'} eq 'number' || $psog->{'type'} eq 'hidden') {
		$GTOOLS::TAG{'<!-- HIDE_TEXTBOX_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_TEXTBOX_END -->'} = '';
		if ($psog->{'type'} eq 'number') {
			$GTOOLS::TAG{'<!-- NUMBER_FIELDS -->'} = qq~
				<tr><td colspan='2'><b>Number Specific Fields:</b></td></tr>
				<tr><td>Minimum Number:</td><td><input type="textbox" size="10" name="MIN" value="$psog->{'min'}"></td></tr>
				<tr><td>Maximum Number:</td><td><input type="textbox" size="10" name="MAX" value="$psog->{'max'}"></td></tr>
			~;
			}
		}

	#$GTOOLS::TAG{'<!-- TEXT_FIELDS -->'} = 'asdf';
	if (($psog->{'type'} eq 'text') || ($psog->{'type'} eq 'textarea') || ($psog->{'type'} eq 'hidden')) {
		$psog->{'fee_char'} = sprintf("%.2f",$psog->{'fee_char'});
		$psog->{'fee_word'} = sprintf("%.2f",$psog->{'fee_word'});
		$psog->{'fee_line'} = sprintf("%.2f",$psog->{'fee_line'});
		$GTOOLS::TAG{'<!-- TEXT_FIELDS -->'} = qq~
	<tr>
		<td colspan=2>Fee Per Character: \$<input type="textbox" name="FEE_CHAR" size="6" value="$psog->{'fee_char'}"></td>
	</tr>
	<tr>
		<td colspan=2>Fee Per Word: \$<input type="textbox" name="FEE_WORD" size="6" value="$psog->{'fee_word'}"></td>
	</tr>
			~;
		if ($psog->{'type'} eq 'textarea') {
		$GTOOLS::TAG{'<!-- TEXT_FIELDS -->'} .= qq~
		<tr>
			<td colspan=2>Fee Per Line: \$<input type="textbox" name="FEE_LINE" size="6" value="$psog->{'fee_line'}"></td>
		</tr>
		~;
			}

		}


	if ($psog->{'type'} =~ /^(text|textarea|hidden|calendar)$/) {
		my $chk_optional = ($psog->{'optional'})?'checked':'';
		$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~
		<br>
		<input type="checkbox" $chk_optional name="optional"> Optional: does not display in cart/order if blank.<br>
		~;
		}


	if ($psog->{'type'} eq 'calendar') {
		$psog->{'fee_rush'} = sprintf("%.2f",$psog->{'fee_rush'});
		$psog->{'rush_days'} = int($psog->{'rush_days'});
		$psog->{'rush_prompt'} = $psog->{'rush_prompt'};
		$psog->{'rush_msg'} = $psog->{'rush_msg'};
		$GTOOLS::TAG{'<!-- CALENDAR_FIELDS -->'} = qq~
		<tr>
			<td>
			<b>Rush Fees:</b><br>	
			Add a fee of \$<input size="6" type="textbox" name="FEE_RUSH" value="$psog->{'fee_rush'}"> 
			for orders within <input size="3" type="textbox" name="RUSH_DAYS" value="$psog->{'rush_days'}"> days.<br>
			<br>
			Rush Prompt: <input type="textbox" name="RUSH_PROMPT" value="~.&ZOOVY::incode($psog->{'rush_prompt'}).qq~"> (what appears on the invoice)<br>
			Rush Message:<br>
			<textarea name="RUSH_MSG">~.&ZOOVY::incode($psog->{'rush_msg'}).qq~</textarea>
			<br>
			</td>
		</tr>
		~;
		}

#	if ($psog->{'type'} eq 'attribs') {
#		$GTOOLS::TAG{'<!-- FINDER_OPTIONS -->'} = qq~
#		<div class="finder_options">
#		Lookup Attrib:
#		<input type="textbox" name="LOOKUP_ATTRIB" value="~.&ZOOVY::incode($psog->{'lookup_attrib'}).qq~">
#		<div class="hint">Specify a product attribute (e.g. zoovy:prod_mfg) to lookup and base this value on.</div>
#		</div>
#		~;
#		}
	

	if ($psog->{'type'} eq 'radio' || $psog->{'type'} eq 'cb' 
   || $psog->{'type'} eq 'select' || $psog->{'type'} eq 'attribs'
	|| $psog->{'type'} eq 'imgselect' || $psog->{'type'} eq 'imggrid') {
		## select, radio, cb
		$GTOOLS::TAG{'<!-- HIDE_SELECT_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_SELECT_END -->'} = '';
		my $out = '';
		foreach my $opt (@{$psog->{'@options'}}) {
			$opt->{'prompt'} = &ZTOOLKIT::encode($opt->{'prompt'});
			my $htmloptval = sprintf('id=%s|pt=%s',$opt->{'id'},$opt->{'prompt'});
			foreach my $k (sort keys %{$opt}) { 
				next if ($k eq 'prompt');
				$htmloptval .= "|$k=$opt->{$k}"; 
				}
			$htmloptval = &ZOOVY::incode($htmloptval);
			$out .= "<option value=\"$htmloptval\">$opt->{'prompt'}</option>\n";
			#if ($opt->{'html'}) { $out .= "|html=".$opt->{'html'}; }
			#if ($opt->{'inv'} & 2) { $out .= "|asm=".$opt->{'asm'}; }
 			#$out .= "\">$opt->{'prompt'}</option>\n";
			#$out .= "<option value=\"pt=$opt->{'prompt'}|id=$opt->{'v'}|$opt->{'m'}";
			#if ($opt->{'html'}) { $out .= "|html=".$opt->{'html'}; }
			#if ($opt->{'inv'} & 2) { $out .= "|asm=".$opt->{'asm'}; }
 			#$out .= "\">$opt->{'prompt'}</option>\n";
			}
		$GTOOLS::TAG{'<!-- SELECT_OPTS -->'} = $out;

		if ($psog->{'type'} ne 'cb') {
			$GTOOLS::TAG{'<!-- REMOVE -->'} = qq~<input class="button" type="button" value=" Remove " onclick="dropItem();">~;
			}

		if ($psog->{'type'} eq 'imgselect' || $psog->{'type'} eq 'imggrid') {
			$GTOOLS::TAG{'<!-- HIDE_IMGSELECT_START -->'} = '';
			$GTOOLS::TAG{'<!-- HIDE_IMGSELECT_END -->'} = '';
			$GTOOLS::TAG{'<!-- HIDE_SELECT_START -->'} = '';
			$GTOOLS::TAG{'<!-- HIDE_SELECT_END -->'} = '';
			my $t = time();
			my %serialref = ('ATTRIB'=>'img','SRC'=>'','PROMPT'=>'Select List Image','DIV'=>'pogFrm',AUTH=>$::AUTH);
			my $passthis = &ZTOOLKIT::fast_serialize(\%serialref,1);
			$GTOOLS::TAG{'<!-- IMAGE_MODIFIER -->'} = qq~
				<table bgcolor="CFCFCF">
					<tr>
					<td bgcolor="CFCFCF">
						<img id="imgimg" src="/images/image_not_selected.gif" width="75" height="75" name="imgimg">
					</td>
					<td bgcolor="CFCFCF">
						Selected Image: 
						<input onChange="document.pogFrm.imgimg.src=imglib(document.pogFrm.img.value,50,50,'FFFFFF',0,'jpg');" type="textbox" id="img" name="img" size="20"><br>
						<input type="BUTTON" style='width: 100px;' value="Image Library" onClick="mediaLibrary(jQuery('#imgimg'),jQuery('#img'),'Choose Option Image');">
					</td>
					</tr>
				</table>
				<br>
				~;

			my $zoom_checked = ($psog->{'zoom'})?'checked':'';
			
			
			$GTOOLS::TAG{'<!-- IMAGE_OPTIONS -->'} = qq~
				Thumbnail Height: <input size="3" type="textbox" name="HEIGHT" value="$psog->{'height'}"> (pixels)<br>
				Thumbnail Width: &nbsp;<input size="3" type="textbox" name="WIDTH" value="$psog->{'width'}"> (pixesl)<br>
				<input type="checkbox" $zoom_checked name="ZOOM"> Enable Click to Zoom on Images<br>
				Image Type: <select name="IMG_TYPE" >\n~;
			
			
			my %imgtypes = ('sku_image'=>'SKU Image',
								 'swatch'=>'Color Swatch',
								 'other'=>'Other');
			foreach my $type (keys %imgtypes) {
				my $selected = '';
				if ($psog->{'img_type'} eq $type) { $selected = 'selected'; }
				$GTOOLS::TAG{'<!-- IMAGE_OPTIONS -->'} .= qq~
					<option value="$type" $selected>$imgtypes{$type}</option>\n~;
				}

			$GTOOLS::TAG{'<!-- IMAGE_OPTIONS -->'} .= "</select><br>";

			if ($psog->{'type'} eq 'imggrid') {
				$GTOOLS::TAG{'<!-- IMAGE_OPTIONS -->'} .= qq~Image Columns: <input size="3" type="textbox" name="COLS" value="$psog->{'cols'}"><br>~;
				}
			}

		if ((index($FLAGS,',EBAY,')>=0) && ($SOGID ne '')) {
			$GTOOLS::TAG{'<!-- EBAY_OPTIONS -->'} = sprintf(qq~<div>
eBay Variation Specifics Name: <input type="textbox" name="EBAY" value="%s">
</div>~,&ZOOVY::incode($psog->{'ebay'}));
			}

			
		if ((index($FLAGS,',AMZ,')>=0) && ($SOGID ne '' )) {
			## this hash is created by app1:/httpd/servers/amazon/build_variation_thms.pl 
			my @options = &AMAZON3::get_amz_options();
			$GTOOLS::TAG{'<!-- AMAZON_OPTIONS -->'} = qq~Amazon Variation Keyword [ ~.
				qq~<a target=_new onClick="return linkOffSite('http://webdoc.zoovy.com/index.cgi?VERB=DOC&DOCID=50391');">?</a> ]: ~.
				qq~\n<select name="AMZ" >\n<option value=''>None</option>\n~;
			
			foreach my $option (sort @options) {
				my $selected = ($option eq $psog->{'amz'})?'selected':'';
				$GTOOLS::TAG{'<!-- AMAZON_OPTIONS -->'} .= qq~<option value="$option" $selected>$option</option>\n~;
				} 
			$GTOOLS::TAG{'<!-- AMAZON_OPTIONS -->'} .= "</select>";
			}
		
		## addition of Google Variation Keyword, 2011-09-14 - patti
		## needed for variations and GOO Marketplace change to take place on Sep22
		$GTOOLS::TAG{'<!-- GOOGLE_OPTIONS -->'} = qq~Google Variation Keyword: ~.
				qq~\n<select name="GOO" >\n<option value=''>None</option>\n~;
		foreach my $option ('Color','Size','Material','Pattern') {
			my $selected = ($option eq $psog->{'goo'})?'selected':'';
			$GTOOLS::TAG{'<!-- GOOGLE_OPTIONS -->'} .= qq~<option value="$option" $selected>$option [$selected]</option>\n~;
			} 
		$GTOOLS::TAG{'<!-- GOOGLE_OPTIONS -->'} .= "</select>";
		
		if ($DEBUG) { $GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} = "<pre>".Dumper($psog)."</pre>"; }

		if ($psog->{'inv'}) {
			$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~<font color='blue'><li> This group affects inventory<li> 100 options max.</font><br>~;
			if (($psog->{'inv'} & 2)==2) {
				$GTOOLS::TAG{'<!-- ASSEMBLY_MODIFIER -->'} = qq~<tr><td>Assembly:</td><td><input type="textbox" value="" name="asm"></td></tr>~;		
				}
			else {
				$GTOOLS::TAG{'<!-- ASSEMBLY_MODIFIER -->'} = qq~<input type="hidden" name="asm">~;
				}
			}
		else {
			my $chk_optional = ($psog->{'optional'})?'checked':'';

			if (not defined $P) {
				## there is no product to check, probably editing a SOG
				}
			elsif (($P->fetch('amz:ts')>0) && ($psog->{'optional'}==0)) {
				$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~
<div class="error">Product is currently configured for Amazon Syndication, so
non-inventoriable options MUST be "optional" or they cannot not be downloaded in orders from Amazon.
HINT: either disable Amazon syndication, or make this "optional"</div>
~;
				}

			$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~
			<br>
			<input type="checkbox" $chk_optional name="optional"> Optional: does not display in cart/order if not selected.<br>
			<input type="hidden" name="asm">
			<font color='blue'>
				<li> Group does not affect Inventory
				<li> 1296 options max.
			</font><br>~;
			}
		} # end if inventoriable type (based on select)


	if ($psog->{'sog'}) {
		$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~<font color='blue'><li> This is a store option group</font><br>~;
		if ($psog->{'global'}>0) { 
			$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~<font color='blue'><li> Managed Globally</font><br>~;		
			}
		else { 
			$GTOOLS::TAG{'<!-- INVENTORY_OPTIONS -->'} .= qq~<font color='blue'><li> Managed Individually</font><br>~;	 
			}
		}


	if ($psog->{'type'} eq 'biglist') {
		$GTOOLS::TAG{'<!-- HIDE_BIGLIST_START -->'} = '';
		$GTOOLS::TAG{'<!-- HIDE_BIGLIST_END -->'} = '';
		my $out = '';
		foreach my $opt (@{$psog->{'@options'}}) {
			$out .= "$opt->{'prompt'}\n";
			}
		$GTOOLS::TAG{'<!-- BIGLIST_CONTENTS -->'} = $out;
		}

	}


##
## Chooser: select type of option, and the name.
##
if ($VERB eq 'CREATESOG' || $VERB eq 'CREATEPOG') {

	$GTOOLS::TAG{'<!-- VERB -->'} = $VERB;
	if ($VERB eq 'CREATEPOG') {
		$GTOOLS::TAG{'<!-- HEADER -->'} = qq~<b>Create Product Option Group</b>~;
		}
	if ($VERB eq 'CREATESOG') {
		$GTOOLS::TAG{'<!-- HEADER -->'} = qq~<b>Create Store Option Group</b>~;
		$GTOOLS::TAG{'<!-- PRODUCT -->'} = 'N/A';
		}

	$GTOOLS::TAG{'<!-- TYPE_SELECT -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_RADIO -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_CB -->'} = '';

	$GTOOLS::TAG{'<!-- TYPE_TEXT -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_TEXTAREA -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_NUMBER -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_READONLY -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_HIDDEN -->'} = '';

	$GTOOLS::TAG{'<!-- TYPE_IMGSELECT -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_BIGLIST -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_SOG_PTR -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_SOG_VAR -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_FILEUPLOAD -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_DYNAMIC -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_IMGSELECT -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_IMGGRID -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_CALENDAR -->'} = '';
	$GTOOLS::TAG{'<!-- TYPE_ASSEMBLY -->'} = '';

	$GTOOLS::TAG{'<!-- TYPE_'.uc($ZOOVY::cgiv->{'TYPE'}).' -->'} = 'checked';
	$GTOOLS::TAG{'<!-- PROMPT_VAL -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'PROMPT'});
	$GTOOLS::TAG{'<!-- META_VAL -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'META'});
	$GTOOLS::TAG{'<!-- CB_INV -->'} = (defined $ZOOVY::cgiv->{'INV'})?'checked':'';

	$GTOOLS::TAG{'<!-- AMZ_OPTIONS -->'} = "";

	if ((index($FLAGS,',AMZ,')>=0) && ($VERB eq 'CREATESOG')) {
		my @options = &AMAZON3::get_amz_options();
		$GTOOLS::TAG{'<!-- AMZ_OPTIONS -->'} .= qq~Amazon Variation Keyword: \n<select name="AMZ" >\n<option value=''>None</option>\n~;
			
		foreach my $option (sort @options) {
			$GTOOLS::TAG{'<!-- AMZ_OPTIONS -->'} .= qq~<option value="$option">$option</option>\n~;
			} 
		$GTOOLS::TAG{'<!-- AMZ_OPTIONS -->'} .= "</select>";

		$GTOOLS::TAG{'<!-- AMZ_OPTIONS -->'} .= qq~
	<a href="#" onClick="if (Element.visible('!help-amzvariation')) { new Effect.SlideUp('!help-amzvariation'); } else { new Effect.SlideDown('!help-amzvariation'); }">[Info]</a><br>
	<div id="!help-amzvariation" style="display: none"><div>
Amazon requires options be mapped to a "variation keyword". A variation keyword  
this is a term that Amazon will use to distinguish properties of the product such as size, color, etc. 
Variation themes are critical when buyers search for a specific size, color, clarity, etc. on the Amazon site.<br>
<br>
If you do not match up your options to Amazon properly then your items will still be purchasable but they 
will NOT appear in search and are therefore MUCH less likely to be found/purchased.<br>
<br>
We'll use Apparel as an example of how Zoovy's options correspond to Amazons variation keywords. 
For the Apparel product type Amazon has three variation keywords: Size, Color, or ColorAndSize<br>
<Br>
Depending on how you choose to setup your products on Zoovy you could implement either a single option group 
called size,  and another called color, or just create one option group called "Color and Size" 
(when you'd put in combined options like Small/White). You can then apply whichever zoovy option groups 
are appropriate for your particular product. 
<br>
If the product being sold only comes in "blue" then you could set the color in the product, and only map the Size 
option group to the product. In otherwords as long as you set the right Variation Themes, and you design your options
to work around Amazon's you have a lot of flexability. Zoovy automatically manages the parentage relations between
master products and their respective lineage in the Amazon system.<br>
<br>
Just remember that in each respective option group you must set the appropriate Amazon Variation Keyword.
You can create as many option groups as you want and map them all to the same variation keywords (e.g. 
Sweater Size, and Pant Size can both map to Amazon variation keyword "Size").
<br>
NOTE: In some cases (ex: jewelry) Amazon will restrict the possible values of the particular variation theme. 
In this case the option prompts for your option group MUST match the Amazon variation theme values. A complete 
list of possible values will be given to you by Zoovy, AND MAY CHANGE OVER TIME as Amazon changes their schema. 
Zoovy will attempt (but not necessarily guarantee) to maintain backward compatibility.<br>
<br>
As a rule you should always try and use industry accepted terms for best compatibility e.g. "Navy Blue" instead of "Royal
Midnight" since Amazon probably won't know that Royal Midnight is the same as Navy blue. If you cannot adhere to well
used industry terms then make sure you contact your Amazon account manager and let them know they will need to map
your variation data to the Amazon thesaurus. 
<br>
	</div></div><br>
		~;
		}

	if ($VERB eq 'CREATESOG') {
		## SOG SPECIFIC OPTIONS
		my $SOGID = &POGS::next_available_sogid($USERNAME);
		$GTOOLS::TAG{'<!-- SOG_OPTIONS -->'} = qq~
			<input type='hidden' name='SOG' value='$SOGID'>
			<b>Store Option Group Behavior:</b> 
			<a href="#" onClick="if (Element.visible('!help-sogbehavior')) { new Effect.SlideUp('!help-sogbehavior'); } else { new Effect.SlideDown('!help-sogbehavior'); }">[Info]</a><br>
			<div id="!help-sogbehavior" style="display: none"><div>
			<b>About Behavior:</b>
			There are two behaviors available when new options are added to the store option group - the new options can
either be automatically added to all products using that group, OR manually added to each product.<br>
			<br>
			Automatic Store Option groups cannot select different options on a product by product basis. 
			When changes are made in an automatic group, they are instantly added to all products associated to the group. 
			When changes are made to manual groups it is necessary to add the new option to each product, 
			but of course then it is also possible to choose which specific options are applicable to the product.<Br>
			<br>
			Useing Automatic groups with inventoriable store option groups is HIGHLY discouraged since inventory for the items
			will be out of stock (zero) when the new item code is created.  Automatic groups are really best suited for situations 
			where (for example) you have a line of products made by a common manufacturer and the options available/unavailable to
			the line of products doesn't change. As new options are added they are available for all products.<br>
			<br> 	
			If you're still in doubtas to which type of option group to use, we recommend manual since it offers the highest degree of flexability.
			<br>
			</div></div>
			<input type="radio" checked name="GLOBAL" value="0"> <b>MANUAL:</b> I need to select options, and customize modifiers on a product by product basis.<br>
			<input type="radio" name="GLOBAL" value="1"> <b>AUTOMATIC:</b> Any changes should automatically affect all products using this group.<br>
			~;


		$GTOOLS::TAG{'<!-- FINDER_OPTION -->'} = qq~
			<input type="checkbox" name="FINDER"> <b>Properties Only (Used with Finders)</b> 
			<a href="#" onClick="if (Element.visible('!help-finder')) { new Effect.SlideUp('!help-finder'); } else { new Effect.SlideDown('!help-finder'); }">[Info]</a><br>
			<div id="!help-finder" style="display: none"><div>
			<b>Properties Only: </b> is used to specify that the store option group data should ONLY be used
to compile search data. With a "Properties Only" style option group the customer will never be prompted to 
select this option while purchasing. 
A "Properties Only" group is not compatible with Inventoriable Options or Assemblies, but is compatible with a
special type of search catalog known as a "Finder" which can be used to let customers find matching products based
on either their options or properties.<br>
<br>
Frequent examples of "Properties Only" options include: 
"Genre", "Year", or even "Price Range". For example if a DVD Is a romantic comedy, 
it could have the Genre option "Romance" and "Comedy" checked, the customer doesn't need to choose between
the Comedy and Romance version, the product is both Comedy and Romance at the same time. <br>
<br>
Other examples include:
	<li> Make/Model: manufacturers of carts, boats, planes, etc. regularly make parts which span multiple 
makes, models and years. 
(NOTE: due to limitations in the number of options per group (1296) it is not possible
to create a single group for "Make/Model/Year" 
	<li> Price Range: setting up price ranges for $1-$25, $26-$50, and $51-$100 lets you provide customers
an easy way to locate products in their price range.
			</div></div><br>
		~;


		$GTOOLS::TAG{'<!-- EBAY_OPTIONS -->'} .= qq~<div>
eBay Variation Specifics Name: \n<input type="textbox" name="EBAY" >
</div><br>~;

		$GTOOLS::TAG{'<!-- GOO_OPTIONS -->'} .= qq~Google Variation Keyword: \n<select name="GOO" >\n<option value=''>None</option>\n~;
			
		foreach my $option ('Color','Size','Material','Pattern') {
			$GTOOLS::TAG{'<!-- GOO_OPTIONS -->'} .= qq~<option value="$option">$option</option>\n~;
			} 
		$GTOOLS::TAG{'<!-- GOO_OPTIONS -->'} .= "</select>";

		$GTOOLS::TAG{'<!-- GOO_OPTIONS -->'} .= qq~
	<a href="#" onClick="if (Element.visible('!help-goovariation')) { new Effect.SlideUp('!help-goovariation'); } else { new Effect.SlideDown('!help-goovariation'); }">[Info]</a><br>
	<div id="!help-amzvariation" style="display: none"><div>
Googlebase requires options be mapped to a "variation keyword". A variation keyword  
this is a term that Googlebase will use to distinguish properties of the product such as size, color, etc. 
Variation themes are critical when buyers search for a specific size, color, etc. on the Googlebase site.<br>
	</div></div><br>
		~;

		}
	else {
		## POG SPECIFIC OPTIONS
		$GTOOLS::TAG{'<!-- SOGPOG -->'} = qq~~;
		}
	$template_file = 'create.shtml';
	}


if ($VERB eq 'XML_END') {
	# my $pogs = $P->fetch('zoovy:pogs');
	# &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:pogs');

	my $inv_enable = $P->fetch('zoovy:inv_enable');
	# &ZOOVY::fetchproduct_attrib($USERNAME,$PRODUCT,'zoovy:inv_enable');
	# my @pogs = &POGS::text_to_struct($USERNAME,$pogs,1);
	# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
	my @pogs2 = ();
	if ( (defined $P) && (defined $P->fetch_pogs()) ) {
		@pogs2 = @{$P->fetch_pogs()};
		}
	
	$inv_enable = ($inv_enable & 4);
	if ($P->has_variations('inv')) { $inv_enable += 4; }
	
	# $pogs = &ZOOVY::incode($pogs);
	
	@pogs2 = &POGS::downgrade_struct(\@pogs2);
	my ($pogs) = &POGS::struct_to_text(\@pogs2);

	print "Content-type: text/html\n\n";
	print qq~
<body>
<!--//
<SESSION_TERMINATED>
<input type="hidden" name="set-zoovy:inv_enable" value="$inv_enable">
<input type="hidden" name="set-zoovy:pogs" value="$pogs"/>
<input type="hidden" name="del-zoovy:notes_default" value=""/>
<input type="hidden" name="del-zoovy:notes_prompt" value=""/>
<input type="hidden" name="del-zoovy:notes_display" value=""/>
</SESSION_TERMINATED>
//-->
</body>
~;

	# print STDERR "POGS: $pogs\n";

	exit;
	}


## this is the main menu (will probably never be used)
if ($VERB eq '') {

	## remove 2.0 options
	if ($::MODE eq '') {
		#if ($P->fetch('zoovy:notes_prompt')) {	
		#	delete $prodref->{'zoovy:notes_default'};
		#	delete $prodref->{'zoovy:notes_prompt'};
		#	delete $prodref->{'zoovy:notes_display'};
		#	&ZOOVY::saveproduct_from_hash($USERNAME,$PRODUCT,$prodref);
		# 	}
		}
	##


	# my ($pogtxt) = $prodref->{'zoovy:pogs'};
	# print STDERR "PRODUCT IS: $PRODUCT [$pogtxt]\n";
	
	# my @pogs = &POGS::text_to_struct($USERNAME,$pogtxt,0);
	# my @pogs2 = @{&ZOOVY::fetch_pogs($USERNAME,$prodref)};
	my @pogs2 = ();
	if ((defined $P) && (defined $P->fetch_pogs())) {
		## note: $P won't always be set because sometimes we're in global sog edit
		@pogs2 = @{$P->fetch_pogs()};
		};
	# use Data::Dumper;
	# print STDERR Dumper($USERNAME,\@pogs);

	my %pogids = ();
	if (not scalar(@pogs2)) {
		$GTOOLS::TAG{'<!-- POG_OUTPUT -->'} = "<tr><Td colspan='5'>This product currently has no options.</td></tr>";
		}
	else {
		my $c = '';
		my $last = scalar(@pogs2);
		my $count = 0;
		foreach my $pog (@pogs2) {
			$pogids{$pog->{'id'}}++;
			$c .= "<tr>";
			$c .= "<td valign='top' nowrap>";
	
			my $sogref = undef;
			$pog->{'_editable'} = 1;					# this is something that is implicity on, unless a sog turns it off.
			if ($pog->{'sog'} ne '') {
				my ($sogid,$sogname) = split(/-/,$pog->{'sog'});
				($sogref) = &POGS::load_sogref($USERNAME,$sogid);
				# my @sogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$sogid,$sogname),0);
				# $sogref = pop @sogs;
#				print STDERR Dumper($sogref);
				if ($sogref->{'global'}) { $pog->{'_editable'} = 0; }
				}

			if ($count++>0) {
				$c .= "	<a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=PROMOTE&PRODUCT=$PRODUCT&POG=".&uri_escape($pog->{'id'})."');\"><img src=\"/biz/images/arrows/blue_up-13x13.gif\" height=13 width=13 border=0></a>";
				} else { $c .= "<img src=\"/images/blank.gif\" width=13 height=13 border=0>"; }

			if ($count<$last) {
				$c .= "	<a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=DEMOTE&PRODUCT=$PRODUCT&POG=".&uri_escape($pog->{'id'})."'');\"><img src=\"/biz/images/arrows/blue_down-13x13.gif\" border=0></a>";
				} else { $c .= "<img src=\"/images/blank.gif\" width=13 height=13 border=0>"; }

			if ($pog->{'_editable'}) {
				if ($pog->{'sog'}) {
					$c .= "	<a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=GRIDEDIT&PRODUCT=$PRODUCT&POG=".&uri_escape($pog->{'id'})."');\"><img src=\"/biz/images/arrows/blue_edit-13x13.gif\" border=0></a>";
					}
				else {
					$c .= "	<a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=EDITPOG&PRODUCT=$PRODUCT&POG=".&uri_escape($pog->{'id'})."');\"><img src=\"/biz/images/arrows/blue_edit-13x13.gif\" border=0></a>";
					}
				} else { $c .= "<img src=\"/images/blank.gif\" width=13 height=13 border=0>"; }
		
			if ($pog->{'sog'}) {
				$c .= "  <a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=KILLPOG&PRODUCT=$PRODUCT&POG=".&uri_escape($pog->{'id'})."');\"><img src=\"/biz/images/arrows/blue_right-13x13.gif\" border=0></a>";
				}

			$c .= "</td>";

			if ((defined $pog->{'sog'}) && ($pog->{'sog'} eq '')) { delete $pog->{'sog'}; }

			if ($pog->{'sog'} ne '') {
				$c .= "<td>$sogref->{'prompt'}</td>";
				$c .= "<td nowrap>$sogref->{'type'}<br>INV: $sogref->{'inv'}<br>GLOBAL: $sogref->{'global'}";
				if ($DEBUG) { $c .= "<pre>".Dumper($sogref)."</pre>"; } 
				$c .= "</td>";
				if (defined($sogref->{'global'}) && $sogref->{'global'}) {
					if (defined $sogref->{'@options'}) {
						$c .= qq~
						<td valign=top>~.(scalar(@{$sogref->{'@options'}})).qq~<br>
						<a href="#" onClick="return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=EDITSOG&SOG=$sogref->{'id'}');">(Edit SOG)</a>
						</td>~; 
						}
					else {	
						## note: global text areas don't have options
						$c .= "<td valign=top>n/a</td>";
						}
					}
				elsif (defined $pog->{'@options'}) { 
					$c .= "<td valign=top>".(scalar(@{$pog->{'@options'}}))."</td>"; 
					}
				else {
					$c .= "<td valign=top>0</td>";
					}
				
				}
			else {
				$c .= "<td valign='top'>$pog->{'prompt'} </td>";
				$c .= "<td valign='top'>$pog->{'type'} </td>";
				if (($pog->{'type'} eq 'text') || ($pog->{'type'} eq 'textarea') || ($pog->{'type'} eq 'number') || 
					 ($pog->{'type'} eq 'readonly') || ($pog->{'type'} eq 'calendar') || ($pog->{'type'} eq 'hidden') || 
					($pog->{'type'} eq 'assembly')) {
					$c .= "<td valign='top'>n/a</td>";
					}
				elsif ((not defined $pog->{'@options'}) || (scalar(@{$pog->{'@options'}}) == 0)) {
					$c .= "<td valign='top'><div class='error'>0 options - CORRUPT!</div></td>";
					}
				else {
					$c .= "<td valign='top'>".scalar(@{$pog->{'@options'}})." options ";
					if ( (scalar(@{$pog->{'@options'}})>1) && (($pog->{'type'} eq 'select') || ($pog->{'type'} eq 'attrib') || ($pog->{'type'} eq 'radio')) ) {
						$c .= "  <a href=\"#\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=GRIDEDIT&PRODUCT=$PRODUCT&POG=".uri_escape($pog->{'id'})."');\">[View]</a>";
						}
					$c .= "</td>";
					}
				}
			$c .= "<td valign='top'>$pog->{'id'} </td>";
			$c .= "</tr>";
			}
		$GTOOLS::TAG{'<!-- POG_OUTPUT -->'} = $c;
		}

	##
	## OUTPUT LIST OF AVAILABLE SOGS
	##	
	my $listref = &POGS::list_sogs($USERNAME);
	my $out = '';
	my $counter = 0;
	foreach my $id (reverse sort keys %{$listref}) {
		# my @sogs = &POGS::text_to_struct($USERNAME,&POGS::load_sog($USERNAME,$id),0);
		# my $sogref = pop @sogs;
		my ($sogref) = &POGS::load_sogref($USERNAME,$id);
		my $row = ($counter++%2);
		$out .= "<tr class='r$row'><td>";
		if ((not defined $pogids{$id}) && ($PRODUCT ne '')) {
			$out .= "<input value=\"add\" type=\"button\" class=\"minibutton\" onClick=\"navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=ADDSOG&PRODUCT=$PRODUCT&SOG=".&uri_escape($id)."');\">";
			} 
		else { 
			$out .= "<img src=\"/images/blank.gif\" width=13 height=13 border=0>"; 
			}

		if ($PRODUCT eq '') {
			$out .= "<button type=\"button\" class=\"minibutton\" onClick=\"return navigateTo('/biz/product/options2/index.cgi?MODE=$::MODE&VERB=EDITSOG&PRODUCT=$PRODUCT&SOG=".$id."');\">Edit SOG $id</button>";
			}

		# $DEBUG = 1;
		if ($DEBUG) {  $out .= "<td><pre>".Dumper($sogref)."</pre></td>"; }
		$out .= "</td><td>$id: $listref->{$id}</div></td>";
		$out .= "</tr>";
		}

	if ($out eq '') {
		$out .= "<tr><td colspan='3'><div class='warning'>There are currently no store option groups</div></td></tr>";
		}
	$GTOOLS::TAG{'<!-- SOGS_OUTPUT -->'} .= $out;
	$GTOOLS::TAG{'<!-- TS -->'} = time();


	$template_file = 'index.shtml';
	if ($PRODUCT eq '') { 
		my $out = '';
		my $count=0;
		my $swogsref = &POGS::list_swogs($USERNAME);
		foreach my $id (keys %{$swogsref}) {
			if ($count==0) { $count = 1; } else { $count = 0; }
			$out .= "<tr><td class=\"r$count\">
				<input value=\"import\" type=\"button\" class=\"minibutton\" onClick=\"navigateTo('/biz/product/options2/index.cgi?VERB=COPYSWOG&ID=$id');\"> 
				&nbsp; 
				</td><td class=\"r$count\">$id: $swogsref->{$id}</td></tr>";
			}
		$GTOOLS::TAG{'<!-- SWOGS_OUTPUT -->'} = $out;

		$template_file = 'indexsog.shtml'; 
		}

	# $GTOOLS::TAG{'<!-- EXIT_URL -->'} = '/biz/product/edit.cgi?PID='.$PRODUCT;
	# $GTOOLS::TAG{'<!-- EXIT_URL -->'} = 'app.ext.admin_prodEdit.a.showPanelsFor($(this).closest('[data-pid]').attr('data-pid'));
	# print STDERR "FLAGS: $FLAGS\n";
	#if ($FLAGS =~ /,TOKENAUTH,/) {
	#	$GTOOLS::TAG{'<!-- EXIT_CLICK -->'} = "navigateTo('/biz/product/index.cgi?PRODUCT=$PRODUCT&VERB=XML_END');";
	#	}
	#elsif ($::MODE =~ /^XML:/) {
	#	$GTOOLS::TAG{'<!-- EXIT_CLICK -->'} = "navigateTo('/biz/product/index.cgi?PRODUCT=$PRODUCT&MODE=$::MODE&VERB=XML_END');";
	#	}
	#elsif ($::MODE =~ /^THASH:/) {
	#	$GTOOLS::TAG{'<!-- EXIT_CLICK -->'} = "navivateTo('/biz/product/index.cgi?PRODUCT=$PRODUCT&MODE=$::MODE&VERB=XML_END');";
	#	}
	}

$GTOOLS::TAG{'<!-- PRODUCT -->'} = $PRODUCT;

use Data::Dumper;
#print STDERR "PWD: $ENV{'PWD'}\n";
#print STDERR Dumper(\%ENV);
#chdir("/httpd/htdocs/biz/product/options2");

if (scalar(@MSGS)) {
	$GTOOLS::TAG{'<!-- MSGS -->'} = &GTOOLS::show_msgs(\@MSGS);
	}

&GTOOLS::output('*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,'*LU'=>$LU,title=>'',js=>2+4,file=>$template_file,header=>1);


