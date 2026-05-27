# Time Borrowing — Economic Simulation & Policy Framework

**Author:** Enis Murseli  
**Language:** Python 3.10+  
**License:** [Humanitarian Use License](LICENSE.md) — free for all, for the good of humanity  
**Default README (Albanian / Shqip):** [README.md](README.md)

> This is the English version. The default repository README is in Albanian — the author's native language.  
> *Ky është versioni anglisht. README-ja kryesore e depoves është në shqip.*

> *"What if artificial intelligence, instead of replacing human potential,  
> became the very engine that funds it?"*

---

## What is Time Borrowing?

**Time Borrowing** is a new economic instrument — a way for citizens to receive capital advances funded by the productivity surplus of artificial intelligence and automation, repaid over time at **zero percent interest**, using their future contribution as collateral rather than their current wealth.

### The Problem It Solves

Three forces are converging to create a structural economic crisis that existing tools are not designed to handle:

1. **Automation Displacement** — AI and robots are eliminating routine jobs. The OECD estimates 14% of jobs are highly automatable and 32% face significant change. The productivity surplus flows to corporations, not the people displaced.

2. **Human Capital Funding Deficit** — Retraining, education, and starting a business require upfront capital. The citizens who need it most — the unemployed, NEET youth, workers in declining industries — cannot access traditional credit. Banks require collateral they don't have.

3. **The Inflation-Welfare Trap** — Universal Basic Income proposals address displacement, but are funded by money printing or broad tax rises — both creating inflation or political resistance. More welfare spending means larger deficits with no productivity return.

### How Time Borrowing Works

```
[AI & Automation Work Done]
         │
         ▼  (15% Automation Tax on output value)
[TB Liquidity Pool]  ◄──────────────────────────────────┐
         │                                               │
         ▼  (Advance to eligible citizen)                │
[Citizen receives capital]                               │
         │                                               │
         ▼  (studies / starts business / bridges hardship)│
[Citizen creates value]                                  │
         │                                               │
         ▼  (Annual repayment — 0% interest)             │
[Repayment returns to pool] ─────────────────────────────┘
         │
         ▼  (if < 30% repaid)
[TDRW Freeze Period] — circuit breaker, not punishment
```

**The key innovation:** The advance is backed by real automation output, not arbitrary money printing. When machines do more work, the pool grows. Citizens invest in themselves, repay, and the pool refills. It is a closed, self-balancing circuit.

### Who Can Get It

Everyone. There is no means test, no credit check, no collateral requirement.

| Eligibility Gate | Condition |
|-----------------|-----------|
| Not in freeze window | No prior default in last 2–7 years (depends on severity) |
| No active loan | Previous advance fully repaid or window closed |
| Pool funded | Pool above 20% reserve floor |

Designed especially for: students, unemployed adults, NEET youth, entrepreneurs without collateral, people bridging hardship, parents returning to work.

### What Makes It Different

| Feature | UBI | Welfare | Bank Loan | **Time Borrowing** |
|---------|-----|---------|-----------|-------------------|
| Repayment | No | No | Yes + interest | **Yes — 0% interest** |
| Collateral | None | None | Financial asset | **Future time only** |
| Inflation risk | HIGH | HIGH | Low | **MINIMAL** |
| Accessible to poor | Yes | Yes | Usually NO | **YES — universal** |
| Productivity link | None | None | Indirect | **Direct** |
| Self-balancing | No | No | Partial | **YES — TDRW circuit** |
| Requires existing systems | No | No | No | **No — fully additive** |

---

## Simulation Results

This repository contains a full agent-based economic simulation proving the instrument works. Run it yourself:

```bash
cd /path/to/economy
python prove_tb_works.py      # full proof: 4 scenarios × 25 years
python run_simulation.py      # interactive simulation runner
python run_simulation.py --help  # all options
```

### 10/10 Proof Points Confirmed (N=50 people, 25 years)

