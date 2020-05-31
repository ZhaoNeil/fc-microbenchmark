#!/bin/bash

### Reset the system to normal values (the turbo boost back etc)
arch="$(uname -m)"
if [[ "$arch" == "x86_64" ]]; then
    echo "0" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

elif [[ "$arch" == "aarch64" ]]; then
    echo "1" | sudo tee /sys/devices/system/cpu/cpufreq/boost
fi

echo "Setting CPU governor to ondemand"
which cpupower > /dev/null

if [[ $? -eq 0 ]]; then
    if [[ "$arch" == "x86_64" ]]; then
        sudo cpupower frequency-set -g powersave
    elif [[ "$arch" == "aarch64" ]]; then
        sudo cpupower frequency-set -g ondemand
    fi
fi

echo "Enabling SMT..."

echo "e" | sudo ./scripts/toggleHT.sh