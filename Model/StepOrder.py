from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from Model.StepOrderType import StepOrderType


@dataclass(frozen=True)
class StepOrder:
    previousStepId: UUID
    nextStepId: UUID
    overlapMin: int
    overlapMax: int
    stepOrderType: StepOrderType = StepOrderType.END_RUN