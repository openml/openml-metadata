import os
import sys
import argparse

from openmlaslib.utils.cvsconverter import generate_scenario

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--study_id", required=True, help="openml study id")
    args_ = parser.parse_args()

    generate_scenario(int(args_.study_id), "predictive_accuracy")