# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This implementation does its best to follow the Robert Martin's Clean code guidelines.
The comments follows the Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'Writer class'


'''
Import delle seguenti dipendze
Flask
Flask-API
wekzeug
'''

import os
import sys
import logging
import threading
import requests
from flask_api import status
from flask import Flask, request, make_response
from werkzeug.utils import secure_filename
import socket

'''definizione della classe writer'''

class Writer:
    
    __ALLOWED_EXTENSIONS = {
        'png',
        'jpg',
        'jpeg'
    }

    '''definizione cpstruttore della classe'''
    def __init__(self, host, port, static_files, mutex, verbosity, logging_path) -> None:
        self.__host = host
        self.__port = port
        self.__static_files = static_files
        self.__mutex = mutex
        self.__writer = None
        self.__verbosity = verbosity
        self.__setup_logging(verbosity, logging_path)
    

    '''vado a definire il formato delle info inserite nel file di log'''
    def __setup_logging(self, verbosity, path):
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s" #formato del messaggio
        filename = path
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.INFO
        if (verbosity):
            level = logging.DEBUG
        
        ''' definisco un oggetto console handler tramite la classe logging.Streamhandler
         setto il livello del log, ed utilizzo metodo setformatter per definire il formato dei messaggi da stampare
          nel file di log   '''

        logging.basicConfig(filename=filename, filemode='a', format=format, level=level, datefmt=datefmt)

    def setup(self):
        if not os.path.exists(self.__static_files): #se non esiste il path 
            os.makedirs(self.__static_files)    #lo crea tramite makedirs

        '''crea 1 thread che richiama il metodo writer_job e passo i parametri tramite args '''
        self.__writer = threading.Thread(       
            target = self.__writer_job, 
            args = (self.__host, self.__port, self.__verbosity)
        )
        
    def __writer_job(self, host, port, verbosity):
        app = Flask(__name__)

        app.add_url_rule('/api/v1/frame-upload', 'frame-upload', self.__frame_upload, methods=['POST'])

        app.run(host=host, port=port, debug=verbosity, threaded=True, use_reloader=False)
    
    def get_ip(self):
        current_ip = socket.gethostbyname(socket.gethostname())
        ip_parts = current_ip.split('.')
        last_digit = int(ip_parts[-1])
        last_digit += 1
        last_digit = last_digit % 256
        ip_parts[-1] = str(last_digit)
        ip_parts = '.'.join(ip_parts)
        return ip_parts
        
    def __frame_upload(self):
        if request.method == 'POST': #controllliamo se è stata effettuata una richiesta di post
            if 'upload' not in request.files: #controllo se il campo upload è richiesto
                response = make_response("File not found", status.HTTP_400_BAD_REQUEST) 
            file = request.files['upload']
            if file and self.__allowed_file(file.filename):
                filename = secure_filename(file.filename) 
                absolute_path = '%s/%s' % (self.__static_files, filename) # self.__static_files rappresenta la directory in cui verrà salvato il file. POTENTIAL_STATIC_FILE
                self.__mutex.acquire() #prendo il mutex
                file.save(absolute_path)    #faccio la scrittura
                self.__mutex.release() #rilascia il mutex
                ip_reader = self.get_ip()
                test_file=open(absolute_path,'rb')
                test_url = "http://"+ip_reader+":8080/api/v1/frame-download"
                test_response = requests.post(test_url, files = {"form_field_name": test_file})
                print(test_response)
                response = make_response("File is stored", status.HTTP_201_CREATED)
            return response

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.__ALLOWED_EXTENSIONS


    def start(self):
        self.__writer.start()