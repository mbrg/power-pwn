from pydantic import Field

from powerpwn.machinepwn.models.command_args_properties_base_model import CommandArgsPropertiesBaseModel


class ExflirtateFileArgsProperties(CommandArgsPropertiesBaseModel):
    exfiltrate_target_file: str = Field(default="", help="Absolute path to file")
