TODO for camguard cli/daemon
############################

Wishlist
--------

Bugs
----
* Gdrive refresh token not working 

Features
--------
* Recording/Upload subfolder {capture}_{count}

* gdrive persist queue
    - via file system (create directory to_upload / uploaded) ?
    - via a persisted queue file

* email notification
    - refactor using gen-based coroutine pipes for motion handling (pre-requisite) ✔️ 

* deactivation when specific mac addr is present in network
    - Sample code for searching:

    .. code-block:: 

        sudo nmap -sn 192.168.1.0/24 --dns-server 192.168.1.1 | grep "MAC-ADDR"

=======
PENDING
=======

====
DONE
====
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
