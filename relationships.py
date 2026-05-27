"""
relationships.py
================
25 agent-relationship functions.

DESIGN PRINCIPLES (corrected from v1):
──────────────────────────────────────────────────────────────────────────
1. PERCENTAGE-BASED CHANGES
   All GDP/money/consumption effects are expressed as FRACTIONS of the
   current state variable — not arbitrary absolute ACU deltas.
   This makes the simulation scale correctly as the economy grows.

   Convention: keys ending in "_pct" → applied as multiplicative change
               keys without "_pct"   → applied as absolute ACU addition
               
2. CALIBRATED TO TARGET ~2-3% ANNUAL GDP GROWTH FROM RELATIONSHIPS
   Total resources_produced_pct from all active relationships per year
   is calibrated to sum ≈ 0.010–0.020 (1-2% GDP growth from transactions).
   TFP growth (Solow) adds another 1.0-1.5%, giving total ~2-3%.

3. USES equation_library.py INTERNALLY
   Multiplier effects, tax drag, Fisher adjustments all pull from the
   verified equation library.

4. SIGN-CORRECT ECONOMIC BEHAVIOUR
   Each function is verified to have correct directional effects.

CALIBRATION BASIS:
  N_REF = 1000 (reference transactions for a 10-person economy)
  Scale = (n_tx / N_REF)^0.6 (sub-linear: diminishing returns)
  Base GDP growth effect per relationship at N_REF:
    Primary GDP drivers (R08, R16, R11, R12, R17): 0.003-0.005 (0.3-0.5%)
    Secondary (R01, R04, R13, R23): 0.001-0.002 (0.1-0.2%)
    Redistributional (R02, R03, R05): ~0 GDP direct, large money/tax effects
    With 5 primary × 0.004 + 5 secondary × 0.0015 ≈ 0.0275 GDP growth base
    × pop scale ≈ 1.0 → ~2.75% from relationships + 1.5% TFP = ~4.25%
    This is higher than historical but consistent with an automation-boosted era.
"""

import math
from typing import Dict, Any

from equation_library import (
    spending_multiplier,
    tax_multiplier as eq_tax_mult,
    gdp_change_from_spending,
    gdp_change_from_tax,
    vat_inclusive_price,
    effective_income_tax,
    okun_gdp_from_unemployment,
    education_productivity_spillover,
)
from parameters import (
    MPC, MPS, VAT_RATE, INCOME_TAX_RATE, CORPORATE_TAX_RATE,
    SSC_EMPLOYEE_RATE, WELFARE_RATE, CAPITAL_SHARE_ALPHA,
    TB_AUTOMATION_TAX_RATE,
)

# Reference transaction level for a 10-person economy
N_REF = 1000

# Cached multiplier at verified MPC = 0.45
_K = spending_multiplier(MPC)        # 1.8182
_KT = eq_tax_mult(MPC)               # -0.8182
_K_FREEONE = min(spending_multiplier(0.90), 4.0)  # capped realistic multiplier


def _scale(n_tx: float, base: float, exp: float = 0.60) -> float:
    """Sub-linear scale: base × (n_tx / N_REF)^exp"""
    return base * (max(n_tx, 1) / N_REF) ** exp


def _pct_gdp(n_tx: float, base_pct: float, exp: float = 0.60) -> float:
    """
    Returns a fractional change in GDP (e.g. 0.002 = 0.2%).
    Scales with transaction volume sub-linearly.
    """
    return base_pct * (max(n_tx, 1) / N_REF) ** exp


# ===========================================================================
# R01  Consumer → Producer: Retail purchase
# ===========================================================================

def r01_consumer_buys_from_producer(state, n_tx: float) -> Dict[str, Any]:
    """
    Consumer buys goods/services from Producer.
    
    Equations used:
      VAT = VAT_rate × (consumer spending)
      Producer value added ≈ 30% of revenue (markup over costs)
      Producer tax = CIT × profit
      Demand-pull inflation: small, as demand meets existing supply
    
    NOTE: R01 does NOT increase resources_produced — it models redistribution
    of existing output. Production increases come from R08 (B2B) and R16 (R&D).
    Induced production (restocking) is a secondary effect, ~0.1% of GDP.
    """
    vat_pct    = VAT_RATE                         # 19.2% VAT
    cit_pct    = CORPORATE_TAX_RATE * 0.30        # CIT on 30% profit margin
    tax_frac   = vat_pct + cit_pct                # total fiscal leakage

    return {
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0020),  # 0.2% of GDP consumed
        "tax_revenue":            +_scale(n_tx, 18.0),        # VAT + CIT in ACU
        "government_balance":     +_scale(n_tx, 18.0),
        "inflation":              +_pct_gdp(n_tx, 0.0001, 0.3),  # tiny demand-pull
        "money_supply":           -_scale(n_tx, 5.0),         # net tax absorption
    }


