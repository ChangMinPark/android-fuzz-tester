#!/usr/bin/env python3.7
'''
@author: Chang Min Park (cpark22@buffalo.edu)
'''

import logging as lg
import sys
import src.config as conf

class Logger:
    _instance = None

    @staticmethod
    def get_instance():
        if Logger._instance == None:
            Logger()
        return Logger._instance

    def __init__(self):
        if Logger._instance != None:
            raise Exception("Singleton class cannot be instantiated more \
                    than once.")
        lg.basicConfig(filename='log.log', level=lg.NOTSET)
        self._logger = lg.getLogger()

        s_handler = lg.StreamHandler(sys.stdout)
        s_handler.setLevel(lg.DEBUG if conf.LOGGER_VERBOSE else lg.INFO)
        formatter = lg.Formatter('%(asctime)s - %(levelname)s : %(message)s')
        s_handler.setFormatter(formatter)
        self._logger.addHandler(s_handler)
        Logger._instance = self

    def info(self, msg: str) -> None:
        self._logger.info(msg)

    def debug(self, msg: str) -> None:
        self._logger.debug(msg)

    def warning(self, msg: str) -> None:
        self._logger.warning(msg)
