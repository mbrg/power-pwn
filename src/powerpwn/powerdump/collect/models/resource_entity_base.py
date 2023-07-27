from typing import Any, Dict, Optional

from powerpwn.powerdump.collect.models.base_entity import BaseEntity
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType


class ResourceEntityBase(BaseEntity):
    entity_type: ResourceType
    display_name: Optional[str] = None
    entity_id: str
    raw_json: Dict[str, Any]
