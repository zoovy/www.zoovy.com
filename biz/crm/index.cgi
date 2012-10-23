#!/usr/bin/perl

use strict;
use Data::Dumper;
use Text::Wrap;
$Text::Wrap::columns = 80;

use lib "/httpd/modules";
require DBINFO;
require LUSER;
require GTOOLS;
require CUSTOMER::TICKET;
require CUSTOMER;
require CART2;
require ZTOOLKIT;


require LUSER;
my ($LU) = LUSER->authenticate(flags=>'_M&8');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my ($udbh) = &DBINFO::db_user_connect($USERNAME);

my $tabs = 1;		## should we display or hide tabs..

my @BC = ( { name=>"Tickets", link=>"/biz/crm" } );
my @TABS = ();

my $template_file = '';
my $VERB = uc($ZOOVY::cgiv->{'VERB'});
my $TKTCODE = $ZOOVY::cgiv->{'TKTCODE'};
my $CID = 0;

if ($FLAGS !~ /,CRM,/) {
	$VERB = 'DENIED';
	$template_file = 'denied.shtml';
	}


my @ERRORS = ();


my $CTCONFIG = {};
my $webdbref = &ZWEBSITE::fetch_website_dbref($USERNAME,$PRT);
if (($webdbref->{'crmtickets'} eq '') && ($VERB ne 'CONFIG') && ($VERB ne 'CONFIG-SAVE')) {	
	push @ERRORS, "WARN:CRM Case Management/Returns is not currently configured/enabled.";
	$VERB = 'CONFIG';
	}
else {
	$CTCONFIG = &ZTOOLKIT::parseparams($webdbref->{'crmtickets'});
	}



#mysql> desc CHECKOUTS;
#+----------------+-------------------------------+------+-----+---------+----------------+
#| Field          | Type                          | Null | Key | Default | Extra          |
#+----------------+-------------------------------+------+-----+---------+----------------+
#| ID             | int(11)                       | NO   | PRI | NULL    | auto_increment |
#| MID            | int(10) unsigned              | NO   | MUL | 0       |                |
#| USERNAME       | varchar(20)                   | NO   |     | NULL    |                |
#| SDOMAIN        | varchar(50)                   | NO   |     | NULL    |                |
#| ASSIST         | enum('NONE','CALL','CHAT','') | NO   |     | NULL    |                |
#| CARTID         | varchar(36)                   | NO   |     | NULL    |                |
#| CID            | int(10) unsigned              | NO   |     | 0       |                |
#| CREATED_GMT    | int(10) unsigned              | NO   |     | 0       |                |
#| HANDLED_GMT    | int(10) unsigned              | NO   |     | 0       |                |
#| CLOSED_GMT     | int(10) unsigned              | NO   |     | 0       |                |
#| ASSISTID       | varchar(5)                    | NO   |     | NULL    |                |
#| CHECKOUT_STAGE | varchar(8)                    | NO   |     | NULL    |                |
#+----------------+-------------------------------+------+-----+---------+----------------+
#12 rows in set (0.02 sec)
if ($VERB eq 'CHECKOUTASSIST') {
	$template_file = 'checkoutassist.shtml';

	my $c = '';
	my $pstmt = "select * from CHECKOUTS where MID=$MID /* $USERNAME */";
	my $sth = $udbh->prepare($pstmt);
	$sth->execute();
	while ( my $ref = $sth->fetchrow_hashref() ) {
		$c .= "<tr><td>$ref->{'ASSIST'}</td><td>$ref->{'ASSISTID'}</td><td>$ref->{'CREATED_GMT'}</td></tr>";
		}
	$sth->finish();	
	$GTOOLS::TAG{'<!-- CHECKOUTS -->'} = $c;
	}




if ($VERB eq 'UNIVERSAL-LOOKUP') {
	## this gets only one value: lookup so we use pattern matching to try and figure out what the heck
	##		we're looking for

	my $lookup = $ZOOVY::cgiv->{'lookup'};
	$lookup = uc($lookup);
	$lookup =~ s/^[\s]+//gs;	# strip leading whitespace
	$lookup =~ s/[\s]+$//gs;	# strip trailing whitespace

	if ($lookup =~ /^[\d]{4,4}\-[\d]{2,2}\-[\d]+$/) {
		## this is an order #
		$VERB = 'EXEC-SEARCH'; $ZOOVY::cgiv->{'orderid'} = $lookup;
		}
	elsif ($lookup =~ /\@/) {
		## this is an email 
		$VERB = 'EXEC-SEARCH'; $ZOOVY::cgiv->{'email'} = $lookup;
		}
	elsif ($lookup =~ /^[\d]{3,3}-[\d]{3,3}-[\d]{1,7}$/) {
		## this is an email 
		$VERB = 'EXEC-SEARCH'; $ZOOVY::cgiv->{'phone'} = $lookup;
		}
	else {
		$VERB = 'EXEC-SEARCH'; $ZOOVY::cgiv->{'ticket'} = $lookup;
		}

	}

