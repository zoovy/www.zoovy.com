// Morten's JavaScript Tree Menu
// version 2.3.3-alpha
// $Id: mtmcode.js,v 1.46 2003/08/24 19:06:35 nettrom Exp $
// http://www.treemenu.com/

// Copyright (c) 2001-2003, Morten Wang & contributors
// All rights reserved.

// This software is released under the BSD License which should accompany
// it in the file "COPYING".  If you do not have this file you can access
// the license through the WWW at http://www.treemenu.com/license.txt

/******************************************************************************
* Define the MenuItem object.                                                 *
******************************************************************************/
function MTMenuItem(text, url, target, tooltip, icon, openIcon) {
// Item text should default to "" since we expect it to be a String()
	this.text = text ? text : "";

	this.url = url ? url : "";
	this.target =  target ? target : (MTMDefaultTarget ? MTMDefaultTarget : "");
	this.tooltip = tooltip;
	this.icon = icon ? icon : "";
	this.openIcon = openIcon ? openIcon : ""; // used for addSubItem

	this.number = MTMNumber++;

	this.parentNode  = null;
	this.submenu     = null;
	this.expanded    = false;

	var hasPage = this.url != "";
	this.showPlusMinus = MTMShowPlusMinus != null ? MTMShowPlusMinus : false;
	this.showIcon  = MTMShowIcon != null ? MTMShowIcon : true;
	this.showText  = MTMShowText != null ? MTMShowText : true;
	this.plusExpands = MTMPlusExpands != null ? MTMPlusExpands : true;
	this.minusCollapses = MTMinusCollapses != null ? MTMinusCollapses : true;
	this.plusShowsPage = MTMPlusShowsPage != null ? MTMPlusShowsPage : hasPage;
	this.minusShowsPage = MTMinusShowsPage != null ? MTMinusShowsPage : false;
	this.iconExpands = MTMIconExpands != null ? MTMIconExpands : false;
	this.iconCollapses = MTMIconCollapses != null ? MTMIconCollapses : false;
	this.collapsedIconShowsPage = MTMCollapsedIconShowsPage != null ? MTMCollapsedIconShowsPage : hasPage;
	this.expandedIconShowsPage = MTMExpandedIconShowsPage != null ? MTMExpandedIconShowsPage : false;
	this.textExpands = MTMTextExpands != null ? MTMTextExpands : false;
	this.textCollapses = MTMTextCollapses != null ? MTMTextCollapses : false;
	this.collapsedTextShowsPage = MTMCollapsedTextShowsPage != null ? MTMCollapsedTextShowsPage : hasPage;
	this.expandedTextShowsPage = MTMExpandedTextShowsPage != null ? MTMExpandedTextShowsPage : hasPage;

	this.MTMakeSubmenu = MTMakeSubmenu;
	this.makeSubmenu = MTMakeSubmenu;
	this.addSubItem = MTMAddSubItem;
	this.itemClick = MTMItemClickHandler;
	MTMLastItem = this;
}

function MTMakeSubmenu(menu, isExpanded, collapseIcon, expandIcon) {
	this.submenu = menu;
	this.childNodes = this.submenu.items;
	this.expanded = isExpanded;
	this.collapseIcon = collapseIcon ? collapseIcon : "menu_folder_closed.gif";
	this.expandIcon = expandIcon ? expandIcon : "menu_folder_open.gif";
	this.submenu.parentNode = this;

	var i;
	for(i = 0; i < this.submenu.items.length; i++) {
		this.submenu.items[i].parentNode = this;
		if(this.submenu.items[i].expanded) {
			this.expanded = true;
		}
	}

	if(MTMSubsGetPlus.toLowerCase() == "always" || MTMEmulateWE) {
		this.showPlusMinus = true;
	} else if(MTMSubsGetPlus.toLowerCase() == "submenu") {
		for(i = 0; i < this.submenu.items.length; i++) {
			if(this.submenu.items[i].submenu) {
				this.showPlusMinus = true; break;
			}
		}
	}

	var hasPage = this.url != "";
	this.showPlusMinus = MTMShowPlusMinus != null ? MTMShowPlusMinus : this.showPlusMinus;
	this.plusShowsPage = MTMPlusShowsPage != null ? MTMPlusShowsPage : !MTMEmulateWE && hasPage;
	this.iconExpands = MTMIconExpands != null ? MTMIconExpands : !MTMEmulateWE || !hasPage;
	this.iconCollapses = MTMIconCollapses != null ? MTMIconCollapses : !MTMEmulateWE || !hasPage;
	this.collapsedIconShowsPage = MTMCollapsedIconShowsPage != null ? MTMCollapsedIconShowsPage : hasPage;
	this.expandedIconShowsPage = MTMExpandedIconShowsPage != null ? MTMExpandedIconShowsPage : MTMEmulateWE && hasPage;
	this.textExpands = MTMTextExpands != null ? MTMTextExpands : !MTMEmulateWE || !hasPage;
	this.textCollapses = MTMTextCollapses != null ? MTMTextCollapses : !hasPage;
}

function MTMakeLastSubmenu(menu, isExpanded, collapseIcon, expandIcon) {
	this.items[this.items.length-1].makeSubmenu(menu, isExpanded, collapseIcon, expandIcon);
}

function MTMAddSubItem(item) {
	if(this.submenu == null){
		this.MTMakeSubmenu(new MTMenu(), false, this.icon, this.openIcon);
	}
	this.submenu.MTMAddItem(item);
}

/******************************************************************************
* Define the Menu object.                                                     *
******************************************************************************/

function MTMenu() {
	this.items   = new Array();
	this.MTMAddItem = MTMAddItem;
	this.addItem = MTMAddItem;
	this.makeLastSubmenu = MTMakeLastSubmenu;
	this.parentNode = null;
}

function MTMAddItem() {
	var lastItemIndex = this.items.length;
	if(arguments[0].toString().indexOf("[object Object]") != -1) {
		this.items[lastItemIndex] = arguments[0];
	} else {
		this.items[lastItemIndex] = new MTMenuItem(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4]);
	}
	this.items[lastItemIndex].parentNode = this.parentNode;
}

/******************************************************************************
* Define the icon list, addIcon function and MTMIcon item.                    *
******************************************************************************/

function IconList() {
	this.items = new Array();
	this.addIcon = addIcon;
}

function addIcon(item) {
	this.items[this.items.length] = item;
}

function MTMIcon(iconfile, match, type) {
	this.file = iconfile;
	this.match = match;
	this.type = type;
}

/******************************************************************************
* Define the stylesheet rules objects and methods.                            *
******************************************************************************/

