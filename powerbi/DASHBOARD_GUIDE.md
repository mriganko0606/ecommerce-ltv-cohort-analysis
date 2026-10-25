# Power BI Dashboard: Build Guide

This guide takes you from the exported CSVs to the finished 4-page dashboard
in about 45-60 minutes. You need **Power BI Desktop** (free, Windows), from the
Microsoft Store or https://powerbi.microsoft.com/desktop.

> Run `python run_pipeline.py` first, so that `powerbi/data/` contains the CSVs.

---

## 1. Load the data

**Home > Get data > Text/CSV**, then load each file from `powerbi/data/`:

| File | Table role |
|---|---|
| `fact_orders.csv` | Fact table, one row per completed order |
| `fact_order_lines.csv` | Fact table, one row per order line (for product/category visuals) |
| `dim_customers.csv` | Customer dimension: country, channel, cohort, RFM scores, segment |
| `dim_products.csv` | Product dimension |
| `cohort_retention.csv` | Optional pre-computed cohort grid (from SQL), useful for cross-checking |

In **Power Query (Transform data)**, check the column types:

- `order_date`, `first_order_date`, `last_order_date`, `signup_date` → **Date**
- `revenue`, `cost`, `gross_profit`, `historical_revenue`, `unit_price`, `line_revenue` → **Decimal number** (or Fixed decimal)
- `months_since_first_order`, `r_score`, `f_score`, `m_score`, `orders` → **Whole number**
- `cohort_month`, `order_month`, `rfm_cell` → **Text**

Click **Close & Apply**.

## 2. Create the date table and the measures

1. **Modeling > New table** and paste the `dim_date` definition from `DAX_measures.dax`.
2. Select `dim_date`, then **Table tools > Mark as date table**, using the `Date` column.
3. Sort `dim_date[Month]` by `Month Number` (**Column tools > Sort by column**).
4. **Home > Enter data**, name the empty table `_Measures` and load it.
5. Add each measure from `DAX_measures.dax` to `_Measures` (**Modeling > New measure**)
   and set the format string given in the comment above it.
6. Hide `CLV Last Date` (it is only used by other measures).

## 3. Relationships (Model view)

Create these relationships (all *one-to-many*, single cross-filter direction):

```
dim_date[Date]              1 ──< fact_orders[order_date]
dim_date[Date]              1 ──< fact_order_lines[order_date]
dim_customers[customer_id]  1 ──< fact_orders[customer_id]
dim_customers[customer_id]  1 ──< fact_order_lines[customer_id]
dim_products[product_id]    1 ──< fact_order_lines[product_id]
```

Leave `cohort_retention` unrelated (it stands alone).

## 4. Pages and visuals

Use the same slicer panel on every page: **Year-Month (dim_date)**,
**acquisition_channel**, **country**, **segment**. Use **View > Sync slicers** to
keep them in sync across pages.

### Page 1: Executive Overview
| Visual | Fields |
|---|---|
| 5 Card visuals | `Total Revenue`, `Total Orders`, `Active Customers`, `Average Order Value`, `Gross Margin %` |
| KPI card with MoM | Card: `Total Revenue`; subtitle/reference label: `Revenue MoM %`, coloured with the `MoM Color` measure |
| Line & clustered column chart | X: `dim_date[Year-Month]`; Columns: `Total Revenue`; Line: `Revenue MoM %` |
| Line chart | X: `Year-Month`; Values: `Total Revenue`, `Revenue 3M Rolling Avg` |
| Stacked column chart | X: `Year-Month`; Values: `New Customers`, `Returning Customers` |
| Table | `Year-Month`, `Total Revenue`, `Revenue MoM %`, `Active Customers MoM %`, `AOV MoM %`, `Revenue YTD` |

### Page 2: Customer Segmentation (RFM)
| Visual | Fields |
|---|---|
| Cards | `Champions Revenue Share %`, `Top 20% Customers Revenue Share %`, `Repeat Customer Rate` |
| Clustered bar chart | Y: `dim_customers[segment]`; X: `Revenue Share %`, `Customer Share %` |
| Matrix (heatmap) | Rows: `r_score` (sorted descending); Columns: `f_score`; Values: `Avg Historical Revenue per Customer`, with a background colour scale |
| Scatter chart | Details: `customer_id`; X: `orders`; Y: `historical_revenue`; Legend: `segment` |
| Table | `segment`, `Active Customers`, `Total Revenue`, `Revenue Share %`, `Average Order Value`, `Orders per Customer` |

### Page 3: Cohort Retention
| Visual | Fields |
|---|---|
| Matrix | Rows: `dim_customers[cohort_month]`; Columns: `fact_orders[months_since_first_order]`; Values: `Cohort Retention %` |
| | Under **Format > Cell elements**, turn on a background colour gradient (white → dark blue). Turn off row and column subtotals. |
| Line chart | X: `months_since_first_order`; Y: `Cohort Retention %` (average curve). Add `cohort_month` to Legend for individual cohorts |
| Line chart | X: `months_since_first_order`; Y: `Cohort Cumulative Revenue per Customer`; Legend: `cohort_month` (filter to quarterly cohorts) |
| Card | `Cohort Size` |

### Page 4: Customer Lifetime Value
| Visual | Fields |
|---|---|
| Cards | `Predicted CLV`, `Annual Churn Rate`, `Expected Lifespan (Years)`, `Annual Margin per Customer`, `Customer Base Value` |
| Clustered bar chart | Y: `acquisition_channel`; X: `Predicted CLV` |
| Clustered bar chart | Y: `country`; X: `Predicted CLV` |
| Table | `acquisition_channel`, `Customers Prior 12M`, `Retained Customers`, `Annual Churn Rate`, `Expected Lifespan (Years)`, `Annual Margin per Customer`, `Predicted CLV`, `Predicted CLV (Revenue)` |
| Text box | Method note: *CLV = annual gross margin per active customer × expected lifespan (1 / annual churn, capped at 5 years).* |

> The CLV measures use fixed 12-month windows ending at the latest order date,
> so they ignore the date slicer on purpose. They do respond to the channel and
> country slicers. Don't slice them by RFM segment: segments are defined by
> recency, which makes their churn rate circular.

## 5. Check against Python

Your cards should match the Python outputs:

| Power BI measure | Python file / value |
|---|---|
| `Total Revenue` (no filters) | `reports/findings.md`, total revenue |
| `Champions Revenue Share %` | `reports/tables/segment_summary.csv`, Champions `pct_revenue` |
| `Annual Churn Rate`, `Predicted CLV` | `reports/tables/clv_overall.csv` |
| `Predicted CLV` by channel | `reports/tables/clv_by_channel.csv` |
| `Cohort Retention %` matrix | `reports/tables/cohort_retention_grid.csv` |

## 6. Finishing touches

- Theme: **View > Themes**, then choose a clean theme, or import a JSON theme with your brand colours.
- Add a title bar and a "Data as of 31 Dec 2024" text box to each page.
- Save the report as `powerbi/Ecommerce_LTV_Cohort_Dashboard.pbix`.
- Export screenshots of each page to `reports/figures/powerbi_*.png` for the README / portfolio.
