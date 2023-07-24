from typing import Any, Dict

from pydantic import ValidationError

from powerpwn.powerdump.utils.const import DATA_MODEL_VERSION


class BaseEntityValidator:
    # noinspection PyUnusedLocal
    @classmethod
    def validate_data_model_version(cls, data_model_version: str, values: Dict[str, Any]) -> str:
        if data_model_version != DATA_MODEL_VERSION:
            raise ValidationError(f"Expected DATA_MODEL_VERSION {DATA_MODEL_VERSION}, got {data_model_version}.")

        return data_model_version
