from typing import Optional

from pydantic import EmailStr, Field

from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase


class Principal(ResourceEntityBase):
    principal_id: str = Field(..., title="Connection ID")
    type: str = Field(..., title="Principal type")
    tenant_id: str = Field(..., title="AAD tenant ID")
    email: Optional[EmailStr] = Field(None, title="Email address")
    upn: Optional[EmailStr] = Field(None, title="User principal name")
