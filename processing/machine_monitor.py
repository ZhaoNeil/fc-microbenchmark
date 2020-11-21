"""
    Firecracker Microbenchmark
    (c) Niels Boonstra, 2020
    File: machine_monitor.py

    Utility to monitor performance metrics of the host during benchmarking.
    Currently monitors the following metrics:
        - System Load
        - 
"""


import psutil
import sys
import time
import argparse

__PROGRAM_DESCRIPTION__ = """Monitor performance metrics of the host"""

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description=__PROGRAM_DESCRIPTION__)

    arg_parser.add_argument("-o", "--output", default="sys-info.txt", type=str, help="Output to specified file")
    arg_parser.add_argument("-i", "--interval", default=1.0, type=float, help="Specify capture interval")

    args = arg_parser.parse_args()

    cap_interval = args.interval
    output_file = args.output

    write_after = 100000

    print("Starting system monitor", file=sys.stderr)

    with open(output_file, "w") as f:
        #Periodicaly write to file, rather then every interval
        line_buffer = []

        f.write(f"#cpu count: {psutil.cpu_count()}")

        f.write("t,pcpu,pmem,load,")

        try:
            while True:
                if len(line_buffer) >= write_after:
                    f.writelines(line_buffer)
                    line_buffer = []

                
                line_buffer.append(f"")

                time.sleep(cap_interval)
        except KeyboardInterrupt:
            print("Received interrupt, exiting...", file=sys.stderr)


        if len(line_buffer) > 0:
            f.writelines(line_buffer)

    print("System monitor exiting", file=sys.stderr)
    