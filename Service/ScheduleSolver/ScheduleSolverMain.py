import logging
from typing import Dict
from uuid import UUID

from Service.Factory.FactoryCreator import FactoryCreator
from Service.Factory.FactoryCropper import FactoryCropper
from Service.Factory.FactoryInfoProvider import FactoryInfoProvider
from Service.ScheduleSolver.OptimalAlgorithm.ScheduleSolverOptimal import ScheduleSolverOptimal
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleSolverRecursive import ScheduleSolverRecursive
from Service.ScheduleSolver.Model.MagneticConstraint import MagneticConstraint
from Model.Factory import Factory
from Model.MovedStep import MovedStep
from Model.MovementType import MovementType
from Model.ResolvedStep import ResolvedStep

logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


class ScheduleSolverMain:
    def __init__(self, factory: Factory, moved_steps: Dict[UUID, MovedStep]):
        logging.info("Starting ScheduleSolverMain")
        self.factory = factory
        self.factory_info_provider = FactoryInfoProvider(factory, moved_steps)
        self.schedule_handler_optimal = ScheduleSolverOptimal(self.factory_info_provider)
        self.schedule_handler_recursive = ScheduleSolverRecursive(self.factory_info_provider)
        self.factory_cropper = FactoryCropper()
        self.factory_creator = FactoryCreator()
        logging.info("Finished ScheduleSolverMain")

    def solve_optimal(self, max_search_time=40) -> ([ResolvedStep], str):
        resolved_steps, status = self.schedule_handler_optimal.solve_optimal()

        return resolved_steps, status

    def solve_for_moved_steps(self, moved_steps: [MovedStep], movement_type: MovementType, max_search_time=3) -> (
            [ResolvedStep], str):
        logging.info("Starting solve_for_moved_steps")

        magnetic_constraints: Dict[UUID, MagneticConstraint] = {}

        # magnetic_constraints изменяется
        resolved_steps, status = self.schedule_handler_recursive.solve_for_moved_steps(movement_type,
                                                                                       magnetic_constraints,
                                                                                       max_search_time)

        if status != "OPTIMAL" and status != "FEASIBLE":
            return resolved_steps, status

        resolved_steps_without_magnetic = resolved_steps



        resolved_steps, status = self.schedule_handler_optimal.adjust_solving_for_magnetic(
            resolved_steps_without_magnetic, magnetic_constraints, max_search_time)

        if status == "OPTIMAL" or status == "FEASIBLE":
            return resolved_steps, status

        status = "FEASIBLE"
        resolved_steps = resolved_steps_without_magnetic

        return resolved_steps, status

    def resolve_conflicts(self, max_search_time=3) -> ([ResolvedStep], str):
        logging.info("Starting resolve_conflicts")

        magnetic_constraints: Dict[UUID, MagneticConstraint] = {}

        # magnetic_constraints изменяется
        resolved_steps, status = self.schedule_handler_recursive.resolve_conflicts(magnetic_constraints,
                                                                                   max_search_time)

        if status != "OPTIMAL" and status != "FEASIBLE":
            return resolved_steps, status

        resolved_steps_without_magnetic = resolved_steps


        resolved_steps, status = self.schedule_handler_optimal.adjust_solving_for_magnetic(
            resolved_steps_without_magnetic, magnetic_constraints, max_search_time)

        if status == "OPTIMAL" or status == "FEASIBLE":
            return resolved_steps, status

        status = "FEASIBLE"
        resolved_steps = resolved_steps_without_magnetic

        return resolved_steps, status

    def solve_for_sorted_steps(self, sorted_steps: [UUID], max_search_time=3) -> ([ResolvedStep], str):
        logging.info("Starting sort steps")

        magnetic_constraints: Dict[UUID, MagneticConstraint] = {}

        # magnetic_constraints изменяется
        resolved_steps, status = self.schedule_handler_recursive.solve_for_sorted_steps(sorted_steps,
                                                                                        magnetic_constraints,
                                                                                        max_search_time)

        if status != "OPTIMAL" and status != "FEASIBLE":
            return resolved_steps, status

        resolved_steps_without_magnetic = resolved_steps

        resolved_steps, status = self.schedule_handler_optimal.adjust_solving_for_magnetic(
            resolved_steps_without_magnetic, magnetic_constraints, max_search_time)

        if status == "OPTIMAL" or status == "FEASIBLE":
            return resolved_steps, status

        status = "FEASIBLE"
        resolved_steps = resolved_steps_without_magnetic

        return resolved_steps, status

    def solve_optimal_for_demands(self, max_search_time=3) -> ([ResolvedStep], str):
        logging.info("Starting resolve fo demands")

        magnetic_constraints: Dict[UUID, MagneticConstraint] = {}

        # magnetic_constraints изменяется
        resolved_steps, status = self.schedule_handler_recursive.solve_optimal_for_demands(magnetic_constraints,
                                                                                           max_search_time)

        if status != "OPTIMAL" and status != "FEASIBLE":
            machines_connected_with_important_demands = self.factory_info_provider.get_machines_connected_with_important_demands()

            logging.info(f"machines_connected_with_important_demands: {machines_connected_with_important_demands}")
            cropped_factory = self.factory_cropper.crop(self.factory, machines_connected_with_important_demands)
            logging.info(f"cropped_factory len: {len(cropped_factory.steps)}")
            logging.info(f"cropped_factory steps: {cropped_factory.steps.keys()}")
            logging.info(f"cropped_factory steps: {cropped_factory.steps.values()}")

            cropped_optimal_solver = ScheduleSolverOptimal(FactoryInfoProvider(cropped_factory, {}))
            cropped_resolved_steps, status = cropped_optimal_solver.solve_optimal_for_demands()
            if status != "OPTIMAL" and status != "FEASIBLE":
                return resolved_steps, status

            # factory у которого поменялось расположение степов которые находились на  machines_connected_with_important_demands
            new_factory = self.factory_creator.create(self.factory, cropped_resolved_steps)

            new_solver = ScheduleSolverMain(new_factory, {})

            # добавляем переналадки ко всем шагам
            optimal_resolved_steps, optimal_status = new_solver.resolve_conflicts()

            return optimal_resolved_steps, optimal_status

        resolved_steps_without_magnetic = resolved_steps

        resolved_steps, status = self.schedule_handler_optimal.adjust_solving_for_magnetic(
            resolved_steps_without_magnetic, magnetic_constraints, max_search_time)

        if status == "OPTIMAL" or status == "FEASIBLE":
            return resolved_steps, status

        status = "FEASIBLE"
        resolved_steps = resolved_steps_without_magnetic

        return resolved_steps, status