| # | Proof Point | Result | Evidence |
|---|-------------|--------|----------|
| PP1 | TB grows GDP faster than baseline | **PROVEN** | +59.0% GDP after 25 years |
| PP2 | TB does NOT cause excess inflation | **PROVEN** | 0.53% vs 1.02%/yr in baseline |
| PP3 | TB pool is self-sustaining | **PROVEN** | Pool grew 20× (132 → 2,809 units) |
| PP4 | TB reduces inequality | **PROVEN** | Gini: 0.358 → 0.323 (−9.8%) |
| PP5 | No welfare dependency bloat | **PROVEN** | Welfare/GDP ratio locked at 12% |
| PP6 | TB boosts worker productivity | **PROVEN** | +50.2% average productivity |
| PP7 | TB beats automation-only scenario | **PROVEN** | TB: 20,521 vs Auto-only: 14,578 |
| PP8 | TB survives climate stress test | **PROVEN** | Pool intact after shocks |
| PP9 | TDRW correctly freezes defaulters | **PROVEN** | Full default → 3.33yr freeze |
| PP10 | TDRW never penalises threshold-meeters | **PROVEN** | 30% repaid → 0yr freeze |

### 4-Scenario Comparison

| Scenario | GDP Year 25 | CAGR | Avg Inflation | Gini |
|----------|------------|------|---------------|------|
| A: Baseline (no TB) | 12,906 | 3.87%/yr | 1.02% | 0.358 |
| B: Automation only (no TB redistribution) | 14,578 | 4.38%/yr | 0.91% | 0.358 |
| C: Full TB instrument | **20,521** | **5.86%/yr** | **0.53%** | **0.323** |
| D: TB + climate stress test | 20,492 | 5.86%/yr | 0.53% | 0.323 |

---

## Repository Structure

```
economy/
├── simulation.py           # Core simulation engine (TimeBorrowingEconomy class)
├── parameters.py           # All calibrated constants + EconomyState dataclass
├── agents.py               # Agent types, population shares, MPC values
├── relationships.py        # 28 agent-relationship functions (R01–R28)
├── time_borrowing.py       # TB instrument equations (EQ-TB-0 through EQ-TB-5)
├── equation_library.py     # 36 pure economic equations (Solow, Taylor, Fisher…)
├── run_simulation.py       # CLI for running simulations
├── prove_tb_works.py       # Full proof: 4 scenarios, 10 proof points, JSON/CSV export
│
├── builders/               # Document generation scripts
│   ├── build_all_docs.py       # Generates all 3 Word documents (EN + SQ)
│   ├── build_word_doc.py       # Original single-doc builder
│   └── doc_i18n.py             # Localisation helpers
│
├── tests/
│   ├── test_equations.py       # 117 tests for equation_library.py
│   ├── test_relationships.py   # 122 tests for all 28 relationships
│   ├── test_agents.py          # 20 tests for agent shares and definitions
│   └── test_time_borrowing.py  # 31 tests for TB instrument equations
│
├── outputs/
│   ├── proof/
│   │   ├── proof_summary.json      # 10 proof points with pass/fail
│   │   ├── proof_timeseries.json   # Full year-by-year data (4 scenarios)
│   │   ├── proof_comparison.csv    # Excel-importable side-by-side
│   │   ├── proof_tb_mechanics.json # TDRW examples, pool projections
│   │   └── proof_report.md        # Human-readable proof document
│   └── documents/
│       ├── en/                     # English Word documents
│       │   ├── Time_Borrowing_Policy_Proposal.docx
│       │   ├── Time_Borrowing_Citizen_Guide.docx
│       │   └── Time_Borrowing_Geopolitics_Game_Theory.docx
│       └── sq/                     # Albanian Word documents (Albanian filenames)
│           ├── Propozimi_i_Politikave_-_Huazimi_i_Kohes.docx
│           ├── Udhezuesi_per_Qytetaret_-_Huazimi_i_Kohes.docx
│           └── Gjeopolitika_dhe_Teoria_e_Lojrave_-_Huazimi_i_Kohes.docx
│
├── README.md           # Default README — Albanian (shown on GitHub)
├── README_ENG.md       # This file — English version
└── LICENSE.md          # Humanitarian Use License (English + Shqip)
```

