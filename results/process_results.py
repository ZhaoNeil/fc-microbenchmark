"""
    Firecracker Microbenchmark
    (c) Niels Boonstra, 2020
    File: process_results.py


    Perform the following operations on a directory with results:
        - Calculate baselines for every workload and argument
        - Calculate deltas using these baselines
        - Calculate average deltas
        - Calculate average runtimes
        - Create graphs
"""

import pandas as pd
import numpy as np
import sys
import argparse
from os import path, listdir

_PROGRAM_DESCRIPTION_ = """Process a folder containing results.

At least a file with baselines must be present, as well as one results set.

"""
BASELINE_FILENAME = "baseline.txt"
#Header names
COLUMN_WORKLOAD = "workloadID"
COLUMN_ARGUMENT = "workload argument"
COLUMN_RUN      = "run"
COLUMN_TIMEFC   = "tFC"
COLUMN_TIMEVM   = "tVM"
COLUMN_START    = "start time"

def err(msg: str) -> None:
    """Print to stderr"""
    if type(msg) is not str:
        return

    print(msg, file=sys.stderr)

def read_csv(filename: str) -> pd.DataFrame:
    """Simple wrapper for reading a csv with pandas"""
    if not path.isfile(filename):
        raise ValueError("{} is not a file".format(filename))

    return pd.read_csv(filename, skipinitialspace=True)

def calculate_baselines(baselines: pd.DataFrame) -> dict:
    if type(baselines) is not pd.DataFrame:
        raise TypeError("calculate_baselines: invalid object type passed.")

    processed_baselines = {}

    distinct_workloads = baselines[COLUMN_WORKLOAD].unique()

    for workload in distinct_workloads:
        #Filter for current workload
        workload_baseline = baselines.loc[baselines[COLUMN_WORKLOAD] == workload]
        #Get all the arguments
        workload_arguments = workload_baseline[COLUMN_ARGUMENT].unique()

        if workload not in processed_baselines:
            processed_baselines[workload] = []

        for argument in workload_arguments:
            workload_argument_baseline = workload_baseline.loc[workload_baseline[COLUMN_ARGUMENT] == argument]
            #Calculate the means of the timings for the workload-argument pair
            tVM = workload_argument_baseline[COLUMN_TIMEVM].mean()
            tFC = workload_argument_baseline[COLUMN_TIMEFC].mean()

            processed_baselines[workload].append([argument, tFC, tVM])

    return processed_baselines


def process_data(directory: str) -> None:
    if not path.isdir(directory):
        err("{} is not a directory!".format(directory))
        return

    directory = path.abspath(directory)


    #Get a list of all files in the directory
    dir_files = [f for f in listdir(directory) if path.isfile(path.join(directory, f))]

    #Check if there are any results and a baseline file
    has_results = False
    has_baseline = False
    for f in dir_files[:]:
        #Stop checking if at least one result and a baseline
        if has_results and has_baseline:
            break

        if f.startswith("results"):
            has_results = True

        if f == BASELINE_FILENAME:
            has_baseline = True
            dir_files.remove(f)

    if not has_baseline:
        err("The directory does not contain a {} file.".format(BASELINE_FILENAME))
        return
    if not has_results:
        err("The directory does not contain at least one result.")
        return

    #Calculate the baselines for later use
    baselines = calculate_baselines(read_csv(path.join(directory, BASELINE_FILENAME)))

    for result_file in dir_files:
        #Result files are automatically named after the arguments file with
        #results added as prefix
        if not result_file.startswith("results"):
            err("Skipping file {}".format(result_file))
            continue

        result_df = pd.read_csv(path.join(directory, result_file), skipinitialspace=True)

        #Sort on starting time and subtract the initial time
        result_df.sort_values(by=COLUMN_START, inplace=True)
        result_df[COLUMN_START] = result_df[COLUMN_START] - result_df[COLUMN_START].min()

        

        

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION_)

    arg_parser.add_argument("directory", type=str, help="Directory containing the results")

    if len(sys.argv) < 2:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    if args.directory:
        process_data(args.directory)