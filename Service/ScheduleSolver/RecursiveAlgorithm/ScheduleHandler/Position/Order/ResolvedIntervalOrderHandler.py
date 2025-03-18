import logging
from typing import Dict, List
from uuid import UUID

from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.Order.DequeResolvedIntervals import \
    DequeResolvedIntervals
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.Order.OrderType import OrderType


# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])

# класс в котором собраны все
class ResolvedIntervalOrderHandler:
    def __init__(self, all_resolved_intervals: List[ResolvedInterval]):
        logging.info("Starting initialization of ResolvedIntervalOrderHandle")

        self.all_resolved_intervals = all_resolved_intervals
        self.machine_to_deque_start_intervals: Dict[
            UUID, DequeResolvedIntervals] = self._create_machine_to_deque_resolved_intervals(OrderType.START)
        self.machine_to_deque_end_intervals: Dict[
            UUID, DequeResolvedIntervals] = self._create_machine_to_deque_resolved_intervals(OrderType.END)

        logging.info("ResolvedIntervalOrderHandle initialized successfully")

    def _create_machine_to_deque_resolved_intervals(self, order_type: OrderType) -> Dict[UUID, DequeResolvedIntervals]:
        machine_to_deque_intervals = {}
        for resolved_interval in self.all_resolved_intervals:
            if resolved_interval.machineId not in machine_to_deque_intervals:
                machine_to_deque_intervals[resolved_interval.machineId] = DequeResolvedIntervals([],
                                                                                                            order_type)

            machine_to_deque_intervals[resolved_interval.machineId].append_interval(resolved_interval)
        return machine_to_deque_intervals

    def update_resolved_interval_position(self, resolved_interval: ResolvedInterval):
        """Определяет, нужно ли двигать узел влево или вправо, и выполняет перемещение.
           Возвращает список  интервалов, e которых могут быть измены переналадки из-за изменения позиции.
           таких мнтервалов может быть от 1 до 3
           """
        self.machine_to_deque_end_intervals[resolved_interval.machineId].update_interval_position(
            resolved_interval.intervalId)
        intervals_with_new_setups = self.machine_to_deque_start_intervals[
            resolved_interval.machineId].update_interval_position(
            resolved_interval.intervalId)
        return intervals_with_new_setups

    def get_previous_interval(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_start_intervals[resolved_interval.machineId].get_previous_interval(
            resolved_interval.intervalId)

    def get_next_interval(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_start_intervals[resolved_interval.machineId].get_next_interval(
            resolved_interval.intervalId)

    def get_previous_step(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_start_intervals[resolved_interval.machineId].get_previous_step(
            resolved_interval.intervalId)

    def get_next_step(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_start_intervals[resolved_interval.machineId].get_next_step(
            resolved_interval.intervalId)

    def get_previous_interval_by_end(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_end_intervals[resolved_interval.machineId].get_previous_interval(
            resolved_interval.intervalId)

    def get_next_interval_by_end(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_end_intervals[resolved_interval.machineId].get_next_interval(
            resolved_interval.intervalId)

    def get_previous_step_by_end(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_end_intervals[resolved_interval.machineId].get_previous_step(
            resolved_interval.intervalId)

    def get_next_step_by_end(self, resolved_interval: ResolvedInterval):
        return self.machine_to_deque_end_intervals[resolved_interval.machineId].get_next_step(
            resolved_interval.intervalId)

    def get_sorted_machine_intervals(self, machine_id: UUID) -> List[ResolvedInterval]:
        if machine_id not in self.machine_to_deque_start_intervals:
            return []
        return self.machine_to_deque_start_intervals[machine_id].get_sorted_intervals()

    def get_sorted_machine_steps(self, machine_id: UUID) -> List[ResolvedInterval]:
        if machine_id not in self.machine_to_deque_start_intervals:
            return []
        return self.machine_to_deque_start_intervals[machine_id].get_sorted_steps()
