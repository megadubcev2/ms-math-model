from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
@dataclass
class ResolvedStepDto:
    stepId: UUID
    start: int
    setupStart: int
    setupStart: Optional[int]
    setupDuration: Optional[int]