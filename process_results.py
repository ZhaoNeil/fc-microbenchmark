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

import sys
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os import path, listdir

_PROGRAM_DESCRIPTION_ = """Process a folder containing results.

At least a file with baselines must be present, as well as one results set.

"""

WORKLOAD_DIR   = "./workloads"
RESULTS_PREFIX = "results-"
BASELINE_FILENAME = "baseline.txt"
BASELINES_FILENAME = "baselines.txt"
HISTO_PREFIX = "histogram-"
HISTO_EXT = ".png"
#Header names
COLUMN_WORKLOAD = "workloadID"
COLUMN_ARGUMENT = "workload argument"
COLUMN_RUN      = "run"
COLUMN_TIMEFC   = "tFC"
COLUMN_TIMEVM   = "tVM"
COLUMN_START    = "start time"
COLUMN_END      = "end time"
COLUMN_PREDICT_END = "pred. end time"
COLUMN_DELTA_FC = "d tFC"
COLUMN_DELTA_VM = "d tVM"

def recursive_file_search(directory: str, list_filter = None) -> list:
    """
        Finds all files in a directory and its subdirectories.

        If list_filter is defined, pass it to filter which is called on the list
        before returning
    """
    sub_dirs = [path.abspath(directory), ]
    all_files = []
    #while sub_dirs: suffices, but I like being explicit
    while len(sub_dirs) > 0:
        sub = sub_dirs.pop(0)

        sub_dirs = sub_dirs + [path.join(sub, d) for d in listdir(sub) if path.isdir(path.join(sub, d))]

        all_files = all_files + [path.join(sub, f) for f in listdir(sub) 
                                 if path.isfile(path.join(sub, f))]

    if list_filter is not None:
        return filter(list_filter, all_files)

    return all_files

def err(msg: str) -> None:
    """Print to stderr"""
    if type(msg) is not str:
        return

    print(msg, file=sys.stderr, flush=True)

def read_csv(filename: str) -> pd.DataFrame:
    """Simple wrapper for reading a csv with pandas"""
    if not path.isfile(filename):
        raise ValueError("{} is not a file, or does not exist".format(filename))

    return pd.read_csv(filename, skipinitialspace=True, comment="#")

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

def predict_workload_runtime(workload: str, baselines: dict) -> pd.DataFrame:
    if path.isdir(workload):
        raise NotImplementedError("Call predict_multiple_workloads for batch prediction!")
    else:
        workload = read_csv(workload)

    if len(workload.columns) == 2:
        start_col = [0 for i in len(workload)]
        workload = workload.append(start_col)
        del start_col

    workload.rename(columns={0: COLUMN_WORKLOAD, 1: COLUMN_ARGUMENT, 2:COLUMN_START}, inplace=True)
    #Quick access lambda for better readability, selects tFC
    get_baseline = lambda idx: baselines.get(workload.iloc[idx, 0], {0: 0}).get(workload.iloc[idx, 1], [0, 0])[0]


    #As the COLUMN_START now holds intervals between two instances, we have to
    #shift the whole series by one, as the first instance starts at time 0
    workload[COLUMN_START] = workload[COLUMN_START].shift(periods=1, fill_value=0)
    
    #End_times will be calculated in parallel to the starting times
    end_times = [0 for i in range(0, len(workload))]
    end_times[0] = get_baseline(0)

    #Calculate starting points for each workload, rather than intervals
    for i in range(1, len(workload)):
        workload.loc[i, COLUMN_START] += workload[COLUMN_START][i-1]
        #Add avg running time to the start time, use tFC (which is always the biggest number)
        end_times[i] = round(workload.loc[i, COLUMN_START] * 1000) + get_baseline(i)
                       

    #All start-times to unfractioned millisecs
    workload[COLUMN_START] = workload[COLUMN_START] * 1000
    workload[COLUMN_START] = workload[COLUMN_START].astype("int32")

    workload[COLUMN_PREDICT_END] = end_times


    #Print some statistics to stderr (will also be appended to the dataframe)
    err("Workload: {}".format(workload))
    err("\tPredicted runtime = {}".format(workload[COLUMN_PREDICT_END].max()))
    err("\t{}th instance determines runtime".format(workload[COLUMN_PREDICT_END].idxmax()))

    workload[COLUMN_END] = workload[COLUMN_PREDICT_END]
    max_conc_evt = concurrency_histogram(workload, 1000)

    err("\tMaximal amount of concurrent instances: {}".format(max_conc_evt)) 

    return workload

