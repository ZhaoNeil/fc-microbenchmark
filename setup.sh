#!/bin/bash

fsName="benchmark.ext4"
kernelName="vmlinux"

tmpDir="/tmp/fc-microbenchmark"
resourceDir="./resources"

echo "Checking if AWS Firecracker is in \$PATH..."

which firecracker > /dev/null

if [[ $? -ne 0 ]]; then
    echo "Firecracker not found!"
    echo "Please make sure it is installed and the binary is in \$PATH"
    exit 1
else
    echo "Found!"
fi

echo "Checking if root filesystem exists..."

if [[ ! -e "$resourceDir/$fsName" ]]; then
    echo "Not found, building..."
    
    ./scripts/create-root-fs.sh "$fsName"

    echo "Compiling binaries..."
    make

    mkdir mount

    if [[ $EUID -ne 0 ]]; then
        echo "You are not root, may ask for root permission to mount..."
    fi

    echo "Copying binaries to filesystem..."
    sudo mount -t ext4 "$fsName" mount

    sudo cp ./bin/* ./mount/bin

    sudo umount mount

    make clean 

    rmdir mount

    mv "$fsName" "$resourceDir/"
else
    echo "Found!"
fi

echo "Checking if kernel exists..."

if [[ ! -e "$resourceDir/$kernelName" ]]; then
    echo "Not found, do you wish to build it from source?"

else
    echo "Found!"
fi

echo "You are ready to go!"