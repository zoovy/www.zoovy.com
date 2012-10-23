#!/usr/bin/perl

use lib "/httpd/modules";
require PAGE;
my $USERNAME = 'panrack';
my $NS = 'HAYSPEAR';
my ($pageinfo) = &PAGE::page_info($USERNAME,$NS,['homepage','aboutus','cart','contactus','gallery','login','privacy','results','return','search','shipquote']);
foreach my $pg (@{$pageinfo}) {
   $GTOOLS::TAG{uc("<!-- $pg->{'safe'}_LASTEDIT -->")} = &ZTOOLKIT::pretty_time_since($pg->{'modified'});
   }
use Data::Dumper;
print Dumper($pageinfo);


exit;

my $src = "PAGE::var";

if ($src =~ m/^PAGE(\[[a-z0-9\.]+\])?\:\:([a-z0-9\.]+)$/o) {
	print "1:$1 2:$2\n";
	exit;
	}
print "skip\n";


exit;

$options{'url'} = 'http://some.url.com';
$options{'update'} = 'update_this_id_with_results';
$options{'indicator'} = 'hidden_span_which_says_searching';
$options{'min_chars'} = 1;
$options{'on_hide'} = 'on_hide';
$options{'on_show'} = 'on_show';

$prototype = HTML::Prototype->new();
# print $prototype->auto_complete_field( 'SSSEARCH', \%options );

print $prototype->auto_complete_stylesheet();
print $prototype->auto_complete_field( 'acomp', { url => '/autocomplete', indicator => 'acomp_stat' } );




__DATA__
q
q~
       prototype->auto_complete_field( field_id, options )
           Adds Ajax autocomplete functionality to the text input field with
           the DOM ID specified by $field_id.

           This function expects that the called action returns a HTML <ul>
           list, or nothing if no entries should be displayed for autocomple-
           tion.

           Required options are:

           "url": Specifies the URL to be used in the AJAX call.

           Addtional options are:

           "update": Specifies the DOM ID of the element whose  innerHTML
           should be updated with the autocomplete entries returned by the
           Ajax request.  Defaults to field_id + '_auto_complete'.

           "with": A Javascript expression specifying the parameters for the
           XMLHttpRequest.  This defaults to 'value', which in the evaluated
           context refers to the new field value.

           "indicator": Specifies the DOM ID of an elment which will be dis-
           played Here's an example using Catalyst::View::Mason with an indi-
           cator against the auto_complete_result example below on the server
           side.  Notice the 'style="display:none"' in the indicator <span>.

                   <% $c->prototype->define_javascript_functions %>

                   <form action="/bar" method="post" id="baz">
                   <fieldset>
                           <legend>Type search terms</legend>
                           <label for="acomp"><span class="field">Search:</span></label>
                           <input type="text" name="acomp" id="acomp"/>
                           <span style="display:none" id="acomp_stat">Searching...</span><br />
                   </fieldset>
                   </form>

                   <span id="acomp_auto_complete"></span><br/>

                   <% $c->prototype->auto_complete_field( 'acomp', { url => '/autocomplete', indicator => 'acomp_stat' } ) %>

           while autocomplete is running.

           "tokens": A  string or an array of strings containing separator
           tokens for tokenized incremental autocompletion. Example: "<tokens
           =" ','>> would allow multiple autocompletion entries, separated by
           commas.

           "min_chars": The minimum number of characters that should be in the
           input field before an Ajax call is made to the server.

           "on_hide": A Javascript expression that is called when the autocom-
           pletion div is hidden. The expression should take two variables:
           element and update.  Element is a DOM element for the field, update
           is a DOM element for the div from which the innerHTML is replaced.

           "on_show": Like on_hide, only now the expression is called then the
           div is shown.
~;
