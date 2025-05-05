from helper import Helper
from typing import List, Tuple, TypeVar
from similar_usage import SimilarUsageService
from similar_code import SimilarCodeService
import os
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CWD)

from utils import (
    get_window_around_cursor,
    get_last_n_path_parts,
    shortest_relative_paths,
    count_tokens,
    render_string_template,
    get_stop_tokens,
    filter_snippets_already_in_caret_window,
    get_ranked_snippets,
    is_valid_snippet
)
import logging
logger = logging.getLogger("prompt_construction")
Snippet = TypeVar("Snippet")


def get_all_snippets(helper: Helper) -> Tuple[List[Snippet]]:
    # similar_usage_snippets = get_similar_usage_snippets(helper)
    similar_code_snippets = get_similar_code_snippets(helper)
    # return similar_usage_snippets, similar_code_snippets
    return [], similar_code_snippets


def get_similar_code_snippets(helper: Helper) -> List[Snippet]:
    similar_code_service = SimilarCodeService(cached_dir=os.path.join(CWD, "..", "..", "data", "chunked"))
    similar_code_snippets = similar_code_service.get_similar_code(helper)
    return similar_code_snippets


def get_similar_usage_snippets(helper: Helper) -> List[Snippet]:
    similar_usage_service = SimilarUsageService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )

    similar_usages = similar_usage_service.get_similar_usages(
        file_path=helper.file_path,
        prefix=helper.full_prefix,
        suffix=helper.full_suffix,
        cursor_index=helper.cursor_index,
    )

    similar_usage_snippets = []
    logger.debug(f"Similar usages:\n{similar_usages}")
    for usage in similar_usages:
        cursor = usage["range"].start_point
        with open(usage["file_path"], "r") as f:
            file_lines = f.readlines()
        content = get_window_around_cursor(cursor, file_lines, window_size=128)
        similar_usage_snippets.append({
            "file_path": usage["file_path"],
            "range": usage["range"],
            "content": content,
        })
    return similar_usage_snippets


def render_prompt(snippet_payload: Tuple[List[Snippet]], helper: Helper):
    snippets = get_snippets(helper, snippet_payload)
    logger.debug(f"Snippets:\n{snippets}")
    match helper.model_name:
        case "deepseek-coder":
            return deepseek_render_prompt(snippets, helper)
        case "codestral-latest":
            return codestral_render_prompt(snippets, helper)


def get_snippets(
    helper: Helper, snippet_payload: Tuple[List[Snippet]]
) -> List[Snippet]:
    similar_usage_snippets, similar_code_snippets = snippet_payload
    filtered_snippets = filter_snippets_already_in_caret_window([
        *similar_code_snippets,
        *similar_usage_snippets
    ], helper.pruned_caret_window)

    query_text = get_window_around_cursor(helper.cursor_index, helper.file_lines)
    ranked_snippets = get_ranked_snippets(
        query_text,
        filtered_snippets
    )
    final_snippets = []
    remaining_token_count = get_remaining_token_count(helper)
    while (remaining_token_count > 0 and len(ranked_snippets) > 0):
        snippet = ranked_snippets.pop(0)
        if (not snippet or not is_valid_snippet(snippet)):
            continue
        snippet_size = count_tokens(snippet["content"]) + 10
        if (remaining_token_count >= snippet_size):
            final_snippets.append(snippet)
            remaining_token_count -= snippet_size

    return final_snippets  


def get_remaining_token_count(helper: Helper) -> int:
    token_count = count_tokens(helper.pruned_caret_window)
    return helper.options.max_prompt_tokens - token_count


def deepseek_render_prompt(snippets: List[Snippet], helper: Helper):
    prefix = helper.pruned_prefix
    suffix = helper.pruned_suffix
    deepseek_fim_template = {
        "template": "<｜fim▁begin｜>{prefix}<｜fim▁hole｜>{suffix}<｜fim▁end｜>",
        "completionOptions": {
            "stop": [
                "<｜fim▁begin｜>",
                "<｜fim▁hole｜>",
                "<｜fim▁end｜>",
                "//",
                "<｜end▁of▁sentence｜>",
            ],
        },
    }
    template = deepseek_fim_template["template"]
    completion_options = deepseek_fim_template["completionOptions"]
    prompt, prefix = render_string_template(
        template, prefix, suffix, snippets, helper.language, helper.relative_path
    )

    stop_tokens = get_stop_tokens(completion_options)

    completion_options = {
        **completion_options,
        "stop": stop_tokens,
    }

    return prompt, prefix, suffix, completion_options


def codestral_render_prompt(snippets: List[Snippet], helper: Helper):
    prefix = helper.pruned_prefix
    suffix = helper.pruned_suffix

    def compile_prefix_suffix(
        prefix: str, suffix: str, filepath: str, snippets: List[Snippet]
    ):
        if len(snippets) == 0:
            if len(suffix.strip()) == 0 and len(prefix.strip()) == 0:
                return [f"+++++ {get_last_n_path_parts(filepath, 2)}\n{prefix}", suffix]
            else:
                return [prefix, suffix]
        relative_paths = shortest_relative_paths(
            [snippet["file_path"] for snippet in snippets] + [filepath]
        )
        # logger.debug(f"Relative paths: {relative_paths}")
        other_files = "\n\n".join(
            [
                f"+++++ {relative_paths[i]}\n{snippet['content']}"
                for i, snippet in enumerate(snippets)
            ]
        )
        # logger.debug(f"Other files: {other_files}")
        return [f"{other_files}\n\n+++++ {relative_paths[-1]}\n{prefix}", suffix]

    def template(prefix: str, suffix: str):
        return f"[SUFFIX]{suffix}[PREFIX]{prefix}"

    completion_options = {
        "stop": ["[PREFIX]", "[SUFFIX]", "/src/", "#- coding: utf-8", "```"],
    }
    
    prefix, suffix = compile_prefix_suffix(
        prefix, suffix, helper.relative_path, snippets
    )
    prompt = template(prefix, suffix)
    return prompt, prefix, suffix, completion_options


# khong refine
# ==========RESULT==========
# EM: 0.4414
# ES: 79.90
# ==========================

# ket hop simiar code va similar usage
# ==========RESULT==========
# EM: 0.4505
# ES: 80.29
# ==========================


# repocoder
# ==========RESULT==========
# EM: 0.4500
# ES: 76.15
# ==========================

