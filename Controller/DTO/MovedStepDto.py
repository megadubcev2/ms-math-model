from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class MovedStepDto:
    stepId: UUID
    newStart: int