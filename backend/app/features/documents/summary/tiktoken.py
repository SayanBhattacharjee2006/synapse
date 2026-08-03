import tiktoken
from functools import lru_cache

@lru_cache(maxsize=1) 
def get_tokenizer():
    return tiktoken.encoding_for_model("gpt-4o-mini")


def get_token_count(text: str) -> int:
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))