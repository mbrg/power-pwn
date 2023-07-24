from powerpwn.enums.str_enum import StrEnum


class ActionType(StrEnum):
    create_flow = "create-flow"
    delete_flow = "delete-flow"
    get_connections = "get-connections"
