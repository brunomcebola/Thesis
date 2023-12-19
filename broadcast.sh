#!/bin/bash

source_folder="/home/thales/Desktop/Argos"
dest_folder="/home/thales/Argos"

yellow='\033[1;33m'
reset='\033[0m'

echo -e "$yellow"Entered in argos-master bash..."$reset"
echo

echo "$ ssh rpi2 \"rm -r -f $dest_folder\""
ssh rpi2 "rm -r -f $dest_folder"

echo "$ ssh rpi2 \"mkdir $dest_folder\""
ssh rpi2 "mkdir $dest_folder"

echo "$ scp -T -r $source_folder/* rpi2:$dest_folder"
scp -T -r $source_folder/* "rpi2:$dest_folder"

echo "$ ssh rpi2 \"rm $dest_folder/broadcast.sh\""
ssh rpi2 "rm $dest_folder/broadcast.sh"

echo "$ ssh \"python -m venv $dest_folder/venv\""
ssh rpi2 "python -m venv $dest_folder/venv"

echo "$ ssh rpi2 \"$dest_folder/venv/bin/pip install -r $dest_folder/requirements.txt\""
ssh rpi2 "$dest_folder/venv/bin/pip install -r $dest_folder/requirements.txt"

echo
echo -e "$yellow"Exited argos-master bash..."$reset"