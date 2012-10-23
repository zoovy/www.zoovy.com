if(! window.jf_transaction_id) {
  var jf_transaction_id = "0";
}
if(! window.jf_merchant_order_num) {
  var jf_merchant_order_num = "0";
}
if(! window.jf_alt_checkout) {
  var jf_alt_checkout = "0";
}


var jf_rnd = Math.floor(Math.random()*999999999);
var jf_url ="https://www.jellyfish.com/pixel?rnd=" + jf_rnd + "&jftid=" + jf_transaction_id + "&jfoid=" + jf_merchant_order_num + "&jfmid=" + jf_merchant_id;

for(var jf_i=0; jf_i<jf_purchased_items.length; jf_i++) {
	var jf_mpi      = escape(jf_purchased_items[jf_i].mpi);
	var jf_price    = (jf_purchased_items[jf_i].price+"").replace(/,/g,'').replace(/\$/g,'');
	var jf_quantity = (jf_purchased_items[jf_i].quantity+"").replace(/,/g,'').replace(/\$/g,'');
	jf_url = jf_url + "&m["+jf_i+"]="+jf_mpi+"&p["+jf_i+"]="+jf_price+"&q["+jf_i+"]="+jf_quantity;
}

if(jf_alt_checkout != "1") {
    var jf_img=new Image(1,1);
    jf_img.src=jf_url;
} else {
    var jf_pixel_url = jf_url;
}