//
// functions for adding/removing/selecting categories - 20090919
//


//
function ZProductFinder(htmlid,jsguidid,src) {
	this.htmlid = htmlid;			// prefix on all html elements.
	this.jsguidid = jsguidid;		// global unique js-safe object id 
	this.src = src;					// source of the product data.
	this.events = '';					// events, woot.
	this.btn = '';						// which button is currently in focus.
	this.sortable = 0;				// is the current display sortable?
	this.prodarr = null;				// an array of products on the current panel.
	this.changes = '';				// a list of changes, hard return separated.

	this.GetResults = function(btn,txt) {
		this.changes = '';
		// alert('id: '+this.htmlid+' btn: '+btn);
		this.btn = btn;

		if ((btn != 'fromlist') && (btn != 'fromcat')) {
			// note: fromlist and fromcategory don't change the button state.
			$(this.htmlid+'!button:current').className = 'button';
			$(this.htmlid+'!button:recent').className = 'button';
			$(this.htmlid+'!button:all').className = 'button';
			$(this.htmlid+'!button:showlist').className = 'button';
			$(this.htmlid+'!button:showcat').className = 'button';
			$(this.htmlid+'!button:showmore').className = 'button';
			$(this.htmlid+'!button:search').className = 'button';
			$(this.htmlid+'!button:csv').className = 'button';
	
			if ($(this.htmlid+'!button:'+btn)) {
				$(this.htmlid+'!button:'+btn).className = 'button2';
				}
			}

		var div = $(this.htmlid+'!results');
		div.innerHTML = '<table height=200 width=250"><tr><td align="center" valign="middle"><img border=0 src="/biz/loading.gif"></td></tr></table>';

		if (btn == 'showlist') {
			var postBody = 'm=PRODFINDER/ShowList&id='+this.htmlid+'&btn='+btn+'&txt='+encodeURIComponent(txt)+'&jsguidid='+this.jsguidid;
			new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowList', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
			}
		else if (btn == 'showcat') {
			var postBody = 'm=PRODFINDER/ShowCat&id='+this.htmlid+'&btn='+btn+'&txt='+encodeURIComponent(txt)+'&jsguidid='+this.jsguidid;
			new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowCat', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
			}
		else if (btn == 'showmore') {
			var postBody = 'm=PRODFINDER/ShowMore&id='+this.htmlid+'&btn='+btn+'&jsguidid='+this.jsguidid;
			new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowMore', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;				
			}
		else {
			// alert('id: '+this.htmlid+' button:'+btn+' txt:'+txt);
			var postBody = 'm=PRODFINDER/Load&id='+this.htmlid+'&btn='+btn+'&txt='+encodeURIComponent(txt)+'&jsguidid='+this.jsguidid;
			new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Load', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;	
			}
		}


	this.SaveProducts = function() {
		var listid = this.jsguidid+'_list';
		// alert(listid);
				
		if (this.sortable) {
			var out = '';
			var poststring = Sortable.serialize(listid,{tag:'p'});
			var arr = poststring.split(/[&]/); // poststring.parseQuery('&');
			for (var i = 0; i < arr.length; i++){ 
				var kv = arr[i].split(/[=]/);
				if (kv[0] == listid+"[]") {
					var pid = kv[1];
					
					// alert(listid+'!chk!'+pid);
					var el = $(listid+'!chk!'+pid);
					if (el && $(listid+'!chk!'+pid).checked) {
						// this product is checked.
						out = out + ((out.length>0)?',':'') + pid;
						}
					}
				this.changes = "sort/"+out+"\n";
				}
			}

		// note: this MUST come after the sortable.
		var div = $(this.htmlid+'!results');
		div.innerHTML = '<table height=200 width=250"><tr><td align="center" valign="middle"><img border=0 src="/biz/loading.gif"></td></tr></table>';

		this.btn = 'current';

		var postBody = 'm=PRODFINDER/UPDATE&id='+this.htmlid+'&src='+this.src+'&cmds='+encodeURIComponent(this.changes)+'&btn='+this.btn+'&jsguidid='+this.jsguidid;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Update', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;	

		// alert('SENDING: '+this.changes);
		}

	this.CheckAll = function() {
		// alert('checkall');
		var listid = this.jsguidid+'_list';
		for (i=0;i<this.prodarr.length;i++) {
			// alert(this.prodarr[i]);
			$(listid+'!chk!'+this.prodarr[i]).checked = true;
			this.RecordChange('add',this.prodarr[i]);
			}
		}

	this.DurkaDurka = function(jspids) {
		// alert("DurkaDurka ");
		}

	this.RecordChange = function(action,pid) {
		this.changes = this.changes + action+'/'+pid+"\n";
		// alert("changes: "+this.changes);
		}


	this.DisplayProducts = function(rows,header,sortable) {
		// alert(rows);
		// out = rows;
		// alert("Muhammad Jihad!");
		var listid = this.jsguidid+'_list';
		out = '';
		if (!header) { header = "Unknown"; }
		out = '<h2>'+header+'</h2>';
		this.prodarr = new Array;
		this.sortable = 0;

		if (sortable) {
			this.sortable = 1;
			out = out + "<div class='hint'>HINT: You can sort the items in this category by dragging and dropping the product images.</div><br>";
			}
		out = out + '<div id="'+listid+'">';
		for(i=0;i<rows.length;i++) {
			// alert(i);
			var row = rows[i];
			var xclass = (i%2==1)?'r0':'r1';
			var checked = '';
			if (row[3]) { xclass = 'rs'; checked = 'checked'; }	// column already selected.
			out = out + '<p id="item_'+row[4]+'" class="'+xclass+'" style="margin: 0pt; position: relative;">';
			out = out + '<input onClick="'+this.jsguidid+'.RecordChange(this.checked?\'add\':\'kill\',\''+row[4]+'\'); $(\'item_'+row[4]+'\').className=(this.checked)?\'rs\':\'r0\';" '+checked+' type="checkbox" name="'+listid+'!chk!'+row[4]+'" id="'+listid+'!chk!'+row[4]+'"> <a href="#" onclick="return false">'+row[0]+'</a> '+row[1]+' '+row[2]+' '+row[4]+'</p>';
			this.prodarr.push(row[4]);
			}
		out = out + '</div>';

		if (this.prodarr.length>0) {
			out = out + '<input type="button" class="button" value=" Save " onClick="'+this.jsguidid+'.SaveProducts();">';
			if (!sortable) {
				out = out + '<input type="button" class="button" value=" Add All " onClick="'+this.jsguidid+'.CheckAll();"> ';
				}
			}
		else {
			out = out + "<br>No Products Found";
			}

		// alert("Bakala");
		$(this.htmlid+"!results").innerHTML = out;
		// alert("Jihad Bakala");

		if (this.sortable) {
			alert("yer-sortable: "+listid);
	    	Sortable.create(listid, {elements:$$('#'+listid+' p'), handles:$$('#'+listid+' a')});
			}
		else {
			alert("nay-sortable: "+listid);
			}

		// alert("Shhhh");
		return(1);
		}


	this.Build = function() {	
		var out = "";
		out = out + "<center>";
		out = out + "<table width='95%' cellspacing=0 class=\"zoovytable\">";
		out = out + "<tr bgcolor='#666666'>";
		out = out + "	<td colspan=2><b><font color='white'>Product Finder ("+this.src+")</font></b></td>";
		// $closelink = qq~<a href="javascript:ProductFinder('$src','$div');"><font style='font-size: 6pt; color: #FFFFFF'>[Close]</font></a>~; 
		out = out + "	<td align='right' valign='middle'></td>";
		out = out + "</tr>";
		out = out + "<tr>";
		out = out + "<td valign='top' width=100>";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('current','Currently Selected Products');\" id=\""+this.htmlid+"!button:current\" style='width: 100px;' type=\"button\" class=\"button\" value=\"Current\">";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('recent','Recently Modified Products');\" id=\""+this.htmlid+"!button:recent\" style='width: 100px;' type=\"button\" class=\"button\" value=\"Recent\">";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('all','All Products');\"  id=\""+this.htmlid+"!button:all\" style='width: 100px;' type=\"button\" class=\"button\" value=\"Show All\">	";

		out = out + "		<img src=\"/images/blank.gif\" width=\"100%\" height=\"12\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('showlist','Select From List');\" id=\""+this.htmlid+"!button:showlist\" style='width: 100px;' type=\"button\" class=\"button\" value=\"From List\">";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('showcat','Select From Category');\" id=\""+this.htmlid+"!button:showcat\" style='width: 100px;' type=\"button\" class=\"button\" value=\"From Category\">		";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('showmore','More Choices');\" id=\""+this.htmlid+"!button:showmore\" style='width: 100px;' type=\"button\" class=\"button\" value=\"More Choices\">		";
		
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"10\">";
		out = out + "	<font style='font-size: 7pt;'>Text:</font><br>";
		out = out + "	<input type=\"textbox\" style=\"width: 95px;\" id=\""+this.htmlid+"!searchtxt\" name=\""+this.htmlid+"!searchtxt\">";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('search',\$('"+this.htmlid+"!searchtxt').value);\" id=\""+this.htmlid+"!button:search\" style='width: 100px;' type=\"button\" class=\"button\" value=\"Search\">	";
		out = out + "	<img src=\"/images/blank.gif\" width=\"100%\" height=\"3\">";
		out = out + "	<input onClick=\""+this.jsguidid+".GetResults('csv',\$('"+this.htmlid+"!searchtxt').value);\" id=\""+this.htmlid+"!button:csv\" style='width: 100px;' type=\"button\" class=\"button\" value=\"Load CSV\">	";
		out = out + "</td>";
		out = out + "<td valign='top' width=\"99%\">";
		out = out + "<div style=\"font-size: 7pt;\" id=\""+this.htmlid+"!results\">";
		out = out + "<table>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">Current:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Currently Selected Products (Use this to remove products)</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">Recent:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Recently Created/Edited Products</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">All:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">All Products</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">From List:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Lets you load products from a preconfigured list.</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">From Category:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Loads products from another category.</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">Search:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Enter keywords to find matching products.</td></tr>";
		out = out + "	<tr><td style=\"font-size: 7pt;\" valign='top' class=\"bold\">CSV:</td>";
		out = out + "	<td style=\"font-size: 7pt;\">Enter a comma separated list of product id's into the textbox.</td></tr>";
		out = out + "</table>";
		out = out + "<i>Note: To optimize download speeds no more than 250 results will be displayed.</i>";
		out = out + "</div>";
		out = out + "</td>";
		out = out + "</tr>";
		out = out + "</table>";
		out = out + "</center>";
		out = out + "<br>";
		out = out + "<!-- end productFinder -->";

		
		$(this.htmlid).innerHTML = out;
		}
	
	}



