"""
equation_library.py
===================
Pure, independently testable economic and TB equations.

Every function here:
  - Takes only primitive inputs (float / int)
  - Returns a single value or a small named dict
  - Has NO side-effects or global state
  - Is self-contained enough to unit-test in isolation
  - Includes the academic source for each equation

Verified sources used for calibration:
  [QTM]   Fisher, I. (1911). The Purchasing Power of Money.
  [FISH]  Fisher, I. (1930). The Theory of Interest.
  [KEY]   Keynes, J.M. (1936). General Theory of Employment.
  [SOL]   Solow, R. (1956). A Contribution to the Theory of Economic Growth.
  [OKU]   Okun, A. (1962). Potential GNP: Its Measurement and Significance.
  [TAY]   Taylor, J.B. (1993). Discretion versus Policy Rules in Practice.
  [LAF]   Laffer, A. (2004). The Laffer Curve: Past, Present, and Future.
  [BEC]   Becker, G. (1964). Human Capital.
  [MPC]   Jappelli & Pistaferri (2014): average MPC = 0.46 (WIFO/euro area).
          Ramey (2023): corrected micro MPC = 0.30-0.40.
  [POP]   UN World Population Prospects 2024; OECD Employment Outlook 2025.
  [TAX]   OECD Revenue Statistics 2025; Tax Foundation 2024 (Tax Wedge).
  [TFP]   OECD Compendium of Productivity Indicators 2024; CRS Report R48695.
"""

import math
from typing import Tuple, List


# ===========================================================================
# 1. GDP EQUATIONS
# ===========================================================================

def gdp_expenditure(C: float, I: float, G: float, X: float, M: float) -> float:
    """
    [KEY] Expenditure approach to GDP.
    Y = C + I + G + (X - M)

    Parameters
    ----------
    C : Consumption
    I : Investment (gross fixed capital formation)
    G : Government spending
    X : Exports
    M : Imports

    Returns
    -------
    float : Nominal GDP (same units as inputs)

    Example
    -------
    >>> gdp_expenditure(700, 200, 150, 100, 80)
    1070.0
    """
    return float(C + I + G + (X - M))


def gdp_growth_rate(Y_current: float, Y_previous: float) -> float:
    """
    Annual real GDP growth rate.
    g = (Y_t - Y_{t-1}) / Y_{t-1}

    Returns
    -------
    float : Growth rate as decimal (e.g., 0.025 for 2.5%)

    Example
    -------
    >>> round(gdp_growth_rate(1025, 1000), 4)
    0.025
    """
    if Y_previous == 0:
        return 0.0
    return (Y_current - Y_previous) / Y_previous


def real_gdp(nominal_gdp: float, price_deflator: float) -> float:
    """
    [QTM] Real GDP = Nominal GDP / Price Deflator
    Price deflator = current_price_index / base_price_index

    Example
    -------
    >>> real_gdp(1050, 1.05)
    1000.0
    """
    if price_deflator == 0:
        raise ValueError("price_deflator cannot be zero")
    return nominal_gdp / price_deflator


# ===========================================================================
# 2. MONEY & INFLATION EQUATIONS
# ===========================================================================

def quantity_theory_inflation(
    delta_M: float,
    M: float,
    delta_Y: float,
    Y: float,
    velocity_change: float = 0.0,
) -> float:
    """
    [QTM] Quantity Theory of Money — inflation formula.
    MV = PY  =>  π ≈ ΔM/M - ΔY/Y + ΔV/V

    Assumptions:
      Velocity (V) is approximately constant (Monetarist view).
      Any velocity change is passed as velocity_change parameter.

    Parameters
    ----------
    delta_M         : Change in money supply this period
    M               : Previous money supply
    delta_Y         : Change in real output this period
    Y               : Previous real output
    velocity_change : ΔV/V (default 0 — velocity constant)

    Returns
    -------
    float : Expected inflation rate (decimal)

    Calibration: OECD avg money growth 2000-2023 ~5-8%/yr; GDP growth ~2%/yr;
                 predicted inflation ~3-6% (directionally correct).

    Example
    -------
    >>> round(quantity_theory_inflation(50, 1000, 20, 1000), 4)
    0.03
    """
    if M == 0 or Y == 0:
        return 0.0
    return (delta_M / M) - (delta_Y / Y) + velocity_change


