from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from tree_sitter import Point
import sys
import os

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, ".."))
from similar_usage import SimilarUsageService

multilspy_logger = MultilspyLogger()

config = MultilspyConfig.from_dict({"code_language": "java"})
language_server = SyncLanguageServer.create(
    config,
    multilspy_logger,
    repository_root_path="/home/lvdthieu/Documents/Projects/UET-thesis/benchmark/data/java_repos_copy/burningtnt--SimpleWEBP--0bdd60c",
)

service = SimilarUsageService(
    repo_dir="/home/lvdthieu/Documents/Projects/UET-thesis/benchmark/data/java_repos_copy/burningtnt--SimpleWEBP--0bdd60c",
    language="java",
    language_server=language_server,
)
with service.language_server.start_server():
    print(
        service.execute_goto_definition(
            file_path="/home/lvdthieu/Documents/Projects/UET-thesis/benchmark/data/java_repos_copy/burningtnt--SimpleWEBP--0bdd60c/src/main/java/net/burningtnt/webp/vp8l/huffman/HuffmanTable.java",
            position=Point(row=334, column=26),
        )
    )
