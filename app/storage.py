"""Optional MongoDB logging. If MONGODB_URI is not set, everything still works without it."""
import os
from datetime import datetime, timezone

_client = None


def _db():
    global _client
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return _client[os.getenv("MONGODB_DATABASE", "apex2")]


def save_run(kind: str, payload: dict) -> bool:
    db = _db()
    if db is None:
        return False
    try:
        db["runs"].insert_one({"kind": kind, "at": datetime.now(timezone.utc), **payload})
        return True
    except Exception:
        return False
