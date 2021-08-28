TODO for camguard cli/daemon
############################

Wishlist
--------

Bugs
----

Features
--------
* Write documentation 

* Recording/Upload subfolder {capture}_{count}

* gdrive persist queue
    - via file system (create directory to_upload / uploaded) ?
    - via a persisted queue file

* deactivation when specific mac addr is present in network
    - Sample code for searching:

    .. code-block:: 

        sudo nmap -sn 192.168.1.0/24 --dns-server 192.168.1.1 | grep "MAC-ADDR"

* email notification
    - make mail client optional

Refactoring
-----------
* FileStorage-Settings: Use implementation setting the same way as for motion detector. This is the same for the mail client

    .. code-block::

        implementation: dummy

=======
PENDING
=======

* Refactor settings - reuse a code refragment for getting settings and throwing a mandatory exception

====
DONE
====
* gdrive - google oauth
    - describe new settings
* motionsensor
    - settings for notification LED

* gdrive - google python api instead of pydrive2
  - enable gmail oauth, therefore remove pydrive2 and use google-api-python-client with oauth2client instead 
  - upgrade fixes bug with refresh token

* email notification
    - refactor using gen-based coroutine pipes for motion handling (pre-requisite) ✔️ 
    - implement first solution check️ ✔
    - write unit/integration tests (currently not necessary)

* general camguard-settings support
    - configurable cam-settings  
    - configurable settings file path (default $HOME/.config/camguard/settings.yaml)
    - rename GDriveDummyStorage -> DummyGDriveStorage

* Add makefiles for easy build
* test refactoring
    - test coverage

* gdrive daemon: remove control thread
* Implement a bridge to hide concrete handler/detector classes
    - this enables switching to a dummy implementation for testing without a raspi 
    - create concrete implementations with abstract factory
* gdrive queue
    - should be exectued async after record
* Configure camguard as a daemon
    - add makefiles for systemd installation