// ---------- LINE OF DEPRECATION ------------




function showNavcatProducts(safe) { 
	// alert(safe);

	if ($('show_products_navcat:'+safe)) {
		// products are already displayed, so go hide them.
		$('~'+safe).innerHTML = '';		
		}
	else {
		//
		var postBody = 'm=NAVCAT/ShowProducts&safe='+safe;
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/ShowProducts', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
		}
	}



//
//
//
function NAVCAThandleResponse(txt) {

	if (txt == '') {
		// empty response, must have been a set only
		}
	else if (txt.indexOf('?') == 0) {
		// NOTE: multiple ? can be returned.
		// ?k1=v1 (NOT XML)
		var txtLines = new Array();
		txtLines = txt.split('?');		// split the txt into lines (separated by ?)
		for (var i = 0;i<txtLines.length;i++) {
			var params = kvTxtToArray('?' + txtLines[i]);
			// alert('i['+i+']='+txtLines[i]);
			// alert(i+' '+params['m']);

			if (txtLines[i] == '') {}	// blank line (probably the first record)
			else if (params['m'] == 'setGraphic') {
				// alert('setGraphic: '+params['id']);
				var img = $(params['id']);
				img.src = params['src'];
				}
			else if (params['m'] == 'loadcontent') {
				var safe = params['div'];
				// alert('reloading div: ' + safe);
				thisDiv = $(safe);
				
				// params['html'] = '<img id="img_TS67" src="/images/zoovy_main.gif">';
				
				thisDiv.innerHTML = params['html'];
				
				// thisDiv.innerHTML = params['html'];
				// alert('html:'+params['html']);
				}
			else if (params['m'] == 'eval') {
				// runs javascript
				try { 
					eval(params['js']); 
					} 
				catch (e) { 
					alert('eval failed: '+params['js']); 
					}
				}
			else if (params['m'] == 'dragdrop') {
				// alert('adding DragDrop for: '+params['id']);
				// new Draggable( 'img_TS67', { revert: true });
				var id = params['id'];
				var obj = $(id);
				// alert('id: ['+id+'] '+obj.src);
				new Draggable( id, { revert: true });
				// alert(obj);
				}
			else {
				// unknown request handler!
				alert('unknown request!');
				}
			// end of each line.
			}
		}		
	else {
		alert('unknown data format sent to NAVCAThandleResponse: '+txt);
		}
	}


