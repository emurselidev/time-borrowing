"""
build_word_doc_sq.py
====================
Gjeneron versionin shqip të propozimit të plotë të politikës:

  Time_Borrowing_Instrument_Policy_Proposal_SQ.docx

Përdorimi:
    python build_word_doc_sq.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from doc_i18n import set_lang, apply_doc_patches, suffix

set_lang("sq")
apply_doc_patches()  # imports build_word_doc after patches (document built on import)

import build_word_doc as bwd  # noqa: E402

OUT_NAME = f"Time_Borrowing_Instrument_Policy_Proposal{suffix()}.docx"

if __name__ == "__main__":
    out_path = os.path.join(bwd.OUT, OUT_NAME)
    bwd.doc.save(out_path)
    print(f"\nDokumenti u ruajt: {out_path}")
    print(f"Madhësia: {os.path.getsize(out_path) / 1024:.1f} KB")
    print("Faqe: ~22 (përafërsisht)")
