@echo off
call "%~dp0release\chan-kg-agent-0.4.0-windows-x64\verify.cmd" %*
exit /b %errorlevel%