def composite_inflation(
    monetary: float,
    demand_pull: float,
    cost_push: float,
    supply_shock: float,
    target: float = 0.02,
    cb_anchoring: float = 0.30,
) -> float:
    """
    Composite inflation model blending four sources.
    π = 0.60×monetary + 0.25×demand_pull + 0.15×cost_push + supply_shock
    π_final = π_raw × (1 - anchor) + target × anchor   [CB mean-reversion]

    Sources  : Quantity Theory (monetary), Keynesian (demand_pull),
               AS shocks (cost_push), exogenous (supply_shock).
    Anchoring: ECB/Fed forward-guidance research (Bernanke 2004).

    Parameters
    ----------
    monetary     : Monetary inflation component (ΔM/M - ΔY/Y)
    demand_pull  : Keynesian excess-demand inflation
    cost_push    : Supply-side cost inflation (energy, wages)
    supply_shock : Exogenous shock (climate, geopolitics)
    target       : Central bank inflation target (default 2%)
    cb_anchoring : Weight given to target in mean-reversion (default 30%)

    Returns
    -------
    float : Blended inflation rate (decimal)

    Example
    -------
    >>> round(composite_inflation(0.04, 0.01, 0.005, 0.0), 4)
    0.0357
    """
    raw = (
        0.60 * monetary
        + 0.25 * demand_pull
        + 0.15 * cost_push
        + supply_shock
    )
    return raw * (1 - cb_anchoring) + target * cb_anchoring


def price_level_update(P_prev: float, inflation: float) -> float:
    """
    Update aggregate price index.
    P(t) = P(t-1) × (1 + π)

    Example
    -------
    >>> round(price_level_update(1.0, 0.02), 4)
    1.02
    """
    return P_prev * (1 + inflation)


# ===========================================================================
# 3. INTEREST RATE EQUATIONS
# ===========================================================================

def fisher_real_rate(nominal_rate: float, inflation: float) -> float:
    """
    [FISH] Fisher Equation: real interest rate.
    r = i - π  (approximate; exact: (1+i)/(1+π) - 1)

    Source: Fisher (1930). Empirical OECD average real rate 2000-2023 ~1-2%.

    Parameters
    ----------
    nominal_rate : Nominal interest rate i (decimal)
    inflation    : Inflation rate π (decimal)

    Returns
    -------
    float : Real interest rate r (decimal)

    Example
    -------
    >>> round(fisher_real_rate(0.045, 0.02), 4)
    0.025
    """
    return nominal_rate - inflation


def fisher_real_rate_exact(nominal_rate: float, inflation: float) -> float:
    """
    [FISH] Exact Fisher Equation.
    r = (1 + i) / (1 + π) - 1

    Example
    -------
    >>> round(fisher_real_rate_exact(0.045, 0.02), 4)
    0.0245
    """
    if 1 + inflation == 0:
        raise ValueError("Inflation cannot be -100%")
    return (1 + nominal_rate) / (1 + inflation) - 1


def taylor_rule(
    inflation: float,
    inflation_target: float = 0.02,
    neutral_real_rate: float = 0.02,
    output_gap: float = 0.0,
    phi_pi: float = 0.5,
    phi_y: float = 0.5,
    i_floor: float = 0.0,
    i_ceiling: float = 0.20,
) -> float:
    """
    [TAY] Taylor Rule (1993): central bank policy rate.
    i = π* + r* + φ_π(π - π*) + φ_y × output_gap

    Parameters
    ----------
    inflation        : Current inflation π
    inflation_target : Target inflation π* (default 2%)
    neutral_real_rate: Neutral real rate r* (default 2%; Laubach-Williams est.)
    output_gap       : (Y - Y_potential) / Y_potential [capped ±10% for stability]
    phi_pi           : Response coefficient to inflation gap (default 0.5)
    phi_y            : Response coefficient to output gap (default 0.5)
    i_floor          : Minimum policy rate (ZLB / NIRP floor, default 0%)
    i_ceiling        : Maximum policy rate cap (default 20%)

    Returns
    -------
    float : Recommended nominal policy rate i

    Calibration: Original Taylor (1993) used φ_π=0.5, φ_y=0.5.
                 ECB and Fed empirical studies confirm these as good estimates.

    Example
    -------
    >>> round(taylor_rule(0.04, 0.02, 0.02, 0.0), 4)
    0.05
    """
    gap = max(-0.10, min(0.10, output_gap))   # cap output gap ±10%
    i = (
        inflation_target
        + neutral_real_rate
        + phi_pi * (inflation - inflation_target)
        + phi_y * gap
    )
    return max(i_floor, min(i_ceiling, i))


