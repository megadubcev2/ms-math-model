import logging
from uuid import UUID
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntervalVar, IntVar, CpSolver

from Model.EntityType import EntityType
from Model.StepType import StepType
from Service.Factory.FactoryCreator import FactoryCreator
from Service.Factory.FactoryCropper import FactoryCropper
from Service.Factory.FactoryInfoProvider import FactoryInfoProvider
from Service.ScheduleSolver.OptimalAlgorithm.SlowPeriodConstraintHandler import SlowPeriodConstraintHandler
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Util.ParserResolvedIntervals import \
    ParserResolvedIntervals
from Service.ScheduleSolver.Model.MagneticConstraint import MagneticConstraint
from Service.ScheduleSolver.Model.MagneticType import MagneticType
from Service.ScheduleSolver.OptimalAlgorithm.Model.SetupVariable import SetupVariable
from Service.ScheduleSolver.OptimalAlgorithm.Model.StepVariable import StepVariable
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictRegistry import ConflictRegistry
from Model.IntervalType import IntervalType
from Model.MovementType import MovementType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval

from Model.Factory import Factory
from Model.ResolvedStep import ResolvedStep
from typing import Dict, List

from Model.StepOrderType import StepOrderType

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScheduleSolverOptimal:
    def __init__(self, factory_info_provider: FactoryInfoProvider, maxSearchTime=15, movedSteps={}):
        self.factory_info_provider = factory_info_provider
        self.factory = factory_info_provider.factory
        self.all_variables: Dict[UUID, StepVariable] = {}
        self.all_differences: [IntVar]
        self.relative_starts_sum: IntVar
        self.last_resolved_intervals: [ResolvedInterval] = []

        self.starts_diff_sum: IntVar

        self.last_solver_without_setups: CpSolver
        self.last_solver_after_setups: CpSolver

        self.all_stepVariables: Dict[UUID, StepVariable] = {}
        self.all_fake_stepVariables: Dict[UUID, StepVariable] = {}
        self.all_setupVariables: Dict[UUID, SetupVariable] = {}
        self.machine_to_intervals: Dict[UUID, List[IntervalVar]] = {}
        self.machine_to_stepVariables: Dict[UUID, List[StepVariable]] = {}
        self.important_vars = []

        self.maxSearchTime = maxSearchTime
        self.movedSteps = movedSteps
        self.parserResolvedIntervals = ParserResolvedIntervals()

        self.slow_period_constraint_handler = SlowPeriodConstraintHandler(self.factory)
        self.factoryCropper = FactoryCropper()
        self.factoryCreator = FactoryCreator()

    def create_demo_model(self, expansion=0, add_fixed_steps=True, need_machine_constraints=True):
        # to do
        expansion = 0

        model = cp_model.CpModel()

        self.initialize_step_variables(model, expansion)
        self.initialize_fake_step_variables(model, expansion)
        self.initialize_idle_period_variables(model, expansion)

        self.important_vars = self.slow_period_constraint_handler.add_slow_period_constraints(model,
                                                                                              self.all_stepVariables,
                                                                                              self.all_fake_stepVariables)

        # добавляю ограничения в модель
        self.add_steps_order_constraints(model, expansion)
        if need_machine_constraints:
            self.add_machine_constraints(model)
        if add_fixed_steps:
            self.add_fixed_steps_constraints(model)

        return model

    def initialize_step_variables(self, model: cp_model.CpModel, expansion: int = 0):
        self.all_stepVariables.clear()
        self.machine_to_stepVariables.clear()
        self.machine_to_intervals.clear()

        for stepId in self.factory.steps:
            machine_id = self.factory.steps[stepId].machineId
            suffix = f'_step_{stepId}'

            start_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                        'start' + suffix)
            end_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration, 'end' + suffix)
            duration_var = model.NewIntVar(0, self.factory.duration, 'duration' + suffix)

            # todo
            step_expansion = expansion
            if self.factory.steps[stepId].fixed:
                step_expansion = 0

            interval_var = model.NewIntervalVar(start_var, duration_var,
                                                end_var,
                                                'interval' + suffix)

            stepVariable = StepVariable(stepId=stepId, duration=duration_var,
                                        start=start_var, end=end_var,
                                        interval=interval_var)

            self.all_stepVariables[stepId] = stepVariable

            self.machine_to_stepVariables.setdefault(machine_id, []).append(stepVariable)
            self.machine_to_intervals.setdefault(machine_id, []).append(interval_var)

    def initialize_fake_step_variables(self, model: cp_model.CpModel, expansion: int = 0):
        self.all_fake_stepVariables.clear()

        for stepId in self.factory.steps:
            step_duration = self.factory.steps[stepId].initialDuration
            suffix = f'_fake_step_{stepId}'

            start_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                        'start' + suffix)
            end_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration, 'end' + suffix)
            duration_var = model.NewIntVar(0, self.factory.duration, 'duration' + suffix)

            # todo
            step_expansion = expansion
            if self.factory.steps[stepId].fixed:
                step_expansion = 0

            model.Add(duration_var == step_duration + step_expansion)

            interval_var = model.NewIntervalVar(start_var, duration_var,
                                                end_var,
                                                'interval' + suffix)

            stepVariable = StepVariable(stepId=stepId, duration=duration_var,
                                        start=start_var, end=end_var,
                                        interval=interval_var)

            self.all_fake_stepVariables[stepId] = stepVariable

    def initialize_idle_period_variables(self, model: cp_model.CpModel, expansion: int = 0):

        for idle_period in self.factory.idlePeriods:
            machine_id = idle_period.machineId
            idle_period_duration = idle_period.duration
            idle_period_start = idle_period.start

            suffix = f'_idle_period_{idle_period.idlePeriodId}'

            interval_var = model.NewIntervalVar(idle_period_start, idle_period_duration + expansion,
                                                idle_period_start + idle_period_duration + expansion,
                                                'interval' + suffix)

            self.machine_to_intervals.setdefault(machine_id, []).append(interval_var)

    def add_steps_order_constraints(self, model: cp_model.CpModel, expansion=0):
        for step_order in self.factory_info_provider.allStepsOrder:
            overlapMin = step_order.overlapMin
            overlapMax = step_order.overlapMax

            if step_order.stepOrderType == StepOrderType.END_RUN:
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].start >= self.all_stepVariables[
                        step_order.previousStepId].end + overlapMin)
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].start <= self.all_stepVariables[
                        step_order.previousStepId].end + max(overlapMax - expansion, overlapMin))

            elif step_order.stepOrderType == StepOrderType.RUN_RUN:
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].start >= self.all_stepVariables[
                        step_order.previousStepId].start + overlapMin)
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].start <= self.all_stepVariables[
                        step_order.previousStepId].start + max(overlapMax - expansion, overlapMin))

            elif step_order.stepOrderType == StepOrderType.END_END:
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].end >= self.all_stepVariables[
                        step_order.previousStepId].end + overlapMin)
                model.Add(
                    self.all_stepVariables[step_order.nextStepId].end <= self.all_stepVariables[
                        step_order.previousStepId].end + max(overlapMax - expansion, overlapMin))

    def add_machine_constraints(self, model: cp_model.CpModel):
        for machineId in self.factory.machines.keys():
            if machineId in self.machine_to_intervals:
                model.AddNoOverlap(self.machine_to_intervals[machineId])

        for step in self.factory.steps.values():
            step_var = self.all_stepVariables[step.stepId]
            machine = self.factory.machines[step.machineId]
            model.Add(machine.start <= step_var.start)

    def add_fixed_steps_constraints(self, model: cp_model.CpModel):
        for fixed_step in self.factory.fixedSteps:
            if fixed_step.stepId in self.all_stepVariables:
                model.Add(self.all_stepVariables[fixed_step.stepId].start == fixed_step.start)

    def add_previous_order_constraints_for_not_moved(self, model: cp_model.CpModel, demo_solver: CpSolver):
        for machine_id in self.machine_to_stepVariables.keys():
            # todo
            moved_step = self.movedSteps[0]
            moved_step_component = self.factory.connectivity_components[moved_step.stepId]

            step_vars_in_machine = self.machine_to_stepVariables[machine_id]
            step_vars_in_machine.sort(key=lambda step_var: self.get_moved_step_new_start(step_var) if self.is_moved(
                step_var) else demo_solver.Value(step_var.start))

            for i in range(len(step_vars_in_machine) - 1):

                previous_step_var = step_vars_in_machine[i]
                next_step_var = step_vars_in_machine[i + 1]

                if self.factory.connectivity_components[previous_step_var.stepId] == moved_step_component:
                    continue

                if self.factory.connectivity_components[next_step_var.stepId] == moved_step_component:
                    continue

                model.Add(previous_step_var.end <= next_step_var.start)

    def add_moved_steps_constraints(self, model: cp_model.CpModel, max_deviation: int = 0):
        if self.movedSteps is not None:
            if max_deviation == 0:
                for moved_step in self.movedSteps:
                    model.Add(self.all_stepVariables[moved_step.stepId].start == moved_step.newStart)
            else:
                for moved_step in self.movedSteps:
                    model.Add(self.all_stepVariables[moved_step.stepId].start <= moved_step.newStart + max_deviation)
                    model.Add(self.all_stepVariables[moved_step.stepId].start >= moved_step.newStart - max_deviation)

    def add_sequence_constraints(self, model: cp_model.CpModel, resolved_steps_full):
        for machine_id in self.machine_to_stepVariables.keys():

            resolved_steps_in_machine = [step for step in resolved_steps_full if
                                         self.factory.steps[step.stepId].machineId == machine_id]
            resolved_steps_in_machine.sort(key=lambda step: step.start)

            step_vars_in_machine = [self.all_stepVariables[step.stepId] for step in resolved_steps_in_machine]

            for i in range(len(step_vars_in_machine) - 1):
                previous_step_var = step_vars_in_machine[i]
                next_step_var = step_vars_in_machine[i + 1]

                model.Add(previous_step_var.end <= next_step_var.start)

                # logging.info(
                #     f"MachineId: {machine_id},previous_step_var {previous_step_var.stepId}, next_step_var {next_step_var.stepId} , ")

    def add_magnetic_constraints(self, model: cp_model.CpModel, resolved_steps_full,
                                 magnetic_constraints: Dict[UUID, MagneticConstraint]):
        # logger.info("Adding magnetic constraints...")
        for step in resolved_steps_full:
            step_var = self.all_stepVariables[step.stepId]
            magnetic_constraint = magnetic_constraints[step.stepId]

            if magnetic_constraint.magneticType == MagneticType.FIXED:
                # logger.info(f"Applying FIXED constraint: stepId={magnetic_constraint.stepId}, "
                #             f"leftConstraint={step.start}")
                model.Add(step_var.start == step.start)

            elif magnetic_constraint.magneticType == MagneticType.LEFT_CONSTRAINED:

                left_constraint = min(self.factory.steps[step.stepId].start, step.start,
                                      magnetic_constraint.strivingPoint, magnetic_constraint.leftBoarder)
                # logger.info(f"Applying LEFT_CONSTRAINED constraint: stepId={magnetic_constraint.stepId}, "
                #             f"leftConstraint={left_constraint}")
                model.Add(step_var.start >= left_constraint)

        logger.info("Magnetic constraints added successfully.")

    def set_optimization_objective_by_sum_starts(self, model: cp_model.CpModel):
        self.relative_starts_sum = model.NewIntVar(0, self.factory.duration * len(self.factory.steps),
                                                   'relative_starts_sum')
        all_step_starts = [self.all_stepVariables[step_var].start for step_var in self.all_stepVariables]

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(self.relative_starts_sum == sum(all_step_starts) - self.factory.start * len(self.factory.steps))

        model.Minimize(self.relative_starts_sum)

    def set_optimization_objective_by_steps_in_deadlines(self, model: cp_model.CpModel):
        steps_in_deadlines_count = model.NewIntVar(0, len(self.factory.steps),
                                                   'steps_in_deadlines_count')
        all_steps_in_deadlines = []

        for step_variable in self.all_stepVariables.values():
            suffix = f'_step_{step_variable.stepId}'

            is_step_in_deadline = model.NewBoolVar(
                'is_step_in_deadline' + suffix)  # Задайте подходящие границы для разности
            step = self.factory.steps[step_variable.stepId]
            demandId = step.demandId
            deadline = self.factory.demands[demandId].dueDate

            model.Add(step_variable.end <= deadline).OnlyEnforceIf(is_step_in_deadline)
            model.Add(step_variable.end > deadline).OnlyEnforceIf(is_step_in_deadline.Not())

            all_steps_in_deadlines.append(is_step_in_deadline)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(steps_in_deadlines_count == sum(all_steps_in_deadlines))

        model.Maximize(steps_in_deadlines_count)

    def set_optimization_objective_by_steps_closely_to_deadlines(self, model: cp_model.CpModel):
        positive_diff_steps_and_deadlines_sum = model.NewIntVar(0, len(self.factory.steps) * (
                self.factory.duration + 1000000),
                                                                'positive_diff_steps_and_deadlines_sum')
        all_positive_diff_steps_and_deadlines = []

        for step_variable in self.all_stepVariables.values():
            suffix = f'_step_{step_variable.stepId}'

            is_step_in_deadline = model.NewBoolVar(
                'is_step_in_deadline' + suffix)  # Задайте подходящие границы для разности

            positive_diff_step_and_deadline = model.NewIntVar(0, self.factory.duration + 1000000,
                                                              'positive_diff_step_and_deadline' + suffix)
            step = self.factory.steps[step_variable.stepId]
            demandId = step.demandId
            deadline = self.factory.demands[demandId].dueDate

            model.Add(step_variable.end <= deadline).OnlyEnforceIf(is_step_in_deadline)
            model.Add(step_variable.end > deadline).OnlyEnforceIf(is_step_in_deadline.Not())

            model.Add(positive_diff_step_and_deadline == 0).OnlyEnforceIf(is_step_in_deadline)
            model.Add(positive_diff_step_and_deadline == step_variable.end - deadline + 1000000).OnlyEnforceIf(
                is_step_in_deadline.Not())

            all_positive_diff_steps_and_deadlines.append(positive_diff_step_and_deadline)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(positive_diff_steps_and_deadlines_sum == sum(all_positive_diff_steps_and_deadlines))

        model.Minimize(positive_diff_steps_and_deadlines_sum)

    def set_optimization_objective_by_demands_in_deadlines(self, model: cp_model.CpModel):
        demands_in_deadlines_count = model.NewIntVar(0, len(self.factory.steps),
                                                     'steps_in_deadlines_count')
        all_demands_in_deadlines = []

        for demand in self.factory.demands.values():
            suffix = f'_demand_{demand.demandId}'

            is_demand_in_deadline = model.NewBoolVar(
                'is_demand_in_deadline' + suffix)  # Задайте подходящие границы для разности
            step_var_ends_in_demand = []
            for step in self.factory.demands_to_steps[demand.demandId]:
                step_var_ends_in_demand.append(self.all_stepVariables[step.stepId].end)

            max_end_in_demand = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                                "max_end_in_demand" + suffix)

            model.add_max_equality(max_end_in_demand, step_var_ends_in_demand)

            deadline = demand.dueDate

            model.Add(max_end_in_demand <= deadline).OnlyEnforceIf(is_demand_in_deadline)
            model.Add(max_end_in_demand > deadline).OnlyEnforceIf(is_demand_in_deadline.Not())

            all_demands_in_deadlines.append(is_demand_in_deadline)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(demands_in_deadlines_count == sum(all_demands_in_deadlines))

        model.Maximize(demands_in_deadlines_count)

    def set_optimization_objective_by_demands_closely_to_deadlines(self, model: cp_model.CpModel):

        positive_diff_demands_and_deadlines_sum = model.NewIntVar(0, len(self.factory.steps) * (
                self.factory.duration + 1000000),
                                                                  'positive_diff_demands_and_deadlines_sum')
        all_positive_diff_demands_and_deadlines = []

        for demand in self.factory.demands.values():
            suffix = f'_demand_{demand.demandId}'

            is_demand_in_deadline = model.NewBoolVar(
                'is_demand_in_deadline' + suffix)  # Задайте подходящие границы для разности

            positive_diff_demand_and_deadline = model.NewIntVar(0, self.factory.duration + 1000000,
                                                                'positive_diff_demand_and_deadline' + suffix)
            step_var_ends_in_demand = []
            for step in self.factory.demands_to_steps[demand.demandId]:
                step_var_ends_in_demand.append(self.all_stepVariables[step.stepId].end)

            max_end_in_demand = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                                "max_end_in_demand" + suffix)

            model.add_max_equality(max_end_in_demand, step_var_ends_in_demand)

            deadline = demand.dueDate

            model.Add(max_end_in_demand <= deadline).OnlyEnforceIf(is_demand_in_deadline)
            model.Add(max_end_in_demand > deadline).OnlyEnforceIf(is_demand_in_deadline.Not())

            model.Add(positive_diff_demand_and_deadline == 0).OnlyEnforceIf(is_demand_in_deadline)
            model.Add(positive_diff_demand_and_deadline == max_end_in_demand - deadline + 1000000).OnlyEnforceIf(
                is_demand_in_deadline.Not())

            all_positive_diff_demands_and_deadlines.append(positive_diff_demand_and_deadline)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(positive_diff_demands_and_deadlines_sum == sum(all_positive_diff_demands_and_deadlines))

        model.Maximize(positive_diff_demands_and_deadlines_sum)

    # заодно здесь и намекаем на предыдущее решение
    def set_optimization_objective_by_abs_diff_starts(self, model: cp_model.CpModel, demo_solver: CpSolver):
        self.starts_diff_sum = model.NewIntVar(0, self.factory.duration * len(self.factory.steps) * 2,
                                               'starts_diff_sum')
        all_positive_differences: [IntVar] = []
        self.all_differences: [IntVar] = []

        for step_variable in self.all_stepVariables.values():
            if self.is_moved(step_variable):
                continue

            suffix = f'_step_{step_variable.stepId}'

            difference = model.NewIntVar(-self.factory.duration, self.factory.duration,
                                         'difference' + suffix)  # Задайте подходящие границы для разности

            # Создаем переменную для результата, которая будет равна разности или 0
            positive_difference = model.NewIntVar(0, self.factory.duration * 2,
                                                  'positive_difference' + suffix)  # Задайте подходящие границы для результата

            # Вычисляем разность
            model.Add(difference == step_variable.start - demo_solver.Value(step_variable.start))

            model.AddAbsEquality(positive_difference, difference)

            all_positive_differences.append(positive_difference)
            self.all_differences.append(difference)

            model.AddHint(difference, 0)
            model.AddHint(positive_difference, 0)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(self.starts_diff_sum == sum(all_positive_differences))

        model.Minimize(self.starts_diff_sum)

        # self.add_previous_order_constraints_for_not_moved(model, demo_solver)

    def set_optimization_by_magnetic_striving(self, model: cp_model.CpModel,
                                              magnetic_constraints: Dict[UUID, MagneticConstraint]):
        differences_with_weight_sum = model.NewIntVar(0, self.factory.duration * len(self.factory.steps) * 10000,
                                                      'differences_with_weight_sum')
        all_differences_with_weight: [IntVar] = []

        for step_variable in self.all_stepVariables.values():
            magnetic_constraint = magnetic_constraints[step_variable.stepId]

            suffix = f'_step_{step_variable.stepId}'

            difference = model.NewIntVar(-self.factory.duration, self.factory.duration,
                                         'difference' + suffix)  # Задайте подходящие границы для разности

            # Создаем переменную для результата, которая будет равна разности или 0
            positive_difference = model.NewIntVar(0, self.factory.duration,
                                                  'positive_difference' + suffix)

            difference_with_weight = model.NewIntVar(0, self.factory.duration * 10000,
                                                     'difference_with_weight' + suffix)  # Задайте подходящие границы для результата

            # Вычисляем разность
            model.Add(difference == step_variable.start - magnetic_constraint.strivingPoint)
            model.AddAbsEquality(positive_difference, difference)
            model.add_multiplication_equality(difference_with_weight, [positive_difference, magnetic_constraint.weight])

            all_differences_with_weight.append(difference_with_weight)

        # Добавляем ограничение, что starts_sum должна быть равна сумме всех переменных из all_step_starts
        model.Add(differences_with_weight_sum == sum(all_differences_with_weight))
        model.Minimize(differences_with_weight_sum)

        # self.add_previous_order_constraints_for_not_moved(model, demo_solver)

    def demo_solve(self, model: cp_model.CpModel, time: int, stop_after_first_solution=False, type_solver: str = ""):
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 7  # Установка количества потоков

        solver.parameters.max_time_in_seconds = time
        solver.parameters.log_search_progress = True
        solver.parameters.search_branching = cp_model.PSEUDO_COST_SEARCH  # cp_model.HINT_SEARCH  #cp_model.LP_SEARCH #cp_model.HINT_SEARCH #cp_model.FIXED_SEARCH
        solver.parameters.stop_after_first_solution = stop_after_first_solution

        status = solver.Solve(model)
        logger.info(f'Решение {type_solver}:')
        logger.info(f'Статус  = {solver.StatusName(status)}')
        logger.info(f'Значение целевой функции: {solver.ObjectiveValue()}')
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            for important_var in self.important_vars:
                logger.info(f"Значение переменной {important_var.name}: {solver.Value(important_var)}")
        return solver, status

    def solve_optimal(self) -> ([ResolvedStep], str):
        demo_model = self.create_demo_model(self.factory_info_provider.maxSetup)
        self.set_optimization_objective_by_sum_starts(demo_model)

        demo_solver_without_setups, status_solver_without_setups = self.demo_solve(demo_model,
                                                                                   self.maxSearchTime * 2 // 3 + 1,
                                                                                   False,
                                                                                   "без переналадок")
        if not demo_solver_without_setups:
            return None, "Ошибка: demo_solver_without_setups не инициализирован"

        if not (status_solver_without_setups == cp_model.OPTIMAL or status_solver_without_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_without_setups)

        first_time_solver = demo_solver_without_setups.UserTime()
        model_after_setups = self.create_demo_model(need_machine_constraints=False)
        self.set_optimization_objective_by_sum_starts(model_after_setups)

        self.adjust_model_with_setups(model_after_setups, demo_solver_without_setups)

        solver_after_setups, status_solver_after_setups = self.demo_solve(model_after_setups,
                                                                          self.maxSearchTime // 3 + 1, False,
                                                                          "с переналадками")

        second_time_solver = solver_after_setups.UserTime()
        logger.info(f"Время на решение без переналадок: {first_time_solver}")
        logger.info(f"Время на решение с переналадками: {second_time_solver}")
        logger.info(f"Суммарное время: {first_time_solver + second_time_solver}")

        if not (status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_after_setups)

        self.last_solver_without_setups = demo_solver_without_setups
        self.last_solver_after_setups = solver_after_setups
        return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

    def solve_first(self) -> ([ResolvedStep], str):
        demo_model = self.create_demo_model(self.factory_info_provider.maxSetup)
        self.set_optimization_objective_by_sum_starts(demo_model)

        demo_solver_without_setups, status_solver_without_setups = self.demo_solve(demo_model,
                                                                                   self.maxSearchTime * 2 // 3 + 1,
                                                                                   True,
                                                                                   "без переналадок")
        if not demo_solver_without_setups:
            return None, "Ошибка: demo_solver_without_setups не инициализирован"

        # не важны положение степов потому что все равно без переналадок
        # важен только статус
        return None, self.translate_status(
            status_solver_without_setups)

    def solve_optimal_for_demands(self) -> ([ResolvedStep], str):
        demo_model = self.create_demo_model(self.factory_info_provider.maxSetup)
        self.set_optimization_objective_by_steps_closely_to_deadlines(demo_model)

        demo_solver_without_setups, status_solver_without_setups = self.demo_solve(demo_model,
                                                                                   self.maxSearchTime * 2 // 3 + 1,
                                                                                   False,
                                                                                   "без переналадок")
        if not demo_solver_without_setups:
            return None, "Ошибка: demo_solver_without_setups не инициализирован"

        if not (status_solver_without_setups == cp_model.OPTIMAL or status_solver_without_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_without_setups)

        first_time_solver = demo_solver_without_setups.UserTime()
        model_after_setups = self.create_demo_model(need_machine_constraints=False)
        self.set_optimization_objective_by_sum_starts(model_after_setups)

        self.adjust_model_with_setups(model_after_setups, demo_solver_without_setups)

        solver_after_setups, status_solver_after_setups = self.demo_solve(model_after_setups,
                                                                          self.maxSearchTime // 3 + 1, False,
                                                                          "с переналадками")

        second_time_solver = solver_after_setups.UserTime()
        logger.info(f"Время на решение без переналадок: {first_time_solver}")
        logger.info(f"Время на решение с переналадками: {second_time_solver}")
        logger.info(f"Суммарное время: {first_time_solver + second_time_solver}")

        if not (status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_after_setups)

        self.last_solver_without_setups = demo_solver_without_setups
        self.last_solver_after_setups = solver_after_setups
        return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

    def solve_for_moved_steps(self, movementType: MovementType) -> ([ResolvedStep], str):
        demo_solver_without_setups, solver_after_setups, status_solver_after_setups = self.solve_for_moved_steps_and_deviation(
            0)

        if status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE:
            self.last_solver_without_setups = demo_solver_without_setups
            self.last_solver_after_setups = solver_after_setups
            # for right_order in self.all_right_sequences_bool:
            #     print(demo_solver_without_setups.Value(right_order))
            for difference in self.all_differences:
                print(demo_solver_without_setups.Value(difference))
            return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

        demo_solver_without_setups, solver_after_setups, status_solver_after_setups = self.solve_for_moved_steps_and_deviation(
            60)

        if status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE:
            self.last_solver_without_setups = demo_solver_without_setups
            self.last_solver_after_setups = solver_after_setups
            return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

        demo_solver_without_setups, solver_after_setups, status_solver_after_setups = self.solve_for_moved_steps_and_deviation(
            600)

        if status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE:
            self.last_solver_without_setups = demo_solver_without_setups
            self.last_solver_after_setups = solver_after_setups
            return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

        return None, self.translate_status(status_solver_after_setups)

    def solve_for_moved_steps_and_deviation(self, max_deviation):
        demo_model = self.create_demo_model(self.factory.maxSetup)
        self.set_optimization_objective_by_abs_diff_starts(demo_model, self.last_solver_without_setups)

        self.add_moved_steps_constraints(demo_model, max_deviation)

        moved_solver_without_setups, status_solver_without_setups = self.demo_solve(demo_model,
                                                                                    self.maxSearchTime,
                                                                                    False,
                                                                                    "сдвиг без переналадок" + str(
                                                                                        max_deviation))
        if not (status_solver_without_setups == cp_model.OPTIMAL or status_solver_without_setups == cp_model.FEASIBLE):
            return moved_solver_without_setups, None, status_solver_without_setups

        first_time_solver = moved_solver_without_setups.UserTime()

        model_with_setups = self.create_demo_model(need_machine_constraints=False)

        self.set_optimization_objective_by_sum_starts(model_with_setups)

        self.add_moved_steps_constraints(model_with_setups, max_deviation)
        self.adjust_model_with_setups(model_with_setups, moved_solver_without_setups)

        solver_with_setups, status_solver_with_setups = self.demo_solve(model_with_setups,
                                                                        self.maxSearchTime, False,
                                                                        "сдвиг с переналадками" + str(max_deviation))

        second_time_solver = solver_with_setups.UserTime()
        logger.info(f"целевая переменная без переналадок: {moved_solver_without_setups.ObjectiveValue()}")
        logger.info(f"Время на решение без переналадок: {first_time_solver}")
        logger.info(f"Время на решение с переналадками: {second_time_solver}")
        logger.info(f"Суммарное время: {first_time_solver + second_time_solver}")
        return moved_solver_without_setups, solver_with_setups, status_solver_with_setups

    def adjust_solving_for_magnetic(self, resolved_steps_full: [ResolvedInterval],
                                    magnetic_constraints: Dict[UUID, MagneticConstraint], max_search_time) -> (
            [ResolvedStep], str):
        # print(resolved_steps_full)
        demo_model = self.create_demo_model()
        self.add_sequence_constraints(demo_model, resolved_steps_full)
        # self.add_magnetic_constraints(demo_model)
        # self.set_optimization_objective_by_sum_starts(demo_model)
        self.set_optimization_by_magnetic_striving(demo_model, magnetic_constraints)

        self.add_magnetic_constraints(demo_model, resolved_steps_full, magnetic_constraints)

        demo_solver_without_setups, status_solver_without_setups = self.demo_solve(demo_model,
                                                                                   self.maxSearchTime * 2 // 3 + 1,
                                                                                   False,
                                                                                   "без переналадок")
        if not demo_solver_without_setups:
            return None, "Ошибка: demo_solver_without_setups не инициализирован"

        if not (status_solver_without_setups == cp_model.OPTIMAL or status_solver_without_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_without_setups)

        first_time_solver = demo_solver_without_setups.UserTime()
        model_after_setups = self.create_demo_model(need_machine_constraints=False)
        self.set_optimization_by_magnetic_striving(model_after_setups, magnetic_constraints)
        # self.set_optimization_objective_by_sum_starts(model_after_setups)

        self.adjust_model_with_setups(model_after_setups, demo_solver_without_setups)
        self.add_magnetic_constraints(model_after_setups, resolved_steps_full, magnetic_constraints)

        solver_after_setups, status_solver_after_setups = self.demo_solve(model_after_setups,
                                                                          self.maxSearchTime // 3 + 1, False,
                                                                          "с переналадками")

        second_time_solver = solver_after_setups.UserTime()
        logger.info(f"Время на решение без переналадок: {first_time_solver}")
        logger.info(f"Время на решение с переналадками: {second_time_solver}")
        logger.info(f"Суммарное время: {first_time_solver + second_time_solver}")

        if not (status_solver_after_setups == cp_model.OPTIMAL or status_solver_after_setups == cp_model.FEASIBLE):
            return None, self.translate_status(status_solver_after_setups)

        self.last_solver_without_setups = demo_solver_without_setups
        self.last_solver_after_setups = solver_after_setups
        return self.create_resolved_steps(solver_after_setups), self.translate_status(status_solver_after_setups)

    def adjust_model_with_setups(self, model: cp_model.CpModel, demo_solver: CpSolver):
        self.all_setupVariables.clear()

        self.hint_model_by_solver(model, demo_solver)

        for machine_id in self.machine_to_stepVariables.keys():
            step_vars_in_machine = self.machine_to_stepVariables[machine_id]
            step_vars_in_machine.sort(key=lambda step_var: demo_solver.Value(step_var.start))

            # переналадка для первого степа в машине
            if len(step_vars_in_machine) >= 1:
                next_step_var = step_vars_in_machine[0]

                machine = self.factory.machines[machine_id]

                previous_step_operation_id = machine.operationIdBeforeActive
                next_step_operation_id = self.factory.steps[next_step_var.stepId].operationId

                if (previous_step_operation_id, next_step_operation_id) in self.factory.machinesSetup:
                    setup_duration = self.factory.machinesSetup[
                        (previous_step_operation_id, next_step_operation_id)].duration

                    suffix = f'first_setup_{next_step_var.stepId}'

                    start_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                                'start' + suffix)
                    end_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                              'end' + suffix)
                    interval_var = model.NewIntervalVar(start_var, setup_duration, end_var,
                                                        'interval' + suffix)

                    # ограничиваем переналадку между машиной и первым степом
                    model.Add(start_var >= machine.start)
                    model.Add(end_var == next_step_var.start)

                    self.all_setupVariables[next_step_var.stepId] = SetupVariable(next_step_var.stepId, setup_duration,
                                                                                  start_var, end_var, interval_var)

                    self.machine_to_intervals.setdefault(machine_id, []).append(interval_var)

            for i in range(len(step_vars_in_machine) - 1):
                previous_step_var = step_vars_in_machine[i]
                next_step_var = step_vars_in_machine[i + 1]
                # logging.info(f"previous_step_var {previous_step_var.stepId} next_step_var {next_step_var.stepId}")

                # фиксируем порядок подзадач внутри одного станка
                model.Add(previous_step_var.end <= next_step_var.start)

                previous_step_operation_id = self.factory.steps[previous_step_var.stepId].operationId
                next_step_operation_id = self.factory.steps[next_step_var.stepId].operationId

                if (previous_step_operation_id, next_step_operation_id) in self.factory.machinesSetup:
                    setup_duration = self.factory.machinesSetup[
                        (previous_step_operation_id, next_step_operation_id)].duration

                    suffix = f'setup_{previous_step_var.stepId}_{next_step_var.stepId}'

                    start_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                                'start' + suffix)
                    end_var = model.NewIntVar(self.factory.start, self.factory.start + self.factory.duration,
                                              'end' + suffix)
                    interval_var = model.NewIntervalVar(start_var, setup_duration, end_var,
                                                        'interval' + suffix)

                    # ограничиваем переналадку между двумя подзадачами
                    model.Add(start_var >= previous_step_var.end)
                    model.Add(end_var == next_step_var.start)

                    self.all_setupVariables[next_step_var.stepId] = SetupVariable(next_step_var.stepId, setup_duration,
                                                                                  start_var, end_var, interval_var)

                    self.machine_to_intervals.setdefault(machine_id, []).append(interval_var)

        self.add_machine_constraints(model)

    def hint_model_by_solver(self, model: cp_model.CpModel, solver: CpSolver):
        for step_variable in self.all_stepVariables.values():
            model.AddHint(step_variable.start,
                          solver.Value(step_variable.start))

    def hint_model_by_solver_and_moved_steps(self, model: cp_model.CpModel, solver: CpSolver):
        for step_variable in self.all_stepVariables.values():
            if self.is_moved(step_variable):
                model.AddHint(step_variable.start,
                              self.get_moved_step_new_start(step_variable))
            else:
                model.AddHint(step_variable.start,
                              solver.Value(step_variable.start))

    def create_resolved_steps(self, solver: CpSolver):

        resolved_steps = []
        for step_var in self.all_stepVariables.values():
            step = self.factory.steps[step_var.stepId]
            if step.type == StepType.TASK:
                entityType = EntityType.STEP
            else:
                entityType = EntityType.CAMPAIGN

            resolved_step = ResolvedStep(step_var.stepId, entityType, solver.Value(step_var.start),
                                         solver.Value(step_var.duration))
            if step_var.stepId in self.all_setupVariables.keys():
                resolved_step.setupDuration = self.all_setupVariables[step_var.stepId].duration
                resolved_step.setupStart = solver.Value(self.all_setupVariables[step_var.stepId].start)
            resolved_steps.append(resolved_step)
        return resolved_steps

    def translate_status(self, status):
        if status == cp_model.OPTIMAL:
            return "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            return "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            return "INFEASIBLE"
        elif status == cp_model.UNKNOWN:
            return "UNKNOWN"
        elif status == cp_model.MODEL_INVALID:
            return "MODEL_INVALID"
        else:
            return "UNDEFINED"

    def is_moved(self, step_var: StepVariable):
        return step_var.stepId in [step.stepId for step in self.movedSteps]

    # todo
    def get_moved_step_new_start(self, step_var: StepVariable):
        return self.movedSteps[0].newStart
