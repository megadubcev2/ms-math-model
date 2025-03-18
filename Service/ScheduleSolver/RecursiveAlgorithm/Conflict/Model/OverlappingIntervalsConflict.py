from dataclasses import dataclass

from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Interval import Interval


@dataclass(frozen=True)
class OverlappingIntervalsConflict(Conflict):
    first_interval: Interval
    second_interval: Interval