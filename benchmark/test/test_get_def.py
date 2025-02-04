import pandas as pd
import os
import sys
import tree_sitter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from continue_dev.lsp_service import LSPService


# df = pd.read_json("data/dataset_cleaned.jsonl", lines=True)

# sample = dict(df.loc[30])
# repos_storage = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "github_repos_tmp"))
# print(df.loc[40, "prompt"])
# for col in df.columns:
#     print(df.loc[30, col])
lsp = LSPService(repo_dir="/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox", language="java")

# cursor_row = len(sample["prompt"].splitlines()) - 1
# cursor_col = len(sample["prompt"].splitlines()[-1])

with open("/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox/thieulvd/test/Calculator.java", "r") as f:
    content = f.read()
    
print(lsp.get_definition_from_lsp(
    rev_file_path="thieulvd/test/Calculator.java",
    content=content,
    cursor_index=tree_sitter.Point(row=21, column=28)
))


