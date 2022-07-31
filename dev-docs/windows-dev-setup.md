## Introduction

The intention of mewbot is to make it possible for people to create various forms of chatbots with as little coding knowedge as possible (ideally none).
As such, it is vital that the framework be well tested on Windows.
This comes with some challenges when it comes to setting up a development environment.

If you run into any problems, we would be most grateful if you would append a summary of what went wrong and what fixed it to the end of this document.

Please back up your files before using any tools such as regedit.
These instructions do not guarantee you will have a working system at the end of this process! (Though you _probably_ will).

Remember to close all open terminals after making changes to Windows environment variables e.t.c.
No changes here should require a restart to take full effect, but it is often a useful first step to debugging a problem.

## Setting up a Windows 10 development environment

1) Install Python

If you have already done this, some of the following instructions might be different.
Uninstalling and reinstalling is probably not required, but can be a helpful debug step.

Mewbot currently targets python 3.9 and later.
Installation media should be obtained directly from [the python downloads page][1].
We are currently working with python 3.10 - though notes from anyone who wants to try and follow these instructions with python 3.11 or later would be very welcome.

During installation
* You want to be sure the "pip" tickbox is ticked - this will be used later to install the dependencies needed to run the mewbot linting scripts
* It's a bit more elegant if you select "Install for all users"
* Selecting "Add Python to environment variables" is a useful addition - but one you might want to avoid if you already have another version of python already installed. As this may cause confusion. In this case you probably want to install without this ticked and use the full path to your python executable in all that follows (once you have the venv setup, this should cease to be necessary).
* The default install location is somewhat buried in the file structure. I personally prefer to change it to something like "C:\Python310\" - but this is a taste thing. It shouldn't affect subsequent steps. However, keeping the path to the python executable short as it cuts down on typing and potential error.

2) Ensure python is on the path

You could work directly with the full path to the python executable, but this might be a little verbose.

To check if python is on the path open a command prompt - by typing "cmd" in the search or otherwise (this prompt need not be in administrator mode - in fact, this should never be needed with this instructions) and type "python".
Or the path to your python executable.

This should yield something like

