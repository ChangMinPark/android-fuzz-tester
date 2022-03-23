#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''
from re import search
from time import sleep
from random import choice, randint
from math import pow
from string import ascii_letters, digits

# Local packages
import src.commons as commons
from src.config import ADB, INSTALL_FAILED_EXCEPTION
import src.config as conf
import src.aapt_utils as aapt


def adb_reboot_uiautomator(d_serial: str) -> None:
    '''
    Reboot UI Automator on the given device
    '''
    command1 = ['shell', 'pm', 'uninstall', 'com.github.uiautomator'] 
    command2 = ['shell', 'pm', 'uninstall', 'com.github.uiautomator.test']
    commons.run_adb_command(d_serial, command1)
    commons.run_adb_command(d_serial, command2)

def adb_close_keyboard(d_serial: str) -> None:
    '''
    close soft keyboard
    '''
    # 4 is pressing back, 111 is closing keyboard 
    # but 111 doesn't work on some devices.
    command = ['shell', 'input', 'keyevent', '4']   
    commons.run_adb_command(d_serial, command)


def adb_reboot(d_serial: str) -> None:
    '''
    adb reboot
    '''
    command = ['reboot']
    commons.run_adb_command(d_serial, command)
    sleep(120)
    while not d_serial in commons.get_device_serials():
        print('Still not rebooted ...')
        sleep(5)

def adb_root(d_serial: str) -> None:
    '''
    Root the given device
    '''
    commons.run_adb_command([ADB, '-s', d_serial, 'root'])
    sleep(conf.APP .ACTION_DELAY)

def install(d_serial: str, apk_path: str) -> None:
    '''
    Install the given APK file to the device
    '''
    commons.run_adb_command(d_serial, ['install', apk_path])
    sleep(conf.APP_INSTALL_DELAY)
    pkg_name = aapt.get_package_name(apk_path)
    installed = is_installed(d_serial, pkg_name)
    if not installed:
        raise Exception(INSTALL_FAILED_EXCEPTION)
    

def uninstall(d_serial: str, pkg_name: str) -> None:
    '''
    Uninstall the given app package on the device
    '''
    commons.run_adb_command(d_serial, ['uninstall', pkg_name])
    sleep(commons.ACTION_DELAY)


def is_installed(d_serial: str, pkg_name: str) -> bool:
    '''
    Check if the given package is already installed on the device
    '''
    out = commons.run_adb_command(d_serial, ['shell', 'pm', 'list', 'packages'])
    return not search('package:' + pkg_name, out) is None

def back(d_serial: str) -> None:
    '''
    Press back button
    '''
    commons.run_adb_command([ADB, '-s', d_serial, "shell", "input", "keyevent", "4"])
    sleep(commons.ACTION_DELAY)
 
def package_is_running(d_serial: str, pkg_name: str) -> bool:
    '''
    Checks if a given package is running.
    '''
    command = ['shell', 'ps']
    out = commons.run_adb_command(d_serial, command)
    if search('.*' + pkg_name, out):
        return True
    else:
        return False
    
def get_window_dumpsys(d_serial: str) -> str:
    '''
    Get dumpsys output to check mCurrentFocus and mFocusedApp
    '''
    command = ['shell', 'dumpsys', 'window', 'windows']
    out = commons.run_adb_command(d_serial, command)
    resultOne = search('mCurrentFocus.*}', out)
    resultTwo = search('mFocusedApp.*}', out)
    resultThree = search('mObscuring.*}', out)
    if resultOne is not None:
        return resultOne.group(0)
    elif resultTwo is not None:
        return resultTwo.group(0)
    elif resultThree is not None:
        return resultThree.group(0)
    else:
        return ''

def get_foreground_package_name(d_serial: str) -> str:
    '''
    Get the foreground package name.
    '''
    # Please note in (<=u0 ) the u0 helps because sometimes there is a u0 Application Error and
    # we want to skip over those as the application has crashed so it won't be in the background
    # but the application name will still show regardless.
    dump = commons.find_first('(?<=Window{).*?(?=\/|})', \
                                get_window_dumpsys(d_serial), True)
    if dump is not None:
        return dump.split(' ')[-1]
    else: 
        return None


def get_foreground_activity_name(d_serial) -> None:
    '''
    Get the foreground Acitvity name
    '''
    dump = commons.find_first('(?<=Window{).*?(?=})', \
                                get_window_dumpsys(d_serial), True)
    return dump.split('/')[-1] if dump else None