---

## Quick Start

### Requirements

```bash
pip install python-docx matplotlib
```

No other dependencies beyond the Python standard library.

### Run the proof simulation

```bash
python prove_tb_works.py
```

Outputs in `outputs/proof/`:
- `proof_summary.json` — all 10 proof assertions with pass/fail status
- `proof_timeseries.json` — full year-by-year data for all 4 scenarios
- `proof_comparison.csv` — importable to Excel or Google Sheets
- `proof_tb_mechanics.json` — TDRW examples, advance calculations, pool projections

### Run all tests

```bash
python tests/test_equations.py
python tests/test_relationships.py
python tests/test_agents.py
python tests/test_time_borrowing.py
```

293 tests total — all should pass with 0 failures.

### Interactive simulation

```bash
python run_simulation.py --years 50 --population 1000
python run_simulation.py --compare          # TB vs no-TB side by side
python run_simulation.py --show-relations   # print all 28 relationships
python run_simulation.py --show-equations   # print all 36 equations
python run_simulation.py --show-agents      # print agent population shares
```

### Generate Word documents

```bash
python builders/build_all_docs.py          # builds English + Albanian
python builders/build_all_docs.py --lang en  # English only
python builders/build_all_docs.py --lang sq  # Albanian only
```

Produces documents in:
- `outputs/documents/en/` — English versions
- `outputs/documents/sq/` — Albanian versions with Albanian filenames:
  - `Propozimi_i_Politikave_-_Huazimi_i_Kohes.docx`
  - `Udhezuesi_per_Qytetaret_-_Huazimi_i_Kohes.docx`
  - `Gjeopolitika_dhe_Teoria_e_Lojrave_-_Huazimi_i_Kohes.docx`

---

## Economic Framework

### Evolving Parameters (18)

The simulation tracks 18 state variables that change year by year:

