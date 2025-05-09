from datetime import datetime, timezone
import os

from pathvalidate import sanitize_filename


def save_diagnostic_log_file(
    app: str, username: str, body: bytes, to_folder: str
) -> str:
    """Save diagnostic log file to DIAGNOSTIC_LOGS_DIR"""

    content = body.decode("utf-8")
    datetime_iso_str = datetime.now(tz=timezone.utc).isoformat()
    file_name = sanitize_filename(
        username + "_" + app + "_" + datetime_iso_str + ".log"
    )
    os.makedirs(to_folder, exist_ok=True)
    with open(os.path.join(to_folder, file_name), "w") as f:
        f.write(content)

    return file_name
