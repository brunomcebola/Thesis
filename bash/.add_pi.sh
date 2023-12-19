#!/bin/bash

NC='\033[0m'
B_CYAN='\033[1;36m'
B_RED='\033[1;31m'
B_GREEN='\033[1;32m'
U_WHITE='\033[4;37m'

echo
echo -e "${B_CYAN}Welcome to the Pi Cluster Wizard!${NC}"
echo

read -p "What is the raspberry pi hostname? " hostname
read -p "What is the raspberry pi fixed ip? " fixed_ip
read -p "What is the raspberry pi serial number? " serial_number
read -p "What is the raspberry pi MAC address? " mac_address

echo ""

if [ -d "/mnt/disk/${hostname}" ]
then
	echo -e "${B_RED}Error:${NC} A raspberry pi with the specified hostname (${hostname}) already exists."
	exit 1
fi

echo -e "${U_WHITE}Entering sudo mode${NC}"
echo '$ sudo su'
sudo su << EOF
	echo

	echo -e "${U_WHITE}Creating nfs directory${NC}"
	echo '$ mkdir -p /mnt/disk/${hostname}'
	mkdir -p /mnt/disk/${hostname}
	echo

	echo -e "${U_WHITE}Copying master nfs${NC}"
	echo '$ cp -a /mnt/disk/master/* /mnt/disk/${hostname}'
	cp -a /mnt/disk/master/* /mnt/disk/${hostname}
	echo

	echo -e "${U_WHITE}Creating tftp boot directory${NC}"
	echo '$ mkdir -p /mnt/disk/tftpboot/${serial_number}'
	mkdir -p /mnt/disk/tftpboot/${serial_number}
	echo

	echo -e "${U_WHITE}Adding new raspberry to fstab${NC}"
	echo '$ echo "/mnt/disk/${hostname}/boot /mnt/disk/tftpboot/${serial_number} none defaults,bind 0 0" >> /etc/fstab'
	echo "/mnt/disk/${hostname}/boot /mnt/disk/tftpboot/${serial_number} none defaults,bind 0 0" >> /etc/fstab
	echo

	echo -e "${U_WHITE}Adding new raspberry to exports${NC}"
	echo '$ echo "/mnt/disk/${hostname} 192.168.50.0/24(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports'
	echo "/mnt/disk/${hostname} 192.168.50.0/24(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports
	echo

	echo -e "${U_WHITE}Changing boot cmdline.txt file${NC}"
	echo '$ echo "console=serial0,115200 console=tty root=/dev/nfs nfsroot=192.168.50.1:/mnt/disk/${hostname},vers=3,proto=tcp rw ip=dhcp rootwait" > /mnt/disk/${hostname}/boot/cmdline.txt'
	echo "console=serial0,115200 console=tty root=/dev/nfs nfsroot=192.168.50.1:/mnt/disk/${hostname},vers=3,proto=tcp rw ip=dhcp rootwait" > /mnt/disk/${hostname}/boot/cmdline.txt
	echo

	echo -e "${U_WHITE}Changing hostname${NC}"
	echo '$ echo "${hostname}" > /mnt/disk/${hostname}/etc/hostname'
	echo "${hostname}" > /mnt/disk/${hostname}/etc/hostname
	echo

	echo -e "${U_WHITE}Adding raspberry to dhcpd.conf${NC}"
	echo "$ sed 's/# nodes/host ${hostname} {\n          option root-path \"\/mnt\/disk\/tftpboot\/\";\\n          hardware ethernet ${mac_address};\\n          option option-43 \"Raspberry Pi Boot\";\\n          option option-66 \"192.168.50.1\";\\n          next-server 192.168.50.1;\\n          fixed-address ${fixed_ip};\\n          option host-name \"${hostname}\";\\n      }\\n\\n      # nodes/' /etc/dhcp/dhcpd.conf"
	sed -i 's/# nodes/host ${hostname} {\n          option root-path "\/mnt\/disk\/tftpboot\/";\n          hardware ethernet ${mac_address};\n          option option-43 "Raspberry Pi Boot";\n          option option-66 "192.168.50.1";\n          next-server 192.168.50.1;\n          fixed-address ${fixed_ip};\n          option host-name "${hostname}";\n      }\n\n      \# nodes/' /etc/dhcp/dhcpd.conf
	echo

	echo -e "${U_WHITE}Adding raspberry to /etc/hosts${NC}"
	echo 'echo "${fixed_ip}   ${hostname}" >> /etc/hosts'
	echo "${fixed_ip}   ${hostname}" >> /etc/hosts
	echo

	echo -e "${U_WHITE}Exiting sudo mode${NC}"
	echo '$ exit'
	exit
EOF
echo

echo -e "${B_GREEN}Success:${NC} New raspberry added to the cluster (${hostname})"
echo

echo -e "${B_CYAN}Exiting Pi Cluster Wizard!${NC}"
echo
