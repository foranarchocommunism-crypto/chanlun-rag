@echo off
setlocal
if exist "%~dp0runtime\node.exe" (
  "%~dp0runtime\node.exe" "%~dp0bin\chan-kg-mcp.mjs" %*
) else (
  node "%~dp0bin\chan-kg-mcp.mjs" %*
)
