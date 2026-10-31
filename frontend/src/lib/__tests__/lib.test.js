import { describe, expect, it } from "vitest";
import { createSseParser } from "../api";
import { ageLabel, defang, shortUrl } from "../format";
import { getVerdict } from "../verdict";

describe("SSE parser", () => {
  it("parses events split across chunks and ignores heartbeats", () => {
    const events = [];
    const feed = createSseParser((e) => events.push(e));
    feed('event: stage\ndata: {"id":"ex');
    feed('tract","status":"start"}\n\n: ping\n\nevent: done\r\ndata: {"verdict":"SAFE"}\r\n\r\n');
    expect(events).toEqual([
      { event: "stage", data: { id: "extract", status: "start" } },
      { event: "done", data: { verdict: "SAFE" } },
    ]);
  });

  it("skips malformed blocks without throwing", () => {
    const events = [];
    createSseParser((e) => events.push(e))("event: stage\ndata: {oops\n\nevent: done\ndata: {}\n\n");
    expect(events).toHaveLength(1);
  });
});

describe("format helpers", () => {
  it("defangs links so they cannot be clicked", () => {
    expect(defang("https://evil.com/a")).toBe("hxxps://evil[.]com/a");
  });
  it("shortens long links", () => {
    expect(shortUrl("https://a.com/" + "x".repeat(100), 30)).toHaveLength(30);
  });
  it("describes domain age", () => {
    expect(ageLabel(0)).toBe("registered today");
    expect(ageLabel(400)).toContain("months");
    expect(ageLabel(4000)).toBe("10 years old");
    expect(ageLabel(null)).toBeNull();
  });
});

describe("verdict config", () => {
  it("falls back safely for unknown verdicts", () => {
    expect(getVerdict("???").word).toBe("Unverified");
    expect(getVerdict("DANGEROUS").word).toBe("Dangerous");
  });
});
