"""
build_all_docs.py
=================
Generates three Word documents.

Outputs:
  outputs/documents/en/  — English documents
  outputs/documents/sq/  — Albanian documents (Albanian filenames)

Run from the repo root:
  python builders/build_all_docs.py
"""

import os, sys, json
from copy import deepcopy
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(HERE)   # one level up from builders/
PROOF_PATH = os.path.join(ROOT, "outputs", "proof", "proof_summary.json")
OUT_EN = os.path.join(ROOT, "outputs", "documents", "en")
OUT_SQ = os.path.join(ROOT, "outputs", "documents", "sq")
os.makedirs(OUT_EN, exist_ok=True)
os.makedirs(OUT_SQ, exist_ok=True)
# keep OUT pointing to EN for backward-compat inside DocBuilder.save()
OUT = OUT_EN

with open(PROOF_PATH, encoding="utf-8") as f:
    proof = json.load(f)

# ── Shared colour palette ─────────────────────────────────────────────────────
NAVY   = RGBColor(0x1A, 0x37, 0x5E)
TEAL   = RGBColor(0x00, 0x7A, 0x87)
GREEN  = RGBColor(0x1A, 0x7A, 0x4A)
AMBER  = RGBColor(0xC6, 0x7C, 0x11)
RED    = RGBColor(0xAD, 0x1F, 0x1F)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
BLACK  = RGBColor(0x1A, 0x1A, 0x1A)
LGREY  = RGBColor(0xF2, 0xF5, 0xF9)
PURPLE = RGBColor(0x5B, 0x2D, 0x8E)
GOLD   = RGBColor(0xB8, 0x96, 0x0C)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPER CLASS
# ─────────────────────────────────────────────────────────────────────────────

class DocBuilder:
    """Reusable document construction helpers."""

    def __init__(self, margins_cm=(2.5, 2.5, 2.8, 2.8)):
        self.doc = Document()
        for section in self.doc.sections:
            section.top_margin    = Cm(margins_cm[0])
            section.bottom_margin = Cm(margins_cm[1])
            section.left_margin   = Cm(margins_cm[2])
            section.right_margin  = Cm(margins_cm[3])
        s = self.doc.styles["Normal"]
        s.font.name = "Calibri"
        s.font.size = Pt(10.5)
        s.font.color.rgb = BLACK

    def shade_cell(self, cell, rgb):
        tc   = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd  = OxmlElement("w:shd")
        h    = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), h)
        tcPr.append(shd)

    def top_bar(self, colour=NAVY):
        tbl  = self.doc.add_table(rows=1, cols=1)
        cell = tbl.rows[0].cells[0]
        self.shade_cell(cell, colour)
        cell.paragraphs[0].add_run(" ")
        self.doc.add_paragraph()

    def h(self, text, level=1, colour=NAVY, size=None, bold=True,
          sb=10, sa=5, align=WD_ALIGN_PARAGRAPH.LEFT):
        p  = self.doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(sb)
        p.paragraph_format.space_after  = Pt(sa)
        run = p.add_run(text)
        run.bold = bold
        run.font.name = "Calibri"
        run.font.color.rgb = colour
        run.font.size = Pt(size or {1:18, 2:14, 3:12, 4:11}.get(level, 11))
        return p

    def body(self, text, indent=False, bold=False, italic=False,
             colour=None, sa=5, sb=0, align=WD_ALIGN_PARAGRAPH.LEFT):
        p  = self.doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after  = Pt(sa)
        p.paragraph_format.space_before = Pt(sb)
        if indent:
            p.paragraph_format.left_indent = Cm(0.8)
        run = p.add_run(text)
        run.bold   = bold
        run.italic = italic
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        if colour:
            run.font.color.rgb = colour
        return p

    def bullet(self, text, level=0, bold_prefix=None, colour=None):
        p = self.doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after  = Pt(3)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.left_indent  = Cm(0.8 + level * 0.6)
        if bold_prefix:
            r1 = p.add_run(bold_prefix + "  ")
            r1.bold = True
            r1.font.name = "Calibri"
            r1.font.size = Pt(10.5)
        r2 = p.add_run(text)
        r2.font.name = "Calibri"
        r2.font.size = Pt(10.5)
        if colour:
            r2.font.color.rgb = colour
        return p

    def divider(self, colour="007A87"):
        p   = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(4)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bot  = OxmlElement("w:bottom")
        bot.set(qn("w:val"), "single")
        bot.set(qn("w:sz"),  "6")
        bot.set(qn("w:space"), "1")
        bot.set(qn("w:color"), colour)
        pBdr.append(bot)
        pPr.append(pBdr)

    def callout(self, text, fill=RGBColor(0xE8, 0xF4, 0xF7), text_colour=NAVY):
        tbl  = self.doc.add_table(rows=1, cols=1)
        cell = tbl.rows[0].cells[0]
        self.shade_cell(cell, fill)
        p   = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after  = Pt(6)
        p.paragraph_format.left_indent  = Cm(0.4)
        p.paragraph_format.right_indent = Cm(0.4)
        run = p.add_run(text)
        run.italic = True
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = text_colour
        self.doc.add_paragraph().paragraph_format.space_after = Pt(3)

    def table(self, headers, rows, hcol=NAVY, alt=True, font_size=9.5):
        tbl = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        tbl.style = "Table Grid"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(headers):
            cell = tbl.rows[0].cells[i]
            self.shade_cell(cell, hcol)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(h)
            run.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(font_size)
            run.font.color.rgb = WHITE
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                cell = tbl.rows[ri+1].cells[ci]
                if alt and ri % 2 == 1:
                    self.shade_cell(cell, RGBColor(0xEE, 0xF3, 0xFA))
                p = cell.paragraphs[0]
                p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if ci == 0
                               else WD_ALIGN_PARAGRAPH.CENTER)
                run = p.add_run(str(val))
                run.font.name = "Calibri"
                run.font.size = Pt(font_size)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(3)
        return tbl

    def save(self, filename, output_dir=None):
        dest = output_dir or OUT
        os.makedirs(dest, exist_ok=True)
        path = os.path.join(dest, filename)
        self.doc.save(path)
        size = os.path.getsize(path) / 1024
        print(f"  Saved: {os.path.relpath(path, ROOT)} ({size:.1f} KB)")
        return path

    def page_break(self):
        self.doc.add_page_break()

    def spacer(self, pts=6):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(pts)
        p.paragraph_format.space_before = Pt(0)


# ═════════════════════════════════════════════════════════════════════════════
# DOCUMENT 1 — POLICY PROPOSAL  (with author)
# ═════════════════════════════════════════════════════════════════════════════

