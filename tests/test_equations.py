"""
test_equations.py
=================
Individual unit tests for every equation in equation_library.py.

Each equation is tested:
  1. Correct output for known inputs (hand-verified)
  2. Boundary conditions (zeros, extremes)
  3. Direction (monotonicity, signs)
  4. Economic sanity (e.g., higher inflation → lower real rate)

Run with: python tests/test_equations.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equation_library import (
    gdp_expenditure, gdp_growth_rate, real_gdp,
    quantity_theory_inflation, composite_inflation, price_level_update,
    fisher_real_rate, fisher_real_rate_exact, taylor_rule, smooth_rate_adjustment,
    spending_multiplier, tax_multiplier, balanced_budget_multiplier,
    gdp_change_from_spending, gdp_change_from_tax,
    solow_growth_rate, solow_steady_state_capital,
    logistic_growth, exponential_growth,
    okun_unemployment_change, okun_gdp_from_unemployment,
    laffer_revenue, laffer_optimal_rate,
    human_capital_wage_premium, education_productivity_spillover,
    tdrw_severity, tdrw_freeze_years, tdrw_full,
    tb_advance_amount, tb_annual_repayment, tb_pool_next, automation_tax_revenue,
    value_added, markup_price, vat_inclusive_price, effective_income_tax,
)

EPS = 1e-9   # floating point tolerance


# ===========================================================================
# 1. GDP EQUATIONS
# ===========================================================================

class TestGDPExpenditure:
    """Y = C + I + G + (X - M)"""

    def test_basic_formula(self):
        assert gdp_expenditure(700, 200, 150, 100, 80) == 1070.0

    def test_trade_deficit_reduces_gdp(self):
        # M > X → trade deficit → lower GDP than closed economy
        y_closed  = gdp_expenditure(700, 200, 150, 0, 0)
        y_deficit = gdp_expenditure(700, 200, 150, 50, 100)
        assert y_deficit < y_closed

    def test_trade_surplus_increases_gdp(self):
        y_closed   = gdp_expenditure(700, 200, 150, 0, 0)
        y_surplus  = gdp_expenditure(700, 200, 150, 200, 50)
        assert y_surplus > y_closed

    def test_all_zero_is_zero(self):
        assert gdp_expenditure(0, 0, 0, 0, 0) == 0.0

    def test_only_consumption(self):
        assert gdp_expenditure(500, 0, 0, 0, 0) == 500.0


class TestGDPGrowthRate:
    def test_2_5_percent_growth(self):
        assert abs(gdp_growth_rate(1025, 1000) - 0.025) < EPS

    def test_zero_growth(self):
        assert gdp_growth_rate(1000, 1000) == 0.0

    def test_negative_growth(self):
        rate = gdp_growth_rate(900, 1000)
        assert rate < 0

    def test_zero_base_returns_zero(self):
        assert gdp_growth_rate(100, 0) == 0.0

    def test_larger_current_is_positive(self):
        assert gdp_growth_rate(1100, 1000) > 0


class TestRealGDP:
    def test_no_inflation(self):
        assert real_gdp(1000, 1.0) == 1000.0

    def test_with_inflation(self):
        assert abs(real_gdp(1050, 1.05) - 1000.0) < EPS

    def test_zero_deflator_raises(self):
        try:
            real_gdp(1000, 0)
            assert False, "Should raise"
        except ValueError:
            pass

    def test_deflation_increases_real(self):
        # Nominal same, but prices fell → higher real value
        r_base = real_gdp(1000, 1.0)
        r_defl = real_gdp(1000, 0.95)
        assert r_defl > r_base


# ===========================================================================
# 2. MONEY & INFLATION EQUATIONS
# ===========================================================================

class TestQuantityTheoryInflation:
    """π ≈ ΔM/M - ΔY/Y"""

    def test_equal_growth_is_zero_inflation(self):
        # 5% money growth, 5% GDP growth → 0% inflation
        pi = quantity_theory_inflation(50, 1000, 50, 1000)
        assert abs(pi) < EPS

    def test_money_growth_exceeds_gdp_is_positive(self):
        # 5% money growth, 2% GDP growth → ~3% inflation
        pi = quantity_theory_inflation(50, 1000, 20, 1000)
        assert abs(pi - 0.030) < EPS

    def test_gdp_growth_exceeds_money_is_negative(self):
        # 2% money growth, 5% GDP growth → -3% (deflationary)
        pi = quantity_theory_inflation(20, 1000, 50, 1000)
        assert pi < 0

    def test_zero_inputs_return_zero(self):
        assert quantity_theory_inflation(0, 1000, 0, 1000) == 0.0

    def test_velocity_change_adds_to_inflation(self):
        base  = quantity_theory_inflation(50, 1000, 20, 1000)
        added = quantity_theory_inflation(50, 1000, 20, 1000, velocity_change=0.01)
        assert abs(added - (base + 0.01)) < EPS


class TestCompositeInflation:
    def test_all_zero_returns_near_target(self):
        # With zero inputs and 30% CB anchoring toward 2% target:
        # π = 0 * 0.7 + 0.02 * 0.3 = 0.006
        pi = composite_inflation(0, 0, 0, 0, target=0.02, cb_anchoring=0.30)
        assert abs(pi - 0.006) < EPS

    def test_high_monetary_causes_high_inflation(self):
        # 10% monetary inflation signal
        pi_low  = composite_inflation(0.01, 0, 0, 0)
        pi_high = composite_inflation(0.10, 0, 0, 0)
        assert pi_high > pi_low

    def test_supply_shock_adds_directly(self):
        base   = composite_inflation(0.02, 0, 0, 0)
        shocked = composite_inflation(0.02, 0, 0, 0.02)
        assert abs(shocked - base - 0.02 * 0.70) < 1e-6  # shock × (1-anchoring)

    def test_cb_anchoring_pulls_toward_target(self):
        # Extreme inflation but strong CB anchoring → capped near target
        pi_weak_anchor   = composite_inflation(0.10, 0, 0, 0, target=0.02, cb_anchoring=0.01)
        pi_strong_anchor = composite_inflation(0.10, 0, 0, 0, target=0.02, cb_anchoring=0.90)
        assert pi_strong_anchor < pi_weak_anchor


class TestPriceLevelUpdate:
    def test_2pct_inflation(self):
        assert abs(price_level_update(1.0, 0.02) - 1.02) < EPS

    def test_zero_inflation_unchanged(self):
        assert price_level_update(1.0, 0) == 1.0

    def test_deflation_reduces_price_level(self):
        assert price_level_update(1.0, -0.01) < 1.0

    def test_compounding(self):
        P = 1.0
        for _ in range(10):
            P = price_level_update(P, 0.02)
        # 2% for 10 years → 1.02^10 ≈ 1.2190
        assert abs(P - 1.0**1 * (1.02)**10) < 1e-6


# ===========================================================================
# 3. INTEREST RATE EQUATIONS
# ===========================================================================

class TestFisherEquation:
    def test_approximate_formula(self):
        # r = i - π: 4.5% - 2.0% = 2.5%
        assert abs(fisher_real_rate(0.045, 0.02) - 0.025) < EPS

    def test_exact_formula(self):
        r = fisher_real_rate_exact(0.045, 0.02)
        expected = (1.045 / 1.02) - 1
        assert abs(r - expected) < EPS

    def test_high_inflation_lowers_real_rate(self):
        r_low_inf  = fisher_real_rate(0.05, 0.02)
        r_high_inf = fisher_real_rate(0.05, 0.07)
        assert r_high_inf < r_low_inf

    def test_zero_inflation_real_equals_nominal(self):
        assert fisher_real_rate(0.05, 0.0) == 0.05

    def test_exact_raises_on_negative_100pct_inflation(self):
        try:
            fisher_real_rate_exact(0.05, -1.0)
            assert False, "Should raise"
        except ValueError:
            pass


class TestTaylorRule:
    def test_inflation_at_target_output_gap_zero(self):
        # i = π* + r* = 0.02 + 0.02 = 0.04
        assert abs(taylor_rule(0.02, 0.02, 0.02, 0.0) - 0.04) < EPS

    def test_above_target_inflation_raises_rate(self):
        i_target = taylor_rule(0.02, 0.02, 0.02, 0.0)
        i_above  = taylor_rule(0.04, 0.02, 0.02, 0.0)
        assert i_above > i_target

    def test_positive_output_gap_raises_rate(self):
        i_base = taylor_rule(0.02, 0.02, 0.02, 0.0)
        i_boom = taylor_rule(0.02, 0.02, 0.02, 0.05)
        assert i_boom > i_base

    def test_rate_bounded_by_floor(self):
        # Very low inflation → should not go below 0
        i = taylor_rule(-0.10, 0.02, 0.02, -0.10, i_floor=0.0)
        assert i >= 0.0

    def test_rate_bounded_by_ceiling(self):
        # Extreme inflation → should not exceed 20%
        i = taylor_rule(0.50, 0.02, 0.02, 0.10, i_ceiling=0.20)
        assert i <= 0.20

    def test_output_gap_capped_at_10pct(self):
        # Output gap of 200% should be capped at 10%
        i_200pct = taylor_rule(0.02, 0.02, 0.02, 2.0)
        i_10pct  = taylor_rule(0.02, 0.02, 0.02, 0.10)
        assert abs(i_200pct - i_10pct) < EPS


class TestSmoothRateAdjustment:
    def test_full_speed_equals_target(self):
        assert smooth_rate_adjustment(0.03, 0.05, 1.0) == 0.05

    def test_zero_speed_keeps_previous(self):
        assert smooth_rate_adjustment(0.03, 0.05, 0.0) == 0.03

    def test_30pct_speed_partial_move(self):
        # i_new = 0.7*0.03 + 0.3*0.05 = 0.021 + 0.015 = 0.036
        assert abs(smooth_rate_adjustment(0.03, 0.05, 0.30) - 0.036) < EPS


# ===========================================================================
# 4. KEYNESIAN MULTIPLIERS
# ===========================================================================

class TestSpendingMultiplier:
    def test_mpc_45_gives_1_82(self):
        assert abs(spending_multiplier(0.45) - 1.8182) < 1e-4

    def test_mpc_75_gives_4(self):
        assert abs(spending_multiplier(0.75) - 4.0) < EPS

    def test_higher_mpc_higher_multiplier(self):
        assert spending_multiplier(0.60) > spending_multiplier(0.40)

    def test_invalid_mpc_raises(self):
        for bad in (0.0, 1.0, -0.1, 1.5):
            try:
                spending_multiplier(bad)
                assert False, f"Should raise for MPC={bad}"
            except ValueError:
                pass

    def test_balanced_budget_is_one(self):
        # Haavelmo theorem: k_G + k_T = 1 exactly, regardless of MPC
        for mpc in (0.30, 0.45, 0.60, 0.75):
            bb = balanced_budget_multiplier(mpc)
            assert abs(bb - 1.0) < 1e-9, f"BB multiplier failed at MPC={mpc}"


class TestTaxMultiplier:
    def test_mpc_45_gives_minus_0_82(self):
        assert abs(tax_multiplier(0.45) - (-0.8182)) < 1e-4

    def test_always_negative(self):
        for mpc in (0.20, 0.45, 0.60, 0.80):
            assert tax_multiplier(mpc) < 0

    def test_magnitude_less_than_spending(self):
        # |k_T| < k_G always
        for mpc in (0.30, 0.50, 0.70):
            assert abs(tax_multiplier(mpc)) < spending_multiplier(mpc)

    def test_gdp_change_from_spending(self):
        delta_y = gdp_change_from_spending(100, 0.45)
        assert abs(delta_y - 181.82) < 0.01

    def test_gdp_change_from_tax(self):
        delta_y = gdp_change_from_tax(100, 0.45)
        assert abs(delta_y - (-81.82)) < 0.01


# ===========================================================================
# 5. SOLOW GROWTH MODEL
# ===========================================================================

class TestSolowGrowth:
    def test_all_zero_growth_is_zero(self):
        assert solow_growth_rate(0, 0, 0) == 0.0

    def test_only_tfp_growth(self):
        g = solow_growth_rate(0.01, 0, 0)
        assert abs(g - 0.01) < EPS

    def test_full_formula(self):
        # 1% TFP + 33%×2.5% capital + 67%×0.7% labour = 0.02294
        g = solow_growth_rate(0.01, 0.025, 0.007, alpha=0.33)
        assert abs(g - 0.02294) < 1e-5

    def test_alpha_bounds(self):
        for bad in (0.0, 1.0, -0.1):
            try:
                solow_growth_rate(0.01, 0.02, 0.01, alpha=bad)
                assert False
            except ValueError:
                pass

    def test_higher_labour_growth_more_output(self):
        g_low  = solow_growth_rate(0.01, 0.02, 0.005)
        g_high = solow_growth_rate(0.01, 0.02, 0.020)
        assert g_high > g_low

    def test_steady_state_capital_positive(self):
        ss = solow_steady_state_capital(0.20, 0.05, 0.011, 0.01)
        assert ss > 0
        # K/Y ≈ 2.82 — typical range for developed economies
        assert 1.0 < ss < 10.0


# ===========================================================================
# 6. POPULATION GROWTH
# ===========================================================================

class TestLogisticGrowth:
    def test_growth_positive_below_capacity(self):
        P_next = logistic_growth(10, 0.011, 500)
        assert P_next > 10

    def test_near_capacity_per_capita_growth_slows(self):
        # Per-capita growth rate = r × (1 - P/K)
        # At P=10:  rate = 0.011 × (1-10/500) = 0.01078 (fast)
        # At P=400: rate = 0.011 × (1-400/500) = 0.0022 (slow)
        rate_low  = (logistic_growth(10,  0.011, 500) - 10)  / 10
        rate_high = (logistic_growth(400, 0.011, 500) - 400) / 400
        assert rate_low > rate_high   # per-capita growth slows as pop approaches K

    def test_at_capacity_no_growth(self):
        P_next = logistic_growth(500, 0.011, 500)
        assert abs(P_next - 500) < EPS   # exactly at K → 0 growth

    def test_zero_capacity_raises(self):
        try:
            logistic_growth(10, 0.011, 0)
            assert False
        except ValueError:
            pass

    def test_1pct_growth_rate(self):
        # With small P/K ratio, approximately exponential
        P_next = logistic_growth(10, 0.01, 10000)
        assert abs(P_next - 10.1) < 0.001


class TestExponentialGrowth:
    def test_standard_growth(self):
        assert abs(exponential_growth(10, 0.011) - 10.11) < EPS

    def test_zero_rate_unchanged(self):
        assert exponential_growth(100, 0.0) == 100.0


# ===========================================================================
# 7. OKUN'S LAW
# ===========================================================================

class TestOkunsLaw:
    def test_positive_gdp_lowers_unemployment(self):
        assert okun_unemployment_change(0.01) < 0

    def test_negative_gdp_raises_unemployment(self):
        assert okun_unemployment_change(-0.01) > 0

    def test_standard_1pct_growth(self):
        # 1pp GDP growth → -0.5pp unemployment (Okun β = -0.5)
        assert abs(okun_unemployment_change(0.01) - (-0.005)) < EPS

    def test_inverse_roundtrip(self):
        delta_u = okun_unemployment_change(0.02)
        delta_g = okun_gdp_from_unemployment(delta_u)
        assert abs(delta_g - 0.02) < EPS

    def test_zero_gdp_no_unemployment_change(self):
        assert okun_unemployment_change(0.0) == 0.0


# ===========================================================================
# 8. LAFFER CURVE
# ===========================================================================

class TestLafferCurve:
    def test_zero_rate_zero_revenue(self):
        assert laffer_revenue(0.0, 1000) == 0.0

    def test_revenue_positive_at_moderate_rate(self):
        assert laffer_revenue(0.30, 1000) > 0

    def test_optimal_rate_at_epsilon_half(self):
        # τ* = 1/(1+ε) = 1/1.5 = 0.667
        assert abs(laffer_optimal_rate(0.5) - 0.6667) < 1e-4

    def test_revenue_maximised_at_optimal_rate(self):
        optimal = laffer_optimal_rate(0.5)
        rev_opt  = laffer_revenue(optimal, 1000, 0.5)
        rev_low  = laffer_revenue(0.20, 1000, 0.5)
        rev_high = laffer_revenue(0.90, 1000, 0.5)
        assert rev_opt > rev_low
        assert rev_opt > rev_high

    def test_invalid_rate_raises(self):
        for bad in (-0.1, 1.1):
            try:
                laffer_revenue(bad, 1000)
                assert False
            except ValueError:
                pass


# ===========================================================================
# 9. HUMAN CAPITAL
# ===========================================================================

class TestHumanCapital:
    def test_zero_years_no_premium(self):
        assert human_capital_wage_premium(0, 0.10) == 1.0

    def test_10yr_at_10pct(self):
        # (1.10)^10 = 2.5937
        assert abs(human_capital_wage_premium(10, 0.10) - 2.5937) < 1e-4

    def test_premium_increases_with_years(self):
        assert human_capital_wage_premium(5, 0.10) < human_capital_wage_premium(10, 0.10)

    def test_education_spillover(self):
        # 40% educated workforce × 30% spillover = 12% TFP boost
        assert abs(education_productivity_spillover(0.40, 0.30) - 0.12) < EPS

    def test_zero_education_zero_spillover(self):
        assert education_productivity_spillover(0.0, 0.30) == 0.0


# ===========================================================================
# 10. TDRW — TIME-DEBT RECOVERY WINDOW
# ===========================================================================

class TestTDRWSeverity:
    def test_at_threshold_zero_severity(self):
        assert tdrw_severity(0.30, 0.30) == 0.0

    def test_above_threshold_zero_severity(self):
        assert tdrw_severity(0.50, 0.30) == 0.0

    def test_zero_repayment_max_severity(self):
        assert abs(tdrw_severity(0.0, 0.30) - 1.0) < EPS

    def test_20pct_repayment_severity(self):
        # severity = (0.30 - 0.20) / 0.30 = 0.3333
        assert abs(tdrw_severity(0.20, 0.30) - 0.3333) < 1e-4

    def test_severity_increases_as_repayment_decreases(self):
        s_low  = tdrw_severity(0.25, 0.30)
        s_high = tdrw_severity(0.05, 0.30)
        assert s_high > s_low


class TestTDRWFreezeYears:
    def test_zero_severity_no_freeze(self):
        assert tdrw_freeze_years(0.0, 5, 0) == 0.0

    def test_full_default_5yr_first_offence(self):
        # F = 2.0 × 1.0 × 1.0 × (5/3) = 3.33
        f = tdrw_freeze_years(1.0, 5, 0)
        assert abs(f - 3.333) < 1e-3

    def test_repeat_default_increases_freeze(self):
        f0 = tdrw_freeze_years(1.0, 3, 0)   # period=3 avoids cap
        f1 = tdrw_freeze_years(1.0, 3, 1)
        f2 = tdrw_freeze_years(1.0, 3, 2)
        assert f1 > f0
        assert f2 > f1

    def test_capped_at_max(self):
        f = tdrw_freeze_years(1.0, 5, 99)
        assert f <= 7.0

    def test_longer_period_longer_freeze(self):
        f_short = tdrw_freeze_years(1.0, 1, 0)
        f_long  = tdrw_freeze_years(1.0, 5, 0)
        assert f_long > f_short


class TestTDRWFull:
    def test_at_threshold_no_freeze(self):
        p, f, _ = tdrw_full(3000, 900, 5, 0)
        assert abs(p - 0.30) < EPS
        assert f == 0.0

    def test_full_default(self):
        p, f, _ = tdrw_full(3000, 0, 5, 0)
        assert abs(p - 0.0) < EPS
        assert f > 0.0

    def test_zero_advance_is_fine(self):
        p, f, msg = tdrw_full(0, 0, 5, 0)
        assert p == 1.0
        assert f == 0.0

    def test_explanation_string_not_empty(self):
        _, _, expl = tdrw_full(3000, 600, 5, 1)
        assert len(expl) > 0


# ===========================================================================
# 11. TB POOL EQUATIONS
# ===========================================================================

class TestTBAdvanceAmount:
    def test_approved_within_bounds(self):
        a = tb_advance_amount(3000, 20000, 3)
        assert 500 <= a <= 5000

    def test_capped_at_max(self):
        a = tb_advance_amount(99999, 200000, 1)
        assert a <= 5000

    def test_small_pool_returns_zero(self):
        # Pool=300 → deployable=240 → share=240/2=120 < min 500 → 0
        a = tb_advance_amount(3000, 300, 1)
        assert a == 0.0

    def test_zero_request_returns_zero(self):
        assert tb_advance_amount(0, 20000, 3) == 0.0

    def test_many_borrowers_reduces_approval(self):
        a_few  = tb_advance_amount(3000, 20000, 2)
        a_many = tb_advance_amount(3000, 20000, 50)
        assert a_many <= a_few


class TestTBRepayment:
    def test_zero_interest_equal_payments(self):
        payment = tb_annual_repayment(3000, 5, 0.0)
        assert abs(payment - 600.0) < EPS

    def test_positive_rate_increases_payment(self):
        p0 = tb_annual_repayment(3000, 5, 0.00)
        p5 = tb_annual_repayment(3000, 5, 0.05)
        assert p5 > p0

    def test_one_year_equals_amount(self):
        assert tb_annual_repayment(1000, 1, 0.0) == 1000.0

    def test_amortized_5pct(self):
        pmt = tb_annual_repayment(3000, 5, 0.05)
        # PMT = 3000 × 0.05×1.05^5 / (1.05^5 - 1)
        assert abs(pmt - 692.92) < 0.10


class TestTBPoolDynamics:
    def test_healthy_pool_grows(self):
        # Large auto tax, small advances, low loss
        P_next = tb_pool_next(2000, 500, 400, 100, 0.02, 0.10, 1)
        assert P_next > 2000

    def test_excessive_advances_shrinks(self):
        # Very large advances, tiny auto tax
        P_next = tb_pool_next(2000, 50, 100, 5000, 0.10, 0.10, 1)
        assert P_next < 2000

    def test_automation_growth_compounds(self):
        P_yr1 = tb_pool_next(1000, 100, 0, 0, 0, 0.10, 1)
        P_yr5 = tb_pool_next(1000, 100, 0, 0, 0, 0.10, 5)
        assert P_yr5 > P_yr1   # more automation tax at year 5

    def test_loss_rate_reduces_pool(self):
        P_no_loss = tb_pool_next(1000, 100, 200, 300, 0.00)
        P_loss    = tb_pool_next(1000, 100, 200, 300, 0.20)
        assert P_loss < P_no_loss


class TestAutomationTax:
    def test_year_zero_is_base(self):
        rev = automation_tax_revenue(1000, 0.15, 0.10, 0)
        assert abs(rev - 150.0) < EPS

    def test_grows_with_year(self):
        r0 = automation_tax_revenue(1000, 0.15, 0.10, 0)
        r5 = automation_tax_revenue(1000, 0.15, 0.10, 5)
        assert r5 > r0

    def test_higher_tax_rate_more_revenue(self):
        r_low  = automation_tax_revenue(1000, 0.10, 0.10, 5)
        r_high = automation_tax_revenue(1000, 0.25, 0.10, 5)
        assert r_high > r_low


# ===========================================================================
# 12. PRODUCTION CHAIN EQUATIONS
# ===========================================================================

class TestProductionChain:
    def test_value_added(self):
        assert value_added(1000, 650) == 350

    def test_value_added_zero_inputs(self):
        assert value_added(1000, 0) == 1000

    def test_markup_price(self):
        assert markup_price(100, 0.30) == 130.0

    def test_zero_markup_equals_cost(self):
        assert markup_price(100, 0.0) == 100.0

    def test_vat_inclusive_price(self):
        assert abs(vat_inclusive_price(100, 0.192) - 119.2) < EPS

    def test_vat_zero_unchanged(self):
        assert vat_inclusive_price(100, 0.0) == 100.0

    def test_effective_income_tax_net_pay(self):
        # 1000 × (1 - 0.133 - 0.081) = 1000 × 0.786 = 786
        net = effective_income_tax(1000, 0.133, 0.081)
        assert abs(net - 786.0) < EPS

    def test_zero_rates_full_pay(self):
        assert effective_income_tax(1000, 0.0, 0.0) == 1000.0


# ===========================================================================
# RUNNER
# ===========================================================================

if __name__ == "__main__":
    test_classes = [
        TestGDPExpenditure, TestGDPGrowthRate, TestRealGDP,
        TestQuantityTheoryInflation, TestCompositeInflation, TestPriceLevelUpdate,
        TestFisherEquation, TestTaylorRule, TestSmoothRateAdjustment,
        TestSpendingMultiplier, TestTaxMultiplier,
        TestSolowGrowth,
        TestLogisticGrowth, TestExponentialGrowth,
        TestOkunsLaw,
        TestLafferCurve,
        TestHumanCapital,
        TestTDRWSeverity, TestTDRWFreezeYears, TestTDRWFull,
        TestTBAdvanceAmount, TestTBRepayment, TestTBPoolDynamics, TestAutomationTax,
        TestProductionChain,
    ]

    passed = 0
    failed = 0
    failures = []

    print("\n" + "=" * 65)
    print("  EQUATION LIBRARY — Comprehensive Unit Tests")
    print("=" * 65)

    for cls in test_classes:
        instance = cls()
        print(f"\n  {cls.__name__}")
        for name in sorted([m for m in dir(instance) if m.startswith("test_")]):
            try:
                getattr(instance, name)()
                print(f"    [PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"    [FAIL] {name}: {e}")
                failures.append((cls.__name__, name, str(e)))
                failed += 1

    print(f"\n{'='*65}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    if failures:
        print("\n  Failures:")
        for c, n, e in failures:
            print(f"    {c}.{n}: {e}")
    print("=" * 65)
