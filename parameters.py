"""
parameters.py
=============
All verified calibration constants and the EconomyState dataclass.

CORRECTION LOG (vs. original parameters.py):
─────────────────────────────────────────────────────────────────────────────
INCOME_TAX_RATE:
  Old value: 0.237  (this was PIT as % of TOTAL TAX REVENUE — wrong use)
  Correct  : 0.133  (PIT as % of total LABOR COST, Tax Foundation 2024)
  Source   : "Tax Burden on Labor in the OECD 2024" — income taxes = 13.3%
             of average labor cost. OECD "Taxing Wages 2023": avg PIT rate
             on gross wages = 13.3%. Tax wedge (incl SSC) = 34.8%.

MPC (Marginal Propensity to Consume):
  Old value: 0.75  (textbook Keynesian assumption — not empirically grounded)
  Correct  : 0.45  (central OECD empirical estimate)
  Sources  : Jappelli & Pistaferri 2014 → 0.46 (euro area avg)
             Ramey 2023 → 0.30-0.40 (corrected micro estimates)
             Sokolova 2022 meta-analysis → general pop 0.20-0.35
  Impact   : Keynesian multiplier = 1/(1-0.45) = 1.82 (vs textbook 4.0)
             This is consistent with IMF empirical range 0.8-2.5.

BASE_PRODUCTIVITY_GROWTH (TFP):
  Old value: 0.015 (1.5%/yr — slightly optimistic)
  Correct  : 0.010 (1.0%/yr — OECD Compendium of Productivity Indicators 2024)
  Sources  : CRS Report R48695: TFP avg 0.9%/yr (2000-2024)
             OECD Productivity Compendium 2024: 0.9-1.2%/yr
  Note     : AUTOMATION_BOOST of 0.5% kept, giving total TFP = 1.5%.
             This represents an AI-augmented productivity scenario.

SOCIAL_SECURITY_RATE:
  Old value: 0.248 (this was SSC as % of TOTAL TAX REVENUE — wrong use)
  Correct  : 0.081 employee side + 0.134 employer side = 0.215 combined
             But employee-side only: 8.1% of labor cost (Tax Foundation 2024)
  Source   : Tax Foundation "Tax Burden on Labor OECD 2024"

TAX_TO_GDP_RATIO:
  Old: 0.339 | Updated to 0.337 (OECD Revenue Statistics 2025, 2023 final data)
─────────────────────────────────────────────────────────────────────────────
"""

from dataclasses import dataclass, field
from typing import Dict


# ===========================================================================
# VERIFIED CALIBRATION CONSTANTS
# ===========================================================================

# ── Population & Labour [UN WPP 2024; OECD Employment Outlook 2025] ─────────
NATURAL_GROWTH_RATE       = 0.011   # 1.1%/yr OECD natural pop growth (birth+immigration)
CARRYING_CAPACITY_MULT    = 50.0    # Logistic cap = initial_pop × 50
LABOR_PARTICIPATION_RATE  = 0.766   # 76.6% of working-age (OECD Q1 2025)
WORKING_AGE_SHARE         = 0.65    # ~65% of total pop is 15-64 (OECD demographics)
EMPLOYMENT_RATE_WA        = 0.702   # 70.2% of working-age population employed

# ── Tax Rates [OECD Revenue Statistics 2025; Tax Foundation 2024] ────────────
# PIT as % of LABOR COST (Tax Foundation "Taxing Wages" methodology):
INCOME_TAX_RATE           = 0.133   # 13.3% effective PIT rate on total labor cost
                                    # NOT 23.7% (that is PIT's share of total tax revenue)

# Employee-side Social Security Contributions as % of labor cost:
SSC_EMPLOYEE_RATE         = 0.081   # 8.1% employee SSC (Tax Foundation 2024)
# Employer-side SSC (adds to total labor cost):
SSC_EMPLOYER_RATE         = 0.134   # 13.4% employer SSC (Tax Foundation 2024)
# Combined tax wedge = PIT + SSC_employee + SSC_employer = 34.8%
TOTAL_TAX_WEDGE           = 0.348   # OECD average 2023 (Tax Foundation 2024)

VAT_RATE                  = 0.192   # 19.2% standard VAT rate (OECD avg 2023)
CORPORATE_TAX_RATE        = 0.236   # 23.6% corporate income tax (OECD avg 2023)
TAX_TO_GDP_RATIO          = 0.337   # 33.7% total tax / GDP (OECD 2023 final)

# ── MPC [Empirical — multiple sources] ───────────────────────────────────────
MPC = 0.45   # Economy-wide average MPC
             # OLD value was 0.75 (textbook, not empirical)
             # NEW: 0.45 consistent with Jappelli & Pistaferri (2014) = 0.46
             #      Ramey (2023) corrected micro = 0.30-0.40
             #      This gives multiplier = 1/(1-0.45) = 1.82 (empirically plausible)
