import argparse
import sys
from os import path
import numpy as np

_PRDSCR_ = """Workload-generator for fc-microbenchmark

This program generates a workload-argument file that will be executed by the benchmark.

It reads from a baseline-argument textfile to determine which pairs of workloads and arguments are baselined.
From here, it will generate a text-file that contains N entries, with a specified mix.

This program does not check whether the id of the workloads (first column in the baseline-argument file) are valid.
"""

#Random number generator needed for some Numpy-functions
rng = np.random.default_rng()

def parse_mix(raw: str) -> list:
    """Parse a raw string that indicates a mix into a list. For example, 
    "3/2/1" will be converted to [0.5, 0.333, 0.166]

    """
    if type(raw) is not str:
        raise TypeError("parse_mix: argument is of invalid type, must be string")

    raw_splits = raw.split("/")

    #Get rid of non-numeric gibberish
    splits = [int(split) for split in raw_splits if split.isnumeric()]

    total = sum(splits)

    #Convert to fraction
    return [(split / total) for split in splits]

def parse_baseline_arguments(raw: list) -> dict:
    ret_dict = {}

    for line in raw:
        #Split the line into individual numeric components, get rid of spaces
        split = line.split(",")

        if len(split) != 2:
            continue
        #Convert to int's
        split = [int(s.strip()) for s in split if s.strip().isnumeric()]

        if split[0] not in ret_dict:
            ret_dict[split[0]] = []

        ret_dict[split[0]].append(split[1])

    return ret_dict


def read_file(filename: str) -> list:
    if type(filename) is not str:
        raise TypeError("read_file: argument is of invalid type, must be string")

    f = path.abspath(filename)

    if not path.exists(f) and not path.isfile(f):
        raise ValueError("read_file: given filename ({}) does not exist, or is not a file!".format(filename))

    with open(f, 'r') as file:
        return file.readlines()

    #Fall-through
    return []



def generate_workload(wid_args: dict, mix: list, n: int) -> list:
    

    if n < 1:
        raise ValueError("generate_workload: n must be larger than 1, got {}".format(n))
    #Select n numbers with the preferred mix
    ret_list = rng.choice(list(wid_args.keys()), n, p=mix).tolist()

    for k in wid_args.keys():
        n = ret_list.count(k)
        #All arguments are equally likely
        args = rng.choice(wid_args[k], n).tolist()

        for i, v in enumerate(ret_list):
            if v == k:
                ret_list[i] = str(v) + ", " + str(args.pop(0)) + "\n"

    return ret_list

def generate_poisson_workload(wid_args: dict, mix: list, n: int, t: float) -> list:
    """
        Generate a list of start times for instances
    """
    workload = generate_workload(wid_args, mix, n)

    time = t * 3600 #t is in hours
    lambda_poisson = n / time
    #Generate intervals via Poisson
    intervals = rng.exponential(1.0/lambda_poisson, len(workload))

    #Zip the strings of workload and interval
    str_cat = lambda x, y: x[:-1] + ", {:.3f} \n".format(y)
    workload = list(map(str_cat, workload, intervals))

    return workload

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description=_PRDSCR_)

    arg_parser.add_argument("baseline", type=str, help="Filename of the baseline-argument textfile", default="baseline-arguments.txt")
    arg_parser.add_argument("N", type=int, help="Number of entries in the workload-argument file.", default=5000)
    arg_parser.add_argument("mix", type=str, help="Mixture of workloads, e.g. 1/1/1", default="1/1/1")
    arg_parser.add_argument("-p", "--poisson", dest="poisson", type=float, default=False)
    arg_parser.add_argument("-o", "--output", type=str, help="If specified, write output to filename, rather than stdout.")

    if len(sys.argv) < 4:
        arg_parser.print_help()
        exit(-1)

    args = arg_parser.parse_args()

    baseline_arguments_file = read_file(args.baseline)
    n = args.N
    mix = parse_mix(args.mix)

    #Get the dictionary with workload IDs and corresponding arguments
    valid_id_arguments = parse_baseline_arguments(baseline_arguments_file)

    if len(valid_id_arguments) != len(mix):
        print("The mix contains {} values, but there are {} workload IDs!".format(len(mix), len(valid_id_arguments)))
        exit(-1)

    output = []

    if args.poisson:
        output = generate_poisson_workload(valid_id_arguments, mix, n, args.poisson)
    else:
        output = generate_workload(valid_id_arguments, mix, n)

    if args.output:
        with open(args.output, "w") as out:
            out.writelines(output)
    else:
        sys.stdout.writelines(output)
