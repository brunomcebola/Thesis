#!/bin/bash

sudo -S  iptables -A FORWARD -o eno1 -i enp8s5 -s 192.168.50.0/24 -m conntrack --ctstate NEW -j ACCEPT
sudo -S iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo -S iptables -t nat -F POSTROUTING
sudo -S iptables -t nat -A POSTROUTING -o eno1 -j MASQUERADE

sudo -S iptables-save | sudo -S tee /etc/iptables.sav

sudo -S sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
