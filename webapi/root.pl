#!/usr/bin/perl 

use Filesys::Virtual::Plain;

    my $handler = Filesys::Virtual::Plain->new({
        root_path => "/tmp",
        cwd       => "/",
        %args
    });

use Data::Dumper;
print Dumper($handler->list());