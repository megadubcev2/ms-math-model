import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from Model.IntervalType import IntervalType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ReslovedMachineSetup import ResolvedMachineSetup

# Настройка логирования
logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])

@dataclass
class ResolvedInterval:
    intervalId: UUID
    machineId: UUID
    start: int
    end: int
    duration: int
    fixed: bool
    type: IntervalType
    isMoved: bool
    operationId: Optional[UUID] = None
    machineSetup: Optional[ResolvedMachineSetup] = None

    def log_state(self, message: str):
        #logging.info(f"{message}: {self.__dict__}")
        pass

    def log_state2(self, message: str):
        logging.info(f"{message}: {self.__dict__}")



    def _update_machine_setup(self):
        self.log_state(f"Updating machine setup for interval {self.intervalId}")
        if self.machineSetup:
            self.machineSetup.move_end(self.start)
        self.log_state(f"Machine setup updated for interval {self.intervalId}")

    def move_start(self, new_start: int):
        self.log_state(f"Moving start of interval {self.intervalId} from {self.start} to {new_start}")
        self.start = new_start
        self.end = self.start + self.duration
        self._update_machine_setup()
        self.log_state(f"Start moved for interval {self.intervalId}")

    def move_start_and_end(self, new_start: int, new_end: int):
        self.log_state(f"Moving start and end of interval {self.intervalId} from start: {self.start}, end: {self.end} "
                     f"to new start: {new_start}, new end: {new_end}")
        self.start = new_start
        self.end = new_end
        self.duration = new_end - new_start
        self._update_machine_setup()
        self.log_state(f"Start and end moved for interval {self.intervalId}")

    def move_setup_start(self, new_setup_start: int):
        self.log_state(f"Moving setup start of interval {self.intervalId} from {self.get_setup_start()} "
                     f"to new setup start: {new_setup_start}")
        self.move_start(new_setup_start + self.get_setup_duration())
        self.log_state(f"Setup start moved for interval {self.intervalId}")

    def move_end(self, new_end: int):
        self.log_state(f"Moving end of interval {self.intervalId} from {self.end} to {new_end}")
        self.end = new_end
        self.start = self.end - self.duration
        self._update_machine_setup()
        self.log_state(f"End moved for interval {self.intervalId}")

    def changeDuration(self, new_duration: int):
        self.log_state(f"Changing duration of interval {self.intervalId} from {self.duration} to {new_duration}")
        self.duration = new_duration
        self.end = self.start + self.duration
        self._update_machine_setup()
        self.log_state(f"Duration changed for interval {self.intervalId}")


    def changeSetupDuration(self, new_duration: int)-> bool:
        """
        возвращает True если длительность изменилась
        """
        self.log_state(f"Changing setup duration for interval {self.intervalId} to {new_duration}")
        if not self.machineSetup:
            self.machineSetup = ResolvedMachineSetup(self.start, self.duration)
            self.log_state(f"Setup duration changed for interval {self.intervalId}")
            return True
        else:
            previous_duration = self.machineSetup.setupDuration
            self.machineSetup.changeDuration(new_duration)
            self.log_state(f"Setup duration changed for interval {self.intervalId}")
            return previous_duration != new_duration


    def get_setup_start(self):
        #self.log_state(f"Getting setup start for interval {self.intervalId}")
        if not self.machineSetup:
            return self.start
        return self.machineSetup.setupStart

    def get_setup_duration(self):
        #self.log_state(f"Getting setup duration for interval {self.intervalId}")
        if not self.machineSetup:
            return 0
        return self.machineSetup.setupDuration
