import argparse
import os
import time
from typing import Dict, List
import json
import dotenv
import pandas as pd
import requests
from tqdm import tqdm
from pydantic import BaseModel

dotenv.load_dotenv(override=True)

HEADER = {
    "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github.v3+json",
}

class Repository(BaseModel):
    username: str
    repo: str
    __hash__ = object.__hash__

def check_candidate_exist(lst_candidate: List[Repository]) -> Dict[Repository, bool]:
    result = {}
    for i, candidate in tqdm(
        enumerate(lst_candidate), total=len(lst_candidate), desc="Querying"
    ):
        try:
            url = f"https://api.github.com/repos/{candidate.username}/{candidate.repo}"
            response = requests.get(url, headers=HEADER)
            if response.status_code == 404:
                result[lst_candidate[i]] = False
            elif response.status_code == 200:
                result[lst_candidate[i]] = True
            else:
                print(response.status_code)
                print(response.text)
        except Exception as e:
            print(candidate)
            print(e)
            print("-" * 100)
        time.sleep(0.72)
    return result


def repo_to_encode(repo: str, list_candidate_filter: List[Repository]) -> str:
    commit = repo.split("-")[-1]
    origin = "-".join(repo.split("-")[:-1])
    for candidate in list_candidate_filter:
        if origin == candidate.username + "-" + candidate.repo:
            encode = candidate.username + "--" + candidate.repo + "--" + commit
            return encode
    raise ValueError(f"There is no candidate satisfy for repo {repo}")


def main(args):
    df = pd.read_json(args.input, lines=True)
    df["repo"] = df["metadata"].apply(lambda x: x["repository"])
    df["commit"] = df["repo"].apply(lambda name: name.split("-")[-1])
    lst_candidate = []
    lst_repo = df["repo"].unique()
    for repo in lst_repo:
        lst = repo.split("-")[:-1]
        for i in range(0, len(lst) - 1):
            username = "-".join(lst[: i + 1])
            repo = "-".join(lst[i + 1 :])
            lst_candidate.append(Repository(username=username, repo=repo))
    lst_candidate = check_candidate_exist(lst_candidate)
    lst_candidate_filter = [
        candidate for candidate, exist in lst_candidate.items() if exist
    ]
    with open("log/list_repository.json", "w") as f:
        json.dump([candidate.dict() for candidate in lst_candidate_filter], f)
    df["encode"] = df["repo"].apply(lambda x: repo_to_encode(x, lst_candidate_filter))
    df.to_json(args.output, orient="records", lines=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input")
    parser.add_argument("-o", "--output", dest="output")
    args = parser.parse_args()
    main(args)