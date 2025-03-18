from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID
@dataclass
class ResolvedStep:
    stepId: UUID
    start: int
    duration: int
    setupStart: Optional[int] = None
    setupDuration: Optional[int] = None