function MTMstyleRuleSet() {
	this.rules = new Array();
	this.addRule = MTMaddStyleRule;
}

function MTMaddStyleRule(thisSelector, thisStyle) {
	this.rules[this.rules.length] = new MTMstyleRule(thisSelector, thisStyle);
}

function MTMstyleRule(thisSelector, thisStyle) {
	this.selector = thisSelector;
	this.style = thisStyle;
}

/******************************************************************************
* The MTMBrowser object.  A custom "user agent" that'll define the browser    *
* seen from the menu's point of view.                                         *
******************************************************************************/

function MTMBrowser() {
	// default properties and values
	this.cookieEnabled = false;
	this.preHREF = "";
	this.MTMable = false;
	this.cssEnabled = true;
	this.browserType = "other";
	this.majVersion = null;
	this.DOMable = null;

	// properties concerning output document
	this.menuFrame = null;
	this.document = null;
	this.head = null;
	this.menuTable = null;

	// methods
	this.setDocument = MTMsetDocument;
	this.getFrames = MTMgetFrames;
	this.appendElement = MTMappendElement;
	this.resolveURL = MTMresolveURL;

	if(navigator.userAgent.indexOf("Opera") != -1) {
		if(navigator.appName == "Opera") {
			this.majVersion = parseInt(navigator.appVersion);
		} else {
			this.majVersion = parseInt(navigator.userAgent.substring(navigator.userAgent.indexOf("Opera")+6));
		}
		if(this.majVersion >= 5) {
			this.MTMable = true;
			this.browserType = "O";
		}
	} else if(navigator.appName == "Netscape" && navigator.userAgent.indexOf("WebTV") == -1) {
		this.MTMable = true;
		this.browserType = "NN";
		if(parseInt(navigator.appVersion) == 3) {
			this.majVersion = 3;
			this.cssEnabled = false;
		} else if(parseInt(navigator.appVersion) >= 4) {
			this.majVersion = parseInt(navigator.appVersion) == 4 ? 4 : 5;
			if(this.majVersion >= 5) {
				this.DOMable = true;
			}
		}
	} else if(navigator.appName == "Microsoft Internet Explorer" && parseInt(navigator.appVersion) >= 4) {
		this.MTMable = true;
		if(navigator.userAgent.toLowerCase().indexOf("mac") != -1) {
			this.browserType = "NN";
			this.majVersion = 4;
			this.DOMable = false;
		} else {
			this.browserType = "IE";
			this.majVersion = navigator.appVersion.indexOf("MSIE 6.") != -1 ? 6 : (navigator.appVersion.indexOf("MSIE 5.") != -1 ? 5 : 4);
			if(this.majVersion >= 5) {
				this.DOMable = true;
			}
		}
	}
	this.preHREF = location.href;
	if(location.search) {
		this.preHREF = this.preHREF.substring(0, this.preHREF.lastIndexOf("?"));
	}
	this.preHREF = this.preHREF.substring(0, this.preHREF.lastIndexOf("/") +1)
}

function MTMsetDocument(menuFrame) {
	// called by function MTMgetFrames and sets
	// properties .menuFrame and .document, and for DOMable browsers also .head
	this.menuFrame = menuFrame;
	this.document = menuFrame.document;

	if(this.DOMable) {
		this.head = this.browserType == "IE" ? this.document.all.tags('head')[0] : this.document.getElementsByTagName('head').item(0);
	}
}

function MTMresolveURL(thisURL, testLocal) {
	// resolves 'thisURL' against this.preHREF depending on whether it's an absolute
	// or relative URL.  if 'testLocal' is set it'll return true for local (relative) URLs.
	var absoluteArray = new Array("http://", "https://", "mailto:", "ftp://", "telnet:", "news:", "gopher:", "nntp:", "javascript:", "file:");

	var tempString, i = 0, n = absoluteArray.length;
	while(!tempString && i < n) {
		if(thisURL.indexOf(absoluteArray[i]) == 0) {
			tempString = thisURL;
		}
		i++;
	}
	if(testLocal) {
		return(!tempString ? true : false);
	}

	if(!tempString) {
		if(thisURL.indexOf("/") == 0) {
			tempString = location.protocol + "//" + location.host + thisURL;
		} else if(thisURL.indexOf("../") == 0) {
			tempString = this.preHREF;
			do {
				thisURL = thisURL.substr(3);
				tempString = tempString.substr(0, tempString.lastIndexOf("/", tempString.length-2) +1);
			} while(thisURL.indexOf("../") == 0);
			tempString += thisURL;
		} else {
			tempString = this.preHREF + thisURL;
		}
	}
	return(tempString);
}

/******************************************************************************
* Default values of all user-configurable options.                            *
******************************************************************************/

var MTMLinkedJSURL, MTMLinkedSS, MTMSSHREF, MTMLinkedInitFunction, MTMDOCTYPE,
		MTMcontentType, MTMHeader = "", MTMFooter = "", MTMrightClickMessage,
		MTMDefaultTarget, MTMTimeOut = 5;
var MTMuseScrollbarCSS, MTMscrollbarBaseColor, MTMscrollbarFaceColor,
		MTMscrollbarHighlightColor, MTMscrollbarShadowColor,
		MTMscrollbar3dLightColor, MTMscrollbarArrowColor, MTMscrollbarTrackColor,
		MTMscrollbarDarkShadowColor;
var MTMUseCookies, MTMCookieName, MTMCookieDays, MTMTrackedCookieName;
var MTMCodeFrame = "code", MTMenuFrame = "menu", MTMTableWidth = "100%",
		MTMenuImageDirectory = "menu-images/";
var MTMUseToolTips = true, MTMEmulateWE, MTMAlwaysLinkIfWE = true,
		MTMSubsGetPlus = "Submenu", MTMSubsAutoClose;
var MTMBackground = "", MTMBGColor = "#ffffff", MTMTextColor = "#000000",
		MTMLinkColor = "#330099", MTMTrackColor = "#000000",
		MTMAhoverColor = "#990000", MTMSubExpandColor = "#666699",
		MTMSubClosedColor = "#666699", MTMSubTextColor = "#000000";
var MTMenuText = "Site contents:", MTMRootIcon = "menu_new_root.gif",
		MTMRootColor = "#000000";
