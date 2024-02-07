#!/bin/bash

source_folder="build"
master_dest_folder="/prog/Argos"
node_dest_folder="~/Argos"
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

echo "$ GLOBIGNORE=argos.py:src:configs:realsense_so:requirements.txt"
GLOBIGNORE=argos.py:src:configs:realsense_so:requirements.txt

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

echo "$ rm -r -f __pycache__"
rm -r -f */__pycache__

echo "$ cd .."
cd ..

deploy to host
echo
echo -e "$blue"Deploying to machines..."$reset"
echo

read -sp "Password: " password
echo
echo

echo "$ ssh $ssh_addr \"/home/thales/.forward_ipv4.sh\""
{
ssh $ssh_addr "echo ${password} | /home/thales/.forward_ipv4.sh"
} > /dev/null 2>/dev/null

echo "$ ssh $ssh_addr \"rm -r -f $master_dest_folder\""
ssh $ssh_addr "rm -r -f $master_dest_folder"

echo "$ ssh $ssh_addr \"mkdir $master_dest_folder\""
ssh $ssh_addr "mkdir $master_dest_folder"

echo "$ scp -T -r ./$source_folder/* $ssh_addr:$master_dest_folder"
scp -T -r ./$source_folder/* "$ssh_addr:$master_dest_folder"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts rm -r -f $node_dest_folder\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts rm -r -f $node_dest_folder"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts mkdir $node_dest_folder\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts mkdir $node_dest_folder"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts cp -r $master_dest_folder/* $node_dest_folder\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts cp -r $master_dest_folder/* $node_dest_folder"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts python -m venv $node_dest_folder/venv\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts python -m venv $node_dest_folder/venv"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts $node_dest_folder/venv/bin/pip install -r $node_dest_folder/requirements.txt\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_pssh_hosts $node_dest_folder/venv/bin/pip install -r $node_dest_folder/requirements.txt"

# remove deployment folder
echo
echo -e "$blue"Removing build folder..."$reset"
echo

echo "$ rm -r -f $source_folder"
rm -r -f $source_folder

echo
echo -e "$green"Deployment finished!"$reset"
echo