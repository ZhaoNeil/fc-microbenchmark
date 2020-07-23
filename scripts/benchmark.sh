#!/bin/bash

myLoc=${0%${0##*/}}
#start.sh already passes defaults, but this is nice in case you want to use this
#script standalone
kernelLoc="${1:-"$myLoc/../resources/vmlinux"}"
fsLoc="${2:-"$myLoc/../resources/rootfs.ext4"}"
workloadsFile="${3:-"$myLoc/../parameters/workloads.txt"}"
#num is the amount of instances that may be active at the same moment
num=${4:-1000}
wargs=${5:-"$myLoc/../parameters/benchmark-arguments.txt"}
isPoisson=${6:-0}


fileResults="$myLoc/../results/results-${wargs##*/}"

#Backup for when we're done
OLDIFS=$IFS

IFS=$'\n'
workloads=( $(cat $workloadsFile ) )
workloadargs=( $(cat $wargs ) )

idx=0
for workloadarg in ${workloadargs[@]}; do
    IFS=$','
    split=( ${workloadarg} )
    workloadnum=${split[0]//[^0-9]/}
    workload=${workloads[$workloadnum]}
    warg=${split[1]//[^0-9]/}
    sleeptime=${split[2]//[^0-9\.]}

    #Unset to avoid weird behavior later on
    unset IFS

    if [[ -z "$workload" ]]; then
        echo "Invalid workload number: $workloadnum" 1>&2
        continue
    fi

    echo "Workload: ${workload} Argument: $warg" 1>&2
    # Increment here, does not work in subshell
    thisId=$((idx++))

    #Run this in a subshell for parallel execution
    (
        #Start time in milliseconds from epoch (for data processing)
        starttime=$(printf '%(%s)T\n' -1)
        mywarg=$warg
        #Save a local copy of workloadnum
        myworknum=$workloadnum
        declare -a res=( $( $myLoc/launch-firecracker.sh $kernelLoc $fsLoc $thisId $workload $warg t ) )
        #Process execution times
        fctime=${res[1]//[^0-9]/}
        fctime=${fctime#"${fctime%%[!0]*}"}
        fctime=$(( 10#$fctime ))
        vmtime=${res[3]//[^0-9]/}
        vmtime=${vmtime#"${vmtime%%[!0]*}"}
        vmtime=$(( 10#$vmtime ))

        
        #Write results to the resultsfile
        #TODO: check if this does not result in data loss due to concurrent 
        #       writes
        echo "$myworknum,$mywarg,$fctime,$vmtime,$starttime" >> $fileResults

    )&

    if [[ isPoisson -eq 1 ]]; then
        echo "Sleeping for $sleeptime" 1>&2
        sleep $sleeptime
    fi

done

echo "Waiting for the instances to finish..." 1>&2
wait 
echo "Processing results..." 1>&2

IFS=$'\n'; results=( $(cat $fileResults) )

#We should get x results, with x being equal to the amount of lines in the
#$wargs file
if [[ ${#results[@]} -ne ${#workloadargs[@]} ]]; then
    echo "Something went wrong with saving the results:" 1>&2
    echo "  Expected ${#workloadargs[@]} results, but got ${#results[@]}" 1>&2
fi

# # Array for the execution time of the workload inside the Firecracker instance
# vmresults=()
# # Array for the execution time of the Firecracker instance itself
# # this accounts for the total runtime
# fcresults=()

# for result in ${results[@]}; do
#     IFS=$','; split=($result)
#     wno=${split[0]}
#     fct=${split[1]}
#     vmt=${split[2]}


#     vmresults[$wno]=$((vmresults[$wno] + vmt))
#     fcresults[$wno]=$((fcresults[$wno] + fct))
# done

# echo "#Workload, total fc time, total vm time, avg fc time, avg vm time"
# for ((i=0; i < ${#workloads[@]}; ++i)); do
#     avgvm=$( echo "scale=4; ${vmresults[$i]}/${#results[@]}" | bc)
#     avgfc=$( echo "scale=4; ${fcresults[$i]}/${#results[@]}" | bc)
#     echo "${workloads[$i]},${fcresults[$i]},${vmresults[$i]},${avgfc},${avgvm}"
# done

# mv $fileResults ./results-benchmark.txt

echo "Results placed in $fileResults" 1>&2