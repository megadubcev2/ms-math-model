from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from Model.MachineType import MachineType


@dataclass
class Machine:
    machineId: UUID
    start: int
    operationIdBeforeActive: UUID
    type: MachineType

