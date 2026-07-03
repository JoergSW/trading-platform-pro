import subprocess
from pathlib import Path

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

SOURCE_DIR = Path("docs")
DOCX_DIR = Path("docs/generated/docx")
PDF_DIR = Path("docs/generated/pdf")


def markdown_lines(source: Path) -> list[str]:
    return source.read_text(encoding="utf-8").splitlines()


def markdown_to_docx(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "pandoc",
            str(source),
            "-o",
            str(target),
        ],
        check=True,
    )


def markdown_to_pdf(source: Path, target: Path) -> None:
    styles = getSampleStyleSheet()
    story = []

    for line in markdown_lines(source):
        text = line.strip()

        if not text:
            story.append(Paragraph("<br/>", styles["Normal"]))
        elif text.startswith("# "):
            story.append(Paragraph(text[2:], styles["Heading1"]))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], styles["Heading2"]))
        elif text.startswith("### "):
            story.append(Paragraph(text[4:], styles["Heading3"]))
        elif text.startswith("- "):
            story.append(Paragraph(f"• {text[2:]}", styles["Normal"]))
        else:
            story.append(Paragraph(text, styles["Normal"]))

    target.parent.mkdir(parents=True, exist_ok=True)

    pdf = SimpleDocTemplate(str(target))
    pdf.build(story)


def main() -> None:
    for md_file in SOURCE_DIR.rglob("*.md"):
        if "generated" in md_file.parts:
            continue

        relative = md_file.relative_to(SOURCE_DIR)

        docx_target = DOCX_DIR / relative.with_suffix(".docx")
        pdf_target = PDF_DIR / relative.with_suffix(".pdf")

        print(f"Processing: {md_file}")

        markdown_to_docx(md_file, docx_target)
        markdown_to_pdf(md_file, pdf_target)

        print(f"Generated DOCX: {docx_target}")
        print(f"Generated PDF : {pdf_target}")


if __name__ == "__main__":
    main()
