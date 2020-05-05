#!/bin/bash

# This script determines a baseline for the execution times of both the workload
# and the microVM as a whole. For this, an x amount of instances will be fired 
# up sequentially and of each instance both executions times will be recorded.
myLoc=${0%${0##*/}}
workloadsFile="${1:-"workloads.txt"}"
#Number of times each workload must be run
num=${2:-1000}
warg=${3:-10000}

#TODO: make this a bit more flexible
kernelLoc="$myLoc/../resources/vmlinux"
fsLoc="$myLoc/../resources/benchmark.ext4"

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

#Set minimal amount of instances to 5 (more is usually better though)
if [[ $num -lt 5 ]]; then
    echo "The minimal value of instances is 5, but got $1."
    echo "Execution will be continued with 5 as the number of instances."
    num=5
fi


for workload in ${workloads[@]}; do
    echo "Creating a baseline for $workload"

    tottime=0
    vmtottime=0

    for (( i=0; i < num; ++i )); do
        declare -a times=( $( { $myLoc/launch-firecracker.sh $kernelLoc $fsLoc $i $workload $warg t; } )) 
        #Fetch times and force base10
        fctime=${times[1]//[^0-9]/}
        fctime=$(( 10#$fctime ))
        vmtime=${times[3]//[^0-9]/}
        vmtime=$(( 10#$vmtime ))
        #Add values to overall values
        vmtottime=$((vmtottime + vmtime))
        tottime=$((tottime + fctime))

        echo "$i $fctime $vmtime"
    done

    echo "$workload $tottime $vmtottime"
done