function addProducts(safe) {
	var postBody = 'm=NAVCAT/Products&safe='+safe;
	new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Products', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;
	}


//
function addNew(safe,mode) {
	// alert("adding new to "+safe);
	if (mode==undefined) { mode = 0; }
	
	if (mode==0) {
		var thisDiv = $('~'+safe);		
		var c = '<table border=0 cellspacing=0 class="zoovytable"><tr><td class="zoovytableheader"> &nbsp; Add New Category </td></tr><tr><td class="cell">';		
		c = c + 'Category Name: <input id="NEW~'+safe+'~pretty" type="textbox" name="NEW~'+safe+'~pretty">';
		c = c + '<input type="hidden" name="NEW~'+safe+'~type" id="NEW~'+safe+'~type" value="navcat">';
		
		if (safe == '.') {
			c = c + '<br>';
			c = c + '<input type="radio" checked onClick="$(\'NEW~'+safe+'~type\').value = \'navcat\';" name="NEW~'+safe+'~type" value="navcat"> Root Level Category<br>';
			c = c + '<input type="radio" onClick="$(\'NEW~'+safe+'~type\').value = \'list\';" name="NEW~'+safe+'~type" value="list"> Product List <i>(Does not appear in navigation)</i><br>';
			}
		else {
			}
		
		c = c + '<input onClick="addNew(\''+safe+'\',1);" type="button" value="Save">';
		c = c + '<input onClick="addNew(\''+safe+'\',2);" type="button" value="Abort">';
		c = c + '</td></tr></table>';
		thisDiv.innerHTML = c;	
		$('NEW~'+safe+'~pretty').focus();
		}
	else if (mode==1) {
		var thisDiv = $('~'+safe);	
		var pretty = $F('NEW~'+safe+'~pretty');
		var modetype = $F('NEW~'+safe+'~type');
		// alert('NEW~'+safe+'~type!list');
		// if (modetype == undefined) {	
		//	alert(modetype);
		//	}

		var postBody = 'm=NAVCAT/Add&safe='+safe+'&pretty='+encodeURIComponent(pretty)+'&type='+modetype;
		if ($('_pid')) { postBody = postBody + '&_pid='+$F('_pid'); }
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Add', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;
		}
	else {
		var thisDiv = $('~'+safe);		
		thisDiv.innerHTML = '';
		}
	}


