FROM ubuntu:latest

RUN echo "|--> Updating"
RUN  apt update -y
RUN  apt upgrade -y
RUN echo "|--> Install Python basics" 
RUN apt install -y python3.10
RUN apt install -y python3-pip
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN apt install -y libjpeg-dev



COPY requirements.txt /opt/app/requirements.txt

WORKDIR /opt/app

RUN echo "|--> Install dependencies"; 
RUN apt install -y libgl1 libglib2.0-0
RUN pip3 install -r requirements.txt

COPY app /opt/app

EXPOSE 8080

CMD ["python3", "main.py", "-c", "config.yaml", "-v"]