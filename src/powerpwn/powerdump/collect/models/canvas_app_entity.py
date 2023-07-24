from datetime import datetime
from typing import List

from pydantic import HttpUrl

from powerpwn.powerdump.collect.models.principal_entity import Principal
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase


class CanvasApp(ResourceEntityBase):
    version: str
    created_by: Principal
    created_at: datetime
    last_modified_at: datetime
    run_url: HttpUrl
    environment_id: str
    permissions: List[Principal]
