import cv2
import pytesseract
import logging
import sys
import os
import threading
from flask import Flask,request,make_response
from flask_api import status
from werkzeug.utils import secure_filename
import requests
from datetime import datetime
import time

class Recognition:
    
    def __init__(self, static_files_detection, logging_path, verbosity, host, port, mutex) -> None:
        self.__static_files_detection = static_files_detection
        self.__verbosity=verbosity
        self.__flaskServer = None
        self.__detection= None
        self.__mutex= mutex
        self.__setup_logging(verbosity, logging_path)

    
    def __setup_logging(self, verbosity, path):
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s" #formato del messaggio
        filename = path
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.INFO
        if (self.__verbosity):
            level = logging.DEBUG
        
        ''' definisco un oggetto console handler tramite la classe logging.Streamhandler
         setto il livello del log, ed utilizzo metodo setformatter per definire il formato dei messaggi da stampare
          nel file di log   '''      

        logging.basicConfig(filename=filename, filemode='a', format=format, level=level, datefmt=datefmt)
    
    def setup(self):
        if not os.path.exists(self.__static_files_detection):
            os.makedirs(self.__static_files_detection)
        
        
        if not os.path.exists("/opt/app/static-files/detected.txt"):
            current_directory = os.getcwd()
            directory = "/opt/app/static-files"
            os.chdir(directory)
            f = open("detected.txt", "w")
            f.close()
            os.chdir(current_directory)
        
        self.__detection = threading.Thread(
            target = self.__detection_job, 
            args = ()
        )


    def  __detection_job(self):
        while True:
                if not self.__detected_folder_is_empty() and self.__oldest():
                    oldest_frame_path = self.__oldest()
                    frame =  self.__get_frame(oldest_frame_path)
                    frame_name = os.path.basename(oldest_frame_path)
                    text = pytesseract.image_to_string(frame, lang="eng")
                    text = text.replace(" ", "")
                    text = text.replace("\n", "")
                    if len(text)>1:
                        current_directory=os.getcwd()
                        os.chdir("/opt/app/static-files")
                        file = open("detected.txt","a")
                        file.write(text+"-"+frame_name+"-"+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"\n \n ")
                        file.close()
                        os.chdir(current_directory)
                        os.chdir(self.__static_files_detection)
                        os.rename(frame_name,"detected_"+frame_name)
                        os.chdir(current_directory)
                    else:
                        current_directory=os.getcwd()
                        os.chdir(self.__static_files_detection)
                        os.rename(frame_name,"not_detected_"+frame_name)
                        os.chdir(current_directory)
                time.sleep(0.4)
    
    def __detected_folder_is_empty(self):
        path = self.__static_files_detection
        return True if not len(os.listdir(path)) else False
    
    def __oldest(self):
        path = self.__static_files_detection
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files if "crop_" in basename and "detected_" not in basename]
        if paths:
            return min(paths, key=os.path.getctime)
        else:
            return 0

    def __get_frame(self, filename):
        """ Read image from file using opencv.

            Args:
                filename(str): relative or absolute path of the image

            Returns:
                (numpy.ndarray) frame read from file 
        """
        return cv2.imread(filename)

    def start(self):
        self.__detection.start()
