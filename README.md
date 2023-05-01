# qcs-python
A very basic python frontend for qcs, written for old machines

## What this is for / assumptions
- This is an extremely basic Python frontend meant to connect to a contentapi instance for chatting only. No other functionality from contentapi is preserved
  (such as creating rooms, managing permissions, avatars, etc)
- This is meant to work on python 3.4 in order to satisfy user requirements for "must run on Windows XP"
- This was developed on **Windows 11** targeting a local copy of **Python 3.4.4**
- I am unable to use **curses** as part of the requirements. This influenced the limited design
- I am not a Python nor a Windows developer. If the bat files or python is garbage, I don't care (sorry!)

## How to start
Because of the unique requirements given to me, this isn't setup like a normal python repository.
- You need to manually download the required pip packages, which are listed in `setup.bat`
- This was not setup to run with a virtual environment (but you're free to change that)
- Run `main.py` for the whole thing. `run.bat` is for me, the developer, there's nothing you need from there

The list of required pip packages is listed in `setup.bat`. If you're on windows, feel free to run that yourself, just know that the default is to use a 
local python 3.4 installation in a specific folder; you'll need to change that. Furthermore, we don't specify versions for most of these, so we assume
"any version" will work (even though I'm aware that these APIs change). 

