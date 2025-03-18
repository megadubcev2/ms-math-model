from dataclasses import dataclass

from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict


@dataclass(frozen=True)
class ConflictWithType:
    conflict: Conflict
    type: str