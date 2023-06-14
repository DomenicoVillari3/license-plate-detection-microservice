#!/bin/bash


host=$2
port=$3


# Percorso della cartella locale contenente le immagini
image_folder=$1
# Itera attraverso ogni file nella cartella delle immagini
for file in "$image_folder"/*; do
    # Controlla se il file è un file regolare
    if [ -f "$file" ]; then
        echo "Invio del file: $file"

        # Esegue lo script upload-file.sh per inviare il file alla pipeline
        ./upload-file.sh $file $host $port
        sleep 0.5
    fi
done
