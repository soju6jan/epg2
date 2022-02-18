#!/bin/sh
export LANG=en_US.utf8
PLUGIN_HOME=$1
cd $PLUGIN_HOME && 
git --git-dir=$PLUGIN_HOME/.git reset --hard HEAD && 
git --git-dir=$PLUGIN_HOME/.git pull