```shell
Python 3.10.0 (tags/v3.10.0:b494f59, Oct  4 2021, 19:00:18) [MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Which should match the version of python you installed above.

If this did not work, you can add python to the path manually (optionally under a different name).

There are many different approaches to adding something to the path - which to use depends on your individual needs.

#### Adding the python root folder

This approach is probably the simplest. Use it if
* You don't already have another python on your path
* Adding the python folder won't screw things up because of name conflicts or other reasons

```
Start the System Control Panel - search "System" and it should be the top result.
Select the "Advanced System Settings" submeu.
Click the "Environment Variables" button.
Under "System Variables", select "Path", then click "Edit".
Click New, add your python folder to the Path, and you're done
(mine was "C:\Python310\" - but our will be where ever you've installed the executable)
```

(adapted from the instructions found [here][2])

3) Create your mewbot dev folder

I put mine at "C:\mewbot_dev" but really, do as you will.

4) Create a mewbot venv

venvs for project development tend to be a good idea.
If nothing else, it makes it less painful if you need to remove the environment entirely because something has gone wrong.

Put the venv wherever you like - I put mine in "C:\mewbot_dev\mewbot_venv" but, as has probably become apparent, I don't care about polluting the root of my C drive much at all.

Open a cmd prompt and create the venv with

```shell
python -m venv C:\mewbot_dev\mewbot_venv
```

(With the dst path where ever you want your venv to go).

#### OPTIONAL BUT RECOMMENDED - Using doskey to make shortcuts for activating the venv

This allows you to create shortcuts (and execute arbitrary code every time you open a termianl in windows).
We'll be using this to streamline the process of activating the `venv` for when you want to do development work with mewbot.

(adapted from [here][3])

```
Firstly, define a list of the alias you want to establish.
Then create a .bat file containing those commands.
Mine just contained, for the moment
   doskey activate_mewbot_venv=C:\mewbot_dev\mewbot_venv\Scripts\activate
Open regedit and navigate to "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Command Processor"
Create a new, string variable. Call it "AutoRun" - note the capitalisation - and value it with the absolute path to the .bat file you previously created.
(I put mine inside my python folder for convenience. But you could put yours anywhere really).
Close all open terminals.
Test funtion by opening a new cmd prompt and typing "activate_mewbot_venv" - the venv should activate, which should be reflected in the command prompt.
Add new commands to the .bat file freely.
```

If you want to stop the commands in this file being printed to the terminal every time it's run - i.e. every time the terminal is opened, you could do something like this

```shell
@echo off
doskey activate_mewbot_venv=C:\mewbot_dev\mewbot_venv\Scripts\activate
:END
```

which will suppress printing.

5) Get the code

You can install and configure git on a windows box pretty simply.
If you don't feel like messing around with keys for github auth, their command line tool is pretty good.
Likewise, if you want a GUI, Github desktop is pretty decent - hides most of the sophisticated features, but you can drop directly into the git command line if you need to.
And it handles authentication for you.

6) Activate your venv

The command to activate your venv can be found (assuming you've used the same paths as I have) at

```shell
C:\mewbot_dev\mewbot_venv\Scripts\activate
```

For convenience, I've already added the following command to the autorun script I created up above.

```shell
doskey activate_mewbot_venv=C:\mewbot_dev\mewbot_venv\Scripts\activate
```

This allows me to now, from where ever I am on the system, activate the venv with "activate_mewbot_venv" ... deactivation is left as an exercise to the reader.

Once your venv is activated, then your command prompt should become something like

```shell
(mewbot_venv) C:\mewbot_dev\mewbot_venv\Scripts>
```

(again, assuming you're using the same paths as I am)

Once you have your venv, it is advisable to check you're running off the executable you think you are.

Invoking the python interpreter and checking the executable path is usually a good idea - doing something like.

```shell
C:\Users\mewbot_demo_account>activate_mewbot_venv

(mewbot_venv) C:\Users\mewbot_demo_account>python
Python 3.10.0 (tags/v3.10.0:b494f59, Oct  4 2021, 19:00:18) [MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import sys
>>> sys.executable
'C:\\mewbot_dev\\mewbot_venv\\Scripts\\python.exe'
```

Which confirms the executable is where and what we expect.

NOTE - Once the venv is active, a call to `python` should always invoke the venv python interpreter - no matter what your environment was before the venv was activated.

If you have another version of python on your path and, as a consequence, you were using the full path to the python instance you wanted to use for mewbot dev, this should no longer be necessary.

7) Install the project dependencies

cd into the dir where you cloned the mewbot repo and execute

```shell
python -m pip install -r requirements-dev.txt
```

NOTE - Administrator privileges should not be required for this - they would be if you were installing the packages globally - but, because of the venv they are not.

This will take some time.

8) Check the linters have properly installed

The linters should be properly installed and on the path - but it's a good idea to check.

To do so, run

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>black src
All done! ✨ 🍰 ✨
15 files left unchanged.
```

(the number of files will probably be different by the time you read this).

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>flake8 src
```

(which should produce no output)

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>mypy src
src\mewbot\ioconfigs\discord_io\output.py:6: error: Cannot find implementation or library stub for module named "mewbot.io"
src\mewbot\ioconfigs\discord_io\input.py:11: error: Cannot find implementation or library stub for module named "mewbot.io"
src\mewbot\ioconfigs\discord_io\input.py:11: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src\mewbot\ioconfigs\socket_input\input.py:8: error: Cannot find implementation or library stub for module named "mewbot.io"
src\mewbot\ioconfigs\post_input\input.py:21: error: Cannot find implementation or library stub for module named "mewbot.io"
Found 4 errors in 4 files (checked 15 source files)
```

(These errors are to be expected - mewbot is not currently installed in the venv - so the static analysis tools - which are using the venv's python.exe get confused.)
NOTE - The number of files checked should match the number of files which where checked by black.

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>pylint src
```

(This will probably throw a bunch of errors - we're just testing the venv for now).

9) Install mewbot in development mode

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>python setup.py develop
```

(`develop` instead of `install` means that the interpreter will use the files here instead of copying them elsewhere.
If you accidentally do `install` not `develop` ... may be best to delete the venv and start again).

10) Test an example actually works

It's a case of "bring your own token" - instructions as to how to generate tokens for each of the supported services are located elsewhere in this documentation.

Execute something like

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>python -m examples examples\discord_to_desktop_notification.yaml
```

with the paths replaced as apporpiate for your setup and the example replaced with the example you actually want to run (though the desktop notificaiton example is perfectly inoffensive).

11) Re-run linters

With mewbot actually installed, the linters should now actually all work.

Confirm it by running them against the `src` folder

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>black src
All done! ✨ 🍰 ✨
15 files left unchanged.
```

e.t.c.

12) Check you can run linters through the linting script

The previous tests have mostly to make sure that the linters are all installed, before running them as intended during dev.

To do this the venv path must be modified to include the root of the checked out source.
In my case

```shell
C:\mewbot_dev\mewbot
```

There are a number of ways to do this.

#### Use a .pth files

Probably the best way is to use a `.pth` file - these provide instructions to the python interpreter as to additional folders to include in its path.

A path file is just a text file with extension `.pth` which include folders you want added to the python path - one per line.

It must be placed on the path of the python interpreter your currently using. In this case, assuming you have the same paths as me, probably the best place to put it would be

```shell
C:\mewbot_dev\mewbot_venv\Lib\site-packages
```

Simple add a file named `mewbot.pth` here with the single line `C:\mewbot_dev\mewbot`. It's probably best to add it as a new file, instead of modifying one of the existing ones - as these are under system control and may be overwritten without warning.

#### Modify the venv activation script

This is probably the harder option, but is included for completeness.

In my case, the script could be found at

```shell
C:\mewbot_dev\mewbot_venv\Scripts\activate.bat
```

and looked like this

```shell
@echo off

rem This file is UTF-8 encoded, so we need to update the current code page while executing it
for /f "tokens=2 delims=:." %%a in ('"%SystemRoot%\System32\chcp.com"') do (
    set _OLD_CODEPAGE=%%a
)
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" 65001 > nul
)

set VIRTUAL_ENV=C:\mewbot_dev\mewbot_venv

if not defined PROMPT set PROMPT=$P$G

if defined _OLD_VIRTUAL_PROMPT set PROMPT=%_OLD_VIRTUAL_PROMPT%
if defined _OLD_VIRTUAL_PYTHONHOME set PYTHONHOME=%_OLD_VIRTUAL_PYTHONHOME%

set _OLD_VIRTUAL_PROMPT=%PROMPT%
set PROMPT=(mewbot_venv) %PROMPT%

if defined PYTHONHOME set _OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%
set PYTHONHOME=

if defined _OLD_VIRTUAL_PATH set PATH=%_OLD_VIRTUAL_PATH%
if not defined _OLD_VIRTUAL_PATH set _OLD_VIRTUAL_PATH=%PATH%

set PATH=%VIRTUAL_ENV%\Scripts;%PATH%
set VIRTUAL_ENV_PROMPT=(mewbot_venv) 

:END
if defined _OLD_CODEPAGE (
    "%SystemRoot%\System32\chcp.com" %_OLD_CODEPAGE% > nul
    set _OLD_CODEPAGE=
)

```

We need to modify the `PYTHONPATH` variables so statements such as
```python
from tools.common import Annotation, ToolChain
```

in `lint.py` will function.

Add a command such as

```shell
set PYTHONPATH=C:\mewbot_dev\mewbot;%PYTHONPATH%
```

to your `activate.bat` file - ideally somewhere between

```shell
@echo off
...
:END
```

so it won't be printed every time you activate the venv.
Save and close all open terminals.
Then open a new terminal, activate the venv, and check that `tools` can now be found by doing

```shell
(mewbot_venv) C:\Users\Adriann Ves Bloche>python
Python 3.10.0 (tags/v3.10.0:b494f59, Oct  4 2021, 19:00:18) [MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import tools
>>>
```

The primary disadvantage of this method is that it will be undone if the activation script is ever recreated.

13) Tests that the linting script is functioning correctly

