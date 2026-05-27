"""
build_all_docs_sq.py
====================
Gjeneron versionet shqipe të tre dokumenteve Word:

  1. Time_Borrowing_Policy_Proposal_SQ.docx
  2. Time_Borrowing_Citizen_Guide_SQ.docx
  3. Time_Borrowing_Geopolitics_Game_Theory_SQ.docx

Përdorimi:
    python build_all_docs_sq.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from doc_i18n import set_lang, apply_doc_patches

set_lang("sq")
apply_doc_patches()

from build_all_docs import (  # noqa: E402
    build_policy_proposal,
    build_citizen_guide,
    build_geopolitics,
    OUT,
)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  GJENERIMI I DOKUMENTEVE — VERSIONI SHQIP")
    print("=" * 60)

    p1 = build_policy_proposal()
    p2 = build_citizen_guide()
    p3 = build_geopolitics()

    print("\n" + "=" * 60)
    print("  TË GJITHA DOKUMENTET U PËRFUNDUAN")
    print("=" * 60)
    print(f"\n  Dosja e daljes: {OUT}")
    for path in (p1, p2, p3):
        name = os.path.basename(path)
        size = os.path.getsize(path) / 1024
        print(f"  {name:<55} {size:>7.1f} KB")
    print()
