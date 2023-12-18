#!/bin/bash

source="build"
dest="~/Desktop/Argos"

blue='\033[1;34m'
green='\033[1;32m'
reset='\033[0m'

# creating build folder
echo
echo -e "$blue"Creating build folder..."$reset"
echo

echo "$ rm -r -f $source"
rm -r -f $source

echo "$ mkdir $source"
mkdir $source

echo "$ GLOBIGNORE=$source"
GLOBIGNORE=$source

echo "$ cp -r * $source"
cp -r * $source

echo "$ unset GLOBIGNORE"
unset GLOBIGNORE

echo "$ cd $source"
cd $source

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

echo "$ ssh thales@argos-master \"rm -r -f $dest\""
ssh thales@argos-master "rm -r -f $dest"

echo "$ ssh thales@argos-master \"mkdir $dest\""
ssh thales@argos-master "mkdir $dest"

echo "$ scp -T -r ./$source/* thales@argos-master:$dest"
scp -T -r ./$source/* "thales@argos-master:$dest"

echo
echo -e "$blue"Broadcasting to nodes..."$reset"
echo

echo "$ ssh thales@argos-master \"chmod 777 $dest/broadcast.sh\""
ssh thales@argos-master "chmod 777 $dest/broadcast.sh"

echo "$ ssh thales@argos-master \"$dest/broadcast.sh\""
ssh thales@argos-master "$dest/broadcast.sh"


# remove deployment folder
echo
echo -e "$blue"Removing build folder..."$reset"
echo

echo "$ rm -r -f $source"
rm -r -f $source

echo
echo -e "$green"Deployment finished successfully!"$reset"
echo