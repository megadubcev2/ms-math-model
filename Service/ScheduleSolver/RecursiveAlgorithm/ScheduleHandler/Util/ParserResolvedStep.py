from Model.IntervalType import IntervalType
from Model.ResolvedStep import ResolvedStep
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval


class ParserResolvedStep:
    def resolved_interval_to_resolved_step(self, resolved_interval: ResolvedInterval) -> ResolvedStep:
        resolved_step = ResolvedStep(resolved_interval.intervalId, resolved_interval.start, resolved_interval.duration)
        if resolved_interval.get_setup_duration() != 0:
            resolved_step.setupDuration = resolved_interval.get_setup_duration()
            resolved_step.setupStart = resolved_interval.get_setup_start()
        return resolved_step

    def resolved_intervals_to_resolved_steps(self, resolved_intervals) -> [ResolvedStep]:
        resolved_steps = []
        resolved_intervals_only_steps = [interval for interval in resolved_intervals if
                                         interval.type != IntervalType.IDLE_PERIOD]
        for step in resolved_intervals_only_steps:
            resolved_step = self.resolved_interval_to_resolved_step(step)
            resolved_steps.append(resolved_step)

        return resolved_steps
