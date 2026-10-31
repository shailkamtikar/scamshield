"""
Build the URL benchmark (data/benchmark/urls.csv).

Bad links : OpenPhish feed + URLhaus recent + synthetic scam patterns
Safe links: Tranco sites OUTSIDE the engine's trusted top-50k (so the engine
            has not seen them) + curated real sites + login-style paths on
            real sites (false-positive stress test)

Nothing here visits any link. It only reads text feeds and writes a CSV.
"""

import csv
import json
import random
import re
import zlib
from pathlib import Path

import httpx

from app.config import settings
from app.intel.registry_data import ADMIN_WORDS, REGISTRY, RISKY_TLDS
from app.intel.trust import brand_tokens, official_index

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "benchmark"
rng = random.Random(42)

TRUSTED_TOP = 50_000


def read_openphish() -> list[str]:
    path = RAW / "openphish.txt"
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []


def fetch_urlhaus(limit=400) -> list[str]:
    if not settings.urlhaus_auth_key:
        return []
    try:
        r = httpx.get(
            f"https://urlhaus-api.abuse.ch/v1/urls/recent/limit/{limit}/",
            headers={"Auth-Key": settings.urlhaus_auth_key}, timeout=30,
        )
        return [u["url"] for u in r.json().get("urls", []) if u.get("url_status") == "online" or True]
    except Exception:
        return []


