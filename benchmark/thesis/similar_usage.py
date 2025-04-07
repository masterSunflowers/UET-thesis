import time

from multilspy import SyncLanguageServer
from tree_sitter import Node, Point
import logging
from common_funcs import get_ast, get_tree_path_at_cursor, lsprange2irange

logger = logging.getLogger("similar_usage")

class SimilarUsageService:
    def __init__(
        self, repo_dir: str, language_server: SyncLanguageServer, language: str = "java"
    ):
        self.repo_dir = repo_dir
        self.language_server = language_server
        self.language = language

    def execute_goto_definition(self, file_path: str, position: Point):
        start = time.time()
        logger.debug(f"Execute goto definition for {file_path} at {position} ...")
        lsf = self.language_server.request_definition(
            file_path, position.row, position.column
        )
        logger.debug(f"Definition: {lsf}")
        logger.debug(f"Language Server tooks: {time.time() - start} s")
        if not lsf:
            return None
        else:
            return {
                "file_path": lsf[0]["absolutePath"],
                "range": lsprange2irange(lsf[0]["range"]),
            }

    def execute_goto_references(self, file_path: str, position: Point):
        start = time.time()
        logger.debug(f"Execute goto references for {file_path} at {position} ...")
        lsf = self.language_server.request_references(
            file_path, position.row, position.column
        )
        logger.debug(f"Language Server tooks: {time.time() - start} s")
        if not lsf:
            return None
        else:
            references = list(
                map(
                    lambda ref: {
                        "file_path": ref["absolutePath"],
                        "range": lsprange2irange(ref["range"]),
                    },
                    lsf,
                )
            )
            return references

    def get_similar_usages_for_node(self, file_path: str, node: Node):
        match node.type:
            case (
                "call_expression"  # Typescript function invocation
                | "method_invocation"  # Java method invocation
                | "call"  # Python function invocation and new class instance
                | "new_expression"  # Typescript function invocation
                | "object_creation_expression"  # Java new class instance
            ):
                def_symbol = self.execute_goto_definition(file_path, node.start_point)
                if not def_symbol:
                    return []

                symbol_usages = self.execute_goto_references(
                    def_symbol["file_path"], def_symbol["range"].start_point
                )
                filtered_symbol_usages = list(
                    filter(
                        lambda usage: (
                            (
                                usage["file_path"]
                                != def_symbol[
                                    "file_path"
                                ]  # Remove the definition itself
                                or usage["range"].start_point
                                != def_symbol["range"].start_point
                            )
                            and (
                                usage["file_path"] != file_path
                                or usage["range"].start_point
                                != node.start_point  # Remove the current usage
                            )
                        ),
                        symbol_usages,
                    )
                )
                return filtered_symbol_usages
            case _:
                pass
        return None

    def get_similar_usages(
        self, file_path: str, prefix: str, suffix: str, cursor_index: Point
    ):
        content = (
            prefix + ")" + suffix if prefix.endswith("(") else prefix + suffix
        )  # Fix the content to be a valid syntax
        try:
            ast = get_ast(content, self.language)

            if not ast:
                return []
            tree_path = get_tree_path_at_cursor(ast, cursor_index)

            if not tree_path:
                return []
            results = []
            for node in reversed(tree_path):
                similar_usages = self.get_similar_usages_for_node(file_path, node)
                if similar_usages:
                    results.extend(similar_usages)
            return results
        except Exception as e:
            logger.error(f"Error getting definitions from LSP {e}")
            return []
