from dataclasses import dataclass
from uuid import UUID

from Model.StepOrder import StepOrder
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict
from Model.StepOrderType import StepOrderType
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderBoundary import StepOrderBoundary


@dataclass(frozen=True)
class StepOrderConflict(Conflict):
    previous_step_id: UUID
    next_step_id: UUID
    step_order_type: StepOrderType
    conflict_boundary: StepOrderBoundary
    step_order: StepOrder