Ww now need to actually check that the linting script will run.
Execute

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>python tools\lint.py
All done! ✨ 🍰 ✨
29 files left unchanged.
Success: no issues found in 29 source files
************* Module tests.test_core
tests\test_core.py:21:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:27:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:32:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:38:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:41:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:47:4: R0201: Method could be a function (no-self-use)
tests\test_core.py:51:4: R0201: Method could be a function (no-self-use)
************* Module tests.test_loader
tests\test_loader.py:23:4: R0201: Method could be a function (no-self-use)
tests\test_loader.py:29:4: R0201: Method could be a function (no-self-use)
tests\test_loader.py:40:4: R0201: Method could be a function (no-self-use)
tests\test_loader.py:50:4: R0201: Method could be a function (no-self-use)

-----------------------------------
Your code has been rated at 9.91/10
```

Less than ideal, but looks functional (and, hopefully, should be fixed by the time you read this.

14) Run the tests

With linting done, time to check that the tests all pass.

```shell
(mewbot_venv) C:\mewbot_dev\mewbot>python tools\test.py
================================================= test session starts =================================================
platform win32 -- Python 3.10.0, pytest-7.1.2, pluggy-1.0.0
rootdir: C:\mewbot_dev\mewbot
plugins: cov-3.0.0
collected 20 items

