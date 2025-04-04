from multilspy import SyncLanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

logger = MultilspyLogger()

server = SyncLanguageServer.create(
    config=MultilspyConfig({"code_language": "java"}),
    
)