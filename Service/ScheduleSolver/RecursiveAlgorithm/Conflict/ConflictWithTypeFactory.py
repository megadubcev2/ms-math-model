from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.ConflictWithType import ConflictWithType
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.DeadlineConflict import DeadlineConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.MachineIntervalConflict import MachineIntervalConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict





class ConflictWithTypeFactory:

    def create_machine_interval_conflict(self, conflict: MachineIntervalConflict) -> ConflictWithType:
        return ConflictWithType(conflict=conflict, type="error.MachineIntervalConflict")

    def create_overlapping_intervals_conflict(self, conflict: OverlappingIntervalsConflict) -> ConflictWithType:
        return ConflictWithType(conflict=conflict, type="error.OverlappingIntervalsConflict")

    def create_step_order_conflict(self, conflict: StepOrderConflict) -> ConflictWithType:
        return ConflictWithType(conflict=conflict, type="error.StepOrderConflict")

    def create_deadline_conflict(self, conflict: DeadlineConflict) -> ConflictWithType:
        return ConflictWithType(conflict=conflict, type="error.DeadLineConflict")
