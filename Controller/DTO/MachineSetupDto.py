from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID




@dataclass
class MachineSetupDto:
    fromOperationId: UUID
    toOperationId: UUID
    duration: int