from typing import Dict, Optional

from pydantic import Field

from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.base_entity import BaseEntity
from powerpwn.powerdump.collect.models.data_store_entity import DataStoreWithContext


class DataRecord(BaseEntity):
    record_type: DataDumpType = Field(..., title="Record type")
    record_id: str = Field(..., title="Record ID")
    record_name: Optional[str] = Field(..., title="Record display name")
    extra: Dict = Field(..., title="Additional information")


class DataRecordWithContext(BaseEntity):
    data_store: DataStoreWithContext = Field(..., title="Data Store")
    data_record: DataRecord = Field(..., title="Data Record")
