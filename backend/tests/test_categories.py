"""Unit tests for the Tier-1/Tier-2 category taxonomy (rule-based classifier,
no API keys needed) and for the cross-domain embedding-similarity assumption
that keeps the shared-session test database in tests/conftest.py safe from
cross-test pollution."""
from app.utils.ai import CATEGORIES, _rule_based_analysis, cosine_similarity, local_embed

NEW_TIER2_CATEGORIES = {
    "Real Estate", "Audio & Podcast", "Publishing", "Events",
    "Music Production", "Data & AI Services",
}


def test_new_tier2_categories_are_registered():
    assert NEW_TIER2_CATEGORIES.issubset(set(CATEGORIES))


def test_real_estate_job_classified_correctly():
    analysis = _rule_based_analysis(
        "Real estate photos for a Warsaw apartment listing",
        "Need real estate photography and virtual staging for a property listing.",
        1500,
    )
    assert analysis["category"] == "Real Estate"


def test_music_production_job_classified_correctly():
    analysis = _rule_based_analysis(
        "Mixing and mastering for a single",
        "Need mixing and mastering for one track, produkcja muzyczna.",
        2000,
    )
    assert analysis["category"] == "Music Production"


def test_data_labeling_job_classified_correctly():
    analysis = _rule_based_analysis(
        "Data annotation for a computer vision model",
        "Need data labeling and data annotation for training data, image bounding boxes.",
        400,
    )
    assert analysis["category"] == "Data & AI Services"


def test_unrelated_domains_have_low_embedding_similarity():
    """This is the assumption tests/conftest.py's shared session DB relies on:
    a photographer's profile must not look like a plausible AI match for an
    unrelated marketing job, or other test files would contaminate each
    other's match results."""
    photographer = local_embed(
        "Anna Kowalska professional product photographer e-commerce photography retouching Warsaw"
    )
    marketing_job = local_embed(
        "SEO campaign for online store marketing seo ads social media campaign for our shop"
    )
    assert cosine_similarity(photographer, marketing_job) < 0.15
