from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from Controller.DTO.ResolvedStepDto import ResolvedStepDto


@dataclass
class OptimizationResponseDto:
    resolvedStepsDto : [ResolvedStepDto]