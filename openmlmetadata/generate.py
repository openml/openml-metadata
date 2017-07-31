import os
import sys
import argparse

from export import generate_files

# Fetches all meta-data for a specific OpenML study
if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--study_id", required=True, help="openml study id")
    parser.add_argument("--eval", required=True, help="evaluation measure")
    args_ = parser.parse_args()

    generate_files(int(args_.study_id), args_.eval)
