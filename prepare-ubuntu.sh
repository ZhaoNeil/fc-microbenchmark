#!/bin/bash

sudo apt update
sudo apt install qemu-kvm python3.7 python3.7-venv -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.7 ./get-pip.py
sudo python3.7 -m pip install pipenv
python3.7 -m pipenv install
sudo usermod -aG kvm $USER

mkdir ~/bin
curl -fsSL https://github.com/firecracker-microvm/firecracker/releases/download/v0.21.1/firecracker-v0.21.1-$(uname -m) -o ~/bin/firecracker
chmod +x ~/bin/firecracker