import { describe, expect, it } from "vitest";
import { reasonText } from "../../components/Impersonation";
import { closestReal } from "../../components/DiffAddress";

describe("real vs fake wording", () => {
  const base = { brand: "HSBC", owner: "hbsc-bank.com", kind: "link" };
  it("says something different for each way of imitating", () => {
    const reasons = ["BRAND_LOOKALIKE", "BRAND_COMBOSQUAT", "BRAND_IN_DOMAIN", "BRAND_IN_SUBDOMAIN_OR_PATH", "BRAND_MISMATCH_LINK", "SENDER_LOOKALIKE", "SENDER_DISPLAY_NAME_MISMATCH"];
    const texts = reasons.map((reason) => reasonText({ ...base, reason }));
    expect(new Set(texts).size).toBe(reasons.length);
    for (const t of texts) expect(t).toContain("HSBC");
  });
  it("names the owner when it matters", () => {
    expect(reasonText({ ...base, reason: "BRAND_IN_SUBDOMAIN_OR_PATH", owner: "secure-login.info" })).toContain("secure-login.info");
  });
  it("falls back to a safe sentence for an unknown reason", () => {
    expect(reasonText({ ...base, reason: "SOMETHING_NEW" })).toContain("does not belong to HSBC");
    expect(reasonText({ ...base, reason: "SOMETHING_NEW", kind: "sender" })).toContain("sender");
  });
});

describe("closestReal", () => {
  it("picks the real address the fake one most resembles", () => {
    expect(closestReal(["hsbc.com", "hsbc.co.in"], "hbsc-bank.co.in")).toBe("hsbc.co.in");
    expect(closestReal(["amazon.in", "amazon.com"], "arnazon.in")).toBe("amazon.in");
  });
  it("works with a single address", () => expect(closestReal(["sbi.co.in"], "x.top")).toBe("sbi.co.in"));
});
