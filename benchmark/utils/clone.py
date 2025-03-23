#   Author: masterSunflowers
#   Github: https://github.com/masterSunflowers/masterSunflowers
#   Date:   01/11/2024
#   Desc:   This file aim to clone github repositories in CrossCodeEval benchmark for Java
import argparse
import logging
import os
import subprocess

import pandas as pd
from tqdm import tqdm

CWD = os.path.abspath(os.path.dirname(__file__))

logger = logging.Logger("clone", level=logging.INFO)
logger.addHandler(logging.FileHandler(os.path.join(CWD, "clone.log")))


def main(args):
    save_dir = os.path.join(args.data_storage)
    if os.path.exists(save_dir):
        os.system(f"rm -rf {save_dir}")
    os.makedirs(save_dir, exist_ok=True)
    df = pd.read_json(args.input, lines=True)
    df.drop_duplicates(subset=["encode"], ignore_index=True, inplace=True)
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Cloning"):
        encode = row["encode"]
        username, repo, commit = encode.split("--")
        repo_url = f"https://github.com/{username}/{repo}.git"
        cmd = f"cd {save_dir} && git clone {repo_url} && mv {repo} {encode}"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info(f"Clone {repo_url} successfully!")
        else:
            logger.error(f"Error when clone {repo_url}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", dest="input")
    parser.add_argument("-s", dest="data_storage")
    args = parser.parse_args()
    main(args)
