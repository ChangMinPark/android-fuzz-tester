#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

import os

# ------------ #
#   Settings   #
# ------------ #
MODE_FOLLOWER_LEADER = True
MODE_RANDOM = False      

REBOOT_AFTER_EACH_APP = False
KEEP_INSTALLED_APP = False
NUM_RUNS_PER_APP = 5            
WAIT_AFTER_APP_LAUNCH = 5          # Wait for the device to load first screen 
APP_INSTALL_DELAY = 30
TESTING_TIMEOUT = WAIT_AFTER_APP_LAUNCH + 180   # in second

LOGGER_VERBOSE = True

# --------- #
#   Paths   #
# --------- #
LOG_DIR = 'log'
TESTED_PKGS_PATH = os.path.join(LOG_DIR, "tested_pkgs")


# ------------- #
#   Tool Paths  #
# ------------- #
ADB = 'adb'
AAPT = 'aapt'


# -------------------------- #
#   Patterns and Constants   #
# -------------------------- #
DELIMITER = "___" #should confirm if it is unique
TIMEOUT_EXCEPTION = "TIMEOUT"
NOT_FOREGROUND_EXCEPTION = "PACKAGE_NOT_FOREGROUND"
INSTALL_FAILED_EXCEPTION = "INSTALL_FAILED"


# ------------------------- #
#   Android API & Version   #
# ------------------------- #
ANDROID_API_VERSION = {
    # https://en.wikipedia.org/wiki/Android_version_history

    '4.0':      '14',       # Oct 18, 2011
    '4.0.1':    '14',
    '4.0.2':    '14',

    '4.0.3':    '15',       # Dec 16, 2011
    '4.0.4':    '15',

    '4.1':      '16',       # Jul 9, 2012
    '4.1.1':    '16',
    '4.1.2':    '16',

    '4.2':      '17',       # Nov 13, 2012
    '4.2.1':    '17',
    '4.2.2':    '17',

    '4.3':      '18',       # Jul 24, 2013
    '4.3.1':    '18',

    '4.4':      '19',       # Oct 31, 2013
    '4.4.1':    '19',
    '4.4.2':    '19',
    '4.4.3':    '19',
    '4.4.4':    '19',

    '4.4W':     '20',       # Jun 25, 2014
    '4.4W.1':   '20',
    '4.4W.2':   '20',

    '5.0':      '21',       # Nov 4, 2014
    '5.0.1':    '21',
    '5.0.2':    '21',

    '5.1':      '22',       # Mar 2, 2015
    '5.1.1':    '22',

    '6.0':      '23',       # Oct 2, 2015
    '6.0.1':    '23',

    '7.0':      '24',       # Aug 22, 2016

    '7.1':      '25',       # Oct 4, 2016
    '7.1.1':    '25',
    '7.1.2':    '25',

    '8.0':      '26',       # Aug 21, 2017

    '8.1':      '27',       # Dec 5, 2017

    '9':        '28',       # Aug 6, 2018

    '10':       '29',       # Sep 3, 2019

    '11':       '30',       # Sep 8, 2020
    
    '12':       '31',       # Oct 4, 2021
}


