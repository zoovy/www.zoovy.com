#!/usr/bin/perl

use locale;  
use strict;
use POSIX qw(locale_h);
use Apache2::RequestRec (); # for $r->content_type
use Apache2::RequestIO ();  # for print
use Apache2::Const -compile => qw(:common :http);
use Storable;
use CGI;
use strict;
use utf8;

use lib "/httpd/modules";
use Data::Dumper;
use CGI;
use strict;
use locale;


sub wordlength {
	my ($check_this) = @_;

	print STDERR "CHECK: $check_this\n";

	if (not defined $check_this) { return 0; }
	$check_this =~ s/[^[:alpha:]]+//g; #strip all non-alphanumeric characters
	return length($check_this);
	}



use POSIX qw(locale_h);

my $old_locale = setlocale(LC_CTYPE);
#setlocale("LC_CTYPE","en_US.utf8");
setlocale("LC_CTYPE","sv_SE");

$old_locale = setlocale(LC_CTYPE);

my $cgi = new CGI;
my $x = $cgi->param('x');

#utf8::upgrade($x);

print qq~Content-type: text/html


<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head>
<body>
$old_locale
<form action="utf8.cgi">
<input type="textbox" value="$x" name="x">
<input type="submit">
</form>

~.
$cgi->param('x').qq~<br>~.
&wordlength($x)."<pre>".Dumper($cgi,\%ENV)."</pre>".qq~

</body>
~;

print STDERR Dumper($cgi);

