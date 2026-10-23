"""Generate the original synthetic policy PDF used by the local upload demonstration."""

import io
import textwrap
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

ROOT = Path(__file__).resolve().parents[1]


def make_pdf(text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    lines = []
    for paragraph in text.splitlines():
        lines.extend(textwrap.wrap(paragraph, width=82) or [""])
    instructions = ["BT /F1 11 Tf 48 790 Td 16 TL"]
    for line in lines:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        instructions.append(f"({escaped}) Tj T*")
    instructions.append("ET")
    stream = DecodedStreamObject()
    stream.set_data("\n".join(instructions).encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def main():
    original = (
        (ROOT / "teaching/contact2/policies/collection.md").read_text().split("\n---\n", 1)[1]
    )
    text = (
        "KORA DISPATCH\nParcel collection and return policy | Version 1.0\n"
        "Original synthetic workshop document\n" + original.replace("# ", "")
    )
    target = ROOT / "teaching/contact2/pdfs/collection-policy.pdf"
    target.write_bytes(make_pdf(text))
    print(target.relative_to(ROOT))
    paragraphs = [part.strip() for part in original.split("\n\n") if part.strip()]
    sections = [
        ("Holding period and notice date", paragraphs[1]),
        ("Collection code and identity checks", paragraphs[2]),
        ("Supervisor review before return", paragraphs[3]),
    ]
    writer = PdfWriter()
    for number, (heading, paragraph) in enumerate(sections, 1):
        page_text = (
            "KORA DISPATCH\nParcel collection and return policy | Version 1.0\n"
            "Original synthetic workshop document\n\n"
            f"{heading}\n\n{paragraph}\n\nPage {number} of 3"
        )
        writer.append(io.BytesIO(make_pdf(page_text)))
    target = target.with_name("collection-policy-multipage.pdf")
    with target.open("wb") as output:
        writer.write(output)
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
