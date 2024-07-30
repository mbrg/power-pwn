import json
import os
from typing import Dict, List, Optional

from powerpwn.common.cache.cached_entity import CachedEntity


class StringKeyValueCache:
    def __init__(self, cache_path: str):
        self.__cache_path = cache_path

    @property
    def cache_path(self) -> str:
        return self.__cache_path

    def clear_token_cache(self) -> None:
        if os.path.exists(self.__cache_path):
            os.remove(self.__cache_path)

    def put_token(self, token_to_cache: CachedEntity) -> None:
        self.put_tokens([token_to_cache])

    def try_fetch_token(self, token_type: str) -> Optional[str]:
        if not os.path.exists(self.__cache_path):
            return None

        tokens = self.__load_tokens()
        return tokens.get(token_type)

    def put_tokens(self, tokens: List[CachedEntity]) -> None:
        cached_tokens = {}
        if os.path.exists(self.__cache_path):
            # json.load fails on "w+" permission
            cached_tokens = self.__load_tokens()
        f = open(self.__cache_path, "w")
        for token in tokens:
            cached_tokens[token.key] = token.val
        f.write(json.dumps(cached_tokens, indent=4))
        f.close()

    def __load_tokens(self) -> Dict[str, str]:
        with open(self.__cache_path) as file:
            try:
                return json.load(file)
            except json.decoder.JSONDecodeError:
                return {}