var MTMRootFont = MTMenuFont = "Arial, Helvetica, sans-serif";
var MTMRootCSSize = MTMenuCSSize = "84%";
var MTMRootFontSize = MTMenuFontSize = "-1";
var MTMDisplayRoot = MTMDisplayRootBar = MTMDisplayRootPlusMinus = true;
var MTMShowPlusMinus, MTMShowIcon, MTMShowText, MTMPlusExpands, MTMinusCollapses,
		MTMPlusShowsPage, MTMinusShowsPage, MTMIconExpands, MTMIconCollapses,
		MTMCollapsedIconShowsPage, MTMExpandedIconShowsPage, MTMTextExpands,
		MTMTextExpands, MTMTextCollapses, MTMCollapsedTextShowsPage,
		MTMExpandedTextShowsPage;

/******************************************************************************
* Global variables.  Not to be altered unless you know what you're doing.     *
* User-configurable options are found in code.html                            *
******************************************************************************/

var MTMLoaded = false;
var MTMLevel;
var MTMBar = new Array();
var MTMIndices = new Array();

var MTMUA = new MTMBrowser();

var MTMExtraCSS = new MTMstyleRuleSet();
var MTMstyleRules;

var MTMLastItem; // last item added to a menu
var MTMClickedItem = false;
var MTMExpansion = false;

var MTMNumber = 1;
// storing the tracked items (plural) now
var MTMTrackedItems = new Array();
var MTMTrack = false;

var MTMignoreDisplay = false;

var MTMFrameNames;

var MTMFirstRun = true;
var MTMCurrentTime = 0;
var MTMUpdating = false;
var MTMWinSize, MTMyval, MTMxval;
var MTMOutputString = "";

var MTMCookieString = "";
var MTMCookieCharNum = 0;
var MTMTCArray, MTMTrackedCookie;

/******************************************************************************
* Code that picks up frame names of frames in the parent frameset.            *
******************************************************************************/

function MTMgetFrames() {
	if(this.MTMable) {
		MTMFrameNames = new Array();
		for(i = 0; i < parent.frames.length; i++) {
			MTMFrameNames[i] = parent.frames[i].name;
			if(parent.frames[i].name == MTMenuFrame) {
				this.setDocument(parent.frames[i]);
			}
		}
	}
}

/******************************************************************************
* Functions to draw the menu.                                                 *
******************************************************************************/

function MTMItemClickHandler(srcElement, doSubAction) {
	// set tracked
	// if DOMable look for all elements in MTMtrackedItem-array
	// and unset their classes
	if(MTMUA.DOMable) {
		var i, myElements;
		for(i = 0; i < MTMTrackedItems.length; i++) {
			myElements = MTMUA.document.getElementsByName("item" + MTMTrackedItems[i].number);
			if(myElements.length > 0) {
				myElements.item(myElements.length-1).className = "";
			}
		}
	}
	MTMTrackedItems = null;
	MTMTrackedItems = new Array(this);
	if(MTMUA.DOMable) {
		// then set the clicked item's class
		srcElement.className = "tracked";
	}
	// if target == _blank or URL is !local, or target can't be tracked, do not
	// set ignore-variable, else do.
	if(this.target == "_blank" || !MTMUA.resolveURL(this.url, true) || !MTMTrackTarget(this.target)) {
		MTMignoreDisplay = false;
	} else {
		MTMignoreDisplay = true;
	}

	if(doSubAction) {
		MTMSubAction(this);
	} else if(!MTMUA.DOMable) {
		setTimeout('MTMDisplayMenu(true)', 10);
	}
	return true;
}

function MTMSubAction(SubItem) {
	SubItem.expanded = (SubItem.expanded) ? false : true;
	// change goes here, if expansion close all submenus on same level (also
	// parent levels?)
	if(MTMSubsAutoClose && SubItem.expanded) {
		MTMExpansion = true;
		MTMCloseSubs(SubItem);
		var i;
		// maybe this part should go too?
		for(i = 0; i < SubItem.childNodes.length; i++) {
			if(SubItem.childNodes[i].submenu) {
				SubItem.childNodes[i].expanded = false;
			}
		}
	}

	MTMClickedItem = SubItem;

	setTimeout("MTMDisplayMenu(true)", 10);

	return true;
}

function MTMStartMenu(thisEvent) {
	if(MTMUA.browserType == "O" && MTMUA.majVersion == 5) {
		parent.onload = MTMStartMenu;
		if(thisEvent) {
			return;
		}
	}
	MTMLoaded = true;
	if(MTMFirstRun) {
		if(MTMCurrentTime++ == MTMTimeOut) { // notice the post-increment
			setTimeout("MTMDisplayMenu()",10);
		} else {
			setTimeout("MTMStartMenu()",100);
		}
	} 
}

