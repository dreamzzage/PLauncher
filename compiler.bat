@echo off
title Building PLauncher EXE...
echo ----------------------------------------
echo   Packaging opener.py into PLauncher.exe
echo ----------------------------------------

REM Use Python 3.12 explicitly if installed
set PYTHON=python

REM Clean previous build
echo Cleaning old build folders...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del PLauncher.spec 2>nul

echo.
echo Running PyInstaller...
%PYTHON% -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "PLauncher" ^
    opener.py

echo.
echo ----------------------------------------
echo   Build complete!
echo   EXE located in: dist\PLauncher.exe
echo ----------------------------------------
pause
