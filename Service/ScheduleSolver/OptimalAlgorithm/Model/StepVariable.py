from dataclasses import dataclass
from uuid import UUID

from ortools.sat.python.cp_model import IntVar, IntervalVar


@dataclass
class StepVariable:
    stepId: UUID
    duration: IntVar
    start: IntVar
    end: IntVar
    interval: IntervalVar