function MTMDisplayMenu(forcedUpdate) {
	if(!forcedUpdate && MTMignoreDisplay) {
		MTMignoreDisplay = false;
		MTMTrack = false;
		return null;
	}

	if(MTMUA.MTMable && !MTMUpdating) {
		MTMUpdating = true;
		MTMLevel = 0;

		if(MTMFirstRun) {
			MTMUA.getFrames();

			if(MTMUseCookies) { 
				MTMFetchCookies();
				if(MTMTrackedCookie) {
					MTMTCArray = MTMTrackedCookie.split("::");
					MTMTrackedItem = MTMTCArray[0];
					if(parent.frames[MTMTCArray[1]]) {
						parent.frames[MTMTCArray[1]].location = MTMTCArray[2];
					}
					MTMTCArray = null;
				}
			}
		}

		if(MTMTrack) {
			MTMTrackedItems = null; MTMTrackedItems = new Array();
			MTMTrackExpand(menu);
		}

		// this needs a rewrite when the multi-item tracking is in
		// moved to function MTMSubAction()
		// if(MTMExpansion && MTMSubsAutoClose) { MTMCloseSubs(menu); }

		if(MTMUA.DOMable) {
			if(MTMFirstRun) {
				MTMinitializeDOMDocument();
			}
		} else if(MTMFirstRun || MTMUA.browserType != "IE") {
			// start of document output
			MTMUA.document.open("text/html", "replace");
			MTMOutputString = (MTMDOCTYPE ? (MTMDOCTYPE + "\n") : '') + "<html><head>\n";
			if(MTMcontentType) {
				MTMOutputString += '<meta http-equiv="Content-Type" content="' + MTMcontentType + '">\n';
			}
			if(MTMLinkedSS) {
				MTMOutputString += '<link rel="stylesheet" type="text/css" href="' + MTMUA.resolveURL(MTMSSHREF) + '">\n';
			} else {
				MTMUA.document.writeln(MTMOutputString);
				MTMOutputString = "";
				MTMcreateStyleSheet();
			}
			if(MTMUA.browserType == "IE" && MTMrightClickMessage) {
				MTMOutputString += '<scr' + 'ipt type="text/javascript">\nfunction MTMcatchRight() {\nif(event && (event.button == 2 || event.button == 3)) {\nalert("' + MTMrightClickMessage + '");\nreturn false;\n}\nreturn true;\n}\n\ndocument.onmousedown = MTMcatchRight;\n';
				MTMOutputString += '<\/scr' + 'ipt>\n';
			}
			MTMOutputString += '</head>\n<body ';
			if(MTMBackground != "") {
				MTMOutputString += 'background="' + MTMUA.resolveURL(MTMenuImageDirectory + MTMBackground) + '" ';
			}
			MTMOutputString += 'bgcolor="' + MTMBGColor + '" text="' + MTMTextColor + '" link="' + MTMLinkColor + '" vlink="' + MTMLinkColor + '" alink="' + MTMLinkColor + '">\n';
			MTMUA.document.writeln(MTMOutputString + (MTMHeader ? MTMHeader : "") + '\n<table border="0" cellpadding="0" cellspacing="0" width="' + MTMTableWidth + '" id="mtmtable">\n');
		}

		if(!MTMFirstRun && (MTMUA.DOMable || MTMUA.browserType == "IE")) {
			if(!MTMUA.menuTable) {
				MTMUA.menuTable = MTMUA.document.all('mtmtable');
			}

			while(MTMUA.menuTable.rows.length > 1) {
				MTMUA.menuTable.deleteRow(1);
			}
		}

		if (MTMDisplayRoot) {
			MTMOutputString = '<img src="' + MTMUA.resolveURL(MTMenuImageDirectory + MTMRootIcon) + '" align="left" border="0" vspace="0" hspace="0">';
			if(MTMUA.cssEnabled) {
				MTMOutputString += '<span id="root">&nbsp;' + MTMenuText + '</span>';
			} else {
				MTMOutputString += '<font size="' + MTMRootFontSize + '" face="' + MTMRootFont + '" color="' + MTMRootColor + '">' + MTMenuText + '</font>';
			}
		}
		if(MTMFirstRun || (!MTMUA.DOMable && MTMUA.browserType != "IE")) {
			MTMAddCell(MTMOutputString);
		}

		MTMListItems(menu);

		if(!MTMUA.DOMable && (MTMFirstRun || MTMUA.browserType != "IE")) {
			MTMUA.document.writeln('</table>\n' + (MTMFooter ? MTMFooter : "") + '\n');
			if(MTMLinkedJSURL && MTMUA.browserType != "IE") {
				MTMUA.document.writeln('<scr' + 'ipt defer type="text/javascript" src="' + MTMUA.resolveURL(MTMLinkedJSURL) + '"></scr' + 'ipt>');
			}
			MTMUA.document.writeln('\n</body>\n</html>');
			MTMUA.document.close();
		}
		// end of document output

		if(!MTMFirstRun && MTMUA.cookieEnabled) { 
			if(MTMCookieString != "") {
				setCookie(MTMCookieName, MTMCookieString.substring(0,4000), MTMCookieDays);
				if(MTMTrackedCookieName) {
					if(MTMTCArray) {
						setCookie(MTMTrackedCookieName, MTMTCArray.join("::"), MTMCookieDays);
					} else {
						setCookie(MTMTrackedCookieName, "", -1);
					}
				}
			} else {
				setCookie(MTMCookieName, "", -1);
			}
		}
		if(MTMLinkedJSURL && MTMLinkedInitFunction && !(MTMUA.browserType == "IE" && MTMUA.majVersion == 4)) {
			setTimeout('MTMUA.menuFrame.' + MTMLinkedInitFunction + '()', 10);

		}

		MTMFirstRun = false;
		MTMClickedItem = false;
		MTMExpansion = false;
		MTMTrack = false;
		MTMCookieString = "";
	}
MTMUpdating = false;
}

function MTMScrollTo() {
// this needs changing now.  we'll need to find the first tracked item.
// check the position of all tracked items present in the menu frame
// and choose the lowest one.  if it's not present in the viewport
// (the viewport is defined as upper 2/3 of the menu frame) scroll the
// window so it _is_ viewable.  since the new highlighting code doesn't
// call MTMDisplayMenu() we know that the user hasn't scrolled to the
// item when this part of the code is called.

// how to solve the problem with scrolling when the item isn't
// a tracked item, but instead a submenu?  write a scrollTo() method
// property of an item instead and then let either MTMSubAction() do
// it, or do it here?  needs thinking...

// create a collection of all A-elements (document.links, or document.all.tags
// or document.getElementsByName()) then iterate over those, find the lowest
//  y-pos of them all, then check if that's in the viewport.

// so this doesn't become O(n*m) use an array and remove each match
// then it becomes maybe O(n * log(m)) or something...

// can Opera scroll correctly?  bug list indicates the answer is
// "no", but check with O6.  O5 couldn't retrieve any positions.
	if(!(MTMUA.browserType == "NN" && MTMUA.majVersion == 3)) {
		var i, bestPos, thisPos;
		for(i = 0; i < MTMTrackedItems.length; i++) {
			thisPos = MTMgetPos(MTMTrackedItems[i].number);
			if(thisPos < bestPos) {
				bestPos = thisPos;
			}
		}
		alert(bestPos);
	}
}

function MTMgetPos(itemNumber) {
	var i, elementName = "item" + itemNumber;
	if(MTMUA.browserType == "NN" && MTMUA.majVersion == 4) {
		// in NN4, pull out MTMUA.document.anchors[i].y
		// must I use document.links?
		for(i = 0; i < MTMUA.document.anchors.length; i++) {
			if(MTMUA.document.anchors[i].name == MTMItemName) {
				return(MTMUA.document.links[i].y);
			}
		}
	} else if(MTMUA.browserType == "IE" && !MTMUA.DOMable) {
		// in IE4 & 5...
		// problem is, have we got multiple items with the same name?
		// document.all will probably return the _item_ if there's
		// only one... can it be solved with a collection?
		return MTMgetYPos(document.all(elementName));
	} else if(MTMUA.DOMable) {
		// IE6 and Mozilla, use document.getElementsByName()
		var myElements = document.getElementsByName(elementName);
		return (myElements.length > 0 ? MTMgetYPos(myElements.item(0)) : 0);
	}
}

