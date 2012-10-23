
/* this is to keep people from stealing bandwidth */
/* remove this to run this on your own server */


isNS = document.layers?true:false;
isIE = navigator.appName.indexOf("Microsoft") != -1
isNS6 = !isIE && document.getElementById?true:false;

function NewDiv(window, id, body, left, top, width, height, zIndex, absolute) {
    this.window = window;
    this.id     = id;
    this.body   = body;
    var d = window.document;
    d.writeln('<STYLE TYPE="text/css">#' + id + ' {');
	if (absolute) d.write('position:absolute;');
	else          d.write('position:relative;');
    if (left)   d.write('left:'  + left  + ';');
    if (top)    d.write('top:'   + top   + ';');
    if (width)  d.write('width:' + width + ';');
	if (height) d.write('height:' + height + ';');
	if (zIndex) d.write('z-index:' + zIndex + ';');
    d.writeln('}</STYLE>');
}
if (isNS) {
    NewDiv.prototype.output             = function()      { var d = this.window.document;d.writeln('<DIV ID="' + this.id + '">');d.writeln(this.body);d.writeln("</DIV>");this.layer = d[this.id];}
    NewDiv.prototype.moveTo             = function(x,y)   { this.layer.moveTo(x,y); }
    NewDiv.prototype.moveBy             = function(x,y)   { this.layer.moveBy(x,y); }
    NewDiv.prototype.show               = function()      { this.layer.visibility = "show"; }
    NewDiv.prototype.hide               = function()      { this.layer.visibility = "hide"; }
    NewDiv.prototype.setZ               = function(z)     { this.layer.zIndex = z; }
    NewDiv.prototype.setBgColor         = function(color) { this.layer.bgColor = color; }
    NewDiv.prototype.setBgImage         = function(image) { this.layer.background.src = image;}
    NewDiv.prototype.getX               = function() { return this.layer.left; }
    NewDiv.prototype.getY               = function() { return this.layer.top; } //was right .. ??
    NewDiv.prototype.getWidth           = function() { return this.layer.width; }
    NewDiv.prototype.getHeight          = function() { return this.layer.height; }
    NewDiv.prototype.getZ               = function() { return this.layer.zIndex; }
    NewDiv.prototype.isVisible          = function() { return this.layer.visibility == "show"; }
    NewDiv.prototype.setBody            = function() { for(var i = 0; i < arguments.length; i++) this.layer.document.writeln(arguments[i]);this.layer.document.close();}
    NewDiv.prototype.addEventHandler    = function(eventname, handler) {this.layer.captureEvents(NewDiv._eventmasks[eventname]); var newdivel = this;this.layer[eventname] = function(event) { return handler(newdivel, event.type, event.x, event.y, event.which, event.which,((event.modifiers & Event.SHIFT_MASK) != 0),((event.modifiers & Event.CTRL_MASK)  != 0),((event.modifiers & Event.ALT_MASK)   != 0));}}
    NewDiv.prototype.removeEventHandler = function(eventname)          {this.layer.releaseEvents(NewDiv._eventmasks[eventname]);delete this.layer[eventname];}
    NewDiv.prototype.centerX            = function() {this.layer.moveTo(Math.round((window.pageXOffset+document.width-100)/2),this.layer.top)}
    NewDiv._eventmasks                  = {onabort:Event.ABORT,onblur:Event.BLUR,onchange:Event.CHANGE,onclick:Event.CLICK,ondblclick:Event.DBLCLICK, ondragdrop:Event.DRAGDROP,onerror:Event.ERROR, onfocus:Event.FOCUS,onkeydown:Event.KEYDOWN,onkeypress:Event.KEYPRESS,onkeyup:Event.KEYUP,onload:Event.LOAD,onmousedown:Event.MOUSEDOWN,onmousemove:Event.MOUSEMOVE, onmouseout:Event.MOUSEOUT,onmouseover:Event.MOUSEOVER, onmouseup:Event.MOUSEUP,onmove:Event.MOVE,onreset:Event.RESET,onresize:Event.RESIZE,onselect:Event.SELECT,onsubmit:Event.SUBMIT,onunload:Event.UNLOAD};
}

