"""
simulation.py
=============
Year-by-year simulation engine for the Time-Borrowing Economy.

Uses equation_library.py for all mathematical operations.
Handles both absolute ACU deltas and percentage-change (_pct) deltas.

Algorithm per year:
  1.  Population growth (logistic, equation_library.logistic_growth)
  2.  Recalculate agent headcounts
  3.  TFP / Solow productivity growth
  4.  Apply all 25 relationships (percentage + absolute deltas)
  5.  Fiscal cycle (tax revenue, welfare, govt investment)
  6.  TB pool health check + injection if needed
  7.  Inflation update (equation_library.composite_inflation)
  8.  Interest rate update (equation_library.taylor_rule + smooth_rate_adjustment)
  9.  Enforce hard constraints
  10. Record year snapshot
"""

import random
import math
from copy import deepcopy
from typing import List, Optional

from equation_library import (
    logistic_growth,
    composite_inflation,
    quantity_theory_inflation,
    price_level_update,
    fisher_real_rate,
    taylor_rule,
    smooth_rate_adjustment,
    solow_growth_rate,
)
from parameters import (
    EconomyState, build_initial_state,
    NATURAL_GROWTH_RATE, CARRYING_CAPACITY_MULT,
    MPC, MPS,
    INFLATION_TARGET, NOMINAL_INTEREST_RATE,
    BASE_PRODUCTIVITY_GROWTH, AUTOMATION_BOOST,
    WELFARE_RATE, GOVT_INVESTMENT_RATE,
    INCOME_TAX_RATE, SSC_EMPLOYEE_RATE, VAT_RATE,
    TAX_TO_GDP_RATIO,
    TB_AUTOMATION_TAX_RATE,
)
from agents import distribute_population, AGENT_SHARES
from relationships import RELATIONSHIPS

# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "years":           20,
    "n_people":        10,
    "initial_money":   1000.0,
    "initial_resources": 1000.0,
    "random_seed":     42,

    # Annual transaction volumes (base for N=10 population)
    "base_tx_per_rel": {
        "R01": 2000,   # Consumer→Producer: most common
        "R02": 500,    # Tax payments
        "R03": 300,    # Welfare (monthly for ~5 FreeOne)
        "R04": 1200,   # Wage payments (monthly × 4 workers)
        "R05": 1800,   # VAT (on every purchase)
        "R06": 100,    # Deficit financing (rare)
        "R07": 50,     # Rate changes
        "R08": 3000,   # B2B (dominant)
        "R09": 100,    # TB advances
        "R10": 80,     # TB repayments
        "R11": 500,    # Automation tax (continuous)
        "R12": 150,    # Infrastructure investment
        "R13": 250,    # FreeOne spending
        "R14": 50,     # Climate shocks (conditional)
        "R15": 200,    # Inflation impact
        "R16": 100,    # R&D investment
        "R17": 300,    # Exports
        "R18": 250,    # Imports
        "R19": 30,     # TB defaults (~5% of borrowers)
        "R20": 80,     # Education → workforce
        "R21": 50,     # TB pool top-up (conditional)
        "R22": 20,     # Wage-price spiral (conditional)
        "R23": 120,    # Hiring from FreeOne
        "R24": 80,     # Subsidies
        "R25": 100,    # Debt service (conditional)
        "R26": 60,     # TB-funded education (conditional on TB)
        "R27": 40,     # TB-funded entrepreneurship (conditional on TB)
        "R28": 80,     # TB productivity premium (conditional on TB)
    },

    "climate_shocks":     True,
    "automation_enabled": True,
    "tb_enabled":         True,
    "open_economy":       True,

    "policy": {
        "tb_max_amount":           5000,
        "tb_min_amount":           500,
        "tb_automation_tax_rate":  0.15,
        "tb_max_period_years":     5,
        "income_tax_rate":         INCOME_TAX_RATE,   # 13.3% (verified)
        "vat_rate":                VAT_RATE,           # 19.2% (verified)
        "welfare_rate":            WELFARE_RATE,       # 12%
        "govt_investment_rate":    GOVT_INVESTMENT_RATE,  # 3%
        "inflation_target":        INFLATION_TARGET,   # 2%
    },
}