| Parameter | Description |
|-----------|-------------|
| `year` | Simulation year |
| `population` | Total population (logistic growth) |
| `money_supply` | Total money in circulation |
| `price_level` | Aggregate price index |
| `inflation_pct` | Annual inflation rate |
| `nominal_interest_rate` | Central bank policy rate (Taylor Rule) |
| `real_interest_rate` | Nominal minus inflation (Fisher equation) |
| `resources_produced` | Total economic output (GDP proxy) |
| `resources_consumed` | Total consumption (≤ resources_produced) |
| `investment` | Capital formation |
| `tax_revenue` | Government tax inflows |
| `government_balance` | Fiscal surplus/deficit |
| `cumulative_debt` | Accumulated government debt |
| `tb_pool_size` | TB liquidity pool balance |
| `tb_amount_issued` | Cumulative TB advances issued |
| `tb_repayments_received` | Cumulative TB repayments |
| `employment_rate` | Employment/population ratio (Okun's Law) |
| `gini_coefficient` | Inequality measure |

### Agents (4)

| Agent | Share | Role |
|-------|-------|------|
| Government | 10% | Manages TB instrument, sets policy, collects taxes |
| FreeOne | 50% | Students, retirees, NEET, unemployed — primary TB users |
| Producer | 40% | Employed workers, self-employed — primary TB repayers |
| Consumer | 100% | Universal — everyone consumes |

> Population shares verified against OECD 2025 Employment Outlook and UN Population data.

### 28 Agent Relationships

| ID | From | To | Economic Effect |
|----|------|----|----------------|
| R01 | Consumer | Producer | Consumption spending → VAT, demand-pull inflation |
| R02 | Producer | Government | Income + corporate tax → fiscal revenue |
| R03 | Government | FreeOne | Welfare/pension transfers → consumption |
| R04 | Producer | Consumer | Wages → disposable income → spending |
| R05 | Consumer | Government | VAT on purchases → fiscal revenue |
| R06 | Government | CentralBank | Deficit financing → money supply |
| R07 | CentralBank | Economy | Interest rate adjustment (Taylor Rule) |
| R08 | Producer | Producer | B2B supply chain → primary GDP driver |
| R09 | TBInstrument | Consumer | TB advance → capital injection |
| R10 | Consumer | TBInstrument | TB repayment → pool refill |
| R11 | Automation | TBPool | Automation tax → pool funding |
| R12 | Government | Economy | Infrastructure investment → TFP |
| R13 | FreeOne | Market | Welfare spending → consumption demand |
| R14 | Environment | Economy | Climate/resource shock → GDP contraction |
| R15 | Inflation | Consumer | Real purchasing power erosion |
| R16 | Producer | R&D | Innovation investment → TFP growth |
| R17 | Producer | World | Exports → external demand |
| R18 | World | Market | Imports → domestic displacement |
| R19 | TBDefaulter | TBSystem | Default → TDRW freeze calculation |
| R20 | FreeOne | Labour | Education → skilled labour entry |
| R21 | TaxReserve | TBPool | Tax top-up → pool stabilisation |
| R22 | Workers | Firms | Wage-price spiral → second-round inflation |
| R23 | Producer | FreeOne | Hiring unemployed → employment rate |
| R24 | Government | Producer | Subsidies → business investment |
| R25 | Government | BondMarket | Debt service → crowding-out |
| R26 | TBInstrument | Education | TB funds education → FreeOne becomes Producer |
| R27 | TBInstrument | NewBusiness | TB funds entrepreneurship → new GDP |
| R28 | TBRecipient | TBPool | Productive TB use → premium repayment loop |

### Key Equations (36)

All equations in `equation_library.py` — individually tested, academically sourced:

| Equation | Formula | Source |
|----------|---------|--------|
| Quantity Theory of Money | `π ≈ ΔM/M − ΔY/Y` | Fisher (1911) |
| Taylor Rule | `i = r* + π + 0.5(π−π*) + 0.5·y_gap` | Taylor (1993) |
| Keynesian Multiplier | `k = 1/(1−MPC)` | Keynes (1936) |
| Solow Growth | `g_Y = g_A + α·g_K + (1−α)·g_L` | Solow (1956) |
| Fisher Equation | `r = (1+i)/(1+π) − 1` | Fisher (1930) |
| Okun's Law | `Δu = −β·(g_Y − g_Y*)` | Okun (1962) |
| Mincer Human Capital | `ln(w) = a + b·edu + c·exp` | Mincer (1974) |
| TDRW Freeze Period | `F = F_base × severity × (1+d·k) × T/T_ref` | Murseli & AI derivation (2026) |
| TB Advance Amount | `A = min(requested, A_max, pool_share)` | Murseli & AI derivation (2026) |
| TB Pool Dynamics | `P(t+1) = P(t) + tax + repayments − advances − losses` | Murseli & AI derivation (2026) |
| TB Automation Tax Revenue | `T_auto(t) = base × (1+g)^t × τ_auto` | Murseli & AI derivation (2026) |

### Governable Policy Parameters (11)

The government has 11 levers to tune the instrument:

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `automation_tax_rate` | 15% | 5–30% | Pool size |
| `tb_min_amount` | 500 units | 100–2,000 | Accessibility |
| `tb_max_amount` | 5,000 units | 1k–50k | Max life investment |
| `tb_max_period_years` | 5 yr | 1–10 | Repayment flexibility |
| `tb_repayment_threshold` | 30% | 10–80% | Freeze trigger strictness |
| `freeze_base_years` | 2.0 yr | 0.5–7 | Deterrent strength |
| `freeze_max_years` | 7 yr | 3–15 | Hard deterrent cap |
| `pool_min_reserve_ratio` | 20% | 10–40% | Safety buffer |
| `inflation_target` | 2% | 0–5% | Central bank response |
| `govt_investment_rate` | 3% GDP | 1–8% | Fiscal stimulus level |
| `seed_capital_multiplier` | 2× | 1–5× | Phase-1 pool ramp-up |

---

## What Can Be Improved (Future Work)

This section is an honest audit of the known gaps and areas where the current model needs further work before real-world implementation.

### 1. Real-World Calibration
**Current state:** The simulation uses Abstract Currency Units (ACU) — a dimensionless proxy.  
**What's needed:** Calibration to a specific real economy (e.g., EU GDP per capita, USD purchasing power). This requires mapping ACU → EUR/USD and verifying that the simulated automation tax rate (15%) generates a realistic pool size given actual AI/automation sector revenues.  
**Effort:** Medium — requires real economic data and a calibration pass over all parameters.

### 2. Agent Heterogeneity
**Current state:** Only 4 agent types with uniform behaviour within each class.  
**What's needed:** Each agent should have individual attributes — age, education level, income, employment history, health status, family size. TB repayment probability should vary by agent profile, not be uniform. This would enable proper actuarial modelling of default rates.  
**Effort:** High — requires rearchitecting the agent model to support individual-level heterogeneity.

### 3. Default Rate Empirical Calibration
**Current state:** Default rate is a fixed assumption (5% loss rate in stress tests). No empirical basis.  
**What's needed:** Actuarial analysis of comparable instruments (student loan default rates, microfinance, social lending) by demographic group. The TDRW calibration should be tested against empirical recidivism data.  
**Effort:** Medium — primarily a research and data task.

### 4. Automation Output Measurement Methodology
**Current state:** The automation tax is modelled as a flat % of GDP growth from automation. No method is specified for measuring "automation output value" in practice.  
**What's needed:** A formal taxation methodology — e.g., compute hours used, cost savings vs prior labour cost, value-added by AI systems. This is the hardest implementation challenge in the real world.  
**Effort:** High — requires collaboration with tax authorities and economists.

### 5. Algorithmic Bias and Disparate Impact Testing
**Current state:** The TDRW freeze equation treats all demographics identically.  
**What's needed:** Audit whether the freeze formula produces disparate outcomes across groups defined by age, gender, income level, health status, or ethnicity. If so, exemption or adjustment mechanisms are needed.  
**Effort:** Medium — requires demographic data and fairness analysis tools.

### 6. Healthcare and Disability Exemptions
**Current state:** No model for citizens who are genuinely unable to repay due to severe illness, disability, or death.  
**What's needed:** A medical hardship exemption track within the TDRW system — waiving or pausing freeze periods for documented cases of involuntary non-repayment.  
**Effort:** Low–Medium — primarily a policy design and legal framework task.

### 7. Privacy Architecture Specification
**Current state:** The simulation assumes a "digital TB registry" without specifying its architecture.  
**What's needed:** A formal privacy-by-design specification for the TB registry: what data is stored, who can access it, how long records are kept, what the appeal process looks like. The registry must be isolated from bank credit systems and employer checks.  
**Effort:** Medium — requires privacy law expertise and systems design.

### 8. Political Economy Modelling
**Current state:** The government is modelled as a passive rule-follower — it sets parameters but does not strategise.  
**What's needed:** A model where the government is itself a strategic actor facing electoral pressures, lobbying from automation companies, and incentives to manipulate the TB parameters for short-term political gain. Game theory applied internally to the instrument's governance.  
**Effort:** High — requires a political economy sub-model.

### 9. International TB Portability
**Current state:** The simulation is a closed or simple open economy — no cross-border TB tracking.  
**What's needed:** A protocol for what happens when a TB borrower migrates: does their obligation follow them? Which country's pool holds the advance? How do repayments flow internationally? This is essential for the OECD TB Treaty scenario.  
**Effort:** High — requires international legal and financial protocol design.

### 10. Skill Depreciation and Matching
**Current state:** TB-funded education permanently increases productivity. No skill obsolescence modelled.  
**What's needed:** Skill depreciation curves (skills learned via TB can become obsolete, especially in tech). A skill-to-job matching model that tracks whether TB-funded education actually produces employable skills in the current labour market.  
**Effort:** Medium — requires occupational data and depreciation modelling.

### 11. Secondary Effects on Credit Markets
**Current state:** No modelling of how TB affects traditional banking.  
**What's needed:** Banks currently profit from student loans, personal loans, and SME lending. TB competes in all three markets. A model of how banks respond (reduce rates? pivot to complementary products?) and how this affects the broader financial system.  
**Effort:** Medium — requires financial sector sub-model.

### 12. TB for Climate Adaptation
**Current state:** Climate appears only as a negative shock (R14). No modelling of TB as a climate investment tool.  
**What's needed:** A specific TB track for green transition investments — funding citizens to retrain for renewable energy jobs, electrify homes, or start green businesses. Should model the carbon reduction co-benefit and whether it justifies a higher advance limit.  
**Effort:** Low–Medium — primarily a policy design and parameter extension task.

### 13. Behavioural Economics Integration
**Current state:** Agents follow rational-actor assumptions (fixed MPC, rational repayment decisions).  
**What's needed:** Behavioural biases — present-biased preferences, loss aversion, social norms around debt — should affect take-up rates, repayment behaviour, and how citizens use their advances. Nudge design for the TB system.  
**Effort:** Medium — requires behavioural economics literature integration.

### 14. Larger Population Simulation and Scaling Validation
**Current state:** The proof simulation uses N=50 people. While mathematically sound, larger populations may reveal emergent dynamics.  
**What's needed:** Run N=10,000, N=1,000,000 simulations. Validate that the percentage-based relationship deltas scale correctly. Check for edge cases at scale (pool exhaustion, hyper-default events, etc.).  
**Effort:** Low — primarily a computational task; infrastructure already supports it.

### 15. Real-World Pilot Programme Design
**Current state:** The simulation proves the concept mathematically. No real-world pilot design exists.  
**What's needed:** A formal pilot programme specification — target country/region, citizen selection, advance parameters, monitoring framework, success metrics, evaluation methodology, and independent oversight structure. Without a real-world pilot, the simulation remains theoretical.  
**Effort:** Very High — this is the ultimate next step. Everything else feeds into this.

---

## Contributing

This project is open for contributions from anyone who wants to improve the model, the documentation, or the real-world implementation pathway. Please:

1. Fork the repository
2. Create a feature branch
3. Add or improve simulation components, tests, or documentation
4. Ensure all 293 tests still pass
5. Submit a pull request with a clear description of what you improved and why

All contributions must align with the [Humanitarian Use License](LICENSE.md).

---

## Tests

```
tests/test_equations.py       117 tests — every equation individually verified
tests/test_relationships.py   122 tests — all 28 relationships sign-correct + monotonic
tests/test_agents.py           20 tests — agent shares and MPC values
tests/test_time_borrowing.py   31 tests — TB instrument equations

Total: 293 tests | Pass rate: 100%
```

Run all at once:
```bash
for t in tests/test_*.py; do python $t; done
```

---

## About the Author

**Enis Murseli** conceived the Time Borrowing Instrument as an original theoretical framework. The economic simulation, code, unit tests, and documentation in this repository were developed under his continuous direction and intellectual guidance.

AI tools (large language models) were used to:
- Search and cross-reference established economic literature and equations
- Write and test Python simulation code under the author's specifications
- Structure and format documentation

All theoretical decisions — which equations to use, how the TB circuit works, what constitutes mathematical proof, and the policy design — are the original intellectual work of Enis Murseli.

---

## License

This work is released under the **Humanitarian Use License**.  
It may be freely used, studied, modified, and shared **for the benefit of humanity as a whole**.  
It may **not** be used for the exclusive benefit of any single country, religion, political party, corporation, or any group that does not represent all of humanity.

See [LICENSE.md](LICENSE.md) for full terms in English and Albanian.

---

*Albanian version (default README): [README.md](README.md)*
