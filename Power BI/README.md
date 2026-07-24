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

## Power BI Service deployment

The report and semantic model are published to the
**Finance Analytics [Test]** workspace with the following operating
configuration:

| Setting | Published configuration |
|---|---|
| Storage mode | Import |
| Data source | Public GitHub Web CSV |
| Source file | [`data/processed/automobile_cleaned.csv`](https://raw.githubusercontent.com/hnguyen76/Automobile_Analysis/main/data/processed/automobile_cleaned.csv) |
| Scheduled refresh | Daily at **6:00 AM** |
| Time zone | **Eastern Time (US and Canada)** |
| Refresh validation | Manual refresh completed successfully on **July 24, 2026 at 3:49:19 PM ET** |
| Next scheduled refresh | **July 25, 2026 at 6:00 AM ET** |

Import mode keeps a managed snapshot in the Power BI semantic model. The
scheduled refresh retrieves the current cleaned CSV from the public GitHub Web
source and updates report visuals after the import completes.

## Row-level security

Five static row-level security (RLS) roles are defined on the `location`
column:

| Role | DAX row filter | Data scope |
|---|---|---|
| `RLS_Northeast` | `[location] IN {"NY", "PA"}` | New York and Pennsylvania |
| `RLS_Midwest` | `[location] IN {"IL", "MI", "OH"}` | Illinois, Michigan, and Ohio |
| `RLS_South` | `[location] IN {"FL", "GA", "NC", "TX"}` | Florida, Georgia, North Carolina, and Texas |
| `RLS_West` | `[location] = "CA"` | California |
| `RLS_DataQuality` | `[location] = "Unknown"` | Records whose location is unknown |

All five roles are published and currently show **0 members**. No users or
groups have been assigned yet, so role membership must be configured before
the regional views are distributed.

RLS is intended for **Viewer/read-only consumers** of the published content.
Power BI workspace Admin, Member, and Contributor roles are not restricted by
these RLS filters. Assign consumers read-only access and add them to the
appropriate RLS role; assigning a role does not itself grant access to the
report.

## Refreshing the data

The downloaded report includes imported data, so a refresh is not required for
viewing. The published semantic model refreshes automatically from the public
GitHub Web CSV every day at 6:00 AM Eastern Time.

To publish updated source data:

1. Run `python scripts/clean_data.py` from the repository root.
2. Validate and commit the updated
   `data/processed/automobile_cleaned.csv` file to the `main` branch.
3. In Power BI Service, run an on-demand refresh or wait for the next daily
   scheduled refresh.
4. Confirm the refresh history shows `Completed` and validate the report
   visuals.

Power BI Desktop can also refresh the Import model directly from the same
GitHub Web source while an internet connection is available.

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