//		if((MTMClickedItem || MTMTrackedItem) && !(MTMUA.browserType == "NN" && MTMUA.majVersion == 3)) {
//			MTMItemName = "item" + (MTMClickedItem ? MTMClickedItem.number : MTMTrackedItem);
//			if(document.layers && MTMUA.menuFrame.scrollbars) {
//				if(!true) {
//				var i;
//				for(i = 0; i < MTMUA.document.anchors.length; i++) {
//					if(MTMUA.document.links[i].name == MTMItemName) {
//						MTMyval = MTMUA.document.links[i].y;
//						MTMUA.document.links[i].focus();
//						break;
//					}
//				}
//				MTMWinSize = MTMUA.menuFrame.innerHeight;
//			} else if(MTMUA.browserType != "O") {
//				if(MTMUA.browserType == "NN" && MTMUA.majVersion == 5) {
//					MTMUA.document.all = MTMUA.document.getElementsByTagName("*");
//				}
// IE dies silently if document.all[MTMItemName] is a collection
// instead of an object
//				MTMyval = MTMGetYPos(MTMUA.document.all[MTMItemName]);
//				MTMUA.document.all[MTMItemName].focus();
//				MTMWinSize = MTMUA.browserType == "IE" ? MTMUA.document.body.offsetHeight : MTMUA.menuFrame.innerHeight;
//			}
//			if(MTMyval > (MTMWinSize - 60)) {
//				MTMUA.menuFrame.scrollTo(0, parseInt(MTMyval - (MTMWinSize * 1/3)));
//			}
//		}
// }

function MTMinitializeDOMDocument() {
	var newElement;
	if(MTMcontentType) {
// Fixed 2003-01-20, httpEquiv->http-equiv, credits to John Russell
		MTMUA.appendElement('head', 'meta', 'http-equiv', 'Content-Type', 'content', MTMcontentType);
	}
	MTMdisableStyleSheets();

	if(MTMLinkedSS) {
		MTMUA.appendElement('head', 'link', 'rel', 'stylesheet', 'type', 'text/css', 'href', MTMUA.resolveURL(MTMSSHREF));
	} else {
		MTMcreateStyleSheet();
	}
	if(MTMLinkedJSURL) {
		MTMUA.appendElement('head', 'script', 'src', MTMUA.resolveURL(MTMLinkedJSURL), 'type', 'text/javascript', 'defer', true);
	}
	while(MTMUA.document.body.childNodes.length > 0) {
		MTMUA.document.body.removeChild(MTMUA.document.body.firstChild);
	}

	var insertHTML = MTMHeader
	+ '<table border="0" cellpadding="0" cellspacing="0" width="' + MTMTableWidth
	+ '" id="mtmtable"></table>' + MTMFooter;
	if(MTMUA.browserType == "IE") {
		MTMUA.document.body.insertAdjacentHTML("afterBegin", insertHTML);
	} else {
		var myRange = MTMUA.document.createRange();
		myRange.setStart(MTMUA.document.body, 0);
		var parsedHTML = myRange.createContextualFragment(insertHTML);
		MTMUA.document.body.appendChild(parsedHTML);
	}
	MTMUA.menuTable = MTMUA.document.getElementById('mtmtable');
}

function MTMappendElement() {
	var newElement = this.document.createElement(arguments[1]);
	var j, newProperty;
	for(j = 2; j < arguments.length; j+=2) {
		newElement.setAttribute(arguments[j], arguments[j+1]);
	}
	if(arguments[0] == 'head') {
		this.head.appendChild(newElement);
	} else if(arguments[0] == 'body') {
		this.document.body.appendChild(newElement);
	}
}

function MTMListItems(menu) {
	var i, isLast, isFirst;
	for (i = 0; i < menu.items.length; i++) {
		MTMIndices[MTMLevel] = i;
		isLast = (i == menu.items.length -1);
		isFirst = (i == 0);
		MTMDisplayItem(menu.items[i], isLast, isFirst);

		if(menu.items[i].submenu && menu.items[i].expanded) {
			if(MTMLevel == 0 && !MTMDisplayRootBar) {
				MTMBar[MTMLevel] = false;
			} else {
				MTMBar[MTMLevel] = (isLast) ? false : true;
			}
			MTMLevel++;
			MTMListItems(menu.items[i].submenu);
			MTMLevel--;
		} else {
			MTMBar[MTMLevel] = false;
		} 
	}
}

