#!/bin/bash

### Give the user the option to select one workload and open all histograms 
### for it. Makes it easier to review all histograms of the same type.

IFS=$'\n'; HISTOGRAMS=( $(find ./results -type f -name "histogram-*") ); unset IFS

UNIQUE_NAMES=()
#Parallel array for counts
UNIQUE_NAMES_COUNTS=()


#Add unique names to the dito array
for f in ${HISTOGRAMS[@]}; do
    basename="$(basename $f)"
    if [[ ! " ${UNIQUE_NAMES[@]} " =~ " $basename " ]]; then
        UNIQUE_NAMES+=("$basename")
        #Hackish way but yeah, want the counts
        UNIQUE_NAMES_COUNTS+=($(find ./results -type f -name "$basename" | wc -l))
    fi
done

echo ${UNIQUE_NAMES_COUNTS[@]}

echo "Please select which histogram you want to view: "
#List the possibilities
i=0
for hist in ${UNIQUE_NAMES[@]}; do
    this_count=${UNIQUE_NAMES_COUNTS[$i]}
    i=$(( ++i ))
    echo "$i) Counted $this_count for $hist"
done

read -p "Select a number [1-$i]: " user_reply

user_reply=${user_reply//[!0-9]/}

#Check user reply within bounds
if [[ $user_reply -gt $i || $user_reply -lt 1 ]]; then
    echo "Reply not within bounds, exiting." 1>&2
    exit 1
fi

#decrement user_reply to serve as index to array
user_reply=$(( --user_reply ))

echo "Selected: ${UNIQUE_NAMES[$user_reply]}"

IFS=$'\n'; SELECTED_HISTOGRAMS=( $(find ./results -type f -name "${UNIQUE_NAMES[$user_reply]}") ); unset IFS

echo "${SELECTED_HISTOGRAMS[@]}"

#Ensure a sort of the histograms (effectively grouping all related ones)
IFS=$'\n'; SELECTED_HISTOGRAMS=( $(sort <<< "${SELECTED_HISTOGRAMS[@]}")); unset IFS

IMG_NAME="gallery-${UNIQUE_NAMES[$user_reply]}.png"

rm -rf $IMG_NAME

#Create a tile and open with feh
montage ${SELECTED_HISTOGRAMS[@]} -mode Concatenate -tile 4x $IMG_NAME

feh --title "Histogram gallery" $IMG_NAME &