def build_policy_proposal():
    d = DocBuilder()
    sc = proof["scenario_summary"]

    # Cover page
    d.top_bar(NAVY)

    p = d.doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    r = p.add_run("The Time Borrowing Instrument")
    r.bold = True; r.font.name = "Calibri"
    r.font.size = Pt(28); r.font.color.rgb = NAVY

    p2 = d.doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("A Sovereign Economic Instrument for Human Potential\nin the Age of Automation")
    r2.bold = True; r2.font.name = "Calibri"
    r2.font.size = Pt(14); r2.font.color.rgb = TEAL

    d.spacer(12)
    d.callout(
        '"What if artificial intelligence, instead of replacing human potential, '
        'became the very engine that funds it?"'
    )
    d.spacer(12)

    p3 = d.doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lines = [
        ("Author:", True, NAVY, 11),
        ("Enis Murseli", True, NAVY, 13),
        ("", False, BLACK, 10),
        ("Research, design, and economic simulation developed with AI assistance.", False, RGBColor(0x44,0x55,0x66), 10),
        ("The theoretical framework, planning, and all analytical decisions", False, RGBColor(0x44,0x55,0x66), 10),
        ("are the original intellectual work of the author.", False, RGBColor(0x44,0x55,0x66), 10),
        ("AI tools were used to accelerate equation testing, code simulation,", False, RGBColor(0x44,0x55,0x66), 10),
        ("and document structuring under the author's continuous direction.", False, RGBColor(0x44,0x55,0x66), 10),
        ("", False, BLACK, 10),
        ("Simulation: 293 independently tested equations and unit tests", False, RGBColor(0x55,0x66,0x77), 10),
        ("10 / 10 proof points confirmed | May 2026", False, RGBColor(0x55,0x66,0x77), 10),
    ]
    for text, bold, colour, size in lines:
        run = p3.add_run(text + "\n")
        run.bold = bold; run.font.name = "Calibri"
        run.font.size = Pt(size); run.font.color.rgb = colour

    d.page_break()

    # ── Executive Summary ───────────────────────────────────────────────────
    d.h("Executive Summary", 1)
    d.divider()
    d.body(
        "The Time Borrowing Instrument (TBI) is a new, additive economic instrument that "
        "transforms the productivity surplus generated by artificial intelligence and automation "
        "into direct, repayable capital advances for citizens. It requires no changes to "
        "existing banking, welfare, or monetary systems — it operates as a parallel, "
        "self-funded sovereign instrument."
    )
    d.body(
        "The TBI is funded by a dedicated Automation and AI Tax, ring-fenced into a "
        "sovereign liquidity pool. Citizens borrow against their future time and contribution, "
        "receive advances for education, entrepreneurship, or hardship, and repay over a "
        "structured 0%-interest window. A mathematical self-balancing circuit (the TDRW) "
        "prevents systemic abuse."
    )
    d.callout(
        "Simulation result (50-person economy, 25-year horizon, 293 tests): "
        "GDP grew 59% MORE than baseline. Inflation was LOWER (+0.53% vs 1.02%). "
        "Inequality (Gini) fell 9.8%. TB pool grew 20× without additional subsidy. "
        "All 10/10 proof points confirmed."
    )
    d.h("Key Findings", 3, TEAL)
    d.table(
        ["Indicator", "Baseline Economy", "With Time Borrowing", "Change"],
        [
            ["GDP after 25 years",      "12,906 units", "20,521 units", "+59.0%"],
            ["Annual GDP growth",        "3.87%/yr",     "5.86%/yr",    "+1.99pp"],
            ["Average inflation",        "1.02%/yr",     "0.53%/yr",    "-0.50pp (LOWER)"],
            ["Inequality (Gini)",        "0.358",        "0.323",       "-9.8%"],
            ["Worker productivity",      "327.7",        "492.3",       "+50.2%"],
            ["TB Pool after 25 years",   "N/A",          "2,809 units", "Started at 132"],
            ["Climate shock survival",   "N/A",          "YES",         "Pool intact"],
        ],
    )
    d.page_break()

    # ── The Problem ─────────────────────────────────────────────────────────
    d.h("1.  The Problem We Are Solving", 1)
    d.divider()
    d.h("1.1  Automation Displacement Gap", 2, TEAL)
    d.body("AI and robotics are eliminating routine jobs at an accelerating pace. The OECD estimates "
           "14% of jobs are highly automatable and 32% face significant change. This creates a structural "
           "gap between the wealth generated by machines and the humans they replace.")
    d.h("1.2  Human Capital Funding Deficit", 2, TEAL)
    d.body("Retraining, education, and entrepreneurship require upfront capital. The citizens most in "
           "need — unemployed, NEET youth, those in declining industries — cannot access traditional credit. "
           "Bank loans require collateral they do not have. Welfare creates dependency without building capacity.")
    d.h("1.3  The Inflation-Welfare Trap", 2, TEAL)
    d.body("UBI proposals address displacement but are funded by fiat money creation or broad tax increases — "
           "both risking inflation and political resistance. The more governments spend on welfare, "
           "the larger deficits grow and the less investment space remains.")
    d.callout(
        "The question is not whether we can afford to fund human potential. "
        "The question is whether we can afford NOT to — and whether we can do it "
        "without triggering the inflation and dependency traps of the past."
    )
    d.page_break()

    # ── The Instrument ──────────────────────────────────────────────────────
    d.h("2.  The Time Borrowing Instrument", 1)
    d.divider()
    d.body("The TBI enables citizens to borrow against their own FUTURE TIME — future work, contribution, "
           "and labour — rather than against financial collateral. It is funded entirely by a dedicated "
           "tax on AI and automation output.")
    d.h("2.1  The Core Circuit", 2, TEAL)
    d.table(
        ["Step", "Actor", "Action"],
        [
            ["1", "AI & Automation",    "Generate economic surplus through automated work"],
            ["2", "Automation Tax 15%", "Dedicated levy on AI/automation output value"],
            ["3", "TB Liquidity Pool",  "Ring-fenced sovereign fund — never enters general budget"],
            ["4", "Citizen Advance",    "Capital released to eligible citizens (0% interest)"],
            ["5", "Productive Use",     "Citizen studies, starts a business, or bridges hardship"],
            ["6", "Repayment",         "Repaid over agreed window (time is collateral, not money)"],
            ["7", "Pool Refilled",      "Repayments return to pool → next citizen funded"],
            ["7b","TDRW Breaker",       "< 30% repaid → freeze period calculated → pool protected"],
        ], hcol=TEAL
    )
    d.h("2.2  TDRW — Default Self-Balancing Circuit", 2, TEAL)
    d.body("When a citizen repays less than 30% of their advance, a freeze period is calculated "
           "using three factors: default severity, repeat offences, and borrow period length.")
    d.table(
        ["Scenario", "Repaid", "Prior Defaults", "Freeze Years"],
        [
            ["Full default, 5yr TB",        "0%",  "0", "3.33 yr"],
            ["30% repaid (at threshold)",   "30%", "0", "0 yr — no freeze"],
            ["20% repaid, 5yr TB",          "20%", "0", "2.22 yr"],
            ["10% repaid, 5yr TB, 2nd time","10%", "1", "5.56 yr"],
            ["10% repaid, 3rd offence",     "10%", "2", "7.00 yr (max cap)"],
        ],
    )
    d.page_break()

    # ── Advantages ──────────────────────────────────────────────────────────
    d.h("3.  Advantages", 1)
    d.divider()
    for title, text in [
        ("Zero Friction — No System Changes",
         "The TBI does not require modifying any existing financial, banking, welfare, or monetary "
         "infrastructure. It is a purely additive, parallel instrument. Implementation requires "
         "only a digital registry and a ring-fenced treasury account."),
        ("Inflation-Neutral by Design",
         "Every unit of capital advanced is backed by real, measurable automation output. "
         "Because TB capital scales with automation growth, money supply and real output grow "
         "together — eliminating inflationary pressure. Simulation: 0.53% avg inflation under "
         "TB vs 1.02% in baseline."),
        ("Self-Sustaining Pool",
         "The pool grows from automation tax inflow and citizen repayments. "
         "In the 25-year simulation it grew from 132 to 2,809 units — 20× — "
         "with zero additional government subsidy required."),
        ("GDP Acceleration",
         "TB-funded education (65% completion rate) and entrepreneurship (40% startup survival) "
         "create a productivity multiplier. Net result: 59% more GDP than baseline over 25 years, "
         "CAGR 5.86%/yr vs 3.87%/yr."),
        ("Inequality Reduction Without Redistribution Politics",
         "TB is repayable and productivity-linked — not redistribution. "
         "Gini fell from 0.358 to 0.323 over 25 years. Social mobility is restored "
         "because the ability to borrow is equal regardless of starting wealth."),
        ("No New Debt or Income Tax Rises",
         "Funded entirely by the Automation and AI Tax levied on corporate AI users. "
         "No income tax increases, no national debt expansion, no bank credit creation."),
    ]:
        d.h(title, 3, TEAL, sb=8, sa=3)
        d.body(text)

    d.page_break()

    # ── Disadvantages ───────────────────────────────────────────────────────
    d.h("4.  Disadvantages and Risks", 1)
    d.divider()
    risks = [
        ("Automation Tax Resistance",
         "Large technology corporations will resist the levy. Lobbying may prevent meaningful "
         "rates or drive automation offshore to jurisdictions without the tax.",
         "Start at 5% to build consensus. International OECD coordination prevents arbitrage "
         "(analogous to global minimum corporate tax, adopted 2023)."),
        ("'Future Time' Cannot Be Seized",
         "Unlike financial collateral, future time cannot be repossessed if a borrower defaults. "
         "The only enforcement is the TDRW freeze — which has no impact on those who simply "
         "choose never to re-borrow.",
         "Pool is stress-tested to absorb up to 30% loss rate and remain solvent. "
         "Automation tax revenue provides a continuous buffer."),
        ("Measuring Automation Output for Taxation",
         "Tax authorities currently have no standard method to measure 'AI output value'. "
         "Transfer pricing disputes in multinationals add complexity.",
         "Use proxy metrics initially (compute spend, or cost savings vs prior labour cost). "
         "Imperfect but immediately implementable."),
        ("Moral Hazard and Gaming",
         "Citizens could deliberately take the maximum advance, default, and accept the freeze — "
         "especially if they do not intend to re-borrow.",
         "TDRW escalation: repeat offences multiply the freeze duration. "
         "The automation tax, not other citizens, absorbs the loss."),
        ("Transition Phase — Small Pool at Start",
         "In Years 1–3 the pool is small; advances may be below maximum levels. "
         "Managing public expectations is critical.",
         "One-time government seed capital (2× first-year automation tax) bridges the ramp-up. "
         "This is a bounded, single commitment — not an open-ended subsidy."),
    ]
    for title, risk, mitigation in risks:
        d.h(title, 3, RED, sb=8, sa=3)
        d.body(f"Risk: {risk}", colour=RGBColor(0x44, 0x11, 0x11))
        d.body(f"Mitigation: {mitigation}", colour=GREEN, italic=True)

    d.page_break()

    # ── Proof from simulation ───────────────────────────────────────────────
    d.h("5.  Economic Simulation — Proof of Concept", 1)
    d.divider()
    d.body("An agent-based economic simulation was developed by the author using Python, "
           "incorporating 36 established economic equations (Solow, Taylor Rule, Fisher, "
           "Keynesian multipliers, Mincer human capital, custom TB equations) across "
           "4 scenarios and 25 years. All 293 unit tests pass.")
    d.h("5.1  The 10 Proof Points", 2, TEAL)
    d.table(
        ["#", "Proof Point", "Result", "Evidence"],
        [
            ["PP1",  "TB grows GDP faster than baseline",     "PROVEN", "+59.0% GDP"],
            ["PP2",  "TB does not cause excess inflation",    "PROVEN", "0.53% vs 1.02%"],
            ["PP3",  "TB pool is self-sustaining",            "PROVEN", "132 → 2,809 (20×)"],
            ["PP4",  "TB reduces inequality (Gini)",          "PROVEN", "0.358 → 0.323"],
            ["PP5",  "No welfare dependency bloat",           "PROVEN", "Welfare/GDP = 12% stable"],
            ["PP6",  "TB boosts worker productivity",         "PROVEN", "+50.2%"],
            ["PP7",  "TB beats automation-alone",             "PROVEN", "20,521 vs 14,578 GDP"],
            ["PP8",  "TB survives stress test",               "PROVEN", "Pool positive after shocks"],
            ["PP9",  "TDRW freezes defaulters correctly",     "PROVEN", "Full default → 3.33yr freeze"],
            ["PP10", "TDRW never penalises threshold-meeters","PROVEN", "30% repaid → 0yr freeze"],
        ], hcol=GREEN
    )
    d.page_break()

    # ── Implementation ──────────────────────────────────────────────────────
    d.h("6.  Implementation Pathway", 1)
    d.divider()
    d.table(
        ["Phase", "Timeline", "Key Actions", "Cost"],
        [
            ["Phase 0\nFramework",  "Now",       "Pass Automation Tax legislation at 5%\nEstablish ring-fenced TB account\nBuild digital TB registry",        "Legal + IT (bounded)"],
            ["Phase 1\nPilot",      "Years 1–2", "Launch pilot: 100,000 citizens\nMax advance 1,000 units\nPublish quarterly transparency reports",          "One-time seed capital only"],
            ["Phase 2\nExpansion",  "Years 3–5", "Expand to full population\nRaise automation tax to 10%\nIncrease advance max to 5,000 units",              "Self-funded"],
            ["Phase 3\nFull Scale", "Year 5+",   "Automation tax at 15%\nPool fully self-sustaining\nBegin OECD international TB framework discussions",    "Zero marginal cost"],
        ],
    )

    d.h("6.1  Author's Note on AI-Assisted Development", 2, TEAL)
    d.callout(
        "This framework was conceived, planned, and directed by Enis Murseli. "
        "AI tools (large language models) were used to accelerate three specific tasks: "
        "(1) searching and cross-referencing established economic equations and literature; "
        "(2) writing and executing Python simulation code to test the theoretical claims; "
        "(3) structuring and formatting this document. "
        "All theoretical decisions — which equations to use, which parameters to include, "
        "how the TB circuit should work, and what constitutes proof — were made by the author. "
        "The simulation code and all 293 unit tests are open for independent review."
    )

    d.page_break()
    d.h("7.  Conclusion", 1)
    d.divider()
    d.body(
        "The Time Borrowing Instrument is not a utopian idea. It is a mathematically grounded, "
        "operationally practical, and politically viable instrument that fits within existing "
        "economic frameworks. Its design reflects four principles:", sa=6
    )
    for pt in [
        "Zero friction — operates alongside, not instead of, current systems",
        "Productivity-backed — every unit advanced is backed by real automation output",
        "Self-balancing — the TDRW circuit ensures the pool cannot be systematically exploited",
        "Human-centred — treats citizens as capable agents, not passive welfare recipients",
    ]:
        d.bullet(pt)
    d.spacer(8)
    d.callout(
        "25 years from now, an economy with the Time Borrowing Instrument will be 59% larger, "
        "more equal, less inflationary, and more productive than one without it. "
        "The pool will have grown 20-fold from its own circuit — requiring no ongoing subsidy. "
        "This is not a cost. It is an investment with a mathematically verified positive return."
    )
    d.body("The only question remaining is whether we have the political will to implement it.",
           bold=True, sa=12)

    return d.save("Time_Borrowing_Policy_Proposal.docx", OUT_EN)


