#!/bin/bash

declare -a modes=("baseline" "benchmark")

mode=${1:-"baseline"}
num=${2:-1000}

if [[ ! " ${modes[@]} " =~ " $mode " ]]; then
    echo "$mode is an invalid runmode."
    echo "Use one of these: ${modes[@]}"
    exit 1
else
    idx=0
    for m in ${modes[@]}; do
        if [[ "$m" == "${modes[idx]}" ]]; then
            mode=idx
            break
        fi
        ((idx++))
    done
fi  

if [[ $mode -eq 0 ]]; then
    #baseline
    #Run each workload once and 
elif [[ $mode -eq 1 ]]; then
    #benchmark
else
    exit 1
fi