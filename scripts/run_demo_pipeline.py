from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config, set_deterministic_seed
from transitshield_vision.runner import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TransitShield prerecorded-video safety pipeline.")
    parser.add_argument("--runtime-config", default="configs/runtime.json")
    parser.add_argument("--camera-config", default="configs/cameras/demo_camera.json")
    parser.add_argument("--event-rules", default="configs/event_rules.json")
    parser.add_argument("--output-root", default="outputs")
    parser.add_argument("--cache-path")
    parser.add_argument("--manual-path")
    args = parser.parse_args()

    runtime = parse_runtime_config(load_json(args.runtime_config))
    camera = parse_camera_config(load_json(args.camera_config), require_video=runtime.execution_mode == "full_ai")
    rules = parse_event_rules(load_json(args.event_rules))
    set_deterministic_seed(runtime.random_seed)
    result = run_pipeline(runtime, camera, rules, output_root=args.output_root, cache_path=args.cache_path, manual_path=args.manual_path)
    print(json.dumps({"summary": result.summary, "output_paths": result.output_paths}, indent=2))


if __name__ == "__main__":
    main()
