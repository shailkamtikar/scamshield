"""
Generate the SMS benchmark (data/benchmark/messages.csv): India-focused scam
and genuine messages built from templates with randomised slots.
"""

import csv
import random
from pathlib import Path

from app.intel.registry_data import ADMIN_WORDS

ROOT = Path(__file__).resolve().parents[2]
rng = random.Random(7)

BANKS = [("SBI", "sbi.co.in", "sbi"), ("HDFC Bank", "hdfcbank.com", "hdfcbank"), ("ICICI Bank", "icicibank.com", "icicibank"),
         ("Axis Bank", "axisbank.com", "axisbank"), ("Kotak", "kotak.com", "kotak"), ("PNB", "pnbindia.in", "pnb"),
         ("Bank of Baroda", "bankofbaroda.in", "bankofbaroda"), ("Canara Bank", "canarabank.com", "canarabank")]
BRANDS = BANKS + [("Amazon", "amazon.in", "amazon"), ("Flipkart", "flipkart.com", "flipkart"), ("Paytm", "paytm.com", "paytm"),
                  ("PhonePe", "phonepe.com", "phonepe"), ("Netflix", "netflix.com", "netflix"), ("Jio", "jio.com", "jio"),
                  ("Airtel", "airtel.in", "airtel"), ("Microsoft", "microsoft.com", "microsoft"), ("Google", "google.com", "google"),
                  ("India Post", "indiapost.gov.in", "indiapost"), ("Income Tax Department", "incometax.gov.in", "incometax"),
                  ("Aadhaar", "uidai.gov.in", "uidai"), ("IRCTC", "irctc.co.in", "irctc"), ("DTDC", "dtdc.in", "dtdc"),
                  ("Blue Dart", "bluedart.com", "bluedart"), ("Swiggy", "swiggy.com", "swiggy"), ("Zomato", "zomato.com", "zomato")]
ADMIN = ["kyc", "verify", "update", "secure", "login", "refund", "support", "care", "reward", "claim", "pay", "alert", "service"]
TLDS = ["com", "in", "top", "xyz", "info", "online", "co.in", "net", "click", "site", "live", "shop"]
NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Neha", "Karan", "Pooja"]


def fake_link(brand_label):
    kind = rng.choice(["combo", "combo", "typo", "gib", "short"])
    tld = rng.choice(TLDS)
    if kind == "combo":
        return f"{rng.choice(['http', 'https'])}://{brand_label}-{rng.choice(ADMIN)}.{tld}/{rng.choice(['', 'login', 'kyc', 'v'])}"
    if kind == "typo":
        i = rng.randrange(1, max(2, len(brand_label) - 1))
        t = brand_label[:i] + brand_label[i + 1:] if rng.random() < 0.5 else brand_label.replace("o", "0", 1)
        return f"https://{t}-{rng.choice(ADMIN)}.{tld}"
    if kind == "gib":
        return "https://" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(rng.randint(8, 13))) + f".{rng.choice(['top','xyz','click','cfd','icu'])}/" + rng.choice(["", "a", "login"])
    return rng.choice(["bit.ly/", "tinyurl.com/", "cutt.ly/", "rb.gy/"]) + "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(7))


def phone():
    return rng.choice("6789") + "".join(rng.choice("0123456789") for _ in range(9))


def amount():
    return rng.choice(["1,499", "2,000", "4,850", "9,999", "25,000", "49,500", "1.5 lakh"])


