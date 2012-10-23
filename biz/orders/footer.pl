#!/usr/bin/perl

use CGI;

my $q = new CGI;

my $CMD = uc($q->param('CMD'));

@POOLS = (
	{ pool=>'RECENT', prompt=>'Recent', },
	{ pool=>'PENDING', prompt=>'Pending', },
	{ pool=>'REVIEW', prompt=>'Review', },
	{ pool=>'HOLD', prompt=>'Hold', },
	{ pool=>'APPROVED', prompt=>'Approved', },
	{ pool=>'PROCESS', prompt=>'Process', },
	{ pool=>'COMPLETED', prompt=>'Completed', },
	{ pool=>'DELETED', prompt=>'Cancelled', },
	{ pool=>'BACKORDER', prompt=>'Backorder', },
	{ pool=>'PREORDER', prompt=>'PreOrder', },
	);

if ($CMD eq 'COMPLETED') {
	push @POOLS, { pool=>'ARCHIVE', prompt=>'Archive' };
	}

if ($CMD eq '') {
	}

print "Content-type: text/html\n\n";

print qq~
<html>
<head>
	<SCRIPT>
	<!--//
	function doCMD() {
		for (var x=0; x < document.forms[0].CMD.length; x++) {
			if (document.forms[0].CMD[x].checked) {
				parent.main.submitIt(document.forms[0].CMD[x].value);
				return false;
			}
		};
		alert("You must select one of choices to submit this request.");
		return false;
	}
	function clickCMD (value) { 
		document.thisFrm.CMD[value].checked=true; return(false); 
		}
	//-->
	</SCRIPT>
	<link rel="STYLESHEET" type="text/css" href="/biz/standard.css">  
	<STYLE>
	a { font-size: 8pt; font-family: Arial, Helvetica, sans-serif; color: #000000; text-decoration: none; }
	a:hover { color: #000000; }
	a:visited { color: #000000; }
	a:active { color: #000000; }
	</STYLE>
</head>
<body topmargin="0" leftmargin="0" marginwidth="0" marginheight="0">
<form target="body" id="thisFrm" name="thisFrm" action="#">
<table border=0 cellpadding=0 cellspacing=0 width=100% class='zoovysub1header'><tr><td>
<table border="0" cellpadding="0" cellspacing="2" align="center">
	<tr>
	~;

my $i = 0;
foreach my $ref (@POOLS) {
	next if ($ref->{'pool'} eq $CMD);

	next if ($ref->{'pool'} eq 'BACKORDER');
	next if ($ref->{'pool'} eq 'PREORDER');

	print qq~
<td nowrap>
<input type="radio" name="CMD" value="$ref->{'pool'}"><a href="#" onClick="return clickCMD($i)">$ref->{'prompt'}</a></td>
<td>&nbsp;</td>
~;
	$i++;
	}

print qq~
		<td rowspan="2" valign="middle">&nbsp;<input onClick="doCMD();" style="width: 40px; height: 20px; font-size: 8pt; font-face: arial;" class="button" type="button" value="  Go   "></td>
	</tr>
	<tr>
		<td><input type="radio" name="CMD" value="PAID"><a href="#" onClick="return clickCMD(~.($i++).qq~)">Flag as Paid</a></td>
		<td>&nbsp;</td>
		<td><input type="radio" name="CMD" value="EMAIL"><a href="#" onClick="return clickCMD(~.($i++).qq~)">Send Email</a></td>
		<td>&nbsp;</td>
<!--
		<td><input type="radio" name="CMD" value="EXPORT"><a href="#" onClick="return clickCMD(~.($i++).qq~)">Export</a></td>
		<td>&nbsp;</td>
-->
	</tr>
</table>

</td></tr></table>
</form>
</body>
</html>
~;
