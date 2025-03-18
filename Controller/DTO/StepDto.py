from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class StepDto:
    stepId: UUID
    machineId: UUID
    start: int
    duration: int
    initialDuration: int
    fixed: bool
    operationId: UUID
    demandId: UUID = uuid4()
    campaignId: Optional[UUID] = None