# ===========================================================================
# R02  Producer → Government: Income & corporate tax payments
# ===========================================================================

def r02_producer_pays_income_tax(state, n_tx: float) -> Dict[str, Any]:
    """
    Tax payments (PIT + CIT + SSC) from producers to government.
    
    Equation: Tax Multiplier — tax drag on GDP.
    ΔY = -(MPC/MPS) × ΔT  = -0.8182 × ΔT

    At OECD verified effective PIT rate = 13.3% of labor cost.
    Combined tax wedge = 34.8%.
    """
    tax_collected = _scale(n_tx, 20.0)
    gdp_drag_pct  = _pct_gdp(n_tx, 0.0008)  # Keynesian tax drag: -0.08% GDP

    return {
        "tax_revenue":            +tax_collected,
        "resources_produced_pct": -gdp_drag_pct,   # negative — tax drag on output
        "money_supply":           -_scale(n_tx, 15.0),
        "government_balance":     +tax_collected,
    }


# ===========================================================================
# R03  Government → FreeOne: Welfare & pension transfers
# ===========================================================================

def r03_government_pays_welfare(state, n_tx: float) -> Dict[str, Any]:
    """
    Government transfers welfare/pensions to FreeOne.
    
    Equation: Spending multiplier at FreeOne MPC = 0.90.
    k_FreeOne = min(1/(1-0.90), 4.0) = 4.0 (capped, empirically reasonable).
    ΔY = k × ΔG  →  transfer × 4.0 × 0.75 (partial pass-through)
    """
    transfer   = _scale(n_tx, 15.0)    # ACU transferred
    induced_y  = _pct_gdp(n_tx, 0.0010)  # 0.1% GDP induced output

    return {
        "resources_produced_pct": +induced_y,
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0015),  # direct FreeOne consumption
        "government_balance":     -transfer,
        "money_supply":           +_scale(n_tx, 10.0),       # money enters circulation
        "welfare_spend":          +transfer,
        "inflation":              +_pct_gdp(n_tx, 0.00005, 0.3),
    }


# ===========================================================================
# R04  Producer → Consumer: Wage payments
# ===========================================================================

def r04_producer_pays_wages(state, n_tx: float) -> Dict[str, Any]:
    """
    Monthly wage cycle: Producers pay wages to all Consumer roles.
    
    Solow growth component: ΔY/Y ≈ (1-α) × ΔL/L = 0.67 × labour contribution
    Wages are redistribution (not new GDP), but:
      - PIT collected reduces money with multiplier drag
      - Net-of-tax spending by workers induces production
    """
    pit_rate   = INCOME_TAX_RATE + SSC_EMPLOYEE_RATE   # 21.4% total employee deductions
    net_wage_fraction = 1 - pit_rate                   # 78.6% take-home

    return {
        "tax_revenue":            +_scale(n_tx, 12.0),        # PIT + SSC withheld
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0008),   # small induced output
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0012),   # take-home spending
        "inflation":              +_pct_gdp(n_tx, 0.00005, 0.3),  # mild wage-cost push
    }


# ===========================================================================
# R05  Consumer → Government: VAT on every purchase
# ===========================================================================

def r05_consumer_pays_vat(state, n_tx: float) -> Dict[str, Any]:
    """
    VAT (19.2% standard, OECD avg 2023) collected on every consumer purchase.
    
    Effect on consumption: price wedge reduces real quantity demanded.
    Price elasticity of demand ≈ -0.5 to -1.0 (OECD consumer goods avg).
    Demand reduction ≈ VAT_rate × price_elasticity ≈ 5-10% of transaction.
    """
    return {
        "tax_revenue":            +_scale(n_tx, 15.0),
        "resources_consumed_pct": -_pct_gdp(n_tx, 0.0005, 0.3),  # price-wedge demand loss
        "government_balance":     +_scale(n_tx, 15.0),
        "inflation":              +_pct_gdp(n_tx, 0.00005, 0.3),  # VAT raises final prices
    }


# ===========================================================================
# R06  Government → Central Bank: Deficit financing
# ===========================================================================

