# Post-Incident Investigation

## Goal

Turn a natural-language report into editable search attributes, retrieve the best matching prepared CCTV clips, let Gemini explain visual support and contradictions, and build a chronological timeline from clips confirmed by an investigator.

## MVP flow

```text
Report
  -> structured extraction
  -> human correction and confirmation
  -> time/camera metadata filtering
  -> deterministic candidate ranking
  -> Gemini VLM verification or cached verification
  -> human confirm/reject
  -> human-verified timeline
```

The API never treats an AI recommendation as evidence. Only a confirmed candidate enters the timeline.

## Architecture

The existing FastAPI, SQLAlchemy, report, investigation, candidate, timeline, and audit models remain the system boundary. A tracked JSON library describes nine controlled Tanah Abang clips: three appearances of the target across consecutive cameras and six hard distractors. Generated videos are copied into ignored local storage later.

Retrieval is metadata-first. It applies the report time window and optional camera filter, then scores location, upper clothing, accessories, event, and direction. Only the top five candidates reach Gemini. This is sufficient for the hackathon library and avoids embeddings, a vector database, face recognition, and person re-identification.

One small Gemini adapter performs:

- structured report extraction with a Pydantic response schema;
- video verification with supported attributes, contradictions, uncertainties, relevant timestamps, and a match recommendation.

The adapter loads `google-genai` lazily. Missing credentials, quota failures, malformed responses, missing videos, and API timeouts use explicit cached responses from the controlled demo library. Every response states whether it came from `gemini`, `cached`, or `fallback`.

The default model is the cost-efficient `gemini-3.1-flash-lite`. Set `GEMINI_MODEL` to override it. `GOOGLE_API_KEY` takes precedence over `GEMINI_API_KEY` when both exist.

## Search attributes

```json
{
  "time_window_start": "2026-07-17T17:05:00",
  "time_window_end": "2026-07-17T17:15:00",
  "location": "Lantai 1 Concourse",
  "camera_ids": [],
  "upper_clothing": "grey jacket",
  "lower_clothing": "dark trousers",
  "accessories": ["black backpack"],
  "direction": "toward Exit D",
  "event": "running"
}
```

Explicit form values for time, location, and direction are authoritative over extracted values. An investigator must PATCH the attributes before starting an investigation.

## Candidate contract

```json
{
  "candidate_id": "...",
  "clip_id": "CLIP-TA-007",
  "score": 1.0,
  "camera_id": "CAM_TA_EXIT_D_LINK",
  "location": "Exit D Link",
  "timestamp": "2026-07-17T17:10:50+07:00",
  "url": null,
  "media_available": false,
  "vlm_result": {
    "supported_attributes": ["grey upper clothing", "black backpack"],
    "contradicted_attributes": [],
    "uncertainties": ["exact backpack material is unclear"],
    "relevant_start_seconds": 1.2,
    "relevant_end_seconds": 7.4,
    "match_recommendation": "likely_match",
    "source": "cached"
  },
  "verification_status": "pending"
}
```

Unavailable local media is represented by `url: null` and `media_available: false`. Cached VLM output may still demonstrate ranking before the generated videos are copied in.

## API behavior

- `POST /api/v1/reports/{id}/extract` persists typed attributes and the AI source.
- `PATCH /api/v1/reports/{id}/attributes` validates and marks attributes confirmed.
- `POST /api/v1/investigations` rejects reports whose attributes are not confirmed.
- `GET /api/v1/investigations/{id}/candidates` returns deterministic ranked candidates.
- `PATCH /api/v1/investigations/{id}/candidates/{candidate_id}` accepts only `confirmed` or `rejected` plus an optional investigator note.
- Confirmation is idempotent. Rejection removes any prior timeline entry for that candidate.
- `GET /api/v1/investigations/{id}/timeline` returns confirmed clips in timestamp order with `human_verified: true`.
- Unknown reports, investigations, and candidates return 404. Invalid state transitions return 409 or 422.

## Demo library

The controlled library contains:

