#!/bin/bash

### This script determines a baseline for the execution times of both the 
### workload and the microVM as a whole. For this, an x amount of instances will
### be fired up sequentially and of each instance both executions times will be 
### recorded.
###
### Author:     N.J.L. Boonstra
###     2020 (c)

myLoc=${0%${0##*/}}
#start.sh already passes defaults, but this is nice in case you want to use this
#script standalone
kernelLoc="${1:-"$myLoc/../resources/vmlinux"}"
fsLoc="${2:-"$myLoc/../resources/rootfs.ext4"}"
workloadsFile="${3:-"workloads.txt"}"
#Number of times each workload must be run
num=${4:-1000}
wargs=${5:-"$myLoc/../baseline-arguments.txt"}

if [[ "$wargs" == "" ]]; then
    echo "Please specify workload arguments."
    exit 1
fi

if [[ ! -e $workloadsFile ]]; then
    echo "The file $workloadsFile does not exist!"
    echo "Exiting..."
    exit 1
elif [[ ! -r $workloadsFile ]]; then
    echo "Could not read the file $workloadsFile!"
    echo "Exiting..."
    exit 1
fi

#Read the workloads
workloads=($(cat $workloadsFile))

#Read the arguments for each workload from the warg file
workloadargs=($(cat $wargs))

for warg in ${workloadargs[@]} ; do


# OLDIFS=$IFS
# IFS=$','; declare -a workloadargs=( $wargs )
# IFS=$OLDIFS

if [[ ${#workloadargs[@]} -lt ${#workloads[@]} ]]; then
    echo "Please provide workload arguments for each workload."
    echo "Got ${#workloadargs[@]}, but expected ${#workloads[@]}"
    exit 1
fi

#Set minimal amount of instances to 5 (more is usually better though)
if [[ $num -lt 5 ]]; then
    echo "The minimal value of instances is 5, but got $1."
    echo "Execution will be continued with 5 as the number of instances."
    num=5
fi

idx=0

for workload in ${workloads[@]}; do
    warg=${workloadargs[idx]}

    echo "${workload},${warg}"

    tottime=0
    vmtottime=0

    for (( i=0; i < num; ++i )); do
        declare -a times=( $( { $myLoc/launch-firecracker.sh $kernelLoc $fsLoc $i $workload $warg t; } )) 
        #Fetch times and force base10 by stripping the dotsign.
        # TODO: now I assume that both times are equally precise, but this is 
        # not necessarily the case
        fctime=${times[1]//[^0-9]/}
        fctime=$(( 10#$fctime ))
        vmtime=${times[3]//[^0-9]/}
        vmtime=$(( 10#$vmtime ))
        #Add values to overall values
        vmtottime=$((vmtottime + vmtime))
        tottime=$((tottime + fctime))

        echo "${i},${fctime},${vmtime}"
    done

    echo "total,${tottime},${vmtottime}"
    echo ""
    ((++idx))
done