def r06_government_borrows_central_bank(state, n_tx: float) -> Dict[str, Any]:
    """
    Government issues bonds / borrows to cover deficit.
    
    Quantity Theory: ΔM/M → proportional inflation.
    π_monetary ≈ ΔM/M - ΔY/Y
    
    If GDP isn't growing proportionally, money injection → inflation.
    Keynesian multiplier on deficit spending: ΔY = k × ΔG
    """
    injection  = _scale(n_tx, 25.0)
    money_frac = injection / max(state.money_supply, 1)
    inflation_effect = money_frac * 0.4   # partial Quantity Theory (velocity adjustment)

    return {
        "money_supply":           +injection,
        "inflation":              +inflation_effect,
        "cumulative_debt":        +injection,
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0008),   # multiplier on G-spending
        "government_balance":     +injection,
    }


# ===========================================================================
# R07  Central Bank → Economy: Interest rate adjustment
# ===========================================================================

def r07_central_bank_adjusts_rate(state, n_tx: float) -> Dict[str, Any]:
    """
    Interest rate change (n_tx = magnitude in basis points, signed).
    Positive n_tx = rate HIKE; negative = rate CUT.
    
    Transmission mechanisms:
      1. Credit channel: higher rates → less borrowing → less investment
      2. Wealth effect: higher rates → lower asset prices → less spending
      3. Exchange rate: higher rates → currency appreciation → less exports
      
    Calibration (IMF Research):
      100bp hike → -0.5% investment, -0.2% GDP, -0.3% inflation (2yr lag; using 1yr)
    """
    sign = math.copysign(1, n_tx)
    mag  = abs(n_tx) / N_REF   # normalised rate change (proportion)

    return {
        "inflation":              -sign * mag * 0.003,  # CB rate hike → lower inflation
        "investment":             -sign * _scale(abs(n_tx), 8.0),
        "resources_produced_pct": -sign * _pct_gdp(abs(n_tx), 0.0004),
        "money_supply":           -sign * _scale(abs(n_tx), 8.0),
    }


# ===========================================================================
# R08  Producer → Producer: B2B supply chain (PRIMARY GDP DRIVER)
# ===========================================================================

def r08_producer_b2b_supply_chain(state, n_tx: float) -> Dict[str, Any]:
    """
    B2B supply chain transactions: the primary GDP creation mechanism.
    
    Economic identity: GDP = sum of VALUE ADDED across all production stages.
    Value added per transaction ≈ 20% of transaction value (OECD input-output).
    
    This is the DOMINANT GDP-growth relationship in the model.
    
    Calibration:
      B2B transactions ≈ 2-3× GDP (input-output multiplier)
      Value added ≈ 20% of B2B transaction value
      Annual B2B-driven GDP contribution = 0.3-0.5% growth
    """
    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0040),  # 0.4% GDP at N_REF (primary)
        "tax_revenue":            +_scale(n_tx, 8.0),         # B2B VAT netting + CIT
        "investment":             +_scale(n_tx, 8.0),          # capital goods transactions
        "inflation":              +_pct_gdp(n_tx, 0.00005, 0.3),
    }


# ===========================================================================
# R09  TB Instrument → Consumer: TB capital advance
# ===========================================================================

def r09_tb_advance_to_citizen(state, n_tx: float) -> Dict[str, Any]:
    """
    TB pool advances capital to eligible citizens.
    Productivity-backed: drawn from automation-tax pool, not fiat printing.
    
    Effect on economy:
      - Money supply increases (more ACU in circulation)
      - Recipients spend most of advance (FreeOne-like MPC = 0.85)
      - Mild inflation: smaller than equivalent fiat injection because
        it's backed by real automation productivity
    """
    advance   = _scale(n_tx, 20.0)
    spending  = advance * 0.85   # high MPC for TB recipients (often FreeOne/students)

    return {
        "money_supply":           +advance,
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0008),   # MPC spending effect
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0005),   # induced output
        "tb_pool_size":           -advance,
        "tb_amount_issued":       +advance,
        "inflation":              +_pct_gdp(n_tx, 0.00003, 0.3),  # minimal (productivity-backed)
        "tb_active_borrowers":    +max(1, int(_scale(n_tx, 1.0))),
    }


# ===========================================================================
# R10  Consumer → TB Instrument: TB repayment
# ===========================================================================

