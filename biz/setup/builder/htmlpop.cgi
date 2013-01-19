#!/usr/bin/perl

use lib "/httpd/modules";
use ZOOVY;
use CGI;

my $q = new CGI;
my $ID = $q->param('id');

print "Content-type: text/html\n\n";
print qq~
<html>
<head>
<title>Zoovy HTML Editor</title>

<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

<!-- Configure the path to the editor.  We make it relative now, so that the
    example ZIP file will work anywhere, but please NOTE THAT it's better to
    have it an absolute path, such as '/htmlarea/'. -->
<script type="text/javascript">
  _editor_url = "/biz/setup/builder/htmlarea/";
  _editor_lang = "en";
</script>

<!-- load the main HTMLArea file, this will take care of loading the CSS and
    other required core scripts. -->
<script type="text/javascript" src="/biz/setup/builder/htmlarea/htmlarea.js"></script>

<!-- load the plugins -->
<script type="text/javascript">
      // WARNING: using this interface to load plugin
      // will _NOT_ work if plugins do not have the language
      // loaded by HTMLArea.

      // In other words, this function generates SCRIPT tags
      // that load the plugin and the language file, based on the
      // global variable HTMLArea.I18N.lang (defined in the lang file,
      // in our case "lang/en.js" loaded above).

      // If this lang file is not found the plugin will fail to
      // load correctly and NOTHING WILL WORK.

      HTMLArea.loadPlugin("TableOperations");
      HTMLArea.loadPlugin("SpellChecker");
      HTMLArea.loadPlugin("FullPage");
      HTMLArea.loadPlugin("CSS");
      HTMLArea.loadPlugin("ContextMenu");
      //HTMLArea.loadPlugin("HtmlTidy");
      HTMLArea.loadPlugin("ListType");
      HTMLArea.loadPlugin("CharacterMap");
		HTMLArea.loadPlugin("DynamicCSS");
</script>

<style type="text/css">
html, body {
  font-family: Verdana,sans-serif;
  background-color: #FFFFFF;
  color: #000000;
}
a:link, a:visited { color: #00f; }
a:hover { color: #048; }
a:active { color: #f00; }

textarea { background-color: #fff00f; border: 1px solid; }
</style>

<script type="text/javascript">
var editor = null;

function initEditor() {

  // create an editor for the "ta" textbox
  editor = new HTMLArea("ta");

  // register the FullPage plugin
  editor.registerPlugin(FullPage);

  // register the Table plugin
  editor.registerPlugin(TableOperations);

  // register the SpellChecker plugin
  editor.registerPlugin(SpellChecker);

  // register the HtmlTidy plugin
  //editor.registerPlugin(HtmlTidy);

  // register the ListType plugin
  // editor.registerPlugin(ListType);

//  editor.registerPlugin(CharacterMap);
// editor.registerPlugin(DynamicCSS);

  // register the CSS plugin
  editor.registerPlugin(CSS, {
    combos : [
      { label: "Syntax:",
                   // menu text       // CSS class
        options: { "None"           : "",
                   "Code" : "code",
                   "String" : "string",
                   "Comment" : "comment",
                   "Variable name" : "variable-name",
                   "Type" : "type",
                   "Reference" : "reference",
                   "Preprocessor" : "preprocessor",
                   "Keyword" : "keyword",
                   "Function name" : "function-name",
                   "Html tag" : "html-tag",
                   "Html italic" : "html-helper-italic",
                   "Warning" : "warning",
                   "Html bold" : "html-helper-bold"
                 },
        context: "pre"
      },
      { label: "Info:",
        options: { "None"           : "",
                   "Quote"          : "quote",
                   "Highlight"      : "highlight",
                   "Deprecated"     : "deprecated"
                 }
      }
    ]
  });

  // add a contextual menu
  editor.registerPlugin("ContextMenu");

  // load the stylesheet used by our CSS plugin configuration
  editor.config.pageStyle = "@import url(custom.css);";

  editor.generate();
  return false;
}

HTMLArea.onload = initEditor;

function insertHTML() {
  var html = prompt("Enter some HTML code here");
  if (html) {
    editor.insertHTML(html);
  }
}
function highlight() {
  editor.surroundHTML('<span style="background-color: yellow">', '</span>');
}
</script>

</head>

<!-- use <body onload="HTMLArea.replaceAll()" if you don't care about
     customizing the editor.  It's the easiest way! :) -->
<body onload="HTMLArea.init();">
<form action="#" name="edit" id="edit" method="POST">

<textarea id="ta" name="ta" style="width:100%" rows="20" cols="80">
</textarea>

<p />

<center><table width=90%>
<tr>
	<td>
		<input type="image" src="/images/bizbuttons/save.gif" onClick="mySubmit();" name="ok" value="  submit  " />
	</td>
	<td>
		<a href="javascript:window.close();"><img src="/images/bizbuttons/quit.gif" border="0"></a>
	</td>
	<td width=100% align='right'>
		<input type="button" name="ins" value="  insert html  " onclick="return insertHTML();" />
	</td>
</tr>
</table>
</center>

<!--
<input type="button" name="hil" value="  highlight text  " onclick="return highlight();" />
-->


<script type="text/javascript">
<!--


function mySubmit() {

	// document.edit.save.value = "yes";
	document.edit.onsubmit(); 	
	document.edit.submit();
	var v = document.forms['edit'].ta.value;

	window.opener.document.getElementById('$ID').value = v;
	window.close();
	return(1);
	};


var frm = window.opener.document.forms['thisFrm'];
if (!frm) { frm = window.opener.document.forms['thisFrm-$ID']; }
ta.value = frm.elements['$ID'].value;

//-->
</script>

</form>
</td></tr></table>
</center>

</body>
</html>
~;

