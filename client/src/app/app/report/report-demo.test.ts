import { describe, expect, test } from "bun:test";

type DemoModule = {
  DEMO_LOADING_STEPS: readonly string[];
  DEMO_REPORT: {
    description: string;
    location: string;
    attributes: Record<string, string>;
    videoSrc: string;
  };
  isDemoShortcut: (event: { altKey: boolean; key: string }) => boolean;
  shouldSubmitDemo: (
    event: { key: string; shiftKey: boolean; isComposing?: boolean },
    armed: boolean,
  ) => boolean;
  getSubmissionMode: (armed: boolean) => "api" | "demo";
};

async function loadDemoModule(): Promise<DemoModule | null> {
  try {
    const path = "./report-demo";
    return (await import(path)) as DemoModule;
  } catch {
    return null;
  }
}

describe("Feature 2 report demo accelerator", () => {
  test("maps Alt+D to the controlled Exit D evidence scenario", async () => {
    const demoApi = await loadDemoModule();

    expect(demoApi).not.toBeNull();
    expect(demoApi!.isDemoShortcut({ altKey: true, key: "d" })).toBeTrue();
    expect(demoApi!.DEMO_REPORT).toEqual({
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
    });
    expect(demoApi!.DEMO_LOADING_STEPS).toEqual([
      "Structuring report details",
      "Searching station cameras",
      "Building evidence timeline",
    ]);
  });

  test("uses plain Enter only after the demo is armed", async () => {
    const demoApi = await loadDemoModule();

    expect(demoApi).not.toBeNull();
    expect(demoApi!.shouldSubmitDemo({ key: "Enter", shiftKey: false }, true)).toBeTrue();
    expect(demoApi!.shouldSubmitDemo({ key: "Enter", shiftKey: true }, true)).toBeFalse();
    expect(demoApi!.shouldSubmitDemo({ key: "Enter", shiftKey: false }, false)).toBeFalse();
    expect(demoApi!.getSubmissionMode(false)).toBe("api");
    expect(demoApi!.getSubmissionMode(true)).toBe("demo");
  });
});
