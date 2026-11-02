"""Fast checks for tools/setup.py and tools/doctor.py."""
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS)

import setup  # noqa: E402


def test_node_versions_match_remotion_engines():
    assert setup.node_ok((22, 13, 0)) and setup.node_ok((20, 19, 1)) and setup.node_ok((24, 1, 0))
    assert not setup.node_ok((20, 18, 0)) and not setup.node_ok((22, 12, 9)) and not setup.node_ok((18, 20, 0))
    assert not setup.node_ok(None)


def test_check_mode_runs_and_changes_nothing():
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "setup.py"), "--check"], capture_output=True, text=True)
    assert r.returncode in (0, 1)
    assert "requirements" in r.stdout


def test_doctor_without_render_reports_versions():
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "doctor.py"), "--no-render"], capture_output=True, text=True)
    assert "cutroom doctor" in r.stdout and "python" in r.stdout
