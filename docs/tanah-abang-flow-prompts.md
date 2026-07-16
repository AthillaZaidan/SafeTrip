# Tanah Abang Flow Prompts for Live Safety Response

These prompts create a fictionalized but spatially plausible Tanah Abang CCTV universe. The station topology and location names follow the real map; the architecture may be simplified. Generate every clip in landscape 16:9 at 8 seconds.

Do not ask Flow for bounding boxes, labels, timestamps, logos, subtitles, or UI overlays. TransitShield adds those after inference.

## Shared visual anchor

Use this paragraph at the beginning of every image or video prompt:

```text
A realistic fixed security CCTV view inside a simplified reconstruction inspired by Tanah Abang railway station in Jakarta, Indonesia. Modern functional commuter station architecture, concrete and metal surfaces, warm neutral daylight, realistic Indonesian adult passengers, practical everyday clothing, accurate human anatomy and scale. Wide high-angle surveillance framing, landscape 16:9, 1280x720 composition, deep focus, stable exposure, slightly compressed CCTV image quality. The camera is permanently mounted and completely motionless.
```

Use the same station image project and color palette for all cameras. Create one clean empty-location reference image for each camera before animating it. Keep the camera angle unchanged across variations.

## Global negative constraints

Append this paragraph to every video prompt:

```text
Single continuous shot. No cuts, no zoom, no pan, no tilt, no dolly, no handheld movement, no slow motion, no time lapse. No camera shake, lens distortion, fisheye warping, flicker, sudden lighting change, motion blur, duplicated people, merged bodies, disappearing limbs, teleportation, costume changes, face close-ups, readable personal identity, text, watermark, logo, timestamp, bounding box, alarm graphic, police activity, blood, injury detail, fire, smoke, or train collision. Keep each person visually distinct and physically consistent from the first frame to the last frame. Keep full bodies and feet visible whenever possible. No person blocks the main subject for more than half a second.
```

## Clip 1 — Restricted-zone intrusion

**Camera ID:** `CAM_TA_PLATFORM_3_WEST`

**Mapped location:** Peron 3 in the old station building, facing a clearly visible platform safety boundary.

**Flow video prompt:**

```text
[SHARED VISUAL ANCHOR]

Camera CAM_TA_PLATFORM_3_WEST overlooks Platform 3 from a fixed elevated corner. A clear yellow safety line separates the normal passenger platform from a restricted trackside service strip. At the beginning, one Indonesian adult passenger wearing a plain red jacket, dark trousers, and a small black backpack walks normally along the safe side of the platform. Two other adults remain far in the background and do not interact.

Timeline: from 0 to 2 seconds the main passenger stays fully inside the normal platform area. From 2 to 3 seconds the passenger deliberately steps across the yellow safety line with both feet. From 3 to 8 seconds the passenger remains inside the restricted strip and walks slowly parallel to the platform edge. The boundary crossing, both feet, and the passenger's complete body remain clearly visible. There is no train movement and nobody falls.

[GLOBAL NEGATIVE CONSTRAINTS]
```

**Expected detector behavior:** one stable track crosses into the configured restricted polygon and remains there for at least 1.5 seconds.

## Clip 2 — Possible person down

**Camera ID:** `CAM_TA_LEVEL_1_CONCOURSE`

**Mapped location:** Lantai 1 near the passenger circulation area and access toward the stairs/escalators.

**Flow video prompt:**

```text
[SHARED VISUAL ANCHOR]

Camera CAM_TA_LEVEL_1_CONCOURSE overlooks a broad Level 1 passenger circulation area from a fixed elevated corner. The floor is dry, uncluttered, and fully visible. One Indonesian adult passenger wearing a light grey long-sleeve top and dark trousers walks from left to right across the middle foreground. Three other adults remain distant near the edge of the frame.

Timeline: from 0 to 2 seconds the main passenger walks normally with the full body visible. From 2 to 3 seconds the passenger loses balance naturally and falls sideways onto the open floor without striking another person or object. From 3 to 8 seconds the passenger remains lying horizontally and almost motionless, still fully visible and not occluded. The event is non-graphic: no blood, no visible injury, no medical diagnosis, and no dramatic reaction from bystanders.

[GLOBAL NEGATIVE CONSTRAINTS]
```

**Expected detector behavior:** one person transitions from upright movement to a horizontal bounding box and low motion for at least one second. The product label remains `possible_person_down`.

## Clip 3 — Crowd compression

**Camera ID:** `CAM_TA_LEVEL_2_MEZZANINE`

**Mapped location:** Lantai 2 mezzanine near the stairs/escalator circulation area.

For this clip, first create a start frame with six separated adults and an end frame with twelve to fourteen distinct adults gathered in the same marked area. Use Flow's first-and-last-frame mode when available so the camera and architecture remain fixed.

**Start-frame image prompt:**

```text
[SHARED VISUAL ANCHOR]

Camera CAM_TA_LEVEL_2_MEZZANINE overlooks the Level 2 mezzanine near a stair and escalator entrance. Six distinct Indonesian adult passengers are spread loosely across the central waiting area with generous visible floor space between them. Every person has a different solid-color top and a complete visible body. The circulation path is calm and unobstructed.
```

**End-frame image prompt:**

```text
[SHARED VISUAL ANCHOR]

The exact same CAM_TA_LEVEL_2_MEZZANINE camera, architecture, lighting, and floor area. Twelve to fourteen distinct Indonesian adult passengers now occupy the central waiting area in a compact but safe cluster near the stair and escalator entrance. Their bodies remain individually separable, with visible heads and torsos and as many visible feet as possible. The crowd is dense and slow but there is no panic, violence, or person on the floor.
```

**Flow video prompt:**

```text
Use the supplied first and last frames without changing the camera or station geometry. A realistic fixed CCTV recording of the Level 2 mezzanine. From 0 to 2 seconds, six passengers move slowly with open space between them. From 2 to 5 seconds, additional distinct adult passengers enter gradually from the left and right edges and join the central waiting area. From 5 to 8 seconds, twelve to fourteen passengers form a compact slow-moving cluster; forward movement becomes visibly constrained and average walking speed drops, but everyone remains standing and calm. Preserve each person's clothing and anatomy. Do not make people appear from thin air.

[GLOBAL NEGATIVE CONSTRAINTS]
```

**Expected detector behavior:** the configured crowd polygon rises from roughly half capacity to at least configured capacity, then stays dense with low median normalized speed. Set capacity from the number of people YOLO actually detects, not the number requested in the prompt.

## Selection checklist

Keep a generated clip only when all answers are yes:

- Is the camera perfectly static for all eight seconds?
- Can YOLO detect the main people without severe body merging?
- Does ByteTrack keep the main subject's ID through the event?
- Are the floor boundary and event zone visually stable?
- Does exactly one intended event occur?
- Are start, confirmation, and end timestamps annotatable?
- Does the clip avoid identity claims, graphic harm, and criminal-intent language?

Generate two to four variations per event and keep only the easiest one for the model, not the most cinematic one.
