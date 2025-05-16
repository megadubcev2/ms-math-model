from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from Model.EntityType import EntityType


@dataclass
class ResolvedStep:
    stepId: UUID
    entityType: EntityType
    start: int
    duration: int
    setupStart: Optional[int] = None
    setupDuration: Optional[int] = None
