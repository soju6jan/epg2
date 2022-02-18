#!/bin/sh
export LANG=en_US.utf8
NowDate=$(date +%Y%m%d)-$(date +%H%M)
PLUGIN_HOME=$1
cd PLUGIN_HOME && 
git add $PLUGIN_HOME/file/epg2_data.db && 
git add $PLUGIN_HOME/file/xmltv_all2.xml
git commit -m $NowDate && 
git push