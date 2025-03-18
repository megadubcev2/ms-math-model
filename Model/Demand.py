from uuid import UUID
from dataclasses import dataclass

@dataclass
class Demand:
    demandId: UUID
    dueDate: int