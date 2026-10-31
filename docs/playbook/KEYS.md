# Keys and accounts guide (Key Gates)

The build **pauses at each gate** and asks you for the items below. Never paste keys into chat, Git, screenshots or the frontend. Put them only in `backend/.env` locally (git-ignored) and in the Render dashboard later. Website menus change; if a button name differs, look for the closest one.

## Gate A - before Milestone 1.1: abuse.ch Auth-Key (URLhaus)
Needed for: URLhaus lookups and the URLhaus feed used in the benchmark.
1. Go to https://auth.abuse.ch and sign in (Google, GitHub, X or LinkedIn login is offered).
2. Open your profile / "Optional: Auth-Keys" area and click to create/show your **Auth-Key**.
3. Copy it into `backend/.env` as `URLHAUS_AUTH_KEY=...`.
OpenPhish needs no key (public community feed), so 1.1 can still start with it if this is delayed.

## Gate B - before Milestone 2.5: Safe Browsing and VirusTotal
**Google Safe Browsing API key** (free, non-commercial)
1. Open https://console.cloud.google.com and sign in; create a project named e.g. `scamshield`.
2. APIs & Services -> Library -> search **Safe Browsing API** -> Enable.
3. APIs & Services -> Credentials -> Create credentials -> **API key**.
4. Click the key -> restrict it to "Safe Browsing API" only (optionally add your Render IP later).
5. Put it in `backend/.env` as `SAFE_BROWSING_API_KEY=...`.
No billing should be required for Safe Browsing; if Google asks for a card for the project, stop and tell me.

**VirusTotal API key** (free: about 4 requests/min, 500/day)
1. Sign up at https://www.virustotal.com (free account) and confirm your email.
2. Click your profile icon -> **API key** -> copy.
3. Put it in `backend/.env` as `VIRUSTOTAL_API_KEY=...`.

Optional: PhishTank (registration is often closed; skip if unavailable).

## Gate C - before Milestone 9.1: hosting accounts
1. **Render** (https://render.com): sign up with your GitHub account, free tier only. Authorise access to `shailkamtikar/scamshield`.
2. **Vercel** (https://vercel.com): sign up with GitHub, import the repo, root directory `frontend`.
3. **UptimeRobot** (https://uptimerobot.com): free account; monitor created in 9.2.
4. You will paste the backend keys into the Render dashboard (Environment tab), never into the repo.

## Already needed from the start
- **Gemini API key**: https://aistudio.google.com/app/apikey -> Create API key -> `GEMINI_API_KEY` in `backend/.env`. Milestone 0.3 checks that it works and which model names it can use.

## If a key leaks
Revoke/regenerate it in the provider's console immediately, update `.env` and Render, then clean the Git history if it was committed.
