import logging
import time

from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

# logging.basicConfig(level=logging.DEBUG)
config = MultilspyConfig.from_dict({"code_language": "java"})
logger = MultilspyLogger()
lsp = SyncLanguageServer.create(
    config,
    logger,
    "/home/lvdthieu/Documents/Projects/benchmark_continue/java_repos_tmp/1754048656--FATJS--4b1e065",
)
start = time.time()
with lsp.start_server():
    started_server_time = time.time()
    print("Time to start server", started_server_time - start, "s")
    x = lsp.request_definition(
        file_path="app/src/main/java/com/linsheng/FATJS/rpa/dingdingService/DingDingService.java",
        line=65,
        column=23,
    )
    print(x)
