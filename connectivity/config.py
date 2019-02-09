from pathlib import Path
from enum import Enum


class Mode(Enum):
    CLIENT = 1
    SERVER = 2
    CLIENT_SERVER = 3


class Config:

    MODE = Mode.CLIENT
    LOCAL_ADDR = '127.0.0.1'
    TARGET_ADDR = '127.0.0.1'
    BEAT_SECS = 5
    PORT = 20019
    LOG_LEVEL = 10 # DEBUG
    LOG_FORMAT = '%(asctime)s: %(levelname)s: %(module)s/%(funcName)s: %(message)s'
    SAVE_LOG = True
    LOG_FILE_PATH = Path.cwd() / 'logs' / 'connectivity_log.log'
