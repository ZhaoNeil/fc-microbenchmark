#!/bin/bash

DIR="${1:-"."}"

find $DIR -type f -name "histogram*" -exec rm {} \;
find $DIR -type f -name "processed*" -exec rm {} \;
find $DIR -type f -name "predictions*" -exec rm {} \;
find $DIR -type f -name "sysmon*.png" -exec rm {} \;
