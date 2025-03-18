from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class StepOrderDto:
    previousStepId: UUID
    nextStepId: UUID
    overlapMin: int
    overlapMax: int
    stepOrderType: Optional[str] = ""
