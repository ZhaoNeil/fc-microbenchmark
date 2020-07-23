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
workloadsFile="${3:-"$myLoc/../parameters/workloads.txt"}"
#Number of times each workload must be run
num=${4:-10}
wargs=${5:-"$myLoc/../baseline-arguments.txt"}

if [[ "$wargs" == "" ]]; then
    echo "Please specify workload arguments." 1>&2
    exit 1
fi

if [[ ! -e $workloadsFile ]]; then
    echo "The file $workloadsFile does not exist!" 1>&2
    echo "Exiting..." 1>&2
    exit 1
elif [[ ! -r $workloadsFile ]]; then
    echo "Could not read the file $workloadsFile!" 1>&2
    echo "Exiting..." 1>&2
    exit 1
fi

OLDIFS=$IFS
#Read the workloads
IFS=$'\n'; workloads=($(cat $workloadsFile))

#Read the arguments for each workload from the warg file
IFS=$'\n'; workloadargs=($(cat $wargs))


# OLDIFS=$IFS
# IFS=$','; declare -a workloadargs=( $wargs )
# IFS=$OLDIFS

# if [[ ${#workloadargs[@]} -lt ${#workloads[@]} ]]; then
#     echo "Please provide workload arguments for each workload."
#     echo "Got ${#workloadargs[@]}, but expected ${#workloads[@]}"
#     exit 1
# fi

#Set minimal amount of instances to 5 (more is usually better though)
if [[ $num -lt 5 ]]; then
    echo "The minimal value of instances is 5, but got $1." 1>&2
    echo "Execution will be continued with 5 as the number of instances." 1>&2
    num=5
fi

idx=0

echo "#workloadID, workload argument, tFC, tVM"

for workloadarg in ${workloadargs[@]}; do
    # Skip comments
    if [[ "${workloadarg:0:1}" == "#" ]]; then
        continue
    fi
    # Get the id of the workload and the warg
    IFS=$','; split=( $workloadarg )
    wno=${split[0]//[^0-9]/}
    arg=${split[1]//[^0-9]/}
    workload=${workloads[$wno]}

    # Invalid workload -> workload is undefined -> skip this
    if [[ -z "$workload" ]]; then
        echo "Invalid workload number: $wno" 1>&2
        continue
    fi

    echo "${workload},${arg}" 1>&2

    tottime=0
    vmtottime=0

    for (( i=0; i < num; ++i )); do
        IFS=$OLDIFS; declare -a times=( $( { $myLoc/launch-firecracker.sh $kernelLoc $fsLoc $i $workload $arg t; } )) 
        #Fetch times and force base10 by stripping the dotsign.
        # TODO: now I assume that both times are equally precise, but this is 
        # not necessarily the case
        fctime=${times[1]//[^0-9]/}
        fctime=$(( 10#$fctime ))
        vmtime=${times[3]//[^0-9]/}
        vmtime=$(( 10#$vmtime ))

        echo "Run ${i}: ${fctime} and ${vmtime}" 1>&2
        echo "${wno},${arg},${i},${fctime},${vmtime}"
    done
    ((++idx))
done

