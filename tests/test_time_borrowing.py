"""
test_time_borrowing.py
======================
Unit tests for the Time Borrowing Instrument equations.
Run with: python -m pytest tests/ -v   (from the static/ directory)
     or:  python tests/test_time_borrowing.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from time_borrowing import (
    calculate_advance_amount,
    repayment_schedule,
    calculate_freeze_period,
    tb_pool_sustainability,
    automation_tax_projection,
    eligibility_check,
    DEFAULT_PARAMS,
)


# ---------------------------------------------------------------------------
# TEST: EQ-TB-0  Eligibility
# ---------------------------------------------------------------------------

class TestEligibility:

    def test_eligible_clean_borrower(self):
        ok, reason = eligibility_check(
            "user_1", is_currently_frozen=False, freeze_until_year=0,
            current_year=5, has_active_loan=False, tb_pool_available=10000
        )
        assert ok, f"Expected eligible, got: {reason}"

    def test_frozen_borrower_blocked(self):
        ok, reason = eligibility_check(
            "user_2", is_currently_frozen=True, freeze_until_year=8,
            current_year=6, has_active_loan=False, tb_pool_available=10000
        )
        assert not ok
        assert "Frozen" in reason

    def test_active_loan_blocks(self):
        ok, reason = eligibility_check(
            "user_3", is_currently_frozen=False, freeze_until_year=0,
            current_year=5, has_active_loan=True, tb_pool_available=10000
        )
        assert not ok
        assert "active" in reason.lower()

    def test_empty_pool_blocks(self):
        ok, reason = eligibility_check(
            "user_4", is_currently_frozen=False, freeze_until_year=0,
            current_year=5, has_active_loan=False, tb_pool_available=200
        )
        assert not ok
        assert "insufficient" in reason.lower() or "Pool" in reason

    def test_freeze_expired_is_eligible(self):
        ok, reason = eligibility_check(
            "user_5", is_currently_frozen=True, freeze_until_year=5,
            current_year=5, has_active_loan=False, tb_pool_available=10000
        )
        # freeze_until_year=5, current_year=5 → NOT strictly less than → eligible
        assert ok, f"Expected eligible after freeze expiry: {reason}"


# ---------------------------------------------------------------------------
# TEST: EQ-TB-1  Advance Amount
# ---------------------------------------------------------------------------

class TestAdvanceAmount:

    def test_capped_at_max(self):
        amount = calculate_advance_amount(
            requested=99999, tb_pool_available=500000,
            n_active_borrowers=1, population=10
        )
        assert amount <= DEFAULT_PARAMS["tb_max_amount"]

    def test_capped_at_pool_share(self):
        # Pool=1000, reserve=20% → deployable=800, 10 borrowers → share=80
        amount = calculate_advance_amount(
            requested=5000, tb_pool_available=1000,
            n_active_borrowers=10, population=10
        )
        assert amount <= 80.0 + 1  # small float tolerance

    def test_below_minimum_returns_zero(self):
        amount = calculate_advance_amount(
            requested=5000, tb_pool_available=100,
            n_active_borrowers=50, population=10
        )
        assert amount == 0.0

    def test_reasonable_amount_approved(self):
        amount = calculate_advance_amount(
            requested=2000, tb_pool_available=50000,
            n_active_borrowers=5, population=10
        )
        assert DEFAULT_PARAMS["tb_min_amount"] <= amount <= DEFAULT_PARAMS["tb_max_amount"]

    def test_zero_requested_returns_zero(self):
        amount = calculate_advance_amount(
            requested=0, tb_pool_available=50000,
            n_active_borrowers=5, population=10
        )
        assert amount == 0.0


# ---------------------------------------------------------------------------
# TEST: EQ-TB-2  Repayment Schedule
# ---------------------------------------------------------------------------

class TestRepaymentSchedule:

    def test_zero_interest_equal_instalments(self):
        schedule = repayment_schedule(3000, 5)
        assert len(schedule) == 5
        for payment in schedule:
            assert abs(payment - 600.0) < 0.01

    def test_sum_equals_principal_at_zero_rate(self):
        amount = 4500
        period = 9
        schedule = repayment_schedule(amount, period)
        assert abs(sum(schedule) - amount) < 0.01

    def test_single_year_repayment(self):
        schedule = repayment_schedule(1000, 1)
        assert len(schedule) == 1
        assert abs(schedule[0] - 1000.0) < 0.01

    def test_positive_rate_increases_total(self):
        params = {**DEFAULT_PARAMS, "tb_interest_rate": 0.05}
        schedule = repayment_schedule(3000, 5, params=params)
        total = sum(schedule)
        assert total > 3000  # positive rate means more than principal repaid

    def test_schedule_all_positive(self):
        schedule = repayment_schedule(2500, 4)
        for p in schedule:
            assert p > 0


# ---------------------------------------------------------------------------
# TEST: EQ-TB-3  Freeze Period (TDRW)
# ---------------------------------------------------------------------------

class TestFreezePeriod:

    def test_full_repayment_no_freeze(self):
        f, _ = calculate_freeze_period(3000, 3000, 5, 0)
        assert f == 0.0

    def test_exactly_threshold_no_freeze(self):
        # p_min = 30%, so 30% repaid = exactly at threshold
        f, _ = calculate_freeze_period(3000, 900, 5, 0)
        assert f == 0.0

    def test_zero_repayment_freeze(self):
        f, _ = calculate_freeze_period(3000, 0, 5, 0)
        assert f > 0.0
        assert f <= DEFAULT_PARAMS["freeze_max_years"]

    def test_freeze_increases_with_default_count(self):
        # Use period=1 to stay below the freeze cap (F_max=7 years)
        # period=1 → time_factor=0.33 → no values hit the 7-yr ceiling
        f0, _ = calculate_freeze_period(3000, 0, 1, 0)
        f1, _ = calculate_freeze_period(3000, 0, 1, 1)
        f2, _ = calculate_freeze_period(3000, 0, 1, 2)
        assert f1 > f0, f"f1={f1} should be > f0={f0}"
        assert f2 > f1, f"f2={f2} should be > f1={f1}"

    def test_freeze_capped_at_max(self):
        f, _ = calculate_freeze_period(3000, 0, 5, 99)  # extreme defaults
        assert f <= DEFAULT_PARAMS["freeze_max_years"]

    def test_partial_repayment_proportional_freeze(self):
        # 10% repaid vs 20% repaid: 10% should freeze longer
        f_10pct, _ = calculate_freeze_period(3000, 300, 5, 0)   # 10%
        f_20pct, _ = calculate_freeze_period(3000, 600, 5, 0)   # 20%
        assert f_10pct > f_20pct

    def test_longer_tb_period_longer_freeze(self):
        f_3yr, _ = calculate_freeze_period(3000, 0, 3, 0)
        f_5yr, _ = calculate_freeze_period(3000, 0, 5, 0)
        assert f_5yr > f_3yr


# ---------------------------------------------------------------------------
# TEST: EQ-TB-4  Pool Sustainability
# ---------------------------------------------------------------------------

class TestPoolSustainability:

    def test_healthy_pool_stays_solvent(self):
        result = tb_pool_sustainability(
            pool_size=5000, annual_advances=300, annual_repayments=250,
            automation_tax_in=200, loss_rate=0.05, years_horizon=10
        )
        assert result["solvent"] is True

    def test_unsustainable_pool_triggers_shortfall(self):
        result = tb_pool_sustainability(
            pool_size=500, annual_advances=1000, annual_repayments=100,
            automation_tax_in=50, loss_rate=0.30, years_horizon=10
        )
        assert result["solvent"] is False
        assert result["shortfall_year"] is not None

    def test_pool_by_year_length(self):
        result = tb_pool_sustainability(
            pool_size=2000, annual_advances=400, annual_repayments=350,
            automation_tax_in=200, loss_rate=0.05, years_horizon=7
        )
        assert len(result["pool_by_year"]) == 8  # year 0 to year 7

    def test_automation_growth_extends_solvency(self):
        # High automation growth should keep pool alive vs low growth
        r_high = tb_pool_sustainability(
            pool_size=1000, annual_advances=500, annual_repayments=200,
            automation_tax_in=200, loss_rate=0.05, years_horizon=15,
            params={**DEFAULT_PARAMS, "automation_growth_rate": 0.20}
        )
        r_low = tb_pool_sustainability(
            pool_size=1000, annual_advances=500, annual_repayments=200,
            automation_tax_in=200, loss_rate=0.05, years_horizon=15,
            params={**DEFAULT_PARAMS, "automation_growth_rate": 0.01}
        )
        # High growth → longer solvency or more solvent
        assert r_high["final_pool"] > r_low["final_pool"]


# ---------------------------------------------------------------------------
# TEST: EQ-TB-5  Automation Tax Projection
# ---------------------------------------------------------------------------

class TestAutomationTaxProjection:

    def test_projection_length(self):
        proj = automation_tax_projection(500, years=10)
        assert len(proj) == 11  # year 0 to 10

    def test_year_zero_is_base(self):
        proj = automation_tax_projection(500, tax_rate=0.15, years=5)
        yr, output, tax = proj[0]
        assert yr == 0
        assert abs(output - 500.0) < 0.01
        assert abs(tax - 75.0) < 0.01

    def test_monotonically_increasing(self):
        proj = automation_tax_projection(500, growth_rate=0.10, years=10)
        outputs = [p[1] for p in proj]
        for i in range(1, len(outputs)):
            assert outputs[i] > outputs[i-1]

    def test_tax_rate_applied_correctly(self):
        proj = automation_tax_projection(1000, tax_rate=0.20, growth_rate=0.0, years=3)
        for yr, output, tax in proj:
            assert abs(tax - output * 0.20) < 0.01


# ---------------------------------------------------------------------------
# INTEGRATION: end-to-end sanity check
# ---------------------------------------------------------------------------

def test_end_to_end_scenario():
    """
    Simulate a borrower lifecycle:
      Year 0: receives 3000 ACU advance for 5 years
      Year 5: repaid only 900 (30% = exactly threshold)
      → Expected: no freeze
    """
    advance = calculate_advance_amount(3000, 20000, 2, 10)
    assert advance > 0, "Should approve advance"

    schedule = repayment_schedule(advance, 5)
    total_due = sum(schedule)
    paid = total_due * 0.30  # paid exactly 30%

    freeze, explanation = calculate_freeze_period(advance, paid, 5, 0)
    assert freeze == 0.0, f"Expected no freeze at 30% repayment; got {freeze}"

    # Now test below threshold
    paid_low = total_due * 0.20
    freeze_low, _ = calculate_freeze_period(advance, paid_low, 5, 0)
    assert freeze_low > 0.0, "Expected freeze for 20% repayment"


# ---------------------------------------------------------------------------
# RUNNER
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    test_classes = [
        TestEligibility,
        TestAdvanceAmount,
        TestRepaymentSchedule,
        TestFreezePeriod,
        TestPoolSustainability,
        TestAutomationTaxProjection,
    ]

    passed = 0
    failed = 0
    errors = []

    print("\n" + "=" * 60)
    print("  TIME BORROWING INSTRUMENT — Unit Tests")
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
                errors.append((cls.__name__, name, str(e)))
                failed += 1

    print(f"\n  Running integration test...")
    try:
        test_end_to_end_scenario()
        print("    [PASS] test_end_to_end_scenario")
        passed += 1
    except Exception as e:
        print(f"    [FAIL] test_end_to_end_scenario: {e}")
        failed += 1

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    if errors:
        print("\n  Failures:")
        for cls_name, test_name, err in errors:
            print(f"    {cls_name}.{test_name}: {err}")
    print("=" * 60)
