from src.platforms.linkedin.apply import apply as linkedin_apply
from src.platforms.linkedin.enricher import enrich_job as linkedin_enrich
from src.platforms.indeed.apply import apply as indeed_apply
from src.platforms.naukri.apply import apply as naukri_apply


def get_platforms() -> dict:
    return {
        "linkedin": linkedin_apply,
        "indeed": indeed_apply,
        "naukri": naukri_apply,
    }


def get_enrichers() -> dict:
    return {
        "linkedin": linkedin_enrich,
    }
