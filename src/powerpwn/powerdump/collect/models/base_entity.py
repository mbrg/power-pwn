from typing import Any

from pydantic import BaseModel, Field, validator

from powerpwn.powerdump.collect.models.base_validator import BaseEntityValidator
from powerpwn.powerdump.utils.const import DATA_MODEL_VERSION


# noinspection PyRedeclaration
class BaseEntity(BaseModel):
    data_model_version: str = Field(title="Data model version", default=DATA_MODEL_VERSION)

    validate_data_model_version: Any = validator("data_model_version", allow_reuse=True)(BaseEntityValidator.validate_data_model_version)

    class Config:
        """
        this config tells pydantic BaseModel to use enum values
        when converting to dict() instead of enum
        """

        validate_assignment = True
        use_enum_values = True
