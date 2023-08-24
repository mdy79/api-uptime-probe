import sys
from unittest.mock import patch, MagicMock
import pytest
from api_uptime_probe.cli import main


def test_cli_missing_config():
    with patch.object(sys, "argv", ["api-uptime-probe", "-c", "/path/to/nonexistent/config.yaml"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_cli_help():
    with patch.object(sys, "argv", ["api-uptime-probe", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
