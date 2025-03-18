from Model.IdlePeriod import IdlePeriod
from Model.IntervalType import IntervalType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ReslovedMachineSetup import ResolvedMachineSetup
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.Step import Step


class ParserResolvedIntervals:

    def parseFromStepToResolvedInterval(self, step: Step, isMoved: bool = False):
        resolved_interval = ResolvedInterval(step.stepId, step.machineId, step.start,
                                             step.start + step.duration, step.duration, step.fixed,
                                             IntervalType.STEP, isMoved,
                                             step.operationId)

        resolved_interval.machineSetup = ResolvedMachineSetup(resolved_interval.start, 0)

        return resolved_interval

    def parseFromIdlePeriodToResolvedInterval(self, idle_period: IdlePeriod):
        resolved_idle_period = ResolvedInterval(idle_period.idlePeriodId, idle_period.machineId, idle_period.start,
                                                idle_period.start + idle_period.duration, idle_period.duration,
                                                True,
                                                IntervalType.IDLE_PERIOD, False)

        return resolved_idle_period