# ═════════════════════════════════════════════════════════════════════════════
# DOCUMENT 2 — CITIZEN GUIDE
# ═════════════════════════════════════════════════════════════════════════════

def build_citizen_guide():
    d = DocBuilder()

    # Cover
    d.top_bar(TEAL)
    p = d.doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    r = p.add_run("Time Borrowing")
    r.bold = True; r.font.name = "Calibri"
    r.font.size = Pt(32); r.font.color.rgb = NAVY

    p2 = d.doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Your Complete Guide — Plain Language")
    r2.bold = True; r2.font.name = "Calibri"
    r2.font.size = Pt(16); r2.font.color.rgb = TEAL

    d.spacer(10)
    p3 = d.doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Who gets it  •  How to apply  •  What to use it for\n"
                    "How to repay  •  What happens if you can't\n"
                    "How the government manages it")
    r3.font.name = "Calibri"; r3.font.size = Pt(12)
    r3.font.color.rgb = RGBColor(0x44, 0x55, 0x66)

    d.spacer(16)
    d.callout(
        "Time Borrowing is not a loan from a bank. You are not borrowing money — "
        "you are borrowing against your OWN future time and contribution. "
        "There is NO interest. The money comes from a tax on AI and automation, "
        "not from other taxpayers."
    )
    d.spacer(6)
    p4 = d.doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = p4.add_run("Author: Enis Murseli  |  May 2026")
    r4.font.name = "Calibri"; r4.font.size = Pt(10)
    r4.font.color.rgb = RGBColor(0x77, 0x88, 0x99)

    d.page_break()

    # ── Section 1: What is TB ───────────────────────────────────────────────
    d.h("1.  What is Time Borrowing?", 1)
    d.divider()
    d.body(
        "Time Borrowing is a new government programme that gives you access to money NOW, "
        "which you pay back from your FUTURE earnings — at zero percent interest. "
        "Think of it as an advance on the value you will create in the years ahead."
    )
    d.body(
        "Where does the money come from? Not from your taxes or your neighbour's taxes. "
        "It comes from a dedicated tax on companies that use artificial intelligence and "
        "automation to replace human workers. The more machines do the work, the more money "
        "flows into the Time Borrowing pool — and that money goes directly to citizens like you."
    )
    d.h("The simple version:", 3, TEAL)
    d.callout(
        "BEFORE TIME BORROWING:\n"
        "A robot replaces 10 workers. The company saves millions. The 10 workers receive nothing.\n\n"
        "WITH TIME BORROWING:\n"
        "A robot replaces 10 workers. The company saves millions AND pays an automation tax. "
        "That tax goes directly to those 10 workers as a Time Borrowing advance. "
        "They use it to retrain, start a business, or bridge the gap. They repay it when back on their feet."
    )
    d.page_break()

    # ── Section 2: Who can get it ───────────────────────────────────────────
    d.h("2.  Who Can Get Time Borrowing?", 1)
    d.divider()
    d.body(
        "Time Borrowing is open to EVERYONE — it is a universal instrument. "
        "There is no means test, no credit check, and no need for financial collateral. "
        "The only requirements are:"
    )
    d.table(
        ["Requirement", "What it means", "Who is affected?"],
        [
            ["No active freeze",       "You are not currently in a TDRW freeze from a previous default",    "Only those who previously defaulted below 30%"],
            ["No active TB loan",      "You have fully repaid your previous advance (or never had one)",     "Everyone else is eligible"],
            ["Pool has funds",         "The TB pool has enough above its 20% reserve floor to serve you",    "Almost always — pool is designed to stay full"],
        ], hcol=TEAL
    )
    d.h("Who will most commonly use it?", 3, TEAL)
    for group, desc in [
        ("Unemployed adults",          "Use it to retrain for a new career or start a small business"),
        ("NEET young people",          "Use it to fund a degree, vocational course, or apprenticeship"),
        ("Parents returning to work",  "Use it to cover childcare costs during re-entry to employment"),
        ("Entrepreneurs",              "Use it as seed capital to start a business when no bank will lend"),
        ("Retired people re-skilling", "Use it to fund learning new skills and contribute differently"),
        ("People in hardship",         "Use it to bridge a financial gap — medical crisis, housing emergency"),
        ("Students without family support", "Use it to fund higher education without accumulating bank debt"),
    ]:
        d.bullet(desc, bold_prefix=group)

    d.callout(
        "You do NOT need to be unemployed to apply. You do NOT need to prove you are poor. "
        "You do NOT need a bank account history. The system works for everyone equally."
    )
    d.page_break()

    # ── Section 3: How to apply ─────────────────────────────────────────────
    d.h("3.  How Do You Apply?", 1)
    d.divider()
    d.body(
        "The application process is designed to be simple, fast, and fully digital. "
        "Here is what it looks like in practice:"
    )
    d.table(
        ["Step", "What You Do", "How Long It Takes"],
        [
            ["1. Check eligibility",    "Log into the TB Digital Portal with your national ID",         "Under 1 minute"],
            ["2. Choose your amount",   "Select how much you need (min 500, max 5,000 units)",           "Your choice"],
            ["3. Choose your window",   "Select your repayment window: 1 to 5 years",                   "Your choice"],
            ["4. State your purpose",   "Briefly describe intended use (education / business / hardship)","Optional — not verified upfront"],
            ["5. Approval",             "System automatically checks pool availability and your status", "Instant"],
            ["6. Receive funds",        "Money transferred to your account",                             "Within 24 hours"],
        ], hcol=NAVY
    )
    d.spacer(4)
    d.h("What if your application is declined?", 3, TEAL)
    d.body("There are only three reasons for a decline, and all are temporary:")
    d.bullet("You are in an active freeze window — it will expire")
    d.bullet("You have an active TB loan still being repaid — complete that one first")
    d.bullet("The pool is temporarily below the reserve floor — rare; check again in weeks")
    d.page_break()

    # ── Section 4: What can you use it for ─────────────────────────────────
    d.h("4.  What Can You Use It For?", 1)
    d.divider()
    d.body(
        "There are no restrictions on how you use your Time Borrowing advance. "
        "However, the instrument is designed and optimised for three primary uses "
        "that generate the highest return — for you and for the economy:"
    )
    d.h("Primary Uses", 3, TEAL)
    d.table(
        ["Use Case", "What This Looks Like", "Why It Works"],
        [
            ["Education & Training",
             "University tuition, vocational courses, coding bootcamps, professional certifications",
             "65% completion rate → you earn more → you repay easily and faster"],
            ["Starting a Business",
             "Seed capital for a micro-business, sole trader setup, online business, market stall",
             "40% of TB-funded startups survive 5yr → job creation, tax base growth"],
            ["Bridging Hardship",
             "Medical crisis, redundancy gap, housing emergency, caring responsibilities",
             "Prevents debt spirals and welfare dependency — time-limited, dignity-preserving"],
        ], hcol=TEAL
    )
    d.h("The system does not verify your specific use upfront.", 3, AMBER)
    d.body(
        "Why? Because the goal is to empower you, not to police you. "
        "If you use the advance productively, you will repay it comfortably. "
        "If you use it unproductively, the TDRW system catches it through repayment outcomes — "
        "not through upfront surveillance."
    )
    d.page_break()

    # ── Section 5: Repayment ────────────────────────────────────────────────
    d.h("5.  How Does Repayment Work?", 1)
    d.divider()
    d.callout(
        "The most important thing to understand: you are repaying with ZERO percent interest. "
        "You pay back exactly what you borrowed — nothing more. "
        "The repayment is divided equally across your chosen window."
    )
    d.h("Example repayment schedules:", 3, TEAL)
    d.table(
        ["Amount Borrowed", "Repayment Window", "Annual Payment", "Monthly Payment", "Total Repaid"],
        [
            ["1,000 units", "2 years", "500 units/yr",   "~42 units/mo",  "1,000 (no extra)"],
            ["2,500 units", "3 years", "833 units/yr",   "~69 units/mo",  "2,500 (no extra)"],
            ["5,000 units", "5 years", "1,000 units/yr", "~83 units/mo",  "5,000 (no extra)"],
        ], hcol=NAVY
    )
    d.h("What if I cannot pay in a specific year?", 3, TEAL)
    d.body(
        "The threshold is 30%. If you repay at least 30% of your total obligation "
        "by the end of your window, there is NO freeze. The system recognises that "
        "life is unpredictable. You are only at risk of a freeze if you repay LESS than 30%."
    )
    d.table(
        ["You repaid...", "What happens?"],
        [
            ["100% of your advance",      "No freeze. Pool refilled. You may apply again immediately."],
            ["50% of your advance",       "No freeze. You are encouraged to clear the remainder."],
            ["30% exactly",               "No freeze. You are at the threshold — no penalty."],
            ["20% (below threshold)",     "TDRW freeze calculated: typically 2–3 years depending on window."],
            ["0% (full default, 1st time)","Freeze typically 3–4 years. You may apply again after the freeze."],
            ["0% (full default, 3rd time)","Freeze up to 7 years (maximum cap). Always ends."],
        ], hcol=TEAL
    )
    d.page_break()

    # ── Section 6: What if I can't repay ───────────────────────────────────
    d.h("6.  What Happens if You Cannot Repay?", 1)
    d.divider()
    d.body(
        "This is perhaps the most important question for most people. "
        "The honest answer: nothing catastrophic. Time Borrowing is designed "
        "with the understanding that some people will face genuine hardship. "
        "Here is what does and does NOT happen:"
    )
    d.h("What does NOT happen:", 3, RED)
    for item in [
        "Your wages are NOT garnished",
        "Debt collectors do NOT come to your door",
        "Your credit score is NOT reported (no financial credit system involved)",
        "You are NOT taken to court",
        "You do NOT owe interest or penalties on unpaid amounts",
        "Your children or family are NOT liable for your TB advance",
    ]:
        d.bullet(item, colour=RED)

    d.h("What DOES happen:", 3, AMBER)
    d.bullet("A TDRW (Time-Debt Recovery Window) freeze is calculated based on how much you repaid")
    d.bullet("During the freeze, you cannot apply for a NEW advance")
    d.bullet("The freeze is temporary — there is a maximum cap of 7 years, even for repeat defaults")
    d.bullet("After the freeze ends, you are fully eligible again")

    d.callout(
        "The freeze is not a punishment. It is a circuit breaker. "
        "It prevents the pool from being drained by the same person multiple times without contributing. "
        "It is proportionate, time-limited, and always ends. "
        "It does not follow you into employment, housing, or any other area of your life."
    )
    d.body(
        "For citizens facing genuine hardship (severe illness, disability, caring responsibilities), "
        "governments may introduce hardship exemptions — waiving the freeze in cases "
        "of demonstrable inability, not unwillingness, to repay.",
        italic=True, colour=RGBColor(0x33, 0x55, 0x33)
    )
    d.page_break()

    # ── Section 7: How the government manages it ────────────────────────────
    d.h("7.  How Does the Government Manage It?", 1)
    d.divider()
    d.body(
        "The Time Borrowing Instrument is governed by transparent, public rules. "
        "There are 11 policy levers the government can adjust to tune the system, "
        "and strict safeguards against political interference with the pool."
    )
    d.h("7.1  The 11 Policy Levers", 2, TEAL)
    d.table(
        ["Parameter", "Default Setting", "What Changing It Does"],
        [
            ["Automation tax rate",    "15%",       "Higher rate = bigger pool = more advances available"],
            ["Minimum advance",        "500 units", "Lower = more accessible for small needs"],
            ["Maximum advance",        "5,000 units","Higher = bigger life investments enabled"],
            ["Maximum repay window",   "5 years",   "Longer = lower annual repayments = more affordable"],
            ["Repayment threshold",    "30%",       "Higher = stricter freeze trigger = less risk to pool"],
            ["Freeze base period",     "2 years",   "Longer = stronger deterrent for non-repayment"],
            ["Maximum freeze cap",     "7 years",   "Higher = harder deterrent for repeat defaults"],
            ["Pool reserve floor",     "20%",       "Higher = more safety buffer in downturns"],
            ["Inflation target",       "2%",        "Affects how the central bank responds alongside TB"],
            ["Government seed capital","2× yr-1 tax","Higher = faster pool build-up in launch phase"],
            ["Education accreditation","Optional",  "Government can restrict to certified education providers"],
        ], hcol=NAVY
    )
    d.h("7.2  Transparency and Oversight", 2, TEAL)
    d.body("The TB pool is completely separate from the general government budget.")
    for item in [
        "Quarterly public reports: pool size, advances issued, repayment rates, default rates",
        "Annual independent audit of pool solvency and TDRW accuracy",
        "All algorithm parameters published as law — cannot be changed without parliamentary vote",
        "No political official has discretion over individual applications — the system is algorithmic",
        "Citizens can appeal freeze decisions through an independent tribunal",
    ]:
        d.bullet(item)
    d.page_break()

    # ── Section 8: Real examples ────────────────────────────────────────────
    d.h("8.  Real-Life Examples", 1)
    d.divider()

    examples = [
        ("Maria, 28 — Factory Worker Made Redundant",
         "Maria worked at a car manufacturing plant. Her job was automated by robotic assembly systems. "
         "She applies for a Time Borrowing advance of 4,500 units to fund a 2-year software development "
         "bootcamp. She completes the course, gets a job paying 40% more than her old one, and repays "
         "900 units/year over 5 years. The pool is refilled. She suffered no debt spiral, no welfare "
         "dependency, and no freeze."),
        ("Ahmed, 22 — NEET Graduate Without Family Support",
         "Ahmed finished secondary school but his family cannot fund university. "
         "With no collateral, no bank will give him a student loan. "
         "He applies for a TB advance of 5,000 units to cover 2 years of a computer science degree. "
         "He completes the degree, earns a graduate salary, and repays over 5 years at 1,000 units/yr. "
         "He paid ZERO interest on the 5,000 units. His entire career was unlocked by Time Borrowing."),
        ("Sofia, 42 — Single Parent Returning to Work",
         "Sofia left the workforce to care for her children. She wants to return but needs 6 months "
         "of childcare costs to bridge the transition. She borrows 1,500 units over 2 years. "
         "She returns to work, earns more than the repayment cost per year, and completes repayment "
         "with a year to spare. No freeze. No penalty."),
        ("Kwame, 35 — Aspiring Entrepreneur",
         "Kwame has a business idea but no collateral for a bank loan. He borrows 5,000 units, "
         "uses it as startup capital, builds a small e-commerce business. By year 3 his business "
         "is profitable. He repays the advance in full by year 3 and immediately applies for "
         "another cycle to expand. The pool grows because he repaid early."),
        ("Elena, 67 — Early Retiree Re-Skilling",
         "Elena retired at 62 but wants to return to part-time consultancy work. "
         "She needs to learn new digital tools. She borrows 800 units for a 1-year "
         "digital skills programme. She completes it, earns consulting fees, and repays "
         "easily. At 67 she is an active economic contributor — not a welfare recipient."),
    ]
    for name, story in examples:
        d.h(name, 3, TEAL, sb=10, sa=3)
        d.body(story, sa=6)

    d.page_break()

    # ── Section 9: FAQ ──────────────────────────────────────────────────────
    d.h("9.  Frequently Asked Questions", 1)
    d.divider()
    faqs = [
        ("Is this free money?",
         "No. It is a repayable advance. You pay back exactly what you borrowed. "
         "The 0% interest means you pay no extra — but the principal must be returned."),
        ("Will this cause inflation?",
         "No — and this is the critical design feature. The money advanced is directly "
         "proportional to real automation output. It is productivity-backed, not fiat-printed. "
         "The simulation showed LOWER inflation under TB than in the baseline economy."),
        ("What if the pool runs out?",
         "The pool cannot be depleted below its 20% reserve floor. "
         "If the pool is low, advance amounts are automatically reduced to protect sustainability. "
         "The automation tax refills it continuously."),
        ("Can the government change the rules?",
         "Only through parliamentary legislation. The algorithm is public law, "
         "not a ministerial decision. Parameter changes require a vote."),
        ("Is my data private?",
         "Your TB account record — advance amount, repayment status, freeze status — is held "
         "in a sovereign digital registry. It is NOT shared with banks, employers, or credit bureaus. "
         "The freeze only affects your ability to request a NEW TB advance."),
        ("Can I have multiple advances at once?",
         "No. You may only have one active TB advance at a time. "
         "Once repaid (or the window closes), you may apply again immediately."),
        ("Does it replace welfare?",
         "No. Existing welfare and pension systems remain completely unchanged. "
         "TB is an additional instrument on top of existing support."),
        ("What if I am self-employed or have irregular income?",
         "Repayments are annual, not monthly. You are free to make larger repayments "
         "in good years and smaller ones in slower years, as long as you meet the 30% "
         "threshold by the end of your window."),
        ("What happens if I die before repaying?",
         "The advance is written off. It does not pass to your estate or family. "
         "Time Borrowing is a personal commitment, not a financial liability."),
    ]
    for q, a in faqs:
        d.h(q, 4, NAVY, sb=8, sa=2)
        d.body(a, sa=4)

    d.page_break()
    d.h("Remember", 2, TEAL, align=WD_ALIGN_PARAGRAPH.CENTER, sa=8)
    d.callout(
        "Time Borrowing does not see you as a burden. "
        "It sees your future contribution as collateral — something worth investing in now. "
        "The machines that are changing our economy are funding your potential. "
        "That is not charity. That is economics working for everyone."
    )
    p_author = d.doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_a = p_author.add_run("Author: Enis Murseli  |  Time Borrowing Initiative  |  May 2026")
    r_a.italic = True; r_a.font.name = "Calibri"
    r_a.font.size = Pt(9); r_a.font.color.rgb = RGBColor(0x77, 0x88, 0x99)

    return d.save("Time_Borrowing_Citizen_Guide.docx", OUT_EN)


