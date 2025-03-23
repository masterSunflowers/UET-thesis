#   Author: masterSunflowers
#   Github: https://github.com/masterSunflowers/masterSunflowers
#   Date:   01/11/2024
#   Desc:   This file aim to set all repositories that have cloned to specific 
#           commit as in CrossCodeEval benchmark

import argparse
import logging
import os
import subprocess

import pandas as pd
from tqdm import tqdm

CWD = os.path.abspath(os.path.dirname(__file__))

logger = logging.Logger("setup_commit", level=logging.INFO)
logger.addHandler(
    logging.FileHandler(os.path.join(CWD, "setup_commit.log"))
)


def main(args):
    save_dir = os.path.join(args.data_storage)
    df = pd.read_json(args.input, lines=True)
    df.drop_duplicates(subset=["encode"], ignore_index=True, inplace=True)
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Setup repo state"):
        encode = row["encode"]
        _, _, commit = encode.split("--")
        cmd = (
            f"cd {os.path.join(save_dir, encode)} && git reset --hard {commit}"
        )
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info(f"Setup state for {encode} successfully!")
            logger.info(f"Output:\n{res.stdout}\n")
            logger.info("-" * 100)
        else:
            logger.error(f"Error when setup state for {encode}")
            logger.info("-" * 100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input")
    parser.add_argument("-s", "--data-storage", dest="data_storage")
    args = parser.parse_args()
    main(args)