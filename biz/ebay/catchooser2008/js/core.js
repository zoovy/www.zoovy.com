var cs_counter = 0;

$(function() {
//  setLinkHandlers();
  setCSLinkHandlers();
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

/* for add custom specific, remove custom specific links */
function setCSLinkHandlers() {
  $('a#add_custom_specific').unbind('click').click(function(event) {
    $(this).after('<div class="custom_specific_block"><p><input type="text" value="Detail Title" name="cs_name'+cs_counter+'" onFocus="if(this.value==\'Detail Title\')this.value=\'\'" onBlur="if(this.value==\'\')this.value=\'Detail Title\'" /><input type="text" value="Detail Value" name="cs_value'+cs_counter+'" onFocus="if(this.value==\'Detail Value\')this.value=\'\'" onBlur="if(this.value==\'\')this.value=\'Detail Value\'" /><a class="remove_cs" id="remove_cs'+cs_counter+'" href="javascript:void(0);">Remove</a></p></div>');
    $('a#remove_cs'+cs_counter).unbind('click').click(function(event) {
      $(this).parent().parent().remove();
      event.preventDefault();
    });
    cs_counter += 1;
    event.preventDefault();
  });
};
