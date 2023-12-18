#!/bin/bash

source="~/Desktop/Argos"
dest="~/Argos"

yellow='\033[1;33m'
reset='\033[0m'

echo
echo -e "$yellow"Entered in argos-master bash..."$reset"
echo

echo "$ ssh rpi2 \"rm -r -f $dest\""
ssh rpi2 "rm -r -f $dest"

echo "$ ssh rpi2 \"mkdir $dest\""
ssh rpi2 "mkdir $dest"

echo "$ scp -T -r $source/* rpi2:$dest"
scp -T -r $source/* "rpi2:$dest"

echo "$ ssh rpi2 \"rm $dest/broadcast.sh\""
ssh rpi2 "rm $dest/broadcast.sh"

echo
echo -e "$yellow"Exited argos-master bash..."$reset"