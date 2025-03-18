from dataclasses import dataclass
from uuid import UUID

from Model import IntervalType

# не помню зачем я это создал но пусть будет
@dataclass
class Interval:
    intervalId: UUID
    machineId: UUID
    start: int
    duration: int
    fixed: bool
    type: IntervalType
