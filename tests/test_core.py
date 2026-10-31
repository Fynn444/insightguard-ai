from pathlib import Path


def test_project_root_exists():
    assert Path(__file__).resolve().parents[1].exists()


def test_requirements_include_streamlit():
    requirements = Path(__file__).resolve().parents[1] / 'requirements.txt'
    assert requirements.exists()
    content = requirements.read_text(encoding='utf-8')
    assert 'streamlit' in content.lower()
