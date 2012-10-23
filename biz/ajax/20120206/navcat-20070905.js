//
// functions for adding/removing/selecting categories
//


function PFChanges() {
	this.events = '';
	}

PFChanges.prototype.Queue = function(e) {
	this.events = this.events + e + "\n";
}

PFChanges.prototype.Show = function(e) {
	alert(this.events);
}


PFChanges.prototype.Send = function(e) {
	var postBody = this.events;
	this.events = '';
	new Ajax.Request('/biz/ajax/prototype.pl/NAVCAT/Batch', { 
		postBody: postBody, asynchronous: 1,
		onComplete: function(request){NAVCAThandleResponse(request.responseText);
		} 
		}) ;			
}



//
// Product Finder Get Results
//		id is the id of the product finder (probably PF/$src)
//		btn is the button which was clicked ex: current, recent, csv, all, search
function PFGetResults(id,btn,txt) {

	// alert('id: '+id+' btn: '+btn);
	if ((btn != 'fromlist') && (btn != 'fromcat')) {
		// note: fromlist and fromcategory don't change the button state.
		$(id+'!button:current').className = 'button';
		$(id+'!button:recent').className = 'button';
		$(id+'!button:all').className = 'button';
		$(id+'!button:showlist').className = 'button';
		$(id+'!button:showcat').className = 'button';
		$(id+'!button:showmore').className = 'button';
		$(id+'!button:search').className = 'button';
		$(id+'!button:csv').className = 'button';
	
		if ($(id+'!button:'+btn)) {
			$(id+'!button:'+btn).className = 'button2';
			}
		}

	var div = $(id+'!results');
	div.innerHTML = '<table height=200 width=250"><tr><td align="center" valign="middle"><img border=0 src="http://www.zoovy.com/biz/loading.gif"></td></tr></table>';

	if (btn == 'showlist') {
		var postBody = 'm=PRODFINDER/ShowList&id='+id+'&btn='+btn;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowList', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
		}
	else if (btn == 'showcat') {
		var postBody = 'm=PRODFINDER/ShowCat&id='+id+'&btn='+btn;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowCat', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
		}
	else if (btn == 'showmore') {
		var postBody = 'm=PRODFINDER/ShowMore&id='+id+'&btn='+btn;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/ShowMore', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;				
		}
	else {
		// alert('id: '+id+' button:'+btn+' txt:'+txt);
		var postBody = 'm=PRODFINDER/Load&id='+id+'&btn='+btn+'&txt='+encodeURIComponent(txt);
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Load', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
		}

	}


//
//
function ProductFinder(src,div) {
	// alert('div: '+div+' src:'+src);
	if ($('PF/'+src)) {
		// products are already displayed, so go hide them.
		$(div).innerHTML = '';		
		}
	else {
		//
		var postBody = 'm=PRODFINDER/New&src='+src+'&div='+div;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/New', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;			
		}
	
	}


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
function PFupdown(cb,direction) {
	// alert ('cb: '+cb+' direction: '+direction);
	var id = cb.id.substring(0,cb.id.indexOf('!'));
	var pid = cb.id.substring(cb.id.indexOf('!')+1);
	var tr = $(id+'!tr:'+pid);

	allTR = $(id+'!datatable').rows;
	totalRows = allTR.length;

	for (x=0; x < totalRows; x++){
		if (tr.id == allTR[x].id) {
			// found row! 

			var y = -1;
			if (direction == 'up') { y = x - 1; }
			else if (direction == 'down') { y = x + 1; }

			if ((direction == 'down') && (y>=totalRows)) { y = -1; alert('operation denied'); }
			if ((direction == 'up') && (x<=0)) { y = -1; alert('operation denied!'); }

			// alert('x: '+x+' y: '+y);			
			if (y>=0) {
				// swap contents
				var tmp = '';
				var pid1 = allTR[x].id.substring(cb.id.indexOf('!')+1);
				pid1 = pid1.substring(3);  // strip tr:
				var pid2 = allTR[y].id.substring(cb.id.indexOf('!')+1);
				pid2 = pid2.substring(3);	

				var postBody = 'm=PRODFINDER/Flip&pid1='+pid1+'&pid2='+pid2+'&id='+id;
				new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Flip', { postBody: postBody, asynchronous: 1 }) ;		
				for (i=0;i<5;i++) {
					tmp = allTR[x].cells[i].innerHTML; 
					allTR[x].cells[i].innerHTML = allTR[y].cells[i].innerHTML;
					allTR[y].cells[i].innerHTML = tmp;
					// alert('i: '+i+' tmp: '+tmp);
					}
				tmp = allTR[x].id; allTR[x].id = allTR[y].id;	allTR[y].id = tmp;
				tmp = allTR[x].className; allTR[x].className = allTR[y].className; allTR[y].className = tmp;
				// tmp = allTR[x].style; allTR[x].style = allTR[y].style; allTR[y].style = tmp;


				}
			}
		}
	return;
	}




//
// ProductFinder Add/Remove Products
//		cb is a reference to "this" checkbox which was probably generated by 
//		a &GTOOLS::Table::buildProductTable
//
function PFaddRemove(cb) {
	// alert(cb.id);

	var pid = cb.id.substring(cb.id.indexOf('!')+1);
	var id = cb.id.substring(0,cb.id.indexOf('!'));
	// alert(cb.checked+'  id: '+id+' pid: '+pid);

	var tr = $(id+'!tr:'+pid);
	// alert(tr.className);

	if (cb.checked) {
		var postBody = 'm=PRODFINDER/Insert&pid='+pid+'&id='+id;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Insert', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;		
		tr.className = tr.className + ' rs';	// adds the selected class to the current tr
		}
	else {
		var postBody = 'm=PRODFINDER/Remove&pid='+pid+'&id='+id;
		new Ajax.Request('/biz/ajax/prototype.pl/PRODFINDER/Remove', { postBody: postBody, asynchronous: 1,onComplete: function(request){NAVCAThandleResponse(request.responseText);} } ) ;		
		tr.className = tr.className.substring(0,2); // removes the ' rs' from the current tr
		}

	}


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
				try { eval(params['js']); } catch (e) { alert('failed: '+params['js']); }
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


