#!/bin/bash

#if [[ $PIPENV_ACTIVE -ne 1 ]]; then
#    echo "Please run from within a pipenv!" 1>&2
#    exit 1
#fi
#
MY_LOC="$(dirname $0)"
THREADS=${1:-0}
PIDS=()

IFS=$'\n'; ALL_DIRS=( $(find $MY_LOC -maxdepth 1 ! -path $MY_LOC -type d) )

if [[ $THREADS -gt 0 ]]; then
    echo "Threaded processing turned on." 1>&2
    for DIR in ${ALL_DIRS[@]}; do
        echo "Processing $DIR" 1>&2

        while [[ ${#PIDS[@]} -ge $THREADS ]]; do
            wait ${PIDS[@]}
            PIDS=()
        done

        python3 $MY_LOC/../processing/process_results.py $DIR &
        PIDS+=($!)

    done

    if [[ ${#PIDS[@]} -gt 0 ]]; then
        wait ${PIDS[@]}
    fi
else

    for DIR in ${ALL_DIRS[@]}; do
        echo "Processing $DIR" 1>&2

        python3 $MY_LOC/../processing/process_results.py $DIR
        
    done

fi
