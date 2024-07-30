import os

from powerpwn.common.cache.string_key_value_cache import StringKeyValueCache


class TokenCache(StringKeyValueCache):
    def __init__(self):
        super().__init__(os.path.join(os.getcwd(), "tokens.json"))