function MTMDisplayItem(item, last, first) {
	var i, img, subNoLink;

	// var MTMfrm = "parent"; // .frames['" + MTMCodeFrame + "']";
	var MTMfrm = "parent.frames['code']";
	var MTMref = '.menu.items[' + MTMIndices[0] + ']';
	if(MTMLevel > 0) {
		for(i = 1; i <= MTMLevel; i++) {
			MTMref += ".childNodes[" + MTMIndices[i] + "]";
		}
	}

	var MTMClickCmd = MTMItemClickCmd = MTMCombinedClickCmd = "return " + MTMfrm;
	MTMClickCmd += ".MTMSubAction(" + MTMfrm + MTMref + ");";
	MTMItemClickCmd += MTMref + ".itemClick(this);";
	MTMCombinedClickCmd += MTMref + ".itemClick(this, true);";

	if(MTMUA.cookieEnabled) {
		if(MTMFirstRun && MTMCookieString != "") {
			item.expanded = (MTMCookieString.charAt(MTMCookieCharNum++) == "1") ? true : false;
		} else {
			MTMCookieString += (item.expanded) ? "1" : "0";
		}
	}

	if(item.submenu) {
		var MTMouseOverCmd = "parent.status='" + (item.expanded ? "Collapse " : "Expand ") + (item.text.indexOf("'") != -1 ? MTMEscapeQuotes(item.text) : item.text) + "';return true;";
		var MTMouseOutCmd = "parent.status=parent.defaultStatus;return true;";
	}

	MTMOutputString = "";
	if(MTMLevel > 0) {
		for (i = 0; i < MTMLevel; i++) {
			if (MTMDisplayRootBar || i > 0) {
				MTMOutputString += (MTMBar[i]) ? MTMakeImage("menu_bar.gif") : MTMakeImage("menu_pixel.gif");
			}
		}
	}

	var madeLink = false;
	var voidURL, addTitle;

	if(item.showPlusMinus && (MTMDisplayRootPlusMinus || MTMLevel > 0)) {
		madeLink = true;
		if (item.expanded) {
			if (MTMDisplayRootBar || MTMLevel > 0 || MTMDisplayRoot && !first) {
				img = last ? "menu_bottom_corner_minus.gif" : "menu_tee_minus.gif";
			} else {
				img = (!MTMDisplayRootBar && MTMLevel == 0 || !MTMDisplayRoot && !first || first && last) ?
					"menu_minus.gif" : "menu_top_corner_minus.gif";
			}
			if (item.minusShowsPage) {
				voidURL = false;
				addTitle = true;
				if (item.minusCollapses) {
					// submenu expanded: show page, collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
				} else {
					// submenu expanded: show page, do not collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.minusCollapses) {
					// submenu expanded: collapse, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
				} else {
					// submenu expanded: do not collapse, do not show page
					madeLink = false;
				}
			}
		} else {
			if ((MTMDisplayRootBar || MTMLevel > 0) && (MTMDisplayRoot || !first)) {
				img = last ? "menu_bottom_corner_plus.gif" : "menu_tee_plus.gif";
			} else {
				img = (!MTMDisplayRootBar && MTMLevel == 0 || !MTMDisplayRoot && !first || first && last) ?
					"menu_plus.gif" : "menu_top_corner_plus.gif";
			}
			if (item.plusShowsPage) {
				voidURL = false;
				addTitle = true;
				MTMItemClickCmd;
				if (item.plusExpands) {
					// submenu collapsed: show page, expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
				} else {
					// submenu collapsed: show page, do not expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.plusExpands) {
					// submenu collapsed: expand, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
				} else {
					// submenu collapsed: do not expand, do not show page
					madeLink = false;
				}
			}
		}
	} else {
		if (MTMDisplayRootBar || MTMLevel > 0 || MTMDisplayRoot && !first) {
			img = (last) ? "menu_bottom_corner.gif" : "menu_tee.gif";
		} else {
			img = (!MTMDisplayRootBar && MTMLevel == 0 || !MTMDisplayRoot && !first || first && last) ?
				"menu_pixel.gif" : "menu_top_corner.gif";
		}
	}
	if (MTMLevel != 0 || MTMDisplayRootBar || MTMDisplayRootPlusMinus) {
		MTMOutputString += MTMakeImage(img);
	}
	if (madeLink) {
		MTMOutputString += '</a>';
	}

	madeLink = false;
	if (item.showIcon) {
		madeLink = true;
		if (item.expanded) {
			if (item.expandedIconShowsPage) {
				voidURL = false;
				addTitle = true;
				if (item.iconCollapses) {
					// submenu expanded: show page, collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
					img = item.expandIcon;
				} else {
					// submenu expanded: show page, do not collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
					img = item.submenu ? item.expandIcon : MTMFetchIcon(item.url);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.iconCollapses) {
					// submenu expanded: collapse, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
					img = item.expandIcon;
				} else {
					// submenu expanded: do not expand, do not show page
					madeLink = false;
					img = item.submenu ? item.expandIcon : (item.icon != "") ? item.icon : MTMFetchIcon(item.url);
				}
			}
		} else {
			if (item.collapsedIconShowsPage) {
				voidURL = false;
				addTitle = true;
				MTMItemClickCmd;
				if (item.iconExpands) {
					// submenu collapsed: show page, expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
					img = item.collapseIcon;
				} else {
					// submenu collapsed: show page, do not expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
					img = item.submenu ? item.collapseIcon : MTMFetchIcon(item.url);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.iconExpands) {
					// submenu collapsed: expand, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
					img = item.collapseIcon;
				} else {
					// submenu collapsed: do not expand, do not show page
					madeLink = false;
					img = item.submenu ? item.collapseIcon : (item.icon != "") ? item.icon : MTMFetchIcon(item.url);
				}
			}
		}
		MTMOutputString += MTMakeImage(img) + (madeLink ? '</a>' : '');
	}


	if (item.showText) {
		madeLink = true;
		if (item.expanded) {
			if (item.expandedTextShowsPage) {
				voidURL = false;
				addTitle = true;
				if (item.textCollapses) {
					// submenu expanded: show page, collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
					img = item.collapseText;
				} else {
					// submenu expanded: show page, do not collapse
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
					img = (item.text != "") ? item.text : MTMFetchText(item.url);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.textCollapses) {
					// submenu expanded: collapse, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
				} else {
					// submenu expanded: do not expand, do not show page
					madeLink = false;
					MTMOutputString += '<span class="subtext">';
				}
			}
		} else {
			if (item.collapsedTextShowsPage) {
				voidURL = false;
				addTitle = true;
				MTMItemClickCmd;
				if (item.textExpands) {
					// submenu collapsed: show page, expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMCombinedClickCmd
					);
					img = item.expandText;
				} else {
					// submenu collapsed: show page, do not expand
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMItemClickCmd
					);
					img = (item.text != "") ? item.text : MTMFetchText(item.url);
				}
			} else {
				voidURL = true;
				addTitle = item.url == "";
				if (item.textExpands) {
					// submenu collapsed: expand, do not show page
					MTMOutputString += MTMakeLink(
						item,
						voidURL,
						true,
						addTitle,
						MTMClickCmd,
						MTMouseOverCmd,
						MTMouseOutCmd
					);
				} else {
					// submenu collapsed: do not expand, do not show page
					madeLink = false;
					MTMOutputString += '<span class="subtext">';
				}
			}
		}
		if(MTMUA.browserType == "NN" && MTMUA.majVersion == 3 && !MTMLinkedSS) {
			var stringColor, n;
			if((n = MTMTrackedItems.length) > 0) {
				i = 0;
				while(!stringColor && i < n) {
					if(MTMTrackedItems[i].number == item.number) {
						stringColor = MTMTrackColor;
					}
					i++;
				}
			}
			if(!stringColor) {
				if(item.submenu && MTMClickedItem && item.number == MTMClickedItem.number) {
					stringColor = (item.expanded) ? MTMSubExpandColor : MTMSubClosedColor;
				} else {
					stringColor = MTMLinkColor;
				}
			}
			MTMOutputString += '<font color="' + stringColor + '" size="' + MTMenuFontSize + '" face="' + MTMenuFont + '">';
		}
		MTMOutputString += (item.showIcon ? '&nbsp;' : '') + item.text;
		MTMOutputString += ((MTMUA.browserType == "NN" && MTMUA.majVersion == 3 && !MTMLinkedSS) ? '</font>' : '');
		MTMOutputString += madeLink ? '</a>' : '</span>';
	}
	MTMAddCell(MTMOutputString);
}

function MTMEscapeQuotes(myString) {
	var newString = "";
	var cur_pos = myString.indexOf("'");
	var prev_pos = 0;
	while (cur_pos != -1) {
		if(cur_pos == 0) {
			newString += "\\";
		} else if(myString.charAt(cur_pos-1) != "\\") {
			newString += myString.substring(prev_pos, cur_pos) + "\\";
		} else if(myString.charAt(cur_pos-1) == "\\") {
			newString += myString.substring(prev_pos, cur_pos);
		}
		prev_pos = cur_pos++;
		cur_pos = myString.indexOf("'", cur_pos);
	}
	return(newString + myString.substring(prev_pos, myString.length));
}

