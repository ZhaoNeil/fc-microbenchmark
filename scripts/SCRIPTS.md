# The ./scripts/ directory


In this directory all scripts necessary for starting the benchmark are placed,
except for the `setup.sh` and the `start.sh` scripts.

## `commands.sh`
In order to keep the other scripts as readable as possible, certain functions, 
and their dependencies are located in this script and will be sourced when needed.

The function currently included in this file are:
* `curl_put`
  * Argument 1: URL where the command is sent, i.e. /boot-source, _string_
  * Accepts an HEREDOC as command to be sent
* `issue_commands`
  * Argument 1: Specifies whether the runtimes of the workloads and the Firecracker instance need to be timed, _bool_

## `baseline.sh`

This file determines the baseline running times of each workload. This is done by running an *x* amount of instances sequentially, each time measuring the total execution time of the microVM and the execution time of the workload inside the microVM.

This scripts expects five parameters:
1. The location of the kernel, default: ../resources/vmlinux. *string*
2. The location of the rootfs, default: ../resources/rootfs.ext4. *string*
3. The file location of the `workloads.txt` file, default: ./workloads.txt. *string*
4. The number of instances to be run for each workload, *integer*, larger than, or equal to 5
5. The location of the workload and arguments file, default: ../baseline-arguments.txt

## `launch-firecracker.sh`



## `create-root-fs.sh`
Builds a blank rootfs based on Alpine Linux.

Arguments:
1. Filename of the filesystem to be created, *string*

