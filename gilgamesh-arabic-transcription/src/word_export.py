from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


def set_font(run, name: str, size: float, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("ascii", "hAnsi", "cs", "eastAsia"):
        rfonts.set(qn(f"w:{attr}"), name)
    rtl = OxmlElement("w:rtl")
    rpr.append(rtl)


def set_rtl(paragraph) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    bidi = ppr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        ppr.append(bidi)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("ملحمة جلجامش  •  ")
    set_font(run, "Arial", 9)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)


def configure(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Cm(21)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.2)
        section.right_margin = Cm(2.2)
        section.footer_distance = Cm(0.9)
        add_page_number(section.footer.paragraphs[0])
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(16)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.line_spacing = 1.28
    for name in ("Title", "Heading 1", "Heading 2"):
        style = styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input_txt", type=Path)
    p.add_argument("output_docx", type=Path)
    args = p.parse_args()
    lines = args.input_txt.read_text(encoding="utf-8").splitlines()
    sep_index = next(i for i, line in enumerate(lines) if line.startswith("[يَنْتَهِي"))

    doc = Document()
    configure(doc)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_rtl(title)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(title.add_run("مَلْحَمَةُ جِلْجَامِشَ"), "Arial", 26, True)
    author = doc.add_paragraph()
    set_rtl(author); author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(author.add_run("تَمِيمُ البَرْغُوثِيُّ"), "Arial", 18, True)
    note = doc.add_paragraph()
    set_rtl(note); note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(note.add_run("نَصٌّ مُقابَلٌ بِالمَصادِرِ المُتاحَةِ مَعَ بَيانِ مُسْتَوَى التَّحَقُّقِ"), "Arial", 13)
    scope = doc.add_paragraph()
    set_rtl(scope)
    scope.paragraph_format.space_before = Pt(18)
    scope.paragraph_format.space_after = Pt(8)
    scope.paragraph_format.line_spacing = 1.35
    scope.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    scope_text = (
        "يضم القسم الأول النص الوارد في النسخة البشرية المشكولة والمقابل بالتفريغ الصوتي الآلي. "
        "ويبدأ بعد علامة الانتقال قسم الاستكمال المبني على مقابلة تفريغ يوتيوب بالتفريغ الجديد، "
        "وتشكيله في ذلك القسم آلي ومعد للمراجعة، فلا يمثل ضبطًا لغويًا نهائيًا."
    )
    set_font(scope.add_run(scope_text), "Arial", 13)
    doc.add_page_break()

    heading = doc.add_paragraph(style="Heading 1")
    set_rtl(heading); heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(heading.add_run("النَّصُّ البَشَرِيُّ المُشَكَّلُ"), "Arial", 19, True)

    for index, line in enumerate(lines[3:], start=3):
        if index == sep_index:
            psep = doc.add_paragraph()
            set_rtl(psep); psep.alignment = WD_ALIGN_PARAGRAPH.CENTER
            psep.paragraph_format.page_break_before = True
            psep.paragraph_format.space_after = Pt(12)
            set_font(psep.add_run("بِدايَةُ قِسْمِ الاسْتِكْمالِ الآلِيِّ"), "Arial", 19, True)
            pnote = doc.add_paragraph()
            set_rtl(pnote); pnote.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(pnote.add_run("مُقابَلٌ بِتَفْرِيغَيْنِ آلِيَّيْنِ ومُشَكَّلٌ مَسْوَدَّةً لِلمُراجَعَةِ"), "Arial", 12, True)
            continue
        if not line.strip():
            spacer = doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(5)
            continue
        para = doc.add_paragraph()
        set_rtl(para)
        para.paragraph_format.keep_together = True
        para.paragraph_format.widow_control = True
        para.paragraph_format.space_after = Pt(2.5)
        para.paragraph_format.line_spacing = 1.25
        set_font(para.add_run(line), "Arial", 16)

    args.output_docx.parent.mkdir(parents=True, exist_ok=True)
    doc.core_properties.title = "ملحمة جلجامش"
    doc.core_properties.subject = "نص مقابل بالمصادر المتاحة مع بيان مستوى التحقق"
    doc.core_properties.author = ""
    doc.save(args.output_docx)
    print(args.output_docx)


if __name__ == "__main__":
    main()
