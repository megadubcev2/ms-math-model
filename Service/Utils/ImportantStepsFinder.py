from Service.Factory.FactoryCropper import FactoryCropper
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleSolverRecursive import ScheduleSolverRecursive


class ImportantStepsFinder:
    def __init__(self):
        self.factory_cropper = FactoryCropper()

    """ищет степы, в которых в теории могут быть неразрешимые конфликты """

    def find(self, schedule_solver_recursive: ScheduleSolverRecursive):
        factory_info_provider = schedule_solver_recursive.factory_info_provider
        factory = factory_info_provider.factory
        steps_id_with_conflicts = schedule_solver_recursive.find_steps_with_conflict()
        important_connectivity_components = set()
        for step in factory.steps.values():
            if step.fixed:
                important_connectivity_components.add(factory_info_provider.connectivity_components[step.stepId])

        for stepId in steps_id_with_conflicts:
            important_connectivity_components.add(factory_info_provider.connectivity_components[stepId])

        important_steps_id = []
        for step in factory.steps.values():
            if factory_info_provider.connectivity_components[step.stepId] in important_connectivity_components:
                important_steps_id.append(step.stepId)

        return important_steps_id

    def crop_factory_with_important_steps(self, schedule_solver_recursive: ScheduleSolverRecursive):
        factory_info_provider = schedule_solver_recursive.factory_info_provider
        factory = factory_info_provider.factory
        important_steps_id = self.find(schedule_solver_recursive)
        factory_with_important_steps = self.factory_cropper.crop_by_steps(factory, important_steps_id)
        return factory_with_important_steps
