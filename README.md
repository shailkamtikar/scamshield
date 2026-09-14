# ScamShield

### An Agentic Multimodal Framework for Explainable Cross-Channel Scam Investigation and Risk Assessment

ScamShield is a cybersecurity prototype that detects and investigates suspicious communications by combining **URL intelligence, brand impersonation detection, social-engineering analysis, screenshot OCR, QR-code decoding, and Gemini-based evidence reasoning**.

Unlike detectors that focus only on URLs, ScamShield treats the entire message as evidence and produces an **explainable risk assessment** with a score, reasons, evidence, confidence, and recommended action.

---

##  Features

- **SMS / Text Analysis** – Analyze suspicious messages and extract URLs, emails, and phone numbers.
- **URL Investigation** – Analyze domain structure, suspicious keywords, and possible lookalike/impersonation domains.
- **Brand Impersonation Detection** – Compare claimed organizations with extracted domains.
- **Social Engineering Detection** – Detect urgency, threats, financial pressure, credential requests, and suspicious calls to action.
- **Screenshot Analysis** – Extract text from scam screenshots using Tesseract OCR.
- **QR Code Analysis** – Decode QR codes using OpenCV and investigate the decoded content.
- **Deterministic Risk Scoring** – Generate transparent risk scores from structured signals.
- **Gemini Evidence Reasoning** – Generate confidence, explanations, and recommendations from collected evidence.
- **Gemini Fallback** – Automatically use a secondary Gemini model when recoverable API failures occur.
- **PDF Reports** – Generate an investigation report from the actual analysis result.
- **Responsive Web UI** – React-based security dashboard with light/dark mode.

---

##  System Architecture

```text
User
 │
 ├── Text / SMS
 ├── Screenshot
 └── QR Code
        │
        ▼
     FastAPI
        │
        ▼
  ScamShield State
        │
        ▼
     LangGraph
        │
        ├── Extraction
        ├── URL Investigation
        ├── Identity Verification
        ├── Social Engineering
        ├── Screenshot / OCR
        ├── Risk Assessment
        └── Gemini Reasoning
                │
                ▼
        Explainable Result
        ├── Risk Score
        ├── Risk Level
        ├── Confidence
        ├── Reasons
        ├── Evidence
        └── Recommendation
