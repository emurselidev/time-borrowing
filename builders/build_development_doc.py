"""
build_development_doc.py
========================
Generates the "Time, Equality and Development" document in English and Albanian.

  outputs/documents/en/Time_Borrowing_Development_and_Equality.docx
  outputs/documents/sq/Zhvillimi_dhe_Barazimi_-_Huazimi_i_Kohes.docx

Run from the repo root:
  python builders/build_development_doc.py
"""

import os, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.dirname(HERE)
OUT_EN = os.path.join(ROOT, "outputs", "documents", "en")
OUT_SQ = os.path.join(ROOT, "outputs", "documents", "sq")
os.makedirs(OUT_EN, exist_ok=True)
os.makedirs(OUT_SQ, exist_ok=True)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1A, 0x37, 0x5E)
TEAL   = RGBColor(0x00, 0x7A, 0x87)
GREEN  = RGBColor(0x1A, 0x7A, 0x4A)
AMBER  = RGBColor(0xC6, 0x7C, 0x11)
RED    = RGBColor(0xAD, 0x1F, 0x1F)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
BLACK  = RGBColor(0x1A, 0x1A, 0x1A)
PURPLE = RGBColor(0x5B, 0x2D, 0x8E)
GOLD   = RGBColor(0xB8, 0x96, 0x0C)
FOREST = RGBColor(0x1B, 0x5E, 0x20)


# ── Helpers ───────────────────────────────────────────────────────────────────

def shade_cell(cell, rgb):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    h    = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), h)
    tcPr.append(shd)


class Doc:
    def __init__(self):
        self.doc = Document()
        for s in self.doc.sections:
            s.top_margin    = Cm(2.5)
            s.bottom_margin = Cm(2.5)
            s.left_margin   = Cm(2.8)
            s.right_margin  = Cm(2.8)
        n = self.doc.styles["Normal"]
        n.font.name = "Calibri"
        n.font.size = Pt(10.5)
        n.font.color.rgb = BLACK

    def bar(self, colour=NAVY):
        t = self.doc.add_table(rows=1, cols=1)
        c = t.rows[0].cells[0]
        shade_cell(c, colour)
        c.paragraphs[0].add_run(" ")
        self.doc.add_paragraph()

    def h(self, text, lvl=1, colour=NAVY, size=None, bold=True,
          sb=10, sa=5, align=WD_ALIGN_PARAGRAPH.LEFT):
        p = self.doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(sb)
        p.paragraph_format.space_after  = Pt(sa)
        r = p.add_run(text)
        r.bold = bold; r.font.name = "Calibri"; r.font.color.rgb = colour
        r.font.size = Pt(size or {1:20,2:14,3:12,4:11}.get(lvl,11))
        return p

    def body(self, text, indent=False, bold=False, italic=False,
             colour=None, sa=5, sb=0, align=WD_ALIGN_PARAGRAPH.LEFT):
        p = self.doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after  = Pt(sa)
        p.paragraph_format.space_before = Pt(sb)
        if indent: p.paragraph_format.left_indent = Cm(0.8)
        r = p.add_run(text)
        r.bold = bold; r.italic = italic; r.font.name = "Calibri"; r.font.size = Pt(10.5)
        if colour: r.font.color.rgb = colour
        return p

    def bullet(self, text, lvl=0, prefix=None, colour=None):
        p = self.doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after  = Pt(3)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.left_indent  = Cm(0.8 + lvl * 0.6)
        if prefix:
            r1 = p.add_run(prefix + "  "); r1.bold = True
            r1.font.name = "Calibri"; r1.font.size = Pt(10.5)
        r2 = p.add_run(text); r2.font.name = "Calibri"; r2.font.size = Pt(10.5)
        if colour: r2.font.color.rgb = colour

    def divider(self, colour="007A87"):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(4)
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bot  = OxmlElement("w:bottom")
        bot.set(qn("w:val"),"single"); bot.set(qn("w:sz"),"6")
        bot.set(qn("w:space"),"1"); bot.set(qn("w:color"), colour)
        pBdr.append(bot); pPr.append(pBdr)

    def callout(self, text, fill=RGBColor(0xE8,0xF4,0xF7), tc=NAVY):
        t = self.doc.add_table(rows=1,cols=1)
        c = t.rows[0].cells[0]
        shade_cell(c, fill)
        p = c.paragraphs[0]
        p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent  = Cm(0.4); p.paragraph_format.right_indent = Cm(0.4)
        r = p.add_run(text); r.italic = True
        r.font.name = "Calibri"; r.font.size = Pt(10.5); r.font.color.rgb = tc
        self.doc.add_paragraph().paragraph_format.space_after = Pt(3)

    def table(self, headers, rows, hcol=NAVY, alt=True, fs=9.5):
        tbl = self.doc.add_table(rows=1+len(rows), cols=len(headers))
        tbl.style = "Table Grid"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(headers):
            c = tbl.rows[0].cells[i]; shade_cell(c, hcol)
            p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(h); r.bold = True
            r.font.name = "Calibri"; r.font.size = Pt(fs); r.font.color.rgb = WHITE
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                c = tbl.rows[ri+1].cells[ci]
                if alt and ri%2==1: shade_cell(c, RGBColor(0xEE,0xF3,0xFA))
                p = c.paragraphs[0]
                p.alignment = (WD_ALIGN_PARAGRAPH.LEFT if ci==0
                               else WD_ALIGN_PARAGRAPH.CENTER)
                r = p.add_run(str(val))
                r.font.name = "Calibri"; r.font.size = Pt(fs)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(3)

    def save(self, path):
        self.doc.save(path)
        size = os.path.getsize(path)/1024
        print(f"  Saved: {os.path.relpath(path, ROOT)} ({size:.1f} KB)")
        return path

    def pb(self): self.doc.add_page_break()
    def sp(self, pts=6):
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(pts)
        p.paragraph_format.space_before = Pt(0)


