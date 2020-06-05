#!/bin/bash

sudo apt update
sudo apt install qemu-kvm python3.7 python3.7-venv linux-tools-common linux-cloud-tools-$(uname -r) linux-tools-$(uname -r) -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.7 ./get-pip.py
sudo python3.7 -m pip install pipenv
python3.7 -m pipenv install
sudo usermod -aG kvm $USER

echo "Please restart the session to ensure the changes take effect."