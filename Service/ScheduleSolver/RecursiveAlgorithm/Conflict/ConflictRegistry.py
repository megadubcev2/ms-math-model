from typing import Dict
from uuid import UUID

from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictWithTypeFactory import ConflictWithTypeFactory
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.DeadlineConflict import DeadlineConflict
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Conflict.ParserConflicts import ParserConflicts
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.ConflictWithType import ConflictWithType
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.MachineIntervalConflict import MachineIntervalConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import \
    OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.StepOrder import StepOrder


class ConflictRegistry:
    def __init__(self):
        self.overlapping_intervals_conflicts: Dict[OverlappingIntervalsConflict, int] = {}
        self.steps_order_conflicts: Dict[StepOrderConflict, int] = {}
        self.machine_and_interval_conflicts: Dict[MachineIntervalConflict, int] = {}
        self.deadline_conflicts: Dict[DeadlineConflict, int] = {}

        self.all_overlapping_intervals_conflicts: Dict[OverlappingIntervalsConflict, int] = {}
        self.all_steps_order_conflicts: Dict[StepOrderConflict, int] = {}
        self.all_machine_and_interval_conflicts: Dict[MachineIntervalConflict, int] = {}
        self.all_deadline_conflicts: Dict[DeadlineConflict, int] = {}

        self.request_count = 0
        self.critical_request_count = 100
        self.parserConflicts = ParserConflicts()
        self.conflictWithTypeFactory = ConflictWithTypeFactory()
        self.last_conflict_with_type: ConflictWithType = None

    def get_overlapping_interval_conflict_count(self, overlappingIntervalsConflict: OverlappingIntervalsConflict):
        if overlappingIntervalsConflict in self.all_overlapping_intervals_conflicts:
            return self.all_overlapping_intervals_conflicts[overlappingIntervalsConflict]
        else:
            return 0

    def get_step_order_conflict_count(self, stepOrderConflict: StepOrderConflict):
        if stepOrderConflict in self.all_steps_order_conflicts:
            return self.all_steps_order_conflicts[stepOrderConflict]
        else:
            return 0



    def add_overlapping_intervals_conflict(self, overlappingIntervalsConflict: OverlappingIntervalsConflict):

        self.last_conflict_with_type = self.conflictWithTypeFactory.create_overlapping_intervals_conflict(
            overlappingIntervalsConflict)

        if overlappingIntervalsConflict in self.all_overlapping_intervals_conflicts:
            self.all_overlapping_intervals_conflicts[overlappingIntervalsConflict] += 1
        else:
            self.all_overlapping_intervals_conflicts[overlappingIntervalsConflict] = 1

        self.request_count += 1
        if self.request_count <= self.critical_request_count:
            return

        if overlappingIntervalsConflict in self.overlapping_intervals_conflicts:
            self.overlapping_intervals_conflicts[overlappingIntervalsConflict] += 1
        else:
            self.overlapping_intervals_conflicts[overlappingIntervalsConflict] = 1

    def add_steps_order_conflict(self, stepOrderConflict: StepOrderConflict):

        self.last_conflict_with_type = self.conflictWithTypeFactory.create_step_order_conflict(
            stepOrderConflict)

        if stepOrderConflict in self.all_steps_order_conflicts:
            self.all_steps_order_conflicts[stepOrderConflict] += 1
        else:
            self.all_steps_order_conflicts[stepOrderConflict] = 1

        self.request_count += 1

        if self.request_count <= self.critical_request_count:
            return

        if stepOrderConflict in self.steps_order_conflicts:
            self.steps_order_conflicts[stepOrderConflict] += 1
        else:
            self.steps_order_conflicts[stepOrderConflict] = 1

    def add_machine_and_interval_conflict(self, machineIntervalConflict: MachineIntervalConflict):

        self.last_conflict_with_type = self.conflictWithTypeFactory.create_machine_interval_conflict(
            machineIntervalConflict)

        if machineIntervalConflict in self.all_machine_and_interval_conflicts:
            self.all_machine_and_interval_conflicts[machineIntervalConflict] += 1
        else:
            self.all_machine_and_interval_conflicts[machineIntervalConflict] = 1

        self.request_count += 1

        if self.request_count <= self.critical_request_count:
            return

        if machineIntervalConflict in self.machine_and_interval_conflicts:
            self.machine_and_interval_conflicts[machineIntervalConflict] += 1
        else:
            self.machine_and_interval_conflicts[machineIntervalConflict] = 1

    def add_deadline_conflict(self, deadlineConflict: DeadlineConflict):

        if deadlineConflict in self.all_deadline_conflicts:
            self.all_deadline_conflicts[deadlineConflict] += 1
        else:
            self.all_deadline_conflicts[deadlineConflict] = 1


        self.request_count += 1
        if self.request_count <= self.critical_request_count:
            return

        if deadlineConflict in self.deadline_conflicts:
            self.deadline_conflicts[deadlineConflict] += 1
        else:
            self.deadline_conflicts[deadlineConflict] = 1

    def get_all_conflicts_with_type(self):
        conflicts_with_type = []

        # Обработка overlapping_intervals_conflicts
        for conflict, count in self.overlapping_intervals_conflicts.items():
            if count > 100:
                conflicts_with_type.append(self.conflictWithTypeFactory.create_overlapping_intervals_conflict(conflict))

        # Обработка steps_order_conflicts
        for conflict, count in self.steps_order_conflicts.items():
            if count > 100:
                conflicts_with_type.append(self.conflictWithTypeFactory.create_step_order_conflict(conflict))

        # Обработка machine_and_interval_conflicts
        for conflict, count in self.machine_and_interval_conflicts.items():
            if count > 100:
                conflicts_with_type.append(self.conflictWithTypeFactory.create_machine_interval_conflict(conflict))
        if len(conflicts_with_type) == 0:
            return [self.last_conflict_with_type]

        return conflicts_with_type
