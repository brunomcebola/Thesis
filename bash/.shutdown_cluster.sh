#!/bin/bash

blue="\033[1;34m"
green="\033[1;32m"
reset="\033[0m"

echo -e "${green}Shutting down cluster...${reset}"
echo

echo -e "${blue}Shutting down nodes...${reset}"
echo

read -sp "Nodes password: " pass
echo
echo

while IFS= read -r rpi
do
    echo "$ ssh $rpi \"echo <pass> | sudo -S shutdown -h now\" &"
    {
    ssh -T "$rpi" "echo ${pass} | sudo -S shutdown -h now" &
    } > /dev/null 2>/dev/null
done < /home/thales/.rpi_pssh_hosts
wait

echo
echo -e "${blue}Shutting down master...${reset}"
echo

echo "$ sudo shutdown -h now"
sudo shutdown -h now > /dev/null 2>/dev/null
