from math import sqrt

from Model.Factory import Factory
from Model.ResolvedStep import ResolvedStep
from Service.Factory.FactoryInfoProvider import FactoryInfoProvider


class ResolvedStepsEvaluator:
    def evaluate(self, ResolvedSteps: [ResolvedStep], factory_info_provider: FactoryInfoProvider) -> float:
        if ResolvedSteps is None:
            return 100000000000000

        result_evaluation = 0
        factory = factory_info_provider.factory
        resolved_steps_dict = {}
        for resolved_step in ResolvedSteps:
            resolved_steps_dict[resolved_step.stepId] = resolved_step

        for machine_id in factory.machines.keys():
            weighted_inversions_sum = 0
            offset_sum = 0
            resolved_step_to_number = {}
            step_to_number = {}
            steps_on_machine = [step for step in factory.steps.values() if step.machineId == machine_id]
            if len(steps_on_machine) == 0:
                continue

            steps_on_machine.sort(key=lambda x: x.start)
            resolved_steps_on_machine = [resolved_steps_dict[step.stepId] for step in steps_on_machine]
            resolved_steps_on_machine.sort(key=lambda x: x.start)

            for i, step in enumerate(steps_on_machine):
                step_to_number[step.stepId] = i

            for i, resolved_step in enumerate(resolved_steps_on_machine):
                resolved_step_to_number[resolved_step.stepId] = i
                offset_sum += abs(i - step_to_number[resolved_step.stepId])

            average_offset = offset_sum / len(steps_on_machine)

            result_evaluation += average_offset

            for i in range(len(steps_on_machine) - 1):
                first_step_id = steps_on_machine[i].stepId
                second_step_id = steps_on_machine[i + 1].stepId

                if resolved_steps_dict[first_step_id].start > resolved_steps_dict[second_step_id].start:
                    if first_step_id in factory_info_provider.moved_steps \
                            or second_step_id in factory_info_provider.moved_steps:
                        weighted_inversions_sum += 20 + int(sqrt(len(factory.steps)))
                    elif factory_info_provider.is_step_connected_with_moved_steps(first_step_id) \
                            or factory_info_provider.is_step_connected_with_moved_steps(second_step_id):
                        weighted_inversions_sum += 0.1
                    else:
                        weighted_inversions_sum += 1

            for i in range(len(steps_on_machine) - 1):
                first_resolved_step_id = resolved_steps_on_machine[i].stepId
                second_resolved_step_id = resolved_steps_on_machine[i + 1].stepId

                if factory.steps[first_resolved_step_id].start > factory.steps[second_resolved_step_id].start:
                    if first_resolved_step_id in factory_info_provider.moved_steps \
                            or second_resolved_step_id in factory_info_provider.moved_steps:
                        weighted_inversions_sum += 10
                    elif factory_info_provider.is_step_connected_with_moved_steps(first_resolved_step_id) \
                            or factory_info_provider.is_step_connected_with_moved_steps(second_resolved_step_id):
                        weighted_inversions_sum += 0.1
                    else:
                        weighted_inversions_sum += 1

            moved_steps_on_machine = [factory.steps[stepId] for stepId in factory_info_provider.moved_steps if
                                      factory.steps[stepId].machineId == machine_id]
            for moved_step in moved_steps_on_machine:
                moved_resolved_step = resolved_steps_dict[moved_step.stepId]
                for step in steps_on_machine:
                    resolved_step = resolved_steps_dict[step.stepId]
                    if not self._is_right_order(moved_step, step, moved_resolved_step, resolved_step):
                        weighted_inversions_sum += 3
            result_evaluation += weighted_inversions_sum

        return result_evaluation

    def _is_right_order(self, first_step, second_step, first_resolved_step, second_resolved_step):
        if first_step.start >= second_step.start and first_resolved_step.start >= second_resolved_step.start:
            return True
        if first_step.start <= second_step.start and first_resolved_step.start <= second_resolved_step.start:
            return True
        return False
