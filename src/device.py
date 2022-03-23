#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

import os
import sys
import random
import string
from datetime import datetime
from time import sleep
from threading import Thread
from uiautomator import Device
import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

# Local Packages
import src.config as conf
import src.commons as commons
import src.adb_utils as adb
import src.aapt_utils as aapt
import src.uiautomator_utils as ua_utils
from src.logger import Logger


class DeviceDriver:
    _instance = None

    @staticmethod
    def get_instance():
        if DeviceDriver._instance == None:
            DeviceDriver()
        return DeviceDriver._instance

    def __init__(self):
        if DeviceDriver._instance != None:
            msg = "Singleton class cannot be instantiated more than once."
            raise Exception(msg)
            
        self.cur_activity = {}      # {d_serial: current activity name}
        self.root_activity = {}     # {d_serial: root activity name}
        self._nth_try = {}          # {d_serial: nth try for the same app}
        self._apk_running = {}      # {d_serial: APK path}
        self._ua_devices = {}       # {d_serial: Device}
        self._graphs = {}           # {d_serial: nx.DiGraph}
        self._random_text = ''      # For EditText UI to type same text
        
        self._logger = Logger.get_instance()
        self.devices = self._find_devices()   # {d_serial: OS version}
        for d_serial in self.devices.keys():
            self._apk_running[d_serial] = None

        # Select a leader device
        self.leader_device = None
        if conf.MODE_FOLLOWER_LEADER:
            self.leader_device = self._select_leader()
        
        # Create a log directory
        if not os.path.isdir(conf.LOG_DIR):
            os.mkdir(conf.LOG_DIR)
        self._log_dir = os.path.join(conf.LOG_DIR, str(datetime.now()))
        os.mkdir(self._log_dir)

        DeviceDriver._instance = self


    # -------------------- #
    #   Pulbic Funcsions   #
    # -------------------- #
    def prepare_device(self, d_serial: str, apk: str, 
                        nth_try: int=0) -> None:
        '''
        Prepare device
        '''
        self._apk_running[d_serial] = apk
        self._reset_device(d_serial)
        self._install_apk(d_serial, apk)
        self._nth_try[d_serial] = str(nth_try)

        # Create a apk log directory
        apk_log_dir = os.path.join(self._log_dir, aapt.get_package_name(apk))
        if not os.path.isdir(apk_log_dir):
            os.mkdir(apk_log_dir)
        nth_log_dir = os.path.join(apk_log_dir, str(nth_try))
        if not os.path.isdir(nth_log_dir):
            os.mkdir(nth_log_dir)
        
    def prepare_device_all(self, apk:str, nth_try: int=0) -> None:
        '''
        Prepare devices
        '''
        threads=[]
        for d_serial in self.devices.keys():
            thread = Thread(target = self.prepare_device, 
                              args = (d_serial, apk, nth_try,))
            threads.append(thread)
        commons.thread_start(threads)
        commons.thread_join(threads)

    def init_test(self, d_serial) -> None:
        '''
        Initialize root activity and grant permissions 
        '''
        while not self.check_foreground_package(d_serial): sleep(1)
        self.allow_permission_popup(d_serial)
        self.add_new_activity(d_serial)

    def init_test_all(self) -> None:
        '''
        Initialize root activity and grant permissions for all devices
        '''
        threads=[]
        for d_serial in self.devices.keys():
            thread = Thread(target = self.init_test, args = (d_serial,))
            threads.append(thread)
        commons.thread_start(threads)
        commons.thread_join(threads)

    def clean_device(self, d_serial: str, last: bool = True) -> None:
        '''
        Clean device after done with testing
        '''
        pkg_name = aapt.get_package_name(self._apk_running[d_serial])

        # Write a log
        self._write_log(d_serial, self._apk_running[d_serial])

        # Draw tested UI graph
        self._draw_graph(d_serial)

        # Uninstall the app or just stop
        if conf.KEEP_INSTALLED_APP:
            adb.force_stop(d_serial, pkg_name)
        else:
            adb.uninstall(d_serial, pkg_name)

        # Add to a tested package list
        commons.write_tested_pkg(pkg_name)

        # Make the device idle
        self._nth_try[d_serial] = None
        self._graphs[d_serial] = None
        self.cur_activity[d_serial] = None
        if last:
            self._apk_running[d_serial] = None

    def clean_device_all(self, last: bool = True) -> None:
        '''
        Clean all devices after done with testing
        '''
        threads=[]
        for d_serial in self.devices.keys():
            thread = Thread(target = self.clean_device, 
                              args = (d_serial, last,))
            threads.append(thread)
        commons.thread_start(threads)
        commons.thread_join(threads)

    def allow_permission_popup(self, d_serial: str) -> None:
        '''
        Handle permission popups
        '''
        sleep(2)
        permission_button_names = [
                'com.android.packageinstaller:id/permission_allow_button',
                'com.android.permissioncontroller:id/permission_allow_button']
        
        xml = self._ua_devices[d_serial].dump()
        uis = ua_utils.get_clickable_list(ua_utils.get_current_tree(xml))
        
        # Allow Permission Popup if found
        for ui in uis:
            if (ui['resourceId'] in permission_button_names
                    and ui['text'].lower() == 'allow'):
                ui_element = self._ua_devices[d_serial](text=ui['text'], \
                                className=ui['className'], \
                                resourceId=ui['resourceId'])
                ui_element.click.wait()

                # Check if other permission popup exists
                self.allow_permission_popup(d_serial)
                break
    
    def check_foreground_package(self, d_serial: str) -> bool:
        '''
        Check if the app is foreground
        '''
        pkg_name = aapt.get_package_name(self._apk_running[d_serial])
        fg_pkg_name = adb.get_foreground_package_name(d_serial)
        return pkg_name == fg_pkg_name
                
    
    def add_new_activity(self, d_serial: str, pre_node=None):
        '''
        Add new activity found to graphs and change current activity
        '''
        self.cur_activity[d_serial] = \
                adb.get_foreground_activity_name(d_serial)   
        
        if self.cur_activity[d_serial] in self._graphs[d_serial]:
            return
        
        cur_package = adb.get_foreground_package_name(d_serial)
        if cur_package != \
                aapt.get_package_name(self._apk_running[d_serial]):
            return
        
        if cur_package not in self._graphs[d_serial]:
            self._graphs[d_serial].add_node(cur_package, 
                    **{"type": "package", "visited": True})
            self._graphs[d_serial].add_node(self.cur_activity[d_serial], 
                    **{"type": "activity", "visited": True})
            self._graphs[d_serial].add_edge(cur_package, 
                    self.cur_activity[d_serial])
        else:
            self._graphs[d_serial].add_node(self.cur_activity[d_serial], 
                    **{"type": "activity", "visited": False})
            if pre_node != None:
                self._graphs[d_serial].add_edge(pre_node, 
                        self.cur_activity[d_serial])
        
        xml = self._ua_devices[d_serial].dump()
        ui_dics = ua_utils.get_clickable_list(ua_utils.get_current_tree(xml))

        for idx, ui in enumerate(ui_dics):
            dic = dict(ui.items() | {"type": "element", "visited": False,
                "second_visit": False}.items())
            node_name = self.cur_activity[d_serial] + conf.DELIMITER \
                    + ui['className'].split('.')[-1].lower() + str(idx)
            self._graphs[d_serial].add_node(node_name, **dic)
            self._graphs[d_serial].add_edge( \
                    self.cur_activity[d_serial], node_name)
    
    def travel_node(self, d_serial: str, node, random_mode= False):
        '''
        Travel the given node
        '''
        # If the app is not foregorund, raise exception
        if not self.check_foreground_package(d_serial):
            raise Exception(conf.NOT_FOREGROUND_EXCEPTION)
    
        self.add_new_activity(d_serial)
        prev_activity = adb.get_foreground_activity_name(d_serial)

        # Print UI node testing
        if not conf.MODE_FOLLOWER_LEADER and conf.DELIMITER in node:
            self._logger.debug('%s, %s ---> %s' %(d_serial, \
                                adb.get_foreground_activity_name(d_serial), 
                                str(node.split(conf.DELIMITER)[-1])))
        if not random_mode:
            if not self._visit_node(d_serial, node):
                self.add_new_activity(d_serial, node)
    
                if len(self.get_next_nodes(d_serial, prev_activity)) != 0 and \
                    not self._graphs[d_serial]._node[node]['second_visit']:

                    self._update_attr(d_serial, node, "visited", False)
                    self._update_attr(d_serial, node, "second_visit", True)
                    self.press_back(d_serial)
                else:
                    # tested all nodes in the current activity
                    self.cur_activity[d_serial] = \
                            self._next_activity(d_serial)
        else:
            if conf.MODE_FOLLOWER_LEADER:
                root_activity = self.root_activity[self.leader_device]
            else:
                root_activity = self.root_activity[d_serial]
            if not self._visit_node(d_serial, node):
                self.add_new_activity(d_serial, node)
                self.cur_activity[d_serial] = \
                        self._next_activity(d_serial)
            if len(self.get_next_nodes(d_serial, self.cur_activity[d_serial])) \
                    == 0 and not self.cur_activity[d_serial] == root_activity:
                self.press_back(d_serial)
    
    def travel_node_all(self, node, random_mode) -> None:
        '''
        Travel the given node on all devices
        '''
        # Print UI node testing
        if conf.DELIMITER in node:
            self._logger.debug('%s ---> %s' \
                    %(adb.get_foreground_activity_name(self.leader_device), 
                    str(node.split(conf.DELIMITER)[-1])))
        else:
            self._logger.debug('%s' \
                    %(adb.get_foreground_activity_name(self.leader_device)))

        threads=[]
        for d_serial in self.devices.keys():
            thread = Thread(target = self.travel_node, 
                              args = (d_serial, node, random_mode))
            threads.append(thread)
        commons.thread_start(threads)
        commons.thread_join(threads)
        self._random_text = ''
    
    def press_back(self, d_serial: str) -> None:
        '''
        Press back button to goto previous activity
        '''
        prev_activity = adb.get_foreground_activity_name(d_serial)
        self._ua_devices[d_serial].press.back()
        while prev_activity == adb.get_foreground_activity_name(d_serial):
            if not self.check_foreground_package(d_serial):
                raise Exception(conf.NOT_FOREGROUND_EXCEPTION)
            sleep(1)
        self.cur_activity[d_serial] = \
                adb.get_foreground_activity_name(d_serial)


    def press_back_all(self) -> None:
        '''
        Press back button to goto previous activity for all devices
        '''
        threads=[]
        for d_serial in self.devices.keys():
            thread = Thread(target = self.press_back, 
                              args = (d_serial,), kwargs={})
            threads.append(thread)
        commons.thread_start(threads)
        commons.thread_join(threads)
    
    def get_next_nodes(self, d_serial: str, activity: str) -> list:
        '''
        Get next nodes to test
        '''
        nodes = []
        if activity == None:
            return nodes
        for node, attr in sorted(self._graphs[d_serial].nodes(data=True)):
            if not node.startswith(activity):
                continue
            if attr['visited']:
                continue
            nodes.append(node)
        return nodes
    
    def get_idle_device(self, apk: str) -> str:
        '''
        Get an idle device
        '''
        while True:
            for d_serial in self._apk_running.keys():
                if not self._apk_running[d_serial]:
                    self._apk_running[d_serial] = apk
                    return d_serial
            sleep(5)
        return None

    def get_visited_nodes(self, d_serial: str) -> list:
        '''
        Get visited nodes
        '''
        nodes = []
        for node, attr in sorted(self._graphs[d_serial].nodes(data=True)):
            if not attr['visited']:
                continue
            nodes.append(node)
        return nodes

    def print_settings(self) -> None:
        '''
        Print test settings
        '''
        self._logger.info('')
        self._logger.info("================== %s ==================" \
                    %(str(datetime.now())))
        self._logger.info("[ New Test ]")
        self._logger.info(" - Follow-the-leader mode: %s" \
                    %(str(conf.MODE_FOLLOWER_LEADER)))
        self._logger.info(" - Random mode: %s" %(str(conf.MODE_RANDOM)))
        self._logger.info(" - Keep apps installed (no uninstall for " +\
                    "login-requied apps): %s" %(str(conf.KEEP_INSTALLED_APP)))
        self._logger.info(" - Connected devices:")
        for idx, d in enumerate(self.devices.items()):
            device_str = "     %d. %s (Android version: %s)" %(idx, d[0], d[1])
            device_str += " <- leader" if d[0] == self.leader_device else ""
            self._logger.info(device_str)
            
    # --------------------- #
    #   Private Funcsions   #
    # --------------------- #
    def _reset_device(self, d_serial: str) -> None:
        '''
        Reset the device
        '''
        # Reboot
        if conf.REBOOT_AFTER_EACH_APP:
            adb.adb_reboot(d_serial)

        # Clear Log
        adb.logcat_clear(d_serial)
        
        # Reset UI Automator Device and DiGraph
        self._ua_devices[d_serial] = Device(d_serial)
        self._graphs[d_serial] = nx.DiGraph()
 
    def _install_apk(self, d_serial: str, apk_path: str) -> None: 
        '''
        Install the given APK to the device
        '''
        self._apk_running[d_serial] = apk_path
        pkg_name = aapt.get_package_name(apk_path)

        if adb.is_installed(d_serial, pkg_name):
            # If it is in foreground, stop 
            if adb.is_in_foreground(d_serial, pkg_name):
                adb.force_stop(d_serial, pkg_name)

            if conf.KEEP_INSTALLED_APP:
                adb.bring_to_foreground(d_serial, pkg_name)
                self._logger.info("%s is ready on %s." %(pkg_name, d_serial))
                sleep(conf.WAIT_AFTER_APP_LAUNCH)
                return
            else:
                adb.uninstall(d_serial, pkg_name)
        adb.install(d_serial, apk_path)
        adb.bring_to_foreground(d_serial, pkg_name)
        self._logger.info("%s is installed and ready on %s." \
                        %( pkg_name, d_serial))
        sleep(conf.WAIT_AFTER_APP_LAUNCH)
 
    def _find_devices(self) -> dict:
        '''
        Using ADB, find serials of connected devices and their Android versions
        '''
        devices = {}
        for d_serial in commons.get_device_serials():
            devices[d_serial] = adb.get_android_version(d_serial)
        return devices

    def _select_leader(self) -> str:
        '''
        Ask a user to select which device to be a leader
        '''
        print('\nList of devices running:')
        d_serials = self.devices.keys()
        for i, d_serial in enumerate(d_serials):
            print('    %s. %s (Android %s)' 
                    %(i, d_serial, self.devices[d_serial]))
        qes = '\nWhich device would you like to select for a '
        qes += 'leader (# or serial)? '
        choice = str(input(qes))
        for i, d_serial in enumerate(d_serials):
            if choice == str(i) or choice == d_serial:
                msg = "[%s]: Device, %s, was selected for a leader. \n"
                print(msg %(str(datetime.now()), d_serial))
                return d_serial
        sys.exit('[!] Invalid device was selected.')

    def _write_log(self, d_serial: str, apk: str) -> None:
        '''
        Write a log with error messages if failed
         - Failure #:
            1. The device is disconnected (hung).
            2. The app is not on foreground.
            3. At least one runtime error found in the logs
            4. Traversed UIs are different with leader device's graph
        '''
        log_file = os.path.join(self._log_dir, 'results.log')
    
        hung = False
        if d_serial in commons.get_device_serials():
            dump = adb.logcat_dump(d_serial)
        else:
            hung = True
            dump = "Device not found in adb devices: " + d_serial
    
        pkg_name = aapt.get_package_name(apk)
        nodes = self.get_visited_nodes(d_serial)

        succ_msg = "%s SUCCESS on %s, try: "+self._nth_try[d_serial]+"\n" 
        fail_msg = "%s FAILED (%d) on %s, try: "+self._nth_try[d_serial]+"\n"
        
        if hung:
            with open(log_file, 'a', encoding='utf8') as log:
                log.write(fail_msg %(apk, 1, d_serial))
        elif not pkg_name == adb.get_foreground_package_name(d_serial):
            with open(log_file, 'a', encoding='utf8') as log:
                log.write(fail_msg %(apk, 2, d_serial))
        elif dump.find("E/AndroidRuntime") >= 0:
            with open(log_file, 'a', encoding='utf8') as log:
                log.write(fail_msg %(apk, 3, d_serial))
        elif conf.MODE_FOLLOWER_LEADER and not nx.is_isomorphic(
                self._graphs[self.leader_device], self._graphs[d_serial]):
            with open(log_file, 'a', encoding='utf8') as log:
                log.write(fail_msg %(apk, 4, d_serial))
        else:
            with open(log_file, 'a', encoding='utf8') as log:
                log.write(succ_msg %(apk, d_serial))
    
        apk_log = os.path.join(self._log_dir, aapt.get_package_name(apk), 
                    self._nth_try[d_serial], 'adb_logcat_'+d_serial+'.log')
        with open(apk_log, 'w', encoding='utf8') as log_f:
            log_f.write(dump)

    def _draw_graph(self, d_serial: str) -> None:
        '''
        Draw a graph for the traversed UIs
        '''
        graph = self._graphs[d_serial]
        cPackage = aapt.get_package_name(self._apk_running[d_serial])
        for node, attr in sorted(graph.nodes(data=True)):
            if attr['type'] == "package":
                graph._node[node]['label'] = "ROOT"
                graph._node[node]['style'] = "filled"
                graph._node[node]['fillcolor'] = "yellow"
            elif attr['type'] == "activity":
                graph._node[node]['label'] = node.split(cPackage)[-1]
                graph._node[node]['style'] = "filled"
                graph._node[node]['fillcolor'] = "orange"
            else:
                graph._node[node]['label'] = node.split(cPackage)[-1]
                graph._node[node]['style'] = "filled"
                graph._node[node]['fillcolor'] = "green"
                
            if attr['visited'] == False:
                graph._node[node]['label'] = node.split(cPackage)[-1]
                graph._node[node]['style'] = "filled"
                graph._node[node]['fillcolor'] = "red"
        
        graphviz = to_agraph(graph)
        graphviz.layout('dot')
        graphviz.draw(os.path.join(self._log_dir, 
                    aapt.get_package_name(self._apk_running[d_serial]), 
                    self._nth_try[d_serial], 'ui_graph_'+d_serial+'.pdf'))
        
    def _update_attr(self, d_serial:str, node, attr, value) -> None:
        '''
        Update the addtribute of the node
        '''
        self._graphs[d_serial]._node[node][attr] = value
   

    def _next_activity(self, d_serial: str):
        '''
        Find an unvisited activity in the node list
        '''
        for node, attr in sorted(self._graphs[d_serial].nodes(data=True)):
            if attr['type'] == "activity" and attr['visited'] == False:
                return node
        return None


    def _visit_node(self, d_serial:str , node) -> bool:
        '''
        Visit the given node
        '''
        if not node in self._graphs[d_serial]:
            self._logger.warning('[!] Node does not exist on device graph')
            return
    
        # Write to a apk log directory
        nth_log = os.path.join(self._log_dir, 
            aapt.get_package_name(self._apk_running[d_serial]), 
            self._nth_try[d_serial], 'uis_traversed_'+d_serial+'.log')
        with open(nth_log, 'a') as nth_log_f:
            nth_log_f.write(node+"\n")
        self.allow_permission_popup(d_serial)
        ui = self._graphs[d_serial]._node[node]
    
        # Check current UIs on foreground
        xml = self._ua_devices[d_serial].dump()
        ui_dics = ua_utils.get_clickable_list(ua_utils.get_current_tree(xml))
        foreground_ui_ids = \
                [ ui['resourceId'] for idx, ui in enumerate(ui_dics) ]
    
        if ui['type'] == "activity":
            self._update_attr(d_serial, node, "visited", True)
        elif not ui['resourceId'] in foreground_ui_ids:
            self._graphs[d_serial].remove_node(node)
        else:
            ui_element = self._ua_devices[d_serial](text=ui['text'], \
                                         className=ui['className'], \
                                         resourceId=ui['resourceId'])
            if ui_element.exists:
                # Type random strign on a EditText widget
                if ui_element.className == "android.widget.EditText":
                    if self._random_text == '':
                        self._random_text = \
                            ''.join(random.choice(string.ascii_letters) \
                            for i in range(10))
                    ui_element.set_text(self._random_text)
                    adb.adb_close_keyboard(d_serial)
                # Long click
                elif ui_element.longClickable:
                    ui_element.long_click.wait()
                # Click or check
                elif ui_element.clickable or ui_element.checkable:
                    ui_element.click.wait()
                # Scroll
                elif ui_element.scrollable:
                    ui_element.swipe.up(steps=10).wait()
                else:
                    self._graphs[d_serial].remove_node(node)
                    return
                self._update_attr(d_serial, node, "visited", True)
            else:
                self._update_attr(d_serial, node, "difference", "deleted")
      
        sleep(1)
        prev = node.split(conf.DELIMITER)[0]
        curr = adb.get_foreground_activity_name(d_serial)
        self.allow_permission_popup(d_serial)
        return prev == curr
            
