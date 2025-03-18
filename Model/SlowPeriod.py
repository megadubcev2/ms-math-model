from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class SlowPeriod:
    slowPeriodId: UUID
    machineId: UUID
    start: float
    duration: float
    coefficient: float


