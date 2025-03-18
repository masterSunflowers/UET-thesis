# import json
# import os
# import socket
# import subprocess
# from subprocess import PIPE
#
#
# class LanguageServer:
#     def __init__(self, repository_root_path: str, port: int = 9211):
#         self.repository_root_path = repository_root_path
#         self.port = port
#         self.id = -1
#         self.data = "/home/lvdthieu/Documents/Projects/benchmark_continue/jdt-ls/data"
#         self.config = (
#             "/home/lvdthieu/Documents/Projects/benchmark_continue/jdt-ls/config_linux"
#         )
#         self.jar = "/home/lvdthieu/Documents/Projects/benchmark_continue/jdt-ls/plugins/org.eclipse.equinox.launcher_1.6.900.v20240613-2009.jar"
#         self.open_file_cache = set()
#
#     def start_server(self):
#         env = os.environ.copy()
#         env["CLIENT_PORT"] = f"{self.port}"
#         cmd = [
#             "java",
#             "--add-modules=ALL-SYSTEM",
#             "--add-opens",
#             "java.base/java.util=ALL-UNNAMED",
#             "--add-opens",
#             "java.base/java.lang=ALL-UNNAMED",
#             "--add-opens",
#             "java.base/sun.nio.fs=ALL-UNNAMED",
#             "-Declipse.application=org.eclipse.jdt.ls.core.id1",
#             "-Dosgi.bundles.defaultStartLevel=4",
#             "-Declipse.product=org.eclipse.jdt.ls.core.product",
#             "-Djava.import.generatesMetadataFilesAtProjectRoot=false",
#             "-Dfile.encoding=utf8",
#             "-noverify",
#             "-XX:+UseParallelGC",
#             "-XX:GCTimeRatio=4",
#             "-XX:AdaptiveSizePolicyWeight=90",
#             "-Dsun.zip.disableMemoryMapping=true",
#             "-Djava.lsp.joinOnCompletion=true",
#             "-Xmx3G",
#             "-Xms100m",
#             "-Xlog:disable",
#             "-Dlog.level=ALL",
#             "-jar",
#             f"{self.jar}",
#             "-configuration",
#             f"{self.config}",
#             "-data",
#             f"{self.data}",
#         ]
#         proc = subprocess.Popen(cmd, env=env, stdin=PIPE, stdout=PIPE, stderr=PIPE)
#         return proc
#
#     def create_connection(self):
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.sock.bind(("localhost", self.port))
#         print(f"Listening on port {self.port}")
#         self.sock.listen(1)
#         print("Waiting for connection...")
#         self.proc = self.start_server()
#         while True:
#             self.conn, addr = self.sock.accept()
#             if self.conn:
#                 break
#         print(f"Connection from {addr}")
#
#     def close_connection(self):
#         subprocess.Popen.kill(self.proc)
#         self.conn.close()
#         self.sock.close()
#
#     def get_id(self):
#         self.id += 1
#         return self.id
#
#     def read_lsp_message(self):
#         header = b""
#         while True:
#             try:
#                 data = self.conn.recv(1)
#             except Exception as e:
#                 raise e
#             header += data
#             if header.endswith(b"\r\n\r\n"):
#                 break
#
#         content_length = int(header.split(b"Content-Length: ")[1].split(b"\r\n")[0])
#         payload = self.conn.recv(content_length)
#         message = json.loads(payload.decode("utf-8"))
#         return message
#
#     def send_lsp_message(self, message):
#         payload = json.dumps(message).encode("utf-8")
#         header = f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8")
#         self.conn.sendall(header + payload)
#
#     def init(self):
#         self.start_server()
#         self.create_connection()
#         self.initialize()
#
#     def initialize(self):
#         request = {
#             "jsonrpc": "2.0",
#             "id": self.get_id(),
#             "method": "initialize",
#             "params": {
#                 "processId": None,
#                 "rootPath": self.repository_root_path,
#                 "rootUri": f"file://{self.repository_root_path}",
#             },
#         }
#         self.send_lsp_message(request)
#         response = self.get_lsp_response(request)
#         if response.get("error"):
#             raise Exception(f"Error initializing LSP server: {response['error']}")
#
#     def get_lsp_response(self, request):
#         while True:
#             response = self.read_lsp_message()
#             if response.get("id", -1) == request["id"]:
#                 return response
#             else:
#                 print(response)
#                 print(request["id"])
#                 print("=" * 100)
#                 continue
#
#     def request_definition(self, file_path, position):
#         if file_path not in self.open_file_cache:
#             notify = {
#                 "jsonrpc": "2.0",
#                 "method": "textDocument/didOpen",
#                 "params": {
#                     "textDocument": {
#                         "uri": f"file://{file_path}",
#                         "languageId": "java",
#                         "version": 1,
#                         "text": self.get_file_content(file_path),
#                     }
#                 },
#             }
#             self.send_lsp_message(notify)
#             self.open_file_cache.add(file_path)
#
#         while True:
#             message = self.read_lsp_message()
#             if message.get("method") == "textDocument/publishDiagnostics":
#                 break
#
#         request = {
#             "jsonrpc": 2.0,
#             "id": self.get_id(),
#             "method": "textDocument/definition",
#             "params": {
#                 "textDocument": {
#                     "uri": f"file://{file_path}",
#                 },
#                 "position": position,
#             },
#         }
#         self.send_lsp_message(request)
#         response = self.get_lsp_response(request)
#         return response
#
#     def get_file_content(self, file_path):
#         with open(file_path, "r") as file:
#             return file.read()
#
#     def destroy(self):
#         self.close_connection()
