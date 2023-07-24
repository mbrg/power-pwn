from typing import Generic, TypeVar

from pydantic.generics import GenericModel

from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.models.command_args_properties_base_model import CommandArgsPropertiesBaseModel

_TCommandArgumentProperties = TypeVar("_TCommandArgumentProperties", bound=CommandArgsPropertiesBaseModel)


class CommandArguments(GenericModel, Generic[_TCommandArgumentProperties]):
    command_to_run: CommandToRunEnum
    command_properties: _TCommandArgumentProperties
