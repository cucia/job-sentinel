import datetime
import os


def _log_path() -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "jobsentinel.log")


def log(message: str) -> None:
    line = f"[{datetime.datetime.now()}] {message}"
    print(line, flush=True)
    with open(_log_path(), "a", encoding="utf-8") as f:
        f.write(line + "\n")
