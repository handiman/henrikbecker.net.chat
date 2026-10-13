from typing import Any

SUPPORTED_COLLECTIONS = frozenset({"henrik"})


class CVStore:
    """The CV document per collection, kept in Workers KV (shared by all instances)."""

    def __init__(self, kv: Any) -> None:
        self._kv = kv

    @staticmethod
    def _key(collection: str) -> str:
        return f"cv:{collection}"

    async def get(self, collection: str) -> str:
        return await self._kv.get(self._key(collection)) or ""

    async def put(self, collection: str, document: str) -> None:
        await self._kv.put(self._key(collection), document)
