#!/bin/bash

blue="\033[1;34m"
green="\033[1;32m"
reset="\033[0m"

echo -e "${green}Rebooting cluster...${reset}"
echo

echo -e "${blue}Rebooting nodes...${reset}"
echo

read -sp "Nodes password: " pass
echo
echo

while IFS= read -r rpi
do
    echo "$ ssh $rpi \"echo <pass> | sudo -S reboot\" &"
    {
    ssh -T "$rpi" "echo ${pass} | sudo -S reboot" &
    } > /dev/null 2>/dev/null
done < /home/thales/.rpi_pssh_hosts
wait

echo
echo -e "${blue}Rebooting master...${reset}"
echo

echo "$ sudo reboot"
sudo reboot > /dev/null 2>/dev/null



