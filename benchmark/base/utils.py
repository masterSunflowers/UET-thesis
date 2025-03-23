import os
from typing import List, NamedTuple

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

Snippet = NamedTuple("Snippet")


# Checked
def get_extra_snippets(helper):
    lsp_service = LSPService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    extra_snippets = lsp_service.get_definition_from_lsp(
        rev_file_path=helper.relative_path,
        prefix=helper.full_prefix,
        suffix=helper.full_suffix,
        cursor_index=helper.cursor_index,
    )
    return extra_snippets


# Checked
def get_snippet_from_import_definitions(helper):
    import_service = ImportService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    import_snippets = import_service.get_snippet_by_import(
        relative_path=helper.relative_path,
        full_prefix=helper.full_prefix,
        full_suffix=helper.full_suffix,
    )
    return import_snippets


# Checked
def get_context_for_path(helper):
    root_path_context_service = RootPathContextService(
        repo_dir=helper.repo_dir,
        language_server=helper.language_server,
        language=helper.language,
    )
    snippets = root_path_context_service.get_snippet_by_root_path(
        relative_path=helper.relative_path, tree_path=helper.tree_path
    )

    return snippets


# Checked
def retrieve_candidate_snippets(helper):
    lsp_snippets = get_extra_snippets(helper)
    import_snippets = get_snippet_from_import_definitions(helper)
    if helper.options.use_root_path_context:
        root_path_context_snippets = get_context_for_path(helper)
        snippets = [*lsp_snippets, *import_snippets, *root_path_context_snippets]
        return lsp_snippets, import_snippets, root_path_context_snippets, snippets
    else:
        snippets = [*lsp_snippets, *import_snippets]
        return lsp_snippets, import_snippets, [], snippets


# Checked
def construct_autocomplete_prompt(helper):
    lsp_snippets, import_snippets, root_path_context_snippets, snippets = (
        retrieve_candidate_snippets(helper)
    )
    snippets = filter_snippets_already_in_caret_window(
        snippets, helper.pruned_caret_window
    )
    scored_snippets = rank_and_order_snippets(helper, snippets)
    final_snippets = remove_range_from_snippets(
        snippets=scored_snippets,
        file_path=helper.file_path,
        relative_path=helper.relative_path,
        range=get_range_of_prefix_and_suffix_with_buffer(
            helper.pruned_prefix, helper.pruned_suffix, helper.cursor_index
        ),
    )
    final_snippets = list(
        filter(
            lambda snippet: snippet["score"]
            >= helper.options.recently_edited_similarity_threshold,
            snippets,
        )
    )
    final_snippets = fill_prompt_with_snippets(
        scored_snippets, helper.max_snippet_tokens
    )
    return lsp_snippets, import_snippets, root_path_context_snippets, final_snippets


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
def rank_and_order_snippets(helper, snippets: List[Snippet]):
    """Rank code snippets to be used in tab-autocomplete prompt.
    Returns a sorted version of the snippet array."""
    window_around_cursor = (
        helper.full_prefix[
            : int(
                -helper.options.sliding_window_size
                * helper.options.sliding_window_prefix_percentage
            )
        ]
        + helper.full_suffix[
            : int(
                helper.options.sliding_window_size
                * (1 - helper.options.sliding_window_prefix_percentage)
            )
        ]
    )
    for snippet in snippets:
        if "score" not in snippet:
            snippet["score"] = jaccard_similarity(
                snippet["content"], window_around_cursor
            )

    snippets = deduplicate_snippets(snippets)
    snippets = sorted(snippets, key=lambda s: s["score"])
    return snippets


# Checked
def remove_range_from_snippets(
    snippets: List[Snippet], file_path: str, relative_path: str, range: IRange
):
    final_snippet = []
    for snippet in snippets:
        if snippet["relative_path"] != relative_path:
            final_snippet.append(snippet)
            continue

        intersection = range_intersection_by_lines(range, snippet["range"])
        if not intersection:
            final_snippet.append(snippet)
        else:
            different_ranges = range_different_by_lines(snippet["range"], intersection)
            for diff_range in different_ranges:
                final_snippet.append(
                    {
                        **snippet,
                        "range": diff_range,
                        "content": read_range_in_file(file_path, diff_range),
                    }
                )
    return final_snippet


# Checked
def jaccard_similarity(a: str, b: str) -> float:
    a_set = get_symbols_for_snippet(a)
    b_set = get_symbols_for_snippet(b)
    union = len(a_set.union(b_set))
    if union == 0:
        return 0
    return len(a_set.intersection(b_set)) / union


