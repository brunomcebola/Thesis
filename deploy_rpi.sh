#!/bin/bash

whl_file="argos-1.0.0-py3-none-any.whl"
setup_file="setup_rpi.py"

ssh_addr="argos-master"

master_folder="/rpi/shared/whl"
rpi_folder="/home/thales/Argos"

blue='\033[1;34m'
green='\033[1;32m'
reset='\033[0m'

echo

echo -e "$green"Deployment to rpi\'s started!"$reset"
echo

# remove previous build folder
echo -e "$blue"Removing previous build folder..."$reset"
echo

echo "$ rm -f ./dist/*"
rm -d ./dist/*

# generate distribution files
echo -e "$blue"Generating distribution files..."$reset"
echo

echo "$ python $setup_file sdist bdist_wheel"
python $setup_file sdist bdist_wheel

# deploy to cluster
echo
echo -e "$blue"Deploying to the rpi\'s..."$reset"
echo

echo "$ ssh $ssh_addr \"rm -f $master_folder/*.whl\""
ssh $ssh_addr "rm -f $master_folder/*.whl"

echo "$ scp -T -r ./dist/$whl_file $ssh_addr:$master_folder"
scp -T -r ./dist/$whl_file $ssh_addr:$master_folder

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts $rpi_folder/pip install --force-reinstall $rpi_folder/whl/$whl_file\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts $rpi_folder/pip install --force-reinstall $node_folder/whl/$whl_file"

echo
echo -e "$green"Deployment finished!"$reset"
echo
