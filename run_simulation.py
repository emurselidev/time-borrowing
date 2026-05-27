"""
run_simulation.py
=================
Entry point: run the Time-Borrowing Economy simulation and produce
output files (CSV, JSON) and optional charts (requires matplotlib).

Usage:
  python run_simulation.py                     # default config
  python run_simulation.py --years 30          # 30-year run
  python run_simulation.py --people 100        # 100 initial people
  python run_simulation.py --no-tb             # disable Time Borrowing
  python run_simulation.py --no-climate        # no climate shocks
  python run_simulation.py --compare           # compare TB vs no-TB
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

from simulation import TimeBorrowingEconomy, DEFAULT_CONFIG
from time_borrowing import (
    calculate_freeze_period, tb_pool_sustainability,
    automation_tax_projection, DEFAULT_PARAMS,
)
from agents import agent_summary_table
from relationships import relationships_summary


def print_header():
    print("\n" + "=" * 78)
    print("  TIME-BORROWING ECONOMY SIMULATION  v1.0")
    print("  A Productivity-Backed, Automation-Funded Economic Instrument")
    print("=" * 78)


def run_scenario(config: dict, label: str = "Base") -> list:
    """Run a single scenario and save outputs."""
    print(f"\n{'─'*78}")
    print(f"  Scenario: {label}")
    print(f"{'─'*78}")
    sim = TimeBorrowingEconomy(config)
    history = sim.run()

    slug = label.lower().replace(" ", "_")
    sim.save_csv(os.path.join(OUTPUT_DIR, f"{slug}_results.csv"))
    sim.save_json(os.path.join(OUTPUT_DIR, f"{slug}_results.json"))
    return history


def compare_scenarios(years: int, n_people: int):
    """Run TB enabled vs disabled and print summary comparison."""
    print("\n\n" + "=" * 78)
    print("  SCENARIO COMPARISON: Time Borrowing ON vs OFF")
    print("=" * 78)

    cfg_on  = {**DEFAULT_CONFIG, "years": years, "n_people": n_people, "tb_enabled": True,  "random_seed": 42}
    cfg_off = {**DEFAULT_CONFIG, "years": years, "n_people": n_people, "tb_enabled": False, "random_seed": 42}

    hist_on  = run_scenario(cfg_on,  "TB Enabled")
    hist_off = run_scenario(cfg_off, "TB Disabled")

    print("\n\n  FINAL YEAR COMPARISON")
    print(f"  {'Metric':<30} {'TB Enabled':>15} {'TB Disabled':>15} {'Δ':>12}")
    print(f"  {'-'*75}")

    def _last(h, attr):
        return getattr(h[-1], attr, 0)

    metrics = [
        ("GDP (resources produced)",    "resources_produced",  ".0f"),
        ("Money Supply",                "money_supply",        ".0f"),
        ("Inflation (%)",               "inflation",           ".2%"),
        ("Real Interest Rate (%)",      "real_interest_rate",  ".2%"),
        ("TB Pool Size",                "tb_pool_size",        ".0f"),
        ("Gini Coefficient",            "gini_coefficient",    ".4f"),
        ("Cumulative Gov Debt",         "cumulative_debt",     ".0f"),
        ("Population",                  "population",          ".1f"),
        ("Employment Rate (%)",         "employment_rate",     ".2%"),
        ("Automation Tax Collected",    "automation_tax_collected", ".0f"),
    ]

    for label, attr, fmt in metrics:
        v_on  = _last(hist_on,  attr)
        v_off = _last(hist_off, attr)
        delta = v_on - v_off
        fmt_str = f"{{:{fmt}}}"
        print(
            f"  {label:<30} {fmt_str.format(v_on):>15} "
            f"{fmt_str.format(v_off):>15} "
            f"{fmt_str.format(delta):>12}"
        )


def show_tb_equations():
    """Demonstrate TB instrument equations."""
    print("\n\n" + "=" * 78)
    print("  TIME BORROWING INSTRUMENT — Key Equations")
    print("=" * 78)

    print("\n  [EQ-TB-0] Eligibility Check")
    print("  ─────────────────────────────────────────────────────────────────")
    print("  A citizen is eligible for TB advance if:")
    print("    1. NOT in a freeze window  (no prior default blocking)")
    print("    2. No active outstanding TB loan")
    print("    3. TB pool deployable balance ≥ minimum advance amount")

    print("\n  [EQ-TB-1] Advance Amount")
    print("  ─────────────────────────────────────────────────────────────────")
    print("  A = min(requested, A_max, pool_share)")
    print("  where pool_share = Pool × (1 − reserve_ratio) ÷ active_borrowers")
    print(f"  A_min = {DEFAULT_PARAMS['tb_min_amount']} ACU")
    print(f"  A_max = {DEFAULT_PARAMS['tb_max_amount']} ACU")

    print("\n  [EQ-TB-2] Repayment Schedule (0% interest)")
    print("  ─────────────────────────────────────────────────────────────────")
    print("  Annual payment = Amount ÷ Period")
    print("  No compounding interest — only time collateral is pledged.")

    print("\n  [EQ-TB-3] Freeze Period (TDRW — Time-Debt Recovery Window)")
    print("  ─────────────────────────────────────────────────────────────────")
    print("  F = F_base × severity × (1 + d×k) × (T / T_ref)")
    print("  where:")
    print("    severity = (p_min − p) / p_min    [0 to 1]")
    print("    d        = number of prior defaults")
    print("    k        = freeze_decay_factor (default 1.5)")
    print("    T_ref    = 3 years (reference TB period)")
    print(f"    F_max    = {DEFAULT_PARAMS['freeze_max_years']} years")
    print()
    print("  Example cases:")

    cases = [
        (5000, 0,    5, 0, "Full default, 5yr TB, first offence"),
        (5000, 1500, 5, 0, "Paid 30% exactly (threshold = no freeze)"),
        (5000, 1000, 5, 0, "Paid 20%, 5-year TB"),
        (5000, 1000, 5, 1, "Paid 20%, 5-yr TB, 1 prior default"),
        (5000, 500,  3, 2, "Paid 10%, 3-yr TB, 2 prior defaults"),
    ]
    print(f"  {'Case':<45} {'Repaid':>8} {'Freeze (yr)':>12}")
    print(f"  {'-'*68}")
    for amt, repaid, period, d, desc in cases:
        fr, _ = calculate_freeze_period(amt, repaid, period, d)
        repay_pct = repaid / amt
        print(f"  {desc:<45} {repay_pct:>8.0%} {fr:>12.1f}")

    print("\n  [EQ-TB-4] Pool Sustainability (10-year)")
    print("  ─────────────────────────────────────────────────────────────────")
    result = tb_pool_sustainability(
        pool_size=2000, annual_advances=500, annual_repayments=350,
        automation_tax_in=250, loss_rate=0.05, years_horizon=10
    )
    status = "SOLVENT" if result["solvent"] else f"SHORTFALL at Year {result['shortfall_year']}"
    print(f"  Status: {status}")
    print(f"  Pool trajectory: {[int(v) for v in result['pool_by_year']]}")

    print("\n  [EQ-TB-5] Automation Tax Revenue (15 years)")
    print("  ─────────────────────────────────────────────────────────────────")
    proj = automation_tax_projection(base_automation_output=500, years=15)
    print(f"  {'Year':>5} {'AI Output':>12} {'TB Tax':>10}")
    for yr, out, rev in proj[::3]:  # every 3rd year
        print(f"  {yr:>5} {out:>12,.0f} {rev:>10,.0f}")


def try_plot(history_on, history_off=None):
    """Generate charts if matplotlib is available."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        years = [s.year for s in history_on]

        fig, axes = plt.subplots(3, 3, figsize=(16, 12))
        fig.suptitle("Time-Borrowing Economy Simulation", fontsize=14, fontweight="bold")

        def plot_metric(ax, attr, title, unit="", yscale=1):
            vals_on = [getattr(s, attr) * yscale for s in history_on]
            ax.plot(years, vals_on, "b-", linewidth=2, label="TB Enabled")
            if history_off:
                vals_off = [getattr(s, attr) * yscale for s in history_off]
                ax.plot(years, vals_off, "r--", linewidth=1.5, label="TB Disabled")
                ax.legend(fontsize=8)
            ax.set_title(title, fontsize=10)
            ax.set_xlabel("Year")
            ax.set_ylabel(unit)
            ax.grid(True, alpha=0.3)

        plot_metric(axes[0][0], "resources_produced", "GDP (Resources Produced)", "ACU")
        plot_metric(axes[0][1], "money_supply",        "Money Supply",             "ACU")
        plot_metric(axes[0][2], "inflation",           "Inflation Rate",           "%", 100)
        plot_metric(axes[1][0], "tb_pool_size",        "TB Pool Size",             "ACU")
        plot_metric(axes[1][1], "gini_coefficient",    "Gini Coefficient",         "")
        plot_metric(axes[1][2], "real_interest_rate",  "Real Interest Rate",       "%", 100)
        plot_metric(axes[2][0], "population",          "Population",               "persons")
        plot_metric(axes[2][1], "cumulative_debt",     "Cumulative Government Debt","ACU")
        plot_metric(axes[2][2], "automation_tax_collected","Automation Tax Revenue","ACU")

        plt.tight_layout()
        chart_path = os.path.join(OUTPUT_DIR, "simulation_chart.png")
        plt.savefig(chart_path, dpi=150, bbox_inches="tight")
        print(f"\nChart saved → {chart_path}")
        plt.close()
    except ImportError:
        print("\n[Note] matplotlib not installed — skipping charts.")
        print("  Install with: pip install matplotlib")


