import datetime


def log(message: str) -> None:
    print(f"[{datetime.datetime.now()}] {message}", flush=True)
