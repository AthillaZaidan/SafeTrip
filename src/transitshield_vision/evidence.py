from __future__ import annotations

from pathlib import Path


def evidence_paths(incident_id: str, root: str | Path = "outputs/incidents") -> dict[str, str]:
    base = Path(root) / incident_id
    return {
        "snapshot_raw": (base / "snapshot_raw.jpg").as_posix(),
        "snapshot_annotated": (base / "snapshot_annotated.jpg").as_posix(),
        "clip": (base / "evidence.mp4").as_posix(),
        "metadata": (base / "metadata.json").as_posix(),
    }


def ensure_evidence_directory(incident_id: str, root: str | Path = "outputs/incidents") -> Path:
    path = Path(root) / incident_id
    path.mkdir(parents=True, exist_ok=True)
    return path
