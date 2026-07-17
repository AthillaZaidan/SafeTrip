export const PIPELINE_STAGES = ["Detect", "Track", "Assess", "Respond"] as const;

export type PipelineClip = {
  id: string;
  event: string;
  location: string;
  src: string;
  description: string;
  signal: string;
  stages: string[];
};

export const pipelineClips: PipelineClip[] = [
  {
    id: "crowd",
    event: "Crowd compression",
    location: "Tanah Abang Platform 2 · Camera 02",
    src: "/videos/feature-1-processed/dense-platform-crowd.mp4",
    description:
      "Density rises while average movement slows inside a monitored concourse zone.",
    signal: "Elevated density",
    stages: [...PIPELINE_STAGES],
  },
  {
    id: "person-down",
    event: "Possible person down",
    location: "Tanah Abang Link Corridor · Camera 01",
    src: "/videos/feature-1-processed/passenger-fall-corridor.mp4",
    description:
      "A horizontal posture and low movement persist long enough to require operator review.",
    signal: "Review required",
    stages: [...PIPELINE_STAGES],
  },
  {
    id: "restricted-zone",
    event: "Restricted zone intrusion",
    location: "Tanah Abang Ticket Gates · Camera 01",
    src: "/videos/feature-1-processed/ticket-gate-flow.mp4",
    description:
      "Persistent entries inside the configured restricted zone are surfaced for operator review.",
    signal: "9 events detected",
    stages: [...PIPELINE_STAGES],
  },
];
