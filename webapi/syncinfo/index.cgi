#!/usr/bin/perl

use CGI;


if (1) {
	my $q = new CGI;

	use lib "/httpd/modules";
	require ADVERT;

	my $USERNAME = $q->param('USERNAME');

	my @URLS = ADVERT::retrieve_urls($USERNAME,15);
	my $jsarray = '';	foreach my $url (@URLS) { $jsarray .= "'$url',"; } chop($jsarray);

	print "Content-type: text/html\n\n";
	print qq~
<body width="320" height="240" scroll="no" bgcolor="FFFFFF" marginwidth="0" marginheight="0" topmargin="0" leftmargin="0" onLoad="progress();">
<center>
<iframe SRC="$URLS[0]" id="iFrameAd" NAME="iFrameAd" WIDTH=320 HEIGHT=240 ALIGN="MIDDLE" FRAMEBORDER=0 MARGINWIDTH=0 MARGINHEIGHT=0 SCROLLING="no"></iframe>
</center><SCRIPT>
<!--
var counter = 0;
var lastTime = 0;
function progress() {
	// called by the flash progress bar
	// never flips an add until 15 seconds or more have elapsed

	var d = new Date();
	var timeIs = d.getTime()/1000;

	if (lastTime + 5 < timeIs) {				
		lastTime = timeIs;	

		var URLS = new Array($jsarray);
		frames['iFrameAd'].location.href = URLS[counter];

		counter = counter + 1;
		if (counter>=URLS.length) { counter = 0; }
		}
	setTimeout('progress()',5000);
	}


if (window.resizeTo) { top.resizeTo(326,246); }
//-->
</SCRIPT></body>
~;

	}

