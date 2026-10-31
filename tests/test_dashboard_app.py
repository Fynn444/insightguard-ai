from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / 'app.py'


def test_dashboard_executes_ml_sections_without_script_errors():
    app = AppTest.from_file(str(APP_PATH), default_timeout=120).run()

    assert not app.exception
    section_titles = {element.value for element in app.subheader}
    assert 'Historical model comparison' in section_titles
    assert 'New-customer prediction' in section_titles
    assert 'Selected model: held-out test results' in section_titles
    assert 'AI-augmented business insights' in section_titles
    assert any('DEVELOPMENT MOCK OUTPUT' in warning.value for warning in app.warning)
