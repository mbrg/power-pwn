from typing import Any, Dict, Optional


class DataStoreValidator:
    # noinspection PyUnusedLocal
    @classmethod
    def validate_tenant(cls, tenant: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        if tenant in (None, ""):
            if (account := values.get("account")) is not None:
                if account.count("@") == 1:
                    # populate tenant with email domain
                    tenant = account.split("@")[-1]

        return tenant
