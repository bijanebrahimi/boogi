# What's Boogi?

Boogi is a light-weight feed reader written using python and (Py)Qt5. 

# Why Boogi?

`boogi` is not a name. it's more of a sound. i make `boogi` sound to make my niece laugh and this was the only name
came to mind when i started this project.

# Features

* Simple and light-weighted
* Full Article reading using Readability! (see screenshot no.2)
* Fast search

# Install

Sorry, right now there's no descent way to install Boogi. i should find some time to create a setuptool script very 
soon. 
but here's the manual instruction:

        $ git clone github.com:bijanebrahimi/boogi.git
        $ cd boogi
        $ pip install -r requirements

but beware there's PyQt5 as package dependency which can not be installed from pip easily (AFAIK). you need to install 
it as well from your system package manager.

        # DEBIAN/UBUNTU based distros
        # apt-get install python-pyqt5
        
        # ArchLinux
        # pacman -S python-pyqt5

Note: if you're using virtual environments, you should install pyqt5 in your virtual environment as well.

# Run

        $ cd boogi
        $ python run.py

# Screenshots

![Screenshot 1](https://bijanebrahimi.github.io/boogi/screenshots/screenshot_01.png)

![Screenshot 2](https://bijanebrahimi.github.io/boogi/screenshots/screenshot_02.png)

![Screenshot 3](https://bijanebrahimi.github.io/boogi/screenshots/screenshot_03.png)


# To-Dos

* code clean-ups
* and maybe some features to make us laugh ;)

# ChangeLog

* ver 0.2
    * added `Full Article` reading in app using readability 

