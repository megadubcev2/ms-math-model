from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

@dataclass
class Operation:
    operationId: UUID