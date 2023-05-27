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
__description__ = 'Reader class'

import os
import sys
import cv2
import time
import torch
import logging
import threading
import numpy as np
from PIL import Image
import torch.backends.cudnn as cudnn
from models.experimental import attempt_load
from utils.general import non_max_suppression
from utils.params import Parameters
from flask import Flask,request,make_response
from flask_api import status
from werkzeug.utils import secure_filename

class Reader:

    def __init__(self, static_files_potential, static_files_detection, model_path, mutex, verbosity, logging_path) -> None:
        self.__static_files_potential = static_files_potential
        self.__static_files_detection = static_files_detection
        self.__mutex = mutex
        self.__reader = None
        self.__flaskServer= None
        self.__params = Parameters(model_path)
        self.__model, self.__labels = self.__load_yolov5_model()
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
        if not os.path.exists(self.__static_files_potential):
            os.makedirs(self.__static_files_potential)

        print("creo il thread")
        self.__flaskServer=threading.Thread(
            target=self._receive,
            args=('0.0.0.0','8080',True)
            )
        
        self.__reader = threading.Thread(
            target = self.__reader_job, 
            args = ()
        )

        print('inizio dal flask server ')
        self.__flaskServer.start()


    def __reader_job(self):
        while True:
            #self._receive('0.0.0.0','8080',True)
            if not self.__potential_folder_is_empty():
                self.__mutex.acquire()
                print('inizio reading ')
                print("acquisizione lock da parte del reading ")
                
                oldest_frame_path = self.__oldest()

                print('FILE: ',oldest_frame_path)
                frame =  self.__get_frame(oldest_frame_path)
                detected, _ = self.__detection(frame, self.__model, self.__labels)
                os.remove(oldest_frame_path)

                #self.__mutex.release()
                image = Image.fromarray(detected)
                filename = os.path.basename(oldest_frame_path)
                absolute_path = '%s/%s' % (self.__static_files_detection, filename)
                image.save(absolute_path)
                time.sleep(0.1)       
                print('rilascio mutex ')
                print('ridò controllo a flask')
                self.__mutex.release()

    def _receive(self,host,port,verbosity):
        self.__mutex.acquire()
        print('mutex acquisito dal server e metto in ascolto')
        app = Flask(__name__)
        app.add_url_rule('/api/v1/frame-download', 'frame-download', self.__frame_download, methods=['POST'])
        print(host, port)
        app.run(host=host, port=port, debug=verbosity, threaded=True, use_reloader=False)


    def __frame_download(self):
        if not self.__detected_folder_is_empty():
            self.__mutex.acquire()
        if request.method == 'POST': #controllliamo se è stata effettuata una richiesta di post
            if 'form_field_name' not in request.files: #controllo se il campo upload è richiesto
                response = make_response("File not found", status.HTTP_400_BAD_REQUEST) 
                print ('ERRORE')
            print('salvo file inviato da writer')
            file = request.files['form_field_name']
            print("/n file ",file,"filename ",file.filename)
            filename = secure_filename(file.filename) 
            absolute_path = '%s/%s' % (self.__static_files_potential, filename) # self.__static_files rappresenta la directory in cui verrà salvato il file. POTENTIAL_STATIC_FILE
            #self.__mutex.acquire() #prendo il mutex
            file.save(absolute_path)    #faccio la scrittura
            #self.__mutex.release() #rilascia il mutex
            response = make_response("File is stored", status.HTTP_201_CREATED)
            print('flask rilascia il mutex')
            self.__mutex.release()
            print('aspetto il reader')
          
            


    def __potential_folder_is_empty(self):
        path = self.__static_files_potential
        return True if not len(os.listdir(path)) else False
    
    def __detected_folder_is_empty(self):
        path = self.__static_files_detection
        return True if not len(os.listdir(path)) else False

    def __oldest(self):
        path = self.__static_files_potential
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files]
        return min(paths, key=os.path.getctime)

    def __load_yolov5_model(self):
        """
        It loads the model and returns the model and the names of the classes.
        :return: model, names
        """
        model = attempt_load(self.__params.model, map_location=self.__params.device)
        print("device",self.__params.device)
        stride = int(model.stride.max())  # model stride
        names = model.module.names if hasattr(model, 'module') else model.names  # get class names

        return model, names

    def __get_frame(self, filename):
        """ Read image from file using opencv.

            Args:
                filename(str): relative or absolute path of the image

            Returns:
                (numpy.ndarray) frame read from file 
        """
        return cv2.imread(filename)

    def __detection(self, frame, model, names):
        """
        It takes an image, runs it through the model, and returns the image with bounding boxes drawn around
        the detected objects
        
        :param frame: The frame of video or webcam feed on which we're running inference
        :param model: The model to use for detection
        :param names: a list of class names
        :return: the image with the bounding boxes and the label of the detected object.
        """
        out = frame.copy()

        frame = cv2.resize(frame, (self.__params.pred_shape[1], self.__params.pred_shape[0]), interpolation=cv2.INTER_LINEAR)
        frame = np.transpose(frame, (2, 1, 0))


        cudnn.benchmark = True  # set True to speed up constant image size inference

        if self.__params.device.type != 'cpu':
            model(torch.zeros(1, 3, self.__params.imgsz, self.__params.imgsz).to(self.__params.device).type_as(next(model.parameters())))  # run once

        frame = torch.from_numpy(frame).to(self.__params.device)
        frame = frame.float()
        frame /= 255.0
        if frame.ndimension() == 3:
            frame = frame.unsqueeze(0)

        frame = torch.transpose(frame, 2, 3)


        pred = model(frame, augment=False)[0]
        pred = non_max_suppression(pred, self.__params.conf_thres, max_det=self.__params.max_det)

        label=""
        # detections per image
        for i, det in enumerate(pred):

            img_shape = frame.shape[2:]
            out_shape = out.shape

            s_ = f'{i}: '
            s_ += '%gx%g ' % img_shape  # print string

            if len(det):

                gain = min(img_shape[0] / out_shape[0], img_shape[1] / out_shape[1])  # gain  = old / new

                coords = det[:, :4]


                pad = (img_shape[1] - out_shape[1] * gain) / 2, (
                        img_shape[0] - out_shape[0] * gain) / 2  # wh padding

                coords[:, [0, 2]] -= pad[0]  # x padding
                coords[:, [1, 3]] -= pad[1]  # y padding
                coords[:, :4] /= gain

                coords[:, 0].clamp_(0, out_shape[1])  # x1
                coords[:, 1].clamp_(0, out_shape[0])  # y1
                coords[:, 2].clamp_(0, out_shape[1])  # x2
                coords[:, 3].clamp_(0, out_shape[0])  # y2

                det[:, :4] = coords.round()

                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s_ += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                for *xyxy, conf, cls in reversed(det):

                    x1 = int(xyxy[0].item())
                    y1 = int(xyxy[1].item())
                    x2 = int(xyxy[2].item())
                    y2 = int(xyxy[3].item())

                    confidence_score = conf
                    class_index = cls
                    object_name = names[int(cls)]
                    
                    crop_name=self.__oldest()
                    crop_name = os.path.basename(crop_name)
                    current_directory = os.getcwd()
                    directory = self.__static_files_detection
                    os.chdir(directory)
                    detected_plate = frame[:,:,y1:y2, x1:x2].squeeze().permute(1, 2, 0).cpu().numpy()
                    crop = out[y1:y2, x1:x2]
                    print(crop,' crop')
                    print(detected_plate,' detected plate')
                    cv2.imwrite("crop_"+crop_name, crop)
                    os.chdir(current_directory)

                    #rect_size= (detected_plate.shape[0]*detected_plate.shape[1])
                    c = int(cls)  # integer class
                    label = names[c] if self.__params.hide_conf else f'{names[c]} {conf:.2f}'

                    tl = self.__params.rect_thickness

                    c1, c2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
                    cv2.rectangle(out, c1, c2, self.__params.color, thickness=tl, lineType=cv2.LINE_AA)

                    if label:
                        tf = max(tl - 1, 1)  # font thickness
                        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
                        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                        cv2.rectangle(out, c1, c2, self.__params.color, -1, cv2.LINE_AA)  # filled
                        cv2.putText(out, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf,
                                    lineType=cv2.LINE_AA)

        return out, label

    
    def start(self):
        self.__reader.start()
