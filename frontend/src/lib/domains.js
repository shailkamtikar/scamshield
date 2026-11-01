/** Split a host into the part anyone can add in front, and the part that tells you who owns the address. */
export function splitHost(host = "", registrable = "") {
  const h = host.toLowerCase();
  const r = registrable.toLowerCase();
  if (!r || !h.endsWith(r)) return { sub: "", owner: h };
  return { sub: h.slice(0, h.length - r.length).replace(/\.$/, ""), owner: r };
}

/**
 * Character-level comparison of a fake address against the real one (longest common subsequence).
 * Returns the fake address as segments, each marked `same` or `diff` (a letter that is added or changed).
 */
export function diffAgainst(real, fake) {
  const a = real.toLowerCase();
  const b = fake.toLowerCase();
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const marks = new Array(b.length).fill("diff");
  let i = 0;
  let j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { marks[j] = "same"; i += 1; j += 1; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) i += 1;
    else j += 1;
  }
  const out = [];
  for (let k = 0; k < b.length; k += 1) {
    const last = out[out.length - 1];
    if (last && last.kind === marks[k]) last.text += fake[k];
    else out.push({ kind: marks[k], text: fake[k] });
  }
  return out;
}