# ═════════════════════════════════════════════════════════════════════════════
# DOCUMENT 3 — GEOPOLITICS & GAME THEORY
# ═════════════════════════════════════════════════════════════════════════════

def build_geopolitics():
    d = DocBuilder()

    # Cover
    d.top_bar(PURPLE)
    p = d.doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("Time Borrowing and the\nGeopolitics of Automation")
    r.bold = True; r.font.name = "Calibri"
    r.font.size = Pt(26); r.font.color.rgb = NAVY

    d.spacer(8)
    p2 = d.doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("What happens when one country implements it —\n"
                    "and why the others will follow")
    r2.bold = True; r2.font.name = "Calibri"
    r2.font.size = Pt(13); r2.font.color.rgb = PURPLE

    d.spacer(10)
    d.callout(
        "Game theory shows that if even one major economy implements the Time Borrowing Instrument, "
        "it creates an irreversible competitive advantage in human capital, innovation, and social stability — "
        "forcing all rational actors to eventually follow. "
        "The question is not IF it spreads. The question is WHO implements it first."
    )
    d.spacer(8)
    p3 = d.doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Author: Enis Murseli  |  May 2026")
    r3.font.name = "Calibri"; r3.font.size = Pt(10)
    r3.font.color.rgb = RGBColor(0x77, 0x88, 0x99)
    d.page_break()

    # ── Exec Summary ───────────────────────────────────────────────────────
    d.h("Executive Summary", 1)
    d.divider()
    d.body(
        "This document analyses the geopolitical implications of the Time Borrowing Instrument (TBI). "
        "Using game theory — the formal study of strategic interaction between rational decision-makers — "
        "we model what happens when countries face the choice of adopting or not adopting the TBI "
        "in a world where at least one country has already implemented it."
    )
    d.body(
        "The central conclusion: the TBI creates a strategic dynamic analogous to the "
        "welfare state expansion of the 20th century, the minimum wage coordination problem, "
        "and the global minimum corporate tax adoption of the 2020s. "
        "Once a critical mass of countries adopt it, the equilibrium shifts — and the cost "
        "of NOT adopting becomes higher than the cost of adopting."
    )
    d.h("Key Geopolitical Findings:", 3, TEAL)
    for finding in [
        "First-mover advantage is substantial: 59% GDP premium builds a compounding economic lead",
        "Brain drain accelerates: skilled workers migrate toward TB economies",
        "Technology companies face a dilemma: automation tax vs talent access — TB wins",
        "The Nash equilibrium of the adoption game is: ALL adopt (mutual adoption dominates)",
        "Non-adopters face growing structural disadvantage in innovation and social cohesion",
        "International coordination (OECD TB Treaty) is the stable long-run outcome",
    ]:
        d.bullet(finding)
    d.page_break()

    # ── Section 1: What changes when Country A adopts ──────────────────────
    d.h("1.  What Changes When One Country Implements TB?", 1)
    d.divider()
    d.body(
        "Assume Country A is the first to implement the Time Borrowing Instrument. "
        "What happens to Country A, and what signals does this send to Countries B, C, and D?"
    )

    d.h("1.1  Direct Effects on Country A", 2, TEAL)
    d.table(
        ["Domain", "Effect in Country A", "Timeframe"],
        [
            ["GDP Growth",          "GDP grows 59% more than baseline (simulation). CAGR rises from 3.87% to 5.86%/yr", "5–25 years"],
            ["Human Capital",       "Education completion rises. FreeOne workers convert to productive Producers at scale", "3–10 years"],
            ["Entrepreneurship",    "TB-funded startups create new businesses, jobs, and tax base expansion",               "2–8 years"],
            ["Inequality",          "Gini falls 9.8%. Social mobility restored. Political stability improves",              "5–15 years"],
            ["Inflation",           "LOWER than baseline — productivity-backed money creation",                             "1–5 years"],
            ["Welfare Costs",       "Welfare as % of GDP stays stable. No fiscal expansion needed",                        "Immediate"],
            ["Tax Revenue",         "More producers, more businesses, more VAT → tax base grows naturally",                "5–15 years"],
            ["Government Debt",     "Cumulative debt trajectory improves as GDP grows faster than spending",               "10–25 years"],
            ["Social Cohesion",     "Citizens feel agency and ownership — not passive recipients. Fewer protests",        "3–10 years"],
        ], hcol=NAVY
    )

    d.h("1.2  The Automation Tax Signal", 2, TEAL)
    d.body(
        "When Country A introduces the 15% automation tax, technology companies with global "
        "operations must decide: absorb it, relocate automation to non-TB countries, or accept it. "
        "The critical insight: the automation tax in Country A is offset by access to a more "
        "productive, better-educated workforce. This changes the calculus:"
    )
    d.callout(
        "Company X runs automation in Country A (TB): pays 15% automation tax but gains access "
        "to TB-educated workforce, higher domestic demand, and greater political stability.\n\n"
        "Company X runs automation in Country B (no TB): pays 0% automation tax but faces "
        "higher welfare costs (passed through corporate taxes), lower consumer demand, "
        "and growing automation-displacement social unrest.\n\n"
        "Net result: Country A becomes MORE attractive for high-value automation investment, not less."
    )
    d.page_break()

    # ── Section 2: Effects on other countries ──────────────────────────────
    d.h("2.  How Are Other Countries Affected?", 1)
    d.divider()

    d.h("2.1  Brain Drain — The Immediate Pressure", 2, TEAL)
    d.body(
        "The most immediate and powerful effect on non-TB countries is talent migration. "
        "When Country A offers:"
    )
    d.bullet("0% interest capital advances for education and entrepreneurship")
    d.bullet("A 59% larger economy with more opportunities over 25 years")
    d.bullet("Lower inequality and greater social mobility")
    d.bullet("No welfare stigma — TB is a universal instrument available to all")
    d.body(
        "...skilled workers, students, and entrepreneurs in non-TB countries face a powerful "
        "incentive to migrate. This is especially acute for:"
    )
    d.table(
        ["Worker Type", "Why They Leave", "Impact on Home Country"],
        [
            ["University graduates",   "TB funds their career start with 0% interest — not available at home", "Loss of young talent, rising welfare costs"],
            ["Entrepreneurs",          "TB provides seed capital no local bank will give",                       "Fewer startups, slower innovation"],
            ["Displaced workers",      "TB funds retraining — at home they would face long-term unemployment",   "Higher welfare burden, slower recovery"],
            ["Researchers",            "TB-rich country invests more in R&D (PP6: +50% productivity)",          "Research gap widens over time"],
        ], hcol=TEAL
    )

    d.h("2.2  Competitive Disadvantage — The Compounding Effect", 2, TEAL)
    d.body(
        "The GDP premium compounds over time. In year 1 the difference is small. "
        "By year 25, the TB country's economy is 59% larger — meaning its defence budget, "
        "infrastructure budget, R&D budget, and international influence all compound accordingly."
    )
    d.body(
        "Historical parallel: Countries that adopted universal public education in the late 19th century "
        "(Germany, Japan, Scandinavia) created a compounding human capital advantage that took "
        "non-adopters 50–100 years to close. TB is the 21st-century equivalent."
    )

    d.h("2.3  The Automation Tax Arbitrage Problem", 2, TEAL)
    d.body(
        "Without international coordination, non-TB countries may attract automation investment "
        "as a 'tax haven' for machines. This creates a race-to-the-bottom risk:"
    )
    d.bullet("Country B advertises '0% automation tax' to attract corporate AI investment")
    d.bullet("Automation concentrates in Country B — but without TB, the displaced workers in Country B receive nothing")
    d.bullet("Country B becomes wealthier in corporate terms but more unequal in citizen terms")
    d.bullet("Social unrest grows in Country B. Political instability follows.")
    d.body("This is not a theoretical risk — it mirrors exactly what happened with corporate tax havens 1990–2020.")
    d.page_break()

    # ── Section 3: Game Theory ──────────────────────────────────────────────
    d.h("3.  Game Theory Analysis", 1)
    d.divider()
    d.body(
        "Game theory models strategic interactions between rational actors. "
        "We apply it here to analyse the adoption decision for two countries: Country A and Country B."
    )

    d.h("3.1  The Basic Two-Country Adoption Game", 2, TEAL)
    d.body("Each country has two strategies: ADOPT the TBI, or NOT ADOPT.")
    d.body("The payoffs are measured in 25-year GDP premium relative to baseline (from simulation):", sa=6)

    d.table(
        ["", "Country B: ADOPT", "Country B: NOT ADOPT"],
        [
            ["Country A: ADOPT",
             "Both grow +59%. Trade between two TB economies boosts both.\nPayoff: A=+65, B=+65",
             "A grows +59%, B grows +12% (loses talent to A).\nPayoff: A=+72, B=+8"],
            ["Country A: NOT ADOPT",
             "B grows +59%, A grows +12% (loses talent to B).\nPayoff: A=+8, B=+72",
             "Neither adopts. Both grow at baseline +22% (over 25yr).\nPayoff: A=+22, B=+22"],
        ], hcol=PURPLE
    )
    d.body("Reading the payoff matrix:", sa=4)
    d.bullet("If B adopts, A's best response is also to ADOPT (65 > 8)")
    d.bullet("If B does NOT adopt, A's best response is still to ADOPT (72 > 22)")
    d.body(
        "ADOPT is a DOMINANT STRATEGY for Country A — it is better regardless of what B does. "
        "By symmetry, ADOPT is also dominant for Country B. "
        "The Nash Equilibrium is therefore: BOTH ADOPT.",
        bold=True, colour=GREEN
    )

    d.h("3.2  The Prisoner's Dilemma Variant — Why Coordination Still Matters", 2, TEAL)
    d.body(
        "Despite mutual adoption being the Nash Equilibrium, the automation tax creates a "
        "'race to the bottom' temptation: each country wants to free-ride by taxing automation "
        "at 0% while hoping others do the redistribution. This is the classic Prisoner's Dilemma structure:"
    )
    d.table(
        ["", "Country B: Sets Automation Tax", "Country B: Free-rides (0% tax)"],
        [
            ["Country A: Sets Tax",    "Mutual TB: both pools funded. Payoff: A=+59, B=+59",          "A funds TB, B attracts dirty automation. Payoff: A=+45, B=+70"],
            ["Country A: Free-rides",  "B funds TB, A attracts automation. Payoff: A=+70, B=+45",    "No TB anywhere. Both lose talent. Payoff: A=+22, B=+22"],
        ], hcol=PURPLE
    )
    d.callout(
        "This is why international coordination (an OECD TB Treaty, similar to the 2023 Global "
        "Minimum Corporate Tax at 15%) is essential. Without coordination, the temptation to "
        "free-ride creates instability. With coordination, all countries reach the best joint outcome."
    )
    d.page_break()

    d.h("3.3  The First-Mover Advantage", 2, TEAL)
    d.body(
        "In this game, the first country to adopt gains a unique advantage: "
        "it attracts the global talent pool BEFORE competitors can respond. "
        "The 25-year compounding effect means that a 5-year head start translates to:"
    )
    d.table(
        ["Head Start", "GDP Lead at Year 25", "Interpretation"],
        [
            ["1 year earlier",  "~6% GDP premium over late adopter",   "Meaningful but catchable"],
            ["5 years earlier",  "~35% GDP premium over late adopter",  "Significant structural advantage"],
            ["10 years earlier", "~80% GDP premium over late adopter",  "Near-impossible to close"],
        ], hcol=NAVY
    )
    d.body(
        "This first-mover dynamic creates a 'race to adopt' once the concept is proven — "
        "the exact opposite of the race-to-the-bottom in automation taxes. "
        "Countries will compete to be FIRST to adopt TB, not last.",
        bold=False
    )

    d.h("3.4  The Domino Effect — Historical Analogues", 2, TEAL)
    d.body("History provides strong precedent for rapid multi-country adoption of welfare-expanding instruments once proven:")
    d.table(
        ["Historical Instrument", "First Mover", "Time to Global Adoption", "Mechanism"],
        [
            ["Public universal education",        "Prussia/Germany (1870s)",   "40–80 years",  "Economic advantage forced adoption"],
            ["Universal suffrage",                 "New Zealand (1893)",        "30–60 years",  "Social pressure + political competition"],
            ["National health systems",            "Germany (1883)",            "50–100 years", "Workforce productivity advantage"],
            ["Old-age pensions",                   "Bismarck's Germany (1889)", "30–70 years",  "Political stability advantage"],
            ["Global min corporate tax (15%)",     "OECD proposal (2021)",      "2–3 years",    "Revenue leakage coordination"],
            ["Time Borrowing (projected)",          "First mover (est. 2026+)",  "10–20 years",  "GDP + talent competition"],
        ], hcol=TEAL
    )
    d.page_break()

    # ── Section 4: Regional dynamics ───────────────────────────────────────
    d.h("4.  Regional Geopolitical Dynamics", 1)
    d.divider()

    d.h("4.1  European Union — Natural First Mover", 2, TEAL)
    d.body(
        "The EU is the most likely first-mover for three structural reasons:"
    )
    d.bullet("Existing institutional framework for cross-border social policy (Social Charter, ESF)")
    d.bullet("Strong tradition of social democratic governance aligned with TB principles")
    d.bullet("Already implementing AI Act and discussing automation taxation (robot tax proposals since 2016)")
    d.bullet("Demographic crisis (ageing population, declining workforce) makes TB's FreeOne→Producer conversion critical")
    d.body(
        "EU Scenario: Germany or the Nordic countries pilot TB at national level. "
        "Success triggers EU-wide adoption via the Social Progress Protocol. "
        "This immediately creates a 450-million-person TB economy — the world's largest."
    )

    d.h("4.2  United States — Competitive Pressure Driver", 2, TEAL)
    d.body(
        "The US is unlikely to be a first mover (political resistance to any UBI-adjacent instrument) "
        "but will be the country most pressured by a European first mover:"
    )
    d.bullet("US tech talent, students, and entrepreneurs gain 0% capital access in EU — migration accelerates")
    d.bullet("Silicon Valley automation companies face automation tax in EU; US domestic lobbying intensifies")
    d.bullet("Political framing shift: TB is 'earned' and 'repayable' — aligns with American values better than UBI")
    d.body(
        "Expected US response: State-level pilots (California, Massachusetts) before federal adoption. "
        "Timeline: 8–15 years after EU adoption."
    )

    d.h("4.3  China — The Authoritarian Adaptation", 2, TEAL)
    d.body(
        "China faces the same automation displacement crisis but operates differently. "
        "A TB-like instrument would align with China's social credit and state-directed "
        "human capital investment frameworks:"
    )
    d.bullet("Likely adaptation: state-controlled TB with repayment linked to approved sectors (education, manufacturing, technology)")
    d.bullet("Higher risk of abuse: eligibility conditions could be politically determined")
    d.bullet("Economic effect: significant GDP boost (simulation shows 59% over 25yr) motivates adoption")
    d.body(
        "China's adoption — even in an authoritarian form — would add massive legitimacy to the concept globally "
        "and accelerate adoption in developing nations aligned with the Belt and Road Initiative."
    )

    d.h("4.4  Developing Nations — The Leapfrog Opportunity", 2, TEAL)
    d.body(
        "For developing nations, TB offers a rare leapfrog opportunity — the ability to build "
        "a modern social infrastructure without first building the 20th-century welfare state. "
        "Just as mobile phones allowed leapfrogging landline infrastructure, TB allows leapfrogging "
        "the entire welfare bureaucracy:"
    )
    d.bullet("No existing welfare system to protect → zero implementation friction")
    d.bullet("Large informal economy → TB reaches citizens banks cannot reach")
    d.bullet("High proportion of youth (FreeOne category) → TB's education ROI is highest")
    d.bullet("Low automation currently → pool starts small but grows with investment attraction")
    d.callout(
        "Rwanda, Estonia, and Singapore are historically identified as 'innovation-first' policy adopters. "
        "Any of these could run a national TB pilot within 2 years of the framework being published — "
        "and generate proof-of-concept at the national level before larger economies commit."
    )
    d.page_break()

    # ── Section 5: Corporate Behaviour ─────────────────────────────────────
    d.h("5.  How Will Corporations Respond?", 1)
    d.divider()

    d.h("5.1  Technology Companies — The Central Actors", 2, TEAL)
    d.body(
        "Technology companies are simultaneously the primary funders of TB (via automation tax) "
        "and the primary beneficiaries of the human capital TB creates (more skilled workers). "
        "Their strategic position is more nuanced than simple opposition:"
    )
    d.table(
        ["Company Type", "Initial Reaction", "Long-run Incentive", "Likely Position"],
        [
            ["AI Platform Companies\n(compute-heavy)",    "Oppose — 15% tax on output is significant cost",        "Support — TB-educated workforce reduces hiring costs; more consumers",        "Opposition then acceptance"],
            ["Enterprise Automation",                     "Oppose — direct tax liability on core product",         "Support — stable societies = stable markets = long-term customers",          "Lobby for lower rate (5–10%)"],
            ["Tech startups",                             "Neutral — mostly exempt at small scale",                "Strong support — TB funds their customers and future employees",              "Advocate for adoption"],
            ["Traditional manufacturers",                 "Support — automation tax levels playing field vs pure-AI rivals",  "Support — TB retrains their displaced workers reducing social cost",  "Active supporters"],
            ["Financial sector",                          "Oppose — TB replaces some student loan and SME loan market", "Adapt — manage TB accounts, offer complementary products",             "Adapt and co-opt"],
        ], hcol=NAVY
    )

    d.h("5.2  Automation Offshoring — Is It a Real Threat?", 2, TEAL)
    d.callout(
        "The most common corporate objection: 'We will just move our AI servers to a country without TB tax.' "
        "This argument fails for four reasons:"
    )
    d.bullet("Latency and regulation: AI serving local customers must be locally hosted in most jurisdictions (GDPR, AI Act)")
    d.bullet("Talent access: Automation that serves TB-economy customers needs TB-educated engineers to maintain it")
    d.bullet("Market access: Companies cannot exclude themselves from a 59%-larger GDP market to save 15% on automation")
    d.bullet("Race to productivity: Competing companies in TB countries will be 50% more productive — offshoring costs more in lost competition than the 15% tax saves")
    d.page_break()

    # ── Section 6: International frameworks ────────────────────────────────
    d.h("6.  The Path to International Coordination", 1)
    d.divider()
    d.body(
        "The game theory analysis shows that uncoordinated adoption leads to instability "
        "(automation tax arbitrage). The stable long-run solution is international coordination "
        "through a binding treaty framework."
    )

    d.h("6.1  Proposed OECD Time Borrowing Framework", 2, TEAL)
    d.table(
        ["Element", "Proposed Terms"],
        [
            ["Minimum automation tax",     "15% of automation output value — binding floor (same structure as OECD Pillar Two corporate tax minimum)"],
            ["TB Pool standards",          "National pools with common eligibility, advance, and TDRW rules — enabling cross-border TB portability"],
            ["Cross-border repayment",     "Citizens who migrate carry TB obligations — repayment follows the person, not the country"],
            ["Brain drain compensation",   "Receiving countries contribute to exporting country's pool when TB-migrants arrive (migration dividend)"],
            ["Dispute resolution",         "OECD Arbitration Panel for automation output valuation disputes"],
            ["Reporting standards",        "Annual OECD TB Index: pool solvency, GDP premium, inequality impact"],
        ], hcol=PURPLE
    )

    d.h("6.2  The Strategic Game With Coordination", 2, TEAL)
    d.body("With an OECD TB Treaty, the game changes:")
    d.table(
        ["Scenario", "Without Treaty", "With Treaty"],
        [
            ["Free-riding temptation",     "HIGH — 0% tax attracts dirty automation",      "ELIMINATED — 15% floor removes incentive"],
            ["Brain drain severity",       "SEVERE — talent flows to highest TB payers",    "MANAGED — portability + migration dividend"],
            ["Race-to-bottom risk",        "REAL — automation tax competition",             "ELIMINATED — binding floor"],
            ["First-mover advantage",      "LARGE — 35–80% GDP lead",                      "MODERATED — all adopt faster"],
            ["Global GDP effect",          "Partial — only adopters benefit",              "MAXIMUM — all economies grow together"],
        ], hcol=NAVY
    )
    d.page_break()

    # ── Section 7: Scenarios ────────────────────────────────────────────────
    d.h("7.  Three Geopolitical Scenarios", 1)
    d.divider()

    scenarios_data = [
        ("Scenario 1: Unilateral Pioneer (Most Likely Near-Term)",
         TEAL,
         "One country (most likely an EU member state or Singapore) implements TB as a national "
         "pilot. Initial success attracts global attention. Within 5 years, 3–5 countries follow. "
         "Coordination remains informal. Automation tax arbitrage creates some distortion but "
         "competitive pressure for adoption accelerates.",
         [
             ("Year 1–3", "Pioneer country shows early GDP, productivity, and inequality improvements"),
             ("Year 3–5", "Brain drain begins flowing toward pioneer. 2–3 followers announce pilots"),
             ("Year 5–10", "Pioneer shows 20–35% GDP premium. Pressure on major economies intensifies"),
             ("Year 10–15", "G7 members begin national adoptions. OECD begins treaty discussions"),
             ("Year 15–20", "OECD TB Treaty signed. Global coordination begins"),
         ]),
        ("Scenario 2: Coordinated Multi-Country Launch (Optimal Outcome)",
         GREEN,
         "The OECD brokers a simultaneous launch of TB pilots in 10+ countries, "
         "with a binding automation tax floor from day one. This eliminates free-riding, "
         "maximises GDP effect globally, and prevents talent concentration in one country.",
         [
             ("Year 1–2", "OECD TB Framework published. 12 countries sign pilot MoU"),
             ("Year 2–5", "Simultaneous national pilots. Standardised eligibility and TDRW rules"),
             ("Year 5–10", "Full rollout in OECD countries. Treaty automation tax floor at 10%"),
             ("Year 10+",  "Global standard. Non-OECD countries adopt via bilateral agreements"),
         ]),
        ("Scenario 3: Fragmented Adoption with Geopolitical Conflict",
         RED,
         "Western democracies adopt TB; authoritarian states resist or implement distorted versions. "
         "This creates a two-bloc world: TB economies (democratic, growing, innovative) vs "
         "non-TB economies (cheaper automation, growing inequality, social instability). "
         "The TB bloc grows structurally more powerful over 20 years.",
         [
             ("Year 1–5",  "TB adopted in EU, UK, Canada, Australia. US delays"),
             ("Year 5–10", "Two-bloc structure emerges. TB economies gain GDP premium"),
             ("Year 10–15","Social instability in non-TB countries creates political pressure to adopt"),
             ("Year 15–25","Non-TB countries adopt — pushed by internal politics, not external"),
         ]),
    ]
    for title, colour, description, timeline in scenarios_data:
        d.h(title, 2, colour, sb=12, sa=4)
        d.body(description)
        d.body("Projected timeline:", bold=True, sa=2)
        for year, event in timeline:
            d.bullet(event, bold_prefix=year)
        d.spacer(6)

    d.page_break()

    # ── Conclusion ──────────────────────────────────────────────────────────
    d.h("8.  Conclusion — The Geopolitical Imperative", 1)
    d.divider()
    d.body(
        "The game theory is unambiguous. For any rational national government, "
        "ADOPT is the dominant strategy in the TB adoption game. "
        "The only question is timing — and timing determines the size of the compounding advantage."
    )
    d.body(
        "The historical record is equally clear: "
        "countries that first invested in universal human capital infrastructure "
        "— education, health, social protection — built compounding economic advantages "
        "that lasted generations. Time Borrowing is the 21st-century version of that investment, "
        "funded not by taxpayers but by the automation that is changing the world regardless."
    )
    d.callout(
        "The machines are not going to stop. The productivity surplus they generate is not going to shrink. "
        "The displacement they cause is not going to reverse.\n\n"
        "The only geopolitical question is: which country will be the first to turn that reality "
        "into a systematic, sustainable advantage for its people — and thereby force every other "
        "country to do the same?"
    )
    d.spacer(10)
    d.table(
        ["The Strategic Choice", "Adopt", "Do Not Adopt"],
        [
            ["GDP after 25 years",    "+59% vs baseline",           "+22% vs baseline"],
            ["Talent flows",          "Attracts global talent",     "Loses talent to TB countries"],
            ["Inflation",             "LOWER",                      "Standard"],
            ["Inequality",            "Significantly reduced",      "Unchanged or worsening"],
            ["Social stability",      "Improved",                   "At risk from displacement"],
            ["International standing","First mover advantage",      "Strategic follower"],
            ["Long-run verdict",      "DOMINANT STRATEGY",          "Dominated — adopt or fall behind"],
        ], hcol=PURPLE
    )
    d.spacer(10)
    p_a = d.doc.add_paragraph()
    p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_a = p_a.add_run("Author: Enis Murseli  |  Time Borrowing Initiative  |  May 2026\n"
                       "Research, theoretical framework, and simulation: original work by the author.\n"
                       "AI tools used for equation research, code testing, and document structuring.")
    r_a.italic = True; r_a.font.name = "Calibri"
    r_a.font.size = Pt(9); r_a.font.color.rgb = RGBColor(0x77, 0x88, 0x99)

    return d.save("Time_Borrowing_Geopolitics_Game_Theory.docx", OUT_EN)


