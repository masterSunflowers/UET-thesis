from typing import NamedTuple
from tree_sitter import Point
import os
from common_funcs import get_tree_path_at_cursor, get_ast, point2index
from utils import count_tokens


class Options(NamedTuple):
    prefix_percentage: float
    max_prompt_tokens: int
    max_suffix_percentage: float
    sliding_window_size: int
    sliding_window_prefix_percentage: float


class Helper:
    tree_path = None
    file_content = None
    file_lines = None
    full_prefix = None
    full_suffix = None
    pruned_prefix = None
    pruned_suffix = None

    options = Options(
        prefix_percentage=0.3,
        max_prompt_tokens=1024,
        max_suffix_percentage=0.2,
        sliding_window_size=500,
        sliding_window_prefix_percentage=0.75,
    )

    def __init__(
        self,
        repo_dir: str,
        relative_path: str,
        cursor_index: Point,
        language_server,
        language: str = "java",
        model_name: str = "codestral-latest",
        suffix: str | None = None
    ):
        self.repo_dir = repo_dir
        self.language = language
        self.relative_path = relative_path
        self.file_path = os.path.join(self.repo_dir, self.relative_path)
        self.cursor_index = cursor_index
        self.model_name = model_name
        self.language_server = language_server
        with open(self.file_path, "r") as f:
            self.file_content = f.read()

        self.file_lines = self.file_content.splitlines()
        ast = get_ast(self.file_content, self.language)
        self.tree_path = get_tree_path_at_cursor(ast, self.cursor_index)

        index = point2index(self.file_content, self.cursor_index)
        self.full_prefix = self.file_content[:index]
        self.full_suffix = suffix if suffix else self.file_content[index:]
        # print("Helper suffix")
        # print(self.full_suffix)
        self.pruned_prefix, self.pruned_suffix = self.prune_prefix_suffix()
        self.pruned_caret_window = self.pruned_prefix + self.pruned_suffix

    def prune_prefix_suffix(self):
        max_prefix_tokens = (
            self.options.max_prompt_tokens * self.options.prefix_percentage
        )
        pruned_prefix = self.prune_lines_from_top(self.full_prefix, max_prefix_tokens)
        max_suffix_tokens = min(
            self.options.max_prompt_tokens - count_tokens(pruned_prefix),
            self.options.max_suffix_percentage * self.options.max_prompt_tokens,
        )
        pruned_suffix = self.prune_lines_from_bottom(
            self.full_suffix, max_suffix_tokens
        )

        return pruned_prefix, pruned_suffix

    @staticmethod
    def prune_lines_from_top(text: str, max_tokens: int):
        total_tokens = count_tokens(text)
        lines = text.splitlines()
        while total_tokens > max_tokens and lines:
            removed_line = lines.pop(0)
            total_tokens -= count_tokens(removed_line)
        return "\n".join(lines)

    @staticmethod
    def prune_lines_from_bottom(text: str, max_tokens: int):
        total_tokens = count_tokens(text)
        lines = text.splitlines()
        while total_tokens > max_tokens and lines:
            removed_line = lines.pop()
            total_tokens -= count_tokens(removed_line)
        return "\n".join(lines)