function MTMTrackExpand(thisMenu) {
	var i, targetPath, targetLocation;
	var foundNumber;
	for(i = 0; i < thisMenu.items.length; i++) {
		if(thisMenu.items[i].url != "" && MTMTrackTarget(thisMenu.items[i].target)) {
			targetLocation = parent.frames[thisMenu.items[i].target].location;
			targetHREF = targetLocation.href;
			if(targetHREF.indexOf("#") != -1) {
				targetHREF = targetHREF.substr(0, targetHREF.indexOf("#"));
			}
			if(MTMUA.browserType == "IE" && targetLocation.protocol == "file:") {
				var regExp = /\\/g;
				targetHREF = targetHREF.replace(regExp, "\/");
			}
			if(targetHREF == MTMUA.resolveURL(thisMenu.items[i].url)) {
				MTMTrackedItems[MTMTrackedItems.length] = thisMenu.items[i];
				foundNumber = true;
			}
		}
		if(thisMenu.items[i].submenu) {
			MTMTrackExpand(thisMenu.items[i].submenu);
		}
	}
	if(foundNumber) {
		var thisItem = thisMenu.items[0];
		while(thisItem.parentNode) {
			thisItem.parentNode.expanded = true;
			thisItem = thisItem.parentNode;
		}
	}
}

function MTMCloseSubs(thisItem) {
	var theseItems;
	if(thisItem.parentNode) {
		MTMCloseSubs(thisItem.parentNode);
		theseItems = thisItem.parentNode.childNodes;
	} else {
		theseItems = menu.items;
	}
	var i, n;
	for(i = 0, n = theseItems.length; i < n; i++) {
		if(theseItems[i].submenu && theseItems[i].number != thisItem.number) {
			theseItems[i].expanded = false;
		}
	}
}

function MTMFetchIcon(testString) {
	var i;
	for(i = 0; i < MTMIconList.items.length; i++) {
		if((MTMIconList.items[i].type == 'any') && (testString.indexOf(MTMIconList.items[i].match) != -1)) {
			return(MTMIconList.items[i].file);
		} else if((MTMIconList.items[i].type == 'pre') && (testString.indexOf(MTMIconList.items[i].match) == 0)) {
			return(MTMIconList.items[i].file);
		} else if((MTMIconList.items[i].type == 'post') && (testString.indexOf(MTMIconList.items[i].match) != -1)) {
			if((testString.lastIndexOf(MTMIconList.items[i].match) + MTMIconList.items[i].match.length) == testString.length) {
				return(MTMIconList.items[i].file);
			}
		}
	}
	return("menu_link_default.gif");
}

function MTMGetYPos(myObj) {
	return(myObj.offsetTop + ((myObj.offsetParent) ? MTMGetYPos(myObj.offsetParent) : 0));
}

function MTMakeLink(thisItem, voidURL, addName, addTitle, clickEvent, mouseOverEvent, mouseOutEvent) {

	var tempString = '<a href="' + (voidURL ? 'javascript:;' : MTMUA.resolveURL(thisItem.url)) + '" ';
	if(MTMUseToolTips && addTitle && thisItem.tooltip) {
		tempString += 'title="' + thisItem.tooltip + '" ';
	}

	tempString += 'name="item' + thisItem.number + '" ';

	if(clickEvent) {
		tempString += 'onclick="' + clickEvent + '" ';
	}
	if(mouseOverEvent && mouseOverEvent != "") {
		tempString += 'onmouseover="' + mouseOverEvent + '" ';
	}
	if(mouseOutEvent && mouseOutEvent != "") {
		tempString += 'onmouseout="' + mouseOutEvent + '" ';
	}
	var linkClass, n, i = 0;
	if((n = MTMTrackedItems.length) > 0) {
		while(!linkClass && i < n) {
			if(MTMTrackedItems[i].number == thisItem.number) {
				linkClass = "tracked";
			}
			i++;
		}
	}
	if(linkClass) {
		if(MTMTrackedCookieName) {
			// populate MTMTCArray
			MTMTCArray = new Array(thisItem.number, thisItem.target, thisItem.url);
		}
	} else {
		if(thisItem.submenu && MTMClickedItem && thisItem.number == MTMClickedItem.number) {
			linkClass = (thisItem.expanded ? "subexpanded" : "subclosed");
		}
	}
	if(linkClass) {
		tempString += 'class="' + linkClass + '" ';
	}
	if(thisItem.target != "") {
		tempString += 'target="' + thisItem.target + '" ';
	}
	return(tempString + '>');
}

function MTMakeImage(thisImage) {
	return('<img src="' + MTMUA.resolveURL(MTMenuImageDirectory + thisImage) + '" align="left" border="0" vspace="0" hspace="0" width="18" height="18">');
}

function MTMakeSVG(thisImage) {
	return('<object type="image/svg+xml" data="' + MTMUA.resolveURL(thisImage) + '" NAME="Main" width="18" height="18" ><\/object>');
}

function MTMTrackTarget(thisTarget) {
	if(thisTarget.charAt(0) == "_") {
		return false;
	} else {
		for(i = 0; i < MTMFrameNames.length; i++) {
			if(thisTarget == MTMFrameNames[i]) {
				return true;
			}
		}
	}
	return false;
}

function MTMAddCell(thisHTML) {
	if(MTMUA.DOMable || (MTMUA.browserType == "IE" && !MTMFirstRun)) {
		var myRow = MTMUA.menuTable.insertRow(MTMUA.menuTable.rows.length);
		myRow.vAlign = "top";
		var myCell = myRow.insertCell(myRow.cells.length);
		myCell.noWrap = true;
		myCell.innerHTML = thisHTML;
	} else {
		MTMUA.document.writeln('<tr valign="top"><td nowrap>' + thisHTML + '<\/td><\/tr>');
	}
//	alert(thisHTML);
}

