from dataclasses import dataclass
from uuid import UUID
from ortools.sat.python.cp_model import IntVar, IntervalVar


@dataclass
class SetupVariable:
    beforeStepId: UUID
    duration: int
    start: IntVar
    end: IntVar
    interval: IntervalVar
