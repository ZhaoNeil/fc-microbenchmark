#!/bin/bash

### Starting point for the fc-microbenchmark. This script provides a nicer user
### experience than when all backing scripts are used manually.
###
### Author:     N.J.L. Boonstra
###     2020 (c)

#Modes accepted by this script
declare -a modes=( "benchmark" "baseline" "interactive")
arch="$(uname -m)"
kernelLoc="./resources/vmlinux-${arch}"
fsLoc="./resources/rootfs.ext4"
wlLoc="./parameters/workloads.txt"
waLoc="./workloads/benchmark-arguments.txt"
mode=${modes[0]}
num=10
usePoisson=0
SYSMON_location="./processing/machine_monitor.py"

which firecracker > /dev/null

if [[ $? -ne 0 ]]; then
    echo "Firecracker is not installed! Please run ./setup.sh" 1>&2
    exit 1
fi


usage() {
    echo "Usage: ${0##*/} [-k <string>] [-f <string>] [-m <string>] [-w <string>] [-n <int>] [-a <string>] [-h]" 1>&2
}

help() {
    echo "Micro-Benchmark for the Firecracker microVM" 1>&2
    usage
    echo "  -k  File location       Location of the kernel to be used, default: $kernelLoc" 1>&2
    echo "  -f  File location       Location of the root filesystem, default: $fsLoc" 1>&2
    echo "  -m  Mode                Mode to run, can be \"${modes[@]}\", default: $mode" 1>&2
    echo "  -w  File location       Location of the workloads.txt file, default: $wlLoc" 1>&2
    echo "  -n  Instances           Number of instances to run maximally, default: $num" 1>&2
    echo "  -a  File location       File locations of the workload arguments, no default." 1>&2
    echo "  -p                      Toggle usage of poisson timings incorporated in workload arugments file." 1>&2
    echo "  -h                      Display this" 1>&2
    exit 1
}

ensure_pipenv() {
    which pipenv > /dev/null

    if [[ $? -ne 0 ]]; then
        echo "Please install pipenv!" 1>&2
        exit 1
    fi
}

#Parse the arguments

while getopts ":k:f:m:w:n:a:hp" o; do
    case $o in
        k )
            kernelLoc=$OPTARG
            if [[ ! -e $kernelLoc ]]; then
                echo "$kernelLoc does not exist!" 1>&2
                exit 1
            fi
            ;;
        f )
            fsLoc=$OPTARG
            if [[ ! -e $fsLoc ]]; then
                echo "$fsLoc does not exist!" 1>&2
                exit 1
            fi
            ;;
        m )
            mode=$OPTARG
            ;;
        w )
            wlLoc=$OPTARG
            if [[ ! -e $wlLoc ]]; then
                echo "$wlLoc does not exist!" 1>&2
                exit 1
            fi
            ;;
        n )
            num=$OPTARG
            if [[ $num -lt 1 ]]; then
                echo "-n requires a number greater than 0, got $num" 1>&2
                exit 1
            fi
            ;;
        a )
            waLoc=$OPTARG
            if [[ ! -e $waLoc ]]; then
                echo "$waLoc does not exist!" 1>&2
                exit 1
            fi
            ;;
        h )
            help
            exit 1
            ;;
        p )
            usePoisson=1
            ;;
        \? )
            echo "Invalid option: -$OPTARG" 1>&2
            usage
            exit 1  
            ;;
        : )
            echo "$OPTARG requires an argument" 1>&2
            usage
            exit 1
            ;;
    esac
done

#Determine the mode and whether it is valid
if [[ ! " ${modes[@]} " =~ " $mode " ]]; then
    echo "$mode is an invalid runmode." 1>&2
    echo "Use one of these: ${modes[@]}" 1>&2
    exit 1
else
    idx=0
    for m in ${modes[@]}; do
        if [[ "$mode" == "$m" ]]; then
            mode=idx
            break
        fi
        ((idx++))
    done
fi

# Set ulimits for this shell (and thus for all subshells)
# Snippet from StackOverflow: https://stackoverflow.com/questions/28068414/how-do-i-set-all-ulimits-unlimited-for-all-users/28068611#28068611
for opt in $(ulimit -a | sed 's/.*\-\([a-z]\)[^a-zA-Z].*$/\1/'); do
    ulimit -$opt unlimited 2> /dev/null
done

echo "Disabling SMT..." 1>&2

echo "d" | sudo ./scripts/toggleHT.sh > /dev/null

echo "Setting CPU governor to performance" 1>&2
which cpupower > /dev/null

if [[ $? -eq 0 ]]; then
    sudo cpupower frequency-set -g performance
fi

echo "Disabling turbo-boost" 1>&2
arch="$(uname -m)"

if [[ "$arch" == "x86_64" ]]; then

    if [[ -e "/sys/devices/system/cpu/intel_pstate/no_turbo" ]]; then
        echo "1" | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo > /dev/null
    elif [[ -e "/sys/devices/system/cpu/cpufreq/boost" ]]; then
        echo "0" | sudo tee /sys/devices/system/cpu/cpufreq/boost > /dev/null
    fi

elif [[ "$arch" == "aarch64" ]]; then
    echo "0" | sudo tee /sys/devices/system/cpu/cpufreq/boost > /dev/null
fi

echo "Raising pid max..." 1>&2

echo "4194303" | sudo tee /proc/sys/kernel/pid_max > /dev/null

echo "Raising user limits..." 1>&2

if [[ $mode -eq 0 ]]; then
    #benchmark

    #We need pipenv
    #ensure_pipenv

    #output to this file, which is sysmon-(workload name)
    SYSMON_OUTPUT="./results/sysmon-${waLoc##*/}"

    (python3 $SYSMON_location -i 1.0 -o $SYSMON_OUTPUT ) &

    SYSMON_PID=$!
    waited=0

    #Wait max 3sec for sysmon to pop up
    while [[ ! -f $SYSMON_OUTPUT ]]; do
        sleep 1.0
        waited=$(( ++waited ))

        if [[ $waited -ge 3 ]]; then
            echo "sysmon took too long to start, exiting..." 1>&2
            exit 1
        fi
    done

    #sleep for 1 sec after, to ensure it has a 0 measurement on the first line
    sleep 1.0s

    echo "Starting benchmark..." 1>&2

    ./scripts/benchmark.sh $kernelLoc $fsLoc $wlLoc $num $waLoc $usePoisson

    kill -2 $SYSMON_PID
elif [[ $mode -eq 1 ]]; then
    #baseline
    echo "Determining baseline execution times..." 1>&2
    ./scripts/baseline.sh $kernelLoc $fsLoc $wlLoc $num $waLoc
elif [[ $mode -eq 2 ]]; then
    #interactive
    ./scripts/launch-firecracker.sh $kernelLoc $fsLoc 1 default 0 v
else
    #Fall-through
    exit 1
fi