# =============================================================================
# ENGLISH DOCUMENT
# =============================================================================

def build_en():
    d = Doc()

    # ── Cover ──────────────────────────────────────────────────────────────────
    d.bar(FOREST)
    p = d.doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("From Minerals to Minutes")
    r.bold = True; r.font.name = "Calibri"
    r.font.size = Pt(30); r.font.color.rgb = FOREST

    p2 = d.doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("How Time Borrowing Redefines the Foundation\nof Economic Development and Human Equality")
    r2.bold = True; r2.font.name = "Calibri"
    r2.font.size = Pt(14); r2.font.color.rgb = NAVY

    d.sp(10)
    d.callout(
        '"For two centuries, the wealth of nations was measured by what lay beneath their soil. '
        'Time Borrowing proposes a different measure: what lives within their people — '
        'and gives everyone equal access to unlock it."'
    )
    d.sp(8)
    p3 = d.doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line, bold, colour, size in [
        ("Author: Enis Murseli", True,  NAVY, 12),
        ("Part of the Time Borrowing Research Framework", False, RGBColor(0x44,0x55,0x66), 10),
        ("May 2026", False, RGBColor(0x77,0x88,0x99), 10),
    ]:
        run = p3.add_run(line + "\n")
        run.bold = bold; run.font.name = "Calibri"
        run.font.size = Pt(size); run.font.color.rgb = colour
    d.pb()

    # ── Section 1: The Old Foundation ─────────────────────────────────────────
    d.h("1.  The Old Foundation of Development: What You Own", 1)
    d.divider()
    d.body(
        "For most of recorded economic history, the development of a nation depended "
        "overwhelmingly on two things: what natural resources it possessed and what "
        "physical capital it had accumulated. Oil, coal, iron ore, fertile land, navigable "
        "rivers, and strategic ports determined which countries grew rich and which stayed poor."
    )
    d.body(
        "This created a world where development was largely a geographical lottery. "
        "A country born above an oil field was structurally advantaged. A landlocked country "
        "with poor soil was structurally disadvantaged — regardless of the intelligence, "
        "creativity, or work ethic of its people."
    )

    d.h("1.1  The Resource Curse", 2, TEAL)
    d.body(
        "Paradoxically, the discovery of valuable natural resources often makes countries "
        "WORSE off over time — a well-documented phenomenon economists call the Resource Curse "
        "or Dutch Disease. The mechanism:"
    )
    for point in [
        "Resource extraction creates concentrated wealth for elites and foreign corporations",
        "The resource sector crowds out manufacturing and agriculture",
        "Currency appreciation from resource exports makes other exports uncompetitive",
        "Governments become dependent on resource revenues rather than building tax institutions",
        "Corruption and conflict over resource control destroy governance and trust",
        "When resources run out or prices fall, nothing else has been built",
    ]:
        d.bullet(point)
    d.body(
        "Nigeria, Venezuela, Libya, Angola, and the Democratic Republic of Congo all sit "
        "on enormous natural wealth. All have experienced the resource curse in varying degrees. "
        "Meanwhile, Singapore, South Korea, Switzerland, and Denmark — with almost no natural "
        "resources — became among the wealthiest nations on Earth.",
        italic=True, colour=RGBColor(0x33,0x44,0x55)
    )

    d.h("1.2  The Capital Accumulation Trap", 2, TEAL)
    d.body(
        "Even in resource-poor countries, traditional development theory said: "
        "accumulate capital first (save, attract foreign investment, borrow), "
        "then invest in people. The sequence was assumed to be:"
    )
    d.callout(
        "Step 1: Attract capital (foreign investment or debt)\n"
        "Step 2: Build physical infrastructure\n"
        "Step 3: Educate workers\n"
        "Step 4: Eventually, growth\n\n"
        "Problem: This requires starting with capital — which poor countries, "
        "by definition, do not have. Development aid, foreign loans, and resource "
        "extraction fill this gap — all with strings attached."
    )
    d.pb()

    # ── Section 2: The AI Disruption ──────────────────────────────────────────
    d.h("2.  The AI Disruption: Resources Become Less Relevant", 1)
    d.divider()
    d.body(
        "Artificial intelligence is rapidly decoupling economic output from physical resources. "
        "In the AI economy, the most valuable products — software, algorithms, creative content, "
        "financial services, biotechnology, advanced manufacturing — require minimal raw materials "
        "and can be produced anywhere with electricity and internet access."
    )
    d.table(
        ["Era", "Primary Input", "Where It Concentrates", "Who Benefits"],
        [
            ["Agricultural", "Fertile land", "Temperate zones", "Landowners"],
            ["Industrial",   "Coal, iron, energy", "Resource-rich nations", "Capital owners"],
            ["Information",  "Education, networks", "Cities with universities", "Educated workers"],
            ["AI",           "Compute + human talent", "Anywhere with talent + electricity", "Talent holders"],
        ], hcol=NAVY
    )
    d.body(
        "AI represents the first era in which the primary input — human cognitive talent — "
        "is distributed relatively equally across the globe. "
        "There are brilliant people in Mozambique, Bangladesh, Bolivia, and Albania. "
        "What they lack is not potential. What they lack is capital access."
    )
    d.callout(
        "Time Borrowing is the mechanism that converts this distributed potential "
        "into distributed capital — funded by the AI economy itself."
    )
    d.pb()

    # ── Section 3: Time as the Universal Resource ─────────────────────────────
    d.h("3.  Time: The Truly Universal Resource", 1)
    d.divider()
    d.body(
        "The core philosophical insight behind the Time Borrowing Instrument is this: "
        "while every other resource is unequally distributed, time is not."
    )
    d.table(
        ["Resource", "Who Has It?", "Can It Be Equalised?", "Can It Fund Development?"],
        [
            ["Oil reserves",       "7% of countries hold 80%", "No",         "Yes — but for the few"],
            ["Arable land",        "Geographically fixed",      "No",         "Yes — but limited"],
            ["Financial capital",  "Concentrated in wealthy",   "Partially",  "Yes — with interest burden"],
            ["Education systems",  "Quality varies enormously", "Over decades","Yes — slowly"],
            ["Human talent",       "Roughly equal globally",    "Yes",        "Yes — with capital access"],
            ["TIME",               "Everyone: 24hr/day",        "Already equal","YES — with Time Borrowing"],
        ], hcol=FOREST
    )
    d.sp(4)
    d.body(
        "A child born today in rural Albania has the same 24 hours as a child born in Zurich. "
        "They do not have the same capital access, the same schools, or the same family wealth. "
        "But they have the same time — and the same future contribution potential.",
        bold=False, italic=True, colour=NAVY
    )

    d.h("3.1  Properties of Time as Collateral", 2, TEAL)
    d.body("Unlike any other form of collateral, time has unique properties:")
    d.table(
        ["Property", "What It Means for Development"],
        [
            ["Universal",   "Every human being possesses it — no geographic lottery"],
            ["Equal",       "The same 24 hours for every person on Earth"],
            ["Non-seizable","You cannot repossess someone's future time by force"],
            ["Renewable",   "Each new generation brings fresh time collateral"],
            ["Non-depletable","Time cannot run out — unlike minerals or land"],
            ["Culturally neutral","Time has no ethnic, religious, or national character"],
            ["Productivity-linked","More education + time = more economic output"],
        ], hcol=TEAL
    )
    d.pb()

    # ── Section 4: How TB Redefines Development ───────────────────────────────
    d.h("4.  How Time Borrowing Redefines National Development", 1)
    d.divider()
    d.body(
        "Traditional development strategy asks: how do we attract capital, build infrastructure, "
        "and exploit our comparative advantages (usually natural resources or cheap labour)? "
        "Time Borrowing inverts this logic entirely."
    )

    d.h("4.1  The New Development Sequence", 2, TEAL)
    d.table(
        ["", "Traditional Sequence", "TB-Enabled Sequence"],
        [
            ["Starting point", "Attract foreign capital", "Implement TB + automation tax"],
            ["Step 1",         "Build physical infrastructure", "Fund human capital directly"],
            ["Step 2",         "Educate workers (slowly, expensively)", "TB advances fund education NOW"],
            ["Step 3",         "Grow manufacturing base", "Entrepreneurs start businesses with TB"],
            ["Step 4",         "Eventually reduce poverty", "Poverty reduces as FreeOne become Producers"],
            ["Driver",         "External capital (foreign debt or investment)", "Internal pool (automation tax)"],
            ["Risk",           "Debt dependency, conditionality, crises", "Self-contained, productivity-backed"],
            ["Beneficiary",    "Capital holders first, workers eventually", "Citizens directly, immediately"],
        ], hcol=NAVY
    )

    d.h("4.2  Breaking the Three Colonial Traps", 2, TEAL)
    d.body("Many developing nations remain caught in three structural traps inherited from colonialism. "
           "TB breaks all three:")
    for trap, mechanism, break_it in [
        ("Commodity Dependence",
         "Export raw materials, import manufactured goods — permanently disadvantaged terms of trade",
         "TB funds education and entrepreneurship, creating a domestic skilled workforce and manufacturing base"),
        ("Debt Dependency",
         "Development requires foreign loans with conditionality — structural adjustment, austerity, loss of sovereignty",
         "TB is funded by domestic automation tax — no foreign creditor, no conditionality, full sovereignty"),
        ("Brain Drain",
         "The best-educated citizens leave for richer countries with better capital access",
         "TB provides capital access at home — no need to emigrate to access investment in your own potential"),
    ]:
        d.h(f"Trap: {trap}", 3, RED, sb=8, sa=2)
        d.body(f"Traditional mechanism: {mechanism}", colour=RGBColor(0x55,0x22,0x22), italic=True)
        d.body(f"TB response: {break_it}", colour=GREEN)
    d.pb()

    # ── Section 5: Equality as Infrastructure ─────────────────────────────────
    d.h("5.  Equality as Economic Infrastructure", 1)
    d.divider()
    d.body(
        "In conventional economics, equality and growth are often presented as trade-offs: "
        "redistribute too much and you kill incentives; focus only on growth and inequality widens. "
        "Time Borrowing dissolves this false dichotomy."
    )
    d.body(
        "Under TB, equality is not a welfare outcome — it is productive infrastructure. "
        "When every citizen has access to capital regardless of their birth circumstances, "
        "the economy taps into a vastly larger pool of human potential. "
        "The talented child in a poor family who could not previously access education "
        "now becomes a producer, a taxpayer, an innovator."
    )

    d.h("5.1  The Untapped Talent Pool", 2, TEAL)
    d.callout(
        "Economists estimate that talent is roughly normally distributed across the global population. "
        "But access to resources that allow talent to be converted into economic output "
        "is massively skewed toward wealthy families and wealthy countries.\n\n"
        "Time Borrowing closes this gap. Not by redistributing wealth — "
        "but by giving every human being access to the capital their own future time represents."
    )

    d.h("5.2  What Equality of Access Produces", 2, TEAL)
    d.table(
        ["Without TB (Current System)", "With TB"],
        [
            ["Talented poor child: constrained to low-skill work", "Talented poor child: accesses education, enters skilled workforce"],
            ["Brilliant entrepreneur without collateral: idea stays in their head", "Brilliant entrepreneur: TB advance funds the startup"],
            ["Displaced worker: welfare dependency cycle", "Displaced worker: TB funds retraining, re-enters economy"],
            ["Small country with no resources: perpetual aid recipient", "Small country with no resources: TB funds human capital — competes globally"],
            ["GDP growth: limited by capital concentration", "GDP growth: distributed human potential unlocked"],
        ], hcol=FOREST
    )
    d.sp(4)

    d.h("5.3  The Gini Coefficient Is Not a Morality Metric — It Is an Efficiency Metric", 2, TEAL)
    d.body(
        "When the Time Borrowing simulation reduced the Gini coefficient from 0.358 to 0.323 "
        "over 25 years, it was not an act of charity. It was an efficiency gain. "
        "Talent that was previously locked in poverty was now contributing to output, "
        "paying taxes, and innovating. The economy became 59% larger — "
        "not despite the equality improvement, but because of it."
    )
    d.pb()

    # ── Section 6: New Development Metrics ────────────────────────────────────
    d.h("6.  New Metrics for a New Development Model", 1)
    d.divider()
    d.body(
        "If development is no longer primarily about resources and capital, "
        "the metrics by which we measure it must change."
    )
    d.table(
        ["Old Metric", "What It Measures", "New TB Metric", "What It Measures"],
        [
            ["GDP per capita",          "Average output (skewed by resources)", "Productivity per worker", "Human capital utilisation"],
            ["Export revenue",          "Mostly commodity prices",              "TB repayment rate", "Productive use of advances"],
            ["Foreign investment flows","Capital seeking returns",               "FreeOne→Producer rate", "Social mobility speed"],
            ["Infrastructure spend",    "Physical capital",                      "Education completion rate", "Human capital formation"],
            ["Sovereign credit rating", "Debt repayment capacity",               "TB pool solvency ratio", "Instrument sustainability"],
            ["Gini coefficient",        "Post-transfer inequality",              "Pre-TB access equality", "Capital access fairness"],
            ["Resource reserves",       "Geological lottery",                   "Youth population size", "Future time collateral pool"],
        ], hcol=NAVY
    )
    d.sp(4)
    d.body(
        "Under this framework, a country with a large young population and no oil — "
        "like Albania, Ethiopia, or the Philippines — is not resource-poor. "
        "It is time-rich. Its youth population represents an enormous pool of "
        "future collateral for Time Borrowing advances.",
        bold=True, colour=NAVY
    )
    d.pb()

    # ── Section 7: Country archetypes ─────────────────────────────────────────
    d.h("7.  How Different Countries Benefit", 1)
    d.divider()

    archetypes = [
        ("Resource-Dependent Economies (Gulf States, Nigeria, Angola)",
         AMBER,
         "These countries face an existential transition as AI reduces demand for fossil fuels "
         "and automation displaces workers. TB offers a pathway: redirect automation tax revenue "
         "from AI-enabled oil operations into a TB pool that funds diversification. "
         "Sovereign wealth built from oil can seed TB pools at scale.",
         [
             "TB funds education in technology, healthcare, engineering — not just oil industry",
             "Automation tax on AI-managed extraction creates a self-funding TB pool",
             "Displaced oil workers retrain via TB rather than becoming welfare dependent",
             "Country transitions from oil-dependent to knowledge-based economy over 15–25 years",
         ]),
        ("Middle-Income Trap Countries (Malaysia, Colombia, Brazil, Turkey)",
         TEAL,
         "These countries have escaped extreme poverty but cannot break into high-income status. "
         "They are stuck competing on low wages against poorer countries, and on technology "
         "against richer ones. TB breaks the trap by funding the human capital upgrade:",
         [
             "TB funds university education and vocational retraining at scale",
             "Entrepreneurship is unlocked for citizens without family collateral",
             "Innovation clusters emerge as TB-funded graduates and entrepreneurs interact",
             "Wage competition gives way to productivity competition",
         ]),
        ("Least Developed Countries (Sub-Saharan Africa, South Asia)",
         FOREST,
         "These nations benefit most from TB's leapfrog potential. Without a legacy welfare "
         "bureaucracy to dismantle, they can implement TB from scratch as their primary "
         "social development mechanism. Their youth bulge becomes an asset, not a liability.",
         [
             "TB replaces the need for foreign aid with a self-sustaining domestic instrument",
             "Mobile-first TB registry can reach unbanked populations immediately",
             "Large youth population = enormous future time collateral pool",
             "No colonial debt cycle: TB funded by domestic automation tax, not foreign creditors",
         ]),
        ("Small Developed Nations (Albania, Estonia, Singapore, New Zealand)",
         PURPLE,
         "These nations have high human capital but limited scale. TB allows them to "
         "maximise their most competitive asset — educated, motivated citizens — "
         "by ensuring no talent is lost to lack of capital access.",
         [
             "TB eliminates emigration driven by lack of domestic capital access",
             "Every citizen can start a business or study regardless of family wealth",
             "Small populations mean TB pool is proportionally large per person",
             "First-mover advantage: becoming a TB pioneer builds international reputation",
         ]),
    ]

    for title, colour, description, bullets in archetypes:
        d.h(title, 2, colour, sb=12, sa=3)
        d.body(description)
        for b in bullets:
            d.bullet(b)
        d.sp(4)

    d.pb()

    # ── Section 8: The Geopolitics of Development ─────────────────────────────
    d.h("8.  Development Without Dependency", 1)
    d.divider()
    d.body(
        "One of the least-discussed but most important features of Time Borrowing is "
        "what it does NOT require: permission from anyone else."
    )
    d.body(
        "Every other major development instrument creates a dependency relationship:"
    )
    d.table(
        ["Instrument", "Who Controls It", "Dependency Created"],
        [
            ["World Bank loans",        "Rich country shareholders", "Policy conditionality"],
            ["IMF structural adjustment","Washington consensus",      "Austerity requirements"],
            ["Foreign Direct Investment","Corporate profit motive",   "Profit repatriation"],
            ["Development aid",         "Donor country priorities",   "Reporting, branding, agenda"],
            ["Export-led growth",       "Global commodity markets",   "Price volatility"],
            ["Time Borrowing",          "The country itself",         "NONE — fully sovereign"],
        ], hcol=NAVY
    )
    d.sp(4)
    d.callout(
        "A country that implements the Time Borrowing Instrument is not asking a foreign "
        "bank for money. It is not selling its resources to a foreign corporation. "
        "It is taxing the automation that is already running in its economy "
        "and redirecting that value to its own citizens. "
        "No permission required. No debt incurred. No sovereignty surrendered."
    )
    d.pb()

    # ── Section 9: The Vision ──────────────────────────────────────────────────
    d.h("9.  The Vision: A World Measured in Time and Talent", 1)
    d.divider()
    d.body(
        "Imagine a world in which the development trajectory of a country is no longer "
        "determined by what lies beneath its soil, but by what lives within its people — "
        "and where every person has equal access to unlock that potential."
    )
    d.body(
        "In this world:"
    )
    for point in [
        "A young woman in Tirana with a brilliant engineering idea has the same capital access as one in Munich",
        "A farmer displaced by agricultural automation in Bangladesh can retrain as a data analyst — funded by the automation that displaced him",
        "A country with no oil but a young population of 30 million has a TB collateral pool worth more than its geological resources",
        "Development rankings are determined by human capital utilisation rates, not sovereign wealth funds",
        "The phrase 'brain drain' becomes obsolete — because talent has capital access at home",
        "Equality is not a welfare outcome — it is the engine of growth",
    ]:
        d.bullet(point)

    d.sp(8)
    d.body(
        "This is not a utopia. It is a mathematical consequence of implementing one instrument correctly. "
        "The simulation showed it works at small scale. The theory shows it scales. "
        "The geopolitics shows it spreads once started. "
        "The only missing piece is the political will to begin.",
        bold=True, colour=NAVY
    )
    d.sp(8)
    d.table(
        ["The Old World", "The TB World"],
        [
            ["Development = resources + capital",           "Development = time + talent + equal access"],
            ["Wealth = what you own",                      "Wealth = what you can contribute"],
            ["Collateral = assets you already have",       "Collateral = future you will create"],
            ["Poor country = disadvantaged",               "Poor country = time-rich"],
            ["Inequality = inevitable by-product",        "Equality = productive infrastructure"],
            ["AI = threat to workers",                    "AI = funding mechanism for workers"],
            ["Born poor = likely to stay poor",           "Born anywhere = equal capital access"],
        ], hcol=FOREST
    )
    d.pb()

    # ── Appendix ──────────────────────────────────────────────────────────────
    d.h("Appendix: Key Concepts Defined", 1, NAVY)
    d.divider()
    for term, defn in [
        ("Resource Curse", "The paradox where resource-rich countries often experience slower growth, more conflict, and worse institutions than resource-poor ones."),
        ("Dutch Disease", "When a natural resource boom strengthens a currency, making other exports uncompetitive and destroying non-resource industries."),
        ("Human Capital", "The economic value of a person's skills, knowledge, experience, and productivity capacity."),
        ("Time Collateral", "In the TB framework: a citizen's future contribution — their working time, taxes paid, community value created — used as collateral instead of financial assets."),
        ("Middle-Income Trap", "When a developing economy reaches middle income levels but cannot transition to high income due to loss of cheap-labour competitiveness and inability to innovate."),
        ("Leapfrogging", "When a developing country skips an entire stage of technological development (e.g., mobile phones skipped landlines; TB can skip traditional welfare bureaucracy)."),
        ("Brain Drain", "Emigration of skilled workers from developing to developed countries, depriving the origin country of its human capital investment."),
        ("Gini Coefficient", "Measures inequality: 0 = perfectly equal distribution of income/wealth, 1 = all income/wealth held by one person."),
        ("Automation Tax", "A levy on the economic output or productivity savings generated by AI and robotic systems — the TB pool's primary revenue source."),
        ("FreeOne → Producer", "The TB conversion metric: citizens in the FreeOne category (students, unemployed, NEET) who, through TB-funded education or entrepreneurship, enter the Producer category."),
    ]:
        p = d.doc.add_paragraph()
        p.paragraph_format.space_after  = Pt(4)
        p.paragraph_format.left_indent  = Cm(0.5)
        r1 = p.add_run(term + ": "); r1.bold = True
        r1.font.name = "Calibri"; r1.font.size = Pt(10)
        r2 = p.add_run(defn)
        r2.font.name = "Calibri"; r2.font.size = Pt(10)

    d.sp(8)
    p_close = d.doc.add_paragraph()
    p_close.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c = p_close.add_run(
        "Author: Enis Murseli  |  Time Borrowing Research Framework  |  May 2026\n"
        "Full simulation, code, and proof: github.com/[your-repo]"
    )
    r_c.italic = True; r_c.font.name = "Calibri"
    r_c.font.size = Pt(9); r_c.font.color.rgb = RGBColor(0x77,0x88,0x99)

    return d.save(os.path.join(OUT_EN, "Time_Borrowing_Development_and_Equality.docx"))


