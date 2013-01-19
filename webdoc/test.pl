#!/usr/bin/perl

use Data::Dumper;

use lib "/httpd/modules";
use WEBDOC::OZMO;
use WEBDOC::SESSION;


my ($s) = WEBDOC::SESSION->new(USERNAME=>'brian',ID=>37);
$s->addDoc(51010);
$s->save();
print Dumper($s);

die();

my (@r) = WEBDOC::OZMO::ask_question("where can i learn more about promotions");
use Data::Dumper;
print Dumper(\@r);

#use Text::Diff;

#$a = qq~asdf\n\nasdfasdf;kjakjasdf\n\nasdf~;
#$b = qq~asdf\n\nasdfasdfk2j35;2lk3j5;lk2j35;4\n~;

#print diff \$a, \$b;
