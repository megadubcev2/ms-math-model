from dataclasses import dataclass, field
from typing import List, Optional

from Controller.DTO.MovedStepDto import MovedStepDto
from Controller.DTO.FactoryDto import FactoryDto

@dataclass
class MovementRequestDto:
    factory: FactoryDto
    maxSearchTime: int
    movementType: Optional[str] = "SOFT"
    movedSteps: Optional[List[MovedStepDto]] = field(default_factory=list)
