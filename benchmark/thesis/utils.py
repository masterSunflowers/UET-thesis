import os
from typing import List, TypeVar
from common_funcs import (
    COMMON_STOPS,
    LANGUAGE_COMMENT_SYMBOL,
    SEP_REGEX,
    TOKENIZER,
    Point,
)
import logging

logger = logging.getLogger("utils")

Snippet = TypeVar("Snippet")


def get_window_around_cursor(
    cursor: Point,
    file_lines: List[str],
    window_size: int = 128,
    tokenizer: any = TOKENIZER,
) -> str:
    """
    Get a window of text around the cursor position that fits within the token window size.

    Args:
        cursor (Point): Current cursor position containing row information
        file_lines (List[str]): List of file lines
        tokenizer: Tokenizer instance to encode text
        window_size (int): Maximum number of tokens allowed in window

    Returns:
        str: Text window around cursor within token limit
    """
    current_row = cursor.row
    start_line = current_row
    end_line = current_row + 1
    max_line = len(file_lines)

    # Initial expansion to find boundaries
    while start_line >= 0 and end_line <= max_line:
        current_window = "\n".join(file_lines[start_line:end_line])
        if len(tokenizer(current_window)["input_ids"]) > window_size:
            break
        start_line -= 1
        end_line += 1

    # Adjust boundaries to last valid window
    start_line += 1
    end_line -= 1
    window = "\n".join(file_lines[start_line:end_line])

    # Fine-tune the window by adding lines one at a time
    def can_add_line(test_window: str) -> bool:
        return len(tokenizer(test_window)["input_ids"]) < window_size

    # Try to add lines above
    for line_no in range(start_line - 1, -1, -1):
        test_window = file_lines[line_no] + "\n" + window
        if not can_add_line(test_window):
            break
        window = test_window

    # Try to add lines below
    for line_no in range(end_line, max_line):
        test_window = window + "\n" + file_lines[line_no]
        if not can_add_line(test_window):
            break
        window = test_window

    return window


def filter_snippets_already_in_caret_window(
    snippets: List[Snippet], caret_window: str
) -> List[Snippet]:
    return list(
        filter(
            lambda s: s["content"].strip() != ""
            and s["content"].strip() not in caret_window,
            snippets,
        )
    )


def count_tokens(content: str) -> int:
    return len(TOKENIZER(content)["input_ids"])


def shortest_relative_paths(paths: List[str]) -> List[str]:
    if len(paths) == 0:
        return []
    
    short_paths = [
        os.path.join(*path.split(os.sep)[-2:]) for path in paths  # Get the last two parts of the path
    ]
    logger.debug(short_paths)
    return short_paths
    # parts_lengths = [len(path.split(SEP_REGEX)) for path in paths]
    # current_relative_paths = [os.path.basename(path) for path in paths]
    # logger.debug(f"Current relative paths: {current_relative_paths}")
    # current_num_parts = [1 for _ in paths]
    # is_duplicated = []
    # for i, x in enumerate(current_relative_paths):
    #     is_duplicated.append(
    #         len(
    #             [
    #                 (j, y)
    #                 for j, y in enumerate(current_relative_paths)
    #                 if x == y and paths[i] != paths[j]
    #             ]
    #         )
    #         > 1
    #     )
    # logger.debug(f"Is duplicated: {is_duplicated}")
    # while any(is_duplicated):
    #     for i, is_dup in enumerate(is_duplicated):
    #         if is_dup:
    #             first_duplicated_path = current_relative_paths[i]
    #             break
    #     else:
    #         break

    #     for i, x in current_relative_paths:
    #         if x == first_duplicated_path:
    #             current_num_parts[i] += 1
    #             current_relative_paths[i] = get_last_n_path_parts(
    #                 paths[i], current_num_parts[i]
    #             )

    #     for i, x in is_duplicated:
    #         if x:
    #             is_duplicated[i] = (
    #                 current_num_parts[i] < parts_lengths[i]
    #                 and len(
    #                     list(
    #                         filter(
    #                             lambda y: y == current_relative_paths[i],
    #                             current_relative_paths,
    #                         )
    #                     )
    #                 )
    #                 > 1
    #             )
    # return current_relative_paths


def render_string_template(
    template: str,
    prefix: str,
    suffix: str,
    snippets: List[Snippet],
    language: str,
    relative_path: str,
):
    # Format snippets as comments and prepend to prefix
    formatted_snippets = "\n".join(
        list(
            map(
                lambda snippet: format_external_snippet(
                    snippet["relative_path"], snippet["content"], language
                ),
                snippets,
            )
        )
    )  # Format snippets as comments and prepend to prefix and given location of the file which include snippets

    if len(formatted_snippets) > 0:
        prefix = f"{formatted_snippets}\n\n{prefix}"
    elif len(prefix.strip()) == 0 and len(suffix.strip()) == 0:
        # If it's an empty file, include the file name as a comment
        prefix = f"{LANGUAGE_COMMENT_SYMBOL[language]} {get_last_n_path_parts(relative_path, 2)}\n{prefix}"

    prompt = compile_template(prefix, suffix, template)
    return prompt, prefix


def format_external_snippet(relative_path: str, content: str, language: str) -> str:
    comment = LANGUAGE_COMMENT_SYMBOL[language]
    lines = [
        f"{comment} Path: {os.path.basename(relative_path)}",
        *map(lambda line: f"{comment} {line}", content.strip().splitlines()),
        comment,
    ]
    return "\n".join(lines)


def get_last_n_path_parts(file_path: str, n: int) -> str:
    return os.path.join(os.path.split(file_path)[-n:])


def compile_template(prefix: str, suffix: str, template: str):
    return template.format(prefix=prefix, suffix=suffix)


def get_stop_tokens(completion_options):
    stop_tokens = completion_options["stop"] if "stop" in completion_options else []
    stop_tokens += COMMON_STOPS
    return stop_tokens


def is_valid_snippet(snippet) -> bool:
    return snippet["content"].strip() != ""
