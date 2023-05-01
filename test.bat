@echo off

REM Change python whatever 
set pyexe=python34\python.exe

REM And now, run all the various tests we have
%pyexe% test_myutils.py