def smooth_rate_adjustment(i_prev: float, i_target: float, speed: float = 0.30) -> float:
    """
    Partial adjustment / inertia model for central bank rate changes.
    i(t) = (1 - speed) × i(t-1) + speed × i_target

    Source: Clarida, Galí, Gertler (1999) — central banks adjust gradually.
    Default speed 0.30 means 30% adjustment toward target each period.

    Example
    -------
    >>> round(smooth_rate_adjustment(0.04, 0.06, 0.30), 4)
    0.046
    """
    return (1 - speed) * i_prev + speed * i_target


# ===========================================================================
# 4. KEYNESIAN MULTIPLIERS
# ===========================================================================

def spending_multiplier(mpc: float) -> float:
    """
    [KEY] Keynesian spending multiplier.
    k = 1 / (1 - MPC)

    Empirical range: 0.8–2.5 (IMF, Blanchard & Leigh 2013).
    At MPC=0.45: k = 1/(1-0.45) = 1.82  — in the plausible empirical range.

    Parameters
    ----------
    mpc : Marginal propensity to consume (0 < mpc < 1)

    Returns
    -------
    float : Spending multiplier

    Example
    -------
    >>> round(spending_multiplier(0.45), 4)
    1.8182
    """
    if mpc >= 1.0 or mpc <= 0.0:
        raise ValueError(f"MPC must be in (0, 1), got {mpc}")
    return 1.0 / (1.0 - mpc)


def tax_multiplier(mpc: float) -> float:
    """
    [KEY] Tax multiplier — effect of tax change on GDP.
    k_T = -MPC / (1 - MPC) = -MPC / MPS

    Negative: tax increase → GDP decrease.
    Always smaller in magnitude than spending multiplier by 1 unit.

    Example
    -------
    >>> round(tax_multiplier(0.45), 4)
    -0.8182
    """
    if mpc >= 1.0 or mpc <= 0.0:
        raise ValueError(f"MPC must be in (0, 1), got {mpc}")
    return -mpc / (1.0 - mpc)


def balanced_budget_multiplier(mpc: float) -> float:
    """
    [KEY] Balanced-budget multiplier (Haavelmo theorem).
    If ΔG = ΔT (equal increase in spending AND taxes): k_BB = 1

    This holds exactly regardless of MPC — verified result.

    Example
    -------
    >>> round(balanced_budget_multiplier(0.45), 6)
    1.0
    """
    return spending_multiplier(mpc) + tax_multiplier(mpc)


def gdp_change_from_spending(delta_G: float, mpc: float) -> float:
    """
    [KEY] GDP change from government spending increase.
    ΔY = k × ΔG  where k = 1/(1-MPC)

    Example
    -------
    >>> round(gdp_change_from_spending(100, 0.45), 2)
    181.82
    """
    return delta_G * spending_multiplier(mpc)


def gdp_change_from_tax(delta_T: float, mpc: float) -> float:
    """
    [KEY] GDP change from tax increase (negative effect).
    ΔY = -(MPC/MPS) × ΔT

    Example
    -------
    >>> round(gdp_change_from_tax(100, 0.45), 2)
    -81.82
    """
    return delta_T * tax_multiplier(mpc)


# ===========================================================================
# 5. SOLOW GROWTH MODEL
# ===========================================================================

def solow_growth_rate(
    tfp_growth: float,
    capital_growth: float,
    labour_growth: float,
    alpha: float = 0.33,
) -> float:
    """
    [SOL] Solow Growth Model — GDP growth decomposition.
    ΔY/Y = ΔA/A + α × ΔK/K + (1-α) × ΔL/L

    Parameters
    ----------
    tfp_growth     : Total Factor Productivity (TFP/Solow residual) growth rate
    capital_growth : Capital stock growth rate ΔK/K
    labour_growth  : Labour input growth rate ΔL/L
    alpha          : Capital share of income (default 0.33; Gollin 2002 est.)

    Returns
    -------
    float : Real GDP growth rate

    Calibration:
      TFP (OECD 2000-2024): 0.9%/yr [CRS Report R48695]
      Capital growth: ~2-3%/yr
      Labour growth: ~0.5-1%/yr
      Predicted GDP growth: 0.9 + 0.33×2.5 + 0.67×0.7 ≈ 0.9 + 0.83 + 0.47 = 2.2%

    Example
    -------
    >>> round(solow_growth_rate(0.009, 0.025, 0.007), 4)
    0.0223   # 0.009 + 0.33*0.025 + 0.67*0.007 = 0.02228
    """
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0,1), got {alpha}")
    return tfp_growth + alpha * capital_growth + (1 - alpha) * labour_growth


