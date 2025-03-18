from uuid import UUID
import uuid
from collections import defaultdict

from Model.Campaign import Campaign
from Model.Demand import Demand
from Model.Factory import Factory
from Model.IdlePeriod import IdlePeriod
from Model.Machine import Machine
from Model.MachineType import MachineType
from Model.MovedStep import MovedStep
from Model.MovementType import MovementType
from Model.NotOverlappingStepsPair import NotOverlappingStepsPair
from Model.SlowPeriod import SlowPeriod
from Model.Step import Step
from Model.MachineSetup import MachineSetup
from Model.StepOrder import StepOrder
from Model.StepOrderType import StepOrderType
from Model.StepType import StepType
from Controller.DTO.OptimizationResponseDto import OptimizationResponseDto

from Controller.DTO.ResolvedStepDto import ResolvedStepDto


class ParserDTO:

    def parse_to_Demand(self, demandDto):
        return Demand(demandDto.demandId, demandDto.dueDate)

    def parse_to_IdlePeriod(self, idlePeriodDto):
        return IdlePeriod(idlePeriodDto.idlePeriodId, idlePeriodDto.machineId,
                          idlePeriodDto.start, idlePeriodDto.duration)
    def parse_to_SlowPeriod(self, slowPeriodDto):
        return SlowPeriod(slowPeriodDto.slowPeriodId, slowPeriodDto.machineId,
                          slowPeriodDto.start, slowPeriodDto.end - slowPeriodDto.start, float(slowPeriodDto.coefficient))

    def parse_to_MovedStep(self, movedStepDto):
        return MovedStep(movedStepDto.stepId, movedStepDto.newStart)

    def parse_to_TaskStep(self, stepDto):
        return Step(
            stepId=stepDto.stepId,
            machineId=stepDto.machineId,
            start=stepDto.start,
            duration=stepDto.duration,
            initialDuration=stepDto.initialDuration,
            fixed=stepDto.fixed,
            operationId=stepDto.operationId,
            type=StepType.TASK,
            demandId=stepDto.demandId,
            campaignId=stepDto.campaignId
        )

    def parse_to_CampaignStep(self, campaignDto, step_machine_to_campaign_machine):
        return Step(
            stepId=campaignDto.campaignId,
            machineId=step_machine_to_campaign_machine[campaignDto.machineId],
            start=campaignDto.start,
            duration=campaignDto.duration,
            initialDuration=campaignDto.duration,
            fixed=campaignDto.fixed,
            operationId=campaignDto.operationId,
            type=StepType.CAMPAIGN,
            demandId=uuid.uuid4(),
            campaignId=None
        )

    def parse_to_MachineSetup(self, machineSetupDto):
        return MachineSetup(
            fromOperationId=machineSetupDto.fromOperationId,
            toOperationId=machineSetupDto.toOperationId,
            duration=machineSetupDto.duration
        )

    def parse_to_StepOrder(self, stepOrderDto):
        # Пытаемся получить тип шага из строки, если она корректная, иначе используем значение по умолчанию
        stepOrderType = StepOrderType[
            stepOrderDto.stepOrderType] if stepOrderDto.stepOrderType and stepOrderDto.stepOrderType in StepOrderType.__members__ else StepOrderType.END_RUN

        return StepOrder(
            previousStepId=stepOrderDto.previousStepId,
            nextStepId=stepOrderDto.nextStepId,
            overlapMin=stepOrderDto.overlapMin,
            overlapMax=stepOrderDto.overlapMax,
            stepOrderType=stepOrderType
        )

    def parse_to_Machine(self, machineDto, machineType: MachineType):
        if machineDto.operationIdBeforeActive is None:
            machineDto.operationIdBeforeActive = uuid.uuid4()
        return Machine(machineDto.machineId, machineDto.start, machineDto.operationIdBeforeActive, machineType)

    def parse_to_NotOverlappingStepsPair(self, notOverlappingStepsPairDto):
        return NotOverlappingStepsPair(
            notOverlappingStepsPairDto.firstStepId,
            notOverlappingStepsPairDto.secondStepId
        )

    def parse_to_Factory(self, FactoryDto):
        taskSteps = {step.stepId: self.parse_to_TaskStep(step) for step in FactoryDto.steps}

        machines = {machine.machineId: self.parse_to_Machine(machine, machineType=MachineType.TASK_MACHINE) for machine
                    in FactoryDto.machines}

        task_machine_to_campaign_machine = {}
        for machine in machines.values():
            task_machine_to_campaign_machine[machine.machineId] = uuid.uuid4()

        for task_machine_id,  campaign_machine_id in task_machine_to_campaign_machine.items():
            task_machine = machines[task_machine_id]
            campaign_machine = Machine(campaign_machine_id, task_machine.start, uuid.uuid4(), MachineType.CAMPAIGN_MACHINE)
            machines[campaign_machine_id] = campaign_machine

        campaignSteps = {campaign.campaignId: self.parse_to_CampaignStep(campaign, task_machine_to_campaign_machine)
                          for campaign in FactoryDto.campaigns}

        steps = taskSteps | campaignSteps

        machinesSetup = {
            (machineSetup.fromOperationId, machineSetup.toOperationId): self.parse_to_MachineSetup(machineSetup) for
            machineSetup in FactoryDto.machinesSetup}

        stepsOrder = defaultdict(list)  # Используем set для хранения уникальных значений

        for stepOrderDto in FactoryDto.stepsOrder:
            key = (stepOrderDto.previousStepId, stepOrderDto.nextStepId)
            stepsOrder[key].append(self.parse_to_StepOrder(stepOrderDto))


        idlePeriods = [self.parse_to_IdlePeriod(idle_period_dto) for idle_period_dto in FactoryDto.idlePeriods]

        slowPeriods = [self.parse_to_SlowPeriod(slow_period_dto) for slow_period_dto in FactoryDto.slowPeriods]



        demands = {demand.demandId: self.parse_to_Demand(demand) for demand in FactoryDto.demands}

        fixedSteps = [steps[stepId] for stepId in steps if steps[stepId].fixed == True]

        notOverlappingStepsPairs = FactoryDto.notOverlappingStepsPairs

        return Factory(
            steps=steps,
            machinesSetup=machinesSetup,
            stepsOrderWithoutCampaigns=stepsOrder,
            machines=machines,
            fixedSteps=fixedSteps,
            idlePeriods=idlePeriods,
            slowPeriods=slowPeriods,
            demands=demands,
            task_machine_to_campaign_machine=task_machine_to_campaign_machine,
            notOverlappingStepsPairs=notOverlappingStepsPairs
        )

    def parse_Optimization_Request_Dto(self, optimizationRequestDto):

        factory = self.parse_to_Factory(optimizationRequestDto.factory)
        maxSearchTime = optimizationRequestDto.maxSearchTime

        return factory, maxSearchTime

    def parse_Movement_Request_Dto(self, MovementRequestDto):
        movedSteps = {moved_step_dto.stepId: self.parse_to_MovedStep(moved_step_dto) for moved_step_dto in
                      MovementRequestDto.movedSteps}

        factory = self.parse_to_Factory(MovementRequestDto.factory)
        maxSearchTime = MovementRequestDto.maxSearchTime
        movementType = MovementType[MovementRequestDto.movementType]

        for movedStep in movedSteps.values():
            factory.steps[movedStep.stepId].start = movedStep.newStart

        return factory, maxSearchTime, movedSteps, movementType

    def parse_Sorting_Request_Dto(self, SortingRequestDto):

        factory = self.parse_to_Factory(SortingRequestDto.factory)
        maxSearchTime = SortingRequestDto.maxSearchTime

        return factory, maxSearchTime, SortingRequestDto.sortedSteps

    def parse_to_ResolvedStepDto(self, resolvedStep):
        return ResolvedStepDto(
            stepId=resolvedStep.intervalId,
            start=resolvedStep.start,
            setupStart=resolvedStep.setupStart,
            setupDuration=resolvedStep.setupDuration
        )

    def parse_to_OptimizationResponseDto(self, resolvedSteps):
        resolvedStepsDto = [self.parse_to_ResolvedStepDto(resolvedStep) for resolvedStep in resolvedSteps]
        return OptimizationResponseDto(
            resolvedStepsDto=resolvedStepsDto
        )
