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
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from os import path, listdir

_PROGRAM_DESCRIPTION_ = """Process a folder containing results.

At least a file with baselines must be present, as well as one results set.

"""

MY_LOCATION = path.dirname(path.abspath(__file__))

WORKLOAD_DIR = path.abspath(path.join(MY_LOCATION, "../workloads"))
PREDICTION_PREFIX = "predictions-"
RESULTS_PREFIX = "results-"
RESULTS_EXT = ".txt"
SYSMON_RESULTS_PREFIX = "sysmon-"
SYSMON_EXT = ".txt"
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
    """
    Read a file that contains multiple runs of the same pair. The format of the
    file must be:

    workload id, workload argument, run number, tFC, tVM

    This function calculates the average over all runs of each unique pair of
    workload id and workload argument.

    """
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

def predict_workload_runtime(filepath: str, baselines: dict, write_dir: str = "") -> pd.DataFrame:
    """
    Predict how long a workload *should* take when run on an ideal system, so
    with inf. CPUs, perfect multitasking etc.

    For this, it needs baseline measurements and a path to the workload.

    This function does *NOT* work for non-Poisson workloads, as these would 
    always finish when the slowest task in the workload finishes.
    """
    workload = None
    if path.isdir(filepath):
        raise NotImplementedError("workload must point to a file, not a directory!")
    else:
        workload = pd.read_csv(filepath, header=None, skipinitialspace=True)

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

    workload[COLUMN_END] = workload[COLUMN_PREDICT_END]

    if write_dir:
        output_name = path.join(write_dir, PREDICTION_PREFIX + path.basename(filepath))

        with open(output_name, "w") as f:
            f.write("# Workload\t{} \n".format(path.basename(filepath)))
            f.write("# Predicted runtime\t{} \n".format(workload[COLUMN_PREDICT_END].max()))
            f.write("# Instance determining runtime\t{} \n".format(workload[COLUMN_PREDICT_END].idxmax()))
            f.write("# Maximal concurrency\t{} \n".format(max_concurrent_events(workload)))
        
        workload.to_csv(output_name, mode="a", index=False)

    return workload

def calculate_average_baselines(directory: str = "", files: list = []) -> dict:
    """
    Calculate the average baselines over multiple baseline files.

    Calls calculate_baselines on each file. Afterwards, it calculates the
    average values over all files.
    """
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
    """
    Finds the maximal number of concurrent events at a time slice.
    """
    total = len(df)
    max_count = 0
    i = 1
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

def concurrency_histogram(df: pd.DataFrame, df_pred: pd.DataFrame, output:str = "", title:str = "", bin_size=1000):
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

    has_predictions = type(df_pred) == type(pd.DataFrame())
    end_time = round(df[COLUMN_END].max())

    second_bins = [-1 for i in range(0, end_time, bin_size)]
    second_bins_pred = second_bins.copy()
    seconds     = [i for i in range(0, end_time, bin_size)]

    for second in range(0, end_time, bin_size):
        bin_start = second
        bin_end = second + bin_size

        #Panda-ized approach (probably faster)
        second_bins[round(second/bin_size)] = len(df[((df[COLUMN_END] > bin_start) & (df[COLUMN_END] <= bin_end)) | ((df[COLUMN_START] >= bin_start) & (df[COLUMN_START] < bin_end)) | ((bin_start >= df[COLUMN_START]) & (bin_end <= df[COLUMN_END]))])
        if has_predictions:
            second_bins_pred[round(second/bin_size)] = len(df_pred[((df_pred[COLUMN_END] > bin_start) & (df_pred[COLUMN_END] <= bin_end)) | ((df_pred[COLUMN_START] >= bin_start) & (df_pred[COLUMN_START] < bin_end)) | ((bin_start >= df_pred[COLUMN_START]) & (bin_end <= df_pred[COLUMN_END]))])


        print("\r{}/{} seconds processed.".format(second, end_time), file=sys.stderr, end="")

    err("")
    if output:
        plt.hist(seconds, len(seconds), weights=second_bins, alpha=0.5, label="Result")
        if has_predictions:
            plt.hist(seconds, len(seconds), weights=second_bins_pred, alpha=0.5, label="Prediction")
            plt.legend(loc="upper right")
        plt.xlabel("seconds")
        plt.ylabel("# instances")
        plt.title(title)
        plt.savefig(output, dpi=1000)
        plt.clf()

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