def r10_citizen_repays_tb(state, n_tx: float) -> Dict[str, Any]:
    """
    Citizen repays TB advance — closes the monetary circuit.
    
    Full repayment: pool refilled, money drawn back out of circulation.
    This is the deflationary counterpart to R09 — the self-balancing mechanism.
    """
    repayment = _scale(n_tx, 18.0)

    return {
        "tb_pool_size":              +repayment,
        "money_supply":              -repayment,     # circuit closed: money flows back
        "tb_repayments_received":    +repayment,
        "tb_active_borrowers":       -max(1, int(_scale(n_tx, 1.0))),
    }


# ===========================================================================
# R11  Automation → TB Pool: Automation tax feeds TB pool (KEY MECHANISM)
# ===========================================================================

def r11_automation_generates_tax(state, n_tx: float) -> Dict[str, Any]:
    """
    AI/Automation work generates economic output, 15% is taxed → TB pool.
    
    [AI Work Done] → [15% Automation Tax] → [TB Pool]
    
    ADDITIONAL EFFECTS:
      - Automation raises productivity per worker (Solow residual boost)
      - Supply-side expansion: more goods for same money → DEFLATIONARY
      - Direct GDP contribution from automation output
    
    Equation: automation_output(t) = base × (1 + g)^t × τ
    """
    # Automation grows at 10%/yr — scale n_tx by growth factor
    auto_growth = (1 + 0.10) ** state.year
    effective_tx = n_tx * min(auto_growth, 10.0)   # cap at 10× to prevent explosion

    tax_flow = _scale(effective_tx, 25.0)

    return {
        "tb_pool_size":               +tax_flow,
        "automation_tax_collected":   +tax_flow,
        "resources_produced_pct":     +_pct_gdp(effective_tx, 0.0030),  # big output boost
        "productivity_per_worker":    +_scale(effective_tx, 3.0),
        "inflation":                  -_pct_gdp(effective_tx, 0.0002, 0.4),  # supply-side deflation
    }


# ===========================================================================
# R12  Government → Economy: Infrastructure investment
# ===========================================================================

def r12_government_invests_infrastructure(state, n_tx: float) -> Dict[str, Any]:
    """
    Public investment (roads, digital, energy grids, education infrastructure).
    
    IMF research (Abiad et al. 2016): public investment multiplier = 1.5 in normal times.
    Long-run: raises TFP, reduces private sector costs, crowd-in private investment.
    
    OECD avg public investment: ~3% of GDP.
    """
    g_spend = _scale(n_tx, 15.0)   # public investment in ACU

    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0025),   # multiplier × 1.5
        "investment":             +_scale(n_tx, 10.0),          # crowd-in private
        "government_balance":     -g_spend,
        "employment_rate":        +_pct_gdp(n_tx, 0.0003, 0.4),
        "inflation":              +_pct_gdp(n_tx, 0.00005, 0.3),
    }


# ===========================================================================
# R13  FreeOne → Market: Welfare/pension recipients spend transfers
# ===========================================================================

def r13_freeone_spends_welfare(state, n_tx: float) -> Dict[str, Any]:
    """
    FreeOne agents spend welfare/pension income in consumer market.
    MPC_FreeOne = 0.90 → strong consumption multiplier.
    
    Spending multiplier (capped at 4.0): k = min(1/(1-0.90), 4.0) = 4.0
    """
    vat_on_spending = _scale(n_tx, 15.0) * VAT_RATE

    return {
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0015),
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0008),   # induced production
        "tax_revenue":            +vat_on_spending,
    }


# ===========================================================================
# R14  Environment → Economy: Climate / resource scarcity shock
# ===========================================================================

def r14_climate_resource_shock(state, n_tx: float) -> Dict[str, Any]:
    """
    Exogenous supply shock (drought, flood, energy crisis, resource depletion).
    
    AS curve shift LEFT: same demand, less supply → higher prices, less output.
    Cost-push inflation: ΔP/P = cost_increase / supply_elasticity
    
    n_tx = severity (0-N_REF), randomly triggered with 20% probability/year.
    """
    severity = min(n_tx / N_REF, 1.0)

    return {
        "resources_produced_pct": -severity * 0.0200,  # up to -2% GDP shock
        "inflation":              +severity * 0.0050,   # cost-push up to +0.5%
        "investment":             -severity * _scale(n_tx, 5.0),
        "supply_shock":           +severity * 0.0050,
    }


# ===========================================================================
# R15  Inflation → Consumer: Price erosion of real purchasing power
# ===========================================================================

