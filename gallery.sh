#!/bin/bash

### Give the user the option to select one workload and open all histograms 
### for it. Makes it easier to review all histograms of the same type.

IFS=$'\n'; HISTOGRAMS=( $(find ./results -type f -name "histogram-*") )

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

IFS=$'\n'; SELECTED_HISTOGRAMS=( $(find ./results -type f -name "${UNIQUE_NAMES[$user_reply]}") )

#Attempt to distribute the dialogs over the screen (not working, doesn't take into account the DE, which takes space)
IFS=$' '; MY_RES=( $(xrandr --current | grep "current" | awk '{print $8 " " $10}') )

RES_X=${MY_RES[0]}
RES_Y=${MY_RES[1]//,/}

WIN_NUM=${#SELECTED_HISTOGRAMS[@]}
# WIN_Y=$(echo "sqrt( ($RES_Y ^ 2) / $WIN_NUM )" | bc)
# WIN_X=$(echo "($WIN_Y * $RES_X) / $RES_Y" | bc)
WIN_X=640
WIN_Y=480

X=0
Y=0

for s in ${SELECTED_HISTOGRAMS[@]}; do
    title="${s//.\/results\//}"
    # title="${title//\// }"

    geostr="${WIN_X}x${WIN_Y}+${X}+${Y}"
    
    kdialog --imgbox $s --title $title --geometry=$geostr &

    X=$(( $X + $WIN_X ))
    if [[ $X -ge $RES_X ]]; then
        X=0
        Y=$(( $Y + $WIN_Y))
    fi
done

sleep 0.2s
read -p "Press enter" forget

killall kdialog