MPS = 1 - MPC   # 0.55 — Marginal Propensity to Save

# ── Monetary [IMF; ECB; Fed Historical] ─────────────────────────────────────
MONEY_VELOCITY            = 1.5     # Velocity of money V in MV=PY (moderate economy)
NOMINAL_INTEREST_RATE     = 0.045   # 4.5% nominal (post-2022 OECD tightening cycle)
LONG_RUN_INTEREST_RATE    = 0.025   # 2.5% long-run neutral real rate (Laubach-Williams)
INFLATION_TARGET          = 0.02    # 2.0% central bank target (universal OECD standard)

# ── Productivity [OECD Compendium of Productivity Indicators 2024; CRS R48695] ─
BASE_PRODUCTIVITY_GROWTH  = 0.010   # 1.0% TFP/yr (OECD 2000-2024 avg = 0.9-1.0%)
                                    # OLD was 0.015 — corrected downward
AUTOMATION_BOOST          = 0.005   # +0.5% from AI/automation (forward-looking estimate)
TOTAL_TFP_GROWTH          = BASE_PRODUCTIVITY_GROWTH + AUTOMATION_BOOST  # 1.5%
CAPITAL_SHARE_ALPHA       = 0.33    # α in Solow (Gollin 2002; standard estimate)
DEPRECIATION_RATE         = 0.05    # 5% capital depreciation/yr (OECD avg)

# ── Government Spending [OECD Fiscal Monitor] ───────────────────────────────
WELFARE_RATE              = 0.12    # 12% GDP on social protection (OECD avg)
GOVT_INVESTMENT_RATE      = 0.03    # 3% GDP on public infrastructure investment
DEFICIT_TOLERANCE         = 0.03    # 3% of GDP (Maastricht criterion reference)

# ── Time Borrowing Instrument Defaults ───────────────────────────────────────
TB_AUTOMATION_TAX_RATE    = 0.15    # 15% levy on AI/automation output value
TB_MAX_PERIOD_YEARS       = 5       # Maximum TB advance window in years
TB_MIN_AMOUNT             = 500     # Minimum TB advance (ACU)
TB_MAX_AMOUNT             = 5000    # Maximum TB advance per person per cycle
TB_REPAYMENT_MIN_PCT      = 0.30    # 30% — below this triggers TDRW freeze
TB_DEFAULT_FREEZE_BASE    = 2.0     # Base freeze years for full default (3yr TB)
TB_AUTOMATION_GROWTH      = 0.10    # 10%/yr growth in automation output


# ===========================================================================
# ECONOMY STATE DATACLASS
# ===========================================================================

@dataclass
class EconomyState:
    """
    Complete snapshot of the economy at a single year.
    All monetary values in Abstract Currency Units (ACU).
    All rates as decimals (0.05 = 5%).
    """

    # ── Time ────────────────────────────────────────────────────────────────
    year: int = 0

    # ── Demographics ────────────────────────────────────────────────────────
    population: float = 10.0
    n_government: float = 1.0       # 10% of population
    n_producer: float = 4.0         # 40% of population
    n_freeone: float = 5.0          # 50% of population
    n_consumer: float = 10.0        # 100% of population

    # ── Money & Prices ──────────────────────────────────────────────────────
    money_supply: float = 1000.0    # M — circulating money (ACU)
    price_level: float = 1.0        # P — aggregate price index (base = 1.0)
    inflation: float = 0.02         # π — annual % change in price level
    nominal_interest_rate: float = NOMINAL_INTEREST_RATE   # i
    real_interest_rate: float = 0.025  # r = i - π

    # ── Production & Consumption ────────────────────────────────────────────
    resources_produced: float = 1000.0   # Y — GDP equivalent
    resources_consumed: float = 750.0    # C — aggregate consumption
    investment: float = 200.0            # I — capital investment
    government_spend: float = 150.0      # G — government expenditure

    # ── Labour ──────────────────────────────────────────────────────────────
    employment_rate: float = 0.702       # Share of working-age pop employed (OECD 2025)
    productivity_per_worker: float = 100.0

    # ── Fiscal ──────────────────────────────────────────────────────────────
    tax_revenue: float = 0.0
    tax_rate_effective: float = TAX_TO_GDP_RATIO
    government_balance: float = 0.0
    cumulative_debt: float = 0.0

    # ── Time Borrowing ───────────────────────────────────────────────────────
    tb_pool_size: float = 100.0
    tb_amount_issued: float = 0.0
    tb_repayments_received: float = 0.0
    tb_loss_rate: float = 0.05
    tb_active_borrowers: int = 0
    tb_defaulters: int = 0
    tb_injection_needed: float = 0.0
    automation_tax_collected: float = 0.0

    # ── Inflation drivers ────────────────────────────────────────────────────
    supply_shock: float = 0.0
    demand_pull: float = 0.0
    cost_push: float = 0.0

    # ── Welfare ─────────────────────────────────────────────────────────────
    welfare_spend: float = 0.0
    gini_coefficient: float = 0.35  # OECD avg Gini ~0.31-0.38 [OECD 2023]

    # ── Logs ─────────────────────────────────────────────────────────────────
    relationship_transactions: Dict[str, float] = field(default_factory=dict)
    delta_log: Dict[str, float] = field(default_factory=dict)


