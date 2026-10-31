from app.services.domain_analysis import compare_domains, has_combosquat_structure


def test_typosquat_detected():
    result = compare_domains("Microsoft", "miconsoft-login.com")
    assert result["possible_typosquatting"] is True
    assert result["exact_match"] is False


def test_exact_match_not_flagged():
    result = compare_domains("Microsoft", "https://www.microsoft.com/")
    assert result["exact_match"] is True
    assert result["possible_typosquatting"] is False


def test_brand_inside_compound_is_not_exact():
    result = compare_domains("Netflix", "netflix-billing-support.example")
    assert result["exact_match"] is False
    assert result["possible_typosquatting"] is True


def test_combosquat_structure():
    assert has_combosquat_structure("https://netflix-billing-support.example") == "billing"
    assert has_combosquat_structure("https://netflix.com") is None
