"""The repository is a Kivy app, not the old nonexistent plugin/ tree."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_validates_the_real_app_and_client():
    workflow = (ROOT / '.github/workflows/build.yml').read_text()
    assert 'plugin/' not in workflow
    assert 'pytest -q tests' in workflow
    assert 'bash -n pc-scripts/' in workflow
    assert 'contents: write' not in workflow
