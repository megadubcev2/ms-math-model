# идея фэйкого времени что там сохраняется длительность интервала
# в фэйовом времени интервалы замедляния выглядят сжатыми
from typing import Dict, List
from uuid import UUID

from Model.Factory import Factory
from Model.SlowPeriod import SlowPeriod


class SlowPeriodRepository:
    def __init__(self, factory: Factory):
        self.factory = factory
        self.machine_to_slow_periods: Dict[UUID, List[SlowPeriod]] = self._create_machine_to_slow_periods()
        self.fake_slow_periods: Dict[UUID, SlowPeriod] = self._create_fake_slow_periods()

    def _create_machine_to_slow_periods(self):
        machine_to_slow_periods = {}

        for machine_id in self.factory.machines:
            machine_to_slow_periods[machine_id] = []

        for slow_period in self.factory.slowPeriods:
            machine_to_slow_periods.setdefault(slow_period.machineId, []).append(slow_period)

        for machine_id in machine_to_slow_periods:
            machine_to_slow_periods[machine_id] = sorted(machine_to_slow_periods[machine_id], key=lambda x: x.start)

        return machine_to_slow_periods

    def _create_fake_slow_periods(self):
        """
        Создает словарь замедленных периодов с учетом фейкового времени.
        Начало и конец рассчитываются на основе перевода реального времени в фейковое,
        а коэффициент является обратным к исходному.

        Возвращает:
            dict: Словарь, где ключ - ID машины, а значение - список пересчитанных периодов.
        """

        fake_slow_periods = {}

        for slow_period in self.factory.slowPeriods:
            machine_id = slow_period.machineId
            fake_start = self._convert_real_time_to_fake_time(slow_period.start,
                                                              self.machine_to_slow_periods[machine_id])
            fake_end = self._convert_real_time_to_fake_time(slow_period.start + slow_period.duration,
                                                            self.machine_to_slow_periods[machine_id])

            # Продолжительность в фейковом времени
            fake_duration = fake_end - fake_start

            # Инвертируем коэффициент замедления
            fake_coefficient = 1 / slow_period.coefficient if slow_period.coefficient > 0 else 1

            fake_slow_periods[slow_period.slowPeriodId] = (
                SlowPeriod(
                    slowPeriodId=slow_period.slowPeriodId,
                    machineId=slow_period.machineId,
                    start=fake_start,
                    duration=fake_duration,
                    coefficient=fake_coefficient
                )
            )

        return fake_slow_periods

    def _convert_real_time_to_fake_time(self, real_time: float, slow_periods: List[SlowPeriod]) -> float:

        # Если нет замедленных периодов, вернуть реальное время без изменений
        if not slow_periods:
            return real_time

        fake_time = 0
        normal_time_accumulated = 0  # Отслеживает сумму прошедшего "нормального" времени без замедлений

        for i, period in enumerate(slow_periods):
            if real_time < period.start:
                # Если реальное время меньше начала текущего замедленного периода
                fake_time += real_time - normal_time_accumulated
                return fake_time

            # Добавляем нормальное время до начала замедленного периода
            fake_time += period.start - normal_time_accumulated

            # Рассчитываем время внутри замедленного периода
            if real_time < period.start + period.duration:
                fake_time += (real_time - period.start) * period.coefficient
                return fake_time

            # Если период полностью пройден, учитываем его эффект
            fake_time += period.duration * period.coefficient
            normal_time_accumulated = period.start + period.duration

        # Если реальное время после последнего замедленного периода
        fake_time += real_time - normal_time_accumulated
        return fake_time
