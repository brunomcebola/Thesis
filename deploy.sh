#!/bin/bash

source_folder="build"
dest_folder="/home/thales/Desktop/Argos"
ssh_addr="thales@argos-master"

blue='\033[1;34m'
green='\033[1;32m'
reset='\033[0m'

# creating build folder
echo
echo -e "$blue"Creating build folder..."$reset"
echo

echo "$ rm -r -f $source_folder"
rm -r -f $source_folder

echo "$ mkdir $source_folder"
mkdir $source_folder

echo "$ GLOBIGNORE=$source_folder"
GLOBIGNORE=$source_folder

echo "$ cp -r * $source_folder"
cp -r * $source_folder

echo "$ unset GLOBIGNORE"
unset GLOBIGNORE

echo "$ cd $source_folder"
cd $source_folder

# remove unnecessary files and folders
echo
echo -e "$blue"Removing unnecessary files and folders..."$reset"
echo

echo "$ GLOBIGNORE=argos.py:helpers:modes:configs:realsense_so:requirements.txt:broadcast.sh"
GLOBIGNORE=argos.py:helpers:modes:configs:realsense_so:requirements.txt:broadcast.sh

echo "$ rm -r -f *"
rm -r -f *

echo "$ unset GLOBIGNORE"
unset GLOBIGNORE

# extracting .so files
echo
echo -e "$blue"Extracting .so files..."$reset"
echo

echo "$ mv realsense_so/*.so ."
mv realsense_so/*.so .

echo "$ rm -r -f realsense_so"
rm -r -f realsense_so

# remove pycache
echo
echo -e "$blue"Removing pycache..."$reset"
echo

echo "$ cd helpers"
cd helpers

echo "$ rm -r -f __pycache__"
rm -r -f __pycache__

echo "$ cd ../modes"
cd ../modes

echo "$ rm -r -f __pycache__"
rm -r -f __pycache__

echo "$ cd ../.."
cd ../..

# deploy to host
echo
echo -e "$blue"Deploying to host..."$reset"
echo

echo "$ ssh $ssh_addr \"rm -r -f $dest_folder\""
ssh $ssh_addr "rm -r -f $dest_folder"

echo "$ ssh $ssh_addr \"mkdir $dest_folder\""
ssh $ssh_addr "mkdir $dest_folder"

echo "$ scp -T -r ./$source_folder/* $ssh_addr:$dest_folder"
scp -T -r ./$source_folder/* "$ssh_addr:$dest_folder"

echo
echo -e "$blue"Broadcasting to nodes..."$reset"
echo

echo "$ ssh $ssh_addr \"chmod 777 $dest_folder/broadcast.sh\""
ssh $ssh_addr "chmod 777 $dest_folder/broadcast.sh"

echo "$ ssh $ssh_addr \"$dest_folder/broadcast.sh\""
echo
ssh $ssh_addr "$dest_folder/broadcast.sh"

# remove deployment folder
echo
echo -e "$blue"Removing build folder..."$reset"
echo

echo "$ rm -r -f $source_folder"
rm -r -f $source_folder

echo
echo -e "$blue"Deployment finished!"$reset"
echo