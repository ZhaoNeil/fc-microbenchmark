"""
    Firecracker Microbenchmark
    (c) Niels Boonstra, 2020
    File: predict_runtimes.py

    Predict runtimes for each benchmark workload.
    For this, only the baselines are needed, preferably as much as possible 
    (to even out small variety in machines)

    The functions in this script were merged to process_results.py
"""

from os import path, listdir
import sys
import argparse
import numpy
import pandas as pd
import matplotlib.pyplot as plt

from process_results import *



_PROGRAM_DESCRIPTION_ = """Predict run-times of benchmark workload(s)

Given a directory containing multiple baselines, or a single baselines file, 
predict the runtime of a given workload, or multiple workloads.

If the baselines argument is a directory, all baselines in that folder, or its
subfolders will be taken into consideration, if and only if that file is named
"{baseline}"
""".format(baseline=BASELINE_FILENAME)

def predict_multiple_workloads(workload_directory: str, baseline_directory: str):
    pass
if __name__ == "__main__":
    # predict_workload_runtime("./results/001/baseline.txt", "./parameters/poisson-100-1hr-equal.txt")

    arg_parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION_)

    arg_parser.add_argument("baseline", type=str, help="Either a directory or a single file containing baseline measurements")
    arg_parser.add_argument("workload", type=str, help="Either a directory or a single file containing parameters for the workload whose run-time will be predicted")
    arg_parser.add_argument("-output", "-o", help="Write to the specified file")

    if len(sys.argv) < 2:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    predict_workload_runtime(args.baseline, args.workload)