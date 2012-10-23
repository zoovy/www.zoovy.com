/**********************************************************************************************
                 DHTML rewrite DIV script written by Mark Wilton-Jones - 2001
***********************************************************************************************

Please see http://www.howtocreate.co.uk/jslibs/ for details and a demo of this script
Please see http://www.howtocreate.co.uk/jslibs/termsOfUse.html for terms of use

This script even permits dynamic writing of div elements when the user is using Opera, which
under normal conditions does not allow you to do that. The way this is achieved is by using an
iframe in each div and with Opera, the iframe contents are re-written. The size of the iframe
cannot change. If it is not possible to rewrite the contents using the separate contents syntax,
the alternative (innerHTML) contents syntax or iframes, the new contents are stripped of their
HTML and displayed in the status bar. Script and CSS will also be removed if surrounded by
HTML comments as they should be. In Opera, iframes cannot be moved so the rewritable elements
cannot move on the page.

To use:
_________________________________________________________________________

Inbetween the <head> tags, put:

	<script src="/biz/ajax/rewritediv.js" type="text/javascript" language="javascript1.2"></script>
_________________________________________________________________________

Now create the bits that you want to be able to rewrite:

	<div id="ID OF DIV" style="position:absolute;left:10px;top:15px;">
		<iframe src="NAME OF PAGE.html" name="NAME OF IFRAME" marginwidth="0" marginheight="0" frameborder="0" height="HEIGHT OF AREA" width="WIDTH OF AREA" scrolling="no"></iframe>
	</div>

You can change the numbers after the 'left:' and 'top:' bits to initially position it on the page

Each iframe used in this way will have to have a page giving its initial contents (not used
if iframes are not supported, eg. in Netscape 4). It is ESSENTIAL that you specify the src
attribute of the iframe even if the page it refers to does not exist:

	<html><head><title>Dynamic content</title></head>
	<body bgcolor="BACKGROUND COLOUR">INITIAL CONTENT (USUALLY &nbsp;)</body></html>
_________________________________________________________________________

To rewrite a div, put:

	reWriteDiv('ID OF DIV','NAME OF IFRAME','TEXT TO WRITE','COLOUR TO SET THE BACKGROUND TO');
or
	reWriteDiv('ID OF DIV','NAME OF IFRAME','TEXT TO WRITE','COLOUR TO SET THE BACKGROUND TO', WIDTH OF (iframe) AREA, HEIGHT OF (iframe) AREA, DES BORDER);

You cannot rewrite the contents of an iframe until AFTER the initial iframe content has
loaded so if you try, this script will keep trying until the iframe loads.

If the width, height and border are all specified, the TEXT TO WRITE will become

	<table border="DES BORDER" cellpadding="0" cellspacing="0">
		<tr><td height="HEIGHT OF AREA" width="WIDTH OF AREA" valign="top">
			TEXT TO WRITE
		</td></tr>
	</table>

WIDTH OF AREA, HEIGHT OF AREA and DES BORDER should all be specified as integers (pixels)

Note: The dynamic bits WILL NOT inherit the sylesheets that your main document may have
_________________________________________________________________________*/

var winStatTim, rotString, iframeHasNotLd = new Array();
function getRefToDivNest( divID, oDoc ) {
	if( !oDoc ) { oDoc = document; }
	if( document.layers ) {
		if( oDoc.layers[divID] ) { return oDoc.layers[divID]; } else {
			for( var x = 0, y; !y && x < oDoc.layers.length; x++ ) {
				y = getRefToDivNest(divID,oDoc.layers[x].document); }
			return y; } }
	if( document.getElementById ) { return document.getElementById(divID); }
	if( document.all ) { return document.all[divID]; }
	return document[divID];
}
function reWriteDiv(oDiv,oFrame,oString,oBGCol,oWidth,oHeight,oBorder,oRepeat) {
	if(oRepeat) { oString = unescape(oString); }
	if( !oRepeat && typeof(oWidth) != 'undefined' && typeof(oHeight) != 'undefined'  && typeof(oBorder) != 'undefined' ) {
		oString = '<table border="'+oBorder+'" cellpadding="0" cellspacing="0"><tr><td height="'+
			oHeight+'" width="'+oWidth+'" valign="top">'+oString+'</td></tr></table>'; }
	var oContent = getRefToDivNest(oDiv); //create fake objects if needed
	if( !oContent ) { oContent = new Object(); } if( !window.frames ) { window.frames = new Object(); }
	if( typeof(oContent.innerHTML) != 'undefined' ) { oContent.innerHTML = oString; //DOM
		if( oContent.style ) { oContent.style.backgroundColor = oBGCol; } return; } //& Proprietary DOM
	if( oContent.document == document || !oContent.document ) { if( !window.frames.length ) { window.clearTimeout(winStatTim);
		rotString = '   -------  '+oString.replace(/<!--([^>]|[^-]>|[^-]->)*-->/g,' ').replace(/<[\/!]?[a-z]+\d*(\s+[a-z][a-z\-]*(=[^\s>"']*|="[^"]*"|='[^']*')?)*\s*(\s\/)?>/gi,' ').replace(/[^\S ]+/g,' ').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&nbsp;/g,' ').replace(/&quot;/g,'"').replace(/&amp;/g,'\t').replace(/&#?\w+;/g,' ').replace(/\t/g,'&').replace(/ +/g,' ');
		startrot(rotString.length); return; } //use status bar. Clears HTML ( clears script & CSS if in comments )
		if(!oRepeat) { window.clearTimeout(iframeHasNotLd[oFrame]); } //if they rewrite more than once before the iframe loads, only show the last one
		if(!window.frames[oFrame]) { //the iframe is unavailable until its content has loaded
			iframeHasNotLd[oFrame] = window.setTimeout('reWriteDiv(\''+oDiv+'\',\''+oFrame+'\',\''+escape(oString)+'\',\''+oBGCol+'\','+oWidth+','+oHeight+','+oBorder+',true)',100); return; }
		oContent = window.frames[oFrame].window; } //use iframe
	oContent.document.open(); //Separate contents syntax
	oContent.document.write('<html><head><title>Dynamic content</title></head><body bgcolor="'+oBGCol+'">'+oString+'</body></html>');
	oContent.document.close();
}
function startrot(rotNum) {
	if( !rotString.replace(/\s/g,'').replace(/-------/,'') ) { rotString = ''; }
	window.status = rotString.substr(rotNum) + rotString.substr(0,rotNum);
	if( rotNum == rotString.length ) { rotNum = -1; }
	if(rotString) { winStatTim = window.setTimeout('startrot('+(rotNum+1)+')',60); }
}

