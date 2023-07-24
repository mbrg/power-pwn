from pydantic import Field

from powerpwn.machinepwn.models.command_args_properties_base_model import CommandArgsPropertiesBaseModel


class StealCookieArgsProperties(CommandArgsPropertiesBaseModel):
    steal_cookie_fqdn: str = Field(help="fully qualified domain name to fetch the cookies of")