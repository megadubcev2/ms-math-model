from dataclasses import dataclass
from uuid import UUID

from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Interval import Interval


@dataclass(frozen=True)
class DeadlineConflict(Conflict):
    interval: Interval
    dueDate: int
