from dataclasses import dataclass
from uuid import UUID

@dataclass
class IdlePeriod:
    idlePeriodId: UUID
    machineId: UUID
    start: int
    duration: int