- three target clips across `CAM_TA_LEVEL_1_CONCOURSE`, `CAM_TA_LEVEL_2_MEZZANINE`, and `CAM_TA_EXIT_D_LINK`;
- two distractors per camera that disagree on clothing, backpack, or direction;
- deterministic timestamps, metadata, and cached VLM explanations;
- local media paths under ignored `data/investigation-videos/`.

The public IDs and filenames are deliberately opaque: `CLIP-TA-001` through `CLIP-TA-009` and `clip-ta-001.mp4` through `clip-ta-009.mp4`. They do not reveal which clips are targets or distractors.

## Run the server

From the repository root:

```bash
conda activate bdc2026-dinov3
python -m pip install -r server/requirements.txt
uvicorn server.app.main:app --reload
```

Live Gemini is optional. Create `.env` at the repository root:

```bash
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY.
```

The application loads this file automatically. Shell environment variables override `.env`, and `GOOGLE_API_KEY` takes precedence over `GEMINI_API_KEY`.

Copy generated videos into `data/investigation-videos/`. The adapter sends only MP4 files smaller than the safe inline request threshold. If a video, credential, or Gemini response is unavailable, the controlled demo uses the corresponding cached result. A non-demo report without a usable AI result receives `source: fallback` and empty unsupported attributes.

After pulling ORM changes, rebuild the ignored SQLite database because this hackathon server has no migration framework:

```bash
rm server/data/transitshield.db
python server/seed.py
```

## Complete curl demo

Create the controlled report:

```bash
curl -sS http://127.0.0.1:8000/api/v1/reports \
  -H 'content-type: application/json' \
  -d '{
    "reporter_type": "passenger",
    "time_window_start": "2026-07-17T17:09:00+07:00",
    "time_window_end": "2026-07-17T17:11:59+07:00",
    "location": "",
    "description": "Orang berjaket abu-abu dan membawa tas hitam berlari menuju Exit D.",
    "direction": "toward Exit D"
  }'
```

Copy the returned `report_id`, then extract and inspect the attributes:

```bash
curl -sS -X POST \
  http://127.0.0.1:8000/api/v1/reports/REPORT_ID/extract
```

The investigator must correct and confirm the attributes before search:

```bash
curl -sS -X PATCH \
  http://127.0.0.1:8000/api/v1/reports/REPORT_ID/attributes \
  -H 'content-type: application/json' \
  -d '{"attributes": {
    "time_window_start": "2026-07-17T17:09:00+07:00",
    "time_window_end": "2026-07-17T17:11:59+07:00",
    "location": "",
    "camera_ids": [],
    "upper_clothing": "grey jacket",
    "lower_clothing": "",
    "accessories": ["black backpack"],
    "direction": "toward Exit D",
    "event": "running"
  }}'
```

Create the investigation and list its candidates:

```bash
curl -sS http://127.0.0.1:8000/api/v1/investigations \
  -H 'content-type: application/json' \
  -d '{"report_id": "REPORT_ID"}'

curl -sS \
  http://127.0.0.1:8000/api/v1/investigations/INVESTIGATION_ID/candidates
```

Confirm or reject candidates after human inspection:

```bash
curl -sS -X PATCH \
  http://127.0.0.1:8000/api/v1/investigations/INVESTIGATION_ID/candidates/CANDIDATE_ID \
  -H 'content-type: application/json' \
  -d '{"verification_status": "confirmed", "note": "Seen moving toward Exit D"}'

curl -sS \
  http://127.0.0.1:8000/api/v1/investigations/INVESTIGATION_ID/timeline
```

Reset only post-incident demo data while preserving cameras, zones, officers, playbooks, incidents, and their audit records:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/demo/reset
```

## Verification

The server test suite must prove the complete cached path without network access: report creation, extraction, correction, investigation creation, deterministic candidates, scoped and idempotent review, and chronological timeline. Separate tests cover Gemini failure fallback, invalid time ranges, unconfirmed reports, invalid statuses, cross-investigation candidate access, missing resources, and truthful missing-media output.

The live Gemini path cannot be considered verified without credentials and generated videos. It remains optional until those assets are available. The cached path is fully covered by API integration tests and never makes a network call.
