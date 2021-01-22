#!/bin/bash

### Give the user the option to select one workload and open all histograms 
### for it. Makes it easier to review all histograms of the same type.

user_reply=${1:-"?"}
OLDIFS=$IFS
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

if [[ "$user_reply" == "?" ]]; then
    echo ${UNIQUE_NAMES_COUNTS[@]}

    echo "Please select which histogram you want to view: "
    #List the possibilities
    i=0
    for hist in ${UNIQUE_NAMES[@]}; do
        this_count=${UNIQUE_NAMES_COUNTS[$i]}
        i=$(( ++i ))
        echo "$i) Counted $this_count for $hist"
    done

    read -p "Select a number [1-$i], or type 'all' to generate for all: " user_reply
else
    i=${#UNIQUE_NAMES[@]}
fi

if [[ "$user_reply" != "all" ]]; then
    user_reply=${user_reply//[!0-9]/}
fi

#Check user reply within bounds
if [[ $user_reply -gt $i || $user_reply -lt 1 && "$user_reply" != "all" ]]; then
    echo "Reply: '$user_reply' not within bounds, exiting." 1>&2
    exit 1
fi

if [[ "$user_reply" != "all" ]]; then
    #decrement user_reply to serve as index to array
    user_reply=$(( --user_reply ))

    echo "Selected: ${UNIQUE_NAMES[$user_reply]}"

    end_loop=$user_reply

else
    echo "Selected: all"
    user_reply=0
    end_loop=${#UNIQUE_NAMES[@]}

fi

mkdir ./montage-tmp

for ((i=user_reply; i<=end_loop; i++)); do

    echo "Generating gallery for ${UNIQUE_NAMES[$i]}..."

    IFS=$'\n'; SELECTED_HISTOGRAMS=( $(find ./results -type f -name "${UNIQUE_NAMES[$i]}") ); unset IFS

    #Ensure a sort of the histograms (effectively grouping all related ones)
    IFS=$'\n'; SELECTED_HISTOGRAMS=( $(sort <<< "${SELECTED_HISTOGRAMS[@]}")); unset IFS

    VIEWBOX=()
    TAILBOX=()

    IFS=$OLDIFS
    for hist in ${SELECTED_HISTOGRAMS[@]}; do 
        histdir="$(dirname $hist)"
        sysmonname="$(basename $hist)"
        sysmonname="sysmon-${sysmonname##histogram-results-}"

        echo $sysmonname

        if [[ -e "$histdir/$sysmonname" ]]; then
            echo "Found sysmon graph for $hist"
            VIEWBOX+=( $hist "$histdir/$sysmonname" )
        else
            echo "$hist does not have a sysmon graph, adding to tail of list later"
            TAILBOX+=( $hist )
        fi

    done

    IMG_NAME="gallery-${UNIQUE_NAMES[$i]}"

    rm -rf $IMG_NAME

    #Create a tile and open with feh
    montage -define registry:temporary-path=./montage-tmp -mode Concatenate -tile 2x -limit memory 3GiB -limit map 1GiB ${VIEWBOX[@]} ${TAILBOX[@]} $IMG_NAME

    if [[ $user_reply -eq $end_loop ]]; then
        if [[ -e $IMG_NAME ]]; then
            feh --title "Histogram gallery" --scale-down $IMG_NAME &
        else
            echo "Could not open image, something went wrong while generating $IMG_NAME!"
        fi
    fi

done

rm -rf ./montage-tmp
