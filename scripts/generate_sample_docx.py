"""Generate data/samples/sample_resume.docx from the markdown source.

Run from the repo root with the API virtualenv (python-docx installed):

    python scripts/generate_sample_docx.py
"""
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "samples" / "sample_resume.md"
TARGET = ROOT / "data" / "samples" / "sample_resume.docx"


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    document = docx.Document()
    for line in lines:
        if line.startswith("# "):
            continue  # markdown title, not resume content
        document.add_paragraph(line)
    document.save(TARGET)
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
