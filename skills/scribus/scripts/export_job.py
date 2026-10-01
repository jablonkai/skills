"""Job for ``scribus.py export``: open an existing .sla and export it to PDF.

argv: SLA OUT_PDF PRESET BLEED_MM_OR_EMPTY MARKS(0|1) MARK_OFFSET_MM
The source .sla is never saved.
"""
import sys
import xml.etree.ElementTree as ET

import scribus

import scribus_lib as L

sla, out, preset, bleed, marks, offset = sys.argv[1:7]
# Scribus replaces fonts it does not have without any error, so compare first.
used = {el.get("FONT") for el in ET.parse(sla).getroot().iter() if el.get("FONT")}
substituted = sorted(used - set(scribus.getFontNames()))
L.open_doc(sla)
L.export_pdf(out, preset=preset, bleed=float(bleed) if bleed else None,
             marks=marks == "1", mark_offset=float(offset))
RESULT = {"pdf": out, "pages": scribus.pageCount(), "preset": preset,
          "substituted_fonts": substituted}
