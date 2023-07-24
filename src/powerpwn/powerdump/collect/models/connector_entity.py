import json
from copy import deepcopy
from datetime import datetime
from typing import Dict

import prance
from pydantic import Field

from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.utils.json_utils import change_obj_recu


class Connector(ResourceEntityBase):
    api_name: str = Field(..., title="API Name")

    environment_id: str = Field(..., title="Environment ID")

    swagger: Dict = Field(..., title="OpenAPI spec")

    created_at: datetime = Field(..., title="Creation time")

    last_modified_at: datetime = Field(..., title="Last modified time")

    created_by: str = Field(..., title="Created by")

    version: str = Field(..., title="Connector version")

    def processed_swagger(self, connection_id: str, make_concrete: bool = False) -> Dict:
        # avoid side effects
        swagger_instance = deepcopy(self.swagger)

        # clean connectionId from path
        swagger_instance["paths"] = {k.replace("{connectionId}", connection_id): v for k, v in swagger_instance.get("paths", {}).items()}

        if make_concrete:
            # resolve references
            parser = prance.ResolvingParser(spec_string=json.dumps(swagger_instance))
            parsed_swagger = parser.specification

            # ensure examples are generate with rich schemas
            def _arrays_should_have_min_items(_val: Dict):
                if _val.get("type") == "array":
                    _val["minItems"] = 1

            change_obj_recu(val=parsed_swagger, obj_changer=_arrays_should_have_min_items)

            def _objects_should_have_all_properties(_val: Dict):
                if _val.get("type") == "object" and "required" not in _val:
                    _val["required"] = list(_val.get("properties", {}).keys())

            change_obj_recu(val=parsed_swagger, obj_changer=_objects_should_have_all_properties)
        else:
            parsed_swagger = swagger_instance

        return parsed_swagger
