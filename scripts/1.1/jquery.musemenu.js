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
(function(b){b.fn.museMenu=function(){return this.each(function(){var c=b(this),a="absolute",d,f,g,i,h;if(c.css("position")=="fixed"){var a="fixed",j=Muse.Utils.getStyleSheetRuleById(Muse.Utils.getPageStyleSheet(),this.id);d=Muse.Utils.getRuleProperty(j,"top");f=Muse.Utils.getRuleProperty(j,"left");g=Muse.Utils.getRuleProperty(j,"right");i=Muse.Utils.getRuleProperty(j,"bottom");h=parseInt(c.css("margin-left"))}else for(j=c.parent();j.length>0&&j.attr("id")!="page";){if(j.css("position")=="fixed"){var a=
"fixed",m=j.offset(),l=c.offset(),k=Muse.Utils.getStyleSheetRuleById(Muse.Utils.getPageStyleSheet(),j.attr("id")),n=Muse.Utils.getRuleProperty(k,"top"),o=Muse.Utils.getRuleProperty(k,"left"),p=Muse.Utils.getRuleProperty(k,"right"),k=Muse.Utils.getRuleProperty(k,"bottom");d=n&&n!="auto"?parseInt(n)+(l.top-m.top):n;f=o&&o!="auto"&&o.indexOf("%")==-1?parseInt(o)+(l.left-m.left):o;g=p&&p!="auto"&&p.indexOf("%")==-1?parseInt(p)+(m.left+j.width())-(l.left+c.width()):p;i=k&&k!="auto"?parseInt(k)+(m.top+
j.height())-(l.top+c.height()):k;h=parseInt(j.css("margin-left"))+(o&&o.indexOf("%")!=-1?l.left-m.left:0);break}j=j.parent()}var q=b(),u=!1,s=c.find(".MenuItemContainer"),j=c.find(".MenuItem"),m=c.find(".SubMenu").add(j),z;m.on("mouseover",function(){u=!0});m.on("mouseleave",function(){u=!1;setTimeout(function(){u===!1&&(s.each(function(){b(this).data("hideSubmenu")()}),q=b())},300)});s.on("mouseleave",function(a){var d=b(a.target),c=d.closest(".SubMenu");z&&clearTimeout(z);c.length>0&&(z=setTimeout(function(){c.find(".MenuItemContainer").each(function(){b(this).data("hideSubmenu")()});
q=d.closest(".MenuItemContainer").data("$parentMenuItemContainer")},300))});s.on("mouseenter",function(){clearTimeout(z)});j.each(function(){var j=b(this),k=j.siblings(".SubMenu"),l=j.closest(".MenuItemContainer"),m=l.parentsUntil(".MenuBar").filter(".MenuItemContainer").length===0,n;if(m&&k.length>0){var o=b("<div style='position:"+a+"' class='MenuBar popup_element'></div>").hide().appendTo("body");k.show();n=k.position().top;k.hide()}l.data("$parentMenuItemContainer",l.parent().closest(".MenuItemContainer")).data("showSubmenuOnly",
function(){if(m&&k.length>0)if(a!="fixed"){var b=l.offset();o.appendTo("body").css({left:b.left,top:b.top}).append(k).show()}else{var b=l.position(),j=0,p=0;g&&g!="auto"&&(j=c.outerWidth()-b.left);i&&i!="auto"&&(p=n);o.appendTo("body").css({left:f,top:d,right:g,bottom:i,marginLeft:h+b.left,marginRight:j,marginTop:b.top,marginBottom:p}).append(k).show()}k.show();k.find(".SubMenu").hide()}).data("hideSubmenu",function(){k.hide()}).data("isDescendentOf",function(a){for(var b=l.data("$parentMenuItemContainer");b.length>
0;){if(a.index(b)>=0)return!0;b=b.data("$parentMenuItemContainer")}return!1});var p=function(){var a=q;a.length==0?l.data("showSubmenuOnly")():l.data("$parentMenuItemContainer").index(a)>=0?l.data("showSubmenuOnly")():l.siblings().index(a)>=0?(a.data("hideSubmenu")(),l.data("showSubmenuOnly")()):a.data("isDescendentOf")(l)?l.data("showSubmenuOnly")():a.data("isDescendentOf")(l.siblings(".MenuItemContainer"))?(l.siblings(".MenuItemContainer").each(function(){b(this).data("hideSubmenu")()}),l.data("showSubmenuOnly")()):
a.get(0)==l.get(0)&&l.data("showSubmenuOnly")();q=l},s=null;j.on("mouseenter",function(){j.data("mouseEntered",!0);s=setTimeout(function(){p()},200);j.one("mouseleave",function(){clearTimeout(s);j.data("mouseEntered",!1)})});k.length&&(j.attr("aria-haspopup",!0),Muse.Browser.Features.Touch&&(j.click(function(){return k.is(":visible")}),b(document.documentElement).on(Muse.Browser.Features.Touch.End,Muse.Browser.Features.Touch.Listener(function(a){!k.is(":visible")&&b(a.target).closest(l).length>0?
(a.stopPropagation(),Muse.Utils.redirectCancelled=!0,setTimeout(function(){Muse.Utils.redirectCancelled=!1},16),j.data("mouseEntered")&&setTimeout(function(){l.data("showSubmenuOnly")()},200)):k.is(":visible")&&b(a.target).closest(k).length==0&&b(a.target).closest(l).length==0&&l.data("hideSubmenu")()}))))});j.filter(".MuseMenuActive").each(function(){for(var a=b(this).closest(".MenuItemContainer").data("$parentMenuItemContainer");a&&a.length>0;)a.children(".MenuItem").addClass("MuseMenuActive"),
a=a.data("$parentMenuItemContainer")})})}})(jQuery);
