#!/bin/bash

sudo apt update
sudo apt install qemu-kvm python3.7 python3.7-venv -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.7 ./get-pip.py
sudo usermod -aG kvm $USER
