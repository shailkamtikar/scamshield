import { describe, expect, it } from "vitest";
import { diffAgainst, splitHost } from "../domains";

describe("splitHost", () => {
  it("separates what anyone can prepend from who owns the address", () => {
    expect(splitHost("hdfcbank.com.secure-login.info", "secure-login.info")).toEqual({ sub: "hdfcbank.com", owner: "secure-login.info" });
    expect(splitHost("sbi-kyc-update.top", "sbi-kyc-update.top")).toEqual({ sub: "", owner: "sbi-kyc-update.top" });
    expect(splitHost("1.hdfc.bank.in", "bank.in").owner).toBe("bank.in");
  });
  it("falls back to the whole host when the owner is unknown", () => {
    expect(splitHost("example.org", "").owner).toBe("example.org");
  });
});

describe("diffAgainst", () => {
  const changed = (real, fake) => diffAgainst(real, fake).filter((s) => s.kind === "diff").map((s) => s.text).join("");
  it("marks an extra letter", () => expect(changed("google.com", "gooogle.com")).toBe("o"));
  it("marks swapped look-alike letters (rn for m)", () => expect(changed("amazon.in", "arnazon.in")).toBe("rn"));
  it("marks added words while keeping the real name", () => {
    const parts = diffAgainst("sbi.co.in", "sbi-kyc-update.top");
    expect(parts[0]).toEqual({ kind: "same", text: "sbi" });
    expect(changed("sbi.co.in", "sbi-kyc-update.top").length).toBeGreaterThanOrEqual(8);
  });
  it("keeps the fake address intact", () => expect(diffAgainst("a.com", "ab.com").map((s) => s.text).join("")).toBe("ab.com"));
});
