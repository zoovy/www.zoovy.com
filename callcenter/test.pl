#!/usr/bin/perl

use lib "/httpd/modules";
use CALLCENTER;

print &CALLCENTER::wikiformat(qq~

''Say this''
blah blah blabh

''SAY:This is a alert''
Blah blah

'''This is a hint'''
Blah blah

~);