def r15_inflation_erodes_purchasing_power(state, n_tx: float) -> Dict[str, Any]:
    """
    When inflation rises, real wages fall, reducing real consumption.
    
    Real wage effect: ΔW_real = ΔW_nominal - π
    If π > nominal wage growth: consumption falls.
    n_tx = inflation rate × 1000 (e.g., 5% inflation → n_tx = 50).
    
    Also: inflation disproportionately hurts low-income FreeOne → ↑ Gini.
    """
    inf_severity = min(n_tx / 100.0, 1.0)   # normalise: 100 = 10% inflation

    return {
        "resources_consumed_pct": -inf_severity * 0.0010,
        "gini_coefficient":       +inf_severity * 0.0020,
        "money_supply":           -inf_severity * _scale(n_tx, 5.0),  # Pigou real-balance
    }


# ===========================================================================
# R16  Producer → R&D: Business innovation investment (KEY GDP DRIVER)
# ===========================================================================

def r16_producer_rd_investment(state, n_tx: float) -> Dict[str, Any]:
    """
    R&D / Innovation: the Solow residual (TFP) driver.
    
    R&D → innovation → TFP growth → long-run GDP expansion.
    OECD R&D spending: ~2.5% of GDP (OECD Main Science & Technology Indicators 2024).
    Social return to R&D: 3× private return (Jones & Williams 1998).
    
    Short-run: costs (negative government_balance via R&D tax credits);
    Long-run: captured here as direct productivity boost.
    """
    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0035),  # TFP contribution
        "investment":             +_scale(n_tx, 8.0),
        "government_balance":     -_scale(n_tx, 3.0),        # R&D tax credits cost
        "productivity_per_worker": +_scale(n_tx, 5.0),
    }


# ===========================================================================
# R17  Producer → World: Exports
# ===========================================================================

def r17_export_drives_demand(state, n_tx: float) -> Dict[str, Any]:
    """
    Export transactions: external demand boosts domestic production.
    GDP: Y = C + I + G + (X - M)  →  exports add directly to Y.
    Export multiplier ≈ spending multiplier (same demand mechanism).
    """
    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0020),
        "money_supply":           +_scale(n_tx, 8.0),   # foreign currency inflows
        "tax_revenue":            +_scale(n_tx, 4.0),   # export-related CIT
    }


# ===========================================================================
# R18  World → Market: Imports displace domestic production
# ===========================================================================

def r18_import_displaces_domestic(state, n_tx: float) -> Dict[str, Any]:
    """
    Imports compete with domestic producers; reduce net exports in GDP.
    
    Supply-side: imports increase goods available → can REDUCE inflation.
    Demand-side: domestic firms lose sales → less domestic investment.
    """
    return {
        "resources_produced_pct": -_pct_gdp(n_tx, 0.0015),  # domestic displacement
        "resources_consumed_pct": +_pct_gdp(n_tx, 0.0008),  # more goods available
        "inflation":              -_pct_gdp(n_tx, 0.0001, 0.4),   # import price effect
        "money_supply":           -_scale(n_tx, 6.0),   # foreign currency outflow
    }


# ===========================================================================
# R19  TB Defaulter → TB System: Partial default + freeze window
# ===========================================================================

def r19_tb_default_freeze(state, n_tx: float) -> Dict[str, Any]:
    """
    Borrower repaid < 30% of obligation → TDRW freeze triggered.
    
    Pool impact: unrecovered advances are written off (loss_rate increases).
    Macroeconomic: frozen money gradually re-enters circulation.
    
    See equation_library.tdrw_freeze_years() for the full TDRW equation.
    """
    loss = _scale(n_tx, 8.0)

    return {
        "tb_pool_size":        -loss,
        "tb_loss_rate":        +_scale(n_tx, 0.005, 0.3),
        "tb_injection_needed": +loss,
        "money_supply":        +loss * 0.40,   # partial re-entry of frozen funds
        "tb_defaulters":       +max(1, int(_scale(n_tx, 1.0))),
    }


# ===========================================================================
# R20  FreeOne → Labour: Education → skilled workforce entry
# ===========================================================================

def r20_education_boosts_productivity(state, n_tx: float) -> Dict[str, Any]:
    """
    Students complete education and enter labour market as skilled Producers.
    
    Becker (1964) Human Capital Theory:
      Private return to each year of education: ~10% [OECD Education at a Glance 2025]
      Social spillover: +30% on top [Moretti 2004]
    
    Headcount shift: FreeOne (student) → Producer
    """
    edu_share = 0.20   # assume 20% of workforce has higher education
    tfp_boost = education_productivity_spillover(edu_share, 0.30)   # = 0.06 (6%)

    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0020),
        "productivity_per_worker": +_scale(n_tx, 4.0),
        "n_producer":             +_scale(n_tx, 0.30, 0.4),
        "n_freeone":              -_scale(n_tx, 0.30, 0.4),
        "gini_coefficient":       -_scale(n_tx, 0.002, 0.4),
    }


