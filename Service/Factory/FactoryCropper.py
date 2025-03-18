from uuid import UUID

from Model.Factory import Factory


class FactoryCropper:
    def crop(self, factory: Factory, machines_id: [UUID]):
        new_steps = {step.stepId: step for step in factory.steps.values() if step.machineId in machines_id}
        new_stepsOrder_without_campaigns = {
            (previousStepId, nextStepId): factory.stepsOrderWithoutCampaigns[previousStepId, nextStepId]
            for (previousStepId, nextStepId) in factory.stepsOrderWithoutCampaigns.keys()
            if previousStepId in new_steps and nextStepId in new_steps
        }
        new_fixed_steps = [step for step in factory.fixedSteps if step.stepId in new_steps]

        return Factory(new_steps, factory.machinesSetup, new_stepsOrder_without_campaigns, factory.machines, new_fixed_steps,
                       factory.idlePeriods, factory.slowPeriods, factory.task_machine_to_campaign_machine, factory.importantDemands,
                       factory.notOverlappingStepsPairs)

