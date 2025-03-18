from uuid import UUID
from dataclasses import dataclass

@dataclass
class DemandDto:
    demandId: UUID
    dueDate: int