SCAM = [
    ("kyc_block", "Dear customer, your {b} account will be blocked today. Update your KYC immediately: {l}"),
    ("kyc_block", "URGENT: {b} KYC pending. Your account is suspended. Complete verification now {l} or call {p}"),
    ("kyc_block", "{b} Alert: PAN not linked. Account will be deactivated in 24 hours. Click {l} to update details."),
    ("otp_theft", "Dear {n}, a charge of Rs {a} is pending on your {b} card. Share the OTP you received to cancel it."),
    ("otp_theft", "{b}: we detected a suspicious login. To secure your account reply with your OTP and CVV immediately."),
    ("otp_theft", "Your {b} reward points worth Rs {a} expire today. Redeem now {l} and enter your card number and PIN."),
    ("electricity", "Dear consumer, your electricity connection will be disconnected tonight at 9:30 PM due to unpaid bill. Call {p} immediately."),
    ("electricity", "Electricity bill not updated. Power will be cut. Contact officer on WhatsApp {p} now."),
    ("courier", "{b}: your parcel could not be delivered. Pay Rs 25 redelivery fee: {l}"),
    ("courier", "Your package is held at customs. Clear the fee of Rs {a} within 24 hours: {l}"),
    ("courier", "Dear {n}, your {b} courier is stuck due to incomplete address. Update address at {l}"),
    ("job", "Hi {n}, part-time job offer! Earn Rs {a} per day by simple tasks. Join our Telegram group now: {l}"),
    ("job", "Work from home opportunity. Like and subscribe videos, salary Rs 5000 daily. WhatsApp {p} to start."),
    ("job", "HR from {b}: you are selected for data entry job work from home, earn 3000 per day. Contact {p}"),
    ("lottery", "Congratulations {n}! You have won Rs {a} in the {b} lucky draw. Claim your prize: {l}"),
    ("lottery", "KBC lottery winner! Your number won 25 lakh. Pay processing fee to claim. Call {p}"),
    ("lottery", "You are the lucky winner of an iPhone from {b}. Claim now {l} limited time only"),
    ("refund", "Income Tax refund of Rs {a} approved. Submit your bank details at {l} to receive the amount."),
    ("refund", "{b} refund of Rs {a} is pending. Verify your account now {l} to credit the money."),
    ("refund", "You are eligible for a refund of Rs {a}. Scan this QR code to receive money in your account."),
    ("arrest", "This is CBI officer. A parcel in your name contains illegal items. You will face arrest. Call {p} immediately."),
    ("arrest", "Digital arrest notice: your Aadhaar is linked to money laundering. Contact police on {p} now or face legal action."),
    ("arrest", "Narcotics bureau: case registered against your number. Pay fine immediately to avoid arrest. {p}"),
    ("upi_collect", "Sir your payment of Rs {a} is stuck. Approve the collect request and enter your UPI PIN to receive the money."),
    ("upi_collect", "I will send you Rs {a}. Scan this QR and enter PIN to receive the payment."),
    ("remote", "To fix your {b} account issue, install AnyDesk and share the 9 digit code with our executive."),
    ("remote", "{b} support: download TeamViewer QuickSupport so we can process your refund."),
    ("apk", "{b}: new rewards available! Download the app from this link {l}/{b}.apk and login."),
    ("apk", "Your {b} account update is available. Install the app: {l}/update.apk"),
    ("investment", "Join our VIP trading group, guaranteed returns of 40% weekly. Whatsapp {p} for stock tips."),
    ("investment", "Double your money in 30 days with crypto trading platform. Join now {l}"),
    ("sim", "Your SIM will be blocked in 2 hours. KYC not done. Call {p} to avoid disconnection."),
    ("sim", "{b}: your number will be deactivated. Update Aadhaar now {l}"),
    ("fastag", "Your FASTag is blocked. Recharge immediately {l} to avoid penalty."),
    ("challan", "Traffic e-challan of Rs 500 pending. Pay now to avoid court notice: {l}"),
    ("loan", "Pre-approved loan of Rs {a} in 5 minutes without documents. Click {l} to get instant cash."),
    ("bank_call", "{b}: unusual activity on your account. Call {p} urgently and share your debit card details to block it."),
]
GENUINE = [
    ("txn_alert", "Rs {a2} debited from A/c XX{d4} on {dt} to VPA store@okaxis. UPI Ref {ref}. Avl Bal Rs {a}. - {b}"),
    ("txn_alert", "Your a/c no. XXXX{d4} is credited by Rs {a2} on {dt}. Avl bal Rs {a}. If not done by you call 1800 1234 - {b}"),
    ("otp", "{o} is your OTP for the transaction of Rs {a2} at Amazon. Do not share this OTP with anyone. - {b}"),
    ("otp", "Your OTP for login is {o}. Valid for 10 minutes. Never share it with anyone, {b} will never ask for it."),
    ("otp", "{o} is the verification code for your Swiggy account. Do not share it."),
    ("delivery", "Your {b} order has been shipped and will arrive by {dt}. Track: https://www.{d}/track"),
    ("delivery", "Hi {n}, your package is out for delivery today. Track it at https://www.{d}"),
    ("bill", "Dear customer, your Jio bill of Rs {a2} is generated. Pay by {dt} via the MyJio app."),
    ("bill", "Your Airtel postpaid bill of Rs {a2} is due on {dt}. Pay on https://www.airtel.in"),
    ("ott", "Your Netflix subscription renews on {dt}. Manage it anytime at https://www.netflix.com/account"),
    ("appt", "Reminder: your appointment with Dr. Mehta is tomorrow at 11:30 AM. Reply YES to confirm."),
    ("appt", "Hi {n}, your haircut is booked for Saturday 4 PM. See you!"),
    ("friend", "Hey {n}, check out this article https://www.thehindu.com/news/national/ it's interesting"),
    ("friend", "Dinner at 8? Here's the menu https://www.zomato.com/mumbai"),
    ("friend", "Movie tickets booked https://in.bookmyshow.com/ see you there"),
    ("friend", "Look at the new phone https://www.flipkart.com/ I want to buy it, thoughts?"),
    ("friend", "Send me the notes from today's class, I'll pay for the chai tomorrow"),
    ("friend", "Mom asked if you are coming for Diwali. Please call her when you are free."),
    ("work", "Your interview is scheduled tomorrow at 3 PM. Join the Zoom meeting: https://zoom.us/j/123456789"),
    ("work", "Meeting moved to 4pm, link: https://meet.google.com/abc-defg-hij"),
    ("advisory", "{b} advisory: Never share your OTP, PIN or password with anyone, including bank staff. Stay alert against fraud."),
    ("advisory", "Dear customer, beware of fake calls. {b} will never ask for your card number or CVV. Report fraud at cybercrime.gov.in"),
    ("govt", "Your Aadhaar download request is successful. Visit https://myaadhaar.uidai.gov.in to view."),
    ("govt", "ITR filed successfully for AY 2025-26. Check status at https://www.incometax.gov.in"),
    ("railway", "PNR {ref}: Your train 12951 departs on {dt}. Have a safe journey. - IRCTC"),
    ("hard_neg", "Urgent: team meeting at 5 PM today about the project deadline. Please be on time."),
    ("hard_neg", "Your account statement for {dt} is ready. Log in to the official app to view it."),
    ("hard_neg", "We have received your payment of Rs {a2}. Thank you for shopping with us!"),
    ("hard_neg", "Your refund of Rs {a2} has been processed and will reflect in 5-7 working days. Order {ref}. - Flipkart"),
    ("hard_neg", "Verify your email by clicking the button in the email we sent from noreply@github.com"),
    ("hard_neg", "Last date to submit the assignment is tomorrow. Do it immediately after the lecture."),
]


