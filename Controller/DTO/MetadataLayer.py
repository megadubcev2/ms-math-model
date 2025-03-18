from enum import Enum

from pydantic import BaseModel


class MetadataLayer(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"