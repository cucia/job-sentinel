from platforms.linkedin.apply import apply as linkedin_apply
from platforms.naukri.apply import apply as naukri_apply


def get_platforms() -> dict:
    return {
        "linkedin": linkedin_apply,
        "naukri": naukri_apply,
    }
