# India Farm Gap Model

Agriculture employs over 40% of India's workers but contributes only about 16% of national output. This model uses official statistics to establish that gap and to test how small landholdings, climate shocks and low productivity keep rural incomes down.

## What is here

| File | Purpose |
|---|---|
| `agri_productivity_gap_model.py` | The model (Python: numpy, pandas, matplotlib). Run it to regenerate every output. |
| `index.html` | Interactive dashboard with sliders for the key assumptions. Open it in a browser. |
| `agri_model_results.json` | Headline results. |
| `agri_model_tables.csv` | Sensitivity grid, land classes, income by class, reallocation scenarios. |
| `agri_model_charts.png` | Six-panel summary chart. |

## Findings

- **Workers vs output:** 43.0% of workers (PLFS 2025) produce about 16% of GVA, so a non-farm worker produces about 4 times as much as a farm worker. Across the official ranges (15-18% GVA, 40-45% of workers) the ratio stays between 3.0 and 4.6.
- **Land:** 86% of holdings are under 2 ha but operate only 47% of the land. The average holding is 1.08 ha, and the class-level land Gini is at least 0.52.
- **Income:** average agricultural household income is about Rs 8,337 per month, roughly half of it from wages. Matching non-farm productivity from land alone would take about 7 ha, while only about 4% of holdings exceed 4 ha.
- **Climate stress:** under an assumed 20% yield loss with farm wages also falling, marginal households lose about 20% of income.

## Sources

- MoSPI, Periodic Labour Force Survey Annual Report 2025
- MoSPI, National Accounts (2011-12 and 2022-23 series)
- NSO, NSS 77th round, Situation Assessment of Agricultural Households (2018-19)
- Department of Agriculture and Farmers Welfare, Agriculture Census 2015-16
- NABARD Working Paper 2025-3, Farm Size and Productivity

## Caveats

- The farm share of GVA is about 15-17% in the old series and about 18% in the new 2022-23 series. 16% is used as the baseline.
- The Rs 8,337 income figure came from a secondary summary of the SAS report and should be checked against the NSO original.
- Income by size class assumes the same return per hectare in every class, and mixes survey households with census holdings, so it is indicative only.
- The yield-loss size, wage pass-through and mover pay are scenario inputs, not observed data.
- Climate, irrigation and state-level data are not yet included.

## Run

```
python3 agri_productivity_gap_model.py
```
