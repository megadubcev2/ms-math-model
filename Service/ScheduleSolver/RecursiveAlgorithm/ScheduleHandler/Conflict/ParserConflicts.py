from uuid import UUID

from Model.Demand import Demand
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.DeadlineConflict import DeadlineConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Interval import Interval
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.MachineIntervalConflict import MachineIntervalConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import \
    OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.StepOrder import StepOrder


class ParserConflicts:
    def parseResolvedIntervalToInterval(self, resolvedInterval: ResolvedInterval):
        return Interval(resolvedInterval.intervalId, resolvedInterval.type)

    def parseToOverlappingIntervalsConflict(self, firstResolvedInterval: ResolvedInterval,
                                            secondResolvedInterval: ResolvedInterval):
        firstInterval = self.parseResolvedIntervalToInterval(firstResolvedInterval)
        secondInterval = self.parseResolvedIntervalToInterval(secondResolvedInterval)
        firstInterval, secondInterval = sorted([firstInterval, secondInterval])

        return OverlappingIntervalsConflict(firstInterval, secondInterval)

    def parseToMachineIntervalConflict(self, machine_id: UUID, resolvedInterval: ResolvedInterval):
        interval = self.parseResolvedIntervalToInterval(resolvedInterval)
        return MachineIntervalConflict(machine_id, interval)

    def parseToStepOrderConflict(self, step_order: StepOrder, conflict_boundary):
        return StepOrderConflict(step_order.previousStepId, step_order.nextStepId, step_order.stepOrderType,
                                 conflict_boundary, step_order)

    def parseToDeadlineConflict(self, resolvedInterval: ResolvedInterval, demand: Demand):
        interval = self.parseResolvedIntervalToInterval(resolvedInterval)
        return DeadlineConflict(interval, demand.dueDate)
