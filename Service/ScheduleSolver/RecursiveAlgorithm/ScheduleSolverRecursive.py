import time
import logging
from collections import deque
import random
from typing import Dict
from uuid import UUID

from Service.Factory.FactoryInfoProvider import FactoryInfoProvider
from Service.ScheduleSolver.Model.MagneticConstraint import MagneticConstraint
from Service.ScheduleSolver.OptimalAlgorithm.ScheduleSolverOptimal import ScheduleSolverOptimal
from Service.ScheduleSolver.Model.MagneticType import MagneticType
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictRegistry import ConflictRegistry
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictResolver import ConflictResolver
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictResolver2 import ConflictResolver2
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.ConflictType import ConflictType
from Service.Exceptions.ConflictException import ConflictException
from Model.Factory import Factory
from Model.IntervalType import IntervalType
from Model.MovementType import MovementType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Model.ResolvedStep import ResolvedStep
from Model.StepOrderType import StepOrderType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.ScheduleHandler import ScheduleHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


def log_blank_line():
    logger = logging.getLogger()
    handlers = logger.handlers
    # Сохраняем старые форматтеры
    old_formatters = [h.formatter for h in handlers]

    try:
        # Устанавливаем временный пустой формат
        for h in handlers:
            h.setFormatter(logging.Formatter('%(message)s'))
        logging.info("")
    finally:
        # Возвращаем старые форматтеры
        for h, fmt in zip(handlers, old_formatters):
            h.setFormatter(fmt)


def suppress_logging():
    logging.disable(logging.CRITICAL)  # Отключает все логи до CRITICAL включительно


def enable_logging():
    logging.disable(logging.NOTSET)  # Включает логирование обратно