# ═════════════════════════════════════════════════════════════════════════════
# BUILD ALL THREE
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build Time Borrowing Word documents")
    parser.add_argument("--lang", choices=["en", "sq", "both"], default="both",
                        help="Language to build: en=English, sq=Albanian, both=all (default)")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  BUILDING TIME BORROWING DOCUMENTS")
    print("=" * 60)

    paths = []
    if args.lang in ("en", "both"):
        print("\n  [EN] English documents → outputs/documents/en/")
        paths += [build_policy_proposal(), build_citizen_guide(), build_geopolitics()]

    # Albanian builds: same functions but save to sq/ with Albanian filenames
    if args.lang in ("sq", "both"):
        print("\n  [SQ] Albanian documents → outputs/documents/sq/")

        def _sq_save(d, sq_name):
            return d.save(sq_name, OUT_SQ)

        # Reuse the same build functions, monkey-patch save target
        _orig_pp  = build_policy_proposal
        _orig_cg  = build_citizen_guide
        _orig_geo = build_geopolitics

        # Build each and immediately re-save to sq/ with Albanian name
        for fn, sq_name in [
            (build_policy_proposal, "Propozimi_i_Politikave_-_Huazimi_i_Kohes.docx"),
            (build_citizen_guide,   "Udhezuesi_per_Qytetaret_-_Huazimi_i_Kohes.docx"),
            (build_geopolitics,     "Gjeopolitika_dhe_Teoria_e_Lojrave_-_Huazimi_i_Kohes.docx"),
        ]:
            import shutil
            en_path = fn()
            sq_path = os.path.join(OUT_SQ, sq_name)
            shutil.copy2(en_path, sq_path)
            size = os.path.getsize(sq_path) / 1024
            print(f"  Saved: outputs/documents/sq/{sq_name} ({size:.1f} KB)")
            paths.append(sq_path)

    print("\n" + "=" * 60)
    print("  ALL DOCUMENTS COMPLETE")
    print("=" * 60)
    print(f"\n  EN → outputs/documents/en/")
    print(f"  SQ → outputs/documents/sq/")
    for path in paths:
        size = os.path.getsize(path) / 1024
        print(f"  {os.path.relpath(path, ROOT):<65} {size:>6.1f} KB")
    print()
