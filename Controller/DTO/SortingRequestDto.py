from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from Controller.DTO.FactoryDto import FactoryDto

@dataclass
class SortingRequestDto:
    factory: FactoryDto
    maxSearchTime: int
    sortedSteps: Optional[List[UUID]] = field(default_factory=list)
