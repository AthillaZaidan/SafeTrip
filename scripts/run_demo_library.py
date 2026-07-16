from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transitshield_vision.config import load_json, parse_camera_config, parse_event_rules, parse_runtime_config, set_deterministic_seed
from transitshield_vision.runner import run_pipeline, write_library_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multiple TransitShield demo cameras without overwriting their outputs.")
    parser.add_argument("--camera-config", action="append", required=True)
    parser.add_argument("--runtime-config", default="configs/runtime.json")
    parser.add_argument("--event-rules", default="configs/event_rules.json")
    parser.add_argument("--output-root", default="outputs/library")
    parser.add_argument("--cache-root", default="data/cached-ai")
    args = parser.parse_args()

    runtime = parse_runtime_config(load_json(args.runtime_config))
    if runtime.execution_mode == "manual_demo":
        raise ValueError("library runner supports full_ai and cached_ai; use run_demo_pipeline.py for manual_demo")
    rules = parse_event_rules(load_json(args.event_rules))
    set_deterministic_seed(runtime.random_seed)
    results = []
    for config_path in args.camera_config:
        camera = parse_camera_config(load_json(config_path), require_video=runtime.execution_mode == "full_ai")
        camera_output = Path(args.output_root) / "cameras" / camera.camera_id
        cache_path = None
        if runtime.execution_mode == "cached_ai":
            cache_path = Path(args.cache_root) / f"{Path(camera.video_path).stem}_tracks.jsonl"
        results.append(run_pipeline(runtime, camera, rules, output_root=camera_output, cache_path=cache_path))

    print(json.dumps(write_library_result(results, args.output_root), indent=2))


if __name__ == "__main__":
    main()