def process_file(filename: str, baselines: dict, output=True) -> pd.DataFrame:
    """
        Processes a single file and write the results to another file.
        This file will have the systematic name "processed_{filename}"
    """
    if not path.isfile(filename):
        raise FileNotFoundError("File {} does not exist!".format(filename))

    write_to_name = "processed-{}".format(path.basename(filename))
    write_to_name = path.join(path.split(filename)[0], write_to_name)

    ### Read the CSV and perform some data transformations
    result_df = read_csv(filename)

    #Sort on starting time and subtract the initial time
    result_df.sort_values(by=COLUMN_START, inplace=True)
    start_time = result_df[COLUMN_START].min()
    result_df[COLUMN_START] = (result_df[COLUMN_START] - start_time) * 1000

    #Perform some datacleansing here
    # result_df = result_df[]

    result_df = calculate_deltas(result_df, baselines)


    ### Calculate some meta-data
    if output:
        to_write = []

        to_write.append(("Total time", result_df[COLUMN_END].max()))
        to_write.append(("Delta runtime", ))
        to_write.append(("No. instances", len(result_df)))
        to_write.append(("Max. concurrent events", max_concurrent_events(result_df)))
        to_write.append(("Sum of delta tFC", result_df[COLUMN_DELTA_FC].sum()))
        to_write.append(("Sum of delta tVM", result_df[COLUMN_DELTA_VM].sum()))
        to_write.append(("Mean of delta tFC", result_df[COLUMN_DELTA_FC].mean()))
        to_write.append(("Mean of delta tVM", result_df[COLUMN_DELTA_VM].mean()))

        with open(write_to_name, "w") as f:
            for t in to_write:
                f.write("# {}: {} \n".format(t[0], t[1]))

        #Append the processed df to the file
        result_df.to_csv(path.join(path.split(filename)[0], write_to_name), mode="a", index=False)

    return result_df

def sysmon_graphs(df: pd.DataFrame, title: str = "sysmon output", output: str = "sysmon.png", total_mem: int = -1) -> None:
    """
    Create graphs with the metrics output by the system monitor.

    For now: simple line graphs
    """
    #Process the following columns
    process_cols = ["t", "cpu_user", "cpu_system", "cpu_idle", "cpu_inter"]

    # for pcol in process_cols:
    #     if pcol not in df:
    #         continue

    #     df[pcol] = df[pcol] - df[pcol][0]

    nrows = len(df.columns) - len(process_cols) + 1
    ncols = 1
    idx = 1

    if "swap_used" in df:
        if df["swap_used"].max() == 0 and df["swap_used"].max() == df["swap_used"].min():
            df = df.drop("swap_used", axis=1)

    print(f"total_mem = {total_mem} other = {df.mem_avail[0]}")

    #Make percentages of available memory if possible
    if total_mem > 0 and "mem_avail" in df:
        df.mem_avail = (df.mem_avail / total_mem) * 100

    
    #Keep track whether we saw one of the process_plots already
    #as we're gonna plot these all in the same plot
    process_col_one = True

    #Do not need the 't' column to be in df
    x_axis = df.t
    df = df.drop(df.t.name, axis=1)
    list_ax = []
    subplot_args = {}


    for col in df.columns:
        if idx > 1:
            subplot_args["sharex"] = list_ax[0]

        if col not in process_cols or process_col_one:
            ax = plt.subplot(nrows, ncols, idx, **subplot_args)
            list_ax.append(ax)
            process_col_one = False
            idx += 1
        else:
            plt.ylabel("Percentage %")
            
        list_ax[-1].plot(x_axis, df[col], ",--", label=col)
        list_ax[-1].legend(loc="upper right")
        plt.xlabel("time (s)")

        if col == "mem_avail":
            plt.ylabel("Percentage available")


    plt.suptitle(title)
    # plt.tight_layout()
    # plt.show()
    plt.savefig(output, dpi=1000)
    plt.clf()



