from datetime import datetime
from typing import Dict, Optional

from pydantic import Field, HttpUrl

from powerpwn.powerdump.collect.models.principal_entity import Principal
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase


class Connection(ResourceEntityBase):
    connection_id: str = Field(..., title="Connection ID")

    is_valid: bool = Field(..., title="Has no error indicators")
    shareable: bool = Field(..., title="Is connection shareable")

    connector_id: str = Field(..., title="Connector ID")
    api_id: str = Field(..., title="API ID")
    icon_uri: HttpUrl = Field(..., title="Icon URI")

    environment_id: str = Field(..., title="Environment ID")
    environment_name: str = Field(..., title="Environment Name")

    created_at: datetime = Field(title="Created time")
    last_modified_at: datetime = Field(title="Last modified time")
    expiration_time: Optional[datetime] = Field(title="Expiration time")

    created_by: Principal = Field(..., title="Created by")

    connection_parameters: Dict = Field(..., title="Connection parameters")
    test_uri: Optional[HttpUrl] = Field(..., title="Test URI")

    @property
    def api_name(self) -> str:
        return self.api_id.split("/")[-1]