class TimeBorrowingEconomy:
    """Year-by-year simulation of the Time Borrowing Economy."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or DEFAULT_CONFIG
        random.seed(self.config.get("random_seed", 42))
        self.history: List[EconomyState] = []

    def _init_state(self) -> EconomyState:
        return build_initial_state(
            n_people          = self.config["n_people"],
            initial_money     = self.config["initial_money"],
            initial_resources = self.config["initial_resources"],
        )

    # ── Transaction scaling ─────────────────────────────────────────────────

    def _tx_volume(self, rel_id: str, s: EconomyState) -> float:
        base = self.config["base_tx_per_rel"].get(rel_id, 500)
        pop_scale = s.population / self.config["n_people"]
        return base * pop_scale

    # ── Conditional gating ──────────────────────────────────────────────────

    def _should_apply(self, rel_id: str, s: EconomyState):
        """Return (active: bool, n_tx: float)."""
        # Climate shock: 20% chance, random severity
        if rel_id == "R14":
            if not self.config.get("climate_shocks", True) or random.random() > 0.20:
                return False, 0.0
            return True, self._tx_volume(rel_id, s) * random.uniform(0.3, 1.0)

        # Wage-price spiral: only if inflation > 4%
        if rel_id == "R22":
            if s.inflation <= 0.04:
                return False, 0.0
            strength = (s.inflation - 0.04) / 0.04
            return True, self._tx_volume(rel_id, s) * strength

        # TB operations: only if TB enabled
        if rel_id in ("R09", "R10", "R11", "R19", "R21", "R26", "R27", "R28"):
            if not self.config.get("tb_enabled", True):
                return False, 0.0

        # Exports/imports: only if open economy
        if rel_id in ("R17", "R18"):
            if not self.config.get("open_economy", True):
                return False, 0.0

        # Automation: scale with compound growth
        if rel_id == "R11":
            growth = (1 + 0.10) ** s.year
            return True, self._tx_volume(rel_id, s) * min(growth, 8.0)

        # Deficit financing: only when in deficit
        if rel_id == "R06":
            if s.government_balance >= 0:
                return False, 0.0

        # Debt service: proportional to debt/GDP
        if rel_id == "R25":
            if s.cumulative_debt <= 0:
                return False, 0.0
            debt_gdp = s.cumulative_debt / max(s.resources_produced, 1)
            return True, self._tx_volume(rel_id, s) * debt_gdp * 100

        # TB top-up: only when pool needs it
        if rel_id == "R21":
            if s.tb_injection_needed <= 0:
                return False, 0.0

        return True, self._tx_volume(rel_id, s)

    # ── Apply delta dict to state ────────────────────────────────────────────

    def _apply_deltas(self, s: EconomyState, deltas: dict) -> None:
        """
        Handle both absolute and percentage-change keys.
        Keys ending in '_pct' are applied as: value *= (1 + delta_pct).
        All other numeric keys are added: value += delta.
        """
        for key, delta in deltas.items():
            if not isinstance(delta, (int, float)):
                continue

            if key.endswith("_pct"):
                # Percentage change: multiply current value
                base_key = key[:-4]
                if hasattr(s, base_key):
                    current = getattr(s, base_key)
                    if isinstance(current, float):
                        setattr(s, base_key, current * (1 + delta))
            else:
                # Absolute change: add delta
                if hasattr(s, key):
                    current = getattr(s, key)
                    if isinstance(current, (int, float)):
                        setattr(s, key, current + delta)

            # Log all deltas
            if key not in s.delta_log:
                s.delta_log[key] = 0.0
            s.delta_log[key] = s.delta_log.get(key, 0.0) + delta

    # ── Inflation update ─────────────────────────────────────────────────────

    def _update_inflation(self, s: EconomyState, prev_M: float, prev_Y: float) -> None:
        """
        equation_library.composite_inflation wraps:
          - Quantity Theory (monetary channel)
          - Demand-pull (Keynesian)
          - Cost-push (supply-side)
          - Supply shock (exogenous)
        """
        monetary = quantity_theory_inflation(
            s.money_supply - prev_M, prev_M,
            s.resources_produced - prev_Y, prev_Y,
        )
        s.inflation = composite_inflation(
            monetary     = monetary,
            demand_pull  = s.delta_log.get("inflation", 0.0) * 0.40,
            cost_push    = s.delta_log.get("cost_push", 0.0),
            supply_shock = s.supply_shock,
            target       = self.config["policy"]["inflation_target"],
            cb_anchoring = 0.35,
        )
        # Bound: -10% to +40%
        s.inflation = max(-0.10, min(0.40, s.inflation))
        s.price_level = price_level_update(s.price_level, s.inflation)

    # ── Interest rate update (Taylor Rule) ──────────────────────────────────

    def _update_interest_rate(self, s: EconomyState) -> None:
        """
        Uses equation_library.taylor_rule (verified, output gap capped ±10%).
        Then smoothed via partial-adjustment inertia model.
        """
        y_potential = self.config["initial_resources"] * (
            (1 + BASE_PRODUCTIVITY_GROWTH) ** s.year
        )
        raw_gap = (s.resources_produced - y_potential) / max(y_potential, 1)
        output_gap = max(-0.10, min(0.10, raw_gap))

        i_target = taylor_rule(
            inflation        = s.inflation,
            inflation_target = self.config["policy"]["inflation_target"],
            neutral_real_rate= 0.02,
            output_gap       = output_gap,
        )
        s.nominal_interest_rate = smooth_rate_adjustment(
            i_prev   = s.nominal_interest_rate,
            i_target = i_target,
            speed    = 0.30,
        )
        s.real_interest_rate = fisher_real_rate(s.nominal_interest_rate, s.inflation)

    # ── Hard constraints ─────────────────────────────────────────────────────

    def _enforce_constraints(self, s: EconomyState) -> None:
        s.resources_consumed = min(s.resources_consumed, s.resources_produced)
        s.resources_consumed = max(0.0, s.resources_consumed)
        s.resources_produced = max(10.0, s.resources_produced)
        s.population         = max(1.0, s.population)
        s.money_supply       = max(10.0, s.money_supply)
        s.tb_pool_size       = max(0.0, s.tb_pool_size)
        s.tb_active_borrowers = max(0, s.tb_active_borrowers)
        s.tb_defaulters      = max(0, s.tb_defaulters)
        s.gini_coefficient   = max(0.0, min(1.0, s.gini_coefficient))
        s.inflation          = max(-0.10, min(0.40, s.inflation))
        s.employment_rate    = max(0.0, min(1.0, s.employment_rate))

    def _tb_health_check(self, s: EconomyState) -> None:
        """Flag if TB pool is below 20% reserve floor."""
        reserve = 0.20
        annual_auto_tax = s.resources_produced * 0.05 * TB_AUTOMATION_TAX_RATE
        min_pool = annual_auto_tax * 0.5
        if s.tb_pool_size < min_pool:
            s.tb_injection_needed = max(0.0, min_pool - s.tb_pool_size)

    # ── STEP ────────────────────────────────────────────────────────────────

    def step(self, s: EconomyState) -> EconomyState:
        ns = deepcopy(s)
        ns.year = s.year + 1
        ns.delta_log = {}
        ns.relationship_transactions = {}
        ns.supply_shock = 0.0

        prev_M = s.money_supply
        prev_Y = s.resources_produced

        # 1. Population (logistic)
        ns.population = logistic_growth(
            s.population, NATURAL_GROWTH_RATE,
            self.config["n_people"] * CARRYING_CAPACITY_MULT
        )
        agents = distribute_population(ns.population)
        ns.n_government = agents["government"]
        ns.n_producer   = agents["producer"]
        ns.n_freeone    = agents["freeone"]
        ns.n_consumer   = agents["consumer"]

        # 2. Solow TFP growth (before relationships)
        auto_boost = AUTOMATION_BOOST if self.config.get("automation_enabled") else 0.0
        tfp = BASE_PRODUCTIVITY_GROWTH + auto_boost   # 1.5% total
        labour_g = (ns.population - s.population) / max(s.population, 1)
        capital_g = 0.025  # assumed 2.5%/yr capital growth
        gdp_growth_tfp = solow_growth_rate(tfp, capital_g, labour_g)
        ns.resources_produced *= (1 + gdp_growth_tfp)
        ns.productivity_per_worker *= (1 + tfp)

        # 3. Apply all 25 relationships
        for rel in RELATIONSHIPS:
            rid = rel["id"]
            active, n_tx = self._should_apply(rid, ns)
            if not active:
                continue
            deltas = rel["fn"](ns, n_tx)
            self._apply_deltas(ns, deltas)
            ns.relationship_transactions[rid] = round(n_tx, 1)

        # 4. Fiscal cycle
        policy = self.config["policy"]
        ns.tax_revenue = (
            ns.resources_produced * policy["income_tax_rate"] * AGENT_SHARES["producer"]
            + ns.resources_consumed * policy["vat_rate"]
        )
        ns.welfare_spend    = ns.resources_produced * policy["welfare_rate"]
        ns.government_spend = ns.resources_produced * policy["govt_investment_rate"]
        ns.government_balance = ns.tax_revenue - ns.welfare_spend - ns.government_spend
        if ns.government_balance < 0:
            ns.cumulative_debt += abs(ns.government_balance)

        # Govt spending recycles money back into circulation
        ns.money_supply += (ns.welfare_spend + ns.government_spend) * 0.35

        # 5. TB health
        self._tb_health_check(ns)

        # 6. Inflation (Quantity Theory + composite)
        ns.supply_shock = ns.delta_log.get("supply_shock", 0.0)
        self._update_inflation(ns, prev_M, prev_Y)

        # 7. Interest rate (Taylor Rule + Fisher)
        self._update_interest_rate(ns)

        # 8. Hard constraints
        self._enforce_constraints(ns)

        return ns

    # ── RUN ────────────────────────────────────────────────────────────────

    def run(self) -> List[EconomyState]:
        state = self._init_state()
        self.history = [state]

        years = self.config["years"]
        print(f"\nTime-Borrowing Economy Simulation  ({years} years, N={self.config['n_people']})")
        print("=" * 82)
        print(f"{'Year':>5} {'Population':>11} {'GDP':>9} {'Money':>9} "
              f"{'Inflation':>10} {'RealRate':>9} {'TBPool':>8} {'Gini':>7}")
        print("-" * 82)

        for _ in range(years):
            state = self.step(state)
            self.history.append(state)
            print(
                f"{state.year:>5} {state.population:>11.1f} "
                f"{state.resources_produced:>9.0f} "
                f"{state.money_supply:>9.0f} "
                f"{state.inflation:>10.2%} "
                f"{state.real_interest_rate:>9.2%} "
                f"{state.tb_pool_size:>8.0f} "
                f"{state.gini_coefficient:>7.3f}"
            )

        print("=" * 82)
        return self.history

    # ── EXPORT ─────────────────────────────────────────────────────────────

    def to_records(self) -> list:
        records = []
        for s in self.history:
            records.append({
                "year":               s.year,
                "population":         round(s.population, 2),
                "n_government":       round(s.n_government, 2),
                "n_producer":         round(s.n_producer, 2),
                "n_freeone":          round(s.n_freeone, 2),
                "money_supply":       round(s.money_supply, 2),
                "price_level":        round(s.price_level, 4),
                "inflation_pct":      round(s.inflation * 100, 3),
                "nominal_rate_pct":   round(s.nominal_interest_rate * 100, 3),
                "real_rate_pct":      round(s.real_interest_rate * 100, 3),
                "resources_produced": round(s.resources_produced, 2),
                "resources_consumed": round(s.resources_consumed, 2),
                "investment":         round(s.investment, 2),
                "tax_revenue":        round(s.tax_revenue, 2),
                "govt_balance":       round(s.government_balance, 2),
                "cumulative_debt":    round(s.cumulative_debt, 2),
                "tb_pool_size":       round(s.tb_pool_size, 2),
                "tb_issued":          round(s.tb_amount_issued, 2),
                "tb_repayments":      round(s.tb_repayments_received, 2),
                "tb_loss_rate_pct":   round(s.tb_loss_rate * 100, 3),
                "tb_active_borrowers": s.tb_active_borrowers,
                "tb_defaulters":      s.tb_defaulters,
                "automation_tax":     round(s.automation_tax_collected, 2),
                "welfare_spend":      round(s.welfare_spend, 2),
                "employment_rate_pct": round(s.employment_rate * 100, 3),
                "productivity":       round(s.productivity_per_worker, 2),
                "gini":               round(s.gini_coefficient, 4),
            })
        return records

    def save_csv(self, path: str) -> None:
        import csv
        records = self.to_records()
        if not records:
            return
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        print(f"Saved  {path}")

    def save_json(self, path: str) -> None:
        import json
        with open(path, "w") as f:
            json.dump(self.to_records(), f, indent=2)
        print(f"Saved  {path}")


if __name__ == "__main__":
    import os
    sim = TimeBorrowingEconomy()
    history = sim.run()
    out = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(out, exist_ok=True)
    sim.save_csv(os.path.join(out, "simulation_results.csv"))
    sim.save_json(os.path.join(out, "simulation_results.json"))
    print("\nDone. See outputs/")