def render(tpl: str, brand, link_real=False):
    b, domain, label = brand
    d4 = "".join(rng.choice("0123456789") for _ in range(4))
    return tpl.format(
        b=b, l=fake_link(label), p=phone(), n=rng.choice(NAMES), a=amount(), a2=rng.choice(["250", "1,200", "5,000", "340.50"]),
        d4=d4, dt=rng.choice(["12-Mar", "05-Apr", "18-Jun", "27-Sep"]), ref="".join(rng.choice("0123456789") for _ in range(9)),
        o="".join(rng.choice("0123456789") for _ in range(6)), d=domain,
    )


def main():
    rows = []
    for _ in range(380):
        cat, tpl = rng.choice(SCAM)
        text = render(tpl, rng.choice(BRANDS))
        if rng.random() < 0.15:
            text = text.replace("account", "a/c") if rng.random() < 0.5 else text.upper()
        rows.append((text, "scam", cat, "DANGEROUS_OR_SUSPICIOUS"))
    for _ in range(380):
        cat, tpl = rng.choice(GENUINE)
        rows.append((render(tpl, rng.choice(BRANDS)), "genuine", cat, "SAFE"))
    seen, out = set(), []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0])
            out.append(r)
    path = ROOT / "data" / "benchmark" / "messages.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["text", "label", "category", "expected"])
        w.writerows(out)
    print(len(out), "messages written")


if __name__ == "__main__":
    main()
