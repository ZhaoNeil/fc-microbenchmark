#!/bin/bash

rootfsName="rootfs.ext4"
writefsName="writedisk.ext4"
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

if [[ ! -e "$resourceDir/$rootfsName" ]]; then
    echo "Not found, building..."
    
    ./scripts/create-root-fs.sh "$rootfsName"

    echo "Compiling binaries..."
    make > /dev/null

    echo "Mounting rootfs..."

    mkdir mount
    sudo mount -t ext4 "$rootfsName" mount

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
/sbin/rc-update add mount-writedisk sysinit

EOF

    echo "Unmounting..."
    sudo umount mount

    make clean > /dev/null

    rmdir mount

    mv "$rootfsName" "$resourceDir/"
else
    echo "Found!"
fi

echo "Checking if write disk exists..."

if [[ ! -e "$resourceDir/$writefsName" ]]; then
    dd if=/dev/zero of="$resourceDir/$writefsName" bs=1G count=10
    mkfs.ext4 "$resourceDir/$writefsName"
fi

echo "Checking if kernel exists..."

if [[ ! -e "$resourceDir/$kernelName" ]]; then
    echo "Not found, do you wish to build it from source?"
    exit 1
else
    echo "Found!"
fi

echo "Disabling SMT..."

echo "d" | sudo ./scripts/toggleHT.sh

echo "Setting CPU governor to performance"
which cpupower > /dev/null

if [[ $? -eq 0 ]]; then
    sudo cpupower frequency-set -g performance
fi

echo "Disabling turbo-boost"
arch="$(uname -m)"

if [[ "$arch" == "x86_64" ]]; then
    echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

elif [[ "$arch" == "aarch64" ]]; then
    echo "0" | sudo tee /sys/devices/system/cpu/cpufreq/boost
fi


echo "You are ready to go!"