from typing import List
from uuid import UUID

from Model.Factory import Factory
from Model.SlowPeriod import SlowPeriod

# идея фэйкого времени что там сохраняется длительность интервала
# в фэйовом времени интервалы замедляния выглядят сжатыми

class FakeTimeConverter:
    def __init__(self, factory: Factory):
        self.factory = factory
        self.machine_to_slow_periods = self._create_machine_to_slow_periods()
        self.machine_to_fake_slow_periods = self._create_machine_to_fake_slow_periods()

    def _create_machine_to_slow_periods(self):
        machine_to_slow_periods = {}
        for slow_period in self.factory.slowPeriods:
            machine_to_slow_periods.setdefault(slow_period.machineId, []).append(slow_period)

        for machine_id in machine_to_slow_periods:
            machine_to_slow_periods[machine_id] = sorted(machine_to_slow_periods[machine_id], key=lambda x: x.start)

        return machine_to_slow_periods

    def _create_machine_to_fake_slow_periods(self):
        """
        Создает словарь замедленных периодов с учетом фейкового времени.
        Начало и конец рассчитываются на основе перевода реального времени в фейковое,
        а коэффициент является обратным к исходному.

        Возвращает:
            dict: Словарь, где ключ - ID машины, а значение - список пересчитанных периодов.
        """

        machine_to_fake_slow_periods = {}

        for machine_id, periods in self.machine_to_slow_periods.items():
            fake_slow_periods = []

            # Преобразуем реальные значения в фейковые с использованием ранее написанной функции
            for period in periods:
                fake_start = self._convert_real_time_to_fake_time(period.start, periods)
                fake_end = self._convert_real_time_to_fake_time(period.start + period.duration, periods)

                # Продолжительность в фейковом времени
                fake_duration = fake_end - fake_start

                # Инвертируем коэффициент замедления
                fake_coefficient = 1 / period.coefficient if period.coefficient > 0 else 1

                fake_slow_periods.append(
                    SlowPeriod(
                        slowPeriodId=period.slowPeriodId,
                        machineId=period.machineId,
                        start=fake_start,
                        duration=fake_duration,
                        coefficient=fake_coefficient
                    )
                )

            machine_to_fake_slow_periods[machine_id] = fake_slow_periods

        return machine_to_fake_slow_periods

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


    def convert_fake_time_to_real_time(self, fake_time: float, machine_id: UUID) -> float:
        fake_slow_periods = self.machine_to_fake_slow_periods.get(machine_id, [])
        return self._convert_real_time_to_fake_time(fake_time, fake_slow_periods)


    def convert_real_time_to_fake_time(self, real_time: float, machine_id: UUID) -> float:
        slow_periods = self.machine_to_slow_periods.get(machine_id, [])
        return self._convert_real_time_to_fake_time(real_time, slow_periods)

    def count_real_duration_by_start(self, real_start: float, fake_duration: float, machine_id: UUID) -> float:
        fake_start = self.convert_real_time_to_fake_time(real_start, machine_id)
        fake_end = fake_start + fake_duration
        real_end = self.convert_fake_time_to_real_time(fake_end, machine_id)
        real_duration = real_end - real_start
        return real_duration


    def count_real_duration_by_end(self, real_end: float, fake_duration: float, machine_id: UUID) -> float:
        fake_end = self.convert_real_time_to_fake_time(real_end, machine_id)
        fake_start = fake_end - fake_duration
        real_start = self.convert_fake_time_to_real_time(fake_start, machine_id)
        real_duration = real_end - real_start
        return real_duration


    def count_real_start_by_end(self, real_end: float, fake_duration: float, machine_id: UUID) -> float:
        real_duration = self.count_real_duration_by_end(real_end, fake_duration, machine_id)
        real_start = real_end - real_duration
        return real_start


    def count_real_end_by_start(self, real_start: float, fake_duration: float, machine_id: UUID) -> float:
        real_duration = self.count_real_duration_by_start(real_start, fake_duration, machine_id)
        real_end = real_start + real_duration
        return real_end

    def count_fake_duration_by_start_and_end(self, real_start: float, real_end: float, machine_id: UUID) -> float:
        fake_start = self.convert_real_time_to_fake_time(real_start, machine_id)
        fake_end = self.convert_real_time_to_fake_time(real_end, machine_id)
        fake_duration = fake_end - fake_start
        return fake_duration