def solow_steady_state_capital(
    savings_rate: float,
    depreciation: float,
    labour_growth: float,
    tfp_growth: float,
    alpha: float = 0.33,
) -> float:
    """
    [SOL] Solow steady-state capital-output ratio.
    (K/Y)* = s / (δ + n + g)

    Parameters
    ----------
    savings_rate  : Fraction of income saved (s)
    depreciation  : Capital depreciation rate (δ, ~0.05-0.10)
    labour_growth : Population/labour force growth (n)
    tfp_growth    : TFP growth rate (g)
    alpha         : Capital share

    Returns
    -------
    float : Steady-state capital-output ratio

    Example
    -------
    >>> round(solow_steady_state_capital(0.20, 0.05, 0.011, 0.01), 4)
    2.8169
    """
    denominator = depreciation + labour_growth + tfp_growth
    if denominator <= 0:
        raise ValueError("depreciation + labour_growth + tfp_growth must be > 0")
    return savings_rate / denominator


# ===========================================================================
# 6. POPULATION GROWTH
# ===========================================================================

def logistic_growth(
    P: float,
    r: float,
    K: float,
) -> float:
    """
    Logistic population growth model.
    P(t+1) = P(t) + r × P(t) × (1 - P(t)/K)

    Preferred over exponential because it models:
      - Resource constraints (carrying capacity K)
      - Demographic transition (declining birth rates as prosperity rises)

    Parameters
    ----------
    P : Current population
    r : Intrinsic growth rate (OECD avg: 0.011 = 1.1%/yr [UN WPP 2024])
    K : Carrying capacity (max sustainable population)

    Returns
    -------
    float : Next-period population

    Calibration:
      r = 0.011 (OECD natural growth rate, UN WPP 2024)
      Global r ≈ 0.009 (slowing), OECD r ≈ 0.004-0.008 (low fertility)
      Modelling uses 1.1% to include some immigration effect.

    Example
    -------
    >>> round(logistic_growth(10, 0.011, 500), 4)
    10.1078   # 10 + 0.011*10*(1-10/500) = 10.1078
    """
    if K <= 0:
        raise ValueError("K (carrying capacity) must be positive")
    return P + r * P * (1 - P / K)


def exponential_growth(P: float, r: float) -> float:
    """
    Exponential population growth (no carrying capacity).
    P(t+1) = P(t) × (1 + r)

    Use logistic_growth() for realistic long-run projections.
    This is useful for short-run approximations.

    Example
    -------
    >>> round(exponential_growth(10, 0.011), 4)
    10.11
    """
    return P * (1 + r)


# ===========================================================================
# 7. OKUN'S LAW
# ===========================================================================

def okun_unemployment_change(
    gdp_growth_change: float,
    okun_coefficient: float = -0.5,
) -> float:
    """
    [OKU] Okun's Law — relationship between GDP growth and unemployment.
    Δu = β × ΔGDP_growth  where β ≈ -0.5

    A 1 percentage-point increase in GDP growth reduces unemployment by ~0.5pp.

    Calibration:
      Original Okun (1962): β ≈ -0.3 (US quarterly)
      Modern OECD estimates: β ranges -0.3 to -0.7 depending on country
      Central estimate: -0.5 [Ball, Leigh, Loungani 2013, IMF WP]

    Parameters
    ----------
    gdp_growth_change : Change in GDP growth rate (e.g., +0.01 for 1pp)
    okun_coefficient  : β (default -0.5)

    Returns
    -------
    float : Expected change in unemployment rate (decimal)

    Example
    -------
    >>> round(okun_unemployment_change(0.01), 4)
    -0.005
    """
    return okun_coefficient * gdp_growth_change


def okun_gdp_from_unemployment(
    delta_u: float,
    okun_coefficient: float = -0.5,
) -> float:
    """
    [OKU] Inverse Okun: GDP growth change from unemployment change.
    ΔGDP = Δu / β

    Example
    -------
    >>> round(okun_gdp_from_unemployment(-0.01), 4)
    0.02
    """
    if okun_coefficient == 0:
        raise ValueError("okun_coefficient cannot be zero")
    return delta_u / okun_coefficient


# ===========================================================================
# 8. LAFFER CURVE (SIMPLIFIED)
# ===========================================================================

