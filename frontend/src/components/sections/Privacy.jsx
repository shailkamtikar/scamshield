import { FadeUp, SectionHead } from "../ui/Reveal";

/** Every line here is something the code does. Update this list whenever the data flow changes. */
const STAYS = [
  ["No account, no cookies", "Nothing to sign up for, and the site sets no cookies and runs no analytics or ad trackers."],
  ["Nothing saved", "We do not keep what you check. Server logs record only a request ID, the address called, the status and how long it took, never the message."],
  ["Screenshots stay in memory", "An uploaded image is read while the check runs and is not written to disk."],
  ["QR codes are read on your phone", "The camera feed is decoded in your browser. Only the text inside the code is sent, and the link inside is never opened by you or by us on your device."],
  ["Your report stays with you", "The PDF report is built in your browser."],
];

const LEAVES = [
  ["Google Gemini", "The message text, to write the plain-language explanation and give a second reading of the wording."],
  ["Google Safe Browsing, VirusTotal, URLhaus", "Each link, to see whether it is already known as dangerous."],
  ["urlscan.io", "Links we cannot otherwise judge may be opened in its isolated browser. These scans are submitted as unlisted, and urlscan keeps its own scan records."],
  ["Page checks from our server", "To read a page we fetch it as plain text from our server, not from your device. Nothing on it is run."],
];

export default function Privacy() {
  return (
    <section id="privacy" className="relative border-y border-line bg-ink-2/40 px-5 py-24 sm:px-8 sm:py-32">
      <div className="mx-auto max-w-[1200px]">
        <SectionHead eyebrow="About, security and privacy" title="Built to look at your messages, not to keep them.">
          ScamShield is an automated assessment tool for Indian users. It reads what you give it, checks it, and tells you what it found. Here is exactly what happens to your data.
        </SectionHead>

        <div className="mt-14 grid gap-12 lg:grid-cols-2 lg:gap-20">
          <FadeUp>
            <h3 className="label mb-5 !text-[rgb(var(--tint))]">What stays with you</h3>
            <dl className="divide-y divide-line border-y border-line">
              {STAYS.map(([k, v]) => (
                <div key={k} className="grid gap-1 py-4 sm:grid-cols-[210px_1fr] sm:gap-6">
                  <dt className="text-[15px] font-medium">{k}</dt>
                  <dd className="text-[14.5px] leading-relaxed text-muted">{v}</dd>
                </div>
              ))}
            </dl>
          </FadeUp>
          <FadeUp delay={0.1}>
            <h3 className="label mb-5 !text-warn">What is sent to other services</h3>
            <dl className="divide-y divide-line border-y border-line">
              {LEAVES.map(([k, v]) => (
                <div key={k} className="grid gap-1 py-4 sm:grid-cols-[210px_1fr] sm:gap-6">
                  <dt className="text-[15px] font-medium">{k}</dt>
                  <dd className="text-[14.5px] leading-relaxed text-muted">{v}</dd>
                </div>
              ))}
            </dl>
          </FadeUp>
        </div>

        <FadeUp delay={0.1} className="mt-12 max-w-[760px] rounded-xl border border-line-strong p-5 text-[14.5px] leading-relaxed text-muted">
          <b className="font-medium text-text">Please never paste a password, PIN or OTP.</b> You never need to. To protect the service, requests are rate-limited per IP address, and that count is kept in memory only. ScamShield gives an assessment, not a guarantee: always confirm through the organisation's official app, website or helpline.
        </FadeUp>
      </div>
    </section>
  );
}
