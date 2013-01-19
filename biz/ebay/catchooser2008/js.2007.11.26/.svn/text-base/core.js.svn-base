$(function() {
//  setLinkHandlers();
  $("#loading").hide();
  $("#loading").ajaxStart(function(){
    $(this).show();
  });
  $("#loading").ajaxStop(function(){
    $(this).hide();
  });
});

var ajaxFormOptions = {
  target: '#body-inner',
  success: setLinkHandlers
};

function setLinkHandlers() {
  if (!$.browser.msie) {  
  $('a.category').click(function(event) {
    $('div#body-inner').load($(this).attr('href'), setLinkHandlers);
    event.preventDefault();
  });
  $('a.describe1').click(function(event) {
    $('div#body-inner').load($(this).attr('href'), setLinkHandlers);
    event.preventDefault();
  });
  $('form#sp-form').ajaxForm(ajaxFormOptions);
  $('form#pf-form').ajaxForm(ajaxFormOptions);
  $('form#suggest-form').ajaxForm(ajaxFormOptions);
  $('form#login-form').ajaxForm(ajaxFormOptions);
  }
};
