from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
import time

logger = MultilspyLogger()

server = SyncLanguageServer.create(
    config=MultilspyConfig.from_dict({"code_language": "java"}),
    logger=logger,
    repository_root_path="/home/lvdthieu/Documents/Projects/UET-thesis/data/java_repos_copy/Francisco-Jean--API-BRINQUEDOMANIA--0013ce2",
)
file_path = "/home/lvdthieu/Documents/Projects/UET-thesis/data/java_repos_copy/Francisco-Jean--API-BRINQUEDOMANIA--0013ce2/src/main/java/com/brinquedomania/api/controllers/CartController.java"
row = 51
column = 52
start = time.time()
print("Execute goto provider for", file_path, "at", (row, column), "...")
with server.start_server():
    lsf = server.request_definition(file_path, row, column)
    print(lsf)
print("Time taken:", time.time() - start)
