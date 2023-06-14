FROM ubuntu:latest

LABEL maintainer="Lorenzo Carnevale <lcarnevale@unime.it>" \
      name="Plate Detection Microservice" \
      description="Docker container for running a plate detection microservice" \
    #   url="https://hub.docker.com/r/petronetto/pytorch-alpine" \
    #   vcs-url="https://github.com/petronetto/pytorch-alpine" \
      vendor="University of Messina" \
      version="1.0"

RUN echo "|--> Updating"
RUN  apt update -y
RUN  apt upgrade -y
RUN echo "|--> Install Python basics" 
RUN apt install -y python3.10
RUN apt install -y python3-pip
#RUN pip3 install xyz --break-system-packages
#RUN pip3 install --upgrade pip

COPY requirements.txt /opt/app/requirements.txt

WORKDIR /opt/app

RUN echo "|--> Install dependencies"; 
RUN apt install -y libgl1 libglib2.0-0
RUN pip3 install -r requirements.txt

COPY app /opt/app

EXPOSE 8080

CMD ["python3", "main.py", "-c", "config.yaml", "-v"]