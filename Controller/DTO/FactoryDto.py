from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from Model.Machine import Machine
from Controller.DTO.CampaignDto import CampaignDto
from Controller.DTO.MachineDto import MachineDto
from Controller.DTO.NotOverlappingStepsPairDto import NotOverlappingStepsPairDto
from Controller.DTO.SlowPeriodDto import SlowPeriodDto
from Controller.DTO.StepDto import StepDto
from Controller.DTO.MachineSetupDto import MachineSetupDto
from Controller.DTO.StepOrderDto import StepOrderDto
from Controller.DTO.IdlePeriodDto import IdlePeriodDto
from Controller.DTO.DemandDto import DemandDto


@dataclass
class FactoryDto:
    steps: Optional[List[StepDto]] = field(default_factory=list)
    machinesSetup: Optional[List[MachineSetupDto]] = field(default_factory=list)
    stepsOrder: Optional[List[StepOrderDto]] = field(default_factory=list)
    machines: Optional[List[MachineDto]] = field(default_factory=list)
    campaigns: Optional[List[CampaignDto]] = field(default_factory=list)
    idlePeriods: Optional[List[IdlePeriodDto]] = field(default_factory=list)
    slowPeriods: Optional[List[SlowPeriodDto]] = field(default_factory=list)

    demands: Optional[List[DemandDto]] = field(default_factory=list)
    notOverlappingStepsPairs: Optional[List[NotOverlappingStepsPairDto]] = field(default_factory=list)