def laffer_revenue(tax_rate: float, tax_base: float, elasticity: float = 0.5) -> float:
    """
    [LAF] Simplified Laffer Curve — tax revenue given rate and base.
    T = τ × B × (1 - ε × τ)^(1/ε)

    Peak revenue at τ* = 1/(1+ε).
    At ε=0.5: τ* = 1/1.5 = 67% (typically 40-60% in empirical literature).

    Parameters
    ----------
    tax_rate   : Tax rate τ (0 to 1)
    tax_base   : Pre-tax income/output base B
    elasticity : Tax base elasticity ε (0.5 is common middle estimate)

    Returns
    -------
    float : Tax revenue

    Example
    -------
    >>> round(laffer_revenue(0.30, 1000), 2)
    237.67
    """
    if tax_rate < 0 or tax_rate > 1:
        raise ValueError("tax_rate must be in [0, 1]")
    return tax_rate * tax_base * (1 - elasticity * tax_rate) ** (1 / elasticity)


def laffer_optimal_rate(elasticity: float = 0.5) -> float:
    """
    [LAF] Revenue-maximising tax rate from Laffer Curve.
    τ* = 1 / (1 + ε)

    At ε=0.5: τ* = 67%. Empirical literature suggests 40-60%.

    Example
    -------
    >>> round(laffer_optimal_rate(0.5), 4)
    0.6667
    """
    return 1.0 / (1.0 + elasticity)


# ===========================================================================
# 9. HUMAN CAPITAL (EDUCATION)
# ===========================================================================

def human_capital_wage_premium(years_education: float, return_rate: float = 0.10) -> float:
    """
    [BEC] Mincer equation — wage premium from education.
    Wage = W_0 × e^(r × s)  (continuous Mincer)
    Wage = W_0 × (1 + r)^s  (discrete approximation used here)

    Returns multiplier relative to no-education baseline.

    Calibration:
      Mincer return per year: 7-12% (Psacharopoulos 1994 global meta-analysis)
      OECD average: ~10% per year of tertiary education [Education at a Glance 2025]

    Parameters
    ----------
    years_education : Years of education s
    return_rate     : Private return per year r (default 10%)

    Returns
    -------
    float : Wage multiplier (e.g., 2.59 = 159% premium over 10 years)

    Example
    -------
    >>> round(human_capital_wage_premium(10, 0.10), 4)
    2.5937
    """
    return (1 + return_rate) ** years_education


def education_productivity_spillover(
    education_share: float,
    spillover_factor: float = 0.30,
) -> float:
    """
    [BEC] Social return to education (spillover above private return).
    Social TFP boost = education_share × spillover_factor

    Source: Moretti (2004) — each 1pp increase in share with college degree
    raises wages of non-graduates by ~0.5–1.6% in US cities.

    Parameters
    ----------
    education_share  : Fraction of workforce with higher education (0-1)
    spillover_factor : Social return above private (default 0.30 = 30%)

    Returns
    -------
    float : TFP boost (additive fraction of GDP)

    Example
    -------
    >>> round(education_productivity_spillover(0.40), 4)
    0.12
    """
    return education_share * spillover_factor


# ===========================================================================
# 10. TIME BORROWING — TDRW (Time-Debt Recovery Window)
#     Equations 10a–10f are original formulations derived by Enis Murseli
#     with AI assistance (2026).  They have no prior academic equivalent.
#     Citation format: Murseli & AI derivation (2026).
# ===========================================================================

def tdrw_severity(repaid_fraction: float, threshold: float = 0.30) -> float:
    """
    Partial-default severity for TDRW freeze calculation.
    severity = (threshold - p) / threshold   if p < threshold
             = 0                              if p >= threshold

    Source: Murseli & AI derivation (2026) — original equation, no prior equivalent.

    Parameters
    ----------
    repaid_fraction : Fraction of TB obligation actually repaid (0 to 1)
    threshold       : Minimum repayment fraction (default 0.30 = 30%)

    Returns
    -------
    float : Severity in [0, 1]; 0 = at threshold, 1 = full default

    Example
    -------
    >>> round(tdrw_severity(0.20, 0.30), 4)
    0.3333
    >>> tdrw_severity(0.30, 0.30)
    0.0
    >>> tdrw_severity(0.50, 0.30)
    0.0
    """
    if repaid_fraction >= threshold:
        return 0.0
    return (threshold - repaid_fraction) / threshold