//
function renameCat(safe,mode) {
	// alert("adding new to "+safe);
	if (mode==undefined) { mode = 0; }
	
	if (mode==0) {
		var thisDiv = $('~'+safe);		
		var c = '<table border=0 cellspacing=0 class="zoovytable"><tr><td class="zoovytableheader"> &nbsp; Rename Category </td></tr><tr><td class="cell">';		
		c = c + 'New Pretty Name: <input type="textbox" id="RENAME~'+safe+'~pretty" name="RENAME~'+safe+'~pretty">';
		c = c + '<input onClick="renameCat(\''+safe+'\',1);" type="button" value="save">';
		c = c + '</td></tr></table>';
		thisDiv.innerHTML = c;	
		}
	else if (mode==1) {
		var pretty = $F('RENAME~'+safe+'~pretty');


		var postBody = 'm=NAVCAT/Rename&safe='+safe+'&pretty='+encodeURIComponent(pretty);
		if ($('_pid')) { postBody = postBody + '&_pid='+$F('_pid'); }
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Rename', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;
		}
	}


// toggleCat - opens and closes a cat based on it's setting in 
function toggleCat(safe) {
	// alert("expanding "+safe);	

	thisDiv = $(safe);		
	var icon = $('ICON_'+safe);
	// alert(icon.src);	
	// icons are: miniup.gif and minidown.gif

	if (icon.src.indexOf('miniup.gif')>=0) { 
		thisDiv.innerHTML = 'Expanding!';
		var postBody = 'm=NAVCAT/Expand&safe='+safe;
		if ($('_pid')) { postBody = postBody + '&_pid='+$F('_pid'); }
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Expand', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;
		}
	else {
		thisDiv.innerHTML = 'Collapsing!';
		var postBody = 'm=NAVCAT/Collapse&safe='+safe;
		if ($('_pid')) { postBody = postBody + '&_pid='+$F('_pid'); }
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Collapse', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;
		}
	}


//
function deleteCat(safe,z) {
	// alert('delete cat'+safe);
	if (z==0) {
		var c = '<table border=0 cellspacing=0 class="zoovytable"><tr><td class="zoovytableheader"> &nbsp; Remove Category </td></tr><tr><td class="cell">';		
		c = c + '<font color="red">Warning: you are about to delete category: '+safe+'</font><br>';
		c = c + '<input type="button" onClick="deleteCat(\''+safe+'\',1);" value="Confirm">';
		c = c + '<input type="button" onClick="deleteCat(\''+safe+'\',2);" value="Abort">';
		c = c + '</td></tr></table>';
		thisDiv = $(safe);	
		thisDiv.innerHTML = c;
		}
	else if (z==1) {
		// yep, really delete it.
		var postBody = 'm=NAVCAT/Delete&safe='+safe;
		if ($('_pid')) { postBody = postBody + '&_pid='+$F('_pid'); }
		new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Delete', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;	
		}
	else {
		// hmm.. they don't actually want to do this.
		toggleCat(safe);
		}
	}

function updateCat(cb) {
// alert(cb.name);
// alert(cb.checked);
   if (cb.name.substring(0,3) == "cb_") {
      $('_diffs').value = $('_diffs').value + "\n" + cb.name.substring(3) + "=" + ((cb.checked)?"1":"0");
      }
// alert($('_diffs').value);
   }


