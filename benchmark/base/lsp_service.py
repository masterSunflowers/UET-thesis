#   Author: masterSunflowers
#   Github: https://github.com/masterSunflowers/masterSunflowers
#   Date:   01/12/2024
#   Desc:   This file implements code to simulate getting context using LSP in Continue autocomplete feature.

import time

from multilspy import SyncLanguageServer
from multilspy.multilspy_logger import MultilspyLogger
from tree_sitter import Node, Point

from common_funcs import (
    FUNCTION_BLOCK_NODE_TYPES,
    FUNCTION_DECLARATION_NODE_TYPES,
    find_children,
    find_type_identifiers,
    get_ast,
    get_tree_path_at_cursor,
    intersection,
    lsprange2irange,
    point2index,
    read_range_in_file,
)

multilspy_logger = MultilspyLogger()


class LSPService:
    def __init__(
        self, repo_dir: str, language_server: SyncLanguageServer, language: str = "java"
    ):
        self.repo_dir = repo_dir
        self.language = language
        self.language_server = language_server

    # Checked
    def get_definition_from_lsp(
        self, file_path: str, prefix: str, suffix: str, cursor_index: Point
    ):
        content = prefix + ")" + suffix if prefix.endswith("(") else prefix + suffix
        try:
            ast = get_ast(content, self.language)

            if not ast:
                return []
            tree_path = get_tree_path_at_cursor(ast, cursor_index)

            if not tree_path:
                return []
            results = []
            for node in reversed(tree_path):
                definitions = self.get_definition_for_node(file_path, node)
                results.extend(definitions)
            return results
        except Exception as e:
            print("Error getting definitions from LSP: ", e)
            return []

    # Checked
    def get_definition_for_node(self, uri: str, node: Node):
        ranges = []
        try:
            match node.type:
                case "call_expression":
                    func_def = self.execute_goto_provider(uri, node.start_point)
                    if not func_def:
                        return []
                    # Don't display a function of more than 15 lines
                    # We can of course do something smarter here eventually
                    if len(func_def["content"].splitlines()) > 15:
                        truncated = False
                        func_root_ast = get_ast(func_def["content"], self.language)
                        if func_root_ast:
                            func_node = find_children(
                                func_root_ast.root_node,
                                lambda node: node.type
                                in FUNCTION_DECLARATION_NODE_TYPES,
                                1,
                            )
                            if func_node:
                                func_node = func_node[0]
                                statement_block_node = find_children(
                                    func_node,
                                    lambda node: node.type in FUNCTION_BLOCK_NODE_TYPES,
                                    1,
                                )
                                if statement_block_node:
                                    statement_block_node = statement_block_node[0]
                                    start_index = point2index(
                                        func_def["content"],
                                        statement_block_node.start_point,
                                    )
                                    func_def["content"] = (
                                        func_root_ast.root_node.text.decode("utf-8")[
                                            :start_index
                                        ].strip()
                                    )
                                    truncated = True
                        if not truncated:
                            func_def["content"] = func_def["content"].splitlines()[0]

                    ranges.append(func_def)

                    type_defs = self.crawl_types(func_def)
                    ranges.extend(type_defs)
                case "new_expression":
                    # In 'new MyClass(...)', "MyClass" is the classNameNode
                    class_name_node = None
                    for child in node.children:
                        if child.type == "identifier":
                            class_name_node = child

                    class_def = self.execute_goto_provider(
                        uri, class_name_node.start_point
                    )
                    if not class_def:
                        return []
                    ranges.append(class_def)

                    new_type_defs = self.crawl_types(class_def)
                    ranges.extend(new_type_defs)
                case _:
                    pass
        except Exception as e:
            print(e)
            return []
        return ranges

    # Checked
    def crawl_types(
        self, definition, depth: int = 1, results=None, searched_labels=None
    ):
        # Parse AST
        if searched_labels is None:
            searched_labels = set()
        if results is None:
            results = []
        ast = get_ast(definition["content"], self.language)
        if not ast:
            return results
        ast_line_count = len(ast.root_node.text.decode("utf-8").splitlines())

        # Find type identifiers
        identifier_nodes = list(
            filter(
                lambda node: node.text.decode("utf-8") not in searched_labels,
                find_type_identifiers(ast.root_node),
            )
        )

        # Don't search for the same type definition more than one
        # We duplicate below to be sure, but this save calls to the LSP
        for node in identifier_nodes:
            searched_labels.add(node.text.decode("utf-8"))

        # Use LSP to get the definitions of those types
        new_definitions = []
        for node in identifier_nodes:
            type_def = self.execute_goto_provider(
                file_path=definition["relative_path"],
                # TODO: tree-sitter is zero-indexed, but there seems to be an off-by-one
                # error at least with the .ts parser sometimes
                position=Point(
                    row=definition["range"].start_point.row
                    + min(node.start_point.row, ast_line_count - 1),
                    column=definition["range"].start_point.column
                    + node.start_point.column,
                ),
            )
            if not type_def:
                continue
            new_definitions.append(type_def)

        # TODO: Filter out if not in our code?

        # Filter out duplicates
        for new_definition in new_definitions:
            if not new_definition or any(
                [
                    result["relative_path"] == new_definition["relative_path"]
                    and intersection(result["range"], new_definition["range"])
                    for result in results
                ]
            ):
                continue

            results.append(new_definition)

        # Recurse
        if depth > 0:
            for result in results:
                self.crawl_types(result, depth - 1, results, searched_labels)

        return results

    # Checked
    def execute_goto_provider(self, file_path, position):
        start = time.time()
        print("Execute goto provider for", file_path, "at", position, "...")
        lsf = self.language_server.request_definition(
            file_path, position.row, position.column
        )
        print("Language Server tooks:", time.time() - start, "s")
        if not lsf:
            return None
        else:
            lsf = lsf[0]
        definition_name_range = lsprange2irange(lsf["range"])
        content = read_range_in_file(lsf["absolutePath"], definition_name_range)
        definition_info = {
            "relative_path": lsf["relativePath"],
            "range": definition_name_range,
            "content": content,
        }
        return definition_info