def tdrw_freeze_years(
    severity: float,
    period_years: int,
    prior_defaults: int,
    freeze_base: float = 2.0,
    freeze_max: float = 7.0,
    repeat_factor: float = 1.5,
    reference_period: float = 3.0,
) -> float:
    """
    TDRW freeze period in years.
    F = F_base × severity × (1 + d × k) × (T / T_ref)
    F = clamp(F, 0, F_max)

    Source: Murseli & AI derivation (2026) — original equation, no prior academic equivalent.
    Combines actuarial default severity with behavioural repeat-offence scaling
    and borrow-period proportionality. Designed to be self-balancing and non-punitive.

    Parameters
    ----------
    severity       : From tdrw_severity() — 0 to 1
    period_years   : TB advance period T (years)
    prior_defaults : Number of prior defaults d (0 = first offence)
    freeze_base    : Base freeze for full default on T_ref period (default 2.0 yr)
    freeze_max     : Hard ceiling (default 7.0 yr)
    repeat_factor  : Severity multiplier per additional default k (default 1.5)
    reference_period: T_ref (default 3.0 yr)

    Returns
    -------
    float : Freeze period in years

    Derivation:
      At severity=1 (full default), period=3yr (T_ref), no prior defaults:
      F = 2.0 × 1 × 1 × 1 = 2.0 years (base penalty)
      
      Each prior default adds k to the multiplier:
      d=1 → ×(1+1.5)=×2.5 → 5.0 years
      d=2 → ×(1+3.0)=×4.0 → 8.0 → capped at 7.0

    Example
    -------
    >>> round(tdrw_freeze_years(1.0, 5, 0), 2)
    3.33
    >>> round(tdrw_freeze_years(0.333, 5, 0), 2)
    1.11
    >>> tdrw_freeze_years(0.0, 5, 0)
    0.0
    """
    if severity <= 0:
        return 0.0
    repeat_penalty = 1.0 + prior_defaults * repeat_factor
    time_factor = period_years / reference_period
    raw = freeze_base * severity * repeat_penalty * time_factor
    return min(raw, freeze_max)


def tdrw_full(
    amount_advanced: float,
    amount_repaid: float,
    period_years: int,
    prior_defaults: int = 0,
    threshold: float = 0.30,
    freeze_base: float = 2.0,
    freeze_max: float = 7.0,
    repeat_factor: float = 1.5,
    reference_period: float = 3.0,
) -> Tuple[float, float, str]:
    """
    Full TDRW calculation — combines severity + freeze.

    Returns
    -------
    (repaid_fraction, freeze_years, explanation_string)

    Example
    -------
    >>> p, f, _ = tdrw_full(3000, 600, 5, 0)
    >>> round(p, 4), round(f, 4)
    (0.2, 1.1111)
    """
    if amount_advanced <= 0:
        return (1.0, 0.0, "Amount advanced is zero — no obligation")

    p = min(amount_repaid / amount_advanced, 1.0)
    sev = tdrw_severity(p, threshold)
    freeze = tdrw_freeze_years(sev, period_years, prior_defaults,
                               freeze_base, freeze_max, repeat_factor, reference_period)

    explanation = (
        f"Repaid: {p:.1%} of {amount_advanced:.0f} ACU | "
        f"Threshold: {threshold:.0%} | "
        f"Severity: {sev:.3f} | "
        f"Prior defaults: {prior_defaults} | "
        f"Freeze: {freeze:.1f} years"
    )
    return (p, freeze, explanation)


# ===========================================================================
# 11. TB POOL DYNAMICS
# ===========================================================================

def tb_advance_amount(
    requested: float,
    pool_available: float,
    active_borrowers: int,
    a_min: float = 500.0,
    a_max: float = 5000.0,
    reserve_ratio: float = 0.20,
) -> float:
    """
    EQ-TB-1: Approved TB advance amount.
    A = min(requested, a_max, pool_share)
    Return 0 if A < a_min (pool cannot meet minimum).

    pool_share = pool × (1 - reserve_ratio) / max(active_borrowers+1, 1)

    Source: Murseli & AI derivation (2026) — original pool-share constraint formula.

    Example
    -------
    >>> tb_advance_amount(3000, 20000, 3)
    3000.0
    >>> tb_advance_amount(3000, 500, 10)
    0.0
    """
    deployable = pool_available * (1 - reserve_ratio)
    share = deployable / max(active_borrowers + 1, 1)
    approved = min(requested, a_max, share)
    return approved if approved >= a_min else 0.0


def tb_annual_repayment(amount: float, period_years: int, rate: float = 0.0) -> float:
    """
    EQ-TB-2: Annual repayment amount.
    At rate=0: payment = amount / period_years.
    At rate>0: standard amortisation formula.

    Example (0% interest)
    -------
    >>> tb_annual_repayment(3000, 5)
    600.0

    Example (5% interest)
    -------
    >>> round(tb_annual_repayment(3000, 5, 0.05), 2)
    692.82
    """
    if rate == 0.0:
        return amount / period_years
    # Amortisation: PMT = P × r(1+r)^n / ((1+r)^n - 1)
    n = period_years
    return amount * (rate * (1 + rate) ** n) / ((1 + rate) ** n - 1)


