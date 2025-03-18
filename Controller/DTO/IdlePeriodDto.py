from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

@dataclass
class IdlePeriodDto:
    idlePeriodId: UUID
    machineId: UUID
    start: int
    duration: int
