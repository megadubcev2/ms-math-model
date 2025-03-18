from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class CampaignDto:
    campaignId: UUID
    machineId: UUID
    start: int
    duration: int
    fixed: bool
    operationId: UUID

