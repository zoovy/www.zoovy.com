/*
 ADOBE CONFIDENTIAL
 ___________________

 Copyright 2011 Adobe Systems Incorporated
 All Rights Reserved.

 NOTICE:  All information contained herein is, and remains
 the property of Adobe Systems Incorporated and its suppliers,
 if any.  The intellectual and technical concepts contained
 herein are proprietary to Adobe Systems Incorporated and its
 suppliers and may be covered by U.S. and Foreign Patents,
 patents in process, and are protected by trade secret or copyright law.
 Dissemination of this information or reproduction of this material
 is strictly forbidden unless prior written permission is obtained
 from Adobe Systems Incorporated.
*/
(function(b){b.fn.museOverlay=function(c){var a=b.extend({autoOpen:!0,offsetLeft:0,offsetTop:0,$overlaySlice:b(),$overlayWedge:b(),duration:300,overlayExtraWidth:0,overlayExtraHeight:0},c);return this.each(function(){var d=b(this).data("museOverlay");if(d&&d[c]!==void 0)return d[c].apply(this,Array.prototype.slice.call(arguments,1));var f=b("<div></div>").appendTo("body").css({position:"absolute",top:0,left:0,zIndex:100001}).hide(),g=b("<div></div>").append(a.$overlaySlice).appendTo(f).css({position:"absolute",
top:0,left:0}),h=b(this).css({position:"absolute",left:0,top:0}).appendTo(f),i=b(window),j,k,m=null,l={isOpen:!1,open:function(){if(!l.isOpen)j=i.width(),k=i.height(),l.positionContent(j,k),f.show(),g.bind("click",l.close),g.css({opacity:0}).stop(!0),h.css({opacity:0}).stop(!0),g.bind("click",l.close).animate({opacity:0.99},{queue:!1,duration:a.duration,complete:function(){g.css({opacity:""});h.animate({opacity:1},{queue:!1,duration:a.duration,complete:function(){h.css({opacity:""})}})}}),b(document).bind("keydown",
l.onKeyDown),l.doLayout(),l.isOpen=!0,i.bind("resize",l.onWindowResize)},close:function(){b(".Container",h).each(function(){Muse.Utils.detachIframesAndObjectsToPauseMedia(b(this))});g.unbind("click",l.close);i.unbind("resize",l.onWindowResize);b(document).unbind("keydown",l.onKeyDown);if(a.onClose)a.onClose();g.css({opacity:0.99}).stop(!0);h.css({opacity:0.99}).stop(!0);h.animate({opacity:0},{queue:!1,duration:a.duration,complete:function(){g.animate({opacity:0},{queue:!1,duration:a.duration,complete:function(){f.hide();
h.css({opacity:""});g.css({opacity:""})}})}});l.isOpen=!1},onKeyDown:function(a){a.keyCode===27&&l.close()},onWindowResize:function(){var a=i.width(),b=i.height();(j!=a||k!=b)&&m==null&&(m=setTimeout(function(){j=i.width();k=i.height();l.positionContent(j,k);l.doLayout();m=null},10))},doLayout:function(){f.css({width:0,height:0});a.$overlayWedge.css({width:0,height:0});var d=b(document),c=d.width(),d=d.height(),g=document.documentElement||document.body;g.clientWidth!=g.offsetWidth&&(c=g.scrollWidth-
1);g.clientHeight!=g.offsetHeight&&(d=g.scrollHeight-1);f.css({width:c,height:d});a.$overlayWedge.css({width:c-a.overlayExtraWidth,height:d-a.overlayExtraHeight})},positionContent:function(b,d){var c=i.scrollLeft()+Math.max(0,b/2+a.offsetLeft),f=i.scrollTop()+Math.max(0,d/2+a.offsetTop);h.css({top:f,left:c})}};h.data("museOverlay",l);a.autoShow&&l.open()})}})(jQuery);
