def init_db(_db_path: str) -> None:
    """Storage init stub."""
    return None


def has_seen_job(_db_path: str, _job_key: str) -> bool:
    return False


def enqueue_job(_db_path: str, _job: dict) -> None:
    return None


def next_queued_job(_db_path: str) -> dict | None:
    return None


def update_job(_db_path: str, _job_key: str, **_fields) -> None:
    return None


def record_decision(_db_path: str, _job_key: str, _decision: str, _score: int) -> None:
    return None


def get_daily_apply_count(_db_path: str, _date_iso: str) -> int:
    return 0


def record_feedback(_db_path: str, _job_key: str, _label: str, _notes: str = "") -> None:
    return None


def get_feedback_label(_db_path: str, _job_key: str) -> str | None:
    return None


def get_approved_count(_db_path: str) -> int:
    return 0


def get_model_state(_db_path: str) -> dict:
    return {}


def save_model_state(_db_path: str, _weights: dict, _bias: float) -> None:
    return None
