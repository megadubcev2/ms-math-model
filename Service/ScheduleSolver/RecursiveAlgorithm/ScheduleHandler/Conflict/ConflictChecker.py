import logging
from typing import Optional

from Model.Demand import Demand
from Model.Factory import Factory
from Model.IntervalType import IntervalType
from Model.StepOrderType import StepOrderType
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.MachineIntervalConflict import MachineIntervalConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import \
    OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderBoundary import StepOrderBoundary
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Conflict.ParserConflicts import ParserConflicts
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.Machine import Machine
from Model.StepOrder import StepOrder

logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])

class ConflictChecker:
    def __init__(self):
        self.parser_conflicts = ParserConflicts()




    def check_overlapping_intervals_conflict(self, firstResolvedInterval: ResolvedInterval,
                                             secondResolvedInterval: ResolvedInterval) -> Optional[OverlappingIntervalsConflict]:
        start1 = firstResolvedInterval.get_setup_start()
        end1 = firstResolvedInterval.end
        start2 = secondResolvedInterval.get_setup_start()
        end2 = secondResolvedInterval.end
        overlap = start1 < end2 and start2 < end1
        #logging.info(f"Overlap intervals between task {firstResolvedInterval.intervalId} and task {secondResolvedInterval.intervalId}: {overlap}")
        if not overlap:
            return None

        return self.parser_conflicts.parseToOverlappingIntervalsConflict(firstResolvedInterval, secondResolvedInterval)


    def check_steps_order_conflict(self, stepOrder: StepOrder, previousInterval: ResolvedInterval,
                                   nextInterval: ResolvedInterval) -> Optional[StepOrderConflict]:

        if stepOrder.stepOrderType == StepOrderType.END_RUN:
            lag = nextInterval.start - previousInterval.end

        elif stepOrder.stepOrderType == StepOrderType.RUN_RUN:
            lag = nextInterval.start - previousInterval.start


        elif stepOrder.stepOrderType == StepOrderType.END_END:
            lag = nextInterval.end - previousInterval.end

        if stepOrder.overlapMin <= lag <= stepOrder.overlapMax:
            return None
        if stepOrder.overlapMin > lag:
            conflict = self.parser_conflicts.parseToStepOrderConflict(stepOrder, StepOrderBoundary.MIN)

        else:
            conflict = self.parser_conflicts.parseToStepOrderConflict(stepOrder, StepOrderBoundary.MAX)



        return conflict


    def check_machine_and_interval_conflict(self, machine: Machine,
                                            resolvedInterval: ResolvedInterval) -> Optional[MachineIntervalConflict]:
        if resolvedInterval.type == IntervalType.IDLE_PERIOD:
            return None
        if resolvedInterval.get_setup_start() >= machine.start:
            return None
        return self.parser_conflicts.parseToMachineIntervalConflict(machine.machineId, resolvedInterval)

    def check_deadline_conflict(self, resolvedInterval: ResolvedInterval, demand: Demand):
        if resolvedInterval.type == IntervalType.IDLE_PERIOD:
            return None
        if resolvedInterval.end > demand.dueDate:
            return self.parser_conflicts.parseToDeadlineConflict(resolvedInterval, demand)
        return None


