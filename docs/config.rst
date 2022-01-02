=============
Configuration
=============

Configuration for ``camguard`` is done in a *yaml*-File with a configurable path, which will be set to ``$HOME/.config/camguard/settings.yaml`` by default. The parent directory path can be changed with the cli flag ``-c CONFIG_PATH`` (see :doc:`cli`).

When installing ``camguard`` by using the available ``Makefile``, a default configuration for Raspberry Pi is automatically copied to the default path.

Settings
========

For further explanation about component interaction please refer to :doc:`intro`.

Components
----------
``camguard`` uses component based settings where each of this components can be switch on, off or set into a dummy mode for testing, without using Raspberry Pi specific dependencies.

.. code-block:: yaml

    components:
        - motion_detector
        - motion_handler
        - file_storage
        - mail_client
        - network_device_detector

Motion detector (``motion_detector``)
`````````````````````````````````````
| A motion detector which calls a motion handler pipeline on detection.
| The following settings are available for ``motion_detector`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the motion detector component, available values are:
| Type: ``enum``
| Default: ``raspi``

- ``raspi``
- ``dummy``

Implementation Settings
'''''''''''''''''''''''
The settings node of the selected implementation type, available values are:

- raspi_gpio_sensor
- dummy_gpio_sensor

Following settings are *only* available for ``raspi_gpio_sensor``.

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

.. code-block:: yaml

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

.. code-block:: yaml

    motion_detector:
        implementation: dummy

        dummy_gpio_sensor:
            # no value available

Motion Handler (``motion_handler``)
```````````````````````````````````
| A component which handles motion detection, in the current implementation this is represented either by a Raspberry Pi- or Dummy-Camera. 
| The following settings are available for ``motion_handler`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the handler component, available values are:
| Type: ``enum``
| Default: ``raspi``

- ``raspi``
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

.. code-block:: yaml

    motion_handler:
        implementation: raspi

        raspi_cam:
            record_path: '$HOME/.camguard/records' # default
            record_count: 15 # default
            record_interval_seconds: 1.0 # default
            record_file_format: "{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg" # default


Example configuration for Dummy usage
'''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    motion_detector:
        implementation: dummy

        dummy_cam:
            record_path: '$HOME/.camguard/records' # default
            record_count: 5
            record_interval_seconds: 0.5
            record_file_format: "{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg" # default

.. _file-storage-label:

File Storage (``file_storage``)
```````````````````````````````
| A component which handles file storage of the recorded files from the motion handler. 
| The following settings are available for ``file_storage`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the file storage component, by default this is a google drive storage implementation. Available values are:
| Type: ``enum``
| Default: ``default`` (google drive storage)

- ``default``
- ``dummy`` (selects a dummy/offline implementation of the file storage for testing purposes)

Implementation Settings
'''''''''''''''''''''''
The settings node of the selected implementation type, available values are:

- gdrive_storage
- dummy_gdrive_storage

Following settings are *only available for ``gdrive_storage``*.

Upload folder name (``upload_folder_name``)
'''''''''''''''''''''''''''''''''''''''''''
| The name of the upload folder in the gdrive root.
| Type: ``string``
| Default: ``'Camguard'``

OAuth token path (``oauth_token_path``)
'''''''''''''''''''''''''''''''''''''''
| Folder path for saving Google-OAuth ``token.json`` file.
| Type: ``string``
| Default: ``'.'``

.. _google-oauth-credentials-label:

OAuth credentials path (``oauth_credentials_path``)
'''''''''''''''''''''''''''''''''''''''''''''''''''
| Folder path for loading Google-OAuth ``credentials.json`` file.
| Type: ``string``
| Default: ``'.'``

Example configuration for GDrive File Storage
'''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    file_storage:
        implementation: default

        gdrive_storage:
                upload_folder_name: 'Camguard' # default 
                oauth_token_path: "~/.config/camguard"
                oauth_credentials_path: "~/.config/camguard"

Example configuration for Dummy usage
'''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    file_storage:
        implementation: dummy

        dummy_gdrive_storage:
            # there are no specific settings for this node

Mail client (``mail_client``)
```````````````````````````````
| Component which enables mail notification after motion motion is detected and handled by the motion handler.
| The following settings are available for ``mail_client`` node:

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the mail client, by default this is a generic SMTP Mail Client implementation.
| Type: ``enum``
| Default: ``default`` (SMTP mail client implementation)

- ``default``
- ``dummy`` (selects a dummy/offline implementation of the mail client for testing purposes)

Implementation Settings
'''''''''''''''''''''''
| There is no dedicated settings node for the mail client, the settings of the selected implementation type reside inside the ``mail_client`` node.

