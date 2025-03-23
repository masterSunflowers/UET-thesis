import os
from typing import List, NamedTuple, Tuple

from tree_sitter import Point

from common_funcs import (
    COMMON_STOPS,
    LANGUAGE_COMMENT_SYMBOL,
    SEP_REGEX,
    TOKENIZER,
    IRange,
    get_symbols_for_snippet,
    read_range_in_file,
)
from import_service import ImportService
from lsp_service import LSPService
from root_path_context_service import RootPathContextService
import random
random.seed(42)
Snippet = NamedTuple("Snippet")
TOKEN_BUFFER = 10

# Checked
def get_all_snippets(helper) -> Tuple[List[Snippet]]:
    ide_snippets = get_ide_snippets(helper)
    import_snippets = get_snippet_from_import_definitions(helper)
    root_path_context_snippets = get_root_path_context(helper)
    return ide_snippets, import_snippets, root_path_context_snippets


# Checked
def render_prompt(snippet_payload, helper):
    prefix = helper.pruned_prefix
    suffix = helper.pruned_suffix

    if (suffix == ""):
        suffix = "\n"

    snippets = get_snippets(helper, snippet_payload)

    print("Snippets:")
    print(snippets)
    print("=" * 100)
    print("=" * 100)

    match helper.model_name:
        case "deepseek-coder":
            return deepseek_render_prompt(snippets, helper)
        case "codestral-latest":
            return codestral_render_prompt(snippets, helper)


# Checked
def get_ide_snippets(helper):
    lsp_service = LSPService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    ide_snippets = lsp_service.get_definition_from_lsp(
        file_path=helper.file_path,
        prefix=helper.full_prefix,
        suffix=helper.full_suffix,
        cursor_index=helper.cursor_index,
    )
    return ide_snippets


# Need check
def get_snippet_from_import_definitions(helper):
    import_service = ImportService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    import_snippets = import_service.get_snippet_by_import(
        file_path=helper.file_path,
        full_prefix=helper.full_prefix,
        full_suffix=helper.full_suffix,
    )
    return import_snippets


def get_root_path_context(helper):
    root_path_context_service = RootPathContextService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    snippets = root_path_context_service.get_snippet_by_root_path(
        file_path=helper.file_path, tree_path=helper.tree_path
    )

    return snippets


# Need check
def get_snippets(helper, snippet_payload):
    ide_snippets, import_snippets, root_path_context_snippets = snippet_payload

    snippets = shuffle_array(filter_snippets_already_in_caret_window([
        *root_path_context_snippets,
        *import_snippets
    ], helper.pruned_caret_window))

    final_snippets = []

    remaining_token_count = get_remaining_token_count(helper)

    while (remaining_token_count > 0) and (len(snippets) > 0):
        snippet = snippets.pop(0)
        if (not snippet or not is_valid_snippet(snippet)):
            continue

        snippet_size = count_tokens(snippet["content"]) + TOKEN_BUFFER

        if remaining_token_count >= snippet_size:
            final_snippets.append(snippet)
            remaining_token_count -= snippet_size
    
    return final_snippets


def get_remaining_token_count(helper):
    token_count = count_tokens(helper.pruned_caret_window)
    return helper.options.max_prompt_tokens - token_count

# Checked
def filter_snippets_already_in_caret_window(snippets: List[Snippet], caret_window: str):
    return list(
        filter(
            lambda s: s["content"].strip() != ""
            and s["content"].strip() not in caret_window,
            snippets,
        )
    )


# Checked
def count_tokens(content: str) -> int:
    return len(TOKENIZER(content)["input_ids"])


def shuffle_array(items: any):
    random.shuffle(items)
    return items


def deepseek_render_prompt(snippets: List[Snippet], helper):
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


def codestral_render_prompt(snippets: List[Snippet], helper):
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
            [snippet["relative_path"] for snippet in snippets] + [filepath]
        )
        other_files = "\n\n".join(
            [
                f"+++++ {relative_paths[i]}\n{snippet['content']}"
                for i, snippet in enumerate(snippets)
            ]
        )
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


def shortest_relative_paths(paths: List[str]) -> List[str]:
    if len(paths) == 0:
        return []

    parts_lengths = [len(path.split(SEP_REGEX)) for path in paths]
    current_relative_paths = [os.path.basename(path) for path in paths]
    current_num_parts = [1 for _ in paths]
    is_duplicated = []
    for i, x in enumerate(current_relative_paths):
        is_duplicated.append(
            len(
                [
                    (j, y)
                    for j, y in enumerate(current_relative_paths)
                    if x == y and paths[i] != paths[j]
                ]
            )
            > 1
        )

    while any(is_duplicated):
        for i, is_dup in enumerate(is_duplicated):
            if is_dup:
                first_duplicated_path = current_relative_paths[i]
                break
        else:
            break

        for i, x in current_relative_paths:
            if x == first_duplicated_path:
                current_num_parts[i] += 1
                current_relative_paths[i] = get_last_n_path_parts(
                    paths[i], current_num_parts[i]
                )

        for i, x in is_duplicated:
            if x:
                is_duplicated[i] = (
                    current_num_parts[i] < parts_lengths[i]
                    and len(
                        list(
                            filter(
                                lambda y: y == current_relative_paths[i],
                                current_relative_paths,
                            )
                        )
                    )
                    > 1
                )
    return current_relative_paths


# Checked
def render_string_template(template, prefix, suffix, snippets, language, relative_path):
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
    )

    if len(formatted_snippets) > 0:
        prefix = f"{formatted_snippets}\n\n{prefix}"
    elif len(prefix.strip()) == 0 and len(suffix.strip()) == 0:
        # If it's an empty file, include the file name as a comment
        prefix = f"{LANGUAGE_COMMENT_SYMBOL[language]} {get_last_n_path_parts(relative_path, 2)}\n{prefix}"

    prompt = compile_template(prefix, suffix, template)
    return prompt, prefix


# Checked
def format_external_snippet(relative_path: str, content: str, language: str) -> str:
    comment = LANGUAGE_COMMENT_SYMBOL[language]
    lines = [
        f"{comment} Path: {os.path.basename(relative_path)}",
        *map(lambda line: f"{comment} {line}", content.strip().splitlines()),
        comment,
    ]
    return "\n".join(lines)


# Checked
def get_last_n_path_parts(file_path: str, n: int) -> str:
    return os.path.join(os.path.split(file_path)[-n:])


# Checked
def compile_template(prefix: str, suffix: str, template: str):
    return template.format(prefix=prefix, suffix=suffix)


# Checked
def get_stop_tokens(completion_options):
    stop_tokens = completion_options["stop"] if "stop" in completion_options else []
    stop_tokens += COMMON_STOPS
    return stop_tokens


def is_valid_snippet(snippet) -> bool:
    return snippet["content"].strip() != ""
