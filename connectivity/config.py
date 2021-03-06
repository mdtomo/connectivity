from pathlib import Path
from enum import Enum
import os


class Mode(Enum):
    CLIENT = 1
    SERVER = 2


class Config:

    MODE = Mode.SERVER
    LOCAL_ADDR = "127.0.0.1"
    REMOTE_ADDR = "127.0.0.1"
    BEAT_SECS = 5
    INACTIVE_SECS = 10
    LOCAL_PORT = 2019
    REMOTE_PORT = 2019
    LOG_LEVEL = 10  # DEBUG
    LOG_FORMAT = "%(asctime)s: %(levelname)s: %(module)s/%(funcName)s: %(message)s"
    SAVE_LOG = True
    LOG_FILE_PATH = Path.cwd() / "logs" / "connectivity_log.log"
    SMS_NOTIFY = True
    SMS_NUMBER = os.environ.get("SMS_NUMBER") or ""
