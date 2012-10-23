#!/usr/bin/perl

use lib "/httpd/modules";
use CGI;
require GTOOLS;
require ZOOVY;
require ZMAIL;
require TOXML::EMAIL;
require EXTERNAL;

my ($USERNAME,$FLAGS,$MID,$LUSER,$RESELLER) = ZOOVY::authenticate("/biz/setup",2,'_O&2');
if ($USERNAME eq '') { exit; }

$q = new CGI;
$CMD = $q->param("CMD");
	

if ($CMD eq 'CONTACT' || $CMD eq '') {
	$template_file = "contact.shtml";

	$ID = $q->param('ID');

	## changed 9/26 - patti
	
#	$hashref = &AUTOEMAIL::safefetch_message($USERNAME,'EREMIND',0);
		
#	$GT::TAG{"<!-- TITLE -->"} = &ZOOVY::incode(${ &AUTOEMAIL::interpolate(\$hashref->{'zoovy:title'},$ref) });
#	$GT::TAG{"<!-- BODY -->"} = &ZOOVY::incode(${ &AUTOEMAIL::interpolate(\$hashref->{'zoovy:body'},$ref) });	
#	$GT::TAG{"<!-- FROM -->"} = &ZOOVY::incode($hashref->{'zoovy:from'});
#	$GT::TAG{"<!-- RECIPIENT -->"} = &ZOOVY::incode($ref->{'%NAME%'});


	} 
elsif ($CMD eq 'SAVE') {
	#&ZMAIL::sendmail($USERNAME,$q->param('RECIPIENT'),$q->param('SUBJECT'),$q->param('BODY'));
	
	$template_file = 'contact-success.shtml';
	}

&GTOOLS::output(header=>1,file=>$template_file);
