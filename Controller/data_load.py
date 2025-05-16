from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from Controller.DTO.MetadataLayer import MetadataLayer  # Предполагается, что это Enum

# DTO для требований
class DemandDto(BaseModel):
    id: UUID
    dueDate: int

# DTO для периодов простоя
class IdlePeriodDto(BaseModel):
    id: UUID
    machineId: UUID
    start: int
    duration: int

# DTO для периодов замедления
class SlowPeriodDto(BaseModel):
    id: UUID
    machineId: UUID
    start: int
    duration: int
    coefficient: str

# DTO для смещённых шагов
class MovedStepDto(BaseModel):
    id: UUID
    newStart: int

# DTO для шага
class StepDto(BaseModel):
    id: UUID
    machineId: UUID
    start: int
    duration: int
    initialDuration: int
    setupStart: int
    setupDuration: int
    fixed: bool
    operationId: UUID
    campaignId: Optional[UUID] = None
    demandId: Optional[UUID] = None

# DTO для настройки машины
class MachineSetupDto(BaseModel):
    fromOperationId: UUID
    toOperationId: UUID
    duration: int

# DTO для порядка шагов
class StepOrderDto(BaseModel):
    previousStepId: UUID
    nextStepId: UUID
    overlapMin: int
    overlapMax: int
    stepOrderType: Optional[str] = None

# DTO для машины
class MachineDto(BaseModel):
    id: UUID
    start: int
    operationIdBeforeActive: Optional[UUID] = None

# DTO для пар нес перекрывающихся шагов
class NotOverlappingStepsPairDto(BaseModel):
    firstStepId: UUID
    secondStepId: UUID

# DTO для кампании
class CampaignDto(BaseModel):
    id: UUID
    machineId: UUID
    start: int
    duration: int
    setupStart: int
    setupDuration: int
    fixed: bool
    operationId: UUID

# DTO для фабрики
class FactoryDto(BaseModel):
    steps: Optional[List[StepDto]] = []
    machinesSetup: Optional[List[MachineSetupDto]] = []
    stepsOrder: Optional[List[StepOrderDto]] = []
    machines: Optional[List[MachineDto]] = []
    idlePeriods: Optional[List[IdlePeriodDto]] = []
    slowPeriods: Optional[List[SlowPeriodDto]] = []
    campaigns: Optional[List[CampaignDto]] = []
    demands: Optional[List[DemandDto]] = []
    notOverlappingStepsPairs: Optional[List[NotOverlappingStepsPairDto]] = []

# DTO для запроса оптимизации
class OptimizationRequestDto(BaseModel):
    maxSearchTime: int
    factory: FactoryDto

# DTO для запроса перемещения
class MovementRequestDto(BaseModel):
    maxSearchTime: int
    factory: FactoryDto
    movedSteps: Optional[List[MovedStepDto]] = []
    movementType: Optional[str] = "SOFT"

# DTO для запроса сортировки
class SortingRequestDto(BaseModel):
    maxSearchTime: int
    factory: FactoryDto
    sortedSteps: Optional[List[UUID]] = []

# DTO для ответа оптимизации
class OptimizationResponseDto(BaseModel):
    stepId: UUID
    start: int
    duration: int
    setupStart: Optional[int] = None
    setupDuration: Optional[int] = None

    class Config:
        from_attributes = True

# DTO для метаданных
class MetadataDto(BaseModel):
    mnemoCode: str
    payload: Any

# DTO для метаданных ответа
class ResponseMetadataDto(BaseModel):
    messages: Dict[MetadataLayer, List[MetadataDto]]

    class Config:
        use_enum_values = True

# DTO для общего ответа
class ResponseDto(BaseModel):
    payload: Optional[Any] = None
    metadata: Optional[ResponseMetadataDto] = None
