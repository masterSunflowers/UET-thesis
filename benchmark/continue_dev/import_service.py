import os
from continue_dev.lsp_service import LSPService
from continue_dev.common_funcs import (
    get_ast,
    get_tree_sitter_query,
    TOP_LEVEL_KEY_WORDS,
    get_symbols_for_snippet,
)


class ImportService:
    # Checked
    def __init__(self, repo_dir: str, language_server, language: str = "java"):
        self.repo_dir = repo_dir
        self.lsp = LSPService(
            repo_dir=self.repo_dir,
            language_server=language_server,
            language=language,
        )
        self.language = language
        self.import_query = get_tree_sitter_query(self.language, "import_query")

    # Checked
    def get_file_info(self, relative_path: str):
        try:
            absolute_path = os.path.join(self.repo_dir, relative_path)
            with open(absolute_path, "r", encoding="utf-8") as f:
                content = f.read()

            ast = get_ast(content, self.language)
            results = self.import_query.captures(ast.root_node)
            file_info = {"imports": {}}
            for var in results:
                for node in results[var]:
                    type_def = self.lsp.execute_goto_provider(
                        relative_path, node.start_point
                    )
                    if type_def:
                        file_info["imports"][node.text.decode("utf-8")] = type_def
            return file_info
        except Exception as e:
            print(e)
            return None

    # Checked
    def get_snippet_by_import(self, relative_path, full_prefix, full_suffix):
        import_snippets = []
        file_info = self.get_file_info(relative_path)
        if file_info and file_info["imports"]:
            imports = file_info["imports"]
            # Look for imports of any symbols around the current range
            text_around_cursor = "\n".join(full_prefix.splitlines()[-5:]) + "\n".join(
                full_suffix.splitlines()[:3]
            )
            symbols = list(
                filter(
                    lambda symbol: symbol not in TOP_LEVEL_KEY_WORDS[self.language],
                    get_symbols_for_snippet(text_around_cursor),
                )
            )
            for symbol in symbols:
                if symbol in imports:
                    if imports[symbol]:
                        import_snippets.append(imports[symbol])

        return import_snippets
