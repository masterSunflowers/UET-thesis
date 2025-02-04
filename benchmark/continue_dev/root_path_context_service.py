from continue_dev.lsp_service import LSPService
from tree_sitter import Node
from continue_dev.common_funcs import get_tree_sitter_query, TYPES_TO_USE


class RootPathContextService:
    # Checked
    def __init__(self, repo_dir: str, language_server, language: str):
        self.repo_dir = repo_dir
        self.language = language
        self.lsp_service = LSPService(
            repo_dir=repo_dir, language_server=language_server, language=language
        )

    # Checked
    def get_snippet_for_node(self, relative_path: str, node: Node):
        snippets = []
        query = None
        match node.type:
            case "program":
                pass
            case "function_declaration":
                query = get_tree_sitter_query(self.language, "function_declaration")
            case "method_declaration":
                query = get_tree_sitter_query(self.language, "method_declaration")
            case "function_definition":
                query = get_tree_sitter_query(self.language, "function_definition")
            case "method_definition":
                query = get_tree_sitter_query(self.language, "method_definition")
            case _:
                pass

        if not query:
            return snippets

        results = query.captures(node)
        for var in results:
            for node in results[var]:
                type_def = self.lsp_service.execute_goto_provider(
                    relative_path, position=node.end_point
                )
                if type_def:
                    snippets.append(type_def)
        return snippets

    # Checked
    def get_snippet_by_root_path(self, relative_path, tree_path):
        snippets = []
        print("Tree Path:")
        print(tree_path)
        for ast_node in list(filter(lambda node: node.type in TYPES_TO_USE, tree_path)):
            new_snippets = self.get_snippet_for_node(relative_path, ast_node)
            snippets.extend(new_snippets)
        return snippets
