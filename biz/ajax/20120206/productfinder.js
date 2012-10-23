function loadProducts(mode,value) {
	// alert(mode+': '+value);

	\$('popimg!search').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!search');
	\$('popimg!recent').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!recent');
	\$('popimg!navcat').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!navcat');
	\$('popimg!list').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!list');
	\$('popimg!all').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!all');
	\$('popimg!pids').src = '/biz/ajax/navcat_icons/miniup.gif';
	Element.hide('popnfo!pids');

	if (mode != '') {	
		\$('popimg!'+mode).src = '/biz/ajax/navcat_icons/minidown.gif';
		Element.show('popnfo!'+mode);

		var postBody = 'm=PRODUCTFINDER/Load&mode='+escape(mode)+'&value='+escape(value);
		new Ajax.Request('/biz/ajax/prototype.pl/PRODUCTFINDER/Load', { postBody: postBody, asynchronous: 1,onComplete: function(request){handleResponse(request.responseText);} } ) ;	
		}
	}