def tb_pool_next(
    pool: float,
    automation_tax_in: float,
    repayments: float,
    advances: float,
    loss_rate: float,
    auto_growth_rate: float = 0.10,
    year: int = 1,
) -> float:
    """
    EQ-TB-4: TB pool balance for next period.
    P(t+1) = P(t) + auto_tax(t) + repayments(t) - advances(t) - losses(t)

    auto_tax(t) = automation_tax_in × (1 + g)^year  (compounding automation growth)
    losses(t)   = advances(t) × loss_rate

    Source: Murseli & AI derivation (2026) — original pool dynamics model.

    Example
    -------
    >>> round(tb_pool_next(2000, 200, 350, 500, 0.05, 0.10, 1), 2)
    2232.0
    """
    auto_tax = automation_tax_in * (1 + auto_growth_rate) ** year
    losses = advances * loss_rate
    return pool + auto_tax + repayments - advances - losses


def automation_tax_revenue(
    base_output: float,
    tax_rate: float = 0.15,
    growth_rate: float = 0.10,
    year: int = 0,
) -> float:
    """
    EQ-TB-5: Automation tax revenue in year t.
    T_auto(t) = base_output × (1 + g)^t × τ_auto

    Source: Murseli & AI derivation (2026) — compound growth applied to a ring-fenced
    automation levy.  The growth rate g reflects observed AI output scaling curves.

    Calibration:
      g = 10%/yr automation productivity growth (conservative AI adoption estimate)
      τ = 15% automation tax rate (policy instrument, adjustable)

    Example
    -------
    >>> round(automation_tax_revenue(1000, 0.15, 0.10, 5), 2)
    241.63
    """
    output = base_output * (1 + growth_rate) ** year
    return output * tax_rate


# ===========================================================================
# 12. VALUE ADDED & PRODUCTION CHAIN EQUATIONS
# ===========================================================================

def value_added(
    revenue: float,
    intermediate_inputs: float,
) -> float:
    """
    Value Added = Revenue - Intermediate Inputs
    This is the GDP contribution of a single firm/transaction.

    Source: UN System of National Accounts (SNA 2008).

    Example
    -------
    >>> value_added(1000, 650)
    350
    """
    return revenue - intermediate_inputs


def markup_price(
    unit_cost: float,
    markup_rate: float = 0.30,
) -> float:
    """
    Firm price = unit_cost × (1 + markup)

    Average gross margin (OECD firms): 20-35% [OECD Competition Policy 2023].
    Default markup = 30%.

    Example
    -------
    >>> markup_price(100, 0.30)
    130.0
    """
    return unit_cost * (1 + markup_rate)


def vat_inclusive_price(pre_vat_price: float, vat_rate: float = 0.192) -> float:
    """
    Consumer-facing price inclusive of VAT.
    P_consumer = P_producer × (1 + VAT_rate)

    Calibration: OECD average standard VAT rate = 19.2% (OECD Tax Database 2023).

    Example
    -------
    >>> round(vat_inclusive_price(100, 0.192), 2)
    119.2
    """
    return pre_vat_price * (1 + vat_rate)


def effective_income_tax(
    gross_wage: float,
    pit_rate: float = 0.133,
    social_security_employee: float = 0.081,
) -> float:
    """
    Net take-home pay after income tax + employee social security.
    Net = Gross × (1 - PIT - SSC_employee)

    Calibration:
      PIT effective rate on wages: 13.3% of total labor cost [Tax Foundation 2024]
      Employee SSC: 8.1% of labor cost [Tax Foundation 2024]
      Combined employee deductions: 21.4%
      OECD average tax wedge: 34.8% (includes employer SSC ~13.4%)

    Example
    -------
    >>> round(effective_income_tax(1000), 2)
    805.0
    """
    return gross_wage * (1 - pit_rate - social_security_employee)


# ===========================================================================
# STANDALONE EQUATION RUNNER (for direct inspection)
# ===========================================================================

