from typing import Any, Dict, Optional

from pydantic import Field, HttpUrl, validator

from powerpwn.powerdump.collect.models.base_entity import BaseEntity
from powerpwn.powerdump.collect.models.data_store_validator import DataStoreValidator


class DataStore(BaseEntity):
    account: str = Field(..., title="Account ID")
    tenant: Optional[str] = Field(..., title="Tenant ID")  # order matters, tenant relies on account

    scope: Optional[str] = Field(..., title="Access scope")

    host: HttpUrl = Field(..., title="Host")
    name: Optional[str] = Field(..., title="Display name")

    extra: Dict = Field(..., title="Additional information")

    validate_tenant: Any = validator("tenant", allow_reuse=True)(DataStoreValidator.validate_tenant)


class DataStoreWithContext(BaseEntity):
    api_name: str = Field(..., title="API Name", description="Example: shared_gmail")
    connection_id: str = Field(..., title="Connection ID")
    data_store: DataStore = Field(..., title="Data Store")
