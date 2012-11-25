#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;
use ZOOVY;

require LUSER;
my ($LU) = LUSER->authenticate(flags=>',BASIC,');
if (not defined $LU) { exit; }

my ($MID,$USERNAME,$LUSERNAME,$FLAGS,$PRT) = $LU->authinfo();
if ($MID<=0) { exit; }

my %NEED = ();
if ($LU->get('todo.setup.download')) {
	require TODO;
   my $t = TODO->new($USERNAME);
  	my ($need,$tasks) = $t->setup_tasks('download',LU=>$LU);
   $GTOOLS::TAG{'<!-- MYTODO -->'} = $t->mytodo_box('download',$tasks);
   }

##
## EDIT THESE VALUES ON A RELEASE
##
$GTOOLS::TAG{'<!-- USERNAME -->'} = $USERNAME;
$GTOOLS::TAG{'<!-- VERSION_MAJOR -->'} = 	q~11~;
$GTOOLS::TAG{'<!-- VERSION_MINOR -->'} = 	q~054~;
$GTOOLS::TAG{'<!-- RELEASE_DATE -->'} = 	q~06/13/12~;
$GTOOLS::TAG{'<!-- ZID_FILE -->'} =			q~ZIDsetup-v11054.msi~;
$GTOOLS::TAG{'<!-- ZNSM_FILE -->'} =		q~ZNSMsetup-v11054.msi~;


$GTOOLS::TAG{'<!-- VERSION -->'} = $GTOOLS::TAG{'<!-- VERSION_MAJOR -->'}.'.'.$GTOOLS::TAG{'<!-- VERSION_MINOR -->'};

my $template_file = 'index.shtml';
&GTOOLS::output(
	title=>"Desktop Software Download Area",
	file=>$template_file,
	todo=>1,
	header=>1,
	help=>"#50407",
	bc=>[
		{ name=>'Downloads', }
		],
	);
