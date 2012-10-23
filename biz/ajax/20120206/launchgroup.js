
function saveForm(thisFrm) {
	thisFrm = $(thisFrm);
	new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/Save', 
		{ postBody: Form.serialize(thisFrm),asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;		
	new Effect.Highlight(thisFrm);
	}

function deleteMe(uuid) {
	new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/Nuke', 
		{ postBody: 'm=LAUNCHGROUP/Nuke&_id='+uuid ,asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;		
	$(uuid).innerHTML = '';
	$(uuid+'!info').innerHTML = '';
	}


// used to determine the hold/unhold value.
function setHold(uuid) {
	var thisCb = $('hold!'+uuid);

	if (thisCb.checked) {
		new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/Hold', 
			{ postBody: 'm=LAUNCHGROUP/Hold&_id='+uuid,asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;		
		}
	else {
		new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/UnHold', 
			{ postBody: 'm=LAUNCHGROUP/UnHold&_id='+uuid,asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;		
		}
	tr = $(uuid);
	if (thisCb.checked) { tr.className = tr.className + ' rs'; } else { tr.className = tr.className.substring(0,tr.className.length-3); }
	}

// used by the main screen to get the info for a specific launch group.
function showMoreInfo(id) {
	var img = $(id+'!img');
	var div = $(id+'!info');

	if (img.src.indexOf('plus')>=0) {
		img.src = '/biz/images/minus-13x13.gif';
		div.innerHTML = 'loading..';
		var postBody = 'm=LAUNCHGROUP/Info&_id='+id;
		new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/Info', 
			{ postBody: postBody,asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;		
		}
	else {
		img.src = '/biz/images/plus-13x13.gif';
		div.innerHTML = '';		
		}
	
	}

// used to load sources e.g. list of navcats, list of lists, etc.
function loadSources(me) {

	var uuid = me.id.substring(0,me.id.indexOf('!'));

	var zs = $(uuid+'!_src2s'); var zt = $(uuid+'!_src2t'); var zx = $(uuid+'!_src2x');
	Element.hide(zs,zt,zx);

	if (me.value == '') {  }
	else if ((me.value == 'list') || (me.value == 'navcat')) {
		Element.show(zs);	
		var postBody = 'm=LAUNCHGROUP/List&type='+me.value+'&select='+zs.id;
		new Ajax.Request('/biz/ajax/prototype.pl/LAUNCHGROUP/List', { postBody: postBody, asynchronous: 1,onComplete: function(request){ handleResponse(request.responseText);} } ) ;			
		}
	else if (me.value == 'other') {
		Element.show(zt,zx);		
		zx.innerHTML = 'Specify DataSource:';
		}
	else if (me.value == 'products') {
		Element.show(zt,zx);			
		zx.innerHTML = 'Product ID: ';
		}
	return(true);	
	}

// used to turn on off dow checkboxes.
function cbselect(me,td) {	
	td = $(td);
	if (me.checked) { td.className = td.className + ' rx'; } else { td.className = td.className.substring(0,td.className.length-3); }
	}

