# Automobile Analysis — Microsoft Power BI Report

An executive-ready Microsoft Power BI report for exploring automobile
inventory, pricing, market mix, and data quality.

**[Download the Power BI report](./Automobile_Analysis_PowerBI.pbix)**

> Created by Hieu Nguyen

## Report overview

The `.pbix` file contains an imported snapshot of the cleaned automobile
dataset, so the report can be viewed immediately after download without running
the Python pipeline first. It includes two report pages:

| Page | Purpose |
|---|---|
| **Executive Overview** | Summarizes inventory scale, listed value, pricing, mileage, accident history, model-level pricing, and fuel mix. |
| **Business Insights** | Highlights data quality, completeness, electrification, body-type pricing, and decision-ready findings from the portfolio. |

The Executive Overview includes a model-level combo chart with:

- `Vehicle Count` as the columns;
- `Average Price` and `Median Price` as line overlays rendered above the
  columns; and
- columns set to **85% opacity** (**15% transparency**) to keep both price
  lines clearly visible.

## KPI and measure catalog

The semantic model contains 11 reusable DAX measures:

1. `Vehicle Count`
2. `Total Listed Value`
3. `Average Price`
4. `Median Price`
5. `Average Mileage`
6. `No-Accident Rate`
7. `Cell Completeness`
8. `Fully Complete Row Rate`
9. `Quality Review Rate`
10. `Electrified Share`
11. `Average Price vs Portfolio`

Cards, KPI indicators, a column-and-line combo chart, a donut chart, a
body-type price chart, and a business-insight panel provide a familiar
Microsoft Power BI executive-dashboard experience.

## Download and open

1. Select **Download the Power BI report** above.
2. If GitHub opens the file page, select **Download raw file**.
3. Open `Automobile_Analysis_PowerBI.pbix` in
   [Microsoft Power BI Desktop](https://powerbi.microsoft.com/desktop/).
4. Use the page tabs at the bottom to switch between **Executive Overview**
   and **Business Insights**.

The saved report includes the imported data and should open with all visuals
populated. Power BI Desktop may display a version-compatibility prompt if an
older release is installed; updating to the current Desktop release resolves
that issue.

## Refreshing the data

The report is delivered with embedded imported data, so a refresh is not
required for viewing. To refresh it with a newer project export:

1. Run `python scripts/clean_data.py` from the repository root.
2. In Power BI Desktop, open **Transform data > Data source settings**.
3. Change the CSV source to
   `data/processed/automobile_cleaned.csv` in your local clone.
4. Select **Refresh**, validate the visuals, and save the report.

Because local clone locations differ, Power BI may ask you to update the source
path before the first refresh. This does not affect the data already embedded
in the downloaded report.

## Interpretation notes

- Prices represent asking/listed prices, not completed-sale prices.
- The dataset is cross-sectional; it does not support revenue growth or
  time-to-sale analysis.
- Relationships shown in the report are descriptive and should not be treated
  as causal.
- Source-system boundary values and incomplete records are retained and
  surfaced through data-quality measures rather than silently removed.

---

**Created by Hieu Nguyen**
