from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import EvidenceReceipt


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_payload(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def make_receipt(*, packet_id: str, kind: str, uri: str, producer: str, payload: Any, claims: dict[str, Any] | None = None) -> EvidenceReceipt:
    if not kind or not uri or not producer:
        raise ValueError("kind, uri, and producer are required")
    return EvidenceReceipt(
        packet_id=packet_id,
        kind=kind,
        uri=uri,
        digest=digest_payload(payload),
        producer=producer,
        claims=claims or {},
    )
