from platforms.linkedin.apply import apply as linkedin_apply
from platforms.linkedin.enricher import enrich_job as linkedin_enrich
from platforms.naukri.apply import apply as naukri_apply


def get_platforms() -> dict:
    return {
        "linkedin": linkedin_apply,
        "naukri": naukri_apply,
    }


def get_enrichers() -> dict:
    return {
        "linkedin": linkedin_enrich,
    }