# =============================================================================
# ALBANIAN DOCUMENT
# =============================================================================

def build_sq():
    d = Doc()

    d.bar(FOREST)
    p = d.doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("Nga Mineralet te Minutat")
    r.bold = True; r.font.name = "Calibri"
    r.font.size = Pt(30); r.font.color.rgb = FOREST

    p2 = d.doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Si Huazimi i Kohës Rindërton Themelet e\nZhvillimit Ekonomik dhe Barazisë Njerëzore")
    r2.bold = True; r2.font.name = "Calibri"
    r2.font.size = Pt(14); r2.font.color.rgb = NAVY

    d.sp(10)
    d.callout(
        '"Për dy shekuj, pasuria e kombeve matet nga ç\'ka shtrihet nën tokën e tyre. '
        'Huazimi i Kohës propozon një masë tjetër: ç\'ka jeton brenda njerëzve të tyre — '
        'dhe u jep të gjithëve qasje të barabartë për ta çliruar atë."'
    )
    d.sp(8)
    p3 = d.doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line, bold, colour, size in [
        ("Autori: Enis Murseli", True,  NAVY, 12),
        ("Pjesë e Kornizës Kërkimore të Huazimit të Kohës", False, RGBColor(0x44,0x55,0x66), 10),
        ("Maj 2026", False, RGBColor(0x77,0x88,0x99), 10),
    ]:
        run = p3.add_run(line + "\n")
        run.bold = bold; run.font.name = "Calibri"
        run.font.size = Pt(size); run.font.color.rgb = colour
    d.pb()

    # S1
    d.h("1.  Themeli i Vjetër i Zhvillimit: Çfarë Zotëron", 1)
    d.divider()
    d.body("Për pjesën më të madhe të historisë ekonomike, zhvillimi i një kombi varej kryesisht nga dy gjëra: çfarë burime natyrore zotëronte dhe çfarë kapitali fizik kishte akumuluar. Nafta, qymyri, xeherori i hekurit, toka pjellore, lumenjtë e lundrueshëm dhe portet strategjike përcaktonin cilat vende u pasuruan dhe cilat mbetën të varfra.")
    d.body("Kjo krijoi një botë ku zhvillimi ishte kryesisht një lotari gjeografike. Një vend i lindur mbi një fushë nafte kishte avantazh strukturor. Një vend pa dalje në det me tokë të dobët ishte strukturalisht i disfavorizuar — pavarësisht nga inteligjenca, kreativiteti ose vullneti i punës i njerëzve të tij.")

    d.h("1.1  Mallkimi i Burimeve", 2, TEAL)
    d.body("Paradoksalisht, zbulimi i burimeve natyrore të vlefshme shpesh e bën vendin MË KEQ me kalimin e kohës — një fenomen i dokumentuar mirë që ekonomistët e quajnë Mallkimi i Burimeve ose Sëmundja Holandeze. Mekanizmi:")
    for p in ["Nxjerrja e burimeve krijon pasuri të koncentruar për elitat dhe korporatat e huaja",
              "Sektori i burimeve i zë vendin bujqësisë dhe industrisë",
              "Vlerësimi i monedhës nga eksportet e burimeve i bën eksportet e tjera jo konkurruese",
              "Qeveritë bëhen të varura nga të ardhurat e burimeve në vend që të ndërtojnë institucione tatimore",
              "Korrupsioni dhe konflikti mbi kontrollin e burimeve shkatërrojnë qeverisjen",
              "Kur burimet mbarojnë ose çmimet bien, asgjë tjetër nuk është ndërtuar"]:
        d.bullet(p)
    d.body("Nigeria, Venezuela, Libia, Angola dhe Republika Demokratike e Kongos të gjitha kanë pasuri natyrore të jashtëzakonshme. Të gjitha kanë përjetuar mallkimin e burimeve. Ndërkohë, Singapori, Koreja e Jugut, Zvicra dhe Danimarka — pa pothuajse asnjë burim natyror — u bënë ndër kombet më të pasura në Tokë.", italic=True, colour=RGBColor(0x33,0x44,0x55))

    d.h("1.2  Kurtha e Akumulimit të Kapitalit", 2, TEAL)
    d.callout("Hapi 1: Tërhiq kapital (investim të huaj ose borxh)\nHapi 2: Ndërto infrastrukturë fizike\nHapi 3: Arsimoji punëtorët (ngadalë, me kosto të lartë)\nHapi 4: Në fund, rritja\n\nProblemi: Kjo kërkon kapital si pikënisje — të cilin vendet e varfra, sipas definicionit, nuk e kanë.")
    d.pb()

    # S2
    d.h("2.  Ndërprerja nga AI: Burimet Bëhen Më Pak Relevante", 1)
    d.divider()
    d.body("Inteligjenca artificiale po ndan prodhimin ekonomik nga burimet fizike. Në ekonominë e AI-t, produktet më me vlerë — softueri, algoritmet, shërbimet financiare, bioteknologjia — kërkojnë lëndë të parë minimale dhe mund të prodhohen kudo me rrymë dhe internet.")
    d.table(["Era","Input kryesor","Ku përqendrohet","Kush përfiton"],
            [["Bujqësorë","Tokë pjellore","Zonat e buta","Pronarët e tokës"],
             ["Industriale","Qymyr, hekur, energji","Kombet me burime","Pronarët e kapitalit"],
             ["Informacioni","Arsim, rrjete","Qytete me universitete","Punëtorët e arsimuar"],
             ["AI","Kompjutim + talenti njerëzor","Kudo me talent + rrymë","Mbajtësit e talentit"]], hcol=NAVY)
    d.callout("Huazimi i Kohës është mekanizmi që shndërron këtë potencial të shpërndarë në kapital të shpërndarë — financuar nga vetë ekonomia e AI-t.")
    d.pb()

    # S3
    d.h("3.  Koha: Burimi Vërtet Universal", 1)
    d.divider()
    d.body("Ndërkohë që çdo burim tjetër është shpërndarë në mënyrë të pabarabartë, koha nuk është.")
    d.table(["Burimi","Kush e ka?","Mund të barazohet?","Mund të financojë zhvillimin?"],
            [["Rezervat e naftës","7% e vendeve mbajnë 80%","Jo","Po — por për pakicën"],
             ["Tokë bujqësore","E fiksuar gjeografikisht","Jo","Po — por e kufizuar"],
             ["Kapital financiar","Koncentruar tek të pasurit","Pjesërisht","Po — me barrë interesi"],
             ["Talenti njerëzor","Shpërndarë përgjithësisht","Po","Po — me qasje kapitali"],
             ["KOHA","Të gjithë: 24 orë/ditë","Tashmë e barabartë","PO — me Huazimin e Kohës"]], hcol=FOREST)
    d.body("Një fëmijë i lindur sot në Shqipërinë rurale ka të njëjtat 24 orë si një fëmijë i lindur në Cyrih. Nuk kanë të njëjtën qasje kapitali, të njëjtat shkolla apo pasuri familjare. Por kanë të njëjtën kohë — dhe të njëjtin potencial kontributi të ardhshëm.", bold=False, italic=True, colour=NAVY)

    d.h("3.1  Vetitë e Kohës si Kolateral", 2, TEAL)
    d.table(["Vetia","Çfarë do të thotë për zhvillimin"],
            [["Universale","Çdo qenie njerëzore e zotëron — asnjë lotari gjeografike"],
             ["E barabartë","Të njëjtat 24 orë për çdo person në Tokë"],
             ["E pazëvëndësueshme me forcë","Nuk mund t'i marrësh dikujt kohën e ardhshme me forcë"],
             ["E rinovueshme","Çdo brez i ri sjell kolateral të ri kohe"],
             ["E pandashme","Koha nuk mund të mbarojë — ndryshe nga mineralet"],
             ["Neutrale kulturalisht","Koha nuk ka karakter etnik, fetar apo kombëtar"],
             ["E lidhur me produktivitetin","Më shumë arsim + kohë = më shumë prodhim ekonomik"]], hcol=TEAL)
    d.pb()

    # S4
    d.h("4.  Si Huazimi i Kohës Rindërton Zhvillimin Kombëtar", 1)
    d.divider()
    d.table(["","Sekuenca Tradicionale","Sekuenca me TB"],
            [["Pikënisja","Tërhiq kapital të huaj","Zbato TB + taksë automatizimi"],
             ["Hapi 1","Ndërto infrastrukturë fizike","Financo kapitalin njerëzor direkt"],
             ["Hapi 2","Arsimoji punëtorët (ngadalë, shtrenjt)","Avanca TB financojnë arsimin TANI"],
             ["Hapi 3","Rrit bazën e prodhimit","Sipërmarrësit nisin biznese me TB"],
             ["Hapi 4","Në fund ulje e varfërisë","Varfëria ulet ndërsa FreeOne bëhen Prodhues"],
             ["Drejtues","Kapital i jashtëm (borxh ose investim)","Fond i brendshëm (taksë automatizimi)"],
             ["Rreziku","Varësia nga borxhi, kushtet","Vetë-i mbyllur, mbështetur nga produktiviteti"]], hcol=NAVY)

    d.h("4.2  Thyerja e Tre Kurtheve Koloniale", 2, TEAL)
    for trap, mek, thyerje in [
        ("Varësia nga mallrat",
         "Eksporto lëndë të para, importo produkte të gatshme — terma shkëmbimi përgjithmonë të disfavorshme",
         "TB financon arsimin dhe sipërmarrjen, duke krijuar një fuqi punëtore të aftë brenda vendit"),
        ("Varësia nga Borxhi",
         "Zhvillimi kërkon kredi të huaja me kushte — rregullim strukturor, kursim, humbje sovraniteti",
         "TB financohet nga taksa e brendshme e automatizimit — asnjë huadhënës i huaj, asnjë kusht, sovranitet i plotë"),
        ("Ikja e Trutë",
         "Qytetarët më të arsimuar largohen për vende më të pasura me qasje më të mirë kapitali",
         "TB ofron qasje kapitali në shtëpi — nuk ka nevojë të emigrosh për të investuar në potencialin tënd"),
    ]:
        d.h(f"Kurtha: {trap}", 3, RED, sb=8, sa=2)
        d.body(f"Mekanizmi tradicional: {mek}", colour=RGBColor(0x55,0x22,0x22), italic=True)
        d.body(f"Përgjigja e TB: {thyerje}", colour=GREEN)
    d.pb()

    # S5
    d.h("5.  Barazia si Infrastrukturë Ekonomike", 1)
    d.divider()
    d.body("Në ekonominë tradicionale, barazia dhe rritja shpesh paraqiten si shkëmbime: rindaj shumë dhe vrasësh stimujt; fokusohu vetëm tek rritja dhe pabarazia zgjerohet. Huazimi i Kohës e shpërbën këtë dichotomi të rreme.")
    d.body("Nën TB, barazia nuk është një rezultat mirëqenieje — është infrastrukturë prodhuese. Kur çdo qytetar ka qasje kapital pavarësisht rrethanave të lindjes, ekonomia prek një grup shumë më të madh të potencialit njerëzor.")
    d.callout("Simulimi ynë tregoi se Gini-ja u ul nga 0.358 në 0.323 gjatë 25 viteve. Kjo nuk ishte bamirësi. Ishte fitim efikasiteti. Talenti i bllokuar në varfëri tani kontribuonte, paguante taksa dhe inovonte. Ekonomia u bë 59% më e madhe — jo pavarësisht përmirësimit të barazisë, por për shkak të tij.")
    d.pb()

    # S6
    d.h("6.  Metrika e Re për Model të Ri Zhvillimi", 1)
    d.divider()
    d.table(["Metrika e Vjetër","Çfarë Mat","Metrika e Re TB","Çfarë Mat"],
            [["PBB për frymë","Prodhimi mesatar (i shtrembëruar nga burimet)","Produktiviteti për punëtor","Shfrytëzimi i kapitalit njerëzor"],
             ["Të ardhurat nga eksportet","Kryesisht çmimet e mallrave","Norma e shlyerjes TB","Përdorimi produktiv i avancave"],
             ["Flukset e investimit të huaj","Kapitali kërkon kthime","Norma FreeOne→Prodhues","Shpejtësia e mobilitetit social"],
             ["Madhësia e rezervave","Lotaria gjeologjike","Madhësia e popullsisë së re","Kolateral i ardhshëm i kohës"]], hcol=NAVY)
    d.body("Nën këtë kornizë, një vend me popullsi të madhe të re dhe pa naftë — si Shqipëria, Etiopia ose Filipinet — nuk është i varfër në burime. Është i pasur në kohë.", bold=True, colour=NAVY)
    d.pb()

    # S7 condensed
    d.h("7.  Si Përfitojnë Vende të Ndryshme", 1)
    d.divider()
    d.table(["Tipi i vendit","Situata tani","Si ndihmon TB"],
            [["Vende me burime (Golfi, Afrika)","Varësia nga nafta, kurba holandeze","Taksa e automatizimit nga nxjerrja AI financon rikualifikimin"],
             ["Kurthi i të ardhurave mesatare (Brasil, Turqi)","Bllokuar midis punës së lirë dhe teknologjisë","TB financon kapital njerëzor për të dalë nga kurthi"],
             ["Vendet më pak të zhvilluara (Afrika Sub-Sahariane)","Varësia nga ndihmat, borxhi i jashtëm","TB zëvendëson ndihmat me instrument sovran, vetë-qëndrueshëm"],
             ["Vende të vogla të zhvilluara (Shqipëria, Estonia)","Largim i talenteve, qasje e kufizuar kapitalit","TB mban talentin brenda vendit, çliron çdo qytetar"]], hcol=FOREST)
    d.pb()

    # S8
    d.h("8.  Zhvillim pa Varësi", 1)
    d.divider()
    d.callout("Një vend që zbaton Huazimin e Kohës nuk po kërkon para nga një bankë e huaj. Nuk po i shet burimet e veta një korporate të huaj. Po tatçon automatizimin që tashmë funksionon në ekonominë e tij dhe po ridrejton atë vlerë tek qytetarët e vet. Asnjë leje e nevojshme. Asnjë borxh i bërë. Asnjë sovranitet i dorëzuar.")
    d.pb()

    # S9 Vision
    d.h("9.  Vizioni: Një Botë e Matur në Kohë dhe Talent", 1)
    d.divider()
    for point in [
        "Një vajzë e re në Tiranë me një ide inxhinierike të shkëlqyer ka të njëjtën qasje kapitali si një në Mynih",
        "Një bujk i zhvendosur nga automatizimi bujqësor në Bangladesh mund të rikualifikohet si analist të dhënash — financuar nga automatizimi që e zhvendosi",
        "Një vend pa naftë por me popullsi të re prej 30 milionësh ka fond kolaterali TB që vlen më shumë se burimet e tij gjeologjike",
        "Termi 'ikja e trutë' bëhet i vjetëruar — sepse talenti ka qasje kapitali në shtëpi",
        "Barazia nuk është rezultat mirëqenieje — është motori i rritjes",
    ]:
        d.bullet(point)
    d.sp(8)
    d.table(["Bota e Vjetër","Bota e TB"],
            [["Zhvillimi = burime + kapital","Zhvillimi = kohë + talent + qasje e barabartë"],
             ["Pasuria = çfarë zotëron","Pasuria = çfarë mund të kontribuosh"],
             ["Kolateral = asete që tashmë ke","Kolateral = e ardhmja që do të krijosh"],
             ["Vend i varfër = i disfavorizuar","Vend i varfër = i pasur në kohë"],
             ["Pabarazia = produkt anësor i pashmangshëm","Barazia = infrastrukturë prodhuese"],
             ["AI = kërcënim për punëtorët","AI = mekanizëm financimi për punëtorët"],
             ["Lindur i varfër = do të mbetesh i varfër","Lindur kudo = qasje e barabartë kapitali"]], hcol=FOREST)

    d.sp(8)
    p_close = d.doc.add_paragraph()
    p_close.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_c = p_close.add_run("Autori: Enis Murseli  |  Korniza Kërkimore e Huazimit të Kohës  |  Maj 2026")
    r_c.italic = True; r_c.font.name = "Calibri"
    r_c.font.size = Pt(9); r_c.font.color.rgb = RGBColor(0x77,0x88,0x99)

    return d.save(os.path.join(OUT_SQ, "Zhvillimi_dhe_Barazimi_-_Huazimi_i_Kohes.docx"))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  BUILDING: Development & Equality Documents")
    print("=" * 60)
    p1 = build_en()
    p2 = build_sq()
    print("\nDone.")
