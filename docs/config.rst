=============
Configuration
=============

Configuration for ``camguard`` is done in a *yaml*-File with a configurable path, which will be set to ``$HOME/.config/camguard/settings.yaml`` by default. The parent directory path can be changed with the cli flag ``-c CONFIG_PATH`` (see ``camguard --help`` for further information).

When installing ``camguard`` by using the available ``Makefile``, a default configuration for Raspberry Pi is automatically copied to the default path.

Settings
========

Components
----------
``camguard`` uses component based settings where each of this components can be switch on, off or set into a dummy mode for testing, without using Raspberry Pi specific dependencies.

.. code:: yaml

    components:
        - motion_detector
        - motion_handler
        - file_storage
        - mail_client

Motion detector (``motion_detector``)
`````````````````````````````````````
| A motion detector which calls a given handler on motion.
| The following settings are available for ``motion_detector`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the detector component, available values are:
| Type: ``enum``

- ``raspi`` (default)
- ``dummy``

Implementation Settings
'''''''''''''''''''''''
The settings node of the selected implementation type, available values are:

- raspi_gpio_sensor
- dummy_gpio_sensor

Following settings are *only available for ``raspi_gpio_sensor``*.

Raspberry Pi GPIO-Pin Number (``gpio_pin_number``)
''''''''''''''''''''''''''''''''''''''''''''''''''
| *Required* General Purpose Input-Output (GPIO) pin number on Raspberry Pi where the motion sensor is connected.
| Type: ``integer``

Notification LED GPIO-Pin Number (``notification_led_gpio_pin_number``)
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
| GPIO-Pin number for *optional* notification LED, which will be activated when a motion is detected.
| Type: ``integer``

Queue Length (``queue_length``)
'''''''''''''''''''''''''''''''
| The length of the queue used to store values read from the motion sensor. If your motion sensor is particularly "twitchy" you may want to increase this value.
| Type: ``integer``
| Default: ``1`` (this effectively disables the queue)

Queue Threshold (``threshold``)
'''''''''''''''''''''''''''''''
| When the average of all values in the internal queue rises above this value, the sensor will be considered *active*.
| Type: ``float``
| Default: ``0.5`` (which means half of the queue has to be considered *active*)

Sample Rate (``sample_rate``)
'''''''''''''''''''''''''''''
| The number of values to read from the device (and append to the internal queue) per second. 
| Type: ``float``
| Default: ``10.0``

Example configuration for Raspberry Pi
''''''''''''''''''''''''''''''''''''''

.. code:: yaml

    motion_detector:
        implementation: raspi

        raspi_gpio_sensor:
            gpio_pin_number: 23
            notification_led_gpio_pin_number: 0 # default
            queue_length: 1 # default
            threshold: 0.5 # default
            sample_rate: 10.0 # default


Example configuration for Dummy usage
'''''''''''''''''''''''''''''''''''''

.. code:: yaml

    motion_detector:
        implementation: dummy

        dummy_gpio_sensor:
            # no value available

Motion handler (``motion_handler``)
```````````````````````````````````
| A component which handles motion detection, in the current implementation this is represented either by a Raspberry Pi- or Dummy-Camera. 
| The following settings are available for ``motion_handler`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the handler component, available values are:
| Type: ``enum``

- ``raspi`` (default)
- ``dummy``

Implementation Settings
'''''''''''''''''''''''
The settings node of the selected implementation type, available values are:

- raspi_cam
- dummy_cam

Following settings are the same for *both* ``dummy_cam`` *and* ``raspi_cam``.

Recording root folder path (``record_path``)
''''''''''''''''''''''''''''''''''''''''''''
| Root folder path where recorded files from the camera will be saved. Environment variables, as well as '~', will be expanded.
| Type: ``string``
| Default: ``'$HOME/.camguard/records'``

Record count (``record_count``)
'''''''''''''''''''''''''''''''
| Defines how many pictures will be taken per motion detection. 
| Type: ``integer``
| Default: ``15``

Record interval seconds (``record_interval_seconds``)
'''''''''''''''''''''''''''''''''''''''''''''''''''''
| Interval between each taken picture in seconds. 
| Type: ``float``
| Default: ``1.0``

Record file name format (``record_file_format``)
''''''''''''''''''''''''''''''''''''''''''''''''
| File name formatting for the recorded file. ``counter`` represents the current picture count, ``timestamp`` the current date-time. Both can be combined in a formatting template. 
| For further information about date-time formatting, see `Date-Time format`_.
| Type: ``string``
| Default: ``'{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg'``

.. _`Date-Time format`: https://docs.python.org/3/library/datetime.html?highlight=time%20format#datetime.datetime

Example configuration for Raspberry Pi
''''''''''''''''''''''''''''''''''''''

.. code:: yaml

    motion_handler:
        implementation: raspi

        raspi_cam:
            record_path: '$HOME/.camguard/records' # default
            record_count: 15 # default
            record_interval_seconds: 1.0 # default
            record_file_format: "{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg" # default


Example configuration for Dummy usage
'''''''''''''''''''''''''''''''''''''

.. code:: yaml

    motion_detector:
        implementation: dummy

        dummy_cam:
            record_path: '$HOME/.camguard/records' # default
            record_count: 5
            record_interval_seconds: 0.5
            record_file_format: "{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg" # default
