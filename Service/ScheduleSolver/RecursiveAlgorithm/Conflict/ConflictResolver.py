import logging
import random
from typing import List
from uuid import UUID

from Service.Exceptions.ConflictException import ConflictException
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.DeadlineConflict import DeadlineConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import \
    OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderBoundary import StepOrderBoundary
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict

from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.ScheduleHandler import ScheduleHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


class ConflictResolver:
    def __init__(self, schedule_handler: ScheduleHandler):
        self.schedule_handler = schedule_handler
        self.processing_count = 0

    def resolve_overlapping_intervals_conflict(self, current_interval_id: UUID,
                                               overlapping_intervals_conflict: OverlappingIntervalsConflict) -> (
    UUID, List[UUID]):
        """
        возвращает id интервала который сдвинули
        """
        if overlapping_intervals_conflict.first_interval.id == current_interval_id:
            other_interval_id = overlapping_intervals_conflict.second_interval.id
        else:
            other_interval_id = overlapping_intervals_conflict.first_interval.id

        self.schedule_handler.log_interval(current_interval_id)
        self.schedule_handler.log_interval(other_interval_id)

        # стараемся двинуть сперва другой интервал
        reference_interval_id, adjusting_interval_id = self.sort_intervals_by_importance(current_interval_id,
                                                                                         other_interval_id)
        updated_intervals_id = self.schedule_handler.move_interval_after_interval_on_same_machine(adjusting_interval_id,
                                                                                                  reference_interval_id)

        logging.info(f"Resolved overlapping intervals conflict: "
                     f"Moved interval {adjusting_interval_id} after {reference_interval_id}.")

        return adjusting_interval_id, updated_intervals_id

    def resolve_steps_order_conflict(self, current_interval_id: UUID, step_order_conflict: StepOrderConflict) -> (
    UUID, List[UUID]):
        """
            возвращает id интервала который сдвинули
        """
        step_order = step_order_conflict.step_order
        if current_interval_id == step_order_conflict.previous_step_id:
            reference_interval_id = step_order_conflict.next_step_id
        else:
            reference_interval_id = step_order_conflict.previous_step_id

        reference_interval_id, adjusting_interval_id = self.sort_intervals_by_importance_for_step_order(
            current_interval_id,
            reference_interval_id)

        if adjusting_interval_id == step_order_conflict.previous_step_id:
            if step_order_conflict.conflict_boundary == StepOrderBoundary.MIN:
                if random.randint(0, 10) == 0:
                    updated_intervals_id = self.schedule_handler.move_interval_max_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to max step order.")
                else:
                    updated_intervals_id = self.schedule_handler.move_interval_min_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to min step order.")
            else:
                if random.randint(0, 10) == 0:
                    updated_intervals_id = self.schedule_handler.move_interval_min_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to min step order.")
                else:
                    updated_intervals_id = self.schedule_handler.move_interval_max_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to max step order.")
        else:
            if step_order_conflict.conflict_boundary == StepOrderBoundary.MIN:
                updated_intervals_id = self.schedule_handler.move_interval_min_step_order(adjusting_interval_id,
                                                                                          step_order)
                logging.info(f"Step order conflict resolved: Moved interval {adjusting_interval_id} to min step order.")
            else:
                if random.randint(0, 10) == 0:
                    updated_intervals_id = self.schedule_handler.move_interval_min_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to min step order.")
                else:
                    updated_intervals_id = self.schedule_handler.move_interval_max_step_order(adjusting_interval_id,
                                                                                              step_order)
                    logging.info(
                        f"Step order conflict resolved: Moved interval {adjusting_interval_id} to max step order.")

        return adjusting_interval_id, updated_intervals_id

    def resolve_machine_and_interval_conflict(self, interval_id: UUID) -> (UUID, List[UUID]):
        """
              возвращает id интервала который сдвинули
        """
        machine_id = self.schedule_handler.factory.steps[interval_id].machineId
        machine = self.schedule_handler.factory.machines[machine_id]
        updated_intervals_id = self.schedule_handler.move_interval_setup_start(interval_id, machine.start)

        logging.info(
            f"Machine and interval conflict resolved: Moved interval {interval_id} to machine start {machine.start}.")

        return interval_id, updated_intervals_id

    def resolve_deadline_conflict(self, deadline_conflict: DeadlineConflict) -> (UUID, List[UUID]):
        """
        возвращает id интервала который сдвинули
        """

        self.processing_count += 1

        random_number = 10 + random.randint(0, 10)
        prediction = min(self.processing_count, 10)

        interval_id = deadline_conflict.interval.id
        dueDate = deadline_conflict.dueDate

        if random_number + random.randint(0, 10) == prediction:
            # редко

            machine_id = self.schedule_handler.factory.steps[interval_id].machineId
            machine = self.schedule_handler.factory.machines[machine_id]
            updated_intervals_id = self.schedule_handler.move_interval_setup_start(interval_id, machine.start)

        else:
            # часто
            updated_intervals_id = self.schedule_handler.move_interval_end(interval_id, dueDate)
        return interval_id, updated_intervals_id

    def sort_intervals_by_importance(self, first_interval_id: UUID, second_interval_id: UUID):

        self.processing_count += 1
        first_interval = self.schedule_handler.resolved_intervals[first_interval_id]
        second_interval = self.schedule_handler.resolved_intervals[second_interval_id]

        logging.info(
            f"Evaluating importance: Interval {first_interval.intervalId} fixed: {first_interval.fixed}, isMoved: {first_interval.isMoved}")
        logging.info(
            f"Evaluating importance: Interval {second_interval.intervalId} fixed: {second_interval.fixed}, isMoved: {second_interval.isMoved}")

        random_number = 10 + random.randint(0, 10)
        prediction = min(self.processing_count, 10)
        if first_interval.fixed and second_interval.fixed:
            raise ConflictException("Conflict with pinned tasks")
        if first_interval.fixed:
            return first_interval.intervalId, second_interval.intervalId

        if second_interval.fixed:
            return second_interval.intervalId, first_interval.intervalId

        if first_interval.isMoved:
            first_initial_interval_start = self.schedule_handler.factory.steps[first_interval_id].start
            second_initial_interval_start = self.schedule_handler.factory.steps[second_interval_id].start
            # если второй интервал раньше в изначальной расстановке
            if second_initial_interval_start < first_initial_interval_start:
                first_interval, second_interval = second_interval, first_interval

            if random_number + random.randint(0, 10) == prediction:
                logging.info(
                    f"Switching interval order due to original positioning: {second_interval.intervalId} first, {first_interval.intervalId} second")
                return second_interval.intervalId, first_interval.intervalId
            return first_interval.intervalId, second_interval.intervalId

        if second_interval.isMoved:
            first_initial_interval_start = self.schedule_handler.factory.steps[first_interval_id].start
            second_initial_interval_start = self.schedule_handler.factory.steps[second_interval_id].start
            # если второй интервал раньше в изначальной расстановке
            if second_initial_interval_start < first_initial_interval_start:
                first_interval, second_interval = second_interval, first_interval

            if random_number + random.randint(0, 10) == prediction:
                logging.info(
                    f"Switching interval order due to original positioning: {second_interval.intervalId} first, {first_interval.intervalId} second")
                return second_interval.intervalId, first_interval.intervalId
            return first_interval.intervalId, second_interval.intervalId

        if (self.schedule_handler.factory_info_provider.is_step_connected_with_moved_steps(first_interval.intervalId)
                or self.schedule_handler.factory_info_provider.is_step_connected_with_moved_steps(
                    second_interval.intervalId)):

            # если второй интервал раньше в данный момент, то передвигать предпочтительней второй
            if second_interval.start < first_interval.start:
                first_interval, second_interval = second_interval, first_interval

        else:
            first_initial_interval_start = self.schedule_handler.factory.steps[first_interval_id].start
            second_initial_interval_start = self.schedule_handler.factory.steps[second_interval_id].start
            # если второй интервал раньше в изначальной расстановке
            if second_initial_interval_start < first_initial_interval_start:
                first_interval, second_interval = second_interval, first_interval

        # часто
        if random_number != prediction:
            return first_interval.intervalId, second_interval.intervalId

        # редко
        return second_interval.intervalId, first_interval.intervalId

    def sort_intervals_by_importance_for_step_order(self, first_interval_id: UUID, second_interval_id: UUID):
        self.processing_count += 1
        first_interval = self.schedule_handler.resolved_intervals[first_interval_id]
        second_interval = self.schedule_handler.resolved_intervals[second_interval_id]

        logging.info(
            f"Evaluating step order importance: Interval {first_interval.intervalId} fixed: {first_interval.fixed}, isMoved: {first_interval.isMoved}")
        logging.info(
            f"Evaluating step order importance: Interval {second_interval.intervalId} fixed: {second_interval.fixed}, isMoved: {second_interval.isMoved}")

        random_number = 10 + random.randint(0, 10)
        prediction = min(self.processing_count, 10)
        if first_interval.fixed and second_interval.fixed:
            raise ConflictException("Conflict with pinned tasks")
        if first_interval.fixed:
            return first_interval.intervalId, second_interval.intervalId

        if second_interval.fixed:
            return second_interval.intervalId, first_interval.intervalId

        if first_interval.isMoved:
            if random_number != prediction:
                return first_interval.intervalId, second_interval.intervalId
            return second_interval.intervalId, first_interval.intervalId

        if second_interval.isMoved:
            if random_number != prediction:
                return second_interval.intervalId, first_interval.intervalId
            return first_interval.intervalId, second_interval.intervalId

        if random_number != prediction:
            return first_interval.intervalId, second_interval.intervalId

        return second_interval.intervalId, first_interval.intervalId
