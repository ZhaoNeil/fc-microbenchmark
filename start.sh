#!/bin/bash

### Starting point for the fc-microbenchmark. This script provides a nicer user
### experience than when all backing scripts are used manually.
###
### Author:     N.J.L. Boonstra
###     2020 (c)

#Modes accepted by this script
declare -a modes=( "benchmark" "baseline" "interactive")
kernelLoc="./resources/vmlinux"
fsLoc="./resources/rootfs.ext4"
wlLoc="./workloads.txt"
waLoc=""
mode=${modes[0]}


usage() {
    echo "Usage: ${0##*/} [-k <string>] [-f <string>] [-m <string>] [-w <string>] [-n <int>] [-a <string>] [-h]" 1>&2
}

help() {
    echo "Micro-Benchmark for the Firecracker microVM" 1>&2
    usage
    echo "  -k  File location       Location of the kernel to be used, default: $kernelLoc" 1>&2
    echo "  -f  File location       Location of the root filesystem, default: $fsLoc" 1>&2
    echo "  -m  Mode                Mode to run, can be ${modes[@]}, default: $mode" 1>&2
    echo "  -w  File location       Location of the workloads.txt file, default: $wlLoc"
    echo "  -n  Instances           Number of instances to run maximally, default: $num" 1>&2
    echo "  -a  File location       File locations of the workload arguments, no defalt." 1>&2
    echo "  -h                      Display this" 1>&2
    exit 1
}

#Parse the arguments

while getopts ":k:f:m:w:n:h" o; do
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
            if [[ ! -e $wlLoc ]]; then
                echo "$wlLoc does not exist!" 1>&2
                exit 1
            fi
            ;;
        h )
            help
            exit 1
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
    echo "$mode is an invalid runmode."
    echo "Use one of these: ${modes[@]}"
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

if [[ $mode -eq 0 ]]; then
    #benchmark
    echo "Running benchmark..."
    ./scripts/benchmark.sh $kernelLoc $fsLoc $wlLoc $num $waLoc
elif [[ $mode -eq 1 ]]; then
    #baseline
    echo "Determining baseline execution times..."
    ./scripts/baseline.sh $kernelLoc $fsLoc $wlLoc $num $waLoc
elif [[ $mode -eq 2 ]]; then
    #interactive
    ./scripts/launch-firecracker.sh $kernelLoc $fsLoc 1 default 0 v
else
    exit 1
fi