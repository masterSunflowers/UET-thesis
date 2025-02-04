# import os
# import sys
# from pprint import pprint

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# from continue_dev.helper import Helper
# from tree_sitter import Point
# from continue_dev.utils import construct_autocomplete_prompt, render_prompt

# repo_dir = "/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox"
# file_path = "/home/lvdthieu/Documents/Projects/continue/manual-testing-sandbox/thieulvd/test/Calculator.java"
# cursor_index=Point(row=21, column=28)
# helper = Helper(
#     repo_dir=repo_dir,
#     language="java",
#     file_path=file_path,
#     cursor_index=cursor_index
# )
# pprint(vars(helper))
# snippets = construct_autocomplete_prompt(helper)
# print(render_prompt(snippets, helper))

print(repr("""; Method parameters
(method_declaration
  (formal_parameters
    (formal_parameter
    	(type_identifier) @a
    )
  )
)

; Return type
(method_declaration
  (type_identifier) @b
)"""))



