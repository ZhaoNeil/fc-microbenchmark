#!/bin/bash

if [[ $PIPENV_ACTIVE -ne 1 ]]; then
    echo "Please run from within a pipenv!" 1>&2
    exit 1
fi

MY_LOC="$(dirname $0)"

IFS=$'\n'; ALL_DIRS=( $(find $MY_LOC -maxdepth 1 ! -path $MY_LOC -type d) )

for DIR in ${ALL_DIRS[@]}; do
    echo "Processing $DIR" 1>&2
    python $MY_LOC/../process_results.py $DIR
done