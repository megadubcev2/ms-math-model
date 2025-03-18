from enum import Enum


class ConflictType(Enum):
    MachineIntervalConflict = 1
    OverlappingIntervalsConflict = 2
    StepOrderConflict = 3
    DeadlineConflict = 4
