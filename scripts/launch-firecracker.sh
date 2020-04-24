#!/bin/bash

kernelLocation="${1:?"Need first argument, kernel location"}"
fsLocation="${2:?"Need second argument, filesystem location"}"
fcID=${3:-1}
workLoad=${4:-"default"}
cpuCount=1
memSize=128
fcSock="/tmp/firecracker-$fcID.socket"

#Check firecracker installation
which firecracker > /dev/null

if [[ $? -eq 1 ]]; then
    echo "Firecracker not found, exiting..."
    exit 1
fi


#For debugging purposes
asDeamon=0

#Shamelessly copied curl_put from https://github.com/firecracker-microvm/firecracker-demo/
CURL=(curl --silent --show-error --header "Content-Type: application/json" --unix-socket "$fcSock" --write-out "HTTP %{http_code}")

curl_put() {
    local URL_PATH="$1"
    local OUTPUT RC
    OUTPUT="$("${CURL[@]}" -X PUT --data @- "http://localhost/${URL_PATH#/}" 2>&1)"
    RC="$?"
    if [ "$RC" -ne 0 ]; then
        echo "Error: curl PUT ${URL_PATH} failed with exit code $RC, output:"
        echo "$OUTPUT"
        return 1
    fi
    # Error if output doesn't end with "HTTP 2xx"
    if [[ "$OUTPUT" != *HTTP\ 2[0-9][0-9] ]]; then
        echo "Error: curl PUT ${URL_PATH} failed with non-2xx HTTP status code, output:"
        echo "$OUTPUT"
        return 1
    fi
}

issue_commands() {
    local KERNEL_ARGS

    KERNEL_ARGS="reboot=k panic=1 pci=off softlevel=$workLoad"

    if [[ $asDeamon -eq 1 ]]; then
        KERNEL_ARGS="console=ttyS0 ' $KERNEL_ARGS"
    fi

curl_put '/boot-source' <<EOF
{
  "kernel_image_path": "$kernelLocation",
  "boot_args": "$KERNEL_ARGS"
}
EOF

curl_put '/machine-config' <<EOF
{
 "vcpu_count": $cpuCount,
 "mem_size_mib": $memSize,
 "ht_enabled": false
}
EOF

curl_put '/drives/1' <<EOF
{
  "drive_id": "1",
  "path_on_host": "$fsLocation",
  "is_root_device": true,
  "is_read_only": false
}
EOF


curl_put '/actions' <<EOF
{
  "action_type": "InstanceStart"
}
EOF

    return 0;
}


if [[ "$5" == "d" ]]; then
    asDeamon=1
elif [[ "$5" == "c" ]]; then
    asDeamon=1
    echo "Issueing commands only"
    issue_commands
    exit 0
fi



rm -rf "$fcSock"

echo "Launching Firecracker..."
if [[ $asDeamon -eq 0 ]]; then
    firecracker --api-sock "$fcSock"
elif [[ $asDeamon -ne 0 ]]; then
    firecracker --api-sock "$fcSock" &
fi
