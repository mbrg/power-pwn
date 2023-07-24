from typing import Any, Dict, List

from pydantic import BaseModel

from powerpwn.powerdoor.enums.flow_state import FlowState


class CreateFlowModel(BaseModel):
    flow_display_name: str
    flow_definition: Dict[str, Any]
    flow_state: FlowState
    connection_references: List[Dict[str, str]]
