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

class Recognition:
    
    def __init__(self, static_files_detection, logging_path, verbosity, host, port, mutex) -> None:
        self.__static_files_detection = static_files_detection
        self.__host = host
        self.__port = port
        self.__verbosity=verbosity
        self.__flaskServer = None
        self.__detection= None
        self.__mutex= mutex
        self.__setup_logging(verbosity, logging_path)

    
    def __setup_logging(self, verbosity, path):
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s" #formato del messaggio
        #filename = path
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.INFO
        if (verbosity):
            level = logging.DEBUG
        
        ''' definisco un oggetto console handler tramite la classe logging.Streamhandler
         setto il livello del log, ed utilizzo metodo setformatter per definire il formato dei messaggi da stampare
          nello stdout   '''
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(format,datefmt))

        logging.basicConfig(stream=sys.stdout, format=format, level=level, datefmt=datefmt)
    
    def setup(self):
        if not os.path.exists(self.__static_files_detection):
            os.makedirs(self.__static_files_detection)
        '''
        else:
            path = self.__static_files_detection
            for file_name in os.listdir(path):
                if file_name != "detected.txt":
                    # construct full file path
                    file = path + file_name
                    if os.path.isfile(file):
                        os.remove(file)
        '''
        
        if not os.path.exists("/opt/app/static-files/detected.txt"):
            current_directory = os.getcwd()
            directory = "/opt/app/static-files"
            os.chdir(directory)
            f = open("detected.txt", "w")
            f.close()
            os.chdir(current_directory)
        print('creo i thread')
        '''self.__flaskServer=threading.Thread(
            target=self.__receive,
            args=(self.__host, self.__port, self.__verbosity)
            )'''
        
        self.__detection = threading.Thread(
            target = self.__detection_job, 
            args = ()
        )
        #print('avvio server')
        #self.__flaskServer.start()

    def  __detection_job(self):
        while True:
            if not self.__detected_folder_is_empty() and self.__newest():
                self.__mutex.acquire()
                newest_frame_path = self.__newest()
                frame =  self.__get_frame(newest_frame_path)
                frame_name = os.path.basename(newest_frame_path)
                print("scrivo il testo")
                text = pytesseract.image_to_string(frame, lang="eng")
                print("testo:",text)
                current_directory=os.getcwd()
                os.chdir("/opt/app/static-files")
                file = open("detected.txt","a")
                file.write(text+"-"+frame_name+"-"+datetime.now().strftime("%d/%m/%Y")+"\n \n ")
                file.close()
                os.chdir(current_directory)
                os.chdir(self.__static_files_detection)
                os.rename(frame_name,"detected_"+frame_name)
                os.chdir(current_directory)
                #os.remove(newest_frame_path)
                self.__mutex.release()

                
    def __receive(self, host, port, verbosity):
        print('blocco per la prima volta mutex')
        self.__mutex.acquire()
        print('mutex acquisito dal server e metto in ascolto')
        app = Flask(__name__)
        app.add_url_rule('/api/v1/detected-frame-download', 'detected-frame-download', self.__detected_frame_download, methods=['POST'])
        app.run(host, port, verbosity, threaded=True, use_reloader=False)
        

    def __detected_frame_download(self):
        if not self.__detected_folder_is_empty():
            print('secondo lock')
            self.__mutex.acquire()
        if request.method == 'POST': #controllliamo se è stata effettuata una richiesta di post
            if 'file-detected' not in request.files: #controllo se il campo upload è richiesto
                response = make_response("File not found", status.HTTP_400_BAD_REQUEST) 
                print ('ERRORE')
            print('salvo file inviato da reader')
            file = request.files['file-detected']
            print("/n file ",file,"filename ",file.filename)
            filename = secure_filename(file.filename) 
            absolute_path = '%s/%s' % (self.__static_files_detection, filename) # self.__static_files rappresenta la directory in cui verrà salvato il file. POTENTIAL_STATIC_FILE
            file.save(absolute_path)    #faccio la scrittura
            print('flask rilascia il mutex')
            self.__mutex.release()
            print('aspetto la detection')
    
    def __detected_folder_is_empty(self):
        path = self.__static_files_detection
        return True if not len(os.listdir(path)) else False
    
    def __newest(self):
        path = self.__static_files_detection
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files if "crop_" in basename and "detected_" not in basename]
        if paths:
            return max(paths, key=os.path.getctime)
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