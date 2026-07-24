# Automobile Portfolio — Business Insights

**Created by Hieu Nguyen**

> Scope: 5,500 automobile listings spanning model years 2005–2024. The dataset
> contains asking prices, not completed transactions. Dollar values below are
> therefore **listed inventory value**, not revenue.

## Executive snapshot

| KPI | Value |
|---|---:|
| Vehicles | 5,500 |
| Total listed value | $67.76M |
| Average asking price | $12,320 |
| Median asking price | $8,586 |
| Average mileage | 114,529 |
| SUVs as a share of inventory | 49.15% |
| Electrified share (Hybrid + Electric) | 12.40% |
| Known no-accident rate | 59.19% |
| Cell-level data completeness | 92.61% |

## Key findings

### 1. Value is concentrated in newer model-year cohorts

- Model years 2020–2024 represent **25.35% of vehicles** but **57.83% of
  listed value**.
- Model year has the strongest observed linear relationship with asking price
  (`r = +0.805`). Mileage (`r = -0.683`) and owner count (`r = -0.669`) also
  have strong negative relationships with price.
- The 2024 cohort averages **$35,424**, versus **$30,552** for the 2023 cohort.
  This is a model-year comparison, not year-over-year sales growth.

**Business implication:** pricing benchmarks should be segmented by model year
and mileage. A single portfolio-wide average obscures most of the variation.

### 2. SUVs dominate both inventory and listed value

- SUVs account for **49.15% of vehicles** and **54.31% of listed value**.
- Their average asking price is **$13,615**, compared with **$11,297** for
  sedans—an observed premium of approximately **20.5%** before controlling for
  make, model year, mileage, or condition.

**Business implication:** SUV inventory deserves dedicated pricing and sourcing
benchmarks, while sedan performance should be evaluated separately rather than
against the portfolio average.

### 3. Premium makes carry disproportionate portfolio value

- Mercedes-Benz, Audi, and BMW make up **28.93% of units** but **46.40% of
  listed value**.
- Their combined average asking price is **$19,763**, versus approximately
  **$9,300** for the remaining makes.
- Among models with more than 100 listings, X5, GLE, and A6 have the highest
  average asking prices.

**Business implication:** changes in premium-brand mix can move the portfolio
average materially. Executive KPIs should always be read alongside mix.

### 4. Condition signals are commercially relevant, but confounded

- Listings with a reported accident average **$6,301**, versus **$16,338** for
  known accident-free listings.
- Within matched model-year and mileage bands, the typical accident-associated
  price gap narrows to roughly **10.8%**, showing that the raw difference is
  partly driven by vehicle mix.
- Full-service listings average **$12,980**, versus **$11,691** for no-service
  listings, an unadjusted difference of about **11.0%**.

**Business implication:** accident and service history should be included in
pricing models, but the dashboard correctly describes these as associations—not
causal effects.

### 5. Electric pricing comparisons require cohort controls

- Electric listings average **$21,522**, compared with **$11,394** for petrol.
- Electric vehicles are much newer and lower-mileage in this dataset (median
  model year 2020 and average 53,632 miles) than petrol vehicles (median model
  year 2013 and average 122,487 miles).
- Electric efficiency values use an MPGe-like scale, while combustion and
  hybrid vehicles use MPG. The dashboard avoids combining these into a single
  global fuel-efficiency KPI.

**Business implication:** the raw EV price premium should not be interpreted as
a fuel-type effect. Compare vehicles within similar model-year and mileage
cohorts.

## Data-quality risks

- **1,216 listings (22.11%)** sit exactly at the $500 price floor. This is
  likely censoring or a system boundary, so records are flagged rather than
  silently removed.
- **273 listings (4.96%)** have mileage exactly equal to 100; older-model
  examples are flagged for review.
- **7.39% of source cells** are missing, while only **24.16% of rows** are
  fully complete. Dropping incomplete rows would discard most of the dataset.
- Missing numeric specifications are imputed within comparable vehicle groups
  and retain explicit `*_was_imputed` flags. Unknown categorical values remain
  `Unknown`.
- One Electric–Manual combination is retained and flagged because the source
  provides no authoritative correction.

## Recommended next actions

1. Investigate the $500 price floor and 100-mile boundary in the source system.
2. Set pricing benchmarks by make/model, model-year band, mileage band, accident
   history, and service status.
3. Track inventory mix alongside average price so premium-brand and SUV shifts
   do not masquerade as pricing performance.
4. Improve data capture for location, service history, accident history, and
   transmission; report both the known-value rate and its coverage.
5. Add listing date, VIN or stable listing ID, sale status, actual transaction
   price, cost, and days on market before attempting revenue, margin, turnover,
   or time-series analysis.

## Interpretation guardrails

- The analysis is descriptive and cross-sectional.
- `Year` is the vehicle's model year, not a transaction date.
- Asking price is not realized sale price.
- Correlation and group differences do not establish causality.
- The source appears synthetic; manufacturer-specific conclusions should be
  validated against operational data.
