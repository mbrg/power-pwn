import json
import os
from typing import Dict, List, NamedTuple, Optional

TOKEN_CACHE_PATH = os.path.join(os.getcwd(), "tokens.json")


class TokenCache(NamedTuple):
    token_key: str
    token_val: str


def put_token(token_to_cache: TokenCache) -> None:
    put_tokens([token_to_cache])


def try_fetch_token(token_type: str) -> Optional[str]:
    if not os.path.exists(TOKEN_CACHE_PATH):
        return None

    tokens = __load_tokens()
    return tokens.get(token_type)


def put_tokens(tokens: List[TokenCache]) -> None:
    cached_tokens = {}
    if os.path.exists(TOKEN_CACHE_PATH):
        # json.load fails on "w+" permission
        cached_tokens = __load_tokens()
    f = open(TOKEN_CACHE_PATH, "w")
    for token in tokens:
        cached_tokens[token.token_key] = token.token_val
    f.write(json.dumps(cached_tokens, indent=4))
    f.close()


def __load_tokens() -> Dict[str, str]:
    with open(TOKEN_CACHE_PATH) as file:
        try:
            return json.load(file)
        except json.decoder.JSONDecodeError:
            return {}
