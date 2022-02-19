SET PLUGIN_HOME=%1
git --git-dir=%PLUGIN_HOME%\.git reset --hard HEAD
git --git-dir=%PLUGIN_HOME%\.git pull
