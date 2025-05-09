from datetime import datetime, timezone
import os
from unittest.mock import patch

from pathvalidate import sanitize_filename

from ..stats.utils import save_diagnostic_log_file


def test_save_diagnostic_log_file(client, app):
    """Test save diagnostic log file"""
    # Mock datetime value
    test_date = "2025-05-09T12:00:00+00:00"
    app_name = "t" * 256
    username = "test-user"
    body = b"Test log content"
    to_folder = app.config["DIAGNOSTIC_LOGS_DIR"]

    saved_file_name = save_diagnostic_log_file(app_name, username, body, to_folder)
    saved_file_path = os.path.join(to_folder, saved_file_name)
    assert os.path.exists(saved_file_path)
    assert len(saved_file_name) == 255

    with patch("mergin.stats.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime.fromisoformat(test_date)
        app_name = "test_<>app"
        saved_file_name = save_diagnostic_log_file(app_name, username, body, to_folder)
        # Check if the file was created
        assert saved_file_name == sanitize_filename(
            username + "_" + app_name + "_" + test_date + ".log"
        )
        saved_file_path = os.path.join(to_folder, saved_file_name)
        assert os.path.exists(saved_file_path)
        # Check the content of the file
        with open(saved_file_path, "r") as f:
            content = f.read()
            assert content == body.decode("utf-8")
