from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class SlowPeriodDto:
    slowPeriodId: UUID
    machineId: UUID
    start: int
    end: int
    coefficient: str

