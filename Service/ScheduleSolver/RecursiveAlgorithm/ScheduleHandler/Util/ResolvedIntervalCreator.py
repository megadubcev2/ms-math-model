import logging
from typing import Dict
from uuid import UUID

from Model.Factory import Factory
from Model.Step import Step
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Util.ParserResolvedIntervals import \
    ParserResolvedIntervals

logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])

class ResolvedIntervalCreator:
    def create_all_resolved_intervals(self, factory: Factory, moved_steps: Dict[UUID, Step] = None) -> (
            [ResolvedInterval], [ResolvedInterval]):

        logging.info("Starting creation of all_resolved_intervals")

        parserResolvedIntervals = ParserResolvedIntervals()
        resolved_intervals: [ResolvedInterval] = []
        moved_resolved_steps: [ResolvedInterval] = []

        for step in factory.steps.values():
            resolved_step = parserResolvedIntervals.parseFromStepToResolvedInterval(step,
                                                                                    step.stepId in moved_steps.keys())
            resolved_intervals.append(resolved_step)
            if step.stepId in moved_steps.keys():
                moved_resolved_steps.append(resolved_step)

        for idle_period in factory.idlePeriods:
            resolved_idle_period = parserResolvedIntervals.parseFromIdlePeriodToResolvedInterval(idle_period)
            resolved_intervals.append(resolved_idle_period)

        logging.info("Finished creation of all_resolved_intervals")

        return resolved_intervals, moved_resolved_steps
