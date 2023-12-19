#!/bin/bash

sudo iptables -A FORWARD -o eno1 -i enp8s5 -s 192.168.50.0/24 -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -t nat -F POSTROUTING
sudo iptables -t nat -A POSTROUTING -o eno1 -j MASQUERADE

sudo iptables-save | sudo tee /etc/iptables.sav

sudo sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
