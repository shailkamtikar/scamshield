import { describe, expect, it } from "vitest";
import { AFTER_A_SCAM, HELPLINE, RESOURCE_GROUPS } from "../resources";
import { CATEGORIES, EXAMPLES, SIGNS, SIGN_MESSAGE } from "../scams";
import { toneOf } from "../../lib/verdict";

describe("resource library", () => {
  const items = RESOURCE_GROUPS.flatMap((g) => g.items);
  it("only points to secure, parseable links and names the organisation behind each", () => {
    expect(items.length).toBeGreaterThanOrEqual(8);
    for (const r of items) {
      expect(() => new URL(r.href)).not.toThrow();
      expect(new URL(r.href).protocol).toBe("https:");
      expect(r.org.length).toBeGreaterThan(2);
    }
  });
  it("has no duplicate links and includes the national helpline and portal", () => {
    expect(new Set(items.map((r) => r.href)).size).toBe(items.length);
    expect(HELPLINE.number).toBe("1930");
    expect(items.some((r) => r.href === "https://cybercrime.gov.in")).toBe(true);
    expect(AFTER_A_SCAM).toHaveLength(4);
  });
});

describe("education content", () => {
  it("every phrase in the sample message maps to a defined warning sign", () => {
    const ids = new Set(SIGNS.map((s) => s.id));
    const used = SIGN_MESSAGE.filter((p) => p.s).map((p) => p.s);
    expect(new Set(used)).toEqual(ids);
  });
  it("covers the nine scam types and four examples, each with reasons", () => {
    expect(CATEGORIES).toHaveLength(9);
    expect(EXAMPLES).toHaveLength(4);
    for (const e of EXAMPLES) expect(e.flags.length).toBeGreaterThanOrEqual(3);
  });
});

describe("page tint", () => {
  it("maps results to the five colours the design uses", () => {
    expect(toneOf({ verdict: "SAFE", assurance: "verified" })).toBe("SAFE");
    expect(toneOf({ verdict: "SAFE", assurance: "promotion" })).toBe("PROMO");
    expect(toneOf({ verdict: "SAFE", assurance: "spam" })).toBe("SPAM");
    expect(toneOf({ verdict: "SUSPICIOUS" })).toBe("SUSPICIOUS");
    expect(toneOf({ verdict: "COULD_NOT_VERIFY" })).toBe("COULD_NOT_VERIFY");
    expect(toneOf(undefined)).toBeUndefined();
  });
});
