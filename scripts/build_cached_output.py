from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config
from transitshield_vision.runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run genuine model inference and save reusable track output.")
    parser.add_argument("--runtime-config", default="configs/runtime.json")
    parser.add_argument("--camera-config", default="configs/cameras/demo_camera.json")
    parser.add_argument("--event-rules", default="configs/event_rules.json")
    parser.add_argument("--output-root", default="outputs")
    args = parser.parse_args()
    runtime = replace(parse_runtime_config(load_json(args.runtime_config)), execution_mode="full_ai")
    camera = parse_camera_config(load_json(args.camera_config), require_video=True)
    result = run_pipeline(runtime, camera, parse_event_rules(load_json(args.event_rules)), output_root=args.output_root)
    print(result.output_paths["track_cache"])


if __name__ == "__main__":
    main()
