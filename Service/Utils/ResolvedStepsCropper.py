from Model.Factory import Factory
from Model.ResolvedStep import ResolvedStep
from Service.Factory.FactoryInfoProvider import FactoryInfoProvider


class ResolvedStepsCropper:
    def leave_only_changed_steps(self, ResolvedSteps: [ResolvedStep], factory_info_provider: FactoryInfoProvider):
        changed_steps = []
        for resolved_step in ResolvedSteps:
            if self.is_changed(resolved_step, factory_info_provider):
                changed_steps.append(resolved_step)

        return changed_steps

    def is_changed(self, resolved_step: [ResolvedStep], factory_info_provider: FactoryInfoProvider):
        if resolved_step.stepId in factory_info_provider.moved_steps:
            return True
        step = factory_info_provider.factory.steps[resolved_step.stepId]
        if resolved_step.setupStart is None:
            resolved_step_setup_start = resolved_step.start
        else:
            resolved_step_setup_start = resolved_step.setupStart

        if resolved_step.setupDuration is None:
            resolved_step_setup_duration = 0
        else:
            resolved_step_setup_duration = resolved_step.setupDuration


        if step.start == resolved_step.start \
                and step.duration == resolved_step.duration \
                and step.setupStart == resolved_step_setup_start \
                and step.setupDuration == resolved_step_setup_duration:
            return False
        return True
