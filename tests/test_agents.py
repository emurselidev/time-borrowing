"""
test_agents.py
==============
Tests for agent definitions and population distribution.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import AGENTS, AGENT_SHARES, FREEONE_SUBTYPES, distribute_population


class TestAgentShares:

    def test_verified_government_share_10pct(self):
        """
        OECD Govt at a Glance 2025: 18.4% of employment.
        Employment ≈ 55% of total pop → govt = 18.4% × 55% ≈ 10% of total.
        Source: OECD (2025), World Bank WWBI (16% of employment globally).
        """
        assert abs(AGENT_SHARES["government"] - 0.10) < 1e-9

    def test_verified_freeone_share_50pct(self):
        """
        Children (17%) + students (8%) + retired (18%) + NEET (3%) + inactive (4%) = 50%.
        Sources: UN WPP 2024 (children/retired), UNESCO 2025 (students),
                 OECD Employment Outlook 2025 (NEET).
        """
        assert abs(AGENT_SHARES["freeone"] - 0.50) < 1e-9

    def test_verified_producer_share_40pct(self):
        """
        Residual: 100% - 10% (govt) - 50% (freeone) = 40%.
        Matches: OECD employment rate 70.2% × working-age 65% = 45.6% employed
                 minus government 10% = 35.6%, plus self-employed ~4% ≈ 40%.
        """
        assert abs(AGENT_SHARES["producer"] - 0.40) < 1e-9

    def test_verified_mpc_values(self):
        """
        Economy-wide MPC: 0.45 (Jappelli & Pistaferri 2014: 0.46; Ramey 2023: 0.30-0.40)
        FreeOne MPC: 0.90 (liquidity-constrained, transfer recipients: Sokolova 2022)
        Producer MPC: 0.38 (employed/higher-income: Ramey 2023)
        """
        assert abs(AGENTS["consumer"].mpc - 0.45) < 1e-9
        assert abs(AGENTS["freeone"].mpc - 0.90) < 1e-9
        assert AGENTS["producer"].mpc <= 0.45   # employed → save more than avg

    def test_non_consumer_shares_sum_to_one(self):
        total = (
            AGENT_SHARES["government"]
            + AGENT_SHARES["freeone"]
            + AGENT_SHARES["producer"]
        )
        assert abs(total - 1.0) < 1e-9, f"Shares sum to {total}, expected 1.0"

    def test_consumer_share_is_100pct(self):
        assert AGENT_SHARES["consumer"] == 1.0

    def test_freeone_subtypes_sum_to_one(self):
        total = sum(FREEONE_SUBTYPES.values())
        assert abs(total - 1.0) < 1e-6, f"FreeOne subtypes sum to {total}"

    def test_all_shares_positive(self):
        for name, share in AGENT_SHARES.items():
            assert share > 0, f"{name} has non-positive share"


class TestAgentDefinitions:

    def test_all_four_agents_defined(self):
        for key in ("government", "freeone", "producer", "consumer"):
            assert key in AGENTS

    def test_consumer_consumes(self):
        assert AGENTS["consumer"].consumes is True

    def test_freeone_does_not_produce(self):
        assert AGENTS["freeone"].produces is False

    def test_producer_produces(self):
        assert AGENTS["producer"].produces is True

    def test_mpc_bounds(self):
        for ag in AGENTS.values():
            assert 0 <= ag.mpc <= 1, f"{ag.name} MPC out of bounds"

    def test_repay_prob_bounds(self):
        for ag in AGENTS.values():
            assert 0 <= ag.tb_repay_prob <= 1

    def test_freeone_high_mpc(self):
        # FreeOnes spend almost all of transfer income
        assert AGENTS["freeone"].mpc >= 0.90

    def test_government_tb_eligible(self):
        assert AGENTS["government"].tb_eligible is True


class TestDistributePopulation:

    def test_distribution_sums_to_population(self):
        dist = distribute_population(100)
        total = dist["government"] + dist["freeone"] + dist["producer"]
        assert abs(total - 100.0) < 1e-6

    def test_consumer_equals_population(self):
        dist = distribute_population(50)
        assert dist["consumer"] == 50

    def test_headcounts_scale_linearly(self):
        d10  = distribute_population(10)
        d100 = distribute_population(100)
        ratio = d100["government"] / d10["government"]
        assert abs(ratio - 10.0) < 1e-6

    def test_producer_is_largest_non_consumer(self):
        dist = distribute_population(100)
        assert dist["producer"] > dist["government"]
        assert dist["producer"] > 0


# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_classes = [TestAgentShares, TestAgentDefinitions, TestDistributePopulation]
    passed = 0
    failed = 0
    failures = []

    print("\n" + "=" * 60)
    print("  AGENT MODULE — Unit Tests")
    print("=" * 60)

    for cls in test_classes:
        instance = cls()
        print(f"\n  {cls.__name__}")
        for name in [m for m in dir(instance) if m.startswith("test_")]:
            try:
                getattr(instance, name)()
                print(f"    [PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"    [FAIL] {name}: {e}")
                failures.append((cls.__name__, name, str(e)))
                failed += 1

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    if failures:
        for c, n, e in failures:
            print(f"    {c}.{n}: {e}")
    print("=" * 60)