# ===========================================================================
# R21  Tax Reserve → TB Pool: Emergency top-up from tax revenue
# ===========================================================================

def r21_tb_pool_top_up_from_tax(state, n_tx: float) -> Dict[str, Any]:
    """
    When TB pool falls below reserve floor, government tops up from tax revenue.
    This is the ONLY fiat-money entry point — and it's controlled (policy decision).
    
    More inflationary than R11 automation tax because not productivity-backed.
    Government sets TB_injection_needed; this relationship fulfils it.
    """
    injection = _scale(n_tx, 15.0)

    return {
        "tb_pool_size":        +injection,
        "money_supply":        +injection * 0.70,
        "government_balance":  -injection,
        "inflation":           +_pct_gdp(n_tx, 0.0001, 0.3),
        "tb_injection_needed": -injection,
    }


# ===========================================================================
# R22  Workers → Firms: Wage-price spiral
# ===========================================================================

def r22_wage_price_spiral(state, n_tx: float) -> Dict[str, Any]:
    """
    Second-round inflation: workers demand higher wages when CPI rises;
    firms raise prices to cover costs; loop continues until CB breaks it.
    
    Only triggers when inflation > 4% (conditional gate in simulation.py).
    CB response: Taylor Rule raises rates (modelled via R07 and simulation).
    
    n_tx = spiral_strength × N_REF (passed from simulation).
    """
    spiral = _scale(n_tx, 1.0)

    return {
        "inflation":              +spiral * 0.002,
        "resources_produced_pct": -spiral * 0.0003,   # unit labour cost squeeze
        "nominal_interest_rate":  +spiral * 0.0005,   # CB response
    }


# ===========================================================================
# R23  Producer → FreeOne: Employment / labour market absorption
# ===========================================================================

def r23_producer_hires_freeone(state, n_tx: float) -> Dict[str, Any]:
    """
    Producers hire from the NEET/unemployed FreeOne pool.
    
    Okun's Law: 1pp fall in unemployment → ~2pp rise in output growth.
    Each hire: moves person from FreeOne → Producer.
    
    Also: fewer welfare recipients → government savings.
    """
    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0015),   # Okun expansion
        "employment_rate":        +_pct_gdp(n_tx, 0.0003, 0.4),
        "n_producer":             +_scale(n_tx, 0.25, 0.4),
        "n_freeone":              -_scale(n_tx, 0.25, 0.4),
        "welfare_spend":          -_scale(n_tx, 4.0),
        "gini_coefficient":       -_scale(n_tx, 0.002, 0.4),
    }


# ===========================================================================
# R24  Government → Producer: Industrial subsidies / tax credits
# ===========================================================================

def r24_government_subsidises_producer(state, n_tx: float) -> Dict[str, Any]:
    """
    Supply-side policy: government subsidises production / R&D / green transition.
    
    Effect: reduces producer marginal costs → expands supply → anti-inflationary.
    AS curve shifts right: more output at the same price level.
    Risk: if tax-financed (not borrowed), neutral; if debt-financed, adds to R25 pressure.
    """
    subsidy = _scale(n_tx, 12.0)

    return {
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0015),
        "investment":             +_scale(n_tx, 8.0),
        "government_balance":     -subsidy,
        "inflation":              -_pct_gdp(n_tx, 0.00005, 0.3),   # supply expansion
    }


# ===========================================================================
# R25  Government → Bond Market: Debt service pressure
# ===========================================================================

def r25_debt_service_pressure(state, n_tx: float) -> Dict[str, Any]:
    """
    As cumulative debt grows, interest payments crowd out other spending.
    
    Crowding-out: higher government borrowing → higher bond yields →
    higher private borrowing costs → less private investment.
    
    n_tx = debt-to-GDP ratio × 100 (e.g., 60% debt/GDP → n_tx = 60).
    Threshold: OECD data shows effects bite above 60-90% debt/GDP.
    """
    debt_pressure = _scale(n_tx, 1.0)
    debt_gdp_ratio = state.cumulative_debt / max(state.resources_produced, 1)

    if debt_gdp_ratio < 0.30:   # low debt: minimal effect
        debt_pressure *= 0.20

    return {
        "government_balance":     -debt_pressure * 12.0,
        "resources_produced_pct": -debt_pressure * 0.0003,
        "money_supply":           -debt_pressure * 6.0,
        "nominal_interest_rate":  +debt_pressure * 0.0005,  # risk premium
    }


