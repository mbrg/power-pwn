from pydantic import Field

from powerpwn.machinepwn.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.machinepwn.models.command_args_properties_base_model import (
    CommandArgsPropertiesBaseModel,
)


class CodeExecArgsProperties(CommandArgsPropertiesBaseModel):
    code_exec_command_type: CodeExecTypeEnum = Field(help="Execution environment")
    code_exec_command: str = Field(help="A command to execute encoded as a string")
