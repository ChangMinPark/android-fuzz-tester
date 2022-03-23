#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

from os.path import abspath, exists, isdir, join
from subprocess import Popen, PIPE
from sys import stderr
from re import search
import sys
import os
import glob
import signal
import multiprocessing
import io
import contextlib

# Local packages
import src.config as conf
import src.aapt_utils as aapt


encoding="utf-8"

# Delay in seconds used to make sure that actions are properly performed.
ACTION_DELAY = 3 #3
REBOOT_DELAY = 60

def find_apks(path: str) -> list:
    '''
    Find all APK files under the given path recursively
    '''
    apks = []
    if path.endswith('.apk'):
        return [path]
    for apk in glob.glob(join(path, "**/*.apk"), recursive=True):
        if apk not in apks:
            apks.append(apk)
    return apks

def dirExists(dirPath: str) -> bool:
    '''
    Checks if the given directory path exists.
    '''
    if isdir(dirPath):
        if exists(dirPath):
            return True
    return False

def error(message: str) -> None:
    '''
    Prints an error message, deletes staging, and exits with status 1.
    '''
    stderr.write('ERROR: %s'  %(message))
    raise AttributeError(message)

def run_adb_command(d_serial: str, command: str, returnCode=False) -> str:
    '''
    Run the given command on the system
    '''
    command = [conf.ADB, '-s', d_serial] + command
    try:
        proc = Popen(command, stdout=PIPE)
        out, err = proc.communicate()
        out = out.decode(encoding, 'ignore')
    except:
        print ("Caught Exception while running command:")
        print ("  %s, %s" %(d_serial, str(command)))
        return out, err
    return proc.wait() if returnCode else out

def run_aapt_command(command: str) -> str:
    '''
    Run AAPT command
    '''
    try:
        proc = Popen([conf.AAPT] + command, stdout=PIPE)
        out, err = proc.communicate()
    except:
        msg = "Caught Exception while running aapt command \n - %s" %(command)
        raise RuntimeError(msg)
    return out

def get_device_serials() -> list:
    '''
    Get a list of currently available Android device serial numbers
    '''
    devices = []
    command = [conf.ADB, 'devices']
    process = Popen(command, stdout=PIPE)
    out, err = process.communicate()
        
    if process.wait() != 0:
        error("getDevices() failed!")

    for line in out.splitlines():
        line = line.strip().decode(encoding, 'ignore')
        if "List" in line:
            continue
        if "device" in line:
            devices.append(line.split("\t")[0])
    return devices

def get_abs_path(f) -> str:
    '''
    Get absolute path of the file
    ''' 
    abs_path = abspath(f)
    if not exists(abs_path):
        error("The file specified does not exist!")
    return abs_path

def get_power_level(d_serial: str) -> int:
    '''
    Get power level of the given device
    '''
    command = ['shell', 'dumpsys', 'battery']
    out = run_adb_command(d_serial, command)
    for line in out.splitlines():
        line = line.strip().decode(encoding, 'ignore')
        if "level" in line:
            return int(line.split(": ")[-1])
    return None

def is_wifi_connected(d_serial: str) -> bool:
    '''
    Check if the wifi is connected
    '''
    command = ['shell', 'dumpsys', 'connectivity']
    out = run_adb_command(d_serial, command)
    for line in out.splitlines():
        line = line.strip().decode(encoding, 'ignore')
        #Cynogenmod uses NetworkInfo, but Stock uses NetworkAgentInfo
        if ("NetworkInfo" in line or "NetworkAgentInfo" in line) \
        and "WIFI" in line \
        and "CONNECTED/CONNECTED" in line:
            return True
    return False

def thread_start(threads):
    '''
    Start threads
    '''
    for t in threads:
        t.start()

def thread_join(threads):
    '''
    Join threads
    '''
    for t in threads:
        t.join()

def prepare_apks(apk_path: str, exclude_tested: bool=False) -> list:
    '''
    Prepare APK files to test
    '''
    path = conf.TESTED_PKGS_PATH
    if not os.path.exists(path):
        with open(conf.TESTED_PKGS_PATH, 'w') as f:
            f.write('')
    apks = find_apks(apk_path)
    if exclude_tested:
        pkgs = []
        with open(path, 'r') as f:
            for row in f.readlines():
                pkgs.append(row.strip())
        apks = find_apks(apk_path)
        for apk in apks:
            pkg_name = aapt.get_package_name(apk)
            if pkg_name in pkgs:
                apks.remove(apk)
    return apks

def write_tested_pkg(pkg: str) -> None:
    '''
    Write tested package name
    '''
    path = conf.TESTED_PKGS_PATH
    if not os.path.exists(path):
        sys.exit("Given file path doesn't exist: %s" %(path))
    with open(path, 'a') as f:
        f.write(pkg+"\n")


def run_signal_timer(timeout: int) -> None:
    '''
    Run signal timer
    '''
    def signal_handler(signum, frame):
        raise Exception(conf.TIMEOUT_EXCEPTION)

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(timeout)


def run_thread_timer(timeout, func, args=(), kwargs={}) -> bool:
    '''
    Run thread timer
    '''
    if type(timeout) not in [int, float] or timeout <= 0.0:
        print("Invalid timeout!")
    elif not callable(func):
        print("{} is not callable!".format(type(func)))
    else:
        p = multiprocessing.Process(target=func, args=args, kwargs=kwargs)
        p.start()
        p.join(timeout)
        if p.is_alive():
            p.terminate()
            return False
        else:
            return True

def find_first(pattern: str, string: str, returnNone=False):
    '''
    Finds the first occurrence of a given pattern in a string
    '''
    output = search(pattern, string)
    if output:
        return output.group(0)
    if returnNone:
        return None
    error("Couldn't findFirst() for pattern: \n" + pattern + '\n' +
          "Couldn't findFirst() for string: \n" + string)

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = io.BytesIO()
    yield
    sys.stdout = save_stdout
