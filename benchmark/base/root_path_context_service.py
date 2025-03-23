from lsp_service import LSPService
from tree_sitter import Node
from common_funcs import get_tree_sitter_query, TYPES_TO_USE


class RootPathContextService:
    # Checked
    def __init__(self, repo_dir: str, language_server, language: str):
        self.repo_dir = repo_dir
        self.language = language
        self.lsp_service = LSPService(
            repo_dir=repo_dir, language_server=language_server, language=language
        )

    # Checked
    def get_snippet_for_node(self, file_path: str, node: Node):
        snippets = []
        query = None
        match node.type:
            case "program":
                pass
            case _:
                query = get_tree_sitter_query("root_path_context_queries", self.language, node.type)

        if not query:
            return snippets

        results = query.captures(node)
        for var in results:
            for node in results[var]:
                type_def = self.lsp_service.execute_goto_provider(
                    file_path, position=node.end_point
                )
                if type_def:
                    snippets.append(type_def)
        return snippets

    # Checked
    def get_snippet_by_root_path(self, file_path, tree_path):
        snippets = []
        print("Tree Path:")
        print(tree_path)
        for ast_node in list(filter(lambda node: node.type in TYPES_TO_USE, tree_path)):
            new_snippets = self.get_snippet_for_node(file_path, ast_node)
            snippets.extend(new_snippets)
        return snippets
