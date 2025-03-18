from uuid import UUID
from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import BoolVarT

from Model.SlowPeriod import SlowPeriod
from Service.ScheduleSolver.OptimalAlgorithm.Model.SetupVariable import SetupVariable
from Service.ScheduleSolver.OptimalAlgorithm.Model.StepVariable import StepVariable


class SlowPeriodIndicator:
    slowPeriodId: UUID
    intervalId: UUID
    is_more_start_than_slow_start: BoolVarT
    is_more_end_than_slow_start: BoolVarT
    is_more_start_than_slow_end: BoolVarT
    is_more_end_than_slow_end: BoolVarT

    def __init__(self, model: cp_model.CpModel, variable, slow_period: SlowPeriod, type: str):
        """
        Аргумент `variable` может быть либо объектом StepVariable, либо SetupVariable.
        Внутри конструктора определяется нужная логика на основе типа переменной.
        """
        self.slowPeriodId = slow_period.slowPeriodId

        # Определяем, с каким типом работаем, и получаем нужные атрибуты
        if isinstance(variable, StepVariable):
            self.intervalId = variable.stepId
            start = variable.start
            end = variable.end
        elif isinstance(variable, SetupVariable):
            self.intervalId = variable.beforeStepId
            start = variable.start
            end = variable.end
        else:
            raise ValueError("Неверный тип переменной. Ожидается StepVariable или SetupVariable.")

        suffix = f"_{type}_{self.intervalId}_{self.slowPeriodId}"
        self.is_more_start_than_slow_start = model.NewBoolVar("is_more_start_than_slow_start" + suffix)
        self.is_more_end_than_slow_start = model.NewBoolVar("is_more_end_than_slow_start" + suffix)
        self.is_more_start_than_slow_end = model.NewBoolVar("is_more_start_than_slow_end" + suffix)
        self.is_more_end_than_slow_end = model.NewBoolVar("is_more_end_than_slow_end" + suffix)

        model.Add(start > int(slow_period.start)).OnlyEnforceIf(
            self.is_more_start_than_slow_start)
        model.Add(start <= int(slow_period.start)).OnlyEnforceIf(self.is_more_start_than_slow_start.Not())

        model.Add(
            end > int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
            self.is_more_end_than_slow_end)
        model.Add(
            end <= int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
            self.is_more_end_than_slow_end.Not())

        model.Add(
            start > int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
            self.is_more_start_than_slow_end)
        model.Add(start <= int(slow_period.start + slow_period.duration)).OnlyEnforceIf(
            self.is_more_start_than_slow_end.Not())

        model.Add(end > int(slow_period.start)).OnlyEnforceIf(
            self.is_more_end_than_slow_start)
        model.Add(end <= int(slow_period.start)).OnlyEnforceIf(
            self.is_more_end_than_slow_start.Not())