if ($VERB eq 'EXEC-SEARCH') {
	$VERB = '';

	# if (($VERB eq '') && (length($lookup)==6) && ($lookup =~ /^[A-Z0-9]+$/)) {
	if (($VERB eq '') && ($ZOOVY::cgiv->{'ticket'} ne '')) {
		my $lookup = $ZOOVY::cgiv->{'ticket'};
		## it's a 6 digit ticket code
		print STDERR "LOOKUP: $lookup\n";
		my ($T) = CUSTOMER::TICKET->new($USERNAME,"+$lookup",PRT=>$PRT);
		if (defined $T) { 
			$VERB = 'TICKET-VIEW';  $TKTCODE = $lookup; 
			}
		}
		
	 if (($VERB eq '') && ($ZOOVY::cgiv->{'orderid'} ne '')) {
		my $lookup = $ZOOVY::cgiv->{'orderid'};
		if ($lookup eq '') { $lookup = '*'; }
		my ($O2) = CART2->new_from_oid($USERNAME,$lookup);
      if ((defined $O2) && (ref($O2) eq 'CART2')) {
			($CID) = &CUSTOMER::searchfor_cid($USERNAME,$PRT,'EMAIL',$O2->in_get('bill/email'));
			if ($CID>0) {
				$VERB = 'TICKETS-SHOWCID-ALL';
				}
         }
		}

	# if (($VERB eq '') && ($lookup =~ /^[\d]{3,3}\-[\d]{3,3}-[\d]{4,4}$/)) {
	if (($VERB eq '') && ($ZOOVY::cgiv->{'phone'} ne '')) {
		my $lookup = $ZOOVY::cgiv->{'phone'};
		## PHONE NUMBER: ###-###-####
		($CID) = &CUSTOMER::searchfor_cid($USERNAME,$PRT,'PHONE',$lookup);
		if ($CID>0) {
			$VERB = 'TICKETS-SHOWCID-ALL';
			}
		}

	# if (($VERB eq '') && (&ZTOOLKIT::validate_email($lookup))) {
	if (($VERB eq '') && ($ZOOVY::cgiv->{'email'} ne '')) {
		my $lookup = $ZOOVY::cgiv->{'email'};
		## EMAIL user@domain.com
		($CID) = &CUSTOMER::searchfor_cid($USERNAME,$PRT,'EMAIL',$lookup);
		if ($CID>0) {
			## we didn't find a record for the customer.
			$VERB = 'TICKETS-SHOWCID-ALL';
			}
		else {
			## 
			}
		}


	if ($VERB eq '') {
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "Could not find ticket, or no results found"; 
		$VERB = 'SEARCH';
		}

	}


##
##
##
if ($VERB eq 'SEARCH') {

	$GTOOLS::TAG{'<!-- TICKET -->'} = ($ZOOVY::cgiv->{'TICKET'})?&ZOOVY::incode($ZOOVY::cgiv->{'TICKET'}):'';
	$GTOOLS::TAG{'<!-- ORDERID -->'} = ($ZOOVY::cgiv->{'ORDERID'})?&ZOOVY::incode($ZOOVY::cgiv->{'ORDERID'}):'';
	$GTOOLS::TAG{'<!-- EMAIL -->'} = ($ZOOVY::cgiv->{'EMAIL'})?&ZOOVY::incode($ZOOVY::cgiv->{'ORDERID'}):'';
	$GTOOLS::TAG{'<!-- PHONE -->'} = ($ZOOVY::cgiv->{'PHONE'})?&ZOOVY::incode($ZOOVY::cgiv->{'ORDERID'}):'';
	# $GTOOLS::TAG{'<!-- CUSTOMER -->'} = ($ZOOVY::cgiv->{'CUSTOMER'})?&ZOOVY::incode($ZOOVY::cgiv->{'ORDERID'}):'';

	$template_file = 'search.shtml';
	}





