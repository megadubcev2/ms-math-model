import logging

from Model.StepOrder import StepOrder
from Model.StepOrderType import StepOrderType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.FakeTimeConverter import FakeTimeConverter
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.Factory import Factory

# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


class ResolvedIntervalMover:
    def __init__(self, factory: Factory):
        logging.info("Starting initialization of ResolvedIntervalMover")

        self.factory = factory
        self.fake_time_converter = FakeTimeConverter(factory)

        logging.info("ResolvedIntervalMover initialized")

    def move_interval_start(self, interval: ResolvedInterval, new_start: int):
        '''
        передвигается старт интервала, считается что переналадка та же (порядок интервала не поменялся)
        '''
        # logging.info(
        #     f"move_interval_start {interval.intervalId} for new_start {new_start}")

        initial_setup_duration = round(self.fake_time_converter.count_fake_duration_by_start_and_end(
            interval.get_setup_start(), interval.start, interval.machineId))
        initial_interval_duration = self.factory.steps[interval.intervalId].initialDuration #self.fake_time_converter.count_fake_duration_by_start_and_end(
            #interval.start, interval.end, interval.machineId)

        new_interval_duration = round(self.fake_time_converter.count_real_duration_by_start(
            new_start, initial_interval_duration, interval.machineId))
        interval.changeDuration(new_interval_duration)
        interval.move_start(new_start)

        new_setup_end = interval.start
        new_setup_duration = round(self.fake_time_converter.count_real_duration_by_end(
            new_setup_end, initial_setup_duration, interval.machineId))
        interval.changeSetupDuration(new_setup_duration)

    def move_interval_end(self, interval: ResolvedInterval, new_end: int):
        '''
        передвигается конеу интервала, считается что переналадка та же (порядок интервала не поменялся)
        '''
        logging.info(
            f"move_interval_end {interval.intervalId} for new_end {new_end}")

        initial_setup_duration = round(self.fake_time_converter.count_fake_duration_by_start_and_end(
            interval.get_setup_start(), interval.start, interval.machineId))
        initial_interval_duration = round(self.fake_time_converter.count_fake_duration_by_start_and_end(
            interval.start, interval.end, interval.machineId))

        new_interval_duration = round(self.fake_time_converter.count_real_duration_by_end(
            new_end, initial_interval_duration, interval.machineId))
        interval.changeDuration(new_interval_duration)
        interval.move_end(new_end)

        new_setup_end = interval.start
        new_setup_duration = round(self.fake_time_converter.count_real_duration_by_end(
            new_setup_end, initial_setup_duration, interval.machineId))
        interval.changeSetupDuration(new_setup_duration)

    def move_interval_setup_start(self, interval: ResolvedInterval, new_setup_start: int):
        '''initial_setup_duration не меняется, то есть длина переналадки меняется только под влиянием slow period '''
        initial_setup_duration = round(self.fake_time_converter.count_fake_duration_by_start_and_end(
            interval.get_setup_start(), interval.start, interval.machineId))
        initial_interval_duration = round(self.factory.steps[interval.intervalId].initialDuration) # self.fake_time_converter.count_fake_duration_by_start_and_end(
            # interval.start, interval.end, interval.machineId)

        new_setup_duration = round(self.fake_time_converter.count_real_duration_by_start(
            new_setup_start, initial_setup_duration, interval.machineId))
        interval.changeSetupDuration(new_setup_duration)
        interval.move_setup_start(new_setup_start)

        new_interval_duration = round(self.fake_time_converter.count_real_duration_by_start(
            interval.start, initial_interval_duration, interval.machineId))

        interval.changeDuration(new_interval_duration)

    def change_setup_duration_fixed_setup_start(self, interval: ResolvedInterval, initialDuration: int) -> bool:
        '''фиксируется старт переналадки'''
        initial_interval_duration = round(self.factory.steps[interval.intervalId].initialDuration) # self.fake_time_converter.count_fake_duration_by_start_and_end(
           # interval.start, interval.end, interval.machineId)
        initial_setup_start = interval.get_setup_start()
        new_setup_duration = round(self.fake_time_converter.count_real_duration_by_start(
            initial_setup_start, initialDuration, interval.machineId))

        interval.changeSetupDuration(new_setup_duration)
        interval.move_setup_start(initial_setup_start)
        new_interval_duration = round(self.fake_time_converter.count_real_duration_by_start(
            interval.start, initial_interval_duration, interval.machineId))
        return interval.changeDuration(new_interval_duration)

    def change_setup_duration_fixed_setup_end(self, interval: ResolvedInterval, initialDuration: int) -> bool:
        '''фиксируется конец переналадки'''

        initial_setup_end = interval.start
        new_setup_duration = round(self.fake_time_converter.count_real_duration_by_end(
            initial_setup_end, initialDuration, interval.machineId))

        return interval.changeSetupDuration(new_setup_duration)

    def move_interval_after_interval_on_same_machine(self, currentInterval: ResolvedInterval,
                                                     relativeInterval: ResolvedInterval):
        """
        Перемещает интервал после другого интервала на той же машине.
        """
        if (relativeInterval.operationId, currentInterval.operationId) in self.factory.machinesSetup:
            new_initial_setup_duration = self.factory.machinesSetup[
                relativeInterval.operationId, currentInterval.operationId].duration
        else:
            new_initial_setup_duration = 0

        self.change_setup_duration_fixed_setup_end(currentInterval, new_initial_setup_duration)
        self.move_interval_setup_start(currentInterval, relativeInterval.end)

    def move_interval_min_step_order(self, current_interval: ResolvedInterval, reference_interval: ResolvedInterval,
                                     step_order: StepOrder):
        """
        Перемещает интервал,  чтобы в последовательности степов растояние было минимальным (overlapMin)
        """

        logging.info(
            f"Move_interval_min_step_order {current_interval.intervalId} for StepOrder {step_order}")

        if current_interval.intervalId == step_order.previousStepId:
            next_interval = reference_interval

            if step_order.stepOrderType == StepOrderType.END_RUN:
                new_end = next_interval.start - step_order.overlapMin
                self.move_interval_end(current_interval, new_end)


            elif step_order.stepOrderType == StepOrderType.RUN_RUN:
                new_start = next_interval.start - step_order.overlapMin
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.END_END:
                new_end = next_interval.end - step_order.overlapMin
                self.move_interval_end(current_interval, new_end)


        else:
            previous_interval = reference_interval

            if step_order.stepOrderType == StepOrderType.END_RUN:
                new_start = previous_interval.end + step_order.overlapMin
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.RUN_RUN:
                new_start = previous_interval.start + step_order.overlapMin
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.END_END:
                new_end = previous_interval.end + step_order.overlapMin
                self.move_interval_end(current_interval, new_end)

        logging.info(f"New start of task {current_interval.intervalId}  {current_interval.start}")

    def move_interval_max_step_order(self, current_interval: ResolvedInterval, reference_interval: ResolvedInterval,
                               step_order: StepOrder):
        """
        Перемещает интервал,  чтобы в последовательности степов растояние было максимальным (overlapMax)
        """
        logging.info(
            f"Move_interval_max_step_order {current_interval.intervalId} for StepOrder {step_order}")

        if current_interval.intervalId == step_order.previousStepId:
            next_interval = reference_interval

            if step_order.stepOrderType == StepOrderType.END_RUN:
                new_end = next_interval.start - step_order.overlapMax
                self.move_interval_end(current_interval, new_end)


            elif step_order.stepOrderType == StepOrderType.RUN_RUN:
                new_start = next_interval.start - step_order.overlapMax
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.END_END:
                new_end = next_interval.end - step_order.overlapMax
                self.move_interval_end(current_interval, new_end)


        else:
            previous_interval = reference_interval

            if step_order.stepOrderType == StepOrderType.END_RUN:
                new_start = previous_interval.end + step_order.overlapMax
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.RUN_RUN:
                new_start = previous_interval.start + step_order.overlapMax
                self.move_interval_start(current_interval, new_start)


            elif step_order.stepOrderType == StepOrderType.END_END:
                new_end = previous_interval.end + step_order.overlapMax
                self.move_interval_end(current_interval, new_end)

        logging.info(f"New start of task {current_interval.intervalId}  {current_interval.start}")