class ScheduleSolverRecursive:

    def __init__(self, factory_info_provider: FactoryInfoProvider, conflict_resolver_type=1, maxSearchTime=2):
        self.maxSearchTime = maxSearchTime
        self.factory_info_provider = factory_info_provider
        self.factory = self.factory_info_provider.factory
        self.last_resolved_conflict_of_step: Dict[UUID] = {}
        self.min_step_start: Dict[UUID] = {}
        for step in self.factory.steps.values():
            self.min_step_start[step.stepId] = step.start

        self.schedule_handler = ScheduleHandler(factory_info_provider)
        self.conflict_registry = ConflictRegistry()
        if conflict_resolver_type == 1:
            self.conflict_resolver = ConflictResolver(self.schedule_handler, self.conflict_registry)
        else:
            self.conflict_resolver = ConflictResolver2(self.schedule_handler, self.conflict_registry)

    def solve_optimal_for_demands(self, magnetic_constraints, max_search_time=3) -> ([ResolvedStep], str):

        logging.info("Starting resolve fo demands")

        self.create_magnetic_constraints(magnetic_constraints)

        intervals_with_conflicts = self.schedule_handler.find_all_intervals_with_conflict(accounting_deadlines=True)

        try:
            step_to_processing_count = self.reschedule(intervals_with_conflicts, 3, accounting_deadlines=True)
        except ConflictException as e:
            return None, "UNKNOWN"

        logging.info("Finished reschedule")

        status = "FEASIBLE"
        resolved_steps_without_magnetic = self.schedule_handler.get_resolved_steps()

        self.set_magnetic_types_for_solving_optimal_for_demands(magnetic_constraints, step_to_processing_count)

        return resolved_steps_without_magnetic, status

    def solve_for_sorted_steps(self, sorted_steps: [UUID], magnetic_constraints, max_search_time=3) -> (
            [ResolvedStep], str):
        logging.info("Starting sort steps")

        self.create_magnetic_constraints(magnetic_constraints)
        sorted_steps.sort(key=lambda x: self.factory.steps[x].start, reverse=True)

        try:
            step_to_processing_count = self.reschedule(sorted_steps, 3)
        except ConflictException as e:
            return None, "UNKNOWN"

        logging.info("Finished reschedule")

        status = "FEASIBLE"
        resolved_steps_without_magnetic = self.schedule_handler.get_resolved_steps()

        self.set_magnetic_types_for_sorting(magnetic_constraints, step_to_processing_count, sorted_steps)

        return resolved_steps_without_magnetic, status

    def solve_for_moved_steps(self, movementType: MovementType, magnetic_constraints, max_search_time=3) -> (
            [ResolvedStep], str):
        logging.info("Starting solve_for_moved_steps")
        self.create_magnetic_constraints(magnetic_constraints)

        # self.create_magnetic_constraints()
        self.correct_initial_moved_steps_position(self.factory_info_provider.moved_steps)

        logging.info(f"Corrected moved steps: {self.factory_info_provider.moved_steps.keys()}")

        try:
            step_to_processing_count = self.reschedule(self.factory_info_provider.moved_steps.keys(), 10)
        except ConflictException as e:
            return None, "UNKNOWN"

        logging.info("Finished reschedule")

        status = "FEASIBLE"
        resolved_steps_without_magnetic = self.schedule_handler.get_resolved_steps()

        if movementType == MovementType.SOFT:
            self.set_magnetic_types_for_soft_moving(magnetic_constraints, step_to_processing_count)

        elif movementType == MovementType.LEFT_MAGNETIZATION:
            self.set_magnetic_types_for_magnetic_moving(magnetic_constraints, step_to_processing_count)

        return resolved_steps_without_magnetic, status

    def resolve_conflicts(self, magnetic_constraints, max_search_time=10) -> ([ResolvedStep], str):
        logging.info("Starting resolve_conflicts")

        self.create_magnetic_constraints(magnetic_constraints)

        intervals_with_conflicts = self.schedule_handler.find_all_intervals_with_conflict()

        try:
            step_to_processing_count = self.reschedule(intervals_with_conflicts, max_search_time)
        except ConflictException as e:
            return None, "UNKNOWN"

        logging.info("Finished reschedule")

        status = "FEASIBLE"
        resolved_steps_without_magnetic = self.schedule_handler.get_resolved_steps()

        self.set_magnetic_types_for_soft_moving(magnetic_constraints, step_to_processing_count)

        return resolved_steps_without_magnetic, status

    def reschedule(self, intervals_with_conflicts: [UUID], time_limit,
                   accounting_deadlines=False):
        processing_count = 0
        step_to_processing_count = {}
        step_to_empty_processing_count = {}

        for step in self.factory.steps.values():
            step_to_processing_count[step.stepId] = 0
            step_to_empty_processing_count[step.stepId] = 0

        start_time = time.time()
        adjusted_steps = set()
        queue = deque()
        queue.extend(intervals_with_conflicts)
        logging.info(f"Starting rescheduling with time limit: {time_limit} seconds")
        a = 0
        b = 0

        while queue:
            processing_count += 1
            if processing_count == 100:
                suppress_logging()
                logging.info("Processing count is 20")

            current_interval_id = queue.pop()
            log_blank_line()
            logging.info(
                f"------- Processing step: {self.factory_info_provider.interval_to_name[current_interval_id]} ----------------------------------------------------------")

            # Проверка ограничения по времени
            if time.time() - start_time > time_limit:
                enable_logging()
                logging.warning("Time limit exceeded")

                logging.info(
                    f" Total adjusted tasks: {len(adjusted_steps)}. "
                    f"Total time: {time.time() - start_time} seconds.")

                logging.info(f"Processing count is {processing_count}")

                steps_and_processing_count = [(step, count) for step, count in step_to_processing_count.items() if
                                              count > 0]
                steps_and_processing_count.sort(key=lambda x: self.factory_info_provider.interval_to_name[x[0]])

                [logging.info(
                    f"Step: {step} {self.factory_info_provider.interval_to_name[step]} has been processed {count} times and {step_to_empty_processing_count[step]} empty times")
                    for step, count in
                    steps_and_processing_count]
                logging.info(f"a = {a} b = {b}")

                raise ConflictException("Time limit exceeded")

            empty_flag = True

            if current_interval_id in self.factory.steps.keys():
                step_to_processing_count[current_interval_id] += 1

            adjusted_steps.add(current_interval_id)

            # разрешение конфликтов если step находится до начала старта машины
            machine_interval_conflict = self.schedule_handler.check_machine_and_interval_conflict(current_interval_id)
            if machine_interval_conflict is not None:
                self.conflict_registry.add_machine_and_interval_conflict(machine_interval_conflict)
                _, updated_intervals_id = self.conflict_resolver.resolve_machine_and_interval_conflict(
                    current_interval_id)
                queue.append(current_interval_id)
                queue.extendleft(updated_intervals_id)
                continue

            # Шаг 3: Разрешение конфликтов пересечения на машине
            continue_flag = False
            overlapping_conflicts = self.schedule_handler.find_overlapping_intervals_conflict_with_current(
                current_interval_id)
            if len(overlapping_conflicts) > 0:
                log_blank_line()
                logging.info(f"Found {len(overlapping_conflicts)} overlapping Conflict for step {current_interval_id}")
                empty_flag = False
                # logging.info(f"overlapping conflicts {overlapping_conflicts}")

            for conflict in overlapping_conflicts:
                # фиксиурем кофликт пересечения
                self.conflict_registry.add_overlapping_intervals_conflict(conflict)
                logging.info(f"Handling overlapping conflict  {conflict}")
                adjusted_interval_id, updated_intervals_id = self.conflict_resolver.resolve_overlapping_intervals_conflict(
                    current_interval_id, conflict)
                queue.append(adjusted_interval_id)
                if adjusted_interval_id in self.factory_info_provider.moved_steps.keys():
                    a += 1
                queue.extendleft(updated_intervals_id)
                if adjusted_interval_id == current_interval_id:
                    continue_flag = True
                    break
            if continue_flag:
                continue

            # Шаг 4: Обеспечение выполнения порядка степов
            step_order_conflicts = self.schedule_handler.find_step_order_conflicts_for_current(current_interval_id)
            if len(step_order_conflicts) > 0:
                empty_flag = False
                log_blank_line()
                logging.info(
                    f"Found {len(step_order_conflicts)} step order conflicts for interval {current_interval_id}")
                # logging.info(f"step order conflicts {step_order_conflicts}")

            for conflict in step_order_conflicts:
                self.conflict_registry.add_steps_order_conflict(conflict)
                logging.info(f"Handling step order conflict  {conflict}")
                adjusted_interval_id, updated_intervals_id = self.conflict_resolver.resolve_steps_order_conflict(
                    current_interval_id, conflict)
                queue.append(adjusted_interval_id)
                if adjusted_interval_id in self.factory_info_provider.moved_steps.keys():
                    b += 1
                queue.extendleft(updated_intervals_id)
                if adjusted_interval_id == current_interval_id:
                    continue_flag = True
                    break
            if continue_flag:
                continue

            # разрешение конфликтов если step находится после дедлайна
            if accounting_deadlines:
                deadline_conflict = self.schedule_handler.check_deadline_conflict(
                    current_interval_id)

                if deadline_conflict is not None:
                    self.conflict_registry.add_deadline_conflict(deadline_conflict)
                    _, updated_intervals_id = self.conflict_resolver.resolve_deadline_conflict(deadline_conflict)

                    queue.append(current_interval_id)
                    queue.extendleft(updated_intervals_id)
                    continue

            if empty_flag and current_interval_id in self.factory.steps.keys():
                step_to_empty_processing_count[current_interval_id] += 1
                # step_to_processing_count[current_interval_id] -= 1

        enable_logging()

        logging.info(
            f"Rescheduling completed successfully. Total adjusted tasks: {len(adjusted_steps)}. "
            f"Total time: {time.time() - start_time} seconds.")

        logging.info(f"Processing count is {processing_count}")

        steps_and_processing_count = [(step, count) for step, count in step_to_processing_count.items() if count > 0]
        steps_and_processing_count.sort(key=lambda x: self.factory_info_provider.interval_to_name[x[0]])

        [logging.info(
            f"Step: {step} {self.factory_info_provider.interval_to_name[step]} has been processed {count} times and {step_to_empty_processing_count[step]} empty times")
            for step, count in
            steps_and_processing_count]
        logging.info(f"a = {a} b = {b}")
        logging.info(
            f"overlapping_offset = {self.conflict_resolver.overlapping_offset} step_order_offset = {self.conflict_resolver.step_order_offset}")

        return step_to_processing_count

    def set_magnetic_types_for_magnetic_moving(self, magnetic_constraints: Dict[UUID, MagneticConstraint],
                                               step_to_processing_count):
        # степы которые не двигались останутся на месте
        for magneticConstraint in magnetic_constraints.values():
            if step_to_processing_count[magneticConstraint.stepId] == 0:
                magneticConstraint.magneticType = MagneticType.FIXED
            else:
                magneticConstraint.magneticType = MagneticType.LEFT_CONSTRAINED

        # степы которые находятся в компоненте связности с перемещенными будут стремиться к strivingPoint
        moving_components = set()
        for moved_step_id in self.factory_info_provider.moved_steps.keys():
            moving_components.add(self.factory_info_provider.connectivity_components[moved_step_id])

        for step in self.factory.steps.values():
            if self.factory_info_provider.connectivity_components[step.stepId] in moving_components:
                magnetic_constraints[step.stepId].magneticType = MagneticType.MOVABLE

        # степы которые перетащили будут примагничены без ограничений
        for moved_step_id in self.factory_info_provider.moved_steps.keys():
            magnetic_constraints[moved_step_id].magneticType = MagneticType.MOVABLE
            magnetic_constraints[moved_step_id].strivingPoint = self.factory.start

    def set_magnetic_types_for_soft_moving(self, magnetic_constraints: Dict[UUID, MagneticConstraint],
                                           step_to_processing_count):
        # степы которые не двигались останутся на месте
        for magneticConstraint in magnetic_constraints.values():
            if step_to_processing_count[magneticConstraint.stepId] == 0:
                magneticConstraint.magneticType = MagneticType.FIXED
            else:
                magneticConstraint.magneticType = MagneticType.LEFT_CONSTRAINED

                # обновляем границу равную минимальному месту, где находился степ
                magneticConstraint.leftBoarder = self.min_step_start[magneticConstraint.stepId]

            # степы которые находятся в компоненте связности с перемещенными будут стремиться к strivingPoint (изначальное их место
            moving_components = set()
            for moved_step_id in self.factory_info_provider.moved_steps.keys():
                moving_components.add(self.factory_info_provider.connectivity_components[moved_step_id])

            for step in self.factory.steps.values():
                if self.factory_info_provider.connectivity_components[step.stepId] in moving_components:
                    magnetic_constraints[step.stepId].magneticType = MagneticType.MOVABLE

            # степы которые перетащили будут примагничены c ограничениями
            for moved_step_id in self.factory_info_provider.moved_steps.keys():
                magnetic_constraints[moved_step_id].magneticType = MagneticType.LEFT_CONSTRAINED

    def set_magnetic_types_for_solving_optimal_for_demands(self, magnetic_constraints: Dict[UUID, MagneticConstraint],
                                                           step_to_processing_count):
        # степы которые не двигались останутся на месте
        for magneticConstraint in magnetic_constraints.values():
            if step_to_processing_count[magneticConstraint.stepId] == 0:
                magneticConstraint.magneticType = MagneticType.FIXED
            else:
                magneticConstraint.magneticType = MagneticType.LEFT_CONSTRAINED

        # степы у которых важен дедлайн зафиксировано положение
        for step in self.factory.steps.values():
            if step.demandId in self.factory.importantDemands.keys():
                magnetic_constraints[step.stepId].magneticType = MagneticType.LEFT_CONSTRAINED
                magnetic_constraints[step.stepId].strivingPoint = self.factory.start
                magnetic_constraints[step.stepId].weight = 10000

    def set_magnetic_types_for_sorting(self, magnetic_constraints: Dict[UUID, MagneticConstraint],
                                       step_to_processing_count, sorted_steps):
        # степы которые не двигались останутся на месте
        for magneticConstraint in magnetic_constraints.values():
            if step_to_processing_count[magneticConstraint.stepId] == 0:
                magneticConstraint.magneticType = MagneticType.FIXED
            else:
                magneticConstraint.magneticType = MagneticType.LEFT_CONSTRAINED

        # самое левое начало среди степов которые сортируются
        left_constraint_of_sorting_steps = min(
            (self.factory.steps[sorted_step].start for sorted_step in sorted_steps),
            default=0
        )
        # степы которые находятся в компоненте связности с сортируемыми будут и стремиться к дефолтной strivingPoint
        moving_components = set()
        for sorted_step_id in sorted_steps:
            moving_components.add(self.factory_info_provider.connectivity_components[sorted_step_id])

        for step in self.factory.steps.values():
            if self.factory_info_provider.connectivity_components[step.stepId] in moving_components:
                magnetic_constraints[step.stepId].magneticType = MagneticType.MOVABLE

        # степы которые сортируются будут примагничены будут с ограничениями и будут стремиться к strivingPoint
        for sorted_step in sorted_steps:
            magnetic_constraints[sorted_step].magneticType = MagneticType.LEFT_CONSTRAINED
            magnetic_constraints[sorted_step].strivingPoint = left_constraint_of_sorting_steps
            magnetic_constraints[sorted_step].weight = 10000

    def correct_initial_moved_steps_position(self, moved_steps):
        for moved_step_id in moved_steps:
            self.correct_one_initial_moved_step_position(moved_step_id)

    def correct_one_initial_moved_step_position(self,
                                                moved_step_id: UUID):
        previous_interval_id = self.schedule_handler.get_previous_interval_id_by_start(moved_step_id)
        if previous_interval_id is not None:
            if self.schedule_handler.check_overlapping_intervals_conflict(previous_interval_id,
                                                                          moved_step_id) is not None:
                self.schedule_handler.move_interval_after_interval_on_same_machine(moved_step_id, previous_interval_id)

    def create_magnetic_constraints(self, magnetic_constraints: Dict[UUID, MagneticConstraint]):
        magnetic_constraints.clear()
        for step in self.factory.steps.values():
            if step.stepId in self.factory_info_provider.moved_steps.keys():
                magnetic_constraints[step.stepId] = MagneticConstraint(step.stepId, step.start, step.start,
                                                                       MagneticType.NONE,
                                                                       10000)
            else:
                magnetic_constraints[step.stepId] = MagneticConstraint(step.stepId, step.start, step.start,
                                                                       MagneticType.NONE,
                                                                       1)

    def find_steps_with_conflict(self):
        intervals_with_conflict = self.schedule_handler.find_all_intervals_with_conflict()
        steps_with_conflict = [intervalId for intervalId in intervals_with_conflict if
                               intervalId in self.factory.steps.keys()]
        return steps_with_conflict
