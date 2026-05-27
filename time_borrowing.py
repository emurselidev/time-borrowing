"""
time_borrowing.py
=================
The Time Borrowing Instrument — core mathematical model.

Central equations:
  1. Eligibility check
  2. Advance amount calculation
  3. Repayment schedule
  4. Freeze period calculation (partial default)
  5. TB pool sustainability check
  6. Automation tax projection

Theory Summary
--------------
Citizens borrow against their FUTURE TIME (labour/contribution) rather than
against financial collateral.  The liquidity pool is funded entirely by an
automation/AI tax — therefore the money supply expansion is directly tied to
real productivity growth, not arbitrary fiat printing.

[AI & Automation Work Done]
        │
        ▼  (15% Automation Tax)
[TB Liquidity Pool]
        │
        ▼  (TB Advance to Citizen)
[Citizen receives capital → studies / innovates / bridges hardship]
        │
        ▼  (Future time contribution: work, tax, community service)
[Repayment → Pool Refilled]
        │ (if partial default: ▼)
[Freeze Period Calculated → Citizen excluded for N years]
        │ (pool deficit: ▼)
[Government Tax Top-Up → pool stabilised]
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, List


# ---------------------------------------------------------------------------
# INSTRUMENT CONSTANTS  (governable input parameters)
# ---------------------------------------------------------------------------

DEFAULT_PARAMS = {
    # Pool funding
    "automation_tax_rate":       0.15,   # 15% levy on AI/automation output value
    "pool_seed_multiplier":      2.0,    # Pool seeded at 2× annual automation tax

    # Advance limits
    "tb_min_amount":             500,    # Minimum advance (ACU)
    "tb_max_amount":             5000,   # Maximum advance per person per cycle
    "tb_max_period_years":       5,      # Maximum borrow window
    "tb_min_period_years":       1,      # Minimum borrow window

    # Repayment
    "tb_interest_rate":          0.00,   # 0% — no financial interest (time-collateral)
    "tb_repayment_min_pct":      0.30,   # Below 30% repayment = partial default
    "repayment_grace_months":    3,      # Grace period before freeze kicks in

    # Freeze (partial default)
    "freeze_base_years":         2.0,    # Minimum freeze for full default
    "freeze_max_years":          7.0,    # Maximum freeze years
    "freeze_decay_factor":       1.5,    # Severity multiplier for repeat defaults

    # Pool health
    "pool_min_reserve_ratio":    0.20,   # 20% must remain as reserve
    "loss_write_off_threshold":  0.70,   # Write off if recovery < 70% after freeze

    # Automation growth
    "automation_growth_rate":    0.10,   # 10% annual growth in AI/automation output
}


# ---------------------------------------------------------------------------
# BORROWER RECORD
# ---------------------------------------------------------------------------

@dataclass
class TBBorrower:
    """State record for one TB borrower."""
    borrower_id:      str
    amount_advanced:  float         # ACU advanced
    period_years:     int           # Agreed TB window
    year_issued:      int           # Year advance was made
    year_due:         int           # Year full repayment expected
    amount_repaid:    float = 0.0   # ACU repaid so far
    is_frozen:        bool  = False # Currently in freeze window?
    freeze_until_year:int   = 0     # First year eligible again
    default_count:    int   = 0     # Number of prior defaults
    notes:            str   = ""

    @property
    def repayment_pct(self) -> float:
        if self.amount_advanced == 0:
            return 1.0
        return self.amount_repaid / self.amount_advanced

    @property
    def outstanding(self) -> float:
        return max(0.0, self.amount_advanced - self.amount_repaid)

    @property
    def is_fully_repaid(self) -> bool:
        return self.repayment_pct >= 1.0


# ---------------------------------------------------------------------------
# CORE EQUATIONS
# ---------------------------------------------------------------------------

def calculate_advance_amount(
    requested: float,
    tb_pool_available: float,
    n_active_borrowers: int,
    population: float,
    params: dict = None,
) -> float:
    """
    EQ-TB-1: Advance Amount
    -----------------------
    Governs how much a single citizen can receive.

    A = min(requested, A_max, pool_share)

    where:
      A_max      = params["tb_max_amount"]
      pool_share = (available_pool × pool_allocation_pct) / projected_borrowers
      pool_allocation_pct = 1 - reserve_ratio = 0.80

    Returns
    -------
    float : approved advance amount (0 if pool insufficient)
    """
    p = params or DEFAULT_PARAMS
    a_min = p["tb_min_amount"]
    a_max = p["tb_max_amount"]
    reserve = p["pool_min_reserve_ratio"]

    deployable_pool = tb_pool_available * (1 - reserve)
    projected_borrowers = max(n_active_borrowers + 1, 1)
    pool_share = deployable_pool / projected_borrowers

    approved = min(requested, a_max, pool_share)
    return max(approved, 0.0) if approved >= a_min else 0.0


def repayment_schedule(
    amount: float,
    period_years: int,
    params: dict = None,
) -> List[float]:
    """
    EQ-TB-2: Annual Repayment Schedule
    ------------------------------------
    Since TB interest rate = 0%, repayment is simply:
      annual_payment = amount / period_years

    Returns list of annual repayment amounts (length = period_years).
    """
    p = params or DEFAULT_PARAMS
    rate = p["tb_interest_rate"]

    if rate == 0.0:
        # Equal annual instalments
        annual = amount / period_years
        return [annual] * period_years
    else:
        # Amortised schedule (for non-zero rate scenarios)
        r = rate
        n = period_years
        pmt = amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        schedule = []
        balance = amount
        for _ in range(n):
            interest = balance * r
            principal = pmt - interest
            schedule.append(pmt)
            balance -= principal
        return schedule


def calculate_freeze_period(
    amount_advanced:  float,
    amount_repaid:    float,
    period_years:     int,
    default_count:    int = 0,
    params:           dict = None,
) -> Tuple[float, str]:
    """
    EQ-TB-3: Freeze Period After Partial Default
    ----------------------------------------------
    Named Equation: "Time-Debt Recovery Window" (TDRW)

    When a borrower repays < repayment_min_pct of their obligation,
    they are frozen from new TB access for a calculated period.

    TDRW formula:
    ─────────────────────────────────────────────────────────────────
    Let:
      p     = repayment_pct     (0 to 1)
      p_min = min_repayment_pct (default 0.30)
      T     = TB period (years)
      d     = default_count (prior defaults, starting at 0)
      F_base= freeze_base_years
      F_max = freeze_max_years
      k     = freeze_decay_factor (severity multiplier)

    Default severity:
      severity = (p_min - p) / p_min        if p < p_min  else 0
               = (0.30 - p) / 0.30  for p_min=0.30

    Freeze years:
      F = F_base × severity × (1 + d × k) × (T / T_ref)
      T_ref = 3  (reference period)
      F = clamp(F, 0, F_max)

    Intuition:
      • Full default (p=0): F = F_base × (T/3) × (1+d×k)
      • Paid 30% exactly: F = 0  (at the threshold — no freeze)
      • Each prior default adds k×F_base penalty
    ─────────────────────────────────────────────────────────────────

    Returns
    -------
    (freeze_years: float, explanation: str)
    """
    p = params or DEFAULT_PARAMS
    p_min    = p["tb_repayment_min_pct"]
    F_base   = p["freeze_base_years"]
    F_max    = p["freeze_max_years"]
    k        = p["freeze_decay_factor"]
    T_ref    = 3.0

    repay_pct = amount_repaid / amount_advanced if amount_advanced > 0 else 0.0

    if repay_pct >= p_min:
        return (0.0, f"No freeze: repaid {repay_pct:.1%} ≥ threshold {p_min:.0%}")

    severity = (p_min - repay_pct) / p_min    # 0 to 1
    repeat_penalty = 1.0 + default_count * k
    time_factor = period_years / T_ref

    freeze_raw = F_base * severity * repeat_penalty * time_factor
    freeze = min(freeze_raw, F_max)

    explanation = (
        f"Repaid {repay_pct:.1%} of {amount_advanced:.0f} ACU "
        f"(threshold {p_min:.0%})\n"
        f"  Severity       = {severity:.3f}\n"
        f"  Repeat penalty = ×{repeat_penalty:.2f} ({default_count} prior defaults)\n"
        f"  Time factor    = {time_factor:.2f} ({period_years}-year TB)\n"
        f"  Freeze period  = {freeze_raw:.2f} → capped at {freeze:.1f} years"
    )

    return (freeze, explanation)


def tb_pool_sustainability(
    pool_size:          float,
    annual_advances:    float,
    annual_repayments:  float,
    automation_tax_in:  float,
    loss_rate:          float,
    years_horizon:      int = 10,
    params:             dict = None,
) -> dict:
    """
    EQ-TB-4: Pool Sustainability Projection
    ----------------------------------------
    Projects TB pool health over a future horizon.

    Pool dynamics:
      P(t+1) = P(t) + automation_tax_in(t) + repayments(t)
               - advances(t) - losses(t)

    where:
      losses(t)           = advances(t) × loss_rate
      automation_tax_in(t) = automation_tax_in(0) × (1 + g)^t
      g                   = automation_growth_rate

    Returns dict with:
      'solvent'       : bool — stays above reserve floor throughout
      'pool_by_year'  : list of pool sizes
      'shortfall_year': first year below reserve (or None)
      'total_deficit' : cumulative deficit if insolvent
    """
    p = params or DEFAULT_PARAMS
    g = p["automation_growth_rate"]
    reserve = p["pool_min_reserve_ratio"]

    pool = pool_size
    pool_by_year = [pool]
    shortfall_year = None
    total_deficit = 0.0

    for t in range(1, years_horizon + 1):
        tax_in      = automation_tax_in * (1 + g) ** t
        losses      = annual_advances * loss_rate
        net_flow    = tax_in + annual_repayments - annual_advances - losses
        pool        = pool + net_flow
        pool_by_year.append(pool)

        min_reserve = pool_size * reserve  # reserve floor = 20% of initial
        if pool < min_reserve and shortfall_year is None:
            shortfall_year = t
            total_deficit += abs(min(0, pool - min_reserve))

    return {
        "solvent":        shortfall_year is None,
        "pool_by_year":   pool_by_year,
        "shortfall_year": shortfall_year,
        "total_deficit":  total_deficit,
        "final_pool":     pool_by_year[-1],
    }


def automation_tax_projection(
    base_automation_output: float,
    tax_rate:               float = 0.15,
    growth_rate:            float = 0.10,
    years:                  int   = 20,
) -> List[Tuple[int, float, float]]:
    """
    EQ-TB-5: Automation Tax Revenue Projection
    -------------------------------------------
    Projects the AI/automation tax inflow to the TB pool.

    automation_output(t) = base × (1 + g)^t
    tax_revenue(t)       = automation_output(t) × tax_rate

    Returns list of (year, automation_output, tax_revenue) tuples.
    """
    results = []
    for t in range(years + 1):
        output = base_automation_output * (1 + growth_rate) ** t
        revenue = output * tax_rate
        results.append((t, round(output, 2), round(revenue, 2)))
    return results


def eligibility_check(
    borrower_id:       str,
    is_currently_frozen: bool,
    freeze_until_year: int,
    current_year:      int,
    has_active_loan:   bool,
    tb_pool_available: float,
    params:            dict = None,
) -> Tuple[bool, str]:
    """
    EQ-TB-0: Eligibility Gate
    --------------------------
    Before any advance is made, borrower must pass all gates:

    Gate 1: Not currently in a freeze window
    Gate 2: No active outstanding TB loan
    Gate 3: Pool has sufficient funds (above reserve)

    Returns (eligible: bool, reason: str)
    """
    p = params or DEFAULT_PARAMS
    reserve = p["pool_min_reserve_ratio"]
    a_min   = p["tb_min_amount"]

    if is_currently_frozen and current_year < freeze_until_year:
        remaining = freeze_until_year - current_year
        return (False, f"Frozen: {remaining} year(s) remaining (until year {freeze_until_year})")

    if has_active_loan:
        return (False, "Ineligible: existing active TB loan not yet repaid")

    deployable = tb_pool_available * (1 - reserve)
    if deployable < a_min:
        return (False, f"Pool insufficient: deployable {deployable:.0f} < minimum {a_min}")

    return (True, "Eligible for Time Borrowing advance")


# ---------------------------------------------------------------------------
# QUICK TEST / DEMO
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  TIME BORROWING INSTRUMENT — Equation Demonstrations")
    print("=" * 60)

    # --- EQ-TB-1: Advance Amount ---
    print("\n[EQ-TB-1] Advance Amount Calculation")
    advance = calculate_advance_amount(
        requested=3000, tb_pool_available=8000,
        n_active_borrowers=3, population=10
    )
    print(f"  Requested: 3000 ACU | Approved: {advance:.0f} ACU")

    # --- EQ-TB-2: Repayment Schedule ---
    print("\n[EQ-TB-2] Repayment Schedule (3000 ACU, 5 years, 0% interest)")
    sched = repayment_schedule(3000, 5)
    for i, pmt in enumerate(sched, 1):
        print(f"  Year {i}: {pmt:.0f} ACU")

    # --- EQ-TB-3: Freeze Period ---
    print("\n[EQ-TB-3] Freeze Period — TDRW Equation")
    cases = [
        (3000, 0,    5, 0, "Full default, first offence"),
        (3000, 900,  5, 0, "Paid 30% exactly"),
        (3000, 600,  5, 0, "Paid 20%, 5-year TB"),
        (3000, 600,  5, 1, "Paid 20%, 5-year TB, 1 prior default"),
        (3000, 300,  3, 2, "Paid 10%, 3-year TB, 2 prior defaults"),
    ]
    for amt, repaid, period, d_count, desc in cases:
        years_f, expl = calculate_freeze_period(amt, repaid, period, d_count)
        print(f"\n  Case: {desc}")
        print(f"  {expl}")

    # --- EQ-TB-4: Pool Sustainability ---
    print("\n[EQ-TB-4] Pool Sustainability (10-year projection)")
    result = tb_pool_sustainability(
        pool_size=2000, annual_advances=500, annual_repayments=350,
        automation_tax_in=200, loss_rate=0.05, years_horizon=10
    )
    print(f"  Solvent:  {result['solvent']}")
    print(f"  Pool by year: {[round(v,0) for v in result['pool_by_year']]}")
    if not result['solvent']:
        print(f"  First shortfall: Year {result['shortfall_year']}")

    # --- EQ-TB-5: Automation Tax Projection ---
    print("\n[EQ-TB-5] Automation Tax Revenue Projection (10 years)")
    proj = automation_tax_projection(base_automation_output=500, years=10)
    print(f"  {'Year':>5} {'Auto Output':>14} {'TB Tax Revenue':>16}")
    print(f"  {'-'*5} {'-'*14} {'-'*16}")
    for yr, output, rev in proj:
        print(f"  {yr:>5} {output:>14,.1f} {rev:>16,.1f}")
