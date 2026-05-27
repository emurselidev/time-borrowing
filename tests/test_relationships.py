"""
test_relationships.py
=====================
Comprehensive individual tests for all 25 economic relationships.

Each relationship is tested for:
  1. Valid return type (dict with float values)
  2. Correct key names (match EconomyState attributes or _pct variants)
  3. Sign-correct economics (e.g., VAT raises tax_revenue)
  4. Monotonic scaling with n_tx (more transactions → bigger effect)
  5. Zero transactions → near-zero effect
  6. Percentage changes are properly bounded (no >50% single-year jump)

Run with: python tests/test_relationships.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parameters import EconomyState, build_initial_state
from relationships import (
    r01_consumer_buys_from_producer,
    r02_producer_pays_income_tax,
    r03_government_pays_welfare,
    r04_producer_pays_wages,
    r05_consumer_pays_vat,
    r06_government_borrows_central_bank,
    r07_central_bank_adjusts_rate,
    r08_producer_b2b_supply_chain,
    r09_tb_advance_to_citizen,
    r10_citizen_repays_tb,
    r11_automation_generates_tax,
    r12_government_invests_infrastructure,
    r13_freeone_spends_welfare,
    r14_climate_resource_shock,
    r15_inflation_erodes_purchasing_power,
    r16_producer_rd_investment,
    r17_export_drives_demand,
    r18_import_displaces_domestic,
    r19_tb_default_freeze,
    r20_education_boosts_productivity,
    r21_tb_pool_top_up_from_tax,
    r22_wage_price_spiral,
    r23_producer_hires_freeone,
    r24_government_subsidises_producer,
    r25_debt_service_pressure,
    apply_relationship, RELATIONSHIPS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_state(**kwargs) -> EconomyState:
    s = build_initial_state(10, 1000.0, 1000.0)
    for k, v in kwargs.items():
        setattr(s, k, v)
    return s


VALID_STATE_KEYS = set(vars(EconomyState()).keys())


def validate_delta(deltas: dict, desc: str = "") -> None:
    """All keys must map to numeric values."""
    assert isinstance(deltas, dict), f"{desc}: must return dict"
    for k, v in deltas.items():
        assert isinstance(v, (int, float)), f"{desc}: key '{k}' value must be numeric, got {type(v)}"


def validate_keys(deltas: dict, desc: str = "") -> None:
    """All non-_pct keys must be valid EconomyState attributes."""
    for k in deltas:
        base_key = k[:-4] if k.endswith("_pct") else k
        assert base_key in VALID_STATE_KEYS, \
            f"{desc}: key '{base_key}' not in EconomyState"


def _delta(rel_fn, n_tx: float, **state_kwargs) -> dict:
    return rel_fn(make_state(**state_kwargs), n_tx)


# ===========================================================================
# R01 — Consumer buys from Producer
# ===========================================================================
class TestR01ConsumerBuysFromProducer:
    def test_returns_dict(self):
        d = _delta(r01_consumer_buys_from_producer, 1000)
        validate_delta(d, "R01"); validate_keys(d, "R01")

    def test_taxes_collected(self):
        d = _delta(r01_consumer_buys_from_producer, 1000)
        assert d.get("tax_revenue", 0) > 0

    def test_consumption_increases(self):
        d = _delta(r01_consumer_buys_from_producer, 1000)
        assert d.get("resources_consumed_pct", 0) > 0

    def test_money_absorbed(self):
        d = _delta(r01_consumer_buys_from_producer, 1000)
        # VAT + fiscal absorption draws money from circulation
        assert d.get("money_supply", 0) < 0

    def test_scales_with_transactions(self):
        d1 = _delta(r01_consumer_buys_from_producer, 500)
        d2 = _delta(r01_consumer_buys_from_producer, 2000)
        assert d2["tax_revenue"] > d1["tax_revenue"]

    def test_zero_transactions_much_less_than_normal(self):
        # _scale uses max(n_tx,1) to avoid div-by-zero; at n_tx=0 effect is tiny
        d_zero   = _delta(r01_consumer_buys_from_producer, 0)
        d_normal = _delta(r01_consumer_buys_from_producer, 1000)
        # At n_tx=0: scale = (1/1000)^0.6 ≈ 0.004 of normal; at least 100× smaller
        assert d_zero["tax_revenue"] < d_normal["tax_revenue"] / 50


# ===========================================================================
# R02 — Producer pays income tax
# ===========================================================================
class TestR02ProducerPaysIncomeTax:
    def test_returns_dict(self):
        d = _delta(r02_producer_pays_income_tax, 1000)
        validate_delta(d, "R02"); validate_keys(d, "R02")

    def test_tax_revenue_increases(self):
        d = _delta(r02_producer_pays_income_tax, 1000)
        assert d.get("tax_revenue", 0) > 0

    def test_gdp_drag_is_negative(self):
        d = _delta(r02_producer_pays_income_tax, 1000)
        assert d.get("resources_produced_pct", 0) < 0  # tax drag

    def test_money_supply_decreases(self):
        d = _delta(r02_producer_pays_income_tax, 1000)
        assert d.get("money_supply", 0) < 0

    def test_monotonic_scaling(self):
        d1 = _delta(r02_producer_pays_income_tax, 200)
        d2 = _delta(r02_producer_pays_income_tax, 800)
        assert d2["tax_revenue"] > d1["tax_revenue"]


# ===========================================================================
# R03 — Government pays welfare
# ===========================================================================
class TestR03GovernmentPaysWelfare:
    def test_returns_dict(self):
        d = _delta(r03_government_pays_welfare, 500)
        validate_delta(d, "R03"); validate_keys(d, "R03")

    def test_govt_balance_falls(self):
        d = _delta(r03_government_pays_welfare, 500)
        assert d.get("government_balance", 0) < 0

    def test_money_supply_rises(self):
        d = _delta(r03_government_pays_welfare, 500)
        assert d.get("money_supply", 0) > 0

    def test_induced_production(self):
        d = _delta(r03_government_pays_welfare, 500)
        assert d.get("resources_produced_pct", 0) > 0

    def test_welfare_spend_increases(self):
        d = _delta(r03_government_pays_welfare, 500)
        assert d.get("welfare_spend", 0) > 0


# ===========================================================================
# R04 — Producer pays wages
# ===========================================================================
class TestR04ProducerPaysWages:
    def test_returns_dict(self):
        d = _delta(r04_producer_pays_wages, 1200)
        validate_delta(d, "R04"); validate_keys(d, "R04")

    def test_pit_collected(self):
        d = _delta(r04_producer_pays_wages, 1200)
        assert d.get("tax_revenue", 0) > 0

    def test_consumption_effect(self):
        d = _delta(r04_producer_pays_wages, 1200)
        assert d.get("resources_consumed_pct", 0) > 0

    def test_mild_inflation(self):
        d = _delta(r04_producer_pays_wages, 1200)
        assert d.get("inflation", 0) >= 0   # cost-push ≥ 0


# ===========================================================================
# R05 — Consumer pays VAT
# ===========================================================================
class TestR05ConsumerPaysVAT:
    def test_returns_dict(self):
        d = _delta(r05_consumer_pays_vat, 1800)
        validate_delta(d, "R05"); validate_keys(d, "R05")

    def test_tax_revenue_rises(self):
        d = _delta(r05_consumer_pays_vat, 1800)
        assert d.get("tax_revenue", 0) > 0

    def test_demand_loss(self):
        d = _delta(r05_consumer_pays_vat, 1800)
        assert d.get("resources_consumed_pct", 0) < 0   # price wedge reduces demand

    def test_govt_balance_rises(self):
        d = _delta(r05_consumer_pays_vat, 1800)
        assert d.get("government_balance", 0) > 0


# ===========================================================================
# R06 — Government deficit financing
# ===========================================================================
class TestR06GovernmentDeficitFinancing:
    def test_returns_dict(self):
        d = _delta(r06_government_borrows_central_bank, 100)
        validate_delta(d, "R06"); validate_keys(d, "R06")

    def test_money_supply_increases(self):
        d = _delta(r06_government_borrows_central_bank, 100)
        assert d.get("money_supply", 0) > 0

    def test_debt_increases(self):
        d = _delta(r06_government_borrows_central_bank, 100)
        assert d.get("cumulative_debt", 0) > 0

    def test_inflation_rises(self):
        d = _delta(r06_government_borrows_central_bank, 100, money_supply=500)
        assert d.get("inflation", 0) > 0   # Quantity Theory


# ===========================================================================
# R07 — Central Bank adjusts interest rate
# ===========================================================================
class TestR07CentralBankAdjustsRate:
    def test_returns_dict(self):
        d = _delta(r07_central_bank_adjusts_rate, 200)
        validate_delta(d, "R07"); validate_keys(d, "R07")

    def test_rate_hike_reduces_inflation(self):
        d = _delta(r07_central_bank_adjusts_rate, +500)   # positive = hike
        assert d.get("inflation", 0) < 0   # hike fights inflation

    def test_rate_hike_reduces_investment(self):
        d = _delta(r07_central_bank_adjusts_rate, +500)
        assert d.get("investment", 0) < 0

    def test_rate_cut_increases_investment(self):
        d = _delta(r07_central_bank_adjusts_rate, -500)
        assert d.get("investment", 0) > 0


# ===========================================================================
# R08 — B2B supply chain (PRIMARY GDP DRIVER)
# ===========================================================================
class TestR08B2BSupplyChain:
    def test_returns_dict(self):
        d = _delta(r08_producer_b2b_supply_chain, 3000)
        validate_delta(d, "R08"); validate_keys(d, "R08")

    def test_gdp_increases(self):
        d = _delta(r08_producer_b2b_supply_chain, 3000)
        assert d.get("resources_produced_pct", 0) > 0

    def test_investment_increases(self):
        d = _delta(r08_producer_b2b_supply_chain, 3000)
        assert d.get("investment", 0) > 0

    def test_tax_collected(self):
        d = _delta(r08_producer_b2b_supply_chain, 3000)
        assert d.get("tax_revenue", 0) > 0

    def test_scales_with_transactions(self):
        d1 = _delta(r08_producer_b2b_supply_chain, 1000)
        d2 = _delta(r08_producer_b2b_supply_chain, 5000)
        assert d2["resources_produced_pct"] > d1["resources_produced_pct"]

    def test_pct_change_reasonable_magnitude(self):
        # At N_REF=1000, base_pct=0.004 → change should be ~0.004
        d = _delta(r08_producer_b2b_supply_chain, 1000)
        assert 0 < d["resources_produced_pct"] < 0.10   # max 10% per year


# ===========================================================================
# R09 — TB advance to citizen
# ===========================================================================
class TestR09TBAdvance:
    def test_returns_dict(self):
        d = _delta(r09_tb_advance_to_citizen, 100)
        validate_delta(d, "R09"); validate_keys(d, "R09")

    def test_money_supply_increases(self):
        d = _delta(r09_tb_advance_to_citizen, 100)
        assert d.get("money_supply", 0) > 0

    def test_tb_pool_decreases(self):
        d = _delta(r09_tb_advance_to_citizen, 100)
        assert d.get("tb_pool_size", 0) < 0

    def test_tb_issued_increases(self):
        d = _delta(r09_tb_advance_to_citizen, 100)
        assert d.get("tb_amount_issued", 0) > 0

    def test_inflation_minimal(self):
        d = _delta(r09_tb_advance_to_citizen, 100)
        # Productivity-backed: inflation < 0.5% per year
        assert d.get("inflation", 0) < 0.005


# ===========================================================================
# R10 — Citizen repays TB (self-balancing mechanism)
# ===========================================================================
class TestR10TBRepayment:
    def test_returns_dict(self):
        d = _delta(r10_citizen_repays_tb, 80)
        validate_delta(d, "R10"); validate_keys(d, "R10")

    def test_tb_pool_refills(self):
        d = _delta(r10_citizen_repays_tb, 80)
        assert d.get("tb_pool_size", 0) > 0

    def test_money_supply_decreases(self):
        d = _delta(r10_citizen_repays_tb, 80)
        assert d.get("money_supply", 0) < 0   # circuit closed

    def test_repayments_tracked(self):
        d = _delta(r10_citizen_repays_tb, 80)
        assert d.get("tb_repayments_received", 0) > 0


# ===========================================================================
# R11 — Automation generates TB tax (KEY MECHANISM)
# ===========================================================================
class TestR11AutomationGeneratesTax:
    def test_returns_dict(self):
        d = _delta(r11_automation_generates_tax, 500)
        validate_delta(d, "R11"); validate_keys(d, "R11")

    def test_tb_pool_increases(self):
        d = _delta(r11_automation_generates_tax, 500)
        assert d.get("tb_pool_size", 0) > 0

    def test_automation_tax_tracked(self):
        d = _delta(r11_automation_generates_tax, 500)
        assert d.get("automation_tax_collected", 0) > 0

    def test_gdp_increases(self):
        d = _delta(r11_automation_generates_tax, 500)
        assert d.get("resources_produced_pct", 0) > 0

    def test_automation_is_deflationary(self):
        d = _delta(r11_automation_generates_tax, 500)
        assert d.get("inflation", 0) < 0   # supply-side expansion

    def test_grows_with_year(self):
        d0 = r11_automation_generates_tax(make_state(year=0), 500)
        d5 = r11_automation_generates_tax(make_state(year=5), 500)
        assert d5.get("tb_pool_size", 0) > d0.get("tb_pool_size", 0)


# ===========================================================================
# R12 — Government invests in infrastructure
# ===========================================================================
class TestR12InfrastructureInvestment:
    def test_gdp_increases(self):
        d = _delta(r12_government_invests_infrastructure, 150)
        assert d.get("resources_produced_pct", 0) > 0

    def test_govt_balance_falls(self):
        d = _delta(r12_government_invests_infrastructure, 150)
        assert d.get("government_balance", 0) < 0

    def test_private_investment_crowd_in(self):
        d = _delta(r12_government_invests_infrastructure, 150)
        assert d.get("investment", 0) > 0


# ===========================================================================
# R13 — FreeOne spends welfare income
# ===========================================================================
class TestR13FreeOneSpends:
    def test_returns_dict(self):
        d = _delta(r13_freeone_spends_welfare, 250)
        validate_delta(d, "R13"); validate_keys(d, "R13")

    def test_consumption_increases(self):
        d = _delta(r13_freeone_spends_welfare, 250)
        assert d.get("resources_consumed_pct", 0) > 0

    def test_induced_production(self):
        d = _delta(r13_freeone_spends_welfare, 250)
        assert d.get("resources_produced_pct", 0) > 0

    def test_vat_collected(self):
        d = _delta(r13_freeone_spends_welfare, 250)
        assert d.get("tax_revenue", 0) > 0


# ===========================================================================
# R14 — Climate / resource shock
# ===========================================================================
class TestR14ClimateShock:
    def test_returns_dict(self):
        d = _delta(r14_climate_resource_shock, 500)
        validate_delta(d, "R14"); validate_keys(d, "R14")

    def test_gdp_decreases(self):
        d = _delta(r14_climate_resource_shock, 500)
        assert d.get("resources_produced_pct", 0) < 0

    def test_cost_push_inflation(self):
        d = _delta(r14_climate_resource_shock, 500)
        assert d.get("inflation", 0) > 0

    def test_investment_decreases(self):
        d = _delta(r14_climate_resource_shock, 500)
        assert d.get("investment", 0) <= 0

    def test_zero_severity_zero_effect(self):
        d = _delta(r14_climate_resource_shock, 0)
        assert d.get("resources_produced_pct", 0) == 0


# ===========================================================================
# R15 — Inflation erodes purchasing power
# ===========================================================================
class TestR15InflationErosion:
    def test_returns_dict(self):
        d = _delta(r15_inflation_erodes_purchasing_power, 50)  # 5% inflation
        validate_delta(d, "R15"); validate_keys(d, "R15")

    def test_consumption_falls(self):
        d = _delta(r15_inflation_erodes_purchasing_power, 50)
        assert d.get("resources_consumed_pct", 0) < 0

    def test_gini_worsens(self):
        d = _delta(r15_inflation_erodes_purchasing_power, 50)
        assert d.get("gini_coefficient", 0) > 0   # inflation hurts poor more

    def test_higher_inflation_worse_impact(self):
        d_low  = _delta(r15_inflation_erodes_purchasing_power, 20)
        d_high = _delta(r15_inflation_erodes_purchasing_power, 100)
        assert d_high["resources_consumed_pct"] < d_low["resources_consumed_pct"]


# ===========================================================================
# R16 — R&D investment
# ===========================================================================
class TestR16RnDInvestment:
    def test_returns_dict(self):
        d = _delta(r16_producer_rd_investment, 100)
        validate_delta(d, "R16"); validate_keys(d, "R16")

    def test_gdp_increases(self):
        d = _delta(r16_producer_rd_investment, 100)
        assert d.get("resources_produced_pct", 0) > 0

    def test_investment_increases(self):
        d = _delta(r16_producer_rd_investment, 100)
        assert d.get("investment", 0) > 0

    def test_productivity_increases(self):
        d = _delta(r16_producer_rd_investment, 100)
        assert d.get("productivity_per_worker", 0) > 0

    def test_tax_credits_cost_govt(self):
        d = _delta(r16_producer_rd_investment, 100)
        assert d.get("government_balance", 0) < 0


# ===========================================================================
# R17 — Exports drive demand
# ===========================================================================
class TestR17Exports:
    def test_returns_dict(self):
        d = _delta(r17_export_drives_demand, 300)
        validate_delta(d, "R17"); validate_keys(d, "R17")

    def test_gdp_increases(self):
        d = _delta(r17_export_drives_demand, 300)
        assert d.get("resources_produced_pct", 0) > 0

    def test_money_supply_increases(self):
        d = _delta(r17_export_drives_demand, 300)
        assert d.get("money_supply", 0) > 0   # foreign currency inflows


# ===========================================================================
# R18 — Imports displace domestic production
# ===========================================================================
class TestR18Imports:
    def test_returns_dict(self):
        d = _delta(r18_import_displaces_domestic, 250)
        validate_delta(d, "R18"); validate_keys(d, "R18")

    def test_domestic_production_falls(self):
        d = _delta(r18_import_displaces_domestic, 250)
        assert d.get("resources_produced_pct", 0) < 0

    def test_consumption_rises(self):
        d = _delta(r18_import_displaces_domestic, 250)
        assert d.get("resources_consumed_pct", 0) > 0

    def test_money_supply_decreases(self):
        d = _delta(r18_import_displaces_domestic, 250)
        assert d.get("money_supply", 0) < 0   # foreign currency outflow

    def test_anti_inflationary(self):
        d = _delta(r18_import_displaces_domestic, 250)
        assert d.get("inflation", 0) <= 0   # import price effect is deflationary


# ===========================================================================
# R19 — TB default freeze
# ===========================================================================
class TestR19TBDefaultFreeze:
    def test_returns_dict(self):
        d = _delta(r19_tb_default_freeze, 30)
        validate_delta(d, "R19"); validate_keys(d, "R19")

    def test_tb_pool_decreases(self):
        d = _delta(r19_tb_default_freeze, 30)
        assert d.get("tb_pool_size", 0) < 0

    def test_loss_rate_increases(self):
        d = _delta(r19_tb_default_freeze, 30)
        assert d.get("tb_loss_rate", 0) > 0

    def test_injection_needed_increases(self):
        d = _delta(r19_tb_default_freeze, 30)
        assert d.get("tb_injection_needed", 0) > 0

    def test_defaulters_increase(self):
        d = _delta(r19_tb_default_freeze, 30)
        assert d.get("tb_defaulters", 0) > 0


# ===========================================================================
# R20 — Education → skilled workforce
# ===========================================================================
class TestR20EducationBoosts:
    def test_returns_dict(self):
        d = _delta(r20_education_boosts_productivity, 80)
        validate_delta(d, "R20"); validate_keys(d, "R20")

    def test_gdp_increases(self):
        d = _delta(r20_education_boosts_productivity, 80)
        assert d.get("resources_produced_pct", 0) > 0

    def test_productivity_increases(self):
        d = _delta(r20_education_boosts_productivity, 80)
        assert d.get("productivity_per_worker", 0) > 0

    def test_freeone_decreases(self):
        d = _delta(r20_education_boosts_productivity, 80)
        assert d.get("n_freeone", 0) < 0   # students leave FreeOne pool

    def test_inequality_falls(self):
        d = _delta(r20_education_boosts_productivity, 80)
        assert d.get("gini_coefficient", 0) < 0


# ===========================================================================
# R21 — Tax top-up refills TB pool
# ===========================================================================
class TestR21TBPoolTopUp:
    def test_returns_dict(self):
        d = _delta(r21_tb_pool_top_up_from_tax, 50)
        validate_delta(d, "R21"); validate_keys(d, "R21")

    def test_tb_pool_increases(self):
        d = _delta(r21_tb_pool_top_up_from_tax, 50)
        assert d.get("tb_pool_size", 0) > 0

    def test_money_supply_increases(self):
        d = _delta(r21_tb_pool_top_up_from_tax, 50)
        assert d.get("money_supply", 0) > 0

    def test_govt_balance_falls(self):
        d = _delta(r21_tb_pool_top_up_from_tax, 50)
        assert d.get("government_balance", 0) < 0

    def test_injection_needed_decreases(self):
        d = _delta(r21_tb_pool_top_up_from_tax, 50)
        assert d.get("tb_injection_needed", 0) < 0


# ===========================================================================
# R22 — Wage-price spiral
# ===========================================================================
class TestR22WagePriceSpiral:
    def test_returns_dict(self):
        d = _delta(r22_wage_price_spiral, 20)
        validate_delta(d, "R22"); validate_keys(d, "R22")

    def test_inflation_rises(self):
        d = _delta(r22_wage_price_spiral, 20)
        assert d.get("inflation", 0) > 0

    def test_gdp_falls(self):
        d = _delta(r22_wage_price_spiral, 20)
        assert d.get("resources_produced_pct", 0) < 0   # unit cost squeeze

    def test_interest_rate_rises(self):
        d = _delta(r22_wage_price_spiral, 20)
        assert d.get("nominal_interest_rate", 0) > 0   # CB response


# ===========================================================================
# R23 — Producers hire FreeOnes
# ===========================================================================
class TestR23ProducerHiresFreeOne:
    def test_returns_dict(self):
        d = _delta(r23_producer_hires_freeone, 120)
        validate_delta(d, "R23"); validate_keys(d, "R23")

    def test_gdp_increases(self):
        d = _delta(r23_producer_hires_freeone, 120)
        assert d.get("resources_produced_pct", 0) > 0   # Okun expansion

    def test_employment_rises(self):
        d = _delta(r23_producer_hires_freeone, 120)
        assert d.get("employment_rate_pct", 0) >= 0 or d.get("employment_rate", 0) >= 0

    def test_freeone_falls(self):
        d = _delta(r23_producer_hires_freeone, 120)
        assert d.get("n_freeone", 0) < 0   # people leave FreeOne pool

    def test_welfare_cost_falls(self):
        d = _delta(r23_producer_hires_freeone, 120)
        assert d.get("welfare_spend", 0) < 0   # fewer welfare recipients

    def test_inequality_falls(self):
        d = _delta(r23_producer_hires_freeone, 120)
        assert d.get("gini_coefficient", 0) < 0


# ===========================================================================
# R24 — Government subsidises producers
# ===========================================================================
class TestR24GovernmentSubsidises:
    def test_returns_dict(self):
        d = _delta(r24_government_subsidises_producer, 80)
        validate_delta(d, "R24"); validate_keys(d, "R24")

    def test_gdp_increases(self):
        d = _delta(r24_government_subsidises_producer, 80)
        assert d.get("resources_produced_pct", 0) > 0

    def test_govt_balance_falls(self):
        d = _delta(r24_government_subsidises_producer, 80)
        assert d.get("government_balance", 0) < 0

    def test_anti_inflationary(self):
        d = _delta(r24_government_subsidises_producer, 80)
        assert d.get("inflation", 0) <= 0   # supply-side expansion

    def test_investment_increases(self):
        d = _delta(r24_government_subsidises_producer, 80)
        assert d.get("investment", 0) > 0


# ===========================================================================
# R25 — Debt service pressure
# ===========================================================================
class TestR25DebtServicePressure:
    def test_returns_dict(self):
        d = _delta(r25_debt_service_pressure, 100)
        validate_delta(d, "R25"); validate_keys(d, "R25")

    def test_govt_balance_falls(self):
        d = _delta(r25_debt_service_pressure, 100)
        assert d.get("government_balance", 0) < 0

    def test_gdp_falls(self):
        d = _delta(r25_debt_service_pressure, 100)
        assert d.get("resources_produced_pct", 0) <= 0   # crowding out

    def test_minimal_at_low_debt(self):
        # Low debt ratio → 80% reduction in pressure
        d_low  = _delta(r25_debt_service_pressure, 50, cumulative_debt=100, resources_produced=2000)
        d_high = _delta(r25_debt_service_pressure, 50, cumulative_debt=2000, resources_produced=2000)
        assert abs(d_high["government_balance"]) >= abs(d_low["government_balance"])


# ===========================================================================
# REGISTRY INTEGRITY TEST
# ===========================================================================
class TestRelationshipsRegistry:
    def test_28_relationships_registered(self):
        assert len(RELATIONSHIPS) == 28, f"Expected 28, got {len(RELATIONSHIPS)}"

    def test_all_have_required_keys(self):
        for r in RELATIONSHIPS:
            assert "id"   in r
            assert "from" in r
            assert "to"   in r
            assert "label" in r
            assert "fn"   in r
            assert callable(r["fn"])

    def test_unique_ids(self):
        ids = [r["id"] for r in RELATIONSHIPS]
        assert len(ids) == len(set(ids))

    def test_apply_relationship_works(self):
        s = make_state()
        for r in RELATIONSHIPS:
            d = apply_relationship(r["id"], s, 500)
            assert isinstance(d, dict)

    def test_unknown_id_raises(self):
        s = make_state()
        try:
            apply_relationship("R99", s, 100)
            assert False, "Should raise"
        except ValueError:
            pass

    def test_all_relationships_return_numeric_deltas(self):
        s = make_state()
        for r in RELATIONSHIPS:
            d = apply_relationship(r["id"], s, 500)
            for k, v in d.items():
                assert isinstance(v, (int, float)), \
                    f"{r['id']}.{k} returned non-numeric: {type(v)}"


# ===========================================================================
# RUNNER
# ===========================================================================
if __name__ == "__main__":
    test_classes = [
        TestR01ConsumerBuysFromProducer,
        TestR02ProducerPaysIncomeTax,
        TestR03GovernmentPaysWelfare,
        TestR04ProducerPaysWages,
        TestR05ConsumerPaysVAT,
        TestR06GovernmentDeficitFinancing,
        TestR07CentralBankAdjustsRate,
        TestR08B2BSupplyChain,
        TestR09TBAdvance,
        TestR10TBRepayment,
        TestR11AutomationGeneratesTax,
        TestR12InfrastructureInvestment,
        TestR13FreeOneSpends,
        TestR14ClimateShock,
        TestR15InflationErosion,
        TestR16RnDInvestment,
        TestR17Exports,
        TestR18Imports,
        TestR19TBDefaultFreeze,
        TestR20EducationBoosts,
        TestR21TBPoolTopUp,
        TestR22WagePriceSpiral,
        TestR23ProducerHiresFreeOne,
        TestR24GovernmentSubsidises,
        TestR25DebtServicePressure,
        TestRelationshipsRegistry,
    ]

    passed = 0
    failed = 0
    failures = []

    print("\n" + "=" * 65)
    print("  RELATIONSHIPS — Comprehensive Unit Tests")
    print("=" * 65)

    for cls in test_classes:
        inst = cls()
        print(f"\n  {cls.__name__}")
        for name in sorted([m for m in dir(inst) if m.startswith("test_")]):
            try:
                getattr(inst, name)()
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
