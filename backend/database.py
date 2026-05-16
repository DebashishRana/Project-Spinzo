import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Optional


class FirestoreUnavailable(RuntimeError):
    """Raised when Firestore is required but not configured."""


class _MemoryIncrement:
    def __init__(self, value: int):
        self.value = value


_MEMORY_DB: Dict[str, Dict[str, Dict[str, Any]]] = {}


@lru_cache(maxsize=1)
def get_firestore_client():
    """Create a Firestore client from env-provided Firebase Admin credentials."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as exc:
        raise FirestoreUnavailable(
            "firebase-admin is not installed. Add it to requirements.txt."
        ) from exc

    if not firebase_admin._apps:
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        if service_account_json:
            try:
                service_account = json.loads(service_account_json)
            except json.JSONDecodeError as exc:
                raise FirestoreUnavailable(
                    "FIREBASE_SERVICE_ACCOUNT_JSON must be valid service account JSON."
                ) from exc

            private_key = service_account.get("private_key")
            if private_key:
                service_account["private_key"] = private_key.replace("\\n", "\n")

            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred)
        else:
            raise FirestoreUnavailable(
                "Firestore is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON."
            )

    return firestore.client()


def server_timestamp():
    try:
        get_firestore_client()
    except FirestoreUnavailable:
        return datetime.now(timezone.utc).isoformat()

    from firebase_admin import firestore

    return firestore.SERVER_TIMESTAMP


def increment(value: int = 1):
    try:
        get_firestore_client()
    except FirestoreUnavailable:
        return _MemoryIncrement(value)

    from firebase_admin import firestore

    return firestore.Increment(value)


def _memory_collection(collection: str) -> Dict[str, Dict[str, Any]]:
    return _MEMORY_DB.setdefault(collection, {})


def _resolve_memory_value(value: Any, existing: Any = None) -> Any:
    if isinstance(value, _MemoryIncrement):
        return int(existing or 0) + value.value

    if isinstance(value, dict):
        existing_dict = existing if isinstance(existing, dict) else {}
        return {
            key: _resolve_memory_value(nested_value, existing_dict.get(key))
            for key, nested_value in value.items()
        }

    return deepcopy(value)


def _merge_dict(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(existing)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = _resolve_memory_value(value, merged.get(key))
    return merged


def get_doc(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    try:
        snapshot = get_firestore_client().collection(collection).document(doc_id).get()
    except FirestoreUnavailable:
        data = _memory_collection(collection).get(doc_id)
        if data is None:
            return None
        data = deepcopy(data)
        data["_id"] = doc_id
        return data

    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    data["_id"] = snapshot.id
    return data


def set_doc(collection: str, doc_id: str, data: Dict[str, Any], merge: bool = True) -> None:
    try:
        get_firestore_client().collection(collection).document(doc_id).set(data, merge=merge)
    except FirestoreUnavailable:
        docs = _memory_collection(collection)
        if merge and doc_id in docs:
            docs[doc_id] = _merge_dict(docs[doc_id], data)
        else:
            docs[doc_id] = _resolve_memory_value(data)


def add_doc(collection: str, data: Dict[str, Any]) -> str:
    try:
        _, ref = get_firestore_client().collection(collection).add(data)
        return ref.id
    except FirestoreUnavailable:
        doc_id = str(uuid.uuid4())
        _memory_collection(collection)[doc_id] = _resolve_memory_value(data)
        return doc_id


def list_docs(collection: str) -> Dict[str, Dict[str, Any]]:
    try:
        docs = get_firestore_client().collection(collection).stream()
    except FirestoreUnavailable:
        return {
            doc_id: deepcopy(data)
            for doc_id, data in _memory_collection(collection).items()
        }

    return {doc.id: doc.to_dict() or {} for doc in docs}
