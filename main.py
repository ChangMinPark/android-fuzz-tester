#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

import random
from argparse import ArgumentParser
from threading import Thread

# Local packages
import src.commons as commons
import src.adb_utils as adb
from src.device import DeviceDriver
import src.config as conf
from src.logger import Logger


# Takes a path containing APKs to test
parser = ArgumentParser(description='Run a fuzz tester with given APKs')
parser.add_argument('APK_PATH', action='store', \
        help='A directory containing APKs')
args = parser.parse_args()
apk_path = args.APK_PATH

class FuzzTester:

    def __init__(self, apk_path: str):

        # Create a DeviceDriver
        self._device_driver = DeviceDriver.get_instance()
        self._device_driver.print_settings()
        self._logger = Logger.get_instance()

        # Prepare APKs to test 
        self._apks = commons.prepare_apks(apk_path, exclude_tested = False)
        self._logger.info(" - Number of APKs to test: %d" %(len(self._apks)))
        self._logger.info(" - Number of runs per app: %d" \
                            %(conf.NUM_RUNS_PER_APP))

    def run(self):
        '''
        Run and distribute apps to available devices
        '''
        threads=[]
        for idx, apk in enumerate(self._apks):
            msg = '================== %s (%d/%d) ==================' \
                %(apk.split('/')[-1], idx+1, len(self._apks))
            self._logger.info(msg)
            try:
                if conf.MODE_FOLLOWER_LEADER:
                    self._run_follower_leader(apk, conf.MODE_RANDOM)
                else:
                    # Get an idle device
                    d_serial = self._device_driver.get_idle_device(apk)
                    t = Thread(target = self._run_individual, \
                            args = (d_serial, apk, conf.MODE_RANDOM))
                    threads.append(t)
                    t.start()

            except Exception as e:
                msg = "Skipping %s due to the following exception: %s" %(apk, e)
                self._logger.warning(msg)

        commons.thread_join(threads)
        self._logger.info('\nTesting completed.')

    # ----------------- #
    #   Local Methods   #
    # ----------------- #
    def _run_individual(self, d_serial: str, 
                        apk: str, random_mode: bool = False) -> None:
        '''
        Run the given app in dividual mode, not follow-the-leader
        '''
        def run() -> None:
            try:
                d = DeviceDriver.get_instance()

                # Allow all permision popups and add the first activity to graph
                d.init_test(d_serial)

                # Root activity to start
                d.root_activity[d_serial] = d.cur_activity[d_serial]
                while True: 

                    # If the app is not foreground raise exception
                    if not d.check_foreground_package(d_serial):
                        raise Exception(conf.NOT_FOREGROUND_EXCEPTION)

                    # Find all nodes not tested yet.
                    nodes = d.get_next_nodes(d_serial, d.cur_activity[d_serial])

                    # If random mode, shuffle the found nodes
                    if random_mode:
                        random.shuffle(nodes)
                    
                    prev_activity = adb.get_foreground_activity_name(d_serial)   
                    for node in nodes:
                        d.travel_node(d_serial, node, random_mode)

                        # If an Activity was changed, break.
                        # (cannot test previously found UIs on the new Activity)
                        if not prev_activity == \
                                adb.get_foreground_activity_name(d_serial):
                            break

                    #  If none, break.
                    if not nodes:
                        if not d.root_activity[d_serial] == \
                            adb.get_foreground_activity_name(d_serial):
                            d.press_back(d_serial)
                        else:
                            break

            except Exception as e:
                print(e)

            # Save test results and clean device
            d.clean_device(d_serial, last= nth_try == conf.NUM_RUNS_PER_APP-1)

        for nth_try in range(conf.NUM_RUNS_PER_APP):
            self._logger.info('[ Run: %d ]' %(nth_try))

            # Prepare the device before testing
            d = DeviceDriver.get_instance()
            d.prepare_device(d_serial, apk, nth_try=nth_try)
            commons.run_thread_timer(conf.TESTING_TIMEOUT, run, args=())
  
    def _run_follower_leader(self, apk: str, random_mode: bool = False) -> None:
        '''
        Run the given app in follow-the-leader mode
        '''
        d = self._device_driver
        
        for nth_try in range(conf.NUM_RUNS_PER_APP):
            self._logger.info('[ Run: %d ]' %(nth_try))

            # Prepare devices before testing
            d.prepare_device_all(apk, nth_try=nth_try)
            
            # Run timer. If ends, it throws a timeout exception.
            commons.run_signal_timer(conf.TESTING_TIMEOUT)
            try:
                # Allow all permision popups and add the first activity to graph
                d.init_test_all()

                # Root activity to start
                d.root_activity[d.leader_device] = d.cur_activity[d.leader_device]
                while True: 

                    # If the app is not foreground raise exception
                    if not d.check_foreground_package(d.leader_device):
                        raise Exception(conf.NOT_FOREGROUND_EXCEPTION)

                    # Find all nodes not tested yet
                    nodes = d.get_next_nodes(
                            d.leader_device, d.cur_activity[d.leader_device])

                    # If random mode, shuffle the found nodes
                    if random_mode:
                        random.shuffle(nodes)
                    prev_activity = \
                        adb.get_foreground_activity_name(d.leader_device)   

                    for node in nodes:
                        d.travel_node_all(node, random_mode)
                        
                        # If an Activity was changed, break.
                        # (cannot test previously found UIs on the new Activity)
                        if not prev_activity == \
                                adb.get_foreground_activity_name(d.leader_device):
                            break

                    # If none, break.
                    if not nodes:
                        if not d.root_activity[d.leader_device] == \
                            adb.get_foreground_activity_name(d.leader_device):   
                            d.press_back_all()
                        else:
                            break
                        
                
            except Exception as e:
                print(e)
        
            # Save test results and clean devices
            d.clean_device_all()
   


def main():

    fz = FuzzTester(apk_path=apk_path)
    fz.run()


if __name__ =='__main__':
    main()
        