if ($VERB eq 'CREATE-SAVE') {
	my $CID = 0;
	my $orderid = $ZOOVY::cgiv->{'orderid'};
	my $email = $ZOOVY::cgiv->{'email'};
	my $phone = $ZOOVY::cgiv->{'phone'};

	if (($CID<=0) && ($orderid ne '')) {
		my ($O2) = CART2->new_from_oid($USERNAME,$orderid);
		if (not defined $O2) {
			$orderid = '';
			}
		else {
			$email = $O2->in_get('bill/email');
			$phone = $O2->in_get('bill/phone');
			}
		}

	if (($CID<=0) && (&ZTOOLKIT::validate_email($email))) {
		## Lookup by email
		($CID) = &CUSTOMER::resolve_customer_id($USERNAME,$PRT,$email);
		}

	if (($CID<=0) && ($phone ne '')) {
		## Lookup by phone
		($CID) = &CUSTOMER::searchfor_cid($USERNAME,$PRT,'PHONE',$phone);
		}

	if (($CID<=0) && ($ZOOVY::cgiv->{'create'})) {
		if (&ZTOOLKIT::validate_email($email)) {
			my ($c) = CUSTOMER->new($USERNAME,PRT=>0,CREATE=>1,EMAIL=>$email,PRT=>$PRT);
			$c->save();
			$CID = $c->cid();
			}
		}

	if (($CID>0) || ($orderid ne '')) {
		## created a ticket.
		my ($t) = CUSTOMER::TICKET->new($USERNAME,$PRT,ORDERID=>$orderid,CID=>$CID,
					PRT=>$PRT,
					SUBJECT=>$ZOOVY::cgiv->{'subject'},
					NOTE=>$ZOOVY::cgiv->{'body'},
					CLASS=>$ZOOVY::cgiv->{'class'},
					);
		if (defined $t) {
			$VERB = 'TICKET-VIEW';
			$TKTCODE = $t->tktcode();
			}
		else {
			$GTOOLS::TAG{'<!-- ERRORS -->'} = "INTERNAL ERROR OCCURRED ATTEMPTING TO CREATE TICKET";
			$VERB = 'CREATE';
			}
		}
	else {
		## FAILED
		$GTOOLS::TAG{'<!-- ERRORS -->'} = "Could not lookup EMAIL, PHONE, or ORDERID";
		$VERB = 'CREATE';
		}
	}


