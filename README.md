# fc-microbenchmark

This micro-benchmark consists of three simple programs:
 * A CPU-bound program
    * Prime-number calculation
 * A I/O-bound program
    * dd command line workload
 * A memory-bound program
    * The [stream](https://www.cs.virginia.edu/stream/) benchmark program

In order to benchmark the microVM-architecture, different workloads have to be generated. The workloads all differ in the following parameters:
 * Mix of programs
    * e.g. 33% CPU-bound, 33%, I/O-bound, 33% memory-bound
 * Different limit on amount of Firecracker instances
    * e.g. never more than 1000 instances at once
 * Workloads with different arrival patterns
    * arrival patterns will use the poisson process

## Getting Started

Firstly, the root filesystem (rootfs) must be generated. This is an installation of the [Alpine Linux mini root filesystem](https://alpinelinux.org/downloads/).
Secondly, a Linux kernel must be selected. This repo does supply a Linux kernel, but in case a customized kernel is desired, the instructions for building a kernel suited for Firecracker can be found [here](https://github.com/firecracker-microvm/firecracker/blob/master/docs/rootfs-and-kernel-setup.md).

When all of the above is done, then the benchmark can be started using:

```shell
python3 microbench.py
```

For different options, use the `-h` or `--help` argument.