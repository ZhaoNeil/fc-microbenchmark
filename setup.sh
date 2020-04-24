#!/bin/bash

fsName="benchmark.ext4"
kernelName="vmlinux"

tmpDir="/tmp/fc-microbenchmark"
resourceDir="./resources"

declare -a workloads=("dd" "primenumber" "stream")
workloadScriptPrefix="run-workload-"
workloadShutdownPrefix="shutdown-after-"


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
    sudo mount -t ext4 "$fsName" mount

    if [[ $EUID -ne 0 ]]; then
        echo "You are not root, may ask for root permission to mount..."
    fi

    echo "Copying binaries to filesystem..."

    sudo cp ./bin/* ./mount/bin

    # TODO: perhaps use the array with workload names, rather than writing them out

    echo "Setting up runlevels for workloads..."
    sudo mkdir ./mount/etc/runlevels/{stream,dd,primenumber}
    sudo chmod +x ./mount/etc/runlevels/{stream,dd,primenumber}

    echo "Installing workloads to runlevels..."
    sudo cp ./openrc/init.d/* ./mount/etc/init.d
    sudo cp ./openrc/conf.d/* ./mount/etc/conf.d



cat <<EOF | sudo chroot ./mount /bin/sh
/sbin/rc-update add run-workload-dd dd
/sbin/rc-update add run-workload-primenumber primenumber
/sbin/rc-update add run-workload-stream stream
/sbin/rc-update add shutdown-after-dd dd
/sbin/rc-update add shutdown-after-stream stream
/sbin/rc-update add shutdown-after-primenumber primenumber
/sbin/rc-update add devfs sysinit
/sbin/rc-update add sysfs sysinit

EOF

    echo "Unmounting..."
    sudo umount mount

    make clean > /dev/null

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