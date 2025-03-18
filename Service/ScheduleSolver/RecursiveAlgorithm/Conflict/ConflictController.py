from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Conflict.ConflictChecker import ConflictChecker
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.ConflictResolver import ConflictResolver
from Model.Factory import Factory


class ConflictController:
    def __init__(self, factory: Factory):
        self.factory = factory
        self.conflict_resolver = ConflictResolver()
        self.conflict_checker = ConflictChecker()
