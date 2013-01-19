#!/usr/bin/perl

use lib "/httpd/modules";
use XML::Parser;
use XML::Parser::EasyTree;
use Data::Dumper;
use Storable;

opendir $D, "/httpd/htdocs/biz/reports/graphs";
while ( $file = readdir($D) ) {

	next if (substr($file,0,1) eq '.');
	next unless ($file =~ /\.xml$/);

	print "FILE: $file\n";
	my $parse = new XML::Parser(Style=>'EasyTree');
	my $tree = $parse->parsefile($file);
	$tree = $tree->[0];
	
	print Dumper($tree);
	my %GRAPH = ();
	$GRAPH{'TYPE'} = $tree->{'attrib'}->{'type'};
	foreach $node (@{$tree->{'content'}}) {
		next if ($node->{'type'} ne 'e');
		if ($node->{'name'} eq 'attribs') {
			$GRAPH{'@ATTRIBS'} = $node->{'attrib'};
			}
		elsif ($node->{'name'} eq 'dataset') {
			$node->{'attrib'}->{'type'} = 'dataset';
			$GRAPH{'DATASET'} = $node->{'attrib'};
			push @{$GRAPH{'SERIES'}}, $node->{'attrib'};
			}
		elsif ($node->{'name'} eq 'categories') {
			$node->{'attrib'}->{'type'} = 'categories';
			push @{$GRAPH{'SERIES'}}, $node->{'attrib'};
			}
		else {
			print Dumper($node);	
			die("Unknown node type!");
			}
		}

	## SAVE:
	$file =~ s/\.xml$/\.bin/s;
	print "FILENAME: $file\n";
	store \%GRAPH, $file;
	}
closedir ($D);