tests\test_core.py .......                                                                                       [ 35%]
tests\test_io_http_socket.py ..                                                                                  [ 45%]
tests\test_loader.py ...........                                                                                 [100%]

---------- coverage: platform win32, python 3.10.0-final-0 -----------
Name                                          Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------------------------------
examples\__init__.py                              0      0      0      0   100%
examples\__main__.py                             10     10      6      0     0%   3-17
examples\discord_to_desktop_notification.py      48     48      8      0     0%   5-86
examples\trivial_discord_bot.py                  46     46      8      0     0%   5-83
examples\yaml_bot.py                             13     13      2      0     0%   3-29
src\mewbot\__init__.py                            0      0      0      0   100%
src\mewbot\api\__init__.py                        0      0      0      0   100%
src\mewbot\api\registry.py                       66     12     34      9    77%   28, 33, 44, 57, 59->52, 76, 79, 84, 89, 109-112, 118
src\mewbot\api\v1.py                            137     44     50      4    63%   38-59, 63, 68, 81, 85, 92, 95, 106, 130, 134, 142, 146, 154, 159, 167, 170-173, 177, 205, 212, 221, 226, 229-230, 233-242, 245-247
src\mewbot\bot.py                               127     85     46      0    27%   40-45, 54, 57-63, 66-72, 75-82, 102-109, 112-148, 160-169, 172-185, 188-197, 200-209
src\mewbot\config.py                             12      0      4      0   100%
src\mewbot\core.py                               87     17     24      0    83%   29, 32, 44, 47, 71, 74, 81, 84, 91, 95, 98, 101, 109, 112, 115, 118, 142
src\mewbot\data.py                               24      0      8      0   100%
src\mewbot\demo.py                               33      8      6      0    79%   11, 17, 21, 24, 27, 41, 55, 58
src\mewbot\io\__init__.py                         0      0      0      0   100%
src\mewbot\io\desktop_notification.py           114    114     36      0     0%   3-256
src\mewbot\io\discord.py                         65     65     20      0     0%   3-131
src\mewbot\io\http.py                            36     15      8      0    61%   38, 49-55, 65, 72-80, 86-91
src\mewbot\io\socket.py                          77     34     16      0    53%   50, 53-56, 59, 76-81, 89, 92-101, 106-130
src\mewbot\loader.py                             68      9     24      5    85%   30-31, 49, 56, 82-86, 118, 156
-----------------------------------------------------------------------------------------
TOTAL                                           963    520    300     18    45%
Coverage HTML written to dir .coverage_html

Required test coverage of 40.0% reached. Total coverage: 44.73%

================================================= 20 passed in 3.80s ==================================================

(mewbot_venv) C:\mewbot_dev\mewbot>
```
15) Celebrate!

You should now have a functional mewbot dev environment.

16) Proceed with dev

We look forward to seeing what you do!

Before any pushes, please run `tools\lint.py` and `tools\test.py`. 


[1]: https://www.python.org/downloads/ "Python downloads"
[2]: https://www.itprotoday.com/windows-server/how-can-i-add-new-folder-my-system-path "Windows Path"
[3]: https://stackoverflow.com/questions/20530996/aliases-in-windows-command-prompt "Running commands every time the cmd prompt is opened"

