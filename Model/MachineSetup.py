from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

@dataclass
class MachineSetup:
    fromOperationId: UUID
    toOperationId: UUID
    duration: int