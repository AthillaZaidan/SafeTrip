from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .schemas import Incident, validate_incident_payload


def write_incidents(incidents: Iterable[Incident | dict[str, Any]], path: str | Path) -> Path:
    payloads = [incident.to_dict() if isinstance(incident, Incident) else incident for incident in incidents]
    for payload in payloads:
        validate_incident_payload(payload)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payloads, indent=2, sort_keys=True), encoding="utf-8")
    return destination


def append_jsonl(record: dict[str, Any], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
