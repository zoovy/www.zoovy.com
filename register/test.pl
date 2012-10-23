#!/usr/bin/perl

use strict;
use lib "/httpd/modules";
use ZTOOLKIT;
use LWP::Simple;

my $firstname = 'brian';
my $lastname = 'horakh';
my $email = 'brian@zoovy.com';
my $company = 'zoovy';
my $phone = '555-555-5555';
my $url = 'http://www.zoovy.com';
my $meta = 'leadsource';
my $operid = '';
my $leadid = 0;


  ## NOTIFY SALESFORCE:
  require LWP::Simple;
  require ZTOOLKIT;
  my %foo = ();
  $foo{'encoding'} = 'UTF-8';
  $foo{'oid'} = '00D80000000cL3u';
  $foo{'retURL'} = 'http://www.zoovy.com/thanks!';
  $foo{'first_name'} = $firstname;
  $foo{'last_name'} = $lastname;
  $foo{'email'} = $email;
  $foo{'company'} = $company;
  $foo{'phone'} = $phone;
  $foo{'URL'} = $url;
  $foo{'lead_source'} = 'site-zoovy.com';
  $foo{'00N80000003Pyp7'} = "$meta|$operid";
  ## Correlation Data:
  $foo{'00N80000003Pyp6'} = '';
  ## CorrelationID:
  $foo{'00N80000003Pyp5'} = "LEAD-$leadid";

  my $paramstr = &ZTOOLKIT::buildparams(\%foo);
  print LWP::Simple::get("https://www.salesforce.com/servlet/servlet.WebToLead?$paramstr");