def main():
    parser = argparse.ArgumentParser(description="Time-Borrowing Economy Simulator")
    parser.add_argument("--years",    type=int,  default=20,    help="Simulation years")
    parser.add_argument("--people",   type=int,  default=10,    help="Initial population")
    parser.add_argument("--money",    type=float, default=1000, help="Initial money supply")
    parser.add_argument("--no-tb",    action="store_true",      help="Disable TB instrument")
    parser.add_argument("--no-climate", action="store_true",    help="Disable climate shocks")
    parser.add_argument("--compare",  action="store_true",      help="Run TB on vs off comparison")
    parser.add_argument("--show-agents", action="store_true",   help="Show agent table")
    parser.add_argument("--show-relations", action="store_true",help="Show relationship table")
    parser.add_argument("--show-equations", action="store_true",help="Show TB equations")
    args = parser.parse_args()

    print_header()

    if args.show_agents:
        print("\n  AGENT DISTRIBUTION TABLE (OECD-Calibrated)\n")
        print(agent_summary_table())

    if args.show_relations:
        print("\n  RELATIONSHIP CATALOGUE (25 relationships)\n")
        print(relationships_summary())

    if args.show_equations:
        show_tb_equations()

    config = {
        **DEFAULT_CONFIG,
        "years":          args.years,
        "n_people":       args.people,
        "initial_money":  args.money,
        "tb_enabled":     not args.no_tb,
        "climate_shocks": not args.no_climate,
        "random_seed":    42,
    }

    if args.compare:
        compare_scenarios(args.years, args.people)
        # Also produce charts
        cfg_on  = {**config, "tb_enabled": True,  "random_seed": 42}
        cfg_off = {**config, "tb_enabled": False, "random_seed": 42}
        sim_on  = TimeBorrowingEconomy(cfg_on)
        sim_off = TimeBorrowingEconomy(cfg_off)
        h_on    = sim_on.run()
        h_off   = sim_off.run()
        try_plot(h_on, h_off)
    else:
        label = "tb_enabled" if config["tb_enabled"] else "tb_disabled"
        history = run_scenario(config, label)
        try_plot(history)

    # Always show TB equations in default run
    if not (args.show_equations or args.compare):
        show_tb_equations()

    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
    print("Done.\n")


if __name__ == "__main__":
    main()
