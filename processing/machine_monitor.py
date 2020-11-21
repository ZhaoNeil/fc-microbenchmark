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

        f.write(f"#cpu_count: {psutil.cpu_count()}\n")
        f.write(f"#total_mem: {psutil.virtual_memory().total}\n")

        #cpu_inter is the sum of waiting for i/o, software and hardware interrupts
        #mem_avail -> memory available w/o system having to swap
        #

        f.write("t,cpu_user,cpu_system,cpu_idle,cpu_inter,cpu_percentage,load_1m,mem_avail,swap_used\n")

        try:
            while True:
                #Write to file after x lines added
                if len(line_buffer) >= write_after:
                    f.writelines(line_buffer)
                    line_buffer = []

                #Measure metrics
                t = time.time()
                cpu_times = psutil.cpu_times()
                cpu_usage = psutil.cpu_percent(interval=None, percpu=False)
                load_1m = psutil.getloadavg()[0]
                mem_avail = psutil.virtual_memory().available
                swap_used = psutil.swap_memory().used
                
                cpu_inter = cpu_times.irq + cpu_times.softirq + cpu_times.iowait

                line_buffer.append(f"{t},{cpu_times.user},{cpu_times.system},{cpu_times.idle},{cpu_inter},{cpu_usage},{load_1m},{mem_avail},{swap_used}\n")

                time.sleep(cap_interval)
        except KeyboardInterrupt:
            print("Received interrupt, exiting...", file=sys.stderr)


        if len(line_buffer) > 0:
            f.writelines(line_buffer)

    print("System monitor exiting", file=sys.stderr)
    