def synthetic_bad(n_each=45) -> list[tuple[str, str]]:
    brands = []
    for entries in REGISTRY.values():
        for name, domains in entries:
            label = re.sub(r"[^a-z0-9]", "", domains[0].split(".")[0].lower())
            if len(label) >= 4:
                brands.append((name, label))
    admin = sorted(w for w in ADMIN_WORDS if len(w) >= 4 and w.isalpha())
    tlds = sorted(RISKY_TLDS) + ["com", "in", "net", "info", "co.in", "org"]
    out = []

    def tld():
        return rng.choice(tlds)

    for _ in range(n_each):  # combosquat
        _, b = rng.choice(brands)
        w = rng.choice(admin)
        host = rng.choice([f"{b}-{w}", f"{w}-{b}", f"{b}-{w}-{rng.choice(admin)}", f"{b}{w}"])
        out.append((f"{rng.choice(['http','https'])}://{host}.{tld()}/{rng.choice(['login','verify','kyc','update','','secure'])}", "combosquat"))
    for _ in range(n_each):  # typosquat
        _, b = rng.choice(brands)
        kind = rng.choice(["swap", "digit", "drop", "dup", "rn"])
        i = rng.randrange(1, len(b) - 1)
        if kind == "swap":
            t = b[:i] + b[i + 1] + b[i] + b[i + 2:]
        elif kind == "digit":
            t = b.replace("o", "0", 1) if "o" in b else b.replace("l", "1", 1) if "l" in b else b[:i] + "1" + b[i + 1:]
        elif kind == "drop":
            t = b[:i] + b[i + 1:]
        elif kind == "dup":
            t = b[:i] + b[i] + b[i:]
        else:
            t = b.replace("m", "rn", 1) if "m" in b else b + "s"
        if t == b:
            t = b + "x"
        suffix = rng.choice(["", "-login", "-secure", "-online"])
        out.append((f"https://{t}{suffix}.{rng.choice(['com','in','net','co.in','online'])}/", "typosquat"))
    for _ in range(n_each):  # gibberish
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(8, 16)))
        out.append((f"{rng.choice(['http','https'])}://{s}.{tld()}/{rng.choice(['', 'login', 'a/b'])}", "gibberish"))
    for _ in range(n_each // 2):  # raw ip
        ip = ".".join(str(rng.randint(11, 220)) for _ in range(4))
        out.append((f"http://{ip}/{rng.choice(['login','bank/verify','secure/index.php'])}", "raw_ip"))
    for _ in range(n_each):  # brand in subdomain / path of foreign host
        _, b = rng.choice(brands)
        host = f"{rng.choice(['secure','login','account','www'])}.{b}.com.{rng.choice(['secure-id','verify-now','clientarea'])}.{tld()}"
        out.append((f"https://{host}/", "brand_subdomain"))
    for _ in range(n_each // 2):
        _, b = rng.choice(brands)
        out.append((f"https://{rng.choice(['mysite','shop24','cdn-files','portal'])}{rng.randint(10,99)}.{rng.choice(['weebly.com','github.io','pages.dev','netlify.app'])}/{b}/login", "platform_brand_path"))
    for _ in range(n_each // 3):  # userinfo trick
        _, b = rng.choice(brands)
        out.append((f"https://www.{b}.com@{rng.choice(['verify','secure'])}-{rng.choice(['id','pay','kyc'])}.{tld()}/", "userinfo"))
    return out


CURATED_SAFE = """
https://www.iitb.ac.in/ https://www.iisc.ac.in/ https://www.nitt.edu/ https://www.du.ac.in/ https://www.jnu.ac.in/
https://www.isro.gov.in/ https://www.drdo.gov.in/ https://www.mea.gov.in/ https://www.mha.gov.in/ https://www.meity.gov.in/
https://www.hindustantimes.com/ https://www.ndtv.com/ https://www.thehindu.com/ https://indianexpress.com/ https://www.news18.com/
https://www.moneycontrol.com/ https://economictimes.indiatimes.com/ https://www.livemint.com/ https://www.business-standard.com/
https://www.irctc.co.in/nget/train-search https://www.flipkart.com/account/login https://www.amazon.in/ap/signin https://accounts.google.com/signin
https://login.microsoftonline.com/ https://www.paypal.com/signin https://www.linkedin.com/login https://www.instagram.com/accounts/login/
https://www.facebook.com/login/ https://twitter.com/i/flow/login https://github.com/login https://www.netflix.com/login
https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC https://www.youtube.com/watch?v=dQw4w9WgXcQ https://music.youtube.com/ https://www.jiosaavn.com/
https://netbanking.hdfcbank.com/netbanking/ https://retail.onlinesbi.sbi/retail/login.htm https://infinity.icicibank.com/ https://retail.axisbank.co.in/
https://www.paytm.com/ https://phonepe.com/ https://pay.google.com/about/ https://www.npci.org.in/ https://www.bhimupi.org.in/
https://www.incometax.gov.in/iec/foportal/ https://www.uidai.gov.in/en/ https://myaadhaar.uidai.gov.in/ https://www.epfindia.gov.in/ https://www.digilocker.gov.in/
https://www.zomato.com/ https://www.swiggy.com/ https://www.myntra.com/ https://www.nykaa.com/ https://www.bigbasket.com/
https://www.makemytrip.com/ https://www.goibibo.com/ https://www.redbus.in/ https://www.olacabs.com/ https://www.uber.com/in/en/
https://www.wikipedia.org/ https://en.wikipedia.org/wiki/India https://www.bbc.com/news https://www.cnn.com/ https://stackoverflow.com/questions
https://www.python.org/ https://nodejs.org/ https://react.dev/ https://developer.mozilla.org/ https://docs.docker.com/
https://www.coursera.org/ https://www.udemy.com/ https://www.khanacademy.org/ https://nptel.ac.in/ https://swayam.gov.in/
https://www.apple.com/in/ https://www.samsung.com/in/ https://www.mi.com/in/ https://www.oneplus.in/ https://www.hp.com/in-en/home.html
https://www.airtel.in/ https://www.jio.com/ https://www.myvi.in/ https://www.bsnl.co.in/ https://www.tataplay.com/
https://www.zerodha.com/ https://groww.in/ https://upstox.com/ https://www.nseindia.com/ https://www.bseindia.com/
https://www.naukri.com/ https://www.indeed.com/ https://internshala.com/ https://www.glassdoor.co.in/ https://www.linkedin.com/jobs/
https://www.practo.com/ https://www.apollopharmacy.in/ https://pharmeasy.in/ https://www.1mg.com/ https://www.lenskart.com/
https://www.cleartax.in/ https://www.policybazaar.com/ https://www.bookmyshow.com/ https://www.dream11.com/ https://www.99acres.com/
https://www.mozilla.org/ https://www.cloudflare.com/ https://aws.amazon.com/ https://azure.microsoft.com/ https://cloud.google.com/
https://www.bankofamerica.com/ https://www.chase.com/ https://www.wellsfargo.com/ https://www.barclays.co.uk/ https://www.hsbc.co.in/
https://www.ola.in/ https://www.oyorooms.com/ https://www.tripadvisor.in/ https://www.booking.com/ https://www.airbnb.co.in/
""".split()

LOGIN_PATHS = ["/login", "/account/verify", "/secure/signin", "/update-profile", "/customer-support", "/my-account/password-reset", "/kyc/update", "/payment/confirm"]


def tranco_unseen(n=450) -> list[str]:
    zpath = RAW / "top-1m.csv"
    rows = []
    with open(zpath, newline="", encoding="utf-8") as fh:
        for rank, domain in csv.reader(fh):
            r = int(rank)
            if r > TRUSTED_TOP and r <= 400_000:
                rows.append(domain)
    off = official_index()
    rows = [d for d in rows if d not in off and d.split(".")[-1] not in RISKY_TLDS]
    rng.shuffle(rows)
    return [f"https://{d}/" for d in rows[:n]]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, str, str, str]] = []  # url,label,category,source

    for u in read_openphish():
        rows.append((u, "phish", "phishing_feed", "openphish"))
    for u in fetch_urlhaus():
        rows.append((u, "phish", "malware_feed", "urlhaus"))
    for u, cat in synthetic_bad():
        rows.append((u, "phish", cat, "synthetic"))

    unseen = tranco_unseen()
    for u in unseen:
        rows.append((u, "safe", "popular_unseen", "tranco_50k_400k"))
    for u in CURATED_SAFE:
        rows.append((u, "safe", "curated_real", "curated"))
    for u in rng.sample(unseen, 120):
        base = u.rstrip("/")
        rows.append((base + rng.choice(LOGIN_PATHS), "safe", "login_path_on_real_site", "tranco+path"))

    seen, final = set(), []
    for url, label, cat, src in rows:
        if url in seen:
            continue
        seen.add(url)
        split = "test" if (zlib.crc32(url.encode()) % 5 == 0) else "train"
        final.append((url, label, cat, src, split))

    with open(OUT / "urls.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "label", "category", "source", "split"])
        w.writerows(final)

    from collections import Counter
    print(Counter((r[1], r[2]) for r in final))
    print("total", len(final))


if __name__ == "__main__":
    main()