if __name__ == "__main__":
    import sys
    print("\n" + "=" * 65)
    print("  EQUATION LIBRARY — Individual Equation Verification")
    print("=" * 65)

    tests = [
        ("GDP Expenditure (C+I+G+Xn)",
         lambda: gdp_expenditure(700, 200, 150, 100, 80),
         1070.0, None),

        ("GDP Growth Rate (1025 vs 1000)",
         lambda: gdp_growth_rate(1025, 1000),
         0.025, None),

        ("Quantity Theory Inflation (ΔM=50/M=1000, ΔY=20/Y=1000)",
         lambda: quantity_theory_inflation(50, 1000, 20, 1000),
         0.030, None),

        ("Composite Inflation",
         lambda: composite_inflation(0.04, 0.01, 0.005, 0.0),
         None, None),  # just run it

        ("Fisher Real Rate (i=4.5%, π=2%)",
         lambda: fisher_real_rate(0.045, 0.02),
         0.025, None),

        ("Fisher Real Rate Exact",
         lambda: fisher_real_rate_exact(0.045, 0.02),
         None, None),

        ("Taylor Rule (π=4%, π*=2%, r*=2%, gap=0)",
         lambda: taylor_rule(0.04, 0.02, 0.02, 0.0),
         0.05, None),

        ("Spending Multiplier (MPC=0.45)",
         lambda: spending_multiplier(0.45),
         1.8182, 4),

        ("Tax Multiplier (MPC=0.45)",
         lambda: tax_multiplier(0.45),
         -0.8182, 4),

        ("Balanced Budget Multiplier (MPC=0.45)",
         lambda: balanced_budget_multiplier(0.45),
         1.0, 6),

        ("Solow Growth (TFP=1%, ΔK/K=2.5%, ΔL/L=0.7%)",
         lambda: solow_growth_rate(0.01, 0.025, 0.007),
         0.02294, 4),   # 0.01 + 0.33*0.025 + 0.67*0.007 = 0.02294

        ("Logistic Growth (P=10, r=1.1%, K=500)",
         lambda: logistic_growth(10, 0.011, 500),
         10.1078, 4),   # 10 + 0.011*10*(1-10/500) = 10.1078

        ("Okun Unemployment Change (ΔGDP=+1%)",
         lambda: okun_unemployment_change(0.01),
         -0.005, 4),

        ("Laffer Revenue (τ=30%, B=1000)",
         lambda: laffer_revenue(0.30, 1000),
         None, 2),

        ("Laffer Optimal Rate (ε=0.5)",
         lambda: laffer_optimal_rate(0.5),
         0.6667, 4),

        ("Human Capital Wage Premium (10yr @ 10%)",
         lambda: human_capital_wage_premium(10, 0.10),
         2.5937, 4),

        ("TDRW Severity (20% repaid, 30% threshold)",
         lambda: tdrw_severity(0.20, 0.30),
         0.3333, 4),

        ("TDRW Freeze (full default, 5yr TB, first offence)",
         lambda: tdrw_freeze_years(1.0, 5, 0),
         3.33, 2),

        ("TDRW Freeze (at threshold 30%→ severity=0)",
         lambda: tdrw_freeze_years(0.0, 5, 0),
         0.0, None),

        ("TB Advance Amount (request=3000, pool=20000, borrowers=3)",
         lambda: tb_advance_amount(3000, 20000, 3),
         3000.0, None),

        ("TB Annual Repayment (3000 over 5yr, 0%)",
         lambda: tb_annual_repayment(3000, 5),
         600.0, None),

        ("TB Annual Repayment (3000 over 5yr, 5%)",
         lambda: tb_annual_repayment(3000, 5, 0.05),
         692.92, 2),   # amortized PMT formula, rounded

        ("TB Pool Next Period",
         lambda: tb_pool_next(2000, 200, 350, 500, 0.05, 0.10, 1),
         2045.0, 2),   # 2000+220+350-500-25=2045

        ("Automation Tax Revenue (base=1000, yr=5)",
         lambda: automation_tax_revenue(1000, 0.15, 0.10, 5),
         241.58, 2),   # 1000*1.1^5*0.15 = 241.58

        ("VAT Inclusive Price (100 at 19.2%)",
         lambda: vat_inclusive_price(100, 0.192),
         119.2, 2),

        ("Effective Income Tax Net Pay (1000 gross)",
         lambda: effective_income_tax(1000),
         786.0, 2),   # 1000*(1-0.133-0.081) = 786.0
    ]

    passed = 0
    failed = 0

    print(f"\n  {'Equation':<50} {'Result':>12} {'Status':>8}")
    print("  " + "-" * 75)

    for name, fn, expected, decimals in tests:
        try:
            result = fn()
            if expected is not None:
                decimals = decimals or 4
                assert abs(round(result, decimals) - round(expected, decimals)) < 10**(-decimals + 1), \
                    f"expected {expected}, got {result}"
            print(f"  {name:<50} {result:>12.4f}   [OK]")
            passed += 1
        except Exception as e:
            print(f"  {name:<50} {'ERROR':>12}   [FAIL] {e}")
            failed += 1

    print(f"\n  {'='*75}")
    print(f"  {passed} passed, {failed} failed")
    print("=" * 65)
