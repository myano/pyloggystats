============
pyloggystats
============

This project creates a web page from logs obtained by loggy.py 
( http://inamidst.com/code/loggy.py ). It is also backwards compatible 
with the logs taken by eggdrop v1.6.19. 

I do not have any plans to have it be compatible with other logging formats
as I encourage people to use Sean B. Palmer's loggy.py script.

This was inspired by the pisg project.


Run
------

Run, ``./stats.py`` with the appropriate command line requirements. You can see
necessary arguments by running ``./stats.py --help``.

Please note, when specifying the channel the ``#`` needs to be escaped. Here is
an example of how to do this:

``./stats.py -u yano -c \#osu_osc -e txt -l /home/yano/yanovich.net/public/logs/``

Trouble / Help
--------------

pyloggystats is meant to be run with Python 2.7.x. Please make sure you are
running at least this version of Python. This script does not work in Python
3.x.

If you need help, please feel free to contact me.


Theming
-------

If you are not satisfied with the default colour scheme, you can change the
colours in the style.css folder. If you want to make your colour scheme
available to others to use please fork this project, commit the theme and
submit a pull request. Please place additional css files in the themes folder. 

To have the ``stats.py`` file pick up on your theme make sure you change or
rename your theme file to style.css and place it in this folder.


License
-------

This script is license under the GNU GPL v3.

The recipe.py was obtained from a blog of which I have lost the link for.
There wasn't a license attached with it and I'm releasing it under
my project which is license by the GNU GPL v3.
