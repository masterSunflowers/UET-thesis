import argparse
import os
import sys
import time

from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
from typing import List, Optional, Dict, Any

import pandas as pd
import multilspy
from multilspy.language_server import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from pydantic import BaseModel
from tree_sitter import Point

from helper import Helper
from prompt_construction import get_all_snippets, render_prompt

multilspy_logger = MultilspyLogger()
CWD = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.join(CWD, "prompt_builder.log"),
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(name=__name__)


class BuilderOutput(BaseModel):
    model_name: str
    built_prompt: Optional[str]
    snippets: Any
    prefix: Optional[str]
    suffix: Optional[str]
    completion_options: Optional[Dict[str, List[str]]]


class PromptBuilder:
    def __init__(
        self,
        input_path: str,
        repos_storage: str,
        output_path: str,
        log_path: str,
        language: str,
        model_name: str,
        log_steps: int = 1,
        debug: bool = False,
    ):
        self.df = pd.read_json(input_path, lines=True)
        if debug:
            self.df = self.df[8:9]
        self.repos_storage = repos_storage
        self.output_path = output_path
        self.log_path = log_path
        self.log_steps = log_steps
        self.language = language
        self.model_name = model_name

    def setup_test_state(self, test_case):
        root_path = os.path.join(self.repos_storage, test_case["encode"])
        file_path = os.path.join(root_path, test_case["metadata"]["file"])
        with open(file_path, "r") as f:
            orig_file_content = f.read()

        new_file_content = test_case["prompt"] + test_case["right_context"]
        with open(file_path, "w") as f:
            f.write(new_file_content)
        row = len(test_case["prompt"].splitlines()) - 1
        col = len(test_case["prompt"].splitlines()[-1])
        cursor_index = Point(row=row, column=col)

        config = MultilspyConfig.from_dict({"code_language": self.language})
        language_server = SyncLanguageServer.create(
            config, multilspy_logger, repository_root_path=root_path, 
        )
        return file_path, orig_file_content, cursor_index, language_server

    def build_prompt(self):
        outputs = []
        for idx, row in tqdm(
            self.df.iterrows(), total=len(self.df), desc="Building prompt"
        ):
            file_path, orig_file_content, cursor_index, language_server = (
                self.setup_test_state(row)
            )
            try:
                helper = Helper(
                    repo_dir=os.path.join(self.repos_storage, row["encode"]),
                    relative_path=row["metadata"]["file"],
                    cursor_index=cursor_index,
                    language_server=language_server,
                    language=self.language,
                    model_name=self.model_name,
                )
                logger.info("Helper is ready")
                logger.info(row["encode"])

                max_tries = 10
                for i in range(max_tries):
                    try:
                        with helper.language_server.start_server():
                            logger.info("Init server success!!!")
                            snippet_payload = get_all_snippets(helper)
                            logger.debug(f"Snippet payload:\n{snippet_payload}")
                            prompt, prefix, suffix, completion_options = render_prompt(
                                snippet_payload, helper
                            )
                            if prompt is None:
                                logger.warning(f"Encounter outlier at index {idx}")
                            outputs.append(
                                BuilderOutput(
                                    model_name=self.model_name,
                                    snippets=snippet_payload,
                                    built_prompt=prompt,
                                    prefix=prefix,
                                    suffix=suffix,
                                    completion_options=completion_options,
                                )
                            )
                    except multilspy.lsp_protocol_handler.server.Error:
                        time.sleep(1)
                        continue
                    except Exception as e:
                        logger.error(f"Error occurs when handling {idx}:\n{e}")
                        raise e
                    break
            except Exception as e:
                logger.error(f"Error occurs when handling {idx}:\n{e}")
                outputs.append(
                    BuilderOutput(
                        model_name=self.model_name,
                        built_prompt=None,
                        ide_snippets=None,
                        import_snippets=None,
                        root_path_context_snippets=None,
                        prefix=None,
                        suffix=None,
                        completion_options=None,
                    )
                )
            finally:
                with open(file_path, "w") as f:
                    f.write(orig_file_content)
            logger.info("="*100)
            if len(outputs) % self.log_steps == 0:
                self.store_df(outputs, self.log_path)

        self.store_df(outputs, self.output_path)

    def store_df(self, updates: List[BuilderOutput], path: str):
        df = self.df.copy()[: len(updates)]
        df.reset_index(drop=True, inplace=True)
        additional_col = pd.DataFrame(
            [item.model_dump_json() for item in updates], columns=["builder_output"]
        )
        df = pd.concat([df, additional_col], axis=1)
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        df.to_json(path, orient="records", lines=True)


def main(args):
    prompt_builder = PromptBuilder(
        input_path=args.input_path,
        repos_storage=args.repos_storage,
        output_path=args.output_path,
        log_path=args.log_path,
        language=args.language,
        model_name=args.model_name,
        log_steps=args.log_steps,
        debug=args.debug,
    )
    prompt_builder.build_prompt()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", dest="input_path")
    parser.add_argument("-r", "--repo-storage", dest="repos_storage")
    parser.add_argument("-o", "--output", dest="output_path")
    parser.add_argument("-l", "--log", dest="log_path")
    parser.add_argument("-m", "--model", dest="model_name")
    parser.add_argument("-lang", "--language", dest="language", default="java")
    parser.add_argument("-lg", "--log-steps", dest="log_steps", type=int, default=1)
    parser.add_argument("--debug", dest="debug", action="store_true", default=False)
    args = parser.parse_args()
    main(args)
