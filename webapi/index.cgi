#!/usr/bin/perl

use lib "/httpd/modules";
use GTOOLS;


$/ = undef; my $html = <DATA>; $/ = "\n";
&GTOOLS::output(header=>1,html=>$html);


__DATA__

<h1>Zoovy WebAPI</h1>
<br>

<b>List of Calls:</b><br>
A list of all the API calls we offer can be found here: <a href="http://webdoc.zoovy.com/doc/51620">http://webdoc.zoovy.com/doc/51620</a><br>
<br>

<b>Order Format:</b><br>
A lot of people just want to know what our order format looks like, we think it's pretty straightforward/self documenting - if you'd like to see for yourself please visit: 
<a href="http://webdoc.zoovy.com/doc/50213">http://webdoc.zoovy.com/doc/50213</a>. <br>
<br>

<b>Usage Policy:</b><br>
Customers can use their own password to access the API and as long as you don't make an unreasonable number of calls we're not going to notice or care.
If you start breaking things or asking for support it will be considered billable.<br>
<br>
However we ask any ISV building software for more than one client that you ask us for an API token and we'll 
come up with a way for users to generate custom tokens using an authentication protocol, or something creative.  
Let us know what you're up to and we'll figure it out.   Just send us an email at info@zoovy.com with your concept/plans and we'll get it to the right people.
<br>
<br>

<b>Support Policy:</b><br>
Customers who are building their own apps should inform us and we'll make a note to notify you when/if we're going to make changes that might impact you.  This is a service
we will provide only to Level 7 accounts (Zoovy One/Complete - aka NON-Basic accounts) and it is not necessarily free, but it depends on the scope of what you need.
Basic accounts, if we make changes your app will break, if that's a problem - upgrade to a better type of account because while we don't restrict API usage, we also don't support it for your type of account..<br>
<br>
For ISV's, first off you should know we have our own windows based desktop client written in .NET that uses most of this API calls and synchronizes this data
down to a MySQL or Microsoft SQL server for local reports, integrations, etc.  It's used by all of our largest clients and so we know this API works, and when/if
it breaks we take care of it pretty quickly so you probably won't be the one who tells us.  But we do offer a premium (bat-line) support to our BPP approved applications
learn more: <a href="http://webdoc.zoovy.com/doc/50849">http://webdoc.zoovy.com/doc/50849</a>.  
But we'll chat about support before we come up with a way to generate API tokens for your application.

<br>
<br>








