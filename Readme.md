[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# pyucache

A python script to connect to the [Apogee μCache AT-100 datalogger](https://www.apogeeinstruments.com/microcache-bluetooth-micro-logger/), makes precision environmental measurements using Apogee’s analog sensors. This script is meant for periodical data collection, while the μCache does internal datalogging. It also verifies the battery charge and alerts the user if the charge gets too low.

Hardware setup steps:
1. Set up sensors and logging in the [Apogee Connect Android app](https://play.google.com/store/apps/details?id=com.apogeeinstruments.apogeeconnect).
2. Set up periodical advertising.

## Dependencies

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Jupyter Notebook](https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white)

The following python packages are required:

  - asyncio
  - logging
  - datetime
  - struct
  - time
  - [Bleak](https://github.com/hbldh/bleak) version 0.16, as this is available in Anaconda. Note that this is an old version.
  
## Occasional issues:

  - Connection can fail, upon which the device and the script will hang. Typically, a few long presses on the device resets the device, and a scan for devices resets the script.
  - Crashes are possible due to connection issues. Make sure to use failsafes when running this script automatically on a periodic schedule.


## Typical setup of a script and functionnality using the Apogee Device class

The typical use of the Apogee Device class is the following, recommended by the Apogee μCache AT-100 API manual. To simplify, a *setup_routine()* and a *download_routine()* are provided in the class definition.

1. Bluetooth advertising is started via button press or other means.
2. The script scans for Apogee Bluetooth devices by searching for the Apogee Company Identifier 0x0644 in the Manufacturer Specific Data portion of the Advertising packet.
3. The Alias of the Apogee Bluetooth device is be read in the Scan Response Data and returned in the list of dictionnaries of discovered devices. This can be used to connect to a specific device.
4. The script is used to create an instance of the *apogee_device(device_address)* class and uses it to connect to an Apogee Bluetooth device (*connect()*).
5. Once connected, the device information and battery levels should be read (*read_info()* and *read_battery_level()*)
6. The current time is read. If it is more than 2s off from the computer time (in UTC, this tolerance is an option in the class function *check_and_update_time()*), it is updated to match the computer time (in UTC).
7. (Optional) An alias can be set to name the device (*set_alias(name)*). This should be unique. This name will show up in advertising packets when the script is scanning for Apogee Bluetooth devices.
8. Data Logging can be set up at desired intervals and includes sampling interval, averaging interval, and an optional start time (in s, using *set_logging_settings(sampling_interval_s, logging_interval_s, start_time)*).
9. Data logging can be enabled or disabled (*set_logging_status(True/False)*), or simply read (*read_logging_status()*).
10. When data logging is enabled, the timestamp of when the data log will be full and starts overwriting entries that have not been transferred can be checked using *read_log_full_time()*.
11. The latest timestamp that has been transferred can be read using *read_last_transferred()*. To move the starting point of the (next) transfer forward, skipping a portion of the data log, or back to transfer data that has already been transferred before, a new timestamp can be written too, using *write_last_transferred(last_transfer_time_unix)*. This is mostly used internally to ensure the data log transfer picks up where it left off from the previous transfer.
12. A data log transfer is done using notifications or indications, using *transfer_data()*.
13. To find out how many data log entries are available to be transferred, the timestamp of the oldest entry in the data log, and the total number of entries in the data log, use *read_nb_logs_available()*.
14. To set up periodical advertising of the BLE device, the function *set_advertising_frequency(freq=0)* is used, where writing a 0 (the standard) sets it up to advertise only on button press.
15. Data can be written to a csv file using *write_datafile(file_path)*.
16. The script disconnects from the Apogee Bluetooth device (*disconnect()*).

### Not implemented

1. Sensor calibration and setup is not implemented. This should be done using the [Apogee Connect Android app](https://play.google.com/store/apps/details?id=com.apogeeinstruments.apogeeconnect). The script merely reads which sensor is connected and uses that data.
2. Live data reception is not (yet) implemented. Logging through constant connections is not recommended, so collecting logs is the priority of this script. Nonetheless:
    1. The Live Data Control Characteristic can be used to set averaging time for live data (in s, rounded down to nearest 0.25s, with a max. value of 31.75s, using *set_live_settings(avg_time_s)*).

## License

This software is distributed under the GNU GPL version 3.

*NOTE*: This license covers the software only. The user and API manuals are copyrighted by [Apogee Instruments, Inc](https://www.apogeeinstruments.com/) and are published here with their permission.

### Disclaimer

This software is not guaranteed to work. Use at your own risk.

