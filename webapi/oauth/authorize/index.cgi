#!/usr/bin/perl

#Parameters
#client_id
#    Required string - The client ID you received from GitHub when you registered.
#redirect_uri
#    Optional string - URL in your app where users will be sent after authorization. See details below about redirect urls.
#scope
#    Optional string - Comma separated list of scopes.
#state
#    Optional string - An unguessable random string. It is used to protect against cross-site request forgery attacks. 
#


#print "Location: /webapi/oauth/login?\n\n";
print "Content-type: text/html\n\n";
print qq~
<html>
<form action="/webapi/oauth/authorize/index.cgi">

Login: <input type="textbox" name="login">
Password: <input type="textbox" name="password">
</form>
</html>
~;