def force_stop(d_serial: str, pkg_name: str) -> None:
    '''
    Force stop the given package.
    '''
    commons.run_adb_command(d_serial, ['shell', 'am', 'force-stop', pkg_name])
    sleep(commons.ACTION_DELAY)

def is_in_foreground(d_serial: str, pkg_name: str) -> bool:
    '''
    Determines if the given package is in the foreground.
    '''
    try:
        interruptPckg = get_foreground_package_name(d_serial)
        if pkg_name == interruptPckg:
            return True
        force_stop(d_serial, interruptPckg)
    except Exception as e:
        print ("Exception in finding foreground APP\n - %s" %(e))
    return False

def bring_to_foreground(d_serial: str, pkg_name: str) -> None:
    '''
    Starts and bring the given package name to the foreground
    '''    
    command = ['shell', 'monkey', '-p', pkg_name,
               '-c', 'android.intent.category.LAUNCHER', '1']
    commons.run_adb_command(d_serial, command)
    sleep(commons.ACTION_DELAY)

def is_keyboard_numeric(d_serial: str) -> bool:
    '''
    Check if the keyboard mode is numeric
    '''
    return "Keyboard mode = 5" in \
        commons.run_adb_command(d_serial, ['shell', 'dumpsys', 'input_method'])

def type_text(d_serial: str, text: str) -> None:
    '''
    Send the given text to type on the Android d_serial.
    '''
    commons.run_adb_command(d_serial, ['shell', 'input', 'text', text])
    sleep(commons.ACTION_DELAY)

def type_random_text(length: int) -> None:
    '''
    Types random text on the Android device.
    '''
    if(not is_keyboard_numeric()):
        type_text(''.join(choice(ascii_letters+digits) for _ in range(length)))
    else:
        strt, end = pow(10,length-1), strt*10
        type_text(str(randint(strt, end)))
    back()


def is_keyboard_shown(d_serial: str) -> bool:
    '''
    Check if the keyboard is shown
    '''
    return "mInputShown=true" in \
        commons.run_adb_command(d_serial, ['shell', 'dumpsys', 'input_method'])

def logcat_clear(d_serial: str) -> None:
    '''
    Clear logcat.
    '''
    commons.run_adb_command(d_serial, ["logcat", "-c"])
    sleep(commons.ACTION_DELAY)

def logcat_dump(d_serial: str, filtered=False) -> str:
    '''
    Dumps logcat
    '''
    filter_list = ['Tethering:S',
#                   'dalvikvm:S',
                   'MobileDataStateTracker:S',
                   'Nat464Xlat:S',
                   'ConnectivityService:S',
                   'libEGL:S',
                   'AudioHardware:S',
                   'AudioService:S',
                   'CaptivePortalTracker:S',
                   'AudioTrack:S',
                   'OpenGLRenderer:S',
                   'SocketClient:S',
                   'OpenDelta:S',
                   'AlarmClock:S',
                   'AlarmManagerService:S',
#                   'AndroidRuntime:S',
                   'memtrack:S',
                   'android.os.Debug:S',
                   'JavaBinder:S',
                   'WindowState:S',
                   'UsageStats:S',
                   'keystore:S',
                   'Binder:S',
                   'AccessibilityNodeInfoDumper:S',
                   'jdwp:S',
                   'Documents:S',
                   'BackupManagerService:S',
                   'Launcher.Workspace:S',
                   'Launcher.Model:S',
                   'RecognitionManagerService:S',
                   'BroadcastQueue:S',
                   'InputReader:S',
                   'DMApp:S',
                   'SurfaceFlinger:S',
                   'MediaPlayer-JNI:S',
                   'SystemEventObserver:S',
                   'NfcService:S',
                   'AppUtils:S',
                   'Finsky:S',
                   'PhoneStatusBar:S',
                   'TAG:S']
    if filtered:
        out = commons.run_adb_command(d_serial, ["logcat", "-d"] + filter_list)
    else:
        out = commons.run_adb_command(d_serial, ["logcat", "-d"])
    sleep(commons.ACTION_DELAY)
    return out

def get_android_version(d_serial: str) -> str:
    '''
    Get Android version of the given device
    '''
    command = ['shell', 'getprop', 'ro.build.version.release']
    out = commons.run_adb_command(d_serial, command).strip()
    return out
