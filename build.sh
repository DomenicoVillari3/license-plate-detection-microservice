#!/bin/bash

cd Writer
docker build -t img_writer .
cd ..
cd Reader
docker build -t img_reader .
cd ..
cd Recognition
docker build -t img_rec .

