"""Customer Lifetime Value (CLV) prediction.

Formula (identical to the Power BI DAX measures, so the numbers reconcile):

    annual churn rate     = 1 - (customers active in BOTH the prior 12m and
                                 the last 12m) / (customers active in prior 12m)
    expected lifespan     = min(1 / annual churn rate, MAX_LIFESPAN_YEARS)
    annual margin / cust  = gross profit in last 12m / customers active in last 12m
    predicted CLV         = annual margin per customer x expected lifespan

CLV is reported overall and by acquisition channel / country. It is not
reported by RFM segment, because segments are themselves defined by recency
(e.g. every Champion is active by definition), which would make the churn
rate circular. Segments are compared on historical value instead.
"""
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from .config import MAX_LIFESPAN_YEARS, TABLE_DIR
from .db import connect, read_table
from .plotting import ACCENT, PRIMARY, save, set_style


def clv_metrics(df):
    prior = df["active_prior_12m"].sum()
    retained = (df["active_prior_12m"] & df["active_last_12m"]).sum()
    active = df["active_last_12m"].sum()
    churn = 1 - retained / prior if prior else float("nan")
    lifespan = min(1 / churn, MAX_LIFESPAN_YEARS) if churn else MAX_LIFESPAN_YEARS
    revenue_l12m = df["revenue_last_12m"].sum()
    margin_l12m = df["gross_profit_last_12m"].sum()
    annual_margin = margin_l12m / active if active else float("nan")
    return pd.Series({
        "customers": len(df),
        "active_last_12m": active,
        "annual_churn_rate_pct": churn * 100,
        "expected_lifespan_years": lifespan,
        "annual_revenue_per_customer": revenue_l12m / active if active else float("nan"),
        "gross_margin_pct": margin_l12m / revenue_l12m * 100 if revenue_l12m else float("nan"),
        "annual_margin_per_customer": annual_margin,
        "predicted_clv": annual_margin * lifespan,
        "avg_historical_revenue": df["historical_revenue"].mean(),
    })


def clv_by(customers, column):
    return (customers.groupby(column).apply(clv_metrics, include_groups=False)
            .sort_values("predicted_clv", ascending=False).round(2))


def plot_clv_by_channel(by_channel, overall_clv):
    df = by_channel.sort_values("predicted_clv")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(df.index, df["predicted_clv"], color=PRIMARY)
    ax.axvline(overall_clv, color=ACCENT, ls="--", lw=1.5, label=f"All customers: ${overall_clv:,.0f}")
    for i, (clv, churn) in enumerate(zip(df["predicted_clv"], df["annual_churn_rate_pct"])):
        ax.text(clv + 2, i, f"${clv:,.0f}  (churn {churn:.0f}%)", va="center", fontsize=9)
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlim(0, df["predicted_clv"].max() * 1.35)
    ax.set_title("Predicted customer lifetime value (gross margin) by acquisition channel")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "clv_by_channel.png")


def plot_segment_value(customers):
    order = (customers.groupby("segment")["historical_revenue"].mean()
             .sort_values(ascending=False).index)
    fig, ax = plt.subplots(figsize=(9, 5))
    means = customers.groupby("segment")["historical_revenue"].mean().reindex(order)
    ax.bar(means.index, means.values, color=PRIMARY)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.set_ylabel("Avg revenue per customer to date")
    ax.set_title("Historical customer value by RFM segment")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    save(fig, "historical_value_by_segment.png")


def main():
    set_style()
    conn = connect()
    customers = read_table(conn, "customer_summary")
    conn.close()

    overall = clv_metrics(customers).round(2)
    by_channel = clv_by(customers, "acquisition_channel")
    by_country = clv_by(customers, "country")

    overall.to_frame("all_customers").to_csv(TABLE_DIR / "clv_overall.csv")
    by_channel.to_csv(TABLE_DIR / "clv_by_channel.csv")
    by_country.to_csv(TABLE_DIR / "clv_by_country.csv")

    plot_clv_by_channel(by_channel, overall["predicted_clv"])
    plot_segment_value(customers)

    return {"overall": overall, "by_channel": by_channel}


if __name__ == "__main__":
    main()
