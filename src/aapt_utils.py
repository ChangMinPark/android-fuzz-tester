#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

from re import findall
from subprocess import Popen, PIPE

# Local packages
import src.commons as commons


encoding="utf-8"

def get_package_name(apkPath: str) -> str:
    '''
    Get package name of the APK file

    :param apkPath: A path of the APK file
    :return: package name
    '''
    command = ['dump', 'badging', apkPath]
    output = commons.run_aapt_command(command).decode(encoding, 'ignore')
    return findall("(?<=package: name=')[^']*", output)[0]

def get_launchable_activityList(apkPath: str) -> list:
    '''
    Get launchable activity list
    
    :param apkPath: A path of the APK file
    :return: a list of launchable activity names
    '''
    command = ['dump', 'badging', apkPath]
    output = commons.run_aapt_command(command).decode(encoding, 'ignore')
    return findall("(?<=launchable-activity: name=')[^']*", output)