Username (``username``)
'''''''''''''''''''''''
| SMTP username for mail server authentication.
| Type: ``string``

Password (``password``)
'''''''''''''''''''''''
| SMTP password for mail server authentication. This is currently *not* encrypted.
| Type: ``string``

Sender mail (``sender_mail``)
'''''''''''''''''''''''''''''
| The sender mail address.
| Type: ``string``

Receiver mail (``receiver_mail``)
'''''''''''''''''''''''''''''''''
| The address of the mail recipient.
| Type: ``string``

Hostname (``hostname``):
''''''''''''''''''''''''
| Mail server hostname
| Type: ``string``

Example configuration for SMTP Mail Client 
''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    mail_client:
        implementation: default

        username: 'my-mail-user'
        password: 'my-user-password'
        sender_mail: 'user@mail-domain.com'
        receiver_mail: 'recipient@gmail.com'
        hostname: mail-domain.com

Example configuration for Dummy usage 
'''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    mail_client:
        implementation: dummy

        username: 'my-mail-user'
        password: 'my-user-password'
        sender_mail: 'user@mail-domain.com'
        receiver_mail: 'recipient@gmail.com'
        hostname: mail-domain.com

Network Device Detector (``network_device_detector``)
`````````````````````````````````````````````````````
| Component which checks continuously if a device can be found on the network by using the configured binary and search configuration. If any of the configured devices is found on network, motion handler will be disabled.

Implementation Type (``implementation``)
''''''''''''''''''''''''''''''''''''''''
| *Required* enumeration type for selecting the implementation of the network device detector component, available values are:
| Type: ``enum``
| Default: ``default``

- ``default``
- ``dummy`` (selects a dummy/offline implementation of the network device detector for testing purposes)

Implementation Settings
'''''''''''''''''''''''
The settings node of the selected implementation type, available values are:

- nmap_device_detector
- dummy_network_device_detector

Following settings are *only available for ``nmap_device_detector``*.

IP Addresses (``ip_addr``)
''''''''''''''''''''''''''
| The IP Addresses from the network device, which should detected 
| Type: ``list[str]``

Interval Seconds (``interval_seconds``)
'''''''''''''''''''''''''''''''''''''''
| The detection interval in seconds
| Type: ``float``

Example configuration for nmap Device Detector 
''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    network_device_detector:
        implementation: default

        nmap_device_detector:
            ip_addr: 
                - '191.168.0.1'
                - '191.168.0.2'
            interval_seconds: 4.0

Example configuration for Dummy Device Detector 
'''''''''''''''''''''''''''''''''''''''''''''''

.. code-block:: yaml

    network_device_detector:
        implementation: dummy

        dummy_network_device_detector:
            # there are no specific settings for this node

Configuring Google-OAuth for Google-Drive
-----------------------------------------
To enable the file storage for google-drive usage (see :ref:'file-storage-label`), it's necessary to configure google-oauth authentication for your google account following these steps:

1. Create a |google cloud platform project|_ 
2. Enable Google-Drive API
3. Create |google access credentials|_ 
   
   1. Configure OAuth consent screen. ⚠️ Take care to *not* configure a logo/icon for the project, otherwise you'll have to verify your production state. [#project_verification]_
   2. Set Application Type to **Desktop**
4. Download client secret json and rename it to `credentials.json`
5. Copy `credentials.json` to `~/.config/camguard` or configure :ref:`google-oauth-credentials-label`

.. _`google cloud platform project`: https://developers.google.com/workspace/guides/create-project 
.. |google cloud platform project| replace:: **Google Cloud Platform Project**

.. _`google access credentials`: https://developers.google.com/workspace/guides/create-credentials
.. |google access credentials| replace:: **access credentials**

.. rubric:: Footnotes
.. [#project_verification] Google verifies projects configured for a user type of External and a publishing status of In production if they meet special criterial like displaying icon/logo on OAuth consent screen. See |google verification status|_

.. _`google verification status`: https://support.google.com/cloud/answer/10311615?hl=en#zippy=%2Cin-production%2Cverification-not-required%2Cneeds-verification
.. |google verification status| replace:: **Google Project Verification Status**
