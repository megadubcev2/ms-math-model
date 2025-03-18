from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Campaign:
    campaignId: UUID
    machineId: UUID
    start: int
    duration: int
    fixed: bool
    operationId: UUID

