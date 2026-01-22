from datetime import datetime
from core.storage import get_daily_apply_count


def can_apply(db_path: str, daily_limit: int) -> bool:
    today = datetime.utcnow().date().isoformat()
    return get_daily_apply_count(db_path, today) < daily_limit
