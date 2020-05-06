#!/bin/bash

fsName="rootfs.ext4"
kernelName="vmlinux"

tmpDir="/tmp/fc-microbenchmark"
resourceDir="./resources"

workloadsFile="${1:-"workloads.txt"}"

#Read installed workloads from file to array
workloads=($(cat $workloadsFile))

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
    make > /dev/null

    echo "Mounting rootfs..."

    mkdir mount
    sudo mount -t ext4 "$fsName" mount

    if [[ $EUID -ne 0 ]]; then
        echo "You are not root, may ask for root permission to mount..."
    fi

    echo "Copying binaries to filesystem..."

    sudo cp ./bin/* ./mount/bin



    echo "Installing openrc files..."
    sudo cp ./openrc/init.d/* ./mount/etc/init.d
    sudo cp ./openrc/conf.d/* ./mount/etc/conf.d

    echo "Setting up runlevels for workloads..."
    for workload in ${workloads[@]}; do
        sudo mkdir ./mount/etc/runlevels/$workload
        sudo chmod +x ./mount/etc/runlevels/$workload
cat <<EOF | sudo chroot ./mount /bin/sh
/sbin/rc-update add run-workload $workload
EOF
    done

# Add agetty to default runlevel and make sure some fs's are available on boot
cat <<EOF | sudo chroot ./mount /bin/sh
/sbin/rc-update add devfs sysinit
/sbin/rc-update add sysfs sysinit

/bin/ln -s /etc/init.d/agetty /etc/init.d/agetty.ttyS0
/sbin/rc-update add agetty.ttyS0 default

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