if ($VERB eq 'CREATE') {
	$GTOOLS::TAG{'<!-- ORDERID -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'orderid'});
	$GTOOLS::TAG{'<!-- EMAIL -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'email'});
	$GTOOLS::TAG{'<!-- PHONE -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'phone'});
	$GTOOLS::TAG{'<!-- SUBJECT -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'subject'});
	$GTOOLS::TAG{'<!-- BODY -->'} = &ZOOVY::incode($ZOOVY::cgiv->{'body'});
	$GTOOLS::TAG{'<!-- CHK_CLASS_NONE -->'} = ($ZOOVY::cgiv->{'class'} eq 'NONE')?'selected':'';
	$GTOOLS::TAG{'<!-- CHK_CLASS_PRESALE -->'} = ($ZOOVY::cgiv->{'class'} eq 'PRESALE')?'selected':'';
	$GTOOLS::TAG{'<!-- CHK_CLASS_POSTSALE -->'} = ($ZOOVY::cgiv->{'class'} eq 'POSTSALE')?'selected':'';
	$GTOOLS::TAG{'<!-- CHK_CLASS_RETURN -->'} = ($ZOOVY::cgiv->{'class'} eq 'RETURN')?'selected':'';
	$GTOOLS::TAG{'<!-- CHK_CLASS_EXCHANGE -->'} = ($ZOOVY::cgiv->{'class'} eq 'EXCHANGE')?'selected':'';
	$template_file = 'create.shtml';
	}





if (($VERB eq 'TICKET-ASK') || ($VERB eq 'TICKET-UPDATE') || ($VERB eq 'TICKET-CLOSE')) {
	my ($T) = CUSTOMER::TICKET->new($USERNAME,"+$TKTCODE",PRT=>$PRT);
	if ($ZOOVY::cgiv->{'note'} ne '') {
		$T->addMsg($LUSERNAME,$ZOOVY::cgiv->{'note'},($ZOOVY::cgiv->{'flag_private'})?1:0);
		}

	my %vars = ();
	$vars{'escalate'} = ($ZOOVY::cgiv->{'flag_escalate'})?1:0;
	$vars{'class'} = $ZOOVY::cgiv->{'class'};

	if (($vars{'class'} eq 'PRESALE') || ($vars{'class'} eq 'POSTSALE')) {
		$T->cdSet("tags",$ZOOVY::cgiv->{'CD*tags'});
		}
	elsif (($vars{'class'} eq 'EXCHANGE') || ($vars{'class'} eq 'RETURN')) {
		$T->cdSet("rtnauth",(defined $ZOOVY::cgiv->{'CD*rtnauth'})?1:0);
		$T->cdSet("rtncredit",$ZOOVY::cgiv->{'CD*rtncredit'});
		$T->cdSet("rtnvia",$ZOOVY::cgiv->{'CD*rtnvia'});
		}

	if ($VERB eq 'TICKET-ASK') {
		## ASK CUSTOMER A QUESTION
		$VERB = 'TICKET-VIEW';
		$T->changeState('WAIT',%vars);
		$LU->log('TICKET.ASK',"Set Ticket: ".$T->tktcode()." to waiting","SAVE");
		}

	##
	##
	##
	if ($VERB eq 'TICKET-UPDATE') {
		## UPDATE A TICKET
		$T->changeState('ACTIVE',%vars);
		$LU->log('TICKET.UPDATE',"Updated Ticket: ".$T->tktcode(),"SAVE");
		$VERB = 'TICKET-VIEW';
		}

	if ($VERB eq 'TICKET-CLOSE') {
		## CLOSE A TICKET
		$T->changeState('CLOSE',%vars);
		$LU->log('TICKET.CLOSE',"Closed Ticket: ".$T->tktcode(),"SAVE");
		$VERB = '';
		}

	}


if ($VERB eq 'TICKET-UNLOCK') {
	## A STUB FUNCTION USED WHEN RETURNING TO MAIN MENU
	$VERB = '';
	}




##
##
##
if ($VERB eq 'TICKET-VIEW') {	

	$GTOOLS::TAG{'<!-- TKTCODE -->'} = $TKTCODE;
	my ($T) = CUSTOMER::TICKET->new($USERNAME,"+$TKTCODE",PRT=>$PRT);

	if (not defined $T) {
		warn "Could not load TKTCODE $TKTCODE";
		$VERB = '';
		}
	else {
		
		my ($ts,$user) = $T->getLock();
		my $tsdiff = time()-$ts;
		if ( $tsdiff < 15*60 ) {
			push @ERRORS, "WARN: Warning user \"$user\" accessed the ticket ".&ZTOOLKIT::pretty_time_since(1,$tsdiff)." ago, they may still be editing.";
			}
		else {
			$T->setLock($LUSERNAME);
			}


		$GTOOLS::TAG{'<!-- STATUS -->'} = $T->{'STATUS'};
		$GTOOLS::TAG{'<!-- ORDER -->'} = '';
		$GTOOLS::TAG{'<!-- SINCE -->'} = '';

		my $inforef = $T->buildInfo();

		if ($inforef->{'orderid'} ne '') {
			my $orderid = $inforef->{'orderid'};
			$GTOOLS::TAG{'<!-- ORDERID -->'} = "<a target=_new href=\"/biz/orders/index.cgi?VERB=QUICKSEARCH&find_text=$orderid&find_status=ANY\">$orderid</a>";
			}		
		else {
			$GTOOLS::TAG{'<!-- ORDERID -->'} = "<i>Not Set</i>";
			}

		$GTOOLS::TAG{'<!-- EMAIL -->'} = $inforef->{'email'};
		$GTOOLS::TAG{'<!-- PHONE -->'} = $inforef->{'phone'};

		$GTOOLS::TAG{'<!-- TKT_OPEN -->'} = ($inforef->{'TKT_open'}>0)?"<a href=\"index.cgi?VERB=TICKETS-SHOWCID-OPEN&CID=$inforef->{'cid'}\">$inforef->{'TKT_open'}</a>":'0';
		$GTOOLS::TAG{'<!-- TKT_TOTAL -->'} = ($inforef->{'TKT_total'}>0)?"<a href=\"index.cgi?VERB=TICKETS-SHOWCID-ALL&CID=$inforef->{'cid'}\">$inforef->{'TKT_total'}</a>":'0';
		$GTOOLS::TAG{'<!-- TKT_WAIT -->'} = ($inforef->{'TKT_wait'}>0)?"<a href=\"index.cgi?VERB=TICKETS-SHOWCID-WAIT&CID=$inforef->{'cid'}\">$inforef->{'TKT_wait'}</a>":'0';

		$GTOOLS::TAG{'<!-- FULLNAME -->'} = ($inforef->{'fullname'} ne '')?$inforef->{'fullname'}:'<i>Not Set</i>';
		if ($inforef->{'cid'}>0) {
			$GTOOLS::TAG{'<!-- FULLNAME -->'} .= " <a target=\"customer_edit\" href=\"/biz/utilities/customer/index.cgi?ACTION=SEARCH&scope=CID&searchfor=$inforef->{'cid'}\">[EDIT]</a>";
			}
		$GTOOLS::TAG{'<!-- ORDER_COUNT -->'} = $inforef->{'order_count'};
		$GTOOLS::TAG{'<!-- CUSTOMER_SINCE -->'} = $inforef->{'customer_since'};

		$GTOOLS::TAG{'<!-- SUBJECT -->'} = &ZOOVY::incode($T->{'SUBJECT'});

  		my $note = Text::Wrap::wrap("","",$T->{'NOTE'});
     	$note = &ZOOVY::incode($note);
		$GTOOLS::TAG{'<!-- BODY -->'} = "<pre>".$note."</pre>";


		$GTOOLS::TAG{'<!-- CHK_CLASS_PRESALE -->'} = ($T->{'CLASS'} eq 'PRESALE')?'selected':'';
		$GTOOLS::TAG{'<!-- CHK_CLASS_POSTSALE -->'} = ($T->{'CLASS'} eq 'POSTSALE')?'selected':'';
		$GTOOLS::TAG{'<!-- CHK_CLASS_RETURN -->'} = ($T->{'CLASS'} eq 'RETURN')?'selected':'';
		$GTOOLS::TAG{'<!-- CHK_CLASS_EXCHANGE -->'} = ($T->{'CLASS'} eq 'EXCHANGE')?'selected':'';


		my $c = '';
		if (($T->{'CLASS'} eq 'PRESALE') || ($T->{'CLASS'} eq 'POSTSALE')) {
			my $tags = &ZOOVY::incode($T->cdGet('tags'));
			$c .= qq~
<table>
<tr>
	<td>Tags:</td>
	<td><input size="100" type="textbox" value="$tags" name="CD*tags"></td>
</tr>
</table>
<div class="hint"><i>Tags are user defined words for grouping related tickets. 
We anticipate making this data accessible via reports in future releases.</i></div>
~;
			}
		elsif (($T->{'CLASS'} eq 'RETURN') || ($T->{'CLASS'} eq 'EXCHANGE')) {
			my $rtnauth = ($T->cdGet("rtnauth")?'checked':'');
			my $rtncredit = &ZOOVY::incode($T->cdGet("rtncredit"));
			my $rtnvia = &ZOOVY::incode($T->cdGet("rtnvia"));

			my ($O2) = undef;
			if (defined $T->oid()) {
				($O2) = CART2->new_from_oid($USERNAME,$T->oid(),'create'=>0);
				}

			if (defined $O2) {
				$c .= sprintf("<div class='success'>Order ID: %s</div>",$T->oid());

				$c .= "<table class='zoovytable'>";
				$c .= "<tr class='zoovysub2header'>";
				$c .= "<td nowrap># Ordered</td>";
				$c .= "<td nowrap># to Return</td>";
				$c .= "<td nowrap>Item Description</td>";
				$c .= "<td nowrap>Action</td>";
				$c .= "<td nowrap>Reason</td>";
				$c .= "<td nowrap>Restock \$</td>";
				$c .= "<td nowrap>Serial #</td>";
				$c .= "</tr>";
				foreach my $item (@{$O2->stuff2()->items()}) {
					my $qty = $item->{'qty'};
					$c .= "<tr>";
					$c .= "<td align=center>$qty</td>";
					$c .= "<td align=center><input size=3 type=textbox value=\"0\"></td>";
					$c .= "<td nowrap>$item->{'prod_name'}</td>";
					$c .= "<td>";
					$c .= "<select name=\"\">";
					$c .= "<option value=''>For Exchange</option>";
					$c .= "<option value=''>For Refund</option>";
					$c .= "<option value=''>For X-Ship</option>";
					$c .= "<option value=''>Refund Only</option>";
					$c .= "</select>";
					$c .= "</td>";
					$c .= "<td>";
					$c .= "<select name=\"\">";
					$c .= "<option value=''>Not Specified</option>";
					$c .= "<option value=''>Did Not Want</option>";
					$c .= "<option value=''>Damaged</option>";
					$c .= "</select>";
					$c .= "</td>";
					$c .= "<td><input size=5 type=\"textbox\"></td>";
					$c .= "<td><input size=10 type=\"textbox\"></td>";
					$c .= "</tr>";
					}
				$c .= "<tr>";
				$c .= "<td colspan=3><input class='button' type='submit' value=' Add Items to RMA '></td>";
				$c .= "</tr>";
				$c .= "</table>";
				}
			else {
				$c .= "<div class='error'>Warning - order not linked, not a supported case for a return record.</div>";
				}

			$c .= qq~
<table>
<tr>
	<td><input type="checkbox" $rtnauth name="CD*rtnauth"> Return Authorized.</td>
</tr>
<tr>
	<td>Authorized Credit Amount: <input type="textbox" name="CD*rtncredit" value="$rtncredit"></td>
</tr>
<tr>
	<td>Credit Issued via: <input type="textbox" name="CD*rtnvia" value="$rtnvia"></td>
</tr>
</table>
~;
			
			}
		$GTOOLS::TAG{'<!-- CLASS_INFO -->'} = $c;

		$c = '';
		my $msgsref = $T->getMsgs();
		if ((defined $msgsref) && (ref($msgsref) eq 'ARRAY')) {
			foreach my $msg (reverse @{$msgsref}) {

      		my $note = Text::Wrap::wrap("","",$msg->{'NOTE'});
         	$note = &ZOOVY::incode($note);

				my $author = $msg->{'AUTHOR'};
				if ($author eq '') { $author = 'CUSTOMER'; }
				$author = &ZOOVY::incode($author);

				my $bgcolor = '#99FF99';
				if ($msg->{'PRIVATE'}) { $bgcolor = '#9999FF';  $author .= " (PRIVATE) "; }

				$c .= qq~
<tr bgcolor="$bgcolor">
	<td>
		<table border=0 cellspacing=0 cellpadding=0 width=100%>
			<tr>
				<td aligh='left'><b>$author</b></td>
				<td align='right'><b>~.&ZTOOLKIT::pretty_date($msg->{'CREATED_GMT'},1).qq~</b>
				</td>
			</tr>
		</table>
	</td>
</tr>~;
				$c .= "<tr><td><pre>$note</pre></td></tr>";
				}
			}
		
		if ($c eq '') {
			$c = qq~<tr><td><i>No updates have been made to this ticket.</i></td></tr>~;
			}
		else {
			}
		$GTOOLS::TAG{'<!-- TICKET_HISTORY -->'} = $c;	


		push @BC, { name=>"Ticket ".$T->tktcode(), link=>"/biz/crm/index.cgi?VERB=TICKET-VIEW&TKTCODE=".$T->tktcode(), };

		$template_file = 'ticket-view.shtml';
		}
	}



##############################################################################################
##
## 
## TICKET LISTING CODE (displays a list of crm in various status, also used for search)
##
##
if (($VERB eq '') || ($VERB =~ /TICKETS\-/)) {
	$template_file = 'index.shtml';

	if ($VERB eq '') { $VERB = 'TICKETS-OPEN'; }	
	my $SORT = $ZOOVY::cgiv->{'SORT'};
	if ($SORT eq '') { $SORT = 'ID-0'; }
	($SORT,my $SORTDIR) = split(/-/,$SORT);
	$SORTDIR = int($SORTDIR);

	foreach my $key ('ID','STATUS','CLASS','CREATED') {
	
		my $link = "index.cgi?VERB=$VERB&SORT=$key-$SORTDIR";
		my $updown = '';
		if ($SORT eq $key) {
			$link="index.cgi?VERB=$VERB&SORT=$key-".(($SORTDIR)?0:1);
			if ($SORTDIR) { $updown = '<font style="font-weight: normal;">&#8657</font>'; } else { $updown = '<font style="font-weight: normal;">&#8659;</font>'; }
			}

		$GTOOLS::TAG{'<!-- '.$key.'_SORT -->'} = qq~<a href='$link'>$key $updown</a>~; 
		}
	
	
	my $ticketsref = undef;
	if ($VERB eq 'TICKETS-NEW') {
		## Shows all open tickets
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,STATUS=>'NEW',SORT=>"$SORT-$SORTDIR",CID=>$CID);	
		push @BC, { name=>"All New Tickets" };
		$GTOOLS::TAG{'<!-- HEADER -->'} = "New Tickets:";
		$tabs++;
		}
	elsif ($VERB eq 'TICKETS-OPEN') {
		## Shows all open tickets
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,STATUS=>'OPEN',SORT=>"$SORT-$SORTDIR",CID=>$CID);	
		push @BC, { name=>"All Open Tickets" };
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Open Tickets:";
		$tabs++;
		}
	elsif ($VERB eq 'TICKETS-WAITING') {
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,STATUS=>'WAIT',SORT=>"$SORT-$SORTDIR");
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Waiting Tickets";
		push @BC, { name=>"All Waiting Tickets" };
		$tabs++;
		}
	elsif ($VERB eq 'TICKETS-SHOWCID-ALL') {
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,CID=>$CID,SORT=>"$SORT-$SORTDIR");
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Search Results CID=$CID: (ALL)";
		push @BC, { name=>"Show All " };
		if ($CID>0) { push @BC, { name=>"CID: $CID" }; }
		}
	elsif ($VERB eq 'TICKETS-SHOWCID-OPEN') {
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,CID=>$CID,STATUS=>'OPEN',SORT=>"$SORT-$SORTDIR");
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Search Results CID=$CID: (OPEN)";
		push @BC, { name=>"Show Open" };
		if ($CID>0) { push @BC, { name=>"CID: $CID" }; }
		}
	elsif ($VERB eq 'TICKETS-SHOWCID-WAIT') {
		$ticketsref = &CUSTOMER::TICKET::getTickets($USERNAME,CID=>$CID,STATUS=>'WAIT',SORT=>"$SORT-$SORTDIR");
		$GTOOLS::TAG{'<!-- HEADER -->'} = "Search Results CID=$CID: (WAITING)";
		push @BC, { name=>"Show Waiting" };
		if ($CID>0) { push @BC, { name=>"CID: $CID" };  }
		}


	if (defined $ticketsref) {
		my $c = '';
		my $r = '';
		foreach my $tkt (@{$ticketsref}) {
			$r = ($r eq 'r0')?'r1':'r0'; 
			if ($tkt->{'ESCALATED'}) { $r = 'rs'; }

			if ($tkt->{'SUBJECT'} eq '') { $tkt->{'SUBJECT'} = 'No subject given.'; }
			if ($tkt->{'CLASS'} eq '') { $tkt->{'CLASS'} = '?'; }
			elsif ($tkt->{'CLASS'} eq 'EXCHANGE') { $tkt->{'CLASS'} = 'EXCHG'; }

			$tkt->{'SUBJECT'} = &ZOOVY::incode($tkt->{'SUBJECT'});
			$c .= qq~<tr class=\"$r\">~;
			$c .= qq~<td><div class='small'><a href=\"index.cgi?VERB=TICKET-VIEW&TKTCODE=$tkt->{'TKTCODE'}\">$tkt->{'TKTCODE'}</a></td>~;


			$c .= qq~<td><div class='small'>$tkt->{'STATUS'}</td>~;


#			if ($tkt->{'CLASS'} eq 'EXCHG') { $tkt->{'CLASS'} = 'exchange'; }
#			if ($tkt->{'CLASS'} eq 'RETURN') { $tkt->{'CLASS'} = 'return'; }
			$c .= qq~<td>$tkt->{'CLASS'}</td>~;
			$c .= qq~<td><div class='small'>$tkt->{'SUBJECT'}</td>~;
			$c .= qq~<td><div class='small'>~.&ZTOOLKIT::pretty_date($tkt->{'CREATED_GMT'}).qq~</td>~;

#			if ($VERB ne '') {
#				$c .= "<td>".$tkt->{'STATUS'}."</td>";
#				}

			$c .= qq~</tr>~;
			}

		if ($c eq '') {

			if ($VERB eq '') {
				$c = qq~<tr><td colspan=5><img align="left" src='images/smiley.jpg'><font color='blue'><h2>Yippie! There are no more active calls or tickets!</h2><br><br><center><input class="button" type="button" value=" Refresh " onClick="document.location='/biz/crm/index.cgi?ts=~.time().qq~';"></center></td></tr>~;
				}
			else {
				$c = qq~<tr><td colspan=5><i>No results found</i></td></tr>~;
				}

			}
		$GTOOLS::TAG{'<!-- TICKETS -->'} = $c;
		}

	}


