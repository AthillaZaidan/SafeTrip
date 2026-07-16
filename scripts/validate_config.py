from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate TransitShield runtime, camera, and event configuration.")
    parser.add_argument("--runtime-config", default="configs/runtime.json")
    parser.add_argument("--camera-config", default="configs/cameras/demo_camera.json")
    parser.add_argument("--event-rules", default="configs/event_rules.json")
    parser.add_argument("--allow-missing-video", action="store_true")
    args = parser.parse_args()

    runtime = parse_runtime_config(load_json(args.runtime_config))
    camera = parse_camera_config(load_json(args.camera_config), require_video=not args.allow_missing_video)
    rules = parse_event_rules(load_json(args.event_rules))
    print(
        json.dumps(
            {
                "execution_mode": runtime.execution_mode,
                "camera_id": camera.camera_id,
                "video_path": camera.video_path,
                "zone_count": len(camera.zones),
                "event_types": sorted(rules),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
