from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class ResolvedMachineSetup:
    setupStart: int
    setupEnd: int
    setupDuration: int

    def __init__(self, setupEnd, setupDuration):
        self.setupEnd = setupEnd
        self.setupDuration = setupDuration
        self.setupStart = setupEnd - setupDuration

    def move_end(self, new_end: int):
        self.setupEnd = new_end
        self.setupStart = self.setupEnd - self.setupDuration

    def changeDuration(self, new_duration: int):
        self.setupDuration = new_duration
        self.setupStart = self.setupEnd - self.setupDuration