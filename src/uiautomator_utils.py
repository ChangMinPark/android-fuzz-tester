#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

from xml.etree import ElementTree as ET

def get_current_tree(xml: str) -> ET.Element:
    '''
    Get current UI tree from xml
    '''
    tree = ET.fromstring(xml)
    return tree

def get_clickable_list(tree: ET.Element) -> list:
    '''
    From UI trees, find clickable UIs and return
    '''
    ui_dics = []
    for node in tree.iter("node"):
        if node.attrib['clickable'] == "false":
            continue

        """
        Do not add the three UIs in the list
        {'contentDescription': 'Back', 
         'resourceId': 'com.android.systemui:id/back', 
         'className': 'android.widget.ImageView', ...}
        {'contentDescription': 'Home', 
         'resourceId': 'com.android.systemui:id/home', 
         'className': 'android.widget.ImageView', ...}
        {'contentDescription': 'Overview', 
         'resourceId': 'com.android.systemui:id/recent_apps', 
         'className': 'android.widget.ImageView',...}
        """
        if 'com.android.systemui:id/back' in node.attrib['resource-id'] \
        or 'com.android.systemui:id/home' in node.attrib['resource-id'] \
        or 'com.android.systemui:id/recent_apps' in node.attrib['resource-id']:
            continue
        ui_dics.append({
            "resourceId": node.attrib['resource-id'],
            "className": node.attrib['class'],
            "text": node.attrib['text'],
            "contentDescription": node.attrib['content-desc'],
            "bounds": node.attrib['bounds']})    
    return ui_dics
