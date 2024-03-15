#!/bin/bash

build_folder="build"
ssh_addr="argos-master"
dest_folder="/rpi/shared/Argos"
node_folder="/home/thales/Argos"

blue='\033[1;34m'
green='\033[1;32m'
reset='\033[0m'

echo
echo -e "$green"Deployment started!"$reset"
echo

# creating build folder
echo -e "$blue"Creating build folder..."$reset"
echo

echo "$ rm -rf $build_folder"
rm -rf $build_folder

echo "$ mkdir $build_folder"
mkdir $build_folder

# copy files and dirs into build folder
echo
echo -e "$blue"Copying files and dirs into build folder..."$reset"
echo

echo "$ cat deploy.txt | xargs -I % cp -r % $build_folder"
cat deploy.txt | xargs -I % cp -r % $build_folder

# enter build folder
echo
echo -e "$blue"Entering build folder..."$reset"
echo

echo "$ cd $build_folder"
cd $build_folder

# remove specific files and dirs from build folder
echo
echo -e "$blue"Removing specific files and dirs from build folder..."$reset"
echo

echo "$ cat ../remove.txt | xargs -I % rm -rf %"
cat ../remove.txt | xargs -I % rm -rf %

# extracting .so files
echo
echo -e "$blue"Extracting .so files..."$reset"
echo

echo "$ mv realsense_so/*.so ."
mv realsense_so/*.so .

echo "$ rm -r -f realsense_so"
rm -r -f realsense_so

# exit build folder
echo
echo -e "$blue"Exiting build folder..."$reset"
echo

echo "$ cd .."
cd ..

# deploy to cluster
echo
echo -e "$blue"Deploying to the cluster..."$reset"
echo

echo "$ ssh $ssh_addr \"rm -r -f $dest_folder\""
ssh $ssh_addr "rm -r -f $dest_folder"

echo "$ ssh $ssh_addr \"mkdir $dest_folder\""
ssh $ssh_addr "mkdir $dest_folder"

echo "$ scp -T -r ./$build_folder/* $ssh_addr:$dest_folder/"
scp -T -r ./$build_folder/* $ssh_addr:$dest_folder/

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts rm -rf $node_folder/code\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts rm -rf $node_folder/code"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts mkdir $node_folder/code\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts mkdir $node_folder/code"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts cp -r $node_folder/Argos_link/* $node_folder/code\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts cp -r $node_folder/Argos_link/* $node_folder/code"

echo "$ ssh $ssh_addr \"parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts $node_folder/Argos_venv/bin/pip install -q -r $node_folder/code/requirements.txt\""
ssh $ssh_addr "parallel-ssh -i -t 0 -h /home/thales/.rpi_hosts $node_folder/Argos_venv/bin/pip install -q -r $node_folder/code/requirements.txt"

# remove deployment folder
echo
echo -e "$blue"Removing build folder..."$reset"
echo

echo "$ rm -r -f $build_folder"
rm -r -f $build_folder

echo
echo -e "$green"Deployment finished!"$reset"
echo