if (isIE) {
    NewDiv.prototype.output             = function()                   { var d = this.window.document;d.writeln('<DIV ID="' + this.id + '">');d.writeln(this.body);d.writeln("</DIV>");this.element = d.all[this.id];this.style = this.element.style;}
    NewDiv.prototype.moveTo             = function(x,y)                { this.style.pixelLeft = x;this.style.pixelTop = y;}
    NewDiv.prototype.moveBy             = function(x,y)                { this.style.pixelLeft += x;this.style.pixelTop += y;}
    NewDiv.prototype.show               = function()                   { this.style.visibility = "visible"; }
    NewDiv.prototype.hide               = function()                   { this.style.visibility = "hidden"; }
    NewDiv.prototype.setZ               = function(z)                  { this.style.zIndex = z; }
    NewDiv.prototype.setBgColor         = function(color)              { this.style.backgroundColor = color; }
    NewDiv.prototype.setBgImage         = function(image)              { this.style.backgroundImage = image;}
    NewDiv.prototype.getX               = function()                   { return this.style.pixelLeft; }
    NewDiv.prototype.getY               = function()                   { return this.style.pixelRight; }
    NewDiv.prototype.getWidth           = function()                   { return this.style.width; }
    NewDiv.prototype.getHeight          = function()                   { return this.style.height; }
    NewDiv.prototype.getZ               = function()                   { return this.style.zIndex; }
    NewDiv.prototype.isVisible          = function()                   { return this.style.visibility == "visible"; }
    NewDiv.prototype.setBody            = function()                   { var body = "";for(var i = 0; i < arguments.length; i++) {body += arguments[i] + "\n";}this.element.innerHTML = body;}
    NewDiv.prototype.addEventHandler    = function(eventname, handler) { var NewDiv = this;this.element[eventname] = function() { var e = NewDiv.window.event;e.cancelBubble = true;return handler(NewDiv, e.type, e.x, e.y, e.button, e.keyCode, e.shiftKey, e.ctrlKey, e.altKey); }}
    NewDiv.prototype.removeEventHandler = function(eventname)          { delete this.element[eventname];}
	NewDiv.prototype.centerX            = function()                   { this.style.pixelLeft=Math.round((document.body.clientWidth+document.body.scrollLeft-300)/2)}
}

/*
 * The following was written by:
 *   Dario Guzik
 *      Spam unfriendly email address: dguzik AT bigfoot DOT com
 */
if (isNS6) {
    NewDiv.prototype.output             = function()                   { var d = this.window.document;d.writeln('<DIV ID="' + this.id + '">');d.writeln(this.body);d.writeln("</DIV>");this.element = d.getElementById(this.id);this.style = this.element.style;}
    NewDiv.prototype.moveTo             = function(x,y)                { this.style.pixelLeft = x;this.style.pixelTop = y;}
    NewDiv.prototype.moveBy             = function(x,y)                { this.style.pixelLeft += x;this.style.pixelTop += y;}
    NewDiv.prototype.show               = function()                   { this.style.visibility = "visible"; }
    NewDiv.prototype.hide               = function()                   { this.style.visibility = "hidden"; }
    NewDiv.prototype.setZ               = function(z)                  { this.style.zIndex = z; }
    NewDiv.prototype.setBgColor         = function(color)              { this.style.backgroundColor = color; }
    NewDiv.prototype.setBgImage         = function(image)              { this.style.backgroundImage = image;}
    NewDiv.prototype.getX               = function()                   { return this.style.pixelLeft; }
    NewDiv.prototype.getY               = function()                   { return this.style.pixelRight; }
    NewDiv.prototype.getWidth           = function()                   { return this.style.width; }
    NewDiv.prototype.getHeight          = function()                   { return this.style.height; }
    NewDiv.prototype.getZ               = function()                   { return this.style.zIndex; }
    NewDiv.prototype.isVisible          = function()                   { return this.style.visibility == "visible"; }
    NewDiv.prototype.setBody            = function()                   { var body = "";for(var i = 0; i < arguments.length; i++) {body += arguments[i] + "\n";}this.element.innerHTML = body;}
    NewDiv.prototype.addEventHandler    = function(eventname, handler) { var NewDiv = this;this.element[eventname] = function() { var e = NewDiv.window.event;e.cancelBubble = true;return handler(NewDiv, e.type, e.x, e.y, e.button, e.keyCode, e.shiftKey, e.ctrlKey, e.altKey); }}
    NewDiv.prototype.removeEventHandler = function(eventname)          { delete this.element[eventname];}
  NewDiv.prototype.centerX            = function()                   { this.style.pixelLeft=Math.round((document.body.clientWidth+document.body.scrollLeft-300)/2)}
}
