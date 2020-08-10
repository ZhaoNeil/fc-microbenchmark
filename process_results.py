"""
    Firecracker Microbenchmark
    (c) Niels Boonstra, 2020
    File: process_results.py


    Perform the following operations on a directory with results:
        - Calculate baselines for every workload and argument
        - Calculate deltas using these baselines
        - Calculate average deltas
        - Calculate average runtimes
        - Calculate maximal amount of parallel processes
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

PARAMATER_DIR   = "./parameters"
BASELINE_FILENAME = "baseline.txt"
#Header names
COLUMN_WORKLOAD = "workloadID"
COLUMN_ARGUMENT = "workload argument"
COLUMN_RUN      = "run"
COLUMN_TIMEFC   = "tFC"
COLUMN_TIMEVM   = "tVM"
COLUMN_START    = "start time"
COLUMN_END      = "end time"
COLUMN_DELTA_FC = "d tFC"
COLUMN_DELTA_VM = "d tVM"

def err(msg: str) -> None:
    """Print to stderr"""
    if type(msg) is not str:
        return

    print(msg, file=sys.stderr, flush=True)

def read_csv(filename: str) -> pd.DataFrame:
    """Simple wrapper for reading a csv with pandas"""
    if not path.isfile(filename):
        raise ValueError("{} is not a file, or does not exist".format(filename))

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
            processed_baselines[workload] = {}

        for argument in workload_arguments:
            workload_argument_baseline = workload_baseline.loc[workload_baseline[COLUMN_ARGUMENT] == argument]
            #Calculate the means of the timings for the workload-argument pair
            tVM = round(workload_argument_baseline[COLUMN_TIMEVM].mean())
            tFC = round(workload_argument_baseline[COLUMN_TIMEFC].mean())

            processed_baselines[workload][argument] = [tFC, tVM]

    return processed_baselines

def calculate_average_baselines(directory: str) -> dict:
    if not path.isdir(directory):
        raise ValueError("{} is not a directory!".format(directory))

    sub_dirs = [directory, ]
    all_baselines = []

    #while sub_dirs: suffices, but I like being explicit
    while len(sub_dirs) > 0:
        sub = sub_dirs.pop(0)

        sub_dirs = sub_dirs + [path.join(sub, d) for d in listdir(sub) if path.isdir(path.join(sub, d))]

        all_baselines = all_baselines + [path.join(sub, f) for f in listdir(sub) 
                                 if path.isfile(path.join(sub, f))
                                 and f == BASELINE_FILENAME]

    average_baselines = dict()
    counter = 0

    for f in all_baselines:
        counter += 1
        c = calculate_baselines(read_csv(f))

        for workload, arguments in c.items():
            if workload not in average_baselines:
                average_baselines[workload] = {}

            for argument, values in arguments.items():
                if argument in average_baselines[workload]:
                    average_baselines[workload][argument] = [v1 + v2 for v1, v2 in zip(average_baselines[workload][argument], values)]
                else:
                    average_baselines[workload][argument] = values
    
    

    #Calculate the average using dict comprehension
    #w = workload, key of first dict
    #a = argument, key of second dict
    return  { 
                w: { 
                    a:  [
                            round(v / counter) for v in average_baselines[w][a]
                        ] for a in average_baselines[w].keys()
                    } for w in average_baselines.keys()
            }

def max_concurrent_events(df: pd.DataFrame) -> int:
    """Old function to calculate the maximal amount of concurrent events
    """
    total = len(df)
    max_count = 0
    i = 0
    for idx, row in df.iterrows():
        start_time  = row[COLUMN_START]
        end_time    = row[COLUMN_END]

        curr_count = len(df[((df[COLUMN_END] > start_time) & (df[COLUMN_END] <= end_time)) | ((df[COLUMN_START] >= start_time) & (df[COLUMN_START] < end_time)) | ((start_time >= df[COLUMN_START]) & (end_time <= df[COLUMN_END]))])


        # curr_count = 0
        # for idx2, row2 in df.iterrows():
        #     if start_time < row2[COLUMN_END]
        #         curr_count += 1

        # curr_count = len(df[(df[COLUMN_START] <= df.loc[idx, COLUMN_START]) & (df[COLUMN_END] < df.loc[idx, COLUMN_END])])
        if curr_count > max_count:
            max_count = curr_count

        print( "\r{}/{}".format(i, total), file=sys.stderr, end="")
        i += 1
        # print("start = {}, end = {}, # = {}".format(start_time, end_time, curr_count))

    err("")


    return max_count

def concurrency_histogram(df: pd.DataFrame, bin_size=1) -> list:
    """Given a processed dataframe, calculate the maximal number of concurrent 
    jobs going on at a certain point in the runtime of the benchmark.

    Furthermore, a histogram can be plotted with the data returned by this 
    function
    
    :param df: The dataframe with start and end timestamps
    :type df: pd.DataFrame
    :param bin_size: Bin size of the histogram in milliseconds
    :type bin_size: int
    :returns: A list with the bins
    :rtype: list
    """
    if type(df) is not pd.DataFrame:
        raise TypeError("max_concurrent_events: df is not of correct type.")

    if not (COLUMN_END in df and COLUMN_START in df): 
        raise ValueError("max_concurrent_events: df misses information!")

    err("Calculating max. concurrent instances...")

   
    end_time = round(df[COLUMN_END].max())

    second_bins = [-1 for i in range(0, end_time, bin_size)]
    check = second_bins.copy()

    for second in range(0, end_time, bin_size):
        curr_second = 0
        bin_start = second
        bin_end = second + bin_size
        #Naive approach
        # for idx, row in df.iterrows():
        #     if (row[COLUMN_END] > bin_start and row[COLUMN_END] <= bin_end) or (row[COLUMN_START] >= bin_start and row[COLUMN_START] < bin_end) or (bin_start >= row[COLUMN_START] and bin_end <= row[COLUMN_END]):
        #         curr_second += 1
        # #Do this here avoids repeatedly calculating the index
        # second_bins[round(second / bin_size)] = curr_second

        #Panda-ized approach (probably faster)
        second_bins[round(second/bin_size)] = len(df[((df[COLUMN_END] > bin_start) & (df[COLUMN_END] <= bin_end)) | ((df[COLUMN_START] >= bin_start) & (df[COLUMN_START] < bin_end)) | ((bin_start >= df[COLUMN_START]) & (bin_end <= df[COLUMN_END]))])


        print("\r{}/{} seconds processed.".format(second, end_time), file=sys.stderr, end="")

    err("")

    return second_bins

def calculate_deltas(df: pd.DataFrame, baselines: dict) -> pd.DataFrame:
    if type(df) is not pd.DataFrame or type(baselines) is not dict:
        raise TypeError("calculate_deltas: arguments are of incorrect type")

    if (COLUMN_START not in df) or (COLUMN_TIMEFC not in df) \
        or (COLUMN_WORKLOAD not in df) or (COLUMN_ARGUMENT not in df) \
        or (COLUMN_TIMEVM not in df):
        raise ValueError("calculate_deltas: missing columns in data")

    #Calculate deltas, end times
    delta_fc = [0 for i in range(0, len(df))]
    delta_vm = delta_fc.copy()
    end_time = delta_fc.copy()

    for idx, row in df.iterrows():
        baseline = baselines.get(row[COLUMN_WORKLOAD], {0: 0}).get(row[COLUMN_ARGUMENT], [0, 0])
        delta_fc[idx] = row[COLUMN_TIMEFC] - baseline[0]
        delta_vm[idx] = row[COLUMN_TIMEVM] - baseline[1]
        end_time[idx] = row[COLUMN_START] + row[COLUMN_TIMEFC]

    df[COLUMN_END] = end_time
    df[COLUMN_DELTA_FC] = delta_fc
    df[COLUMN_DELTA_VM] = delta_vm

    return df

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

    processed_files = 0
    to_process = len(dir_files)

    for result_file in dir_files:
        processed_files += 1
        err("{}/{}: Processing {}".format(processed_files, to_process, result_file))
        #Result files are automatically named after the arguments file with
        #results added as prefix
        if not result_file.startswith("results"):
            err("Skipping file {}".format(result_file))
            continue

        ### Read the CSV and perform some data transformations

        result_df = read_csv(path.join(directory, result_file))

        #Sort on starting time and subtract the initial time
        result_df.sort_values(by=COLUMN_START, inplace=True)
        start_time = result_df[COLUMN_START].min()
        result_df[COLUMN_START] = result_df[COLUMN_START] - start_time

        result_df = calculate_deltas(result_df, baselines)

        result_df.to_csv(path.join(directory, "processed-{}".format(result_file)), index=False)

        ### Calculate some meta-data and save it as well

        conc_events = concurrency_histogram(result_df)
        meta_data = {}
        totals = {}
        stats = {}

        totals["runtime"] = result_df[COLUMN_END].max()
        totals["# instances"] = len(result_df)
        totals["# max concurrent instances"] = max(conc_events)
        totals["delta tFC"] = result_df[COLUMN_DELTA_FC].sum()
        totals["delta tVM"] = result_df[COLUMN_DELTA_VM].sum()

        stats["Mean delta tFC"] = result_df[COLUMN_DELTA_FC].mean()
        stats["Mean delta tVM"] = result_df[COLUMN_DELTA_VM].mean()

        meta_data["Totals"] = totals
        meta_data["Statistics"] = stats

        print(meta_data)
 
           

if __name__ == "__main__":
    # process_data("./results/001")

    arg_parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION_)

    arg_parser.add_argument("directory", type=str, help="Directory containing the results")
    arg_parser.add_argument("-output", "-o", help="Write to the specified file")

    if len(sys.argv) < 2:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    if args.directory:
        process_data(args.directory)