function MTMcreateStyleSheet() {
	var i;

	if(!MTMstyleRules) {
		MTMstyleRules = new MTMstyleRuleSet();
		with(MTMstyleRules) {
			addRule('body', 'color:' + MTMTextColor + ';');
			if(MTMuseScrollbarCSS && MTMUA.browserType != "NN") {
				addRule('body', 'scrollbar-3dlight-color:' + MTMscrollbar3dLightColor + ';scrollbar-arrow-color:' + MTMscrollbarArrowColor + ';scrollbar-base-color:' + MTMscrollbarBaseColor + ';scrollbar-darkshadow-color:' + MTMscrollbarDarkShadowColor + ';scrollbar-face-color:' + MTMscrollbarFaceColor + ';scrollbar-highlight-color:' + MTMscrollbarHighlightColor + ';scrollbar-shadow-color:' + MTMscrollbarShadowColor + ';scrollbar-track-color:' + MTMscrollbarTrackColor + ';');
			}
			addRule('#root', 'color:' + MTMRootColor + ';background:transparent;font-family:' + MTMRootFont + ';font-size:' + MTMRootCSSize + ';');
			addRule('.subtext', 'font-family:' + MTMenuFont + ';font-size:' + MTMenuCSSize + ';color:' + MTMSubTextColor + ';background: transparent;');
			addRule('a', 'font-family:' + MTMenuFont + ';font-size:' + MTMenuCSSize + ';text-decoration:none;color:' + MTMLinkColor + ';background:transparent;');
			addRule('a:hover', 'color:' + MTMAhoverColor + ';background:transparent;');
			addRule('a.tracked', 'color:' + MTMTrackColor + ';background:transparent;');
			addRule('a.subexpanded', 'color:' + MTMSubExpandColor + ';background:transparent;');
			addRule('a.subclosed', 'color:' + MTMSubClosedColor + ';background:transparent;');

		}
	}

	if(MTMUA.DOMable) {
		if(MTMUA.browserType == "IE") {
			for(i = 0; i < MTMUA.document.styleSheets.length; i++) {
				if(MTMUA.document.styleSheets(i).title == 'mtmiesheet') {
					newStyleSheet = MTMUA.document.styleSheets(i);
					break;
				}
			}
			if(newStyleSheet) {
				for(i = 0; i < newStyleSheet.rules.length; i++) {
					newStyleSheet.removeRule();
				}
				newStyleSheet.disabled = false;
			} else {
				newStyleSheet = MTMUA.document.createStyleSheet();
				newStyleSheet.title = 'mtmiesheet';
			}
		} else if(MTMUA.browserType == "NN") {
			var newStyleSheet = MTMUA.document.getElementById('mtmsheet');
			if(newStyleSheet) {
				newStyleSheet.disabled = false;
			}
		}
	} else {
		var outputHTML = '<style type="text/css">\n';
	}
	for(i = 0; i < MTMstyleRules.rules.length; i++) {
		if(MTMUA.DOMable && MTMUA.browserType == "IE") {
			newStyleSheet.addRule(MTMstyleRules.rules[i].selector, MTMstyleRules.rules[i].style);
		} else if(MTMUA.DOMable && MTMUA.browserType == "NN" && newStyleSheet) {
			newStyleSheet.sheet.insertRule((MTMstyleRules.rules[i].selector + " { " + MTMstyleRules.rules[i].style + " } "), newStyleSheet.sheet.cssRules.length);
		} else {
			outputHTML += MTMstyleRules.rules[i].selector + ' {\n' + MTMstyleRules.rules[i].style + '\n}\n';
		}
	}
	
	for(i = 0; i < MTMExtraCSS.rules.length; i++) {
		if(MTMUA.DOMable && MTMUA.browserType == "IE") {
			newStyleSheet.addRule(MTMExtraCSS.rules[i].selector, MTMExtraCSS.rules[i].style);
		} else if(MTMUA.DOMable && MTMUA.browserType == "NN" && newStyleSheet) {
			newStyleSheet.sheet.insertRule((MTMExtraCSS.rules[i].selector + "{" + MTMExtraCSS.rules[i].style + "}"), newStyleSheet.sheet.cssRules.length);
		} else {
			outputHTML += MTMExtraCSS.rules[i].selector + ' {\n' + MTMExtraCSS.rules[i].style + '\n}\n';
		}
	}
	if(MTMFirstRun && MTMUA.DOMable) {
		with(MTMUA.document.body) {
			bgColor = MTMBGColor;
			text = MTMTextColor;
			link = MTMLinkColor;
			vLink = MTMLinkColor;
			aLink = MTMLinkColor;
			if(MTMBackground) {
				background = MTMUA.resolveURL(MTMenuImageDirectory + MTMBackground);
			}
		}
	} else if(!MTMUA.DOMable) {
		MTMUA.document.writeln(outputHTML + '</style>');
	}
}

function MTMdisableStyleSheets() {
	if(MTMUA.browserType == "IE") {
		for(i = 0; i < MTMUA.document.styleSheets.length; i++) {
			MTMUA.document.styleSheets(i).disabled = true;
		}
	} else if(MTMUA.browserType == "NN") {
		var myCollection = MTMUA.document.getElementsByTagName('style');
		for(i = 0; i < myCollection.length; i++) {
			myCollection.item(i).disabled = true;
		}
		var myCollection = MTMUA.document.getElementsByTagName('link');
		for(i = 0; i < myCollection.length; i++) {
			if(myCollection.item(i).getAttribute('type') == "text/css") {
				myCollection.item(i).disabled = true;
			}
		}
	}
}

function MTMFetchCookies() {
	var cookieString = getCookie(MTMCookieName);
	if(cookieString == null) {
		setCookie(MTMCookieName, "Say-No-If-You-Use-Confirm-Cookies");
		cookieString = getCookie(MTMCookieName);
		MTMUA.cookieEnabled = (cookieString == null) ? false : true;
		return;
	}

	MTMCookieString = cookieString;
	if(MTMTrackedCookieName) { MTMTrackedCookie = getCookie(MTMTrackedCookieName); }
	MTMUA.cookieEnabled = true;
}

// These are from Netscape's Client-Side JavaScript Guide.
// setCookie() is altered to make it easier to set expiry.

function getCookie(Name) {
	var search = Name + "="
	if (document.cookie.length > 0) { // if there are any cookies
		offset = document.cookie.indexOf(search)
		if (offset != -1) { // if cookie exists
			offset += search.length
			// set index of beginning of value
			end = document.cookie.indexOf(";", offset)
			// set index of end of cookie value
			if (end == -1)
				end = document.cookie.length
			return unescape(document.cookie.substring(offset, end))
		}
	}
}

function setCookie(name, value, daysExpire) {
	if(daysExpire) {
		var expires = new Date();
		expires.setTime(expires.getTime() + 1000*60*60*24*daysExpire);
	}
	document.cookie = name + "=" + escape(value) + (daysExpire == null ? "" : (";expires=" + expires.toGMTString())) + ";path=/";
}

function show_props(obj, obj_name) {
var result = ""
for (var i in obj)
result += obj_name + "." + i + " = " + obj[i] + "\n"
return result
}