if ($VERB eq 'CONFIG-SAVE') {
	$VERB = 'CONFIG';

	if (not defined $ZOOVY::cgiv->{'style'}) {
		## disabled
		$webdbref->{'crmtickets'} = '';
		}
	else {
		## enabled
		$CTCONFIG->{'v'} = 1;
		$CTCONFIG->{'is_external'} = 0;
		if ($ZOOVY::cgiv->{'style'} == 10) {
			$CTCONFIG->{'is_external'} = 1;
			}
		$webdbref->{'crmtickets'} = &ZTOOLKIT::buildparams($CTCONFIG);
		}


	my $ticket_count = $ZOOVY::cgiv->{'ticket_number'};
	my $ticket_seq = $ZOOVY::cgiv->{'sequence'};
	my $email_cleanup = (defined $ZOOVY::cgiv->{'email_cleanup'})?1:0;
	
	my $EMAIL = $ZOOVY::cgiv->{'EMAIL'};
	my $pstmt = DBINFO::insert($udbh,'CRM_SETUP',{
		MID=>$MID, PRT=>$PRT, USERNAME=>$USERNAME,
		EMAIL_ADDRESS=>$EMAIL,
		EMAIL_CLEANUP=>$email_cleanup,
		TICKET_COUNT=>$ticket_count,
		TICKET_SEQ=>$ticket_seq,
		},debug=>2,key=>['MID','PRT']);
	$udbh->do($pstmt);
	print STDERR "PSTMT: $pstmt\n";

	
	require PLUGIN::FUSEMAIL;
	my %VALID_EMAILS = ();
	foreach my $uref (&PLUGIN::FUSEMAIL::report($USERNAME)) {
		$VALID_EMAILS{ $uref->{'email'} }++;
		}

#	my ($s) = SYNDICATION->new($USERNAME, "#$PRT", 'CRM');
#	if ($VALID_EMAILS{$EMAIL}) {
#		$s->set('.email',$EMAIL);
#		$s->set('NEXTRUN_GMT',time());
#		$s->save();
#		}


	&ZWEBSITE::save_website_dbref($USERNAME,$webdbref,$PRT);
	}

