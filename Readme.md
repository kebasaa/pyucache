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
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)

The following python packages are required to read the FLIR files:

  - Pandas
  - Numpy
  - PyBluez

## How to Cite

Jonathan D. Muller. (2022). pyucache: Script to log data from Apogee uCache. DOI: 10.5281/zenodo.4117838  (URL:
<https://doi.org/10.5281/zenodo.4117838>), Python notebook

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4117838.svg)](https://doi.org/10.5281/zenodo.4117838)

## License

This software is distributed under the GNU GPL version 3

