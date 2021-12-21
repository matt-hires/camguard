===================================
camguard - home surveillance system
===================================

| |github license| |_| |PyPI Python| |_| |Travis CI| |_| |RTD|
| |Deepsource Resolved Issues| |_| |Deepsource Active Issues|

.. |_| unicode:: 0xA0 

.. |github license| image:: https://img.shields.io/github/license/matt-hires/camguard?logo=Open%20Source%20Initiative&logoColor=0F0 
    :target: https://github.com/matt-hires/camguard/blob/main/LICENSE
    :alt: Project License on GitHub
.. |PyPI Python| image:: https://img.shields.io/pypi/pyversions/camguard?logo=python&logoColor=yellow
    :target: https://pypi.org/project/camguard 
    :alt: PyPI Package
.. |Travis CI| image:: https://img.shields.io/travis/com/matt-hires/camguard?logo=travis 
    :target: https://app.travis-ci.com/matt-hires/camguard
    :alt: Travis CI
.. |RTD| image:: https://img.shields.io/readthedocs/camguard?logo=readthedocs&logoColor=%238CA1AF
    :target: https://camguard.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. |Deepsource Resolved Issues| image:: https://deepsource.io/gh/matt-hires/camguard.svg/?label=resolved+issues&show_trend=true&token=LXkH6P36GjNCig8w940UG5Q4
  :target: https://deepsource.io/gh/matt-hires/camguard/?ref=repository-badge
  :alt: Deepsource Resolved Issues
.. |Deepsource Active Issues| image:: https://deepsource.io/gh/matt-hires/camguard.svg/?label=active+issues&show_trend=true&token=LXkH6P36GjNCig8w940UG5Q4
  :target: https://deepsource.io/gh/matt-hires/camguard/?ref=repository-badge
  :alt: Deepsource Active Issues

``camguard`` offers a home surveillance system for |raspi|_ while using a connected motion sensor and camera. It can be used as a cli-application as well as a unix daemon.

Full documentation is available on |camguard rtd|_

Requirements
============
You need **at least Python 3.7** to use this module.

Supported Platforms
-------------------
``camguard`` has been tested on **Raspberry Pi 3 Model B Plus Rev 1.3** for the Platform **Raspbian GNU/Linux 10 (buster)** with Kernel **5.10.60-v7+ armv7l**

``camguard`` *probably* can run on platforms not listed above,
but I cannot provide support for unlisted platforms.

Equipment
---------
The following additional hardware is required:
    - Joy-IT SBC-PIR BIS0001 Motion Sensor
    - Raspi-Cam Electreeks E-RS015
    - Raspi-Cam Case Electreeks Komplex I
    - 1m/2m Electreeks FFC Ribbon-Cable AWM 20624 80C 60V VW-1
    - Red notification LED with current limiting resistor (optional)
    - Raspi T-Cobbler (optional)
  
⚠️ Be careful not to use a HC-SR501 Motion Sensor, it can be really hard to adjust the re-triggering on this sensor. Make your life easy by using SBC-PIR BIS0001 or similar.

Raspi-Setup
-----------
For the complete setup guide please see |camguard rtd|_

Installation and Usage
======================

For installation on Raspberry Pi there are two options:

1. Installation with ``pip``::

    $ pip install camguard[raspi]

2. Installation with available ``Makefile``::

    $ make install

Usage
-----
``camguard`` can be used via cli or unix daemon, started by the available init system. 

All available cli flags can be shown with ::

    $ camguard --help

Example usage with unix daemon and systemd user unit ``~/.config/systemd/user/camguard.service``
    
.. code-block:: cfg

    [Unit]
    Description=Camguard Test-Service

    [Service]
    Type=simple
    ExecStart=python -u -m camguard $HOME/.config/camguard/settings.yaml --daemonize
    TimeoutStopSec=3

    [Install]
    WantedBy=multi-user.target

``--daemonize`` is used here without the ``--detach`` due to the usage with systemd. ``camguard`` can also be used **without** the init system by combining both flags.

Project details
===============

* Project home: https://github.com/matt-hires/camguard
* Report bugs at:  https://github.com/matt-hires/camguard/issues
* Git clone: https://github.com/matt-hires/camguard.git
* Documentation: http://camguard.readthedocs.io/

Building
========

This project comes with a GNU-Make ``Makefile`` which can be used for building and installation. Help for the available targets can be shown with::

    $ make help

Developing
==========

For local development it is not possible to use the same dependencies as on the raspi installation, therefore camguard offers different installation environments:

- **dev** - contains all necessary dependencies for local development and debugging
- **raspi** - includes all necessary dependencies for installation on a raspberrypi
- **debug** - only includes (remote-)debug dependencies which can be combined with the raspi environment (the dev env already includes this)

Installing an environment can either be done directly via ``pip`` \.\.\. ::

    # install for local dev
    $ pip install -e .[dev]

    # install for raspi with remote debugging
    $ pip install -e .[raspi,debug]

\.\.\. or via ``Makefile``::

    # clean + check + install + docs-html
    $ make all

    # raspi + install-systemd + raspi-settings 
    $ make install
    
    # raspi with debugging + install-systemd + raspi-settings
    $ make install-debug

    # development + dummy-settings
    $ make install-dev

The ``Makefile`` also installs a fully functioning user systemd-unit with some default settings as well.

Sync changes to remote Raspberry Pi
-----------------------------------

| For syncing changes to a remote raspberry pi the script `sync_watch.sh` can be used. 
| It requires usage of the following tools:

* `inotifywait` - a cli file watcher
* `rsync` - for syncing changes to remote pi
* `ssh` - for network file transfers

Adaption to host and sync directory can be done via the variables `remote_host` and `remote_dir` in the script, as well as additional excludes for the watcher and rsync:

.. code-block:: bash
    :name: sync-watch
    :caption: sync_watch.sh

    # change to your raspi hostname and sync directory
    remote_host="pi@raspberrycam"
    remote_dir="/home/pi/pydev/camguard"

    # sync excludes
    rsync_excludes=("--exclude=venv/" "--exclude=*.log" "--exclude=**/__pycache__"
        "--exclude=.tox/" "--exclude=.git/" "--exclude=.python-version"
        "--exclude=pip-wheel-metadata/" "--exclude=src/*.egg-info/" "--exclude=.vscode/"
        "--exclude=**/*.tmp" "--exclude=settings.yaml" "--exclude=.coverage" "--exclude=htmlcov/" 
        "--exclude=docs/_build" "--exclude=dist/")

    # watcher excludes
    inotify_excludes="(\.idea)|(.*~)|(venv)|(\.python-version)|\
    (__pycache__)|(\.git)|(\.vscode)|(\.tox)|(camguard-.*)|\
    (.*\.egg-info)|(settings\.yaml)|(\.coverage)|(htmlcov)|(docs)|(dist)"

Static Code Analysis
--------------------

This project performs static code analysis check with |deepsource|_.

.. _deepsource: https://deepsource.io/gh/matt-hires/camguard/
.. |deepsource| replace:: deepsource


Documentation
-------------

Builds html documentation with sphinx, by using makefile goal::

    $ make docs-html

License
=======

``camguard`` is released under the GNU General Public License v3.0

.. _`raspi`: https://www.raspberrypi.org/
.. |raspi| replace:: **Raspberry Pi** 
.. _`camguard rtd`: https://camguard.readthedocs.io
.. |camguard rtd| replace:: **camguard.readthedocs.io**
