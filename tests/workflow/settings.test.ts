import { describe, it, expect, beforeEach } from "vitest";
import { loadSettings, saveSettings, DEFAULT_SETTINGS, type Settings } from "../../src/lib/settings";

describe("settings", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns defaults when storage is empty", () => {
    const s = loadSettings();
    expect(s).toEqual(DEFAULT_SETTINGS);
  });

  it("returns defaults when storage is corrupt JSON", () => {
    localStorage.setItem("grading-settings-v1", "{not valid");
    const s = loadSettings();
    expect(s).toEqual(DEFAULT_SETTINGS);
  });

  it("merges stored values with defaults", () => {
    const partial: Partial<Settings> = { apiKey: "sk-test" };
    localStorage.setItem("grading-settings-v1", JSON.stringify(partial));
    const s = loadSettings();
    expect(s.apiKey).toBe("sk-test");
    expect(s.baseUrl).toBe(DEFAULT_SETTINGS.baseUrl);
  });

  it("round-trips through saveSettings and loadSettings", () => {
    const s: Settings = { apiKey: "k", baseUrl: "https://x", modelName: "m" };
    saveSettings(s);
    expect(loadSettings()).toEqual(s);
  });
});
