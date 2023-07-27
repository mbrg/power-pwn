from typing import Optional

from pydantic import Field

from powerpwn.powerdump.collect.models.base_entity import BaseEntity
from powerpwn.powerdump.collect.models.data_record_entity import DataRecordWithContext
from powerpwn.powerdump.utils.const import ENCODING


class DataDump(BaseEntity):
    extension: str = Field(..., title="File extension")
    encoding: Optional[str] = Field(title="Text encoding", default=ENCODING)
    content: bytes = Field(..., title="Content in bytes")


class DataDumpWithContext(BaseEntity):
    data_record: DataRecordWithContext = Field(..., title="Data record")
    data_dump: DataDump = Field(..., title="Data Dump")
