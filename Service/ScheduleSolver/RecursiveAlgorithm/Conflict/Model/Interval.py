from dataclasses import dataclass
from uuid import UUID

from Model.IntervalType import IntervalType


@dataclass(frozen=True, order=True)
class Interval:
    id: UUID    # UUID в виде строки
    type: IntervalType  # Например, "STEP" или "IDLE_PERIOD"