from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from Model.StepType import StepType


@dataclass
class Step:
    stepId: UUID
    machineId: UUID
    start: int
    duration: int
    initialDuration: int
    setupStart: int
    setupDuration: int
    fixed: bool
    operationId: UUID
    type: StepType
    demandId: UUID
    campaignId: Optional[UUID]

