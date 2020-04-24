#!/bin/bash

#Default values
defaultName="rootfs.ext4"

#Argument values
fsName="${1:-$defaultName}"

#Script variables
tmpDir="/tmp/rootfs"
tmpFile="apktools.tar.gz"
alpineMirror="http://nl.alpinelinux.org/alpine"
alpineBranch="latest-stable"
alpineURL="https://github.com/alpinelinux/apk-tools/releases/download/v2.10.4/apk-tools-2.10.4-x86_64-linux.tar.gz"

pushd . > /dev/null

# Make sure tmpDir is non-existent
rm -rf "$tmpDir"

mkdir -p "$tmpDir"

cd "$tmpDir"

echo "Downloading apk tools..."
curl -fsSL -o "$tmpFile" "$alpineURL"

echo "Creating filesystem..."
dd if=/dev/zero of="$fsName" bs=1M count=150
mkfs.ext4 "$fsName"

if [[ $EUID -ne 0 ]]; then
    echo "You are not root, may ask for root permission to mount..."
fi

mkdir "$tmpDir/fs"
sudo mount -t ext4 "$fsName" "$tmpDir/fs"

echo "Extracting apk tools..."
tar -xf "$tmpFile"
mv ./apk-tools-*/apk ./apk




echo "Installing Alpine Linux..."

sudo mkdir -p "$tmpDir/fs/etc/apk/"
# Need to echo to root owned directory, so use tee
sudo touch "$tmpDir/fs/etc/apk/repositories"
echo "$alpineMirror/$alpineBranch/main" | sudo tee "$tmpDir/fs/etc/apk/repositories" > /dev/null
echo "$alpineMirror/$alpineBranch/community" | sudo tee -a "$tmpDir/fs/etc/apk/repositories" > /dev/null

sudo $tmpDir/apk --root "$tmpDir/fs" --update-cache --initdb --allow-untrusted --arch x86_64 add alpine-base util-linux openrc

# Remove the spawning getty's
cat <<EOF > ./inittab
# /etc/inittab

::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::wait:/sbin/openrc default

# Stuff to do for the 3-finger salute
::ctrlaltdel:/sbin/reboot

# Stuff to do before rebooting
::shutdown:/sbin/openrc shutdown
EOF

sudo mv ./inittab "$tmpDir/fs/etc/inittab"
sudo chown root:root "$tmpDir/fs/etc/inittab"

echo "Unmounting..."
sudo umount "$tmpDir/fs"

popd > /dev/null

echo "Copying file..."
mv "$tmpDir/$fsName" ./

echo "Cleanup..."
rm -rf "$tmpDir"