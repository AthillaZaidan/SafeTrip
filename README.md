# TransitShield AI

Human-reviewed CCTV safety response and post-incident investigation for public transportation.

The MVP supports exactly three human-reviewed events:

- `restricted_zone_intrusion`
- `possible_person_down`
- `crowd_compression`

## Environment

```bash
conda activate bdc2026-dinov3
export PYTHONPATH=src
python -m pytest tests -q
```

The same commands can be run without activating the shell:

```bash
conda run -n bdc2026-dinov3 env PYTHONPATH=src python -m pytest tests -q
```

The server has no migration framework. After schema changes, rebuild the ignored hackathon database from the repository root:

```bash
rm server/data/transitshield.db
python server/seed.py
```

## Run the investigation API

Install the server dependencies inside the same Conda environment, then start FastAPI from the repository root:

```bash
python -m pip install -r server/requirements.txt
uvicorn server.app.main:app --reload
```

Gemini is optional for the deterministic demo. Create a local environment file to enable live structured extraction and video verification:

```bash
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY. GEMINI_MODEL is already set to Flash-Lite.
```

The repository-root `.env` file is loaded automatically and ignored by Git. Values exported by the shell override `.env`. `GOOGLE_API_KEY` is also accepted and takes precedence over `GEMINI_API_KEY`. Without credentials or local footage, the controlled Tanah Abang scenario uses cached extraction and cached VLM explanations. Unrelated reports return an explicit `fallback` source instead of fabricated attributes.

Generated MP4 files belong in the ignored `data/investigation-videos/` directory using the neutral names `clip-ta-001.mp4` through `clip-ta-009.mp4`. Missing media is returned as `url: null` and `media_available: false`.

Run the server contract tests with:

```bash
uv run --no-project --with-requirements server/requirements.txt \
  env PYTHONPATH=. python -m pytest server/tests -q
```

The complete API workflow, request bodies, reset behavior, and demo limitations are documented in [`docs/post-incident-investigation.md`](docs/post-incident-investigation.md).

## Run one camera

Full inference reads the camera video, runs YOLO/ByteTrack, and writes a reusable track cache:

```bash
python scripts/run_demo_pipeline.py \
  --execution-mode full_ai \
  --camera-config configs/cameras/demo_camera.json \
  --output-root outputs/demo
```

Cached inference reruns the deterministic event rules from a genuine track JSONL produced by `full_ai`:

```bash
python scripts/run_demo_pipeline.py \
  --execution-mode cached_ai \
  --camera-config configs/cameras/demo_camera.json \
  --cache-path outputs/demo/frame-events/platform_b_demo_tracks.jsonl \
  --output-root outputs/demo-cached
```

Manual demo loads a prepared incident JSON. Every non-null evidence path in that file must already exist:

```bash
python scripts/run_demo_pipeline.py \
  --execution-mode manual_demo \
  --camera-config configs/cameras/demo_camera.json \
  --manual-path data/manual-demo/incidents.json \
  --output-root outputs/demo-manual
```

All modes write `incidents.json` and `pipeline_summary.json`. Incident lifecycle fields must satisfy `start <= detected <= end` when an end exists, and `duration_seconds` must match those timestamps. Unavailable evidence media and failed annotated video outputs are reported as `null`, never as paths to files that do not exist. Every incident remains `requires_human_review: true`.

## Run several cameras

```bash
python scripts/run_demo_library.py \
  --camera-config configs/cameras/demo_camera.json \
  --camera-config configs/cameras/man_falls_platform.json \
  --camera-config configs/cameras/crowd_compression_concourse.json \
  --output-root outputs/library
```

Each camera writes to its own directory. The library runner combines their incidents into `outputs/library/incidents.json` without overwriting earlier cameras.

## Replacing the demo videos

The checked-in camera configurations describe the old generated videos. After creating the Tanah Abang clips:

1. replace each `video_path`;
2. set the camera's `enabled_events`;
3. redraw zone polygons against the new frame resolution;
4. calibrate capacity and event thresholds using genuine cached detections;
5. annotate event start/end frames before reporting precision or recall.

Flow production prompts and validation criteria are in `docs/tanah-abang-flow-prompts.md`.
