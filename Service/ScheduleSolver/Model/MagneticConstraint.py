from dataclasses import dataclass
from uuid import UUID

from Service.ScheduleSolver.Model.MagneticType import MagneticType


@dataclass
class MagneticConstraint:
    stepId: UUID
    strivingPoint: int
    leftBoarder: int
    magneticType: MagneticType
    weight: int

