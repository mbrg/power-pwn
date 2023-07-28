from powerpwn.enums.str_enum import StrEnum


class BackdoorActionType(StrEnum):
    create_flow = "create-flow"
    delete_flow = "delete-flow"
    get_connections = "get-connections"
    install_factory = "install-factory"
