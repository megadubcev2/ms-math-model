from typing import Optional
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval

class ResolvedIntervalNode:
    def __init__(self, resolvedInterval: ResolvedInterval, previousNode: Optional['ResolvedIntervalNode'] = None, nextNode: Optional['ResolvedIntervalNode'] = None):
        self.resolvedInterval: ResolvedInterval = resolvedInterval
        self.previousNode: Optional['ResolvedIntervalNode'] = previousNode  # Ссылка на предыдущий узел
        self.nextNode: Optional['ResolvedIntervalNode'] = nextNode  # Ссылка на следующий узел