# ===========================================================================
# INITIAL STATE BUILDER
# ===========================================================================

def build_initial_state(
    n_people: int = 10,
    initial_money: float = 1000.0,
    initial_resources: float = 1000.0,
) -> EconomyState:
    """
    Build year-0 economy state from government-controlled inputs.

    Agent distribution (verified):
      Government  10%  (OECD: 18.4% of employment × 55% emp-rate)
      FreeOne     50%  (children 17% + students 8% + retired 18% + NEET 3% + other 4%)
      Producer    40%  (private-sector employed + self-employed)
    """
    from agents import AGENT_SHARES

    s = EconomyState()
    s.year = 0
    s.population = float(n_people)
    s.money_supply = initial_money
    s.resources_produced = initial_resources
    s.resources_consumed = initial_resources * 0.75   # 75% utilisation at start

    # Agent headcounts
    s.n_government = round(s.population * AGENT_SHARES["government"], 2)
    s.n_freeone    = round(s.population * AGENT_SHARES["freeone"],    2)
    s.n_producer   = round(s.population * AGENT_SHARES["producer"],   2)
    s.n_consumer   = s.population

    # Derived fiscal quantities
    s.investment        = initial_resources * 0.20
    s.government_spend  = initial_resources * GOVT_INVESTMENT_RATE
    s.welfare_spend     = initial_resources * WELFARE_RATE
    s.tax_revenue       = initial_resources * TAX_TO_GDP_RATIO

    # Producer labour productivity
    s.productivity_per_worker = (
        initial_resources / max(s.n_producer, 1)
    )

    # TB pool: seeded from initial automation tax estimate
    s.automation_tax_collected = (
        initial_resources * 0.05 * TB_AUTOMATION_TAX_RATE
    )  # 5% of GDP is automation output in year 0
    s.tb_pool_size    = s.automation_tax_collected * 3.0   # 3-year seeding
    s.tb_amount_issued = s.tb_pool_size * 0.15             # 15% deployed yr 0
    s.tb_active_borrowers = max(1, int(n_people * 0.08))  # ~8% in TB

    # Monetary rates
    s.real_interest_rate = NOMINAL_INTEREST_RATE - s.inflation

    return s


# ---------------------------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\nVerified Constants Summary")
    print("=" * 55)
    print(f"  Income Tax Rate (PIT on wages)   : {INCOME_TAX_RATE:.1%}")
    print(f"  Employee SSC                     : {SSC_EMPLOYEE_RATE:.1%}")
    print(f"  Employer SSC                     : {SSC_EMPLOYER_RATE:.1%}")
    print(f"  Total Tax Wedge on Labour        : {TOTAL_TAX_WEDGE:.1%}")
    print(f"  VAT Rate                         : {VAT_RATE:.1%}")
    print(f"  Corporate Tax Rate               : {CORPORATE_TAX_RATE:.1%}")
    print(f"  Tax / GDP                        : {TAX_TO_GDP_RATIO:.1%}")
    print(f"  MPC (economy-wide)               : {MPC}")
    print(f"  MPS (economy-wide)               : {MPS}")
    print(f"  Keynesian multiplier @ MPC=0.45  : {1/(1-MPC):.4f}")
    print(f"  Inflation target                 : {INFLATION_TARGET:.1%}")
    print(f"  Base TFP growth (OECD actual)    : {BASE_PRODUCTIVITY_GROWTH:.1%}")
    print(f"  Automation productivity boost    : {AUTOMATION_BOOST:.1%}")
    print(f"  Total TFP (TB-augmented economy) : {TOTAL_TFP_GROWTH:.1%}")
    print(f"  TB automation tax rate           : {TB_AUTOMATION_TAX_RATE:.1%}")
    print()
    s = build_initial_state(10, 1000, 1000)
    print(f"  Initial state (N=10):")
    print(f"    Population      : {s.population}")
    print(f"    Government      : {s.n_government} persons")
    print(f"    FreeOne         : {s.n_freeone} persons")
    print(f"    Producer        : {s.n_producer} persons")
    print(f"    GDP (resources) : {s.resources_produced}")
    print(f"    Money Supply    : {s.money_supply}")
    print(f"    TB Pool         : {s.tb_pool_size:.1f}")
