import logging
from typing import Dict, Optional, List
from uuid import UUID

from Model.IntervalType import IntervalType
from Model.Step import Step
from Model.StepOrder import StepOrder
from Service.Factory.FactoryInfoProvider import FactoryInfoProvider
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.Conflict import Conflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.DeadlineConflict import DeadlineConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.MachineIntervalConflict import MachineIntervalConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.OverlappingIntervalsConflict import \
    OverlappingIntervalsConflict
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.StepOrderConflict import StepOrderConflict
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Conflict.ConflictChecker import ConflictChecker
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.Order.ResolvedIntervalOrderHandler import \
    ResolvedIntervalOrderHandler
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Util.ParserResolvedStep import ParserResolvedStep
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Util.ResolvedIntervalCreator import \
    ResolvedIntervalCreator
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.ResolvedIntervalMover import \
    ResolvedIntervalMover

# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


class ScheduleHandler:
    def __init__(self, factory_info_provider: FactoryInfoProvider):
        self.factory_info_provider = factory_info_provider
        self.factory = self.factory_info_provider.factory

        self.resolved_interval_mover = ResolvedIntervalMover(self.factory_info_provider.factory)


        self.resolved_intervals, _ = ResolvedIntervalCreator().create_all_resolved_intervals(
            self.factory, factory_info_provider.moved_steps)
        self.resolved_intervals = {interval.intervalId: interval for interval in self.resolved_intervals}

        self.interval_order_handler = ResolvedIntervalOrderHandler(list(self.resolved_intervals.values()))

        self.update_all_setups()
        self._update_all_durations()
        self.conflict_checker = ConflictChecker()
        self.parser_resolved_step = ParserResolvedStep()

    def move_interval_start(self, resolved_interval_id: UUID, new_start):
        resolved_interval = self.resolved_intervals[resolved_interval_id]
        self.resolved_interval_mover.move_interval_start(resolved_interval, new_start)
        return self._handle_after_movement(resolved_interval_id)

    def move_interval_setup_start(self, resolved_interval_id: UUID, new_start):
        resolved_interval = self.resolved_intervals[resolved_interval_id]
        self.resolved_interval_mover.move_interval_setup_start(resolved_interval, new_start)
        return self._handle_after_movement(resolved_interval_id)

    def move_interval_end(self, resolved_interval_id: UUID, new_end):
        resolved_interval = self.resolved_intervals[resolved_interval_id]
        self.resolved_interval_mover.move_interval_end(resolved_interval, new_end)
        return self._handle_after_movement(resolved_interval_id)

    def _handle_after_movement(self, moved_interval_id: UUID) -> List[UUID]:
        moved_interval = self.resolved_intervals[moved_interval_id]
        intervals_with_new_setups = self.interval_order_handler.update_resolved_interval_position(
            moved_interval)
        updated_intervals_id = []
        for interval in intervals_with_new_setups:
            is_updated = self.update_setup(interval.intervalId)
            if is_updated and interval.intervalId != moved_interval_id:
                updated_intervals_id.append(interval.intervalId)
        return updated_intervals_id

    def update_setup(self, resolved_interval_id) -> bool:
        current_interval = self.resolved_intervals[resolved_interval_id]
        if current_interval.type == IntervalType.IDLE_PERIOD:
            return False
        previous_step = self.interval_order_handler.get_previous_step(current_interval)
        if not previous_step is None:
            return self.update_setup_for_sequential_steps(previous_step.intervalId, current_interval.intervalId)
        else:
            return self.update_setup_for_first_step(current_interval.intervalId)

    def update_setup_for_sequential_steps(self, previous_step_id, next_step_id) -> bool:
        previous_interval = self.resolved_intervals[previous_step_id]
        next_interval = self.resolved_intervals[next_step_id]
        if previous_interval.type == IntervalType.IDLE_PERIOD or next_interval.type == IntervalType.IDLE_PERIOD:
            return False
        if (previous_interval.operationId, next_interval.operationId) in self.factory.machinesSetup:
            initial_setup_duration = self.factory.machinesSetup[
                (previous_interval.operationId, next_interval.operationId)].duration
        else:
            initial_setup_duration = 0

        return self.resolved_interval_mover.change_setup_duration_fixed_setup_end(next_interval, initial_setup_duration)

    def update_setup_for_first_step(self, resolved_interval_id) -> bool:
        current_interval = self.resolved_intervals[resolved_interval_id]
        if current_interval.type == IntervalType.IDLE_PERIOD:
            return False
        machine = self.factory.machines[current_interval.machineId]

        previous_step_operation_id = machine.operationIdBeforeActive
        next_step_operation_id = self.factory.steps[current_interval.intervalId].operationId

        if (previous_step_operation_id, next_step_operation_id) in self.factory.machinesSetup:
            initial_setup_duration = self.factory.machinesSetup[
                (previous_step_operation_id, next_step_operation_id)].duration
        else:
            initial_setup_duration = 0

        return self.resolved_interval_mover.change_setup_duration_fixed_setup_end(current_interval,
                                                                                  initial_setup_duration)

    def update_all_setups(self):
        for machine_id in self.factory.machines.keys():
            sorted_resolved_steps_in_machine = self.interval_order_handler.get_sorted_machine_steps(machine_id)

            if len(sorted_resolved_steps_in_machine) >= 1:
                next_step = sorted_resolved_steps_in_machine[0]
                self.update_setup_for_first_step(next_step.intervalId)

            for i in range(len(sorted_resolved_steps_in_machine) - 1):
                previous_step = sorted_resolved_steps_in_machine[i]
                next_step = sorted_resolved_steps_in_machine[i + 1]
                self.update_setup_for_sequential_steps(previous_step.intervalId, next_step.intervalId)
                # проверка на пересечение с новыми переналадками

    def _update_duration(self, current_interval_id: UUID):
        '''
        обновляет длительность интервала из-за периодов замедления
        используется только при инициализации
          '''
        current_interval = self.resolved_intervals[current_interval_id]
        if current_interval.type == IntervalType.IDLE_PERIOD:
            return
        self.move_interval_start(current_interval_id, current_interval.start)

    def _update_all_durations(self, ):
        '''
        обновляет длительность ысех интервалов из-за периодов замедления
        используется только при инициализации
        '''
        for current_interval_id in self.resolved_intervals.keys():
            self._update_duration(current_interval_id)

    def move_interval_after_interval_on_same_machine(self, current_interval_id: UUID,
                                                     relative_interval_id: UUID) -> List[UUID]:
        """
        Перемещает интервал после другого интервала на той же машине.
        """
        current_interval = self.resolved_intervals[current_interval_id]
        relative_interval = self.resolved_intervals[relative_interval_id]
        self.resolved_interval_mover.move_interval_after_interval_on_same_machine(current_interval, relative_interval)
        return self._handle_after_movement(current_interval_id)

    def move_interval_min_step_order(self, current_interval_id: UUID,
                                     step_order: StepOrder) -> List[UUID]:
        """
        Перемещает интервал,  чтобы в последовательности степов растояние было минимальным (overlapMin)
        """
        if current_interval_id == step_order.previousStepId:
            reference_interval_id = step_order.nextStepId
        else:
            reference_interval_id = step_order.previousStepId
        reference_interval = self.resolved_intervals[reference_interval_id]
        current_interval = self.resolved_intervals[current_interval_id]
        self.resolved_interval_mover.move_interval_min_step_order(current_interval, reference_interval, step_order)
        return self._handle_after_movement(current_interval_id)

    def move_interval_max_step_order(self, current_interval_id: UUID, step_order: StepOrder) -> List[UUID]:
        """
        Перемещает интервал,  чтобы в последовательности степов растояние было максимальным (overlapMax)
        """
        if current_interval_id == step_order.previousStepId:
            reference_interval_id = step_order.nextStepId
        else:
            reference_interval_id = step_order.previousStepId
        reference_interval = self.resolved_intervals[reference_interval_id]
        current_interval = self.resolved_intervals[current_interval_id]
        self.resolved_interval_mover.move_interval_max_step_order(current_interval, reference_interval, step_order)
        return self._handle_after_movement(current_interval_id)

    def get_previous_interval_id_by_start(self, current_interval_id: UUID) -> Optional[UUID]:
        current_interval = self.resolved_intervals[current_interval_id]
        previous_interval = self.interval_order_handler.get_previous_interval(current_interval)
        if previous_interval is None:
            return None
        else:
            return previous_interval.intervalId

    def check_overlapping_intervals_conflict(self, first_interval_id: UUID, second_interval_id: UUID) \
            -> Optional[OverlappingIntervalsConflict]:
        firstResolvedInterval = self.resolved_intervals[first_interval_id]
        secondResolvedInterval = self.resolved_intervals[second_interval_id]

        return self.conflict_checker.check_overlapping_intervals_conflict(firstResolvedInterval, secondResolvedInterval)

    def check_steps_order_conflict(self, stepOrder: StepOrder) -> Optional[StepOrderConflict]:
        previous_interval = self.resolved_intervals[stepOrder.previousStepId]
        next_interval = self.resolved_intervals[stepOrder.nextStepId]
        conflict = self.conflict_checker.check_steps_order_conflict(stepOrder, previous_interval, next_interval)

        return conflict

    def check_machine_and_interval_conflict(self, resolved_interval_id: UUID) -> Optional[MachineIntervalConflict]:
        resolved_interval = self.resolved_intervals[resolved_interval_id]
        machine = self.factory.machines[resolved_interval.machineId]
        return self.conflict_checker.check_machine_and_interval_conflict(machine, resolved_interval)

    def check_deadline_conflict(self, resolved_interval_id: UUID) -> Optional[DeadlineConflict]:
        resolved_interval = self.resolved_intervals[resolved_interval_id]
        if resolved_interval.type == IntervalType.IDLE_PERIOD:
            return None

        demand_id = self.factory.steps[resolved_interval.intervalId].demandId
        demand = self.factory.demands[demand_id]

        return self.conflict_checker.check_deadline_conflict(resolved_interval, demand)

    def find_intervals_overlapping_with_current(self, current_interval_id: UUID) -> List[UUID]:
        current_interval = self.resolved_intervals[current_interval_id]
        overlapping_intervals = set()
        checking_interval = self.interval_order_handler.get_next_interval(current_interval)
        while checking_interval is not None:
            if self.check_overlapping_intervals_conflict(current_interval_id, checking_interval.intervalId) is not None:
                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_next_interval(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_previous_interval_by_end(current_interval)
        while checking_interval is not None:
            if self.check_overlapping_intervals_conflict(current_interval_id, checking_interval.intervalId) is not None:
                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_previous_interval_by_end(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_previous_interval(current_interval)
        while checking_interval is not None:
            if self.check_overlapping_intervals_conflict(current_interval_id, checking_interval.intervalId) is not None:
                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_previous_interval(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_next_interval_by_end(current_interval)
        while checking_interval is not None:
            if self.check_overlapping_intervals_conflict(current_interval_id, checking_interval.intervalId) is not None:
                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_next_interval_by_end(checking_interval)
            else:
                break



        return list(overlapping_intervals)

    def find_overlapping_intervals_conflict_with_current(self, current_interval_id: UUID) -> List[
        OverlappingIntervalsConflict]:
        current_interval = self.resolved_intervals[current_interval_id]
        overlapping_intervals = set()
        overlapping_conflicts = []

        checking_interval = self.interval_order_handler.get_next_interval(current_interval)
        while checking_interval is not None:
            overlapping_conflict = self.check_overlapping_intervals_conflict(current_interval_id,
                                                                             checking_interval.intervalId)
            if overlapping_conflict is not None:
                overlapping_conflicts.append(overlapping_conflict)
                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_next_interval(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_previous_interval_by_end(current_interval)
        while checking_interval is not None:
            overlapping_conflict = self.check_overlapping_intervals_conflict(current_interval_id,
                                                                             checking_interval.intervalId)
            if overlapping_conflict is not None:
                if checking_interval.intervalId not in overlapping_intervals:
                    overlapping_conflicts.append(overlapping_conflict)

                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_previous_interval_by_end(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_previous_interval(current_interval)
        while checking_interval is not None:
            overlapping_conflict = self.check_overlapping_intervals_conflict(current_interval_id,
                                                                             checking_interval.intervalId)
            if overlapping_conflict is not None:
                if checking_interval.intervalId not in overlapping_intervals:
                    overlapping_conflicts.append(overlapping_conflict)

                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_previous_interval(checking_interval)
            else:
                break

        checking_interval = self.interval_order_handler.get_next_interval_by_end(current_interval)
        while checking_interval is not None:
            overlapping_conflict = self.check_overlapping_intervals_conflict(current_interval_id,
                                                                             checking_interval.intervalId)
            if overlapping_conflict is not None:
                if checking_interval.intervalId not in overlapping_intervals:
                    overlapping_conflicts.append(overlapping_conflict)

                overlapping_intervals.add(checking_interval.intervalId)
                checking_interval = self.interval_order_handler.get_next_interval_by_end(checking_interval)
            else:
                break



        return overlapping_conflicts

    def find_step_order_conflicts_for_current(self, current_interval_id: UUID) -> List[StepOrderConflict]:
        current_interval = self.resolved_intervals[current_interval_id]
        if current_interval.type == IntervalType.IDLE_PERIOD:
            return []
        current_step_orders = self.factory_info_provider.step_to_step_orders[current_interval_id]
        step_order_conflicts = []

        for step_order in current_step_orders:
            step_order_conflict = self.check_steps_order_conflict(step_order)
            if step_order_conflict is not None:
                step_order_conflicts.append(step_order_conflict)
        return step_order_conflicts

    def find_all_conflicts_with_current(self, interval_id: UUID, accounting_deadlines=False) -> List[Conflict]:
        conflicts = []
        conflicts.extend(self.find_overlapping_intervals_conflict_with_current(interval_id))
        conflicts.extend(self.find_step_order_conflicts_for_current(interval_id))
        machine_and_interval_conflict = self.check_machine_and_interval_conflict(interval_id)
        if machine_and_interval_conflict is not None:
            conflicts.append(machine_and_interval_conflict)
        if accounting_deadlines:
            deadline_conflict = self.check_deadline_conflict(interval_id)
            if deadline_conflict is not None:
                conflicts.append(deadline_conflict)
            pass

        return conflicts

    def find_all_intervals_with_conflict(self, accounting_deadlines=False) -> List[UUID]:
        intervals_id_with_conflict = []
        for interval_id in self.resolved_intervals.keys():
            if self.find_all_conflicts_with_current(interval_id, accounting_deadlines):
                intervals_id_with_conflict.append(interval_id)
        return intervals_id_with_conflict

    def get_resolved_steps(self):
        return self.parser_resolved_step.resolved_intervals_to_resolved_steps(self.resolved_intervals.values())

    def log_interval(self, interval_id: UUID):
        interval = self.resolved_intervals[interval_id]
        interval.log_state2("")
