#!/bin/bash

#Default values
defaultName="rootfs.ext4"

#Argument values
fsName="${1:-$defaultName}"

#Script variables
tmpDir="/tmp/rootfs"
tmpFile="fs.tar.gz"
alpineURL="http://dl-cdn.alpinelinux.org/alpine/v3.11/releases/x86_64/alpine-minirootfs-3.11.5-x86_64.tar.gz"

pushd . > /dev/null

mkdir -p "$tmpDir"

cp "./resources/openrc.tar" "$tmpDir/"

cd "$tmpDir"

echo "Downloading mini rootfs..."
curl -fsSL -o "$tmpFile" "$alpineURL"

echo "Creating filesystem..."
dd if=/dev/zero of="$fsName" bs=1M count=150
mkfs.ext4 "$fsName"

if [[ $EUID -ne 0 ]]; then
    echo "You are not root, may ask for root permission to mount..."
fi

mkdir "$tmpDir/fs"
sudo mount -t ext4 "$fsName" "$tmpDir/fs"

echo "Extracting rootfs..."
sudo tar -xf "$tmpFile" -C "$tmpDir/fs"
sudo tar -xf "openrc.tar" -C "$tmpDir/fs"

echo "Unmounting..."
sudo umount "$tmpDir/fs"

popd > /dev/null

echo "Copying file..."
mv "$tmpDir/$fsName" ./

echo "Cleanup..."
rm -rf "$tmpDir"