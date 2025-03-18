from dataclasses import dataclass
from uuid import UUID

from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Interval import Interval


@dataclass(frozen=True)
class MachineIntervalConflict(Conflict):
    machine_id: UUID
    interval: Interval