def calculate_average_baselines(directory: str = "", files: list = []) -> dict:
    all_baselines = []
    if directory:
        if not path.isdir(directory):
            raise FileNotFoundError("{} is not a directory!".format(directory))
        is_baseline_filter = lambda x: x == BASELINE_FILENAME or x == BASELINES_FILENAME
        all_baselines = recursive_file_search(directory, list_filter=is_baseline_filter)
    elif files:
        all_baselines = files

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
    """Finds the maximal number of concurrent events at a time slice.
    """
    total = len(df)
    max_count = 0
    i = 0
    for _, row in df.iterrows():
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

def concurrency_histogram(df: pd.DataFrame, df_pred: pd.DataFrame, output:str = "", bin_size=1000):
    """Given a processed dataframe, calculate the maximal number of concurrent 
    jobs going on in certain bins (histogram).

    Furthermore, a histogram can be plotted with the data returned by this 
    function
    
    :param df: The dataframe with start and end timestamps
    :type df: pd.DataFrame
    :param output: Path to (not existing) file to which the histogram will be written
    :type output: str
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
    second_bins_pred = second_bins.copy()
    seconds     = [i for i in range(0, end_time, bin_size)]

    for second in range(0, end_time, bin_size):
        bin_start = second
        bin_end = second + bin_size

        #Panda-ized approach (probably faster)
        second_bins[round(second/bin_size)] = len(df[((df[COLUMN_END] > bin_start) & (df[COLUMN_END] <= bin_end)) | ((df[COLUMN_START] >= bin_start) & (df[COLUMN_START] < bin_end)) | ((bin_start >= df[COLUMN_START]) & (bin_end <= df[COLUMN_END]))])
        if df_pred:
            second_bins_pred[round(second/bin_size)] = len(df_pred[((df_pred[COLUMN_END] > bin_start) & (df_pred[COLUMN_END] <= bin_end)) | ((df_pred[COLUMN_START] >= bin_start) & (df_pred[COLUMN_START] < bin_end)) | ((bin_start >= df_pred[COLUMN_START]) & (bin_end <= df_pred[COLUMN_END]))])


        print("\r{}/{} seconds processed.".format(second, end_time), file=sys.stderr, end="")

    
    if output:
        plt.hist(seconds, len(seconds), weight=second_bins, label="Result")
        if df_pred:
            plt.hist(seconds, len(seconds), weight=second_bins_pred, label="Prediction")
            plt.legend(loc="upper right")
        plt.xlabel("seconds")
        plt.ylabel("# instances")
        plt.savefig(output)

    return second_bins, second_bins_pred

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

def process_file(filename: str, baselines: dict) -> pd.DataFrame:
    """
        Processes a single file and write the results to another file.
        This file will have the systematic name "processed_{filename}"
    """
    if not path.isfile(filename):
        raise FileNotFoundError("File {} does not exist!".format(filename))

    write_to_name = "processed-{}".format(path.basename(filename))

    ### Read the CSV and perform some data transformations
    result_df = read_csv(filename)

    #Sort on starting time and subtract the initial time
    result_df.sort_values(by=COLUMN_START, inplace=True)
    start_time = result_df[COLUMN_START].min()
    result_df[COLUMN_START] = result_df[COLUMN_START] - start_time

    result_df = calculate_deltas(result_df, baselines)


    ### Calculate some meta-data

    to_write = []

    to_write.append(("Total time", result_df[COLUMN_END].max()))
    to_write.append(("No. instances", len(result_df)))
    to_write.append(("Max. concurrent events", max_concurrent_events(result_df)))
    to_write.append(("Sum of delta tFC", result_df[COLUMN_DELTA_FC].sum()))
    to_write.append(("Sum of delta tVM", result_df[COLUMN_DELTA_VM].sum()))
    to_write.append(("Mean of delta tFC", result_df[COLUMN_DELTA_FC].mean()))
    to_write.append(("Mean of delta tVM", result_df[COLUMN_DELTA_VM].mean()))

    with open(write_to_name, "w") as f:
        for t in to_write:
            f.write("# {}: {}".format(t[0], t[1]))

    #Append the processed df to the file
    result_df.to_csv(path.join(path.split(filename)[0], write_to_name), mode="a", index=False)

    return result_df

def process_data(directory: str) -> None:
    """
        Gather all files in a directory and its subdirectories and process these
        result files. It is advisable to call this function per directory that 
        contains data from multiple machines/experiments. For example, a 
        directory that contains all experiments for the CFS scheduler.
    """
    if not path.isdir(directory):
        raise FileNotFoundError("Directory {} does not exist!".format(directory))

    # Gather all files from this directory
    directory = path.abspath(directory)

    all_files = recursive_file_search(directory)

    all_files = [path.split(f) for f in all_files]
    files_per_dir = {}

    for f in all_files:
        files_per_dir.setdefault(f[0], []).append(f[1])

    baselines_per_dir = {}
    #Dict comprehension?
    for d, baselines in files_per_dir.items():
        for baseline in baselines: 
            if baseline == "baseline.txt" or baseline == "baselines.txt":
                baselines_per_dir[d] = baseline

    #Ensure no dirs without results or baselines are processed
    keys_baselines_per_dir = set(baselines_per_dir.keys())
    keys_files_per_dir = set(files_per_dir.keys())
    diff = keys_baselines_per_dir ^ keys_files_per_dir

    for d in diff:
        err("{} omitted, no baselines/results found!".format(d))
        if d in baselines_per_dir:
            del baselines_per_dir[d]
        if d in files_per_dir:
            del files_per_dir[d]


    #Calculate this once, as we're gonna use this for the predictions
    err("Calculating average baselines...")
    avg_baselines = calculate_average_baselines(files=[path.join(key, value) for key, value in baselines_per_dir.items()])

    err("Determining bin size by picking smallest value for primenumber baselines...")
    bin_size = avg_baselines.get(0, {})
    bin_size = max(bin_size.get(min(bin_size.keys()), []))
    err("Picked bin_size = {}".format(bin_size))

    #Pre-calculate all the baselines
    for d, baseline in baselines_per_dir.items():
        baselines_per_dir[d] = calculate_baselines(read_csv(path.join(d, baseline)))

    err("Starting predictions per workload...")
    #Scheme: workload: prediction_df
    predictions = {}
    #Calculate all predictions
    for d, files in files_per_dir.items():
        for f in files:
            workload_name = path.basename(f)
            basename = workload_name
            #Skip work done
            if workload_name in predictions:
                continue

            if workload_name.startswith(RESULTS_PREFIX):
                workload_name = workload_name[len(RESULTS_PREFIX):]
                workload_name = path.join(WORKLOAD_DIR, workload_name)

                if path.isfile(workload_name):
                    err("Calculating predictions for {}".format(basename))
                    predictions[basename] = predict_workload_runtime(workload_name, avg_baselines)
                else:
                    err("Workload file {} does not exist, where it should?".format(workload_name))

    #Process all the files
    err("Starting processing of results...")
    for d, files in files_per_dir.items():
        for f in files:
            #Perhaps delete these baselines somewhere above? As we've already processed them
            if f == BASELINE_FILENAME or f == BASELINES_FILENAME:
                continue

            err("Processing {}...".format(path.join(d,f)))
            workload_name = f[len(RESULTS_PREFIX):]
            preds = predictions.get(workload_name, None)
            proc_df = process_file(path.join(d, f), baselines_per_dir[d])

            histo_name = HISTO_PREFIX + path.splitext(f)[0] + HISTO_FORMAT
            # Save the bins to avoid extra work in case of rerender of histo?
            _, _ = concurrency_histogram(df=proc_df, df_pred=preds, output=path.join(d, histo_name), bin_size=bin_size)




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION_)

    arg_parser.add_argument("directory", type=str, help="Directory containing the results per scheduler")

    if len(sys.argv) < 2:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    if args.directory:
        process_data(args.directory)