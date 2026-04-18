LINKEDIN_BASE_URL = "https://www.linkedin.com"


def normalize_job_url(job_url: str | None) -> str:
    url = (job_url or "").strip()
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}".split("?", 1)[0]
    if url.startswith("/"):
        return f"{LINKEDIN_BASE_URL}{url}".split("?", 1)[0]
    return url.split("?", 1)[0]
