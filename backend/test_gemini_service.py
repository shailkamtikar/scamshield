from app.services.gemini import analyze_scam_evidence


evidence = [
    "URL contains suspicious keyword: 'login'.",
    "Possible impersonation of Microsoft (domain similarity: 88.89%).",
    "Social engineering indicator: urgency ('urgent').",
    "Social engineering indicator: fear or threat ('suspended').",
    "Social engineering indicator: suspicious call to action ('click here').",
    "Screenshot OCR text: Micresot Security Alert",
]


score_breakdown = [
    {"signal": "Possible brand impersonation", "points": 35},
    {"signal": "Suspicious URL keyword", "points": 10},
    {"signal": "Fear / threat language", "points": 15},
    {"signal": "Urgency language", "points": 10},
    {"signal": "Suspicious call to action", "points": 10},
]

result, model_used = analyze_scam_evidence(evidence, risk_score=80, score_breakdown=score_breakdown)

print("GEMINI STRUCTURED ASSESSMENT:")
print("Model used:", model_used)
print("Risk level:", result.risk_level)
print("Confidence:", result.confidence)

print("Reasons:")
for reason in result.reasons:
    print("-", reason)

print("Recommendation:")
print(result.recommendation)