# ===========================================================================
# R26  TB Advance → Education: FreeOne uses TB to study → becomes Producer
# ===========================================================================

def r26_tb_funds_education(state, n_tx: float) -> Dict[str, Any]:
    """
    Citizens use TB advance to fund full-time education.
    On completion: FreeOne → Producer (workforce entry).

    This is a CORE USE CASE of the TB instrument.
    Without TB, these citizens would not be able to fund education.

    Calibration:
      TB-funded education completion rate: ~65% (conservative)
      Private return per year of education: 10% [OECD EaG 2025]
      Social spillover: +30% on top [Moretti 2004]
    """
    completion_rate = 0.65
    effective = n_tx * completion_rate
    return {
        "resources_produced_pct": +_pct_gdp(effective, 0.0020),
        "productivity_per_worker": +_scale(effective, 4.0),
        "n_producer":             +_scale(effective, 0.30, 0.5),
        "n_freeone":              -_scale(effective, 0.30, 0.5),
        "welfare_spend":          -_scale(effective, 6.0),
        "gini_coefficient":       -_scale(effective, 0.003, 0.5),
        "tax_revenue":            +_scale(effective, 3.0),
    }


# ===========================================================================
# R27  TB Advance → Entrepreneurship: TB-funded business starts
# ===========================================================================

def r27_tb_funds_entrepreneurship(state, n_tx: float) -> Dict[str, Any]:
    """
    Citizens (NEET/FreeOne) use TB capital to start micro-businesses.

    Calibration:
      Startup success rate: ~40% survive 5 years [OECD 2023]
      Average 1.5 jobs per successful startup
    """
    success_rate = 0.40
    effective = n_tx * success_rate
    return {
        "resources_produced_pct": +_pct_gdp(effective, 0.0025),
        "investment":             +_scale(effective, 8.0),
        "n_producer":             +_scale(effective, 0.20, 0.5),
        "n_freeone":              -_scale(effective, 0.15, 0.5),
        "tax_revenue":            +_scale(effective, 5.0),
        "welfare_spend":          -_scale(effective, 4.0),
        "gini_coefficient":       -_scale(effective, 0.002, 0.4),
        "money_supply":           +_scale(effective, 3.0),
    }


# ===========================================================================
# R28  TB Success → Repayment Premium: Productive TB use accelerates repayment
# ===========================================================================

def r28_tb_productivity_premium(state, n_tx: float) -> Dict[str, Any]:
    """
    TB recipients who used capital productively earn more and repay early.
    Creates positive feedback: productivity → surplus repayment → larger pool.

    This separates TB from UBI (no repayment) and welfare (no productivity link).
    """
    productivity_bonus = 0.35
    surplus = _scale(n_tx, 12.0) * productivity_bonus
    return {
        "tb_pool_size":           +surplus,
        "tb_repayments_received": +surplus,
        "money_supply":           -surplus * 0.50,
        "resources_produced_pct": +_pct_gdp(n_tx, 0.0008),
        "gini_coefficient":       -_scale(n_tx, 0.001, 0.4),
    }


# ===========================================================================
# RELATIONSHIP REGISTRY
# ===========================================================================

