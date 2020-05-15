# fc-microbenchmark

This micro-benchmark consists of three simple programs:
 * A CPU-bound program
    * Prime-number calculation
 * A I/O-bound program
    * dd command line workload
    * Block size is set to 1M
    * Count parameter is set by the workload argument
 * A memory-bound program
    * The [stream](https://www.cs.virginia.edu/stream/) benchmark program
    * Modified `STREAM_ARRAY_SIZE` to a value resulting in a memory usage of 91.6MiB
    * Added the ability to change `NTIMES` by making it an argument, e.g. ./stream 10 sets `NTIMES=10`.

In order to benchmark the microVM-architecture, different workloads have to be generated. The workloads all differ in the following parameters:
 * Different limit on amount of Firecracker instances
    * e.g. never more than 1000 instances at once
    * e.g. Fire up *n* instances consecutively 
 * Workloads with different arrival patterns
    * arrival patterns will use the Poisson process
 * Different parameters for each program
 * Different amounts of each program

The different parameters and amounts for the programs are read from a text file. An example of such a file is `baseline-arguments.txt`:

```
0, 1000000
0, 2500000
...
```

The first number maps to a program array, which is read from `workloads.txt`. The second number is the parameter for this program. As this text file is read per line, the mix of programs can be specified via this file as well.

## Getting Started

Firstly, the root filesystem (rootfs) must be generated. This is an installation of the [Alpine Linux mini root filesystem](https://alpinelinux.org/downloads/).

Secondly, a Linux kernel must be selected. This repo does supply a Linux kernel, but in case a customized kernel is desired, the instructions for building a kernel suited for Firecracker can be found [here](https://github.com/firecracker-microvm/firecracker/blob/master/docs/rootfs-and-kernel-setup.md).

When all of the above is done, then the benchmark can be started using:

```shell
./start.sh -m benchmark -n1000
```

For different options, use the `-h` argument.