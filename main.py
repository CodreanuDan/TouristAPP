#***********************************************************************
# MODULE: main
# SCOPE:  Main file of the program
# REV: 1.0
# Created by: Codreanu Dan

#***********************************************************************
# IMPORTS:
import streamlit as st
import pandas as pd
import numpy
import requests
from tenacity import retry, stop_after_attempt
import json
import time
from dataclasses import dataclass
from datetime import datetime
import os
import subprocess
import tomllib
import requests_cache
import signal
import threading

from graphical_interface import Streamlit_GUI as gui
from api_handlers import OpenMeteoHdl as open_meteo
from api_handlers import OpenMeteoHdl as open_sTmap


#***********************************************************************
# CONTENT: Program
# INFO: Main instance of the project 
class Program(gui):
    """ 
        :Class name: Program
        :Descr: Main instance of the project 
        :Inherits from: Streamlit_GUI
    """
    def __init__(self):
        super().__init__()
        # "main.py" file path 
        self.main_file_path = os.path.join(os.path.dirname(__file__), "main.py")
        # Aux file to check if streamlit started
        self.lock_file_path = os.path.join(os.path.dirname(__file__), ".streamlit_lock")
        # Run streamlit
        self.__run_streamlit(self.main_file_path)
    
    #***********************************************************************
    """ 
        This block of functions is used for Streamlit service runtime operations:
        Run Streamlit: 1.start service -> create lock file;
                       2.monitor state, if CTRL+C then: delete lockfile
    """
    def __run_streamlit(self, file_path):
        """ 
        Run streamlit only once, based on a lock file check.
                :param:  file_path; main.py file
                :return: None.
        """
        if not os.path.exists(self.lock_file_path):
            # Create lock file to signal that the app already started
            open(self.lock_file_path, 'w').close()
            try:
                self.__start_streamlit(file_path)
                self.__start_signal_listener()
            finally:
                # Ensure cleanup occurs even if an error happens
                self.__lockFile_cleanup()
        else:
            print("[✅][main.py/Program/__run_streamlit] --> Streamlit app is already running. Skipping...")
            
    def __start_signal_listener(self):
        """ 
            Start listening for signals in a separate thread
                :remark: it may be redundant, i don`t know if it handles something ?
        """
        signal.signal(signal.SIGINT, self.__handle_interrupt)
        # Wait for signal to be triggered
        signal.pause()  
        
    def __start_streamlit(self, file_path:str):
        """
            Run command to start streamlit
                :param:  file_path; main.py file
                :return: None.
        """
        command = ["streamlit", "run", file_path]
        arguments = []
        try:
            self.streamlit_process =subprocess.run(command + arguments, check=True)
        except Exception as e :
            print(f"[❌][main.py/Program/__start_streamlit] --> Error at running {file_path}, err msg: {e}!")
        else:
            print("[✅][main.py/Program/__start_streamlit] --> Streamlit app started successfully.")
            
    def __lockFile_cleanup(self):
        """ Remove lock file after app is finished"""
        if os.path.exists(self.lock_file_path):
            os.remove(self.lock_file_path)
            print("[✅][main.py/Program/__lockFile_cleanup] --> Streamlit lock file removed.")
            
    def __handle_interrupt(self, sig, frame):
        """ Handle CTRL+C to cleanup and stop streamlit """
        print("[❗][main.py/Program/__handle_interrupt] --> CTRL+C detected. Cleaning up...")
        self.__lockFile_cleanup()
        # Terminate Streamlit thread
        if hasattr(self, 'streamlit_process'):
            self.streamlit_process.terminate() 
            print("[✅][main.py/Program/__handle_interrupt] --> Streamlit process terminated.")
        exit(0)
        
#***********************************************************************
# DBG_AREA:
if __name__ == "__main__":
    pr = Program()
    print(f"[🪲][DEBUG][<main.py>] Testing main.py...")