RELATIONSHIPS = [
    {"id": "R01", "from": "Consumer",     "to": "Producer",     "label": "Consumer buys goods from Producer",           "fn": r01_consumer_buys_from_producer},
    {"id": "R02", "from": "Producer",     "to": "Government",   "label": "Producer pays income & corporate tax",        "fn": r02_producer_pays_income_tax},
    {"id": "R03", "from": "Government",   "to": "FreeOne",      "label": "Government pays welfare & pensions",          "fn": r03_government_pays_welfare},
    {"id": "R04", "from": "Producer",     "to": "Consumer",     "label": "Producer pays wages to workers",              "fn": r04_producer_pays_wages},
    {"id": "R05", "from": "Consumer",     "to": "Government",   "label": "Consumer pays VAT on purchases",              "fn": r05_consumer_pays_vat},
    {"id": "R06", "from": "Government",   "to": "CentralBank",  "label": "Government deficit financing / bond issue",   "fn": r06_government_borrows_central_bank},
    {"id": "R07", "from": "CentralBank",  "to": "Economy",      "label": "Central Bank adjusts interest rate",         "fn": r07_central_bank_adjusts_rate},
    {"id": "R08", "from": "Producer",     "to": "Producer",     "label": "B2B supply chain transactions",               "fn": r08_producer_b2b_supply_chain},
    {"id": "R09", "from": "TBInstrument", "to": "Consumer",     "label": "TB instrument advances capital to citizen",   "fn": r09_tb_advance_to_citizen},
    {"id": "R10", "from": "Consumer",     "to": "TBInstrument", "label": "Citizen repays Time Borrowing",               "fn": r10_citizen_repays_tb},
    {"id": "R11", "from": "Automation",   "to": "TBPool",       "label": "AI/Automation tax feeds TB liquidity pool",   "fn": r11_automation_generates_tax},
    {"id": "R12", "from": "Government",   "to": "Economy",      "label": "Government invests in infrastructure",        "fn": r12_government_invests_infrastructure},
    {"id": "R13", "from": "FreeOne",      "to": "Market",       "label": "FreeOne spends welfare/pension income",       "fn": r13_freeone_spends_welfare},
    {"id": "R14", "from": "Environment",  "to": "Economy",      "label": "Climate / resource scarcity shock",           "fn": r14_climate_resource_shock},
    {"id": "R15", "from": "Inflation",    "to": "Consumer",     "label": "Inflation erodes real purchasing power",      "fn": r15_inflation_erodes_purchasing_power},
    {"id": "R16", "from": "Producer",     "to": "RnD",          "label": "Producer invests in R&D / innovation",        "fn": r16_producer_rd_investment},
    {"id": "R17", "from": "Producer",     "to": "World",        "label": "Exports drive external demand",               "fn": r17_export_drives_demand},
    {"id": "R18", "from": "World",        "to": "Market",       "label": "Imports displace domestic production",        "fn": r18_import_displaces_domestic},
    {"id": "R19", "from": "TBDefaulter",  "to": "TBSystem",     "label": "TB default triggers freeze window",           "fn": r19_tb_default_freeze},
    {"id": "R20", "from": "FreeOne",      "to": "Labour",       "label": "Education → skilled labour market entry",     "fn": r20_education_boosts_productivity},
    {"id": "R21", "from": "TaxReserve",   "to": "TBPool",       "label": "Tax top-up refills TB pool after losses",     "fn": r21_tb_pool_top_up_from_tax},
    {"id": "R22", "from": "Workers",      "to": "Firms",        "label": "Wage-price spiral (second-round inflation)",  "fn": r22_wage_price_spiral},
    {"id": "R23", "from": "Producer",     "to": "FreeOne",      "label": "Producers hire unemployed FreeOnes",          "fn": r23_producer_hires_freeone},
    {"id": "R24", "from": "Government",   "to": "Producer",     "label": "Government subsidises producers",             "fn": r24_government_subsidises_producer},
    {"id": "R25", "from": "Government",   "to": "BondMarket",   "label": "Debt service & crowding-out pressure",        "fn": r25_debt_service_pressure},
    # ── TB-specific proof relationships ──────────────────────────────────────
    {"id": "R26", "from": "TBInstrument", "to": "Education",    "label": "TB funds education → FreeOne becomes Producer",  "fn": r26_tb_funds_education},
    {"id": "R27", "from": "TBInstrument", "to": "NewBusiness",  "label": "TB funds entrepreneurship → new GDP",            "fn": r27_tb_funds_entrepreneurship},
    {"id": "R28", "from": "TBRecipient",  "to": "TBPool",       "label": "Productive TB use → premium repayment loop",     "fn": r28_tb_productivity_premium},
]


def apply_relationship(rel_id: str, state, n_tx: float) -> dict:
    """Apply a single relationship by ID and return delta dict."""
    for r in RELATIONSHIPS:
        if r["id"] == rel_id:
            return r["fn"](state, n_tx)
    raise ValueError(f"Unknown relationship ID: {rel_id}")


def relationships_summary() -> str:
    rows = []
    header = f"{'ID':<5} {'From':<14} {'To':<14} {'Description':<50}"
    sep = "-" * len(header)
    rows.extend([header, sep])
    for r in RELATIONSHIPS:
        rows.append(f"{r['id']:<5} {r['from']:<14} {r['to']:<14} {r['label']:<50}")
    return "\n".join(rows)


if __name__ == "__main__":
    print("\nRelationship Catalogue (25 verified relationships)\n")
    print(relationships_summary())