def process_data(directory: str) -> None:
    """
    Gather all files in a directory and its subdirectories and process these
    result files. It is advisable to call this function per directory that 
    contains data from multiple machines/experiments. For example, a directory 
    that contains all experiments for the CFS scheduler.
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
            if baseline == BASELINE_FILENAME or baseline == BASELINES_FILENAME:
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

    # err("Determining bin size by picking smallest value for primenumber baselines...")
    # bin_size = avg_baselines.get(0, {})
    # bin_size = max(bin_size.get(max(bin_size.keys()), []))
    bin_size = 20000 #20sec
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
            if workload_name.startswith(RESULTS_PREFIX):
                workload_name = workload_name[len(RESULTS_PREFIX):]


                basename = workload_name
                workload_name = path.abspath(path.join(WORKLOAD_DIR, workload_name))

                if path.isfile(workload_name):
                    err("Calculating predictions for {}".format(workload_name))
                    predictions[basename] = predict_workload_runtime(workload_name, avg_baselines, directory)

                else:
                    err("Workload file {} does not exist, where it should?".format(workload_name))
            else:
                #Unsupported file
                err(f"Skipping file {workload_name}")

    #Process all the files
    err("Starting processing of results...")
    for d, files in files_per_dir.items():
        for f in files:
            if f.endswith(RESULTS_EXT) and f.startswith(RESULTS_PREFIX):
                #Process the results and create graphs
                err("Processing {}...".format(path.join(d,f)))
                #Cut-off the prefix, as this is the key for predictions
                workload_name = f[len(RESULTS_PREFIX):]
                preds = predictions.get(workload_name, None)
                #Process the results and write them to a file + store in variable
                proc_df = process_file(path.join(d, f), baselines_per_dir[d])


                prefix_start = d.find("results")
                if prefix_start < 0:
                    prefix_start = 0
                
                #Transform path to a nice readable title
                histo_title = d[prefix_start+len("results"):].replace("/", " ") + f[len(RESULTS_PREFIX):]
                histo_name = HISTO_PREFIX + path.splitext(f)[0] + HISTO_EXT
                # Save the bins to avoid extra work in case of rerender of histo?
                _, _ = concurrency_histogram(df=proc_df, df_pred=preds, output=path.join(d, histo_name), title=histo_title, bin_size=bin_size)

            elif f.startswith(SYSMON_RESULTS_PREFIX) and f.endswith(SYSMON_EXT):
                #Create some graphs of the sysmon results and store these 
                #as a file as well
                err(f"Processing system monitor results {path.join(d,f)}")

                cpu_count = -1
                total_mem = -1

                with open(path.join(d,f), "r") as sysfile:
                    cpu_count = sysfile.readline()
                    total_mem = sysfile.readline()

                if "total_mem" in total_mem:
                    total_mem = [int(s) for s in total_mem.split() if s.isdigit()]
                    total_mem = total_mem[0]

                sysmon_df = read_csv(path.join(d, f))

                prefix_start = d.find("results")
                if prefix_start < 0:
                    prefix_start = 0

                graph_output = path.join(d, path.splitext(f)[0] + ".png")
                graph_title = d[prefix_start+len("results"):].replace("/", " ") + f[len(SYSMON_RESULTS_PREFIX):]

                sysmon_graphs(sysmon_df, title=graph_title, output=graph_output, total_mem=total_mem)





if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description=_PROGRAM_DESCRIPTION_)

    arg_parser.add_argument("directory", type=str, help="Directory containing the results per scheduler")

    if len(sys.argv) < 2:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    if args.directory:
        process_data(args.directory)