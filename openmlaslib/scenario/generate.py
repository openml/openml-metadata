import os
import sys
import argparse

from openmlaslib.utils.cvsconverter import generate_scenario

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--runtime", required=True, help="csv file with runtimes (rows instances, cols algorithms)")
    parser.add_argument("--features", required=True, help="csv file with instance features (rows instances, cols features)")
    parser.add_argument("--cutoff", required=True, type=float, help="runtime cutoff")

    args_ = parser.parse_args()

    generate_scenario(args_.runtime, args_.features, args_.cutoff)