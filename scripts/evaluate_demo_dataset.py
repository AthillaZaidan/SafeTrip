from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transitshield_vision.annotations import validate_annotation_document
from transitshield_vision.evaluation import GroundTruthEvent, evaluate_by_event_type


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate saved TransitShield incidents at event level.")
    parser.add_argument("--incidents", default="outputs/incidents.json")
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--duration-hours", type=float, required=True)
    parser.add_argument("--iou-threshold", type=float, default=0.1)
    parser.add_argument("--output-dir", default="outputs/metrics")
    args = parser.parse_args()

    predictions = json.loads(Path(args.incidents).read_text(encoding="utf-8"))
    raw_annotations = json.loads(Path(args.annotations).read_text(encoding="utf-8"))
    documents = raw_annotations if isinstance(raw_annotations, list) else [raw_annotations]
    truth = []
    for raw in documents:
        document = validate_annotation_document(raw)
        for event in document["events"]:
            truth.append(
                GroundTruthEvent(
                    event["event_type"],
                    document["camera_id"],
                    event.get("zone_id"),
                    event["start_frame"] / document["fps"],
                    event["end_frame"] / document["fps"],
                    event.get("track_id"),
                )
            )
    metrics = evaluate_by_event_type(predictions, truth, duration_hours=args.duration_hours, iou_threshold=args.iou_threshold)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "event_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    with (output_dir / "event_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["event_type", *next(iter(metrics.values())).keys()]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({"event_type": event_type, **values} for event_type, values in metrics.items())
    print(output_dir.as_posix())


if __name__ == "__main__":
    main()