if ($VERB eq 'CONFIG') {
	$template_file = 'config.shtml';

	$GTOOLS::TAG{'<!-- STYLE_0 -->'} = ($CTCONFIG->{'is_external'}==0)?'selected':'';
	$GTOOLS::TAG{'<!-- STYLE_10 -->'} = ($CTCONFIG->{'is_external'}==1)?'selected':'';

	my $pstmt = "select * from CRM_SETUP where MID=$MID /* $USERNAME */ and PRT=$PRT";
	my ($crm_ref) = $udbh->selectrow_hashref($pstmt);
	
	if (not defined $crm_ref) {
		## not initialized - so we default.
		$crm_ref->{'TICKET_COUNT'} = 1000;
		$crm_ref->{'TICKET_SEQ'} = 'ALPHA';
		}
	
	$GTOOLS::TAG{'<!-- CRM_TICKET_NUMBER -->'} = $crm_ref->{'TICKET_COUNT'};
	$GTOOLS::TAG{'<!-- SELECT_TICKET_SEQ_ALPHA -->'} = ($crm_ref->{'TICKET_SEQ'} eq 'ALPHA')?'selected':'';
	$GTOOLS::TAG{'<!-- SELECT_TICKET_SEQ_SEQ5 -->'} = ($crm_ref->{'TICKET_SEQ'} eq 'SEQ5')?'selected':'';
	$GTOOLS::TAG{'<!-- SELECT_TICKET_SEQ_DATEYYMM4 -->'} = ($crm_ref->{'TICKET_SEQ'} eq 'DATEYYMM4')?'selected':'';
	$GTOOLS::TAG{'<!-- CHK_EMAIL_CLEANUP -->'} = ($crm_ref->{'EMAIL_CLEANUP'})?'checked':'';

#	my ($s) = SYNDICATION->new($USERNAME, "#$PRT", 'CRM');
#	$GTOOLS::TAG{'<!-- EMAIL_STATUS -->'} = $s->statustxt();

	my $c = '';
	require PLUGIN::FUSEMAIL;
	my @USERS = &PLUGIN::FUSEMAIL::report($USERNAME);
#	my $selectedemail = $s->get('.email');
	$c .= "<option value=\"\">do not download email</option>";
	if (scalar(@USERS)==0) {
		$c .= "<option value=\"\" selected>Cannot configure: Need ZoovyMail Users</option>\n";
		}
	my $found = 0;
	foreach my $u (@USERS) {
		my $selected = '';
		if ($crm_ref->{'EMAIL_ADDRESS'} eq $u->{'email'}) {
			$selected = 'selected'; $found++;
			}
		$c .= "<option $selected value='$u->{'email'}'>$u->{'email'}</option>\n";
		}
	if ((not $found) && ($crm_ref->{'EMAIL_ADDRESS'} ne '')) {
		$c .= sprintf('<option selected value="%s">%s</option>',$crm_ref->{'EMAIL_ADDRESS'},"**INVALID: $crm_ref->{'EMAIL_ADDRESS'}");
		}
	$GTOOLS::TAG{'<!-- EMAILS -->'} = $c;

#	$c = '';
#	my $r = '';
#	foreach my $stageref (@CUSTOMER::TICKET::STAGES) {
#		$r = ($r eq 'r0')?'r1':'r0';
#		$c .= "<tr class='$r'><td><input type='checkbox'></td><td>$stageref->{'id'}</td><td>$stageref->{'name'}</td></tr>";
#		}
#	$GTOOLS::TAG{'<!-- CRM_STAGES -->'} = $c;

	}



