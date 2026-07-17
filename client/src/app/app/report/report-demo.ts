import type { PassengerAttributes } from "@/components/passenger-characteristic-form";

export const DEMO_LOADING_STEPS = [
  "Structuring report details",
  "Searching station cameras",
  "Building evidence timeline",
] as const;

export const DEMO_REPORT: {
  description: string;
  location: string;
  attributes: PassengerAttributes;
  videoSrc: string;
} = {
  description:
    "Seorang penumpang dewasa berjaket abu-abu, bercelana gelap, dan membawa ransel hitam bergerak cepat menuju Exit D sekitar pukul 17.10.",
  location: "Lantai 1 Concourse menuju Exit D",
  attributes: {
    gender: "Unknown",
    age_group: "Adult",
    upper_clothing: "grey jacket",
    lower_clothing: "dark trousers",
    accessories: "black backpack",
  },
  videoSrc: "/videos/feature-2/evidence-timeline.mp4",
};

export function isDemoShortcut(event: { altKey: boolean; key: string }): boolean {
  return event.altKey && event.key.toLowerCase() === "d";
}

export function shouldSubmitDemo(
  event: { key: string; shiftKey: boolean; isComposing?: boolean },
  armed: boolean,
): boolean {
  return armed && event.key === "Enter" && !event.shiftKey && !event.isComposing;
}

export function getSubmissionMode(armed: boolean): "api" | "demo" {
  return armed ? "demo" : "api";
}
