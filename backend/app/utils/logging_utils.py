import json
import os
from datetime import datetime

LOG_DIR = os.path.join("backend", "metrics_logs")


def log_json(filename: str, data: dict):
    """
    Append a single JSON record to a log file.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    filepath = os.path.join(LOG_DIR, filename)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        **data
    }

    with open(filepath, "a") as f:
        f.write(json.dumps(record) + "\n")

