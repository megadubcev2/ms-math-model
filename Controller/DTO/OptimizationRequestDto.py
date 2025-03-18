from dataclasses import dataclass, field
from typing import List, Optional

from Controller.DTO.FactoryDto import FactoryDto


@dataclass
class OptimizationRequestDto:
    factory: FactoryDto
    maxSearchTime: int

