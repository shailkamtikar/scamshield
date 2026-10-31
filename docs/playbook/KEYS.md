# Keys and accounts guide (Key Gates)

The build **pauses at each gate** and asks you for the items below. Never paste keys into chat, Git, screenshots or the frontend. Put them only in `backend/.env` locally (git-ignored) and in the Render dashboard later. Website menus change; if a button name differs, look for the closest one.

## Gate A - before Milestone 1.1: abuse.ch Auth-Key (URLhaus)
Needed for: URLhaus lookups and the URLhaus feed used in the benchmark.
1. Go to https://auth.abuse.ch and sign in (Google, GitHub, X or LinkedIn login is offered).
2. Open your profile / "Optional: Auth-Keys" area and click to create/show your **Auth-Key**.
3. Copy it into `backend/.env` as `URLHAUS_AUTH_KEY=...`.
OpenPhish needs no key (public community feed), so 1.1 can still start with it if this is delayed.

## Gate B - before Milestone 2.5: Safe Browsing and VirusTotal
**Google Safe Browsing API key** (free, non-commercial use only; checked against Google's docs, which now list Safe Browsing API **v5** with v4 still available)
1. Sign in at https://console.cloud.google.com. At the top-left click the project selector -> **New project** -> name it `scamshield` -> Create, and make sure it is the selected project.
2. Open the API page directly: https://console.cloud.google.com/apis/library/safebrowsing.googleapis.com and click **Enable**. (Or use the search bar at the top and type `safebrowsing.googleapis.com`; the console may label it "Safe Browsing API" - the service name is what matters.)
3. Open https://console.cloud.google.com/apis/credentials -> **+ Create credentials** -> **API key**. Copy the key.
4. Optional but recommended: click the key -> **API restrictions** -> Restrict key -> select the Safe Browsing API only -> Save.
5. Put it in `backend/.env` as `SAFE_BROWSING_API_KEY=...`.
If Google demands billing/credit card to enable it, stop and skip this key: the engine works without it (URLhaus, OpenPhish and VirusTotal still run), with slightly lower coverage. Verified in testing: your key works with the v4 Lookup API (`POST https://safebrowsing.googleapis.com/v4/threatMatches:find?key=...`, JSON), which correctly flags Google's official test pages. The v5 endpoint answered only in a binary format, so the backend uses v4.

**VirusTotal API key** (free: about 4 requests/min, 500/day)
1. Sign up at https://www.virustotal.com (free account) and confirm your email.
2. Click your profile icon -> **API key** -> copy.
3. Put it in `backend/.env` as `VIRUSTOTAL_API_KEY=...`.

Optional: PhishTank (registration is often closed; skip if unavailable).

## Optional but recommended: urlscan.io (the real browser sandbox)
Without this key ScamShield can only reuse earlier public scans of a site. With it, every unknown link is opened in an isolated browser on urlscan's computers.
1. Sign up at https://urlscan.io/user/signup (free) and confirm your email.
2. Open your profile -> Settings & API -> **New API key**, and copy it.
3. Put it in `backend/.env` as `URLSCAN_API_KEY=...`.
ScamShield submits scans as "unlisted" so links with personal tokens are not shown publicly.

## Chat assistant (second Gemini key)
The scam assistant uses its own key so chatting never uses the checker's quota. Create another key at https://aistudio.google.com/app/apikey (use a different Google project from the first key if you want a separate quota) and put it in `backend/.env` as `GEMINI_CHAT_API_KEY=...`. Without it the chat button is hidden.

## Gate C - before Milestone 9.1: hosting accounts
1. **Render** (https://render.com): sign up with your GitHub account, free tier only. Authorise access to `shailkamtikar/scamshield`.
2. **Vercel** (https://vercel.com): sign up with GitHub, import the repo, root directory `frontend`.
3. **UptimeRobot** (https://uptimerobot.com): free account; monitor created in 9.2.
4. You will paste the backend keys into the Render dashboard (Environment tab), never into the repo.

## Already needed from the start
- **Gemini API key**: https://aistudio.google.com/app/apikey -> Create API key -> `GEMINI_API_KEY` in `backend/.env`. Milestone 0.3 checks that it works and which model names it can use.

## If a key leaks
Revoke/regenerate it in the provider's console immediately, update `.env` and Render, then clean the Git history if it was committed.
