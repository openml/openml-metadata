import os
import sys
import argparse

from export import generate_files

# Fetches all meta-data for a specific OpenML study
if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--study_id", required=False, help="openml study id")
    parser.add_argument("--user_id", required=False, help="openml user id")
    parser.add_argument("--eval", required=True, help="evaluation measure")
    args_ = parser.parse_args()

    generate_files(args_.eval, study_id=args_.study_id, user_id=args_.user_id)
