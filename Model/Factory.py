import logging
from collections import defaultdict
from copy import copy
from typing import List, Dict, Tuple, Set
from uuid import UUID

from Model.IdlePeriod import IdlePeriod
from Model.Machine import Machine
from Model.MachineSetup import MachineSetup
from Model.NotOverlappingStepsPair import NotOverlappingStepsPair
from Model.SlowPeriod import SlowPeriod
from Model.Step import Step
from Model.StepOrder import StepOrder
from Model.Demand import Demand
from Model.StepOrderType import StepOrderType
from Model.StepType import StepType

logging.basicConfig(level=logging.INFO,  # Уровень логирования
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат логов
                    handlers=[
                        logging.FileHandler("../../info_log.log"),  # Запись логов в файл
                        logging.StreamHandler()  # Одновременный вывод на консоль
                    ])


class Factory:
    def __init__(self,
                 steps: Dict[UUID, Step],
                 machinesSetup: Dict[Tuple[UUID, UUID], MachineSetup],
                 stepsOrderWithoutCampaigns: Dict[Tuple[UUID, UUID], List[StepOrder]],
                 machines: Dict[UUID, Machine],
                 fixedSteps: List[Step],
                 idlePeriods: List[IdlePeriod],
                 slowPeriods: List[SlowPeriod],
                 task_machine_to_campaign_machine: Dict[UUID, UUID],
                 demands: Dict[UUID, Demand],
                 notOverlappingStepsPairs: List[NotOverlappingStepsPair]):

        logging.info("Creating factory")

        self.duration = 100_000_000
        self.steps = steps
        self.task_machine_to_campaign_machine = task_machine_to_campaign_machine
        self.taskSteps = self.create_task_steps()
        self.compaignSteps = self.create_campaign_steps()

        self.machinesSetup = machinesSetup
        self.stepsOrderWithoutCampaigns = stepsOrderWithoutCampaigns
        self.stepsOrder = self.create_steps_order_with_campaigns()
        self.machines = machines
        self.fixedSteps = fixedSteps
        self.idlePeriods = idlePeriods
        self.slowPeriods = slowPeriods




        self.notOverlappingStepsPairs = notOverlappingStepsPairs
        self.start = self.define_start()
        self.importantDemands = demands
        self.demands = self.create_all_demands(demands, steps, self.start + self.duration)


        logging.info("Factory created")









    def create_all_demands(self, part_of_demands, steps, default_due_date):
        all_demands = copy(part_of_demands)
        for step in steps.values():
            if step.demandId not in all_demands:
                all_demands[step.demandId] = Demand(step.demandId, default_due_date)
        return all_demands



    def define_start(self):
        return min([machine.start for machine in self.machines.values()])



    def create_steps_order_with_campaigns(self):
        steps_order = defaultdict(list, copy(self.stepsOrderWithoutCampaigns))
        for step in self.taskSteps.values():
            if step.campaignId:
                left_step_order = StepOrder(step.campaignId, step.stepId, 0, self.duration, StepOrderType.RUN_RUN)
                steps_order[step.campaignId, step.stepId].append(left_step_order)
                right_step_order = StepOrder(step.stepId, step.campaignId, 0, self.duration, StepOrderType.END_END)
                steps_order[step.stepId, step.campaignId].append(right_step_order)
        return steps_order


    def create_task_steps(self):
        task_steps = {step.stepId: step for step in self.steps.values() if step.type == StepType.TASK}
        return task_steps

    def create_campaign_steps(self):
        campaign_steps = {step.stepId: step for step in self.steps.values() if step.type == StepType.CAMPAIGN}
        return campaign_steps


