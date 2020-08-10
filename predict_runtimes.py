"""
    Firecracker Microbenchmark
    (c) Niels Boonstra, 2020
    File: predict_runtimes.py

    Predict runtimes for each benchmark workload.
    For this, only the baselines are needed, preferably as much as possible 
    (to even out small variety in machines)
"""

from os import path, listdir
import sys
import argparse
import numpy
import pandas as pd
import matplotlib.pyplot as plt

from process_results import *

COLUMN_PREDICT_END = "pred. end time"

_PROGRAM_DESCRIPTION_ = """Predict run-times of benchmark workload(s)

Given a directory containing multiple baselines, or a single baselines file, 
predict the runtime of a given workload, or multiple workloads.

If the baselines argument is a directory, all baselines in that folder, or its
subfolders will be taken into consideration, if and only if that file is named
"{baseline}"
""".format(baseline=BASELINE_FILENAME)

def predict_workload_runtime(baseline: str, workload: str) -> int:
    #Calculate the baseline(s) first
    baselines = {}
    if path.isdir(baseline):
        baselines = calculate_average_baselines(baseline)
    else:
        baselines = calculate_baselines(pd.read_csv(baseline, skipinitialspace=True))

    if path.isdir(workload):
        raise NotImplementedError("Processing a multitude of workloads at once not yet implemented!")
    else:
        workload = pd.read_csv(workload, header=None, skipinitialspace=True)

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
    err("Predicted runtime = {}".format(workload[COLUMN_PREDICT_END].max()))
    err("\t \t {}th instance determines runtime".format(workload[COLUMN_PREDICT_END].idxmax()))

    workload[COLUMN_END] = workload[COLUMN_PREDICT_END]
    max_conc_evt = concurrency_histogram(workload, 1000)
    del workload[COLUMN_END]

    err("Maximal amount of concurrent instances: {}".format(max_conc_evt))



    # #Create GANTT plot of predicted events
    # duration = workload[COLUMN_PREDICT_END] - workload[COLUMN_START]

    # fig, gnt = plt.subplots()

    # for idx, row in workload.iterrows():
    #     gnt.broken_barh([(row[COLUMN_START], duration[idx])], [idx, 1], facecolor="red")

    # plt.show()    

    return workload

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