# Checked
def deduplicate_snippets(snippets: List[Snippet]) -> List[Snippet]:
    """Deduplicate code snippets by merging overlapping ranges into a single range."""
    # Group snippets by file path
    file_groups = {}
    for snippet in snippets:
        file_groups[snippet["relative_path"]] = file_groups.get(
            snippet["relative_path"], []
        ) + [snippet]

    # Merge overlapping ranges
    all_ranges = []

    for file in file_groups:
        all_ranges.extend(merge_snippet_by_range(file_groups[file]))

    return all_ranges


# Checked
def merge_snippet_by_range(snippets: List[Snippet]) -> List[Snippet]:
    if len(snippets) <= 1:
        return snippets

    sorted_snippets = sorted(snippets, key=lambda x: x["range"].start_point.row)
    merged = []
    while len(sorted_snippets) > 0:
        next_snippet = sorted_snippets.pop(0)
        if (
            len(merged) > 0
            and merged[-1]["range"].end_point.row
            > next_snippet["range"].start_point.row
        ):
            last_merged = merged[-1]
            # Merge with previous snippet
            last_merged["score"] = max(last_merged["score"], next_snippet["score"])
            try:
                last_merged["range"].end_point = next_snippet["range"].end_point
            except Exception as e:
                print("Error merging ranges", e)
            last_merged["content"] = merge_overlapping_range_content(
                last_merged, next_snippet
            )
        else:
            merged.append(next_snippet)
    return merged


# Checked
def merge_overlapping_range_content(first: Snippet, second: Snippet) -> str:
    first_lines = first["content"].splitlines()
    num_overlapping = first["range"].end_point.row - second["range"].start_point.row
    return "\n".join(first_lines[:-num_overlapping] + second["content"].splitlines())


# Checked
def range_intersection_by_lines(range1: IRange, range2: IRange) -> IRange:
    start_line = max(range1.start_point.row, range2.start_point.row)
    end_line = min(range1.end_point.row, range2.end_point.row)
    if start_line >= end_line:
        return None

    return IRange(
        start_point=Point(row=start_line, column=0),
        end_point=Point(row=end_line, column=0),
    )


# Checked
def range_different_by_lines(orig: IRange, remove: IRange) -> List[IRange]:
    if (
        orig.start_point.row >= remove.start_point.row
        and orig.end_point.row <= remove.end_point.row
    ):
        return []

    if (
        orig.start_point.row <= remove.start_point.row
        and orig.end_point.row >= remove.end_point.row
    ):
        return [
            IRange(
                start_point=orig.start_point,
                end_point=remove.start_point,
            ),
            IRange(
                start_point=remove.end_point,
                end_point=orig.end_point,
            ),
        ]

    if (
        orig.start_point.row >= remove.start_point.row
        and orig.end_point.row >= remove.end_point.row
    ):
        return [
            IRange(
                start_point=remove.end_point,
                end_point=orig.end_point,
            )
        ]
    if (
        orig.start_point.row <= remove.start_point.row
        and orig.end_point.row <= remove.end_point.row
    ):
        return [
            IRange(
                start_point=orig.start_point,
                end_point=remove.start_point,
            )
        ]

    return [orig]


# Checked
def get_range_of_prefix_and_suffix_with_buffer(
    prefix: str, suffix: str, cursor_index: int
) -> IRange:
    prefix_lines = len(prefix.splitlines())
    suffix_lines = len(suffix.splitlines())

    buffer = 8
    prefix_suffix_range_with_buffer = IRange(
        start_point=Point(row=cursor_index.row - prefix_lines - buffer, column=0),
        end_point=Point(row=cursor_index.row + suffix_lines + buffer, column=0),
    )

    return prefix_suffix_range_with_buffer


# Checked
def fill_prompt_with_snippets(
    snippets: List[Snippet], max_snippet_tokens: int
) -> List[Snippet]:
    tokens_remaining = max_snippet_tokens
    kept_snippets = []
    for snippet in snippets:
        token_count = count_tokens(snippet["content"])
        if tokens_remaining - token_count >= 0:
            tokens_remaining -= token_count
            kept_snippets.append(snippet)
        else:
            continue
    return kept_snippets


# Checked
def count_tokens(content: str) -> int:
    return len(TOKENIZER(content)["input_ids"])


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
def render_prompt(snippets, helper):
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
def format_external_snippet(relative_path, content, language):
    comment = LANGUAGE_COMMENT_SYMBOL[language]
    lines = [
        f"{comment} Path: {os.path.basename(relative_path)}",
        *map(lambda line: f"{comment} {line}", content.strip().splitlines()),
        comment,
    ]
    return "\n".join(lines)


# Checked
def get_last_n_path_parts(file_path, n):
    return os.path.join(os.path.split(file_path)[-n:])


# Checked
def compile_template(prefix: str, suffix: str, template: str):
    return template.format(prefix=prefix, suffix=suffix)


# Checked
def get_stop_tokens(completion_options):
    stop_tokens = completion_options["stop"] if "stop" in completion_options else []
    stop_tokens += COMMON_STOPS
    return stop_tokens
