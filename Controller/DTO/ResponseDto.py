from dataclasses import dataclass
from typing import Optional, Any

from Controller.DTO.ResponseMetadataDto import ResponseMetadataDto


@dataclass
class ResponseDto:
    payload: Optional[Any] = None
    metadata: Optional[ResponseMetadataDto] = None
