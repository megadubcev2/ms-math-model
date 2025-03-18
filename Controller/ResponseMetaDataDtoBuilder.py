from typing import Dict, List, Any

from Controller.data_load import MetadataDto, ResponseMetadataDto
from Service.ScheduleSolver.RecursiveAlgorithm.Conflict.Model.ConflictWithType import ConflictWithType
# from Controller.DTO.MetadataDto import MetadataDto
from Controller.DTO.MetadataLayer import MetadataLayer
# from Controller.DTO.ResponseMetadataDto import ResponseMetadataDto


class ResponseMetaDataDtoBuilder:
    def __init__(self):
        self.metadata_messages: Dict[MetadataLayer, List[MetadataDto]] = {
            MetadataLayer.INFO: [],
            MetadataLayer.WARNING: [],
            MetadataLayer.ERROR: []
        }

    def add_message(self, mnemo_code: str, payload: Any, layer: MetadataLayer = MetadataLayer.ERROR):
        if layer not in self.metadata_messages:
            raise ValueError(f"Неверный слой метаданных: {layer}")
        self.metadata_messages[layer].append(MetadataDto(mnemoCode=mnemo_code, payload=payload))

    def add_conflicts_with_types(self, conflicts_with_type: [ConflictWithType]):
        for conflict_with_type in conflicts_with_type:
            self.add_message(mnemo_code=conflict_with_type.type, payload=conflict_with_type.conflict)

    def getResponseMetaDataDTO(self):
        return ResponseMetadataDto(messages=self.metadata_messages)