if ($tabs) {
	#	require Net::POP3;
	#	require FUSEMAIL;
	#
	#	## GO GO GADGET IMAP
	#	my ($pop) = Net::POP3->new("pop3.fusemail.net", Timeout => 15);
	#
	#	my $username = "admin\@username.zoovy.com";
	#	my ($password) = &FUSEMAIL::getpassword($username);
	#
	#	if ($pop->login($username, $password) > 0) {
	#		my $msgnums = $pop->list; # hashref of msgnum => size
	#		foreach my $msgnum (keys %$msgnums) {
	#			my $msg = $pop->get($msgnum);
	#			print @$msg;
	#			# $pop->delete($msgnum);
	#			}
	#		}
	##	$pop->quit;
	#
	#	## STOP GADGET IMAP STOP!
	push @TABS, { name=>"Create", link=>"index.cgi?VERB=CREATE", selected=>($VERB eq 'CREATE')?1:0, };
	push @TABS, { name=>"New", link=>"index.cgi?VERB=TICKETS-NEW", selected=>($VERB eq 'TICKETS-NEW')?1:0, };
	push @TABS, { name=>"Open", link=>"index.cgi?VERB=TICKETS-OPEN", selected=>($VERB eq 'TICKETS-OPEN')?1:0, };
	push @TABS, { name=>"Waiting", link=>"index.cgi?VERB=TICKETS-WAITING", selected=>($VERB eq 'TICKETS-WAITING')?1:0, };
#		push @TABS, { name=>"Checkout Assist", link=>"index.cgi?VERB=CHECKOUTASSIST", selected=>($VERB eq 'CHECKOUTASSIST')?1:0, };
#		push @TABS, { name=>"Today", link=>"index.cgi?VERB=TICKETS-WAITING", selected=>($VERB eq 'TICKETS-WAITING')?1:0, };
#		push @TABS, { name=>"This Week", link=>"index.cgi?VERB=TICKETS-WAITING", selected=>($VERB eq 'TICKETS-WAITING')?1:0, };
#		push @TABS, { name=>"This Month", link=>"index.cgi?VERB=TICKETS-WAITING", selected=>($VERB eq 'TICKETS-WAITING')?1:0, };
	push @TABS, { name=>"Search", link=>"index.cgi?VERB=SEARCH", selected=>($VERB eq 'SEARCH')?1:0, };
	push @TABS, { name=>"Config", link=>"index.cgi?VERB=CONFIG", selected=>($VERB eq 'CONFIG')?1:0, };
	$VERB = '';
	}

##
## generic message/warn/error handler
##
if ((scalar @ERRORS)>0) {
	my $txt = '';
	foreach my $e (@ERRORS) {
		if ($e =~ /^WARN\:[\s]*(.*?)$/) { $txt .= qq~<div class="warning">WARNING: $1</div>~; }
		if ($e =~ /^ERR\:[\s]*(.*?)$/) { $txt .= qq~<div class="error">ERROR: $1</div>~; }
		if ($e =~ /^MSG\:[\s]*(.*?)$/) { $txt .= qq~<div class="captainibs">$1</div>~; }
		}
	$GTOOLS::TAG{'<!-- ERRORS -->'} = "<table width=600><tr><td>$txt</td></tr></table>";
	}


&GTOOLS::output(tabs=>\@TABS,bc=>\@BC,file=>$template_file,header=>1);

&DBINFO::db_zoovy_close();
&DBINFO::db_user_close();
