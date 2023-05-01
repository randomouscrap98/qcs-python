@echo off

REM Change python whatever 
set pyexe=python34\python.exe

REM The list of packages this thing requires (maybe?)
set packages=requests colorama==0.4.1 websocket-client toml readchar

REM Actually install the packages... maybe?
%pyexe% -m pip install %packages%