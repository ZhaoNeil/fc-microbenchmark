# The ./scripts/ directory


In this directory all scripts necessary for starting the benchmark are placed,
except for the `setup.sh` and the `start.sh` scripts.

## `baseline.sh`

This file determines the baseline running times of each workload. This is done by running an *x* amount of instances sequentially, each time measuring the total execution time of the microVM and the execution time of the workload inside the microVM.

This scripts expects two parameters:
1. The file location of the `workloads.txt` file, *string*
2. The number of instances to be run for each workload, *integer*, larger than, or equal to 5

## `launch-firecracker.sh`


