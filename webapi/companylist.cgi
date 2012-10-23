#!/bin/sh

echo Content-type: text/plain
echo
cat /httpd/static/channellist

exit

PATH="/httpd/zoovy/templates";

function dolist
{
  RSTR="";
  PATH=$1;
  shift;
  while [ $# -gt 0 ] ; do
     if [ -f "$PATH/$1" ] ; then
        RSTR=$RSTR"$1:0"
        WASFILE="1"
     else
        WASFILE="0"
     fi

     shift
     if [ "$WASFILE" = "1" -a $# -gt 0 ] ; then
        RSTR=$RSTR","
     fi
  done
  echo $RSTR
}

function parse
{
 while [ $# -gt 0 ] ; do
#   echo $1;
   if [ -d "$1" ] ; then
      TPATH=`echo $1 | /usr/bin/cut -b 24-255`
      RESULT=`/bin/ls $1`
      echo "/"$TPATH"{"`dolist $1 $RESULT`"}"
   fi
   shift;
 done
}

parse `/usr/bin/find $PATH`