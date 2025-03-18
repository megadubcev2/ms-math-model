from uuid import UUID
from dataclasses import dataclass

@dataclass
class NotOverlappingStepsPairDto:
    firstStepId: UUID
    secondStepId: UUID