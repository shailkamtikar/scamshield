from app.services.domain_analysis import compare_domains


tests = [
    ("Microsoft", "microsoft.com"),
    ("Microsoft", "microsft.com"),
    ("Microsoft", "miconsoft-login.com"),
    ("Microsoft", "google.com"),
    ("Microsoft", "www.microsoft.com"),
]

for claimed_name, domain in tests:
    result = compare_domains(claimed_name, domain)
    print(result)