from uuid import UUID
from dataclasses import dataclass

@dataclass
class NotOverlappingStepsPair:
    firstStepId: UUID
    secondStepId: UUID