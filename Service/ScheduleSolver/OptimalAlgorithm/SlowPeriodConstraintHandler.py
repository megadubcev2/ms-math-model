from typing import Dict
from uuid import UUID

from ortools.constraint_solver.pywrapcp import IntVar
from ortools.sat.python import cp_model

from Model.Factory import Factory
from Service.ScheduleSolver.OptimalAlgorithm.Model.SlowPeriodIndicator import SlowPeriodIndicator
from Service.ScheduleSolver.OptimalAlgorithm.Model.StepVariable import StepVariable
from Service.ScheduleSolver.OptimalAlgorithm.SlowPeriodRepository import SlowPeriodRepository


class SlowPeriodConstraintHandler:
    def __init__(self, factory: Factory):
        self.SCALE_FACTOR = 1000
        self.slow_period_repository = SlowPeriodRepository(factory)
        self.factory = factory
        self.important_vars = []


    def add_slow_period_constraints(self, model: cp_model.CpModel, all_stepVariables: Dict[UUID, StepVariable],
                                    all_fake_stepVariables: Dict[UUID, StepVariable]):

        self.important_vars = []


        for step in self.factory.steps.values():
            step_var = all_stepVariables[step.stepId]
            fake_step_var = all_fake_stepVariables[step.stepId]
            machine_id = step.machineId
            self.add_constraint_fake_var(model, step_var.start, fake_step_var.start, machine_id,
                                         f"step_start_{step.stepId}")
            self.add_constraint_fake_var(model, step_var.end, fake_step_var.end, machine_id, f"step_end_{step.stepId}")

        return self.important_vars

    def add_constraint_fake_var(self, model: cp_model.CpModel, real_var: IntVar, fake_var: IntVar, machine_id: UUID,
                                name: str):
        if len(self.slow_period_repository.machine_to_slow_periods[machine_id]) > 0:
            all_scaled_elements = []
            self.important_vars.append(real_var)

            self.important_vars.append(fake_var)

            for slow_period in self.slow_period_repository.machine_to_slow_periods[machine_id]:
                suffix = f'_{name}_{slow_period.slowPeriodId}'

                is_more_than_slow_start = model.NewBoolVar("is_more_than_slow_start" + suffix)
                self.important_vars.append(is_more_than_slow_start)

                is_more_than_slow_end = model.NewBoolVar("is_more_than_slow_end" + suffix)
                self.important_vars.append(is_more_than_slow_end)

                model.Add(real_var > int(slow_period.start)).OnlyEnforceIf(
                    is_more_than_slow_start)
                model.Add(real_var <= int(slow_period.start)).OnlyEnforceIf(is_more_than_slow_start.Not())

                model.Add(real_var > int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
                    is_more_than_slow_end)
                model.Add(real_var <= int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
                    is_more_than_slow_end.Not())

                # is_more_than_last_end = is_more_than_slow_end

                scaled_element = model.NewIntVar(-self.factory.duration * self.SCALE_FACTOR,
                                                 self.factory.duration * self.SCALE_FACTOR,
                                                 "scaled_element" + suffix)
                self.important_vars.append(scaled_element)

                scaled_slow_coefficient = int(round(self.SCALE_FACTOR * slow_period.coefficient))
                scaled_neutral_coefficient = self.SCALE_FACTOR

                relative_to_start = model.NewIntVar(-self.factory.duration,
                                                    self.factory.duration,
                                                    "relative_to_start" + suffix)
                self.important_vars.append(relative_to_start)

                relative_to_end = model.NewIntVar(-self.factory.duration,
                                                  self.factory.duration,
                                                  "relative_to_end" + suffix)


                model.Add(relative_to_start == (real_var - int(round(slow_period.start))))
                model.Add(relative_to_end == (real_var - int(round(slow_period.start + slow_period.duration))))

                # Определяем вспомогательную переменную для произведения
                term_start = model.NewIntVar(-self.factory.duration * self.SCALE_FACTOR,
                                             self.factory.duration * self.SCALE_FACTOR, "term_start" + suffix)

                self.important_vars.append(term_start)

                # Если is_more_than_slow_start истинна, term_start равно произведению
                model.Add(term_start == relative_to_start * (scaled_slow_coefficient - scaled_neutral_coefficient)) \
                    .OnlyEnforceIf(is_more_than_slow_start)

                # Если is_more_than_slow_start ложна, term_start равна 0
                model.Add(term_start == 0).OnlyEnforceIf(is_more_than_slow_start.Not())

                term_end = model.NewIntVar(-self.factory.duration * self.SCALE_FACTOR,
                                             self.factory.duration * self.SCALE_FACTOR, "term_end" + suffix)
                self.important_vars.append(term_end)


                model.Add(term_end == relative_to_end * (scaled_neutral_coefficient - scaled_slow_coefficient)) \
                    .OnlyEnforceIf(is_more_than_slow_end)
                model.Add(term_end == 0).OnlyEnforceIf(is_more_than_slow_end.Not())

                model.Add(scaled_element == term_start + term_end)

                all_scaled_elements.append(scaled_element)


            scaled_fake_var = model.NewIntVar((self.factory.start - self.factory.duration) * self.SCALE_FACTOR,
                                              (self.factory.start + self.factory.duration) * self.SCALE_FACTOR, f"scaled_fake_var_{name}")

            self.important_vars.append(scaled_fake_var)
            model.Add(
                scaled_fake_var == self.SCALE_FACTOR * real_var + sum(all_scaled_elements))

            model.Add(fake_var * self.SCALE_FACTOR <= scaled_fake_var)
            model.Add((fake_var + 1) * self.SCALE_FACTOR > scaled_fake_var)
            # model.AddDivisionEquality(fake_var - 1, scaled_fake_var, self.SCALE_FACTOR)



        else:
            model.Add(real_var == fake_var)
