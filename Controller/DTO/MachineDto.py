from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass
class MachineDto:
    machineId: UUID
    start: int
    operationIdBeforeActive: Optional[UUID] = None
