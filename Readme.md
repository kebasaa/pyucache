[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4117838.svg)](https://doi.org/10.5281/zenodo.4117838)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

# pyucache

A python script to connect to the [Apogee μCache AT-100 datalogger](https://www.apogeeinstruments.com/microcache-bluetooth-micro-logger/), makes precision environmental measurements using Apogee’s analog sensors. This script is meant for periodical data collection, while the μCache does internal datalogging. It also verifies the battery charge and alerts the user if the charge gets too low.

Hardware setup steps:
1. Set up sensors and logging in the [Apogee Connect Android app](https://play.google.com/store/apps/details?id=com.apogeeinstruments.apogeeconnect).
2. Set up periodical advertising.

## Dependencies

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Jupyter Notebook](https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white)
<!--![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)-->

The following python packages are required:

<!--  - Pandas-->
<!--  - Numpy-->
  - asyncio
  - logging
  - datetime
  - [Bleak](https://github.com/hbldh/bleak) version 0.16, as this is available in Anaconda. Note that this is an old version.


## Typical setup of a script using the Apogee Device class

The typical use of the Apogee Device class is the following, recommended by the Apogee μCache AT-100 API manual:

1. Bluetooth advertising is started via button press or other means.
2. The script scans for Apogee Bluetooth devices by searching for the Apogee Company Identifier 0x0644 in the Manufacturer Specific Data portion of the Advertising packet.
3. The Alias of the Apogee Bluetooth device is be read in the Scan Response Data and returned in the list of dictionnaries of discovered devices. This can be used to connect to a specific device.
4. The script connects to an Apogee Bluetooth device using the apogee_device class.
5. Once connected, the device information and battery levels are read
6. The current time is read. If it is more than 2s of tolerance (option to change this in the class function _check_and_update_time()_) off from the computer time (in UTC), it is updated to match the computer time (in UTC).

6. The Alias Characteristic can be used to give the device a name for reference. This name will show up in advertising packets when the script is scanning for Apogee Bluetooth devices.
7. The Sensor ID Characteristic can be read to find out which sensor to expect data from. It can also be changed to another sensor as needed.
8. Coefficients need to be programmed for some sensors using Coefficients1 and Coefficients2 Characteristics.
9. Calibration can be done for some sensors using the Calibration Characteristic.
10. The Live Data Control Characteristic can be used to set averaging time for live data.
11. Live data can be received by enabling notifications of the Live Data Control Characteristic.
12. Data Logging can be set up at desired intervals using the Data Log Timing Characteristic. It includes sampling interval, averaging interval, and an optional start time.
13. Data logging can be enabled or disabled using the Data Log Control Characteristic.
14. When data logging is enabled, the Data Log Full Time Characteristic can be read to know when the data log will be full and start overwriting entries that have not been transferred.
15. The Data Log Latest Timestamp Transferred Characteristic can be read to find out the latest timestamp that has been transferred. This characteristic can also be written to move the starting point of the transfer forward, skipping a portion of the data log, or back to transfer data that has already been transferred before. It can also be used to ensure the data log transfer picks up where it left off from the previous transfer.
    1. The script's save data has some data from previous transfers, including the timestamp 1562884800
    2. The script reads the Data Log Latest Timestamp Transferred Characteristic.
    3. The script compares the characteristic value to the most recent timestamp from the collected data log. In this example, it is 1562884800.
    4. If these values do not match, 1562884800 is written to Data Log Latest Timestamp Transferred characteristic.
    5. The script proceeds with the data log transfer.
16. The Data Log Entries Available Characteristic can be read to find out how many data log entries are available to be transferred, the timestamp of the oldest entry in the data log, and the total number of entries in the data log.
17. A data log transfer is done using notifications or indications of the Data Log Transfer Characteristic.
18. The Data Log Collection Rate Characteristic can be written to advertise only with a button press or to advertise synchronized with data logging to collect data as it becomes available.
19. The script disconnects from the Apogee Bluetooth device.


## How to Cite

Jonathan D. Muller. (2023). pyucache: Python script to interface with the Apogee μCache AT-100 datalogger through Bluetooth LE. DOI: 10.5281/zenodo.4117838  (URL:
<https://doi.org/10.5281/zenodo.4117838>), Python notebook

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4117838.svg)](https://doi.org/10.5281/zenodo.4117838)

## License

This software is distributed under the GNU GPL version 3.

**IMPORTANT NOTE:** The API documentation is copyrighted by Apogee Instruments, and not under the license above.

