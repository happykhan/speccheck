from pathlib import Path


def test_user_facing_docs_and_html_do_not_use_manuscript_framing():
    checked_files = [
        *Path("docs").glob("**/*.md"),
        *Path("examples").glob("**/*.md"),
        *Path("examples").glob("**/report.html"),
        Path("README.md"),
    ]

    offenders = [
        str(path)
        for path in checked_files
        if "manuscript" in path.read_text(encoding="utf-8").lower()
    ]

    assert offenders == []
