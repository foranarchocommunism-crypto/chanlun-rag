@echo off
setlocal
if exist "%~dp0runtime\node.exe" (
  "%~dp0runtime\node.exe" "%~dp0bin\chan-kg.mjs" %*
) else (
  node "%~dp0bin\chan-kg.mjs" %*
)
