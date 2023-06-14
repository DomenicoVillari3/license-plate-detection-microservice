# License Plate Detection - Microservices

**Automatic Number Plate Recognition** (ANPR) is the process of reading the characters on the plate with various **optical character recognition** (OCR) methods by separating the plate region on the vehicle image obtained from automatic plate recognition.

This repository forks the [Automatic_Number_Plate_Recognition_YOLO_OCR
](https://github.com/mftnakrsu/Automatic_Number_Plate_Recognition_YOLO_OCR) one by [mftnakrsu](https://github.com/mftnakrsu) to extract the license plate detection methods, adds the license plate characters recognition and create a microservices deployable as Docker containers.

## How to Build
Run the *build.sh* script.

```bash
chmod +x build.sh
./build.sh
```

## How to Run
Run the *run.sh* script.

```bash
chmod +x run.sh
./run.sh
```

## How to upload image
To upload a single image run the *upload-file.sh* script.

```bash
chmod +x upload-file.sh
./upload-file.sh /path/file 0.0.0.0 5001
```
To upload multiple images from a folder run the *upload-files.sh* script.

```bash
chmod +x upload-files.sh
./upload-files.sh /path/folder 0.0.0.0 5001
```

## How to see logs
The filename is custom and it can be modified in the configuration file.
```bash
tail -f ~/log/platedetection/license-plate-detection.log
```
## How to see recognised plates
The filename is custom and it can be modified in the configuration file.
```bash
tail -f ~/static-files/detected.txt
```



