from Model.Factory import Factory
from Model.ResolvedStep import ResolvedStep
from Model.Step import Step

import copy


class FactoryCreator:
    def create(self, old_factory: Factory, resolved_steps: [ResolvedStep]):
        new_steps = {step.stepId: copy.copy(step) for step in old_factory.steps.values()}
        for resolved_step in resolved_steps:
            new_steps[resolved_step.stepId].start = resolved_step.start

        return Factory(new_steps, old_factory.machinesSetup, old_factory.stepsOrderWithoutCampaigns,
                       old_factory.machines,
                       old_factory.fixedSteps, old_factory.idlePeriods, old_factory.slowPeriods,  old_factory.task_machine_to_campaign_machine,
                       old_factory.importantDemands, old_factory.notOverlappingStepsPairs)
