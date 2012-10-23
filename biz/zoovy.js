//
// zoovy.js file
//		<script type="text/javascript" src="http://www.zoovy.com/biz/zoovy.js"></script>
//

//
// opens a popup window
//
function openWindow(url) {
	myWinHandle	= window.open(url, 'popupWindow','resizable=yes,toolbar=yes,status=yes,width=638,height=400,menubar=yes,scrollbars=yes');
   if (myWinHandle.opener == null) { myWinHandle.opener = self; }
   myWinHandle.focus(true);
	return(myWinHandle);
	}

//
// validates that the string has nothing more than the allowed characters
//
function validate(string,Chars,min,max) {
     if (!string) return false;

     for (var i = 0; i < string.length; i++) {
        if (Chars.indexOf(string.charAt(i)) == -1)
           return false;
     }

     return true;
}

//
// returns a filtered string.
//
function validated(valid,string) {
     for (var i=0, output=''; i<string.length; i++)
        if (valid.indexOf(string.charAt(i)) != -1)
           output += string.charAt(i)
     return output;
 }


//
// <textarea name="limitedtextarea" onKeyDown="limitText(this.form.limitedtextarea,this.form.countdown,100);" 
// onKeyUp="limitText(this.form.limitedtextarea,this.form.countdown,100);">
// </textarea><br>
// <font size="1">(Maximum characters: 100)<br>
// You have <input readonly type="text" name="countdown" size="3" value="100"> characters left.</font>
//
function limitText(limitField, limitCount, limitNum) {
	if (limitField.value.length > limitNum) {
		limitField.value = limitField.value.substring(0, limitNum);
	} else {
		limitCount.value = limitNum - limitField.value.length;
	}
}



function ClipboardCopy(inElement) {
  if (inElement.createTextRange) {
    var range = inElement.createTextRange();
    if (range && BodyLoaded==1)
      range.execCommand('Copy');
  } else {
    var flashcopier = 'flashcopier';
    if(!document.getElementById(flashcopier)) {
      var divholder = document.createElement('div');
      divholder.id = flashcopier;
      document.body.appendChild(divholder);
    }
    document.getElementById(flashcopier).innerHTML = '';
    var divinfo = '<embed src="//www.zoovy.com/biz/ajax/_clipboard.swf" FlashVars="clipboard='+encodeURIComponent(inElement.value)+'" width="0" height="0" type="application/x-shockwave-flash"></embed>';
    document.getElementById(flashcopier).innerHTML = divinfo;
  }
}

