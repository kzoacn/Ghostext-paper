#!/usr/bin/env python3
"""Check the built review PDF against the declared IEEE S&P format constraints."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def main():
    paper = ROOT / "paper"
    source = (paper / "main.tex").read_text()
    assert r"\documentclass[conference,compsoc]{IEEEtran}" in source
    assert re.search(r"\\author\{\s*\}", source)
    for item in json.loads((ROOT / "results/sp2027-format/upstream-style.json").read_text()):
        assert hashlib.sha256((paper / item["file"]).read_bytes()).hexdigest() == item["sha256"]
    log = (paper / "main.log").read_text()
    assert "Using 8.5in x 11in (letter) paper." in log
    assert "This is a 10 point document." in log
    assert not re.search(r"Overfull|LaTeX Warning:.*(?:undefined|multiply defined)", log)
    pdf_path = paper / "main.pdf"
    pdf = PdfReader(pdf_path)
    assert 1 <= len(pdf.pages) <= 18
    assert not str((pdf.metadata or {}).get("/Author", "")).strip()
    for page in pdf.pages:
        assert abs(float(page.mediabox.width) - 612) < .01
        assert abs(float(page.mediabox.height) - 792) < .01
    reference_page = main_pages = None
    for index, page in enumerate(pdf.pages):
        text = page.extract_text()
        match = re.search(r"(?:^|\n)References\s*(?:\n|$)", text)
        if match:
            reference_page = index + 1
            prefix = re.sub(r"[\s\d]", "", text[:match.start()])
            main_pages = index + bool(prefix)
            break
    assert reference_page is not None, "Cannot locate the reference boundary"
    aux = (paper / "main.aux").read_text()
    float_pages = [int(m.group(1)) for m in re.finditer(
        r"\\newlabel\{(?:fig|tab|alg):[^}]+\}\{\{[^}]*\}\{(\d+)\}", aux)]
    main_pages = max([main_pages, *float_pages])
    assert 7 <= main_pages <= 13, main_pages
    fonts = subprocess.check_output(["pdffonts", str(pdf_path)], text=True)
    font_rows = fonts.splitlines()[2:]
    assert font_rows
    assert all(row.split()[-5] == "yes" for row in font_rows), "Unembedded font"
    assert all("Type 3" not in row for row in font_rows)
    paths = {paper / "main.tex", paper / "refs.bib", paper / "IEEEtran.cls", paper / "IEEEtran.bst",
             *paper.glob("*.sty")}
    pending = [paper / "main.tex"]
    while pending:
        current = pending.pop()
        for match in re.finditer(r"\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}",
                                 current.read_text()):
            path = paper / match.group(1)
            if not path.suffix:
                path = path.with_suffix(".tex")
            if path not in paths:
                paths.add(path)
                if path.suffix == ".tex":
                    pending.append(path)
    record = {
        "pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "document_class": "Unmodified IEEEtran 1.8b, conference,compsoc",
        "paper_size_points": [612, 792], "body_font_points_declared_by_class": 10,
        "total_pages": len(pdf.pages), "conservative_main_content_pages": main_pages,
        "references_begin_page": reference_page, "last_main_float_page": max(float_pages),
        "author_metadata": "", "all_fonts_embedded": True, "type3_fonts": False,
        "unresolved_references": False, "overfull_boxes": False,
        "underfull_box_count": len(re.findall(r"Underfull \\[hv]box", log)),
        "visual_inspection_required": "Inspect every final rendered page; these mechanical checks do not assess layout quality.",
        "font_inventory": font_rows,
        "paper_sources_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(paths)},
    }
    out = ROOT / "results/sp2027-format/validation.json"
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: v for k, v in record.items()
                      if k not in {"font_inventory", "paper_sources_sha256"}}, indent=2))


if __name__ == "